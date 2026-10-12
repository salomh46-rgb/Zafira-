"""
Zafira Language - C Transpiler Testlari
"""

import unittest
from src.lexer import Lexer
from src.parser import Parser
from src.transpiler import Transpiler


class TestTranspiler(unittest.TestCase):
    def transpile_code(self, source: str) -> str:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        transpiler = Transpiler()
        return transpiler.transpile(program)

    def test_seal_fn(self):
        code = """
        seal fn qo'sh(a: Int, b: Int) -> Int {
            return a + b
        }
        """
        c_code = self.transpile_code(code)
        self.assertIn("int64_t qo_sh(int64_t a, int64_t b);", c_code)
        self.assertIn("int64_t qo_sh(int64_t a, int64_t b) {", c_code)
        self.assertIn("return (a + b);", c_code)

    def test_draft_fn(self):
        code = """
        draft fn salom(ism) {
            return ism
        }
        """
        c_code = self.transpile_code(code)
        self.assertIn("ZfAny salom(ZfAny ism);", c_code)
        self.assertIn("ZfAny salom(ZfAny ism) {", c_code)

    def test_let_and_const(self):
        code = """
        let x: Int = 10
        const PI: Float = 3.14
        """
        c_code = self.transpile_code(code)
        self.assertIn("int64_t x = 10;", c_code)
        self.assertIn("const double PI = 3.14;", c_code)

    def test_for_loop(self):
        code = """
        for i in 0..10 {
            print(i)
        }
        """
        c_code = self.transpile_code(code)
        self.assertIn("for (int64_t i = 0; i < 10; i++) {", c_code)
        self.assertIn('printf("%lld\\n", (long long)(i));', c_code)

    def test_if_else(self):
        code = """
        let x = 5
        if x > 0 {
            print("musbat")
        } else {
            print("manfiy")
        }
        """
        c_code = self.transpile_code(code)
        self.assertIn("if ((x > 0)) {", c_code)
        self.assertIn("} else {", c_code)

    def test_string_concat_and_print(self):
        code = """
        let ism = "Jasper"
        print("Salom, " + ism)
        """
        c_code = self.transpile_code(code)
        self.assertIn('zf_str_concat("Salom, ", ism)', c_code)

    def test_compile_test_file(self):
        with open("examples/compile_test.zf", encoding="utf-8") as f:
            code = f.read()
        c_code = self.transpile_code(code)
        self.assertIn("int64_t qo_sh(int64_t a, int64_t b)", c_code)
        self.assertIn("int64_t faktorial(int64_t n)", c_code)
        self.assertIn("int main(int argc, char** argv)", c_code)
        self.assertIn("qo_sh(10, 20)", c_code)
        self.assertIn("faktorial(7)", c_code)


if __name__ == '__main__':
    unittest.main()
