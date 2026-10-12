"""
Zafira Language - Lokal Ko'p Faylli Modullar Tizimi (Local Modules) Sinovlari
Tests for `import "./fayl.zf"`, relative resolution, circular import protection,
module caching, scope isolation, and struct/function exports.
"""

import os
import shutil
import tempfile
import unittest

from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter, ZafiraError, ZafiraStruct
from src.type_checker import TypeChecker
from zafira import execute_source


class TestLocalModules(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="zafira_test_mods_")
        self.interpreter = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))

    def tearDown(self):
        if hasattr(self, 'interpreter') and self.interpreter:
            self.interpreter.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_file(self, rel_path: str, content: str) -> str:
        full_path = os.path.join(self.temp_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    def _run_source(self, source: str, file_name: str = "main.zf"):
        main_path = os.path.join(self.temp_dir, file_name)
        lexer = Lexer(source)
        parser = Parser(lexer.tokenize())
        program = parser.parse()
        interp = Interpreter(current_file=main_path)
        try:
            return interp.run(program)
        finally:
            interp.close()

    # ─── 1. BAZAVIY LOKAL MODUL IMPORTI ───

    def test_import_with_extension_and_alias(self):
        self._write_file("matematika.zf", """
        fn kvadrat(x) { return x * x }
        fn kub(x) { return x * x * x }
        """)
        code = """
        import "./matematika.zf" as mat
        let kv = mat.kvadrat(5)
        let kb = mat.kub(3)
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            self.assertEqual(interp.global_env.get("kv"), 25)
            self.assertEqual(interp.global_env.get("kb"), 27)
        finally:
            interp.close()

    def test_import_without_extension(self):
        self._write_file("matematika.zf", """
        fn kvadrat(x) { return x * x }
        """)
        code = """
        import "./matematika" as mat
        let natija = mat.kvadrat(7)
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            self.assertEqual(interp.global_env.get("natija"), 49)
        finally:
            interp.close()

    def test_import_default_name_without_alias(self):
        self._write_file("hisob.zf", """
        fn qosh(a, b) { return a + b }
        let doimiy = 42
        """)
        code = """
        import "./hisob.zf"
        let yigindi = hisob.qosh(10, 20)
        let qiymat = hisob.doimiy
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            self.assertEqual(interp.global_env.get("yigindi"), 30)
            self.assertEqual(interp.global_env.get("qiymat"), 42)
            self.assertIsInstance(interp.global_env.get("hisob"), ZafiraStruct)
        finally:
            interp.close()

    # ─── 2. EXAMPLES/MULTI_FILE ASOSIY TESTI ───

    def test_examples_multi_file_integration(self):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        asosiy_zf = os.path.join(root_dir, "examples", "multi_file", "asosiy.zf")
        matematika_zf = os.path.join(root_dir, "examples", "multi_file", "matematika.zf")

        self.assertTrue(os.path.exists(asosiy_zf), "examples/multi_file/asosiy.zf mavjud bo'lishi kerak")
        self.assertTrue(os.path.exists(matematika_zf), "examples/multi_file/matematika.zf mavjud bo'lishi kerak")

        with open(asosiy_zf, "r", encoding="utf-8") as f:
            source = f.read()

        # TypeChecker va Interpreter orqali xatosiz bajarilishi kerak
        interp = Interpreter(current_file=asosiy_zf)
        try:
            prog = Parser(Lexer(source).tokenize()).parse()
            tc = TypeChecker(current_file=asosiy_zf)
            tc.check(prog)
            interp.run(prog)
            mat = interp.global_env.get("mat")
            self.assertIsInstance(mat, ZafiraStruct)
            self.assertEqual(mat.fields["kvadrat"](5), 25)
            self.assertEqual(mat.fields["kub"](3), 27)
        finally:
            interp.close()

    # ─── 3. SIKLIK IMPORTDAN HIMOYALANISH (CIRCULAR IMPORT PROTECTION) ───

    def test_circular_imports(self):
        self._write_file("a.zf", """
        import "./b.zf" as b
        fn func_a() { return "A_SALOM" }
        fn call_b() { return b.func_b() }
        """)
        self._write_file("b.zf", """
        import "./a.zf" as a
        fn func_b() { return "B_SALOM" }
        fn call_a() { return a.func_a() }
        """)
        code = """
        import "./a.zf" as a
        import "./b.zf" as b
        let res_a = a.func_a()
        let res_b = b.func_b()
        let cross_b = a.call_b()
        let cross_a = b.call_a()
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            self.assertEqual(interp.global_env.get("res_a"), "A_SALOM")
            self.assertEqual(interp.global_env.get("res_b"), "B_SALOM")
            self.assertEqual(interp.global_env.get("cross_b"), "B_SALOM")
            self.assertEqual(interp.global_env.get("cross_a"), "A_SALOM")
        finally:
            interp.close()

    # ─── 4. MODUL KESHI (CACHE REUSE) ───

    def test_module_cache_reuse(self):
        self._write_file("state.zf", """
        let counter = 100
        fn get_val() { return counter }
        """)
        code = """
        import "./state.zf" as s1
        import "./state.zf" as s2
        let v1 = s1.get_val()
        let v2 = s2.get_val()
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            # Ikkala import ham bitta keshdagi modul obyektiga murojaat qiladi
            s1 = interp.global_env.get("s1")
            s2 = interp.global_env.get("s2")
            self.assertIs(s1, s2)
            self.assertEqual(interp.global_env.get("v1"), 100)
            self.assertEqual(interp.global_env.get("v2"), 100)
        finally:
            interp.close()

    # ─── 5. STRUCT VA FUNKSIYALARNING EXPORTI ───

    def test_struct_exported_from_module(self):
        self._write_file("geometriya.zf", """
        struct Nuqta { x: Int, y: Int }
        fn yangi_nuqta(a, b) { return Nuqta(a, b) }
        """)
        code = """
        import "./geometriya.zf" as geom
        let p1 = geom.Nuqta(10, 20)
        let p2 = geom.yangi_nuqta(30, 40)
        let x1 = p1.x
        let y2 = p2.y
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            self.assertEqual(interp.global_env.get("x1"), 10)
            self.assertEqual(interp.global_env.get("y2"), 40)
        finally:
            interp.close()

    # ─── 6. MUHITLAR IZOLYATSIYASI (SCOPE ISOLATION) ───

    def test_module_scope_isolation(self):
        self._write_file("izolyatsiya.zf", """
        let maxfiy = "parol123"
        fn test_caller_access() { return caller_secret }
        """)

        # 1. Chaqiruvchi o'zgaruvchisi modulga sizib kirmasligi kerak
        code1 = """
        let caller_secret = "hacker"
        import "./izolyatsiya.zf" as izo
        izo.test_caller_access()
        """
        interp1 = Interpreter(current_file=os.path.join(self.temp_dir, "main1.zf"))
        try:
            prog1 = Parser(Lexer(code1).tokenize()).parse()
            with self.assertRaises(ZafiraError):
                interp1.run(prog1)
        finally:
            interp1.close()

        # 2. Modul ichidagi o'zgaruvchi chaqiruvchining global maydoniga to'g'ridan-to'g'ri tushmasligi kerak
        code2 = """
        import "./izolyatsiya.zf" as izo
        let ko_rish = maxfiy
        """
        interp2 = Interpreter(current_file=os.path.join(self.temp_dir, "main2.zf"))
        try:
            prog2 = Parser(Lexer(code2).tokenize()).parse()
            with self.assertRaises(ZafiraError):
                interp2.run(prog2)
        finally:
            interp2.close()

    # ─── 7. ICHMA-ICH PAPKALAR VA NISBIY YO'LLAR (NESTED RELATIVE) ───

    def test_nested_subfolder_relative_import(self):
        self._write_file("common/utils.zf", """
        fn salom() { return "Salom Zafira" }
        """)
        self._write_file("features/calc/service.zf", """
        import "../../common/utils.zf" as u
        fn ishla() { return u.salom() + "!" }
        """)
        code = """
        import "./features/calc/service.zf" as srv
        let xabar = srv.ishla()
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            self.assertEqual(interp.global_env.get("xabar"), "Salom Zafira!")
        finally:
            interp.close()

    # ─── 8. MAVJUD BO'LMAGAN FAYL XATOSI (ERROR HANDLING) ───

    def test_nonexistent_file_raises_error(self):
        code = """
        import "./mavjud_bolmagan_fayl.zf" as yoq
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            with self.assertRaises(ZafiraError) as ctx:
                interp.run(prog)
            self.assertIn("Modul fayli topilmadi", str(ctx.exception))
        finally:
            interp.close()

    # ─── 9. STANDART BUILTINLAR MODUL ICHIDA ISHLASHI ───

    def test_builtins_work_inside_module(self):
        self._write_file("util_tools.zf", """
        fn matn_uzunligi(s) {
            return len(s)
        }
        fn satrga_aylantir(son) {
            return String(son)
        }
        """)
        code = """
        import "./util_tools.zf" as tools
        let l = tools.matn_uzunligi("Zafira")
        let s = tools.satrga_aylantir(12345)
        """
        interp = Interpreter(current_file=os.path.join(self.temp_dir, "main.zf"))
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            self.assertEqual(interp.global_env.get("l"), 6)
            self.assertEqual(interp.global_env.get("s"), "12345")
        finally:
            interp.close()


if __name__ == '__main__':
    unittest.main()
