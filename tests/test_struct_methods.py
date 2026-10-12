"""
Zafira Language - Struct Metodlari (impl bloklari va self) Testlari
Muallif: Jasper & Antigravity
"""

import os
import shutil
import tempfile
import unittest

from src.lexer import Lexer, TokenType, KEYWORDS
from src.parser import Parser, ParseError, ImplBlock, StructDef, FunctionDef
from src.interpreter import Interpreter, ZafiraError, ZafiraStruct, ZafiraBoundMethod
from src.type_checker import TypeChecker, TypeCheckError


class TestLexerStructMethods(unittest.TestCase):
    """Lexer impl tokeni va kalit so'zi testlari."""

    def test_keywords_contains_impl(self):
        self.assertIn('impl', KEYWORDS)
        self.assertEqual(KEYWORDS['impl'], TokenType.IMPL)

    def test_impl_tokenization(self):
        code = "impl Odam { fn salom(self) { return 1 } }"
        tokens = Lexer(code).tokenize()
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(token_types[0], TokenType.IMPL)
        self.assertEqual(token_types[1], TokenType.IDENT)
        self.assertEqual(token_types[2], TokenType.LBRACE)


class TestParserStructMethods(unittest.TestCase):
    """Parser impl bloki AST tugunlari testlari."""

    def test_parse_single_impl_block(self):
        code = """
        struct Odam {
            ism: String,
            yosh: Int
        }

        impl Odam {
            fn salom(self) {
                return "Salom, " + self.ism
            }
        }
        """
        program = Parser(Lexer(code).tokenize()).parse()
        self.assertEqual(len(program.body), 2)
        self.assertIsInstance(program.body[0], StructDef)
        self.assertIsInstance(program.body[1], ImplBlock)

        impl_node: ImplBlock = program.body[1]
        self.assertEqual(impl_node.struct_name, "Odam")
        self.assertEqual(len(impl_node.methods), 1)
        self.assertEqual(impl_node.methods[0].name, "salom")
        self.assertEqual(impl_node.methods[0].params[0][0], "self")

    def test_parse_multi_method_impl_block(self):
        code = """
        struct Nuqta { x: Int, y: Int }

        impl Nuqta {
            fn get_x(self) { return self.x }
            fn get_y(self) { return self.y }
            fn sur(self, dx: Int, dy: Int) {
                self.x = self.x + dx
                self.y = self.y + dy
                return self
            }
        }
        """
        program = Parser(Lexer(code).tokenize()).parse()
        impl_node = program.body[1]
        self.assertIsInstance(impl_node, ImplBlock)
        self.assertEqual(impl_node.struct_name, "Nuqta")
        self.assertEqual(len(impl_node.methods), 3)
        method_names = [m.name for m in impl_node.methods]
        self.assertEqual(method_names, ["get_x", "get_y", "sur"])

    def test_parse_multiple_impl_blocks_for_same_struct(self):
        code = """
        struct Foydalanuvchi { ism: String }

        impl Foydalanuvchi {
            fn salom(self) { return "Salom" }
        }

        impl Foydalanuvchi {
            fn xayr(self) { return "Xayr" }
        }
        """
        program = Parser(Lexer(code).tokenize()).parse()
        self.assertEqual(len(program.body), 3)
        self.assertIsInstance(program.body[1], ImplBlock)
        self.assertIsInstance(program.body[2], ImplBlock)
        self.assertEqual(program.body[1].struct_name, "Foydalanuvchi")
        self.assertEqual(program.body[2].struct_name, "Foydalanuvchi")

    def test_parse_invalid_impl_content(self):
        code = """
        struct Odam { ism: String }
        impl Odam {
            let x = 10
        }
        """
        tokens = Lexer(code).tokenize()
        parser = Parser(tokens)
        with self.assertRaises(ParseError):
            parser.parse()


class TestInterpreterStructMethods(unittest.TestCase):
    """Interpreter struct metodlari bajarilishi testlari."""

    def setUp(self):
        self.interp = Interpreter()

    def tearDown(self):
        self.interp.close()

    def run_code(self, code: str):
        tokens = Lexer(code).tokenize()
        program = Parser(tokens).parse()
        return self.interp.run(program)

    def test_basic_method_call(self):
        code = """
        struct Odam {
            ism: String,
            yosh: Int
        }

        impl Odam {
            fn salom(self) {
                return "Salom, mening ismim " + self.ism
            }
        }

        let ali = Odam("Ali", 20)
        let xabar = ali.salom()
        """
        self.run_code(code)
        self.assertEqual(self.interp.global_env.get("xabar"), "Salom, mening ismim Ali")

    def test_method_mutates_self_field(self):
        code = """
        struct Odam {
            ism: String,
            yosh: Int
        }

        impl Odam {
            fn yosh_oshir(self, yil: Int) {
                self.yosh = self.yosh + yil
                return self.yosh
            }
        }

        let vali = Odam("Vali", 25)
        let yangi_yosh = vali.yosh_oshir(5)
        let bevosita_yosh = vali.yosh
        """
        self.run_code(code)
        self.assertEqual(self.interp.global_env.get("yangi_yosh"), 30)
        self.assertEqual(self.interp.global_env.get("bevosita_yosh"), 30)
        obj: ZafiraStruct = self.interp.global_env.get("vali")
        self.assertEqual(obj.fields["yosh"], 30)

    def test_multiple_instances_isolation(self):
        code = """
        struct Hisob { balans: Int }

        impl Hisob {
            fn qosh(self, summa: Int) {
                self.balans = self.balans + summa
                return self.balans
            }
        }

        let h1 = Hisob(100)
        let h2 = Hisob(500)

        h1.qosh(50)
        let b1 = h1.balans
        let b2 = h2.balans
        """
        self.run_code(code)
        self.assertEqual(self.interp.global_env.get("b1"), 150)
        self.assertEqual(self.interp.global_env.get("b2"), 500)

    def test_method_calling_another_method(self):
        code = """
        struct Robot { nom: String }

        impl Robot {
            fn signal(self) {
                return "BEEP"
            }

            fn salom(self) {
                return self.nom + " deydi: " + self.signal()
            }
        }

        let r = Robot("R2D2")
        let natija = r.salom()
        """
        self.run_code(code)
        self.assertEqual(self.interp.global_env.get("natija"), "R2D2 deydi: BEEP")

    def test_method_returning_self_chaining(self):
        code = """
        struct Sanagich { qiymat: Int }

        impl Sanagich {
            fn bir_qosh(self) {
                self.qiymat = self.qiymat + 1
                return self
            }
        }

        let c = Sanagich(0)
        c.bir_qosh().bir_qosh().bir_qosh()
        let q = c.qiymat
        """
        self.run_code(code)
        self.assertEqual(self.interp.global_env.get("q"), 3)

    def test_bound_method_passed_as_value(self):
        code = """
        struct Salomchi { ism: String }

        impl Salomchi {
            fn ayt(self) {
                return "Salom " + self.ism
            }
        }

        let s = Salomchi("Zafira")
        let funksiya = s.ayt
        let natija = funksiya()
        """
        self.run_code(code)
        self.assertEqual(self.interp.global_env.get("natija"), "Salom Zafira")

    def test_multiple_impl_blocks_execution(self):
        code = """
        struct Kalkulyator { asosiy: Int }

        impl Kalkulyator {
            fn qosh(self, x: Int) {
                self.asosiy = self.asosiy + x
                return self.asosiy
            }
        }

        impl Kalkulyator {
            fn kopaytir(self, x: Int) {
                self.asosiy = self.asosiy * x
                return self.asosiy
            }
        }

        let k = Kalkulyator(10)
        let r1 = k.qosh(5)
        let r2 = k.kopaytir(2)
        """
        self.run_code(code)
        self.assertEqual(self.interp.global_env.get("r1"), 15)
        self.assertEqual(self.interp.global_env.get("r2"), 30)

    def test_nonexistent_method_raises_error(self):
        code = """
        struct Sinov { a: Int }
        let s = Sinov(1)
        s.yoq_metod()
        """
        with self.assertRaises(ZafiraError) as ctx:
            self.run_code(code)
        self.assertIn("maydoni yoki metodi yo'q", str(ctx.exception))

    def test_async_struct_method(self):
        code = """
        struct Tarmoq { manzil: String }

        impl Tarmoq {
            async fn sorov(self) {
                return "Javob: " + self.manzil
            }
        }

        let t = Tarmoq("https://zafira.org")
        let vazifa = t.sorov()
        let javob = await vazifa
        """
        self.run_code(code)
        self.assertEqual(self.interp.global_env.get("javob"), "Javob: https://zafira.org")


class TestTypeCheckerStructMethods(unittest.TestCase):
    """TypeChecker struct metodlari statik tekshiruvi testlari."""

    def check_code(self, code: str):
        tokens = Lexer(code).tokenize()
        program = Parser(tokens).parse()
        checker = TypeChecker()
        checker.check(program)

    def test_type_checker_valid_impl(self):
        code = """
        struct Odam {
            ism: String,
            yosh: Int
        }

        impl Odam {
            fn salom(self) {
                return "Salom, " + self.ism
            }

            seal fn yosh_oshir(self, yil: Int) -> Int {
                self.yosh = self.yosh + yil
                return self.yosh
            }
        }

        let o = Odam("Jasper", 25)
        let s = o.salom()
        let y = o.yosh_oshir(2)
        """
        self.check_code(code)

    def test_type_checker_nonexistent_struct_error(self):
        code = """
        impl MavjudEmas {
            fn salom(self) {
                return 1
            }
        }
        """
        with self.assertRaises(TypeCheckError) as ctx:
            self.check_code(code)
        self.assertIn("nomli struct topilmadi", str(ctx.exception))

    def test_type_checker_nonexistent_method_error(self):
        code = """
        struct Odam { ism: String }
        let o = Odam("Ali")
        let x = o.noma_lum_metod
        """
        with self.assertRaises(TypeCheckError) as ctx:
            self.check_code(code)
        self.assertIn("maydoni yoki metodi mavjud emas", str(ctx.exception))

    def test_type_checker_seal_method_arg_type_mismatch(self):
        code = """
        struct Odam { yosh: Int }

        impl Odam {
            seal fn oshir(self, yil: Int) -> Int {
                return self.yosh + yil
            }
        }

        let o = Odam(20)
        let res = o.oshir("uch")
        """
        with self.assertRaises(TypeCheckError) as ctx:
            self.check_code(code)
        self.assertIn("parametri uchun String o'rniga Int kutilgan", str(ctx.exception))

    def test_type_checker_seal_method_return_type_mismatch(self):
        code = """
        struct Odam { yosh: Int }

        impl Odam {
            seal fn get_str(self) -> String {
                return self.yosh
            }
        }
        """
        with self.assertRaises(TypeCheckError) as ctx:
            self.check_code(code)
        self.assertIn("qaytarilyapti, String kutilgan", str(ctx.exception))


class TestModuleStructMethods(unittest.TestCase):
    """Boshqa moduldan import qilingan struct metodlari testlari."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="zafira_impl_mod_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_struct_methods_in_imported_module(self):
        mod_path = os.path.join(self.temp_dir, "geometriya.zf")
        with open(mod_path, "w", encoding="utf-8") as f:
            f.write("""
            struct Shakl { kenglik: Int, balandlik: Int }

            impl Shakl {
                fn maydon(self) {
                    return self.kenglik * self.balandlik
                }
            }
            """)

        main_path = os.path.join(self.temp_dir, "main.zf")
        code = """
        import "./geometriya.zf" as geom
        let s = geom.Shakl(5, 10)
        let m = s.maydon()
        """
        interp = Interpreter(current_file=main_path)
        try:
            prog = Parser(Lexer(code).tokenize()).parse()
            interp.run(prog)
            self.assertEqual(interp.global_env.get("m"), 50)
        finally:
            interp.close()


if __name__ == "__main__":
    unittest.main()
