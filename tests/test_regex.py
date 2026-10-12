"""
Zafira Language - std.regex Moduli Testlari
std.regex ning barcha funksiyalari, xatolik holatlari va Zafira tili integratsiyasini 100% to'liq sinovdan o'tkazish.
"""

import unittest
from src.interpreter import Interpreter, ZafiraError, ZafiraList, Environment
from src.lexer import Lexer
from src.parser import Parser
from src.stdlib import load_stdlib_module, STDLIB_MODULES
from src.std_regex import (
    _regex_test,
    _regex_find,
    _regex_find_all,
    _regex_replace,
    _regex_replace_all,
    _regex_split,
    _regex_is_valid,
    create_regex_module,
)
from src.type_checker import TypeChecker, TypeCheckError


class TestStdRegexUnit(unittest.TestCase):
    """std.regex modulining Python birlik (unit) testlari."""

    def test_regex_test_basic(self):
        # Moslik mavjud
        self.assertTrue(_regex_test(r"\d+", "Alisher 1995 yilda tug'ilgan"))
        # Moslik mavjud emas
        self.assertFalse(_regex_test(r"\d+", "Faqat harflar"))
        # To'liq moslik (^...$)
        self.assertTrue(_regex_test(r"^[a-z]+$", "salom"))
        self.assertFalse(_regex_test(r"^[a-z]+$", "salom123"))
        # Case insensitive
        self.assertTrue(_regex_test(r"(?i)zafira", "ZAFIRA tili"))

    def test_regex_test_email(self):
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        self.assertTrue(_regex_test(email_pattern, "user@example.com"))
        self.assertTrue(_regex_test(email_pattern, "admin.support@company.org"))
        self.assertFalse(_regex_test(email_pattern, "invalid-email"))
        self.assertFalse(_regex_test(email_pattern, "@missing-user.com"))

    def test_regex_test_errors(self):
        # Noto'g'ri regex sintaksisi
        with self.assertRaises(ZafiraError):
            _regex_test(r"[a-", "matn")
        with self.assertRaises(ZafiraError):
            _regex_test(r"(", "matn")
        # Noto'g'ri tiplar
        with self.assertRaises(ZafiraError):
            _regex_test(None, "matn")
        with self.assertRaises(ZafiraError):
            _regex_test(r"\d+", None)
        with self.assertRaises(ZafiraError):
            _regex_test(123, "matn")
        with self.assertRaises(ZafiraError):
            _regex_test(r"\d+", 456)

    def test_regex_find_basic(self):
        # Birinchi mos kelgan qism
        res = _regex_find(r"\d+", "Narxi: 25000 so'm, chegirma: 5000 so'm")
        self.assertEqual(res, "25000")
        # Moslik topilmasa -> None (Zafira null)
        self.assertIsNone(_regex_find(r"\d+", "Raqam yo'q"))
        # Guruhlar bilan
        res2 = _regex_find(r"([A-Z]+)-(\d+)", "Hujjat KOD-777 tasdiqlandi")
        self.assertEqual(res2, "KOD-777")

    def test_regex_find_errors(self):
        with self.assertRaises(ZafiraError):
            _regex_find(r"[0-9", "test")
        with self.assertRaises(ZafiraError):
            _regex_find(None, "test")
        with self.assertRaises(ZafiraError):
            _regex_find(r"\d+", None)

    def test_regex_find_all_basic(self):
        # Barcha mosliklar
        res = _regex_find_all(r"\d+", "10, 20 va 30 raqamlari")
        self.assertIsInstance(res, ZafiraList)
        self.assertEqual(res.items, ["10", "20", "30"])
        # Moslik topilmasa -> bo'sh ro'yxat
        res_empty = _regex_find_all(r"\d+", "Hech qanday raqam yo'q")
        self.assertIsInstance(res_empty, ZafiraList)
        self.assertEqual(res_empty.items, [])
        # Guruhlar bilan butun moslikni olish
        res_groups = _regex_find_all(r"#\w+", "Teglar: #zafira #code #ai")
        self.assertEqual(res_groups.items, ["#zafira", "#code", "#ai"])

    def test_regex_find_all_errors(self):
        with self.assertRaises(ZafiraError):
            _regex_find_all(r"(?", "test")
        with self.assertRaises(ZafiraError):
            _regex_find_all(None, "test")
        with self.assertRaises(ZafiraError):
            _regex_find_all(r"\w+", None)

    def test_regex_replace_basic(self):
        # Faqat birinchi moslikni almashtirish
        text = "ID 101 va ID 102"
        res = _regex_replace(r"\d+", "999", text)
        self.assertEqual(res, "ID 999 va ID 102")
        # Moslik bo'lmasa matn o'zgarmaydi
        res_same = _regex_replace(r"\d+", "999", "Raqam yo'q")
        self.assertEqual(res_same, "Raqam yo'q")

    def test_regex_replace_errors(self):
        with self.assertRaises(ZafiraError):
            _regex_replace(r"[a-", "X", "abc")
        with self.assertRaises(ZafiraError):
            _regex_replace(None, "X", "abc")
        with self.assertRaises(ZafiraError):
            _regex_replace(r"\d+", None, "abc")
        with self.assertRaises(ZafiraError):
            _regex_replace(r"\d+", "X", None)

    def test_regex_replace_all_basic(self):
        # Barcha mosliklarni almashtirish
        text = "Telefon: 111-222 yoki 333-444"
        res = _regex_replace_all(r"\d{3}-\d{3}", "[YASHIRIN]", text)
        self.assertEqual(res, "Telefon: [YASHIRIN] yoki [YASHIRIN]")
        # Bo'sh joylarni bitta probelga almashtirish
        multi_space = "Salom    dunyo   zafira"
        res_space = _regex_replace_all(r"\s+", " ", multi_space)
        self.assertEqual(res_space, "Salom dunyo zafira")

    def test_regex_replace_all_errors(self):
        with self.assertRaises(ZafiraError):
            _regex_replace_all(r"[0-9", "X", "123")
        with self.assertRaises(ZafiraError):
            _regex_replace_all(None, "X", "123")
        with self.assertRaises(ZafiraError):
            _regex_replace_all(r"\d+", None, "123")
        with self.assertRaises(ZafiraError):
            _regex_replace_all(r"\d+", "X", None)

    def test_regex_split_basic(self):
        # Vergul va nuqta-vergul bo'yicha bo'lish
        text = "olma,nok;anor, shaftoli"
        res = _regex_split(r"[,;]\s*", text)
        self.assertIsInstance(res, ZafiraList)
        self.assertEqual(res.items, ["olma", "nok", "anor", "shaftoli"])
        # Bo'sh joylar bo'yicha bo'lish
        words = _regex_split(r"\s+", "bitta ikkita uchta")
        self.assertEqual(words.items, ["bitta", "ikkita", "uchta"])
        # Moslik topilmasa -> 1 elementli ro'yxat
        single = _regex_split(r"\d+", "faqat_matn")
        self.assertEqual(single.items, ["faqat_matn"])

    def test_regex_split_errors(self):
        with self.assertRaises(ZafiraError):
            _regex_split(r"*", "test")
        with self.assertRaises(ZafiraError):
            _regex_split(None, "test")
        with self.assertRaises(ZafiraError):
            _regex_split(r"\s+", None)

    def test_regex_is_valid(self):
        # To'g'ri regexlar
        self.assertTrue(_regex_is_valid(r"^[0-9]+$"))
        self.assertTrue(_regex_is_valid(r"[a-zA-Z_]\w*"))
        self.assertTrue(_regex_is_valid(r"(?P<nomi>\w+)"))
        self.assertTrue(_regex_is_valid(r""))
        # Noto'g'ri regexlar
        self.assertFalse(_regex_is_valid(r"[0-9"))
        self.assertFalse(_regex_is_valid(r"("))
        self.assertFalse(_regex_is_valid(r"*"))
        self.assertFalse(_regex_is_valid(r"+"))
        self.assertFalse(_regex_is_valid(r"?"))
        # Satr bo'lmagan qiymatlar
        self.assertFalse(_regex_is_valid(None))
        self.assertFalse(_regex_is_valid(123))
        self.assertFalse(_regex_is_valid([]))

    def test_create_regex_module_structure(self):
        mod = create_regex_module()
        self.assertEqual(mod.name, 'regex')
        expected_fields = {'test', 'find', 'find_all', 'replace', 'replace_all', 'split', 'is_valid'}
        self.assertTrue(expected_fields.issubset(set(mod.fields.keys())))


class TestStdRegexZafiraIntegration(unittest.TestCase):
    """std.regex modulining Zafira tili (Interpreter va TypeChecker) integratsiya testlari."""

    def setUp(self):
        self.interpreter = Interpreter()

    def run_code(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check(program)
        return self.interpreter.run(program)

    def test_stdlib_registration(self):
        self.assertIn('regex', STDLIB_MODULES)
        env = Environment()
        load_stdlib_module('std.regex', env)
        self.assertTrue(env.has('regex'))
        # Alias bilan
        env2 = Environment()
        load_stdlib_module('std.regex', env2, alias='re')
        self.assertTrue(env2.has('re'))

    def test_zafira_regex_execution_all_functions(self):
        code = r"""
        import std.regex

        let test_ok = regex.test("^[0-9]+$", "12345")
        let test_fail = regex.test("^[0-9]+$", "12a45")

        let find_res = regex.find("\\d+", "Id raqam: 88899 berildi")
        let find_null = regex.find("\\d+", "Raqam yo'q")

        let all_matches = regex.find_all("\\d+", "A: 10, B: 20, C: 30")
        let count_matches = all_matches.len

        let repl_one = regex.replace("\\d+", "X", "10 va 20")
        let repl_all = regex.replace_all("\\d+", "X", "10 va 20")

        let parts = regex.split("[,;]\\s*", "a, b; c, d")
        let parts_count = parts.len

        let valid_pat = regex.is_valid("^[a-z]+$")
        let invalid_pat = regex.is_valid("[a-z")
        """
        self.run_code(code)
        env = self.interpreter.global_env

        self.assertTrue(env.get('test_ok'))
        self.assertFalse(env.get('test_fail'))
        self.assertEqual(env.get('find_res'), "88899")
        self.assertIsNone(env.get('find_null'))
        self.assertEqual(env.get('count_matches'), 3)
        self.assertEqual(env.get('all_matches').items, ["10", "20", "30"])
        self.assertEqual(env.get('repl_one'), "X va 20")
        self.assertEqual(env.get('repl_all'), "X va X")
        self.assertEqual(env.get('parts_count'), 4)
        self.assertEqual(env.get('parts').items, ["a", "b", "c", "d"])
        self.assertTrue(env.get('valid_pat'))
        self.assertFalse(env.get('invalid_pat'))

    def test_zafira_regex_alias_import(self):
        code = r"""
        import std.regex as re

        let is_num = re.test("^[0-9]+$", "999")
        let first = re.find("\\d+", "kod: 777")
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('is_num'))
        self.assertEqual(env.get('first'), "777")

    def test_zafira_regex_try_catch_error(self):
        code = """
        import std.regex

        let xatolik_ushlandi = false
        try {
            regex.test("[noto'g'ri", "matn")
        } catch (e) {
            xatolik_ushlandi = true
        }
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('xatolik_ushlandi'))

    def test_type_checker_regex_types(self):
        code = r"""
        import std.regex

        seal fn check_types() -> Bool {
            let b1: Bool = regex.test("^a", "abc")
            let b2: Bool = regex.is_valid(".*")
            let f: Any = regex.find("\\w+", "salom")
            let r: String = regex.replace("a", "b", "cat")
            let ra: String = regex.replace_all("a", "b", "banana")
            let l1: List = regex.find_all("\\d+", "1 2 3")
            let l2: List = regex.split(",", "a,b,c")
            return b1 and b2
        }

        let natija = check_types()
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('natija'))

    def test_type_checker_regex_invalid_member(self):
        code = """
        import std.regex
        regex.noma_lum_funksiya()
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        with self.assertRaises(TypeCheckError) as ctx:
            checker.check(program)
        self.assertIn("std.regex modulida 'noma_lum_funksiya' funksiyasi mavjud emas!", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
