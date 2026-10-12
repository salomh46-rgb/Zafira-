"""
Zafira Language - Standalone AOT Single-Binary Packager Tests
Unit testlar:
  - Yagona faylni paketlash (.zf -> C / binar)
  - Ko'p faylli lokal modullarni bitta AST ga birlashtirish (Single Translation Unit)
  - Taxallussiz (alias bo'lmagan) importlarni boshqarish
  - Chuqur ichma-ich (nested/transitive) modullarni tartib bilan jamlash
  - Aylanma (circular) importlardan himoya
  - C Runtime komponentlarini (ZfList, strings, math, fs, io) tekshirish
  - zafira.json manifestli loyihalarni paketlash
  - Mocklangan C kompilyatori (GCC/Clang/TCC) orqali binar yaratish
  - Fallback rejimi (csc / standalone C generatsiyasi)
  - zafira.py pack CLI buyrug'i integratsiyasi
  - Birlashtirilgan dasturni Zafira Interpreterida to'g'ri bajarilishini tekshirish

Muallif: Jasper & Antigravity
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.lexer import Lexer
from src.parser import Parser, Program
from src.interpreter import Interpreter
from src.packager import (
    pack_project,
    bundle_project_ast,
    generate_single_translation_unit_c,
    resolve_entry_point,
    PackagerError,
    ProjectBundler
)
import zafira

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestZafiraPackager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="zf_test_pack_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_file(self, rel_path: str, content: str) -> str:
        """Test papkasida fayl yaratadi."""
        full_path = os.path.join(self.temp_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    # ─── 1. YAGONA FAYLNI PAKETLASH ───

    def test_single_file_packaging_c_only(self):
        """Yagona .zf fayli to'liq C manba kodiga paketlanishi kerak."""
        main_zf = self._write_file("main.zf", """
        let xabar = "Salom, Zafira Packager!"
        print(xabar)
        """)

        out_c = os.path.join(self.temp_dir, "dist", "main.c")
        res = pack_project(main_zf, output_path=out_c, force_c_only=True)

        self.assertTrue(res['success'])
        self.assertEqual(res['mode'], 'c_source')
        self.assertEqual(res['compiler'], 'c_transpiler')
        self.assertTrue(os.path.exists(out_c))
        self.assertGreater(res['size_bytes'], 0)
        self.assertEqual(len(res['bundled_files']), 1)

        # C kodini tekshirish
        with open(out_c, 'r', encoding='utf-8') as f:
            c_code = f.read()
        self.assertIn("#include <stdio.h>", c_code)
        self.assertIn("Salom, Zafira Packager!", c_code)
        self.assertIn("int main(int argc, char** argv)", c_code)

    # ─── 2. KO'P FAYLLI LOKAL MODULLARNI BIRLASHTIRISH ───

    def test_multi_file_local_modules_bundling(self):
        """
        Lokal modullar (import "./math_mod.zf" as m) Single Translation Unit
        AST ga birlashtirilib, nom maydoni to'g'ri qayta yozilishi kerak.
        """
        self._write_file("math_mod.zf", """
        fn kvadrat(x) {
            return x * x
        }
        let pi_taqribiy = 3
        """)

        main_zf = self._write_file("main.zf", """
        import "./math_mod.zf" as m
        let res = m.kvadrat(7)
        let pi = m.pi_taqribiy
        print("Kvadrat: " + String(res))
        """)

        bundled_ast, bundled_files = bundle_project_ast(main_zf)
        self.assertEqual(len(bundled_files), 2)

        # Bundled AST da funksiya m_kvadrat ga o'zgargan bo'lishi kerak
        fn_names = [stmt.name for stmt in bundled_ast.body if hasattr(stmt, 'name')]
        self.assertIn("m_kvadrat", fn_names)
        self.assertIn("m_pi_taqribiy", fn_names)

        # Interpreter orqali tekshirish
        interp = Interpreter(current_file=main_zf)
        interp.run(bundled_ast)
        self.assertEqual(interp.global_env.get("res"), 49)
        self.assertEqual(interp.global_env.get("pi"), 3)

        # C transpilatsiyasini tekshirish
        c_code = generate_single_translation_unit_c(bundled_ast)
        self.assertIn("m_kvadrat", c_code)
        self.assertIn("m_pi_taqribiy", c_code)

    # ─── 3. TAXALLUSSIZ (ALIAS BO'LMAGAN) IMPORTLAR ───

    def test_import_without_alias(self):
        """Taxallussiz import qilingan modullar fayl nomidan nom maydoni oladi."""
        self._write_file("hisob.zf", """
        fn qosh(a, b) {
            return a + b
        }
        """)

        main_zf = self._write_file("main.zf", """
        import "./hisob.zf"
        let yigindi = hisob.qosh(15, 25)
        """)

        bundled_ast, bundled_files = bundle_project_ast(main_zf)
        self.assertEqual(len(bundled_files), 2)

        interp = Interpreter(current_file=main_zf)
        interp.run(bundled_ast)
        self.assertEqual(interp.global_env.get("yigindi"), 40)

        c_code = generate_single_translation_unit_c(bundled_ast)
        self.assertIn("hisob_qosh", c_code)

    # ─── 4. CHUQUR ICHMA-ICH (TRANSITIVE) MODULLAR ───

    def test_nested_transitive_imports(self):
        """
        main.zf -> sub/a.zf -> sub/b.zf zanjiri to'g'ri topologik
        tartibda va yo'llar nisbiyligi saqlangan holda jamlanishi kerak.
        """
        self._write_file("sub/b.zf", """
        fn kub(x) {
            return x * x * x
        }
        """)

        self._write_file("sub/a.zf", """
        import "./b.zf" as b
        fn hisobla(x) {
            return b.kub(x) + 10
        }
        """)

        main_zf = self._write_file("main.zf", """
        import "./sub/a.zf" as a
        let natija = a.hisobla(3)
        """)

        bundled_ast, bundled_files = bundle_project_ast(main_zf)
        self.assertEqual(len(bundled_files), 3)

        interp = Interpreter(current_file=main_zf)
        interp.run(bundled_ast)
        # 3*3*3 + 10 = 37
        self.assertEqual(interp.global_env.get("natija"), 37)

        c_code = generate_single_translation_unit_c(bundled_ast)
        self.assertIn("b_kub", c_code)
        self.assertIn("a_hisobla", c_code)

    # ─── 5. SIKLIK (CIRCULAR) IMPORTDAN HIMOYALANISH ───

    def test_circular_import_protection(self):
        """Aylanma importlar cheksiz rekursiyaga olib kelmasdan xavfsiz jamlanishi kerak."""
        self._write_file("mod_a.zf", """
        import "./mod_b.zf" as b
        fn func_a() { return 100 }
        """)

        self._write_file("mod_b.zf", """
        import "./mod_a.zf" as a
        fn func_b() { return 200 }
        """)

        main_zf = self._write_file("main.zf", """
        import "./mod_a.zf" as a
        import "./mod_b.zf" as b
        let val_a = a.func_a()
        let val_b = b.func_b()
        """)

        # Xatoliksiz va cheksiz tsiklsiz yakunlanishi kerak
        bundled_ast, bundled_files = bundle_project_ast(main_zf)
        self.assertIn(os.path.abspath(main_zf), bundled_files)

        interp = Interpreter(current_file=main_zf)
        interp.run(bundled_ast)
        self.assertEqual(interp.global_env.get("val_a"), 100)
        self.assertEqual(interp.global_env.get("val_b"), 200)

    # ─── 6. C RUNTIME FUNKSIYALARINING MAVJUDLIGI ───

    def test_c_runtime_functions_included(self):
        """
        Single Translation Unit C kodida ZfList, satrlar, matematika,
        fayllar tizimi (fs) va kiritish-chiqarish (io) bo'lishi shart.
        """
        main_zf = self._write_file("runtime_test.zf", """
        let ro`yxat = [1, 2, 3]
        ro`yxat.push(4)
        let s = "  Salom  ".trim().upper()
        let ildiz = 16
        print(s)
        """)

        bundled_ast, _ = bundle_project_ast(main_zf)
        c_code = generate_single_translation_unit_c(bundled_ast)

        # 1. ZfList funksiyalari
        self.assertIn("typedef struct {", c_code)
        self.assertIn("int64_t* items;", c_code)
        self.assertIn("zf_list_create", c_code)
        self.assertIn("zf_list_push", c_code)
        self.assertIn("zf_list_pop", c_code)
        self.assertIn("zf_list_len", c_code)
        self.assertIn("zf_list_get", c_code)
        self.assertIn("zf_list_set", c_code)
        self.assertIn("zf_list_new", c_code)

        # 2. Satr funksiyalari
        self.assertIn("zf_str_concat", c_code)
        self.assertIn("zf_str_int", c_code)
        self.assertIn("zf_str_float", c_code)
        self.assertIn("zf_str_bool", c_code)
        self.assertIn("zf_str_eq", c_code)
        self.assertIn("zf_str_repeat", c_code)
        self.assertIn("zf_str_upper", c_code)
        self.assertIn("zf_str_lower", c_code)
        self.assertIn("zf_str_trim", c_code)

        # 3. Matematika funksiyalari
        self.assertIn("zf_pow_int", c_code)
        self.assertIn("zf_math_sqrt", c_code)
        self.assertIn("zf_math_abs", c_code)

        # 4. Fayllar tizimi (fs) funksiyalari
        self.assertIn("zf_fs_read_text", c_code)
        self.assertIn("zf_fs_write_text", c_code)
        self.assertIn("zf_fs_append_text", c_code)
        self.assertIn("zf_fs_exists", c_code)
        self.assertIn("zf_fs_remove", c_code)

        # 5. Standart IO (kiritish/chiqarish)
        self.assertIn("zf_input", c_code)
        self.assertIn("printf(", c_code)

    # ─── 7. ZAFIRA.JSON MANIFESTLI LOYIHALAR ───

    def test_project_with_zafira_json_manifest(self):
        """zafira.json manifestli loyiha papkasini to'g'ri aniqlash va paketlash."""
        proj_dir = os.path.join(self.temp_dir, "my_app")
        os.makedirs(os.path.join(proj_dir, "src"), exist_ok=True)

        manifest = {
            "name": "super_kalkulyator",
            "version": "1.0.0",
            "entry": "src/entry.zf"
        }
        with open(os.path.join(proj_dir, "zafira.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f)

        with open(os.path.join(proj_dir, "src", "entry.zf"), "w", encoding="utf-8") as f:
            f.write("""
            let x = 100
            let y = 200
            print(x + y)
            """)

        entry_file, base_dir, proj_name = resolve_entry_point(proj_dir)
        self.assertEqual(proj_name, "super_kalkulyator")
        self.assertTrue(entry_file.endswith("entry.zf"))

        res = pack_project(proj_dir, force_c_only=True)
        self.assertTrue(res['success'])
        self.assertIn("super_kalkulyator", res['output_path'])
        self.assertTrue(os.path.exists(res['output_path']))

    # ─── 8. MOCKLANGAN GCC/CLANG/TCC KOMPILYATSIYASI ───

    def test_mocked_c_compiler_binary_generation(self):
        """Mavjud C kompilyatori topilganda native binar .exe yaratilishi kerak."""
        main_zf = self._write_file("main.zf", 'print("Native Binary")\n')
        target_exe = os.path.join(self.temp_dir, "output_app.exe")

        def fake_compile(c_path, output_path, **kwargs):
            # Soxta .exe yaratish
            with open(output_path, "wb") as f:
                f.write(b"MOCK_PE_HEADER_BINARY" * 40)
            return {
                'success': True,
                'binary_path': output_path,
                'compiler': 'gcc',
                'compiler_path': 'C:\\fake\\gcc.exe',
                'size_bytes': 1024,
                'size_str': '1.00 KB'
            }

        with patch("src.packager.find_c_compiler", return_value={'name': 'gcc', 'path': 'C:\\fake\\gcc.exe'}):
            with patch("src.packager.compile_to_binary", side_effect=fake_compile):
                res = pack_project(main_zf, output_path=target_exe)
                self.assertTrue(res['success'])
                self.assertEqual(res['compiler'], 'gcc')
                self.assertEqual(res['mode'], 'c_binary')
                self.assertEqual(res['output_path'], target_exe)
                self.assertTrue(os.path.exists(target_exe))

    # ─── 9. FALLBACK REJIMI (C KOMPILYATORI BO'LMAGANDA) ───

    def test_fallback_when_c_compiler_missing(self):
        """
        C kompilyatori (gcc/clang/tcc) topilmaganda, pack_project
        csc/pyinstaller orqali .exe yoki mustaqil .c fayl yaratishi kerak.
        """
        main_zf = self._write_file("main.zf", 'print("Fallback Mode")\n')
        target_c = os.path.join(self.temp_dir, "fallback.c")

        with patch("src.packager.find_c_compiler", return_value=None):
            # 1. C fayl so'ralganda
            res_c = pack_project(main_zf, output_path=target_c, force_c_only=True)
            self.assertTrue(res_c['success'])
            self.assertEqual(res_c['mode'], 'c_source')
            self.assertTrue(os.path.exists(target_c))

            # 2. Binar so'ralganda (Windows csc mavjud bo'lsa csc_standalone, bo'lmasa c_source)
            res_bin = pack_project(main_zf)
            self.assertTrue(res_bin['success'])
            self.assertIn(res_bin['mode'], ['csc_standalone', 'pyinstaller', 'c_source'])
            self.assertTrue(os.path.exists(res_bin['output_path']))

    # ─── 10. CLI `zafira pack` BUYRUG'I ───

    def test_cli_pack_command(self):
        """zafira.py CLI pack buyrug'i to'g'ri ishlashi va parametrlar qabul qilishi kerak."""
        main_zf = self._write_file("app.zf", 'print("Salom CLI Pack")\n')
        custom_out = os.path.join(self.temp_dir, "my_custom.c")

        # zafira.pack_cli orqali chaqirish
        out = zafira.pack_cli(target=main_zf, output_path=custom_out, force_c_only=True)
        self.assertEqual(out, custom_out)
        self.assertTrue(os.path.exists(custom_out))

        # CLI subprocess orqali tekshirish
        cmd = [sys.executable, "zafira.py", "pack", main_zf, "-o", custom_out, "--c-only"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=_ROOT_DIR)
        self.assertEqual(res.returncode, 0)
        self.assertIn("[Zafira Pack] Standalone paket muvaffaqiyatli yaratildi!", res.stdout)

    # ─── 11. STRUKTURALAR VA METODLARNI BIRLASHTIRISH ───

    def test_structs_bundling(self):
        """Modul ichidagi strukturalar ham bitta AST ga to'g'ri ko'chirilishi kerak."""
        self._write_file("modellar.zf", """
        struct Nuqta {
            x: Int,
            y: Int
        }
        """)

        main_zf = self._write_file("main.zf", """
        import "./modellar.zf" as m
        let p = m.Nuqta(10, 20)
        """)

        bundled_ast, _ = bundle_project_ast(main_zf)
        c_code = generate_single_translation_unit_c(bundled_ast)
        self.assertIn("typedef struct m_Nuqta", c_code)


if __name__ == '__main__':
    unittest.main()
