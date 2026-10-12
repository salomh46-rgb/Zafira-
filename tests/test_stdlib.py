"""
Zafira Language - Standart Kutubxona (stdlib) Testlari
std.math, std.string, std.list, std.io modullarini 100% to'liq sinovdan o'tkazish
"""

import unittest
import io
import sys
import math
from src.interpreter import Interpreter, Environment, ZafiraList, ZafiraError
from src.parser import Parser
from src.lexer import Lexer
from src.stdlib import load_stdlib_module, STDLIB_MODULES


class TestStdlib(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    def run_code(self, source: str):
        lexer = Lexer(source)
        parser = Parser(lexer.tokenize())
        program = parser.parse()
        return self.interpreter.run(program)

    # ─── 1. STD.MATH SINOVLARI ───

    def test_std_math_functions(self):
        code = """
        import std.math
        let s = math.sqrt(25.0)
        let p = math.pow(2, 8)
        let a = math.abs(-42)
        let fl = math.floor(3.7)
        let ce = math.ceil(3.2)
        let rd = math.round(3.567, 2)
        let mn = math.min(10, 5, 20)
        let mx = math.max(10, 5, 20)
        let lg = math.log(math.E)
        let sn = math.sin(0)
        let cs = math.cos(0)
        let tn = math.tan(0)
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('s'), 5.0)
        self.assertEqual(env.get('p'), 256.0)
        self.assertEqual(env.get('a'), 42)
        self.assertEqual(env.get('fl'), 3)
        self.assertEqual(env.get('ce'), 4)
        self.assertEqual(env.get('rd'), 3.57)
        self.assertEqual(env.get('mn'), 5)
        self.assertEqual(env.get('mx'), 20)
        self.assertAlmostEqual(env.get('lg'), 1.0)
        self.assertAlmostEqual(env.get('sn'), 0.0)
        self.assertAlmostEqual(env.get('cs'), 1.0)
        self.assertAlmostEqual(env.get('tn'), 0.0)

    def test_std_math_constants(self):
        code = """
        import std.math
        let pi = math.PI
        let e = math.E
        let inf = math.INF
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertAlmostEqual(env.get('pi'), math.pi)
        self.assertAlmostEqual(env.get('e'), math.e)
        self.assertEqual(env.get('inf'), math.inf)

    # ─── 2. STD.STRING SINOVLARI ───

    def test_std_string_functions(self):
        code = """
        import std.string
        let up = string.upper("salom")
        let lw = string.lower("DUNYO")
        let tr = string.trim("   zafira   ")
        let sp = string.split("one,two,three", ",")
        let jn = string.join(["a", "b", "c"], "-")
        let rp = string.replace("hello world", "world", "zafira")
        let ct = string.contains("alisher navoiy", "navoiy")
        let sw = string.starts_with("javascript", "java")
        let ew = string.ends_with("archive.tar.gz", ".gz")
        let rep = string.repeat("abc", 3)
        let rev = string.reverse("salom")
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('up'), "SALOM")
        self.assertEqual(env.get('lw'), "dunyo")
        self.assertEqual(env.get('tr'), "zafira")
        self.assertEqual(env.get('sp').items, ["one", "two", "three"])
        self.assertEqual(env.get('jn'), "a-b-c")
        self.assertEqual(env.get('rp'), "hello zafira")
        self.assertTrue(env.get('ct'))
        self.assertTrue(env.get('sw'))
        self.assertTrue(env.get('ew'))
        self.assertEqual(env.get('rep'), "abcabcabc")
        self.assertEqual(env.get('rev'), "molas")

    # ─── 3. STD.LIST SINOVLARI ───

    def test_std_list_functions(self):
        code = """
        import std.list
        let nums = [5, 2, 8, 1, 9]
        let sorted = list.sort(nums)
        let rev = list.reverse(nums)
        let sm = list.sum(nums)
        let mx = list.max(nums)
        let mn = list.min(nums)
        let has_eight = list.contains(nums, 8)
        let uniq = list.unique([1, 2, 2, 3, 1, 4])
        let flat = list.flatten([[1, 2], [3, 4], 5])
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('sorted').items, [1, 2, 5, 8, 9])
        self.assertEqual(env.get('rev').items, [9, 1, 8, 2, 5])
        self.assertEqual(env.get('sm'), 25)
        self.assertEqual(env.get('mx'), 9)
        self.assertEqual(env.get('mn'), 1)
        self.assertTrue(env.get('has_eight'))
        self.assertEqual(env.get('uniq').items, [1, 2, 3, 4])
        self.assertEqual(env.get('flat').items, [1, 2, 3, 4, 5])

    def test_std_list_higher_order_functions(self):
        code = """
        import std.list
        let nums = [1, 2, 3, 4, 5, 6]
        let evens = list.filter(nums, fn(x) { return x % 2 == 0 })
        let doubled = list.map(nums, fn(x) { return x * 2 })
        let sum_all = list.reduce(nums, fn(acc, x) { return acc + x }, 0)
        let found = list.find(nums, fn(x) { return x > 4 })
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('evens').items, [2, 4, 6])
        self.assertEqual(env.get('doubled').items, [2, 4, 6, 8, 10, 12])
        self.assertEqual(env.get('sum_all'), 21)
        self.assertEqual(env.get('found'), 5)

    # ─── 4. STD.IO SINOVLARI ───

    def test_std_io_functions(self):
        code = """
        import std.io
        io.print("A")
        io.print("B")
        io.println("C")
        io.write("D")
        """
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            self.run_code(code)
            out = buf.getvalue()
        finally:
            sys.stdout = old_stdout

        self.assertIn("ABC\nD", out)

    # ─── 5. STD.AI MODULI YUKLANISHI ───

    def test_std_ai_module_loading(self):
        code = """
        import std.ai
        let t = ai.tensor([1, 2, 3])
        let d = ai.device()
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertIsNotNone(env.get('ai'))
        self.assertEqual(env.get('d'), 'cpu')

    # ─── 6. STD.JSON VA STD.NET MODULLARI YUKLANISHI ───

    def test_std_json_module_loading(self):
        code = """
        import std.json
        let parsed = json.parse("{\\\"hello\\\": \\\"world\\\"}")
        let dumped = json.stringify(parsed)
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertIsNotNone(env.get('json'))
        self.assertEqual(env.get('parsed').fields['hello'], 'world')

    def test_std_net_module_loading(self):
        code = """
        import std.net
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertIsNotNone(env.get('net'))

    # ─── 7. XATOLIKLAR VA CHEKKA HOLATLAR ───

    def test_unknown_stdlib_module(self):
        env = Environment()
        with self.assertRaises(ZafiraError):
            load_stdlib_module('std.unknwn', env)


if __name__ == '__main__':
    unittest.main()
