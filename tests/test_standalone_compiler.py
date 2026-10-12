"""
Zafira Language - Standalone Native Binar Kompilyator Testlari
Tekshiradi:
  - Mustaqil (self-contained) C Runtime: ZfList, String, arifmetika, printf
  - Kompilyator qidirish (find_c_compiler: gcc, clang, tcc)
  - Agar GCC/Clang/TCC mavjud bo'lsa binar test (.exe) ijrosi, bo'lmasa C generatsiyasi va yo'riqnoma
  - CLI compile buyrug'i (-o, --standalone, --native)
Muallif: Jasper & Antigravity
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.lexer import Lexer
from src.parser import Parser
from src.transpiler import (
    Transpiler,
    find_c_compiler,
    compile_to_binary,
    format_file_size,
    CompilerNotFoundError,
    CompilationError,
    COMPILER_INSTALL_HELP
)
import zafira


class TestStandaloneCompiler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="zf_test_compiler_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def transpile_code(self, source: str) -> str:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        transpiler = Transpiler()
        return transpiler.transpile(program)

    def test_self_contained_c_runtime_headers_and_structures(self):
        """Transpilyatsiya qilingan C kodi barcha kerakli header va ZfList structini o'z ichiga olishi kerak"""
        code = """
        let x = 42
        print(x)
        """
        c_code = self.transpile_code(code)

        # 1. Headerlar
        self.assertIn("#include <stdio.h>", c_code)
        self.assertIn("#include <stdlib.h>", c_code)
        self.assertIn("#include <string.h>", c_code)
        self.assertIn("#include <stdint.h>", c_code)
        self.assertIn("#include <math.h>", c_code)
        self.assertIn("#include <ctype.h>", c_code)
        self.assertIn("#include <stdarg.h>", c_code)

        # 2. ZfList strukturasi va metodlari
        self.assertIn("typedef struct {", c_code)
        self.assertIn("int64_t* items;", c_code)
        self.assertIn("int64_t length;", c_code)
        self.assertIn("int64_t capacity;", c_code)
        self.assertIn("} ZfList;", c_code)
        self.assertIn("static inline ZfList* zf_list_create", c_code)
        self.assertIn("static inline void zf_list_push", c_code)
        self.assertIn("static inline int64_t zf_list_pop", c_code)
        self.assertIn("static inline int64_t zf_list_len", c_code)
        self.assertIn("static inline int64_t zf_list_get", c_code)
        self.assertIn("static inline void zf_list_set", c_code)
        self.assertIn("static inline ZfList* zf_list_new", c_code)
        self.assertIn("static inline ZfList* zf_list_from_range", c_code)
        self.assertIn("static inline char* zf_str_list", c_code)

        # 3. Satr yordamchilari
        self.assertIn("static inline char* zf_str_concat", c_code)
        self.assertIn("static inline char* zf_str_int", c_code)
        self.assertIn("static inline char* zf_str_float", c_code)
        self.assertIn("static inline char* zf_str_bool", c_code)
        self.assertIn("static inline int zf_str_eq", c_code)
        self.assertIn("static inline int zf_str_neq", c_code)
        self.assertIn("static inline char* zf_str_repeat", c_code)
        self.assertIn("static inline char* zf_str_upper", c_code)
        self.assertIn("static inline char* zf_str_lower", c_code)
        self.assertIn("static inline char* zf_str_trim", c_code)

        # 4. Arifmetika va kiritish
        self.assertIn("static inline int64_t zf_pow_int", c_code)
        self.assertIn("static inline char* zf_input", c_code)

    def test_list_operations_transpilation(self):
        """Zafira ro'yxat (list) amallari to'g'ri C funksiyalariga transpile qilinishi kerak"""
        code = """
        let sonlar = [10, 20, 30]
        sonlar.push(40)
        let birinchi = sonlar.first
        let oxirgi = sonlar.last
        let uzunlik = sonlar.len
        sonlar[0] = 99
        let element = sonlar[1]
        print(sonlar)

        for item in sonlar {
            print(item)
        }
        """
        c_code = self.transpile_code(code)

        # Ro'yxat yaratish
        self.assertIn("zf_list_new(3, (int64_t)(10), (int64_t)(20), (int64_t)(30))", c_code)
        # Push
        self.assertIn("zf_list_push(sonlar, (int64_t)(40));", c_code)
        # First & Last
        self.assertIn("zf_list_get(sonlar, 0)", c_code)
        self.assertIn("zf_list_get(sonlar, zf_list_len(sonlar) - 1)", c_code)
        # Len
        self.assertIn("zf_list_len(sonlar)", c_code)
        # Indeks bo'yicha yozish va o'qish
        self.assertIn("zf_list_set(sonlar, 0, (int64_t)(99));", c_code)
        self.assertIn("zf_list_get(sonlar, 1)", c_code)
        # Print list
        self.assertIn("zf_str_list(sonlar)", c_code)
        # List bo'yicha for tsikli
        self.assertIn("zf_list_len(sonlar)", c_code)
        self.assertIn("int64_t item = zf_list_get(sonlar, _zf_i_item);", c_code)

    def test_string_methods_and_comparisons(self):
        """Satr metodlari va solishtirish amallari to'g'ri transpile qilinishi kerak"""
        code = """
        let s1 = "  Zafira  "
        let s2 = "Zafira"
        let teng = s1 == s2
        let farq = s1 != s2
        let katta = s1.upper()
        let kichik = s1.lower()
        let toza = s1.trim()
        let takror = s2 * 3
        """
        c_code = self.transpile_code(code)

        self.assertIn("zf_str_eq(s1, s2)", c_code)
        self.assertIn("zf_str_neq(s1, s2)", c_code)
        self.assertIn("zf_str_upper(s1)", c_code)
        self.assertIn("zf_str_lower(s1)", c_code)
        self.assertIn("zf_str_trim(s1)", c_code)
        self.assertIn("zf_str_repeat(s2, 3)", c_code)

    def test_arithmetic_powers_and_functions(self):
        """Arifmetika, daraja (**) va funksiya chaqiruvlari transpile qilinishi kerak"""
        code = """
        let a = 2 ** 8
        let b = 10 % 3
        print(a + b)
        """
        c_code = self.transpile_code(code)
        self.assertIn("zf_pow_int(2, 8)", c_code)
        self.assertIn("(10 % 3)", c_code)

    def test_find_c_compiler_behavior(self):
        """find_c_compiler mavjud kompilyatorni topishi yoki None qaytarishi kerak"""
        compiler = find_c_compiler()
        if compiler:
            self.assertIn('name', compiler)
            self.assertIn('path', compiler)
            self.assertIn(compiler['name'], ['gcc', 'clang', 'tcc'])
            self.assertTrue(os.path.exists(compiler['path']))
        else:
            self.assertIsNone(compiler)

        # Mock orqali tekshirish: gcc topilganda
        with patch("shutil.which", return_value="C:\\fake\\bin\\gcc.exe"):
            mock_comp = find_c_compiler()
            self.assertIsNotNone(mock_comp)
            self.assertEqual(mock_comp['name'], 'gcc')
            self.assertEqual(mock_comp['path'], "C:\\fake\\bin\\gcc.exe")

        # Mock orqali tekshirish: tcc topilganda
        def mock_which(name):
            return "C:\\tcc\\tcc.exe" if name == 'tcc' else None

        with patch("shutil.which", side_effect=mock_which):
            with patch("os.path.isfile", return_value=False):
                mock_tcc = find_c_compiler()
                self.assertIsNotNone(mock_tcc)
                self.assertEqual(mock_tcc['name'], 'tcc')

    def test_compiler_not_found_raises_helpful_error(self):
        """Kompilyator topilmasa, aniq o'rnatish yo'riqnomasi bilan CompilerNotFoundError berishi kerak"""
        c_file = os.path.join(self.temp_dir, "test.c")
        with open(c_file, "w", encoding="utf-8") as f:
            f.write("int main() { return 0; }")

        with patch("src.transpiler.find_c_compiler", return_value=None):
            with self.assertRaises(CompilerNotFoundError) as ctx:
                compile_to_binary(c_file)
            err_msg = str(ctx.exception)
            self.assertIn("Tizimda C kompilyatori", err_msg)
            self.assertIn("GCC", err_msg)
            self.assertIn("Clang", err_msg)
            self.assertIn("TCC", err_msg)
            self.assertIn("winget install", err_msg)

    def test_mock_successful_compilation(self):
        """Kompilyator muvaffaqiyatli ishlaganda binar ma'lumotlari to'g'ri shakllanishi kerak"""
        c_file = os.path.join(self.temp_dir, "app.c")
        exe_file = os.path.join(self.temp_dir, "app.exe")
        with open(c_file, "w", encoding="utf-8") as f:
            f.write("int main() { return 0; }")

        def fake_run(cmd, **kwargs):
            # Soxta .exe yaratish
            with open(exe_file, "wb") as f:
                f.write(b"MOCK_BINARY_DATA_ZAFIRA" * 50)
            class MockResult:
                returncode = 0
                stdout = ""
                stderr = ""
            return MockResult()

        with patch("subprocess.run", side_effect=fake_run):
            with patch("src.transpiler.find_c_compiler", return_value={'name': 'gcc', 'path': 'gcc'}):
                res = compile_to_binary(c_file, output_path=exe_file)
                self.assertTrue(res['success'])
                self.assertEqual(res['binary_path'], exe_file)
                self.assertEqual(res['compiler'], 'gcc')
                self.assertGreater(res['size_bytes'], 0)
                self.assertIn("KB", res['size_str'])

    def test_format_file_size(self):
        """Fayl hajmi formatlash funksiyasini tekshirish"""
        self.assertEqual(format_file_size(500), "500 bayt")
        self.assertEqual(format_file_size(2048), "2.00 KB")
        self.assertEqual(format_file_size(1024 * 1024 * 3), "3.00 MB")

    def test_zafira_cli_compile_flags(self):
        """zafira.py compile buyrug'i CLI flaglarini (-o, --standalone, --native) qabul qilishi kerak"""
        zf_file = os.path.join(self.temp_dir, "hello.zf")
        with open(zf_file, "w", encoding="utf-8") as f:
            f.write('print("Salom, Binar Dunyo!")\n')

        custom_exe = os.path.join(self.temp_dir, "custom_prog.exe")

        # 1. compile_file funksiyasini tekshirish (-o bilan)
        with patch("src.transpiler.compile_to_binary") as mock_bin:
            mock_bin.return_value = {
                'success': True,
                'binary_path': custom_exe,
                'compiler': 'gcc',
                'compiler_path': 'C:\\fake\\gcc.exe',
                'size_bytes': 15360,
                'size_str': '15.00 KB'
            }
            out = zafira.compile_file(zf_file, output_path=custom_exe, standalone=True)
            self.assertEqual(out, custom_exe)
            mock_bin.assert_called_once()
            args, kwargs = mock_bin.call_args
            self.assertEqual(kwargs['output_path'], custom_exe)

    def test_live_or_fallback_compilation(self):
        """
        Agar tizimda real GCC/Clang/TCC mavjud bo'lsa binar .exe yaratib ishlatib ko'radi,
        mavjud bo'lmasa C generatsiyasini va xavfsiz ogohlantirishni tasdiqlaydi.
        """
        zf_file = os.path.join(self.temp_dir, "calc.zf")
        with open(zf_file, "w", encoding="utf-8") as f:
            f.write("""
seal fn qosh(a: Int, b: Int) -> Int {
    return a + b
}
let natija = qosh(100, 25)
print("Hisob: " + String(natija))
""")

        compiler = find_c_compiler()
        if compiler:
            # Haqiqiy kompilyatsiya va ishga tushirish testi
            out_exe = os.path.join(self.temp_dir, "calc.exe")
            bin_path = zafira.compile_file(zf_file, output_path=out_exe, standalone=True)
            self.assertIsNotNone(bin_path)
            self.assertTrue(os.path.exists(bin_path))
            self.assertGreater(os.path.getsize(bin_path), 0)

            # Binarni ishga tushirib chiqishini tekshirish
            run_res = subprocess.run([bin_path], capture_output=True, text=True)
            self.assertEqual(run_res.returncode, 0)
            self.assertIn("Hisob: 125", run_res.stdout)
        else:
            # Kompilyator bo'lmaganda C fayl yaratilishi va yo'riqnoma ko'rsatilishi
            c_file = zafira.transpile_file(zf_file)
            self.assertTrue(os.path.exists(c_file))
            with open(c_file, "r", encoding="utf-8") as f:
                c_content = f.read()
            self.assertIn("int64_t qosh(int64_t a, int64_t b)", c_content)
            self.assertIn("int main(int argc, char** argv)", c_content)

            # compile_file xatoliksiz None qaytarishi va ogohlantirish berishi
            res = zafira.compile_file(zf_file)
            self.assertIsNone(res)


if __name__ == '__main__':
    unittest.main()
