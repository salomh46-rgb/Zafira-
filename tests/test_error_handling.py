"""
Zafira Language - Error Handling (try / catch / throw / finally) Unit Testlari
Muallif: Jasper & Antigravity
"""

import unittest
from src.lexer import Lexer, TokenType
from src.parser import Parser, ParseError, TryStatement, ThrowStatement
from src.interpreter import Interpreter, ZafiraUserError, ZafiraError
from src.type_checker import TypeChecker, TypeCheckError


class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    def run_code(self, source: str):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        return self.interpreter.run(program)

    # ─── 1. LEXER SINOVLARI ───

    def test_lexer_tokens(self):
        source = "try catch throw finally"
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(types, [
            TokenType.TRY,
            TokenType.CATCH,
            TokenType.THROW,
            TokenType.FINALLY
        ])

    def test_lexer_with_code(self):
        source = 'try { throw "xatodir"; } catch (e) { } finally { }'
        tokens = Lexer(source).tokenize()
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertIn(TokenType.TRY, token_types)
        self.assertIn(TokenType.THROW, token_types)
        self.assertIn(TokenType.CATCH, token_types)
        self.assertIn(TokenType.FINALLY, token_types)

    # ─── 2. PARSER SINOVLARI ───

    def test_parser_full_try_catch_finally(self):
        source = """
        try {
            throw "Xato"
        } catch (err) {
            let x = 1
        } finally {
            let y = 2
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        self.assertEqual(len(program.body), 1)
        stmt = program.body[0]
        self.assertIsInstance(stmt, TryStatement)
        self.assertEqual(stmt.catch_param, "err")
        self.assertIsNotNone(stmt.catch_block)
        self.assertIsNotNone(stmt.finally_block)
        self.assertIsInstance(stmt.try_block[0], ThrowStatement)

    def test_parser_catch_without_param(self):
        source = """
        try {
            throw 404
        } catch {
            let handled = true
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        stmt = program.body[0]
        self.assertIsInstance(stmt, TryStatement)
        self.assertIsNone(stmt.catch_param)
        self.assertIsNotNone(stmt.catch_block)
        self.assertIsNone(stmt.finally_block)

    def test_parser_try_finally_only(self):
        source = """
        try {
            let a = 10
        } finally {
            let b = 20
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        stmt = program.body[0]
        self.assertIsInstance(stmt, TryStatement)
        self.assertIsNone(stmt.catch_param)
        self.assertIsNone(stmt.catch_block)
        self.assertIsNotNone(stmt.finally_block)

    def test_parser_try_without_catch_or_finally_raises(self):
        source = """
        try {
            let a = 1
        }
        """
        with self.assertRaises(ParseError):
            Parser(Lexer(source).tokenize()).parse()

    # ─── 3. INTERPRETER: ODDIY THROW VA CATCH ───

    def test_throw_and_catch_string(self):
        code = """
        let natija = ""
        try {
            throw "Bizning xato"
        } catch (e) {
            natija = e
        }
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("natija"), "Bizning xato")

    def test_throw_and_catch_number(self):
        code = """
        let kod = 0
        try {
            throw 404
        } catch (err) {
            kod = err
        }
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("kod"), 404)

    def test_catch_without_param(self):
        code = """
        let flag = false
        try {
            throw "xatolik"
        } catch {
            flag = true
        }
        """
        self.run_code(code)
        self.assertTrue(self.interpreter.global_env.get("flag"))

    def test_no_error_skips_catch(self):
        code = """
        let catch_ishladi = false
        let try_ishladi = false
        try {
            try_ishladi = true
        } catch (e) {
            catch_ishladi = true
        }
        """
        self.run_code(code)
        self.assertTrue(self.interpreter.global_env.get("try_ishladi"))
        self.assertFalse(self.interpreter.global_env.get("catch_ishladi"))

    # ─── 4. INTERPRETER: FINALLY BLOKI ───

    def test_finally_runs_on_success(self):
        code = """
        let log = []
        try {
            log.push("try")
        } catch (e) {
            log.push("catch")
        } finally {
            log.push("finally")
        }
        """
        self.run_code(code)
        items = self.interpreter.global_env.get("log").items
        self.assertEqual(items, ["try", "finally"])

    def test_finally_runs_on_caught_error(self):
        code = """
        let log = []
        try {
            log.push("try")
            throw "xato"
        } catch (e) {
            log.push("catch: " + e)
        } finally {
            log.push("finally")
        }
        """
        self.run_code(code)
        items = self.interpreter.global_env.get("log").items
        self.assertEqual(items, ["try", "catch: xato", "finally"])

    def test_finally_runs_on_uncaught_error(self):
        code = """
        let log = []
        try {
            log.push("try")
            throw "tutib olinmagan xato"
        } finally {
            log.push("finally")
        }
        """
        with self.assertRaises(ZafiraUserError) as ctx:
            self.run_code(code)
        self.assertEqual(ctx.exception.value, "tutib olinmagan xato")
        items = self.interpreter.global_env.get("log").items
        self.assertEqual(items, ["try", "finally"])

    # ─── 5. INTERPRETER: TIZIMLI XATOLIKLAR (NOLGA BO'LISH VA BOSHQALAR) ───

    def test_catch_system_zero_division(self):
        code = """
        let tutildi = false
        let xato_xabari = ""
        try {
            let x = 100 / 0
        } catch (e) {
            tutildi = true
            xato_xabari = e
        }
        """
        self.run_code(code)
        self.assertTrue(self.interpreter.global_env.get("tutildi"))
        self.assertIn("Nolga bo'lish", self.interpreter.global_env.get("xato_xabari"))

    def test_catch_system_index_out_of_bounds(self):
        code = """
        let ushlandi = false
        try {
            let r = [1, 2, 3]
            let val = r[99]
        } catch (e) {
            ushlandi = true
        }
        """
        self.run_code(code)
        self.assertTrue(self.interpreter.global_env.get("ushlandi"))

    def test_catch_system_const_reassignment(self):
        code = """
        const CHEKLOV = 50
        let ushlandi = false
        try {
            CHEKLOV = 100
        } catch (e) {
            ushlandi = true
        }
        """
        self.run_code(code)
        self.assertTrue(self.interpreter.global_env.get("ushlandi"))

    # ─── 6. INTERPRETER: FUNKSIYALAR, RETURN VA QAYTA THROW ───

    def test_throw_inside_function_call(self):
        code = """
        fn tekshir(yosh) {
            if yosh < 18 {
                throw "Yosh yetarli emas!"
            }
            return "Xush kelibsiz"
        }

        let natija = ""
        try {
            natija = tekshir(15)
        } catch (xato) {
            natija = "Xato: " + xato
        }
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("natija"), "Xato: Yosh yetarli emas!")

    def test_return_inside_try_executes_finally(self):
        code = """
        let finally_bajarildi = false
        fn test_fn() {
            try {
                return 42
            } finally {
                finally_bajarildi = true
            }
        }
        let res = test_fn()
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("res"), 42)
        self.assertTrue(self.interpreter.global_env.get("finally_bajarildi"))

    def test_return_inside_catch_executes_finally(self):
        code = """
        let finally_bajarildi = false
        fn test_fn() {
            try {
                throw "muammo"
            } catch (e) {
                return 99
            } finally {
                finally_bajarildi = true
            }
        }
        let res = test_fn()
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("res"), 99)
        self.assertTrue(self.interpreter.global_env.get("finally_bajarildi"))

    def test_rethrow_in_catch(self):
        code = """
        let log = []
        try {
            try {
                throw "dastlabki xato"
            } catch (e) {
                log.push("ichki: " + e)
                throw "ikkinchi xato"
            } finally {
                log.push("ichki finally")
            }
        } catch (e2) {
            log.push("tashqi: " + e2)
        }
        """
        self.run_code(code)
        items = self.interpreter.global_env.get("log").items
        self.assertEqual(items, [
            "ichki: dastlabki xato",
            "ichki finally",
            "tashqi: ikkinchi xato"
        ])

    def test_nested_try_catch(self):
        code = """
        let yigindi = 0
        try {
            try {
                throw 10
            } catch (x) {
                yigindi = yigindi + x
            }
            throw 20
        } catch (y) {
            yigindi = yigindi + y
        }
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("yigindi"), 30)

    # ─── 7. TYPE CHECKER SINOVLARI ───

    def test_type_checker_try_statement(self):
        source = """
        seal fn hisobla(x: Int) -> Int {
            try {
                if x < 0 {
                    throw "Manfiy son kiritildi"
                }
                return x * 2
            } catch (e) {
                return 0
            } finally {
                let toza = true
            }
        }
        let javob = hisobla(5)
        """
        program = Parser(Lexer(source).tokenize()).parse()
        checker = TypeChecker()
        checker.check(program)  # Xatolik bermasligi kerak

    def test_type_checker_undeclared_in_throw_fails(self):
        source = """
        seal fn xato() -> Null {
            throw noma_lum_ozgaruvchi
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        checker = TypeChecker()
        with self.assertRaises(TypeCheckError):
            checker.check(program)


if __name__ == "__main__":
    unittest.main()
