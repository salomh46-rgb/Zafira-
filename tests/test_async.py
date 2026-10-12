"""
Zafira Language - Asinxron Dasturlash (async / await) Testlari
Lekser, Parser, Interpreter va Type Checker bo'yicha to'liq test to'plami.
"""

import time
import unittest
from src.lexer import Lexer, TokenType
from src.parser import Parser, FunctionDef, AwaitExpr, LetStatement
from src.interpreter import Interpreter, ZafiraError, ZafiraTask
from src.type_checker import TypeChecker, TypeCheckError


class TestAsyncAwait(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    def tearDown(self):
        self.interpreter.close()

    def run_code(self, source: str):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        return self.interpreter.run(program)

    # ─── 1. LEKSER SINOVLARI ───

    def test_lexer_async_await_keywords(self):
        source = "async fn yukla() { await ma_lumot() }"
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens]
        self.assertIn(TokenType.ASYNC, types)
        self.assertIn(TokenType.AWAIT, types)
        self.assertEqual(tokens[0].type, TokenType.ASYNC)

    def test_lexer_identifiers_starting_with_async(self):
        source = "let async_var = 10 let awaiting_data = 20"
        tokens = Lexer(source).tokenize()
        ident_tokens = [t for t in tokens if t.type == TokenType.IDENT]
        names = [t.value for t in ident_tokens]
        self.assertIn("async_var", names)
        self.assertIn("awaiting_data", names)

    # ─── 2. PARSER SINOVLARI ───

    def test_parser_async_function_def(self):
        source = "async fn yukla_data(id) { return id * 2 }"
        program = Parser(Lexer(source).tokenize()).parse()
        self.assertEqual(len(program.body), 1)
        fn_node = program.body[0]
        self.assertIsInstance(fn_node, FunctionDef)
        self.assertEqual(fn_node.name, "yukla_data")
        self.assertTrue(fn_node.is_async)

    def test_parser_seal_async_function(self):
        source = "seal async fn hisobla(x: Int) -> Int { return x + 1 }"
        program = Parser(Lexer(source).tokenize()).parse()
        fn_node = program.body[0]
        self.assertIsInstance(fn_node, FunctionDef)
        self.assertEqual(fn_node.name, "hisobla")
        self.assertEqual(fn_node.mode, "seal")
        self.assertTrue(fn_node.is_async)
        self.assertEqual(fn_node.return_type, "Int")

    def test_parser_await_expr(self):
        source = "let res = await yukla_data(42)"
        program = Parser(Lexer(source).tokenize()).parse()
        stmt = program.body[0]
        self.assertIsInstance(stmt, LetStatement)
        self.assertIsInstance(stmt.value, AwaitExpr)

    def test_parser_anonymous_async_function(self):
        source = "let f = async fn(x) { return x + 1 }"
        program = Parser(Lexer(source).tokenize()).parse()
        stmt = program.body[0]
        self.assertIsInstance(stmt.value, FunctionDef)
        self.assertTrue(stmt.value.is_async)

    # ─── 3. INTERPRETER ASOSIY SINOVLARI ───

    def test_basic_async_await_execution(self):
        code = """
        async fn salom() {
            return "Salom, Zafira!"
        }
        let xabar = await salom()
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("xabar"), "Salom, Zafira!")

    def test_async_function_returns_task_object(self):
        code = """
        async fn yukla(id) {
            return "Element_" + String(id)
        }
        let task = yukla(100)
        let t_type = type(task)
        let natija = await task
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("t_type"), "Task")
        self.assertEqual(self.interpreter.global_env.get("natija"), "Element_100")

    def test_task_object_done_method(self):
        code = """
        async fn tez_vazifa() {
            return 777
        }
        let t = tez_vazifa()
        let res = await t
        let tugadimi = t.done()
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("res"), 777)
        self.assertTrue(self.interpreter.global_env.get("tugadimi"))

    def test_nested_async_calls(self):
        code = """
        async fn birlamchi() {
            return 10
        }
        async fn ikkilamchi(x) {
            let a = await birlamchi()
            return a + x
        }
        let javob = await ikkilamchi(25)
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("javob"), 35)

    def test_await_plain_value(self):
        code = """
        let oddiy = await 999
        let satr = await "salom"
        """
        self.run_code(code)
        self.assertEqual(self.interpreter.global_env.get("oddiy"), 999)
        self.assertEqual(self.interpreter.global_env.get("satr"), "salom")

    # ─── 4. PARALLEL ASINXRON BAJARILISH ISBOTI ───

    def test_parallel_async_execution_speed(self):
        code = """
        async fn yukla_data(id) {
            sleep(0.08)
            return "Data_" + String(id)
        }
        let t1 = yukla_data(1)
        let t2 = yukla_data(2)
        let r1 = await t1
        let r2 = await t2
        """
        start_time = time.time()
        self.run_code(code)
        elapsed = time.time() - start_time

        self.assertEqual(self.interpreter.global_env.get("r1"), "Data_1")
        self.assertEqual(self.interpreter.global_env.get("r2"), "Data_2")
        # Ketma-ket bo'lsa kamida 0.16s ketardi. Parallel bo'lgani sababli < 0.14s da yakunlanadi
        self.assertLess(elapsed, 0.15, f"Vazifalar parallel bajarilmadi! Ketgan vaqt: {elapsed:.3f}s")

    # ─── 5. XATOLIKLAR BILAN ISHLASH ───

    def test_async_exception_propagation_on_await(self):
        code = """
        async fn xato_qil() {
            let x = 10 / 0
            return x
        }
        let t = xato_qil()
        let r = await t
        """
        with self.assertRaises(ZafiraError) as ctx:
            self.run_code(code)
        self.assertIn("Nolga bo'lish mumkin emas", str(ctx.exception))

    def test_async_where_clause_failure(self):
        code = """
        async fn musbat_bolsin(x) where x > 0 {
            return x * 10
        }
        let t = musbat_bolsin(-5)
        """
        with self.assertRaises(ZafiraError) as ctx:
            self.run_code(code)
        self.assertIn("where", str(ctx.exception))

    # ─── 6. TYPE CHECKER SINOVLARI ───

    def test_type_checker_seal_async_function(self):
        source = """
        seal async fn hisobla(x: Int, y: Int) -> Int {
            return x + y
        }
        let res: Int = await hisobla(10, 20)
        """
        lexer = Lexer(source)
        program = Parser(lexer.tokenize()).parse()
        checker = TypeChecker()
        checker.check(program)  # Xatoliksiz o'tishi kerak

    def test_type_checker_seal_async_arg_type_mismatch(self):
        source = """
        seal async fn kvadrat(x: Int) -> Int {
            return x * x
        }
        let res = await kvadrat("matn")
        """
        lexer = Lexer(source)
        program = Parser(lexer.tokenize()).parse()
        checker = TypeChecker()
        with self.assertRaises(TypeCheckError):
            checker.check(program)

    def test_type_checker_task_type_annotation(self):
        source = """
        async fn yukla(id: Int) -> String {
            return "data"
        }
        let t: Task = yukla(1)
        """
        lexer = Lexer(source)
        program = Parser(lexer.tokenize()).parse()
        checker = TypeChecker()
        checker.check(program)  # Task tipi muvaffaqiyatli tanilishi kerak


if __name__ == '__main__':
    unittest.main()
