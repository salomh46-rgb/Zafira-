"""
Zafira Language - Pattern Matching (match ... case / =>) Unit Testlari
Muallif: Jasper & Antigravity
"""

import unittest
from src.lexer import Lexer, TokenType
from src.parser import (
    Parser, ParseError, MatchArm, MatchExpr, Wildcard,
    NumberLiteral, StringLiteral, BoolLiteral, RangeExpr, Identifier, LetStatement
)
from src.interpreter import Interpreter, ZafiraError, ZafiraUserError
from src.type_checker import TypeChecker, TypeCheckError


class TestPatternMatching(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    def run_code(self, source: str):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        return self.interpreter.run(program)

    # ─── 1. LEXER SINOVLARI ───

    def test_lexer_match_and_fat_arrow_tokens(self):
        source = "match 1 => 2"
        tokens = Lexer(source).tokenize()
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(token_types, [
            TokenType.MATCH,
            TokenType.INT,
            TokenType.FAT_ARROW,
            TokenType.INT
        ])

    def test_lexer_keyword_match(self):
        tokens = Lexer("match").tokenize()
        self.assertEqual(tokens[0].type, TokenType.MATCH)
        self.assertEqual(tokens[0].value, "match")

    def test_lexer_fat_arrow(self):
        tokens = Lexer("=>").tokenize()
        self.assertEqual(tokens[0].type, TokenType.FAT_ARROW)
        self.assertEqual(tokens[0].value, "=>")

    def test_lexer_arrow_vs_fat_arrow(self):
        tokens = Lexer("-> =>").tokenize()
        self.assertEqual(tokens[0].type, TokenType.ARROW)
        self.assertEqual(tokens[1].type, TokenType.FAT_ARROW)

    def test_lexer_full_match_snippet(self):
        source = """
        let natija = match son {
            1 => "Bir",
            3..10 => "Oraliq",
            _ => "Boshqa"
        }
        """
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertIn(TokenType.MATCH, types)
        self.assertIn(TokenType.FAT_ARROW, types)
        self.assertIn(TokenType.DOTDOT, types)

    # ─── 2. PARSER SINOVLARI ───

    def test_parser_match_expression_ast(self):
        source = """
        let natija = match son {
            1 => "Bir",
            2 => "Ikki",
            _ => "Boshqa"
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        self.assertEqual(len(program.body), 1)
        stmt = program.body[0]
        self.assertIsInstance(stmt, LetStatement)
        self.assertIsInstance(stmt.value, MatchExpr)
        match_expr = stmt.value
        self.assertIsInstance(match_expr.expr, Identifier)
        self.assertEqual(match_expr.expr.name, "son")
        self.assertEqual(len(match_expr.arms), 3)

        arm1, arm2, arm3 = match_expr.arms
        self.assertIsInstance(arm1.pattern, NumberLiteral)
        self.assertEqual(arm1.pattern.value, 1)
        self.assertIsInstance(arm1.body, StringLiteral)
        self.assertEqual(arm1.body.value, "Bir")

        self.assertIsInstance(arm2.pattern, NumberLiteral)
        self.assertEqual(arm2.pattern.value, 2)

        self.assertTrue(isinstance(arm3.pattern, Wildcard) or (isinstance(arm3.pattern, Identifier) and arm3.pattern.name == '_'))

    def test_parser_range_pattern(self):
        source = """
        match x {
            3..10 => "Oraliq",
            _ => "Tashqari"
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        stmt = program.body[0]
        self.assertIsInstance(stmt, MatchExpr)
        arm = stmt.arms[0]
        self.assertIsInstance(arm.pattern, RangeExpr)
        self.assertEqual(arm.pattern.start.value, 3)
        self.assertEqual(arm.pattern.end.value, 10)

    def test_parser_optional_case_keyword(self):
        source = """
        match x {
            case 1 => "A",
            case 2 => "B",
            case _ => "C"
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        stmt = program.body[0]
        self.assertIsInstance(stmt, MatchExpr)
        self.assertEqual(len(stmt.arms), 3)

    def test_parser_block_and_statements_in_arms(self):
        source = """
        match son {
            1 => {
                let x = 10
                print(x)
            },
            _ => print("Boshqa")
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        stmt = program.body[0]
        self.assertIsInstance(stmt, MatchExpr)
        self.assertEqual(len(stmt.arms), 2)

    # ─── 3. INTERPRETER ASOSIY SINOVLARI ───

    def test_exec_integer_match(self):
        source = """
        let son = 2
        let natija = match son {
            1 => "Bir",
            2 => "Ikki",
            3 => "Uch",
            _ => "Boshqa"
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("natija"), "Ikki")

    def test_exec_string_match(self):
        source = """
        let til = "uz"
        let salom = match til {
            "en" => "Hello",
            "ru" => "Privet",
            "uz" => "Assalomu alaykum",
            _ => "Salom"
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("salom"), "Assalomu alaykum")

    def test_exec_bool_match(self):
        source = """
        let flag = true
        let holat = match flag {
            true => "Faol",
            false => "Nofaol"
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("holat"), "Faol")

    def test_exec_wildcard_fallback(self):
        source = """
        let x = 999
        let res = match x {
            1 => "Bir",
            2 => "Ikki",
            _ => "Standart"
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("res"), "Standart")

    def test_exec_range_match_boundaries(self):
        source = """
        let a = 3
        let b = 5
        let c = 9
        let d = 10
        let r_a = match a { 3..10 => "Oraliqda", _ => "Oraliqda emas" }
        let r_b = match b { 3..10 => "Oraliqda", _ => "Oraliqda emas" }
        let r_c = match c { 3..10 => "Oraliqda", _ => "Oraliqda emas" }
        let r_d = match d { 3..10 => "Oraliqda", _ => "Oraliqda emas" }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("r_a"), "Oraliqda")
        self.assertEqual(self.interpreter.global_env.get("r_b"), "Oraliqda")
        self.assertEqual(self.interpreter.global_env.get("r_c"), "Oraliqda")
        self.assertEqual(self.interpreter.global_env.get("r_d"), "Oraliqda emas")

    def test_exec_existing_variable_match(self):
        source = """
        let kutilgan = 42
        let x = 42
        let y = 99
        let res1 = match x { kutilgan => "Teng", _ => "Farqli" }
        let res2 = match y { kutilgan => "Teng", _ => "Farqli" }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("res1"), "Teng")
        self.assertEqual(self.interpreter.global_env.get("res2"), "Farqli")

    def test_exec_variable_binding(self):
        source = """
        let kiruvchi = 15
        let natija = match kiruvchi {
            1 => 100,
            qiymat => qiymat * 2
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("natija"), 30)

    def test_exec_statement_match_with_assignment(self):
        source = """
        let maqom = 0
        match 2 {
            1 => maqom = 10,
            2 => maqom = 20,
            _ => maqom = 30
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("maqom"), 20)

    def test_exec_first_match_wins(self):
        source = """
        let x = 5
        let res = match x {
            1..10 => "Birinchi oraliq",
            5 => "Aniq besh",
            _ => "Boshqa"
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("res"), "Birinchi oraliq")

    def test_exec_match_inside_function_with_return(self):
        source = """
        fn bahola(ball) {
            return match ball {
                5 => "A",
                4 => "B",
                3 => "C",
                _ => "F"
            }
        }
        let b1 = bahola(5)
        let b2 = bahola(2)
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("b1"), "A")
        self.assertEqual(self.interpreter.global_env.get("b2"), "F")

    def test_exec_nested_match(self):
        source = """
        let tur = "meva"
        let nom = "olma"
        let natija = match tur {
            "meva" => match nom {
                "olma" => "Shirin olma",
                _ => "Boshqa meva"
            },
            _ => "Boshqa narsa"
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("natija"), "Shirin olma")

    def test_exec_throw_inside_arm(self):
        source = """
        let xato_xabar = ""
        try {
            match 0 {
                0 => throw "Nol taqiqlangan!",
                _ => "Yaxshi"
            }
        } catch (e) {
            xato_xabar = e
        }
        """
        self.run_code(source)
        self.assertEqual(self.interpreter.global_env.get("xato_xabar"), "Nol taqiqlangan!")

    def test_exec_no_match_returns_none(self):
        source = """
        let res = match 100 {
            1 => "Bir",
            2 => "Ikki"
        }
        """
        self.run_code(source)
        self.assertIsNone(self.interpreter.global_env.get("res"))

    # ─── 4. TYPE CHECKER SINOVLARI ───

    def test_type_checker_seal_function_match_success(self):
        source = """
        seal fn toifa(ball: Int) -> String {
            return match ball {
                5 => "Alo",
                4 => "Yaxshi",
                3 => "Qoniqarli",
                _ => "Qoniqarsiz"
            }
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        checker = TypeChecker()
        checker.check(program)

    def test_type_checker_seal_function_match_type_mismatch(self):
        source = """
        seal fn hisob(son: Int) -> Int {
            return match son {
                1 => 10,
                _ => "Matn qaytishi mumkin emas"
            }
        }
        """
        program = Parser(Lexer(source).tokenize()).parse()
        checker = TypeChecker()
        with self.assertRaises(TypeCheckError):
            checker.check(program)


if __name__ == '__main__':
    unittest.main()
