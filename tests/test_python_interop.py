"""
Zafira Language - Python Interop Tests
"""

import unittest
import io
import sys
from src.interpreter import Interpreter, Environment
from src.parser import Parser
from src.lexer import Lexer
from src.python_interop import PythonInterop, PythonObjectWrapper, PythonCallableWrapper


class TestPythonInterop(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    def run_code(self, source: str):
        lexer = Lexer(source)
        parser = Parser(lexer.tokenize())
        program = parser.parse()
        return self.interpreter.run(program)

    def test_import_math(self):
        env = Environment()
        ok = PythonInterop.import_module('py.math', env)
        self.assertTrue(ok)
        math_mod = env.get('math')
        self.assertIsInstance(math_mod, PythonObjectWrapper)
        self.assertAlmostEqual(math_mod.fields['pi'], 3.141592653589793)
        sqrt_fn = math_mod.fields['sqrt']
        self.assertIsInstance(sqrt_fn, PythonCallableWrapper)
        self.assertEqual(sqrt_fn(144.0), 12.0)

    def test_import_random(self):
        env = Environment()
        ok = PythonInterop.import_module('py.random', env)
        self.assertTrue(ok)
        random_mod = env.get('random')
        randint_fn = random_mod.fields['randint']
        num = randint_fn(1, 100)
        self.assertTrue(1 <= num <= 100)

    def test_import_numpy_and_alias(self):
        try:
            import numpy
        except ImportError:
            self.skipTest("numpy o'rnatilmagan (ixtiyoriy)")
        env = Environment()
        ok = PythonInterop.import_module('py.numpy', env)
        self.assertTrue(ok)
        self.assertIsNotNone(env.get('numpy'))
        self.assertIsNotNone(env.get('np'))

    def test_missing_module_error_message(self):
        env = Environment()
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            ok = PythonInterop.import_module('py.torch', env)
            output = buf.getvalue()
        finally:
            sys.stdout = old_stdout

        self.assertFalse(ok)
        self.assertIn("pip install torch", output)

    def test_full_script_execution(self):
        code = """
        import py.math
        let pi = math.pi
        let sqrt144 = math.sqrt(144.0)

        import py.random
        let r = random.randint(5, 5)
        """
        self.run_code(code)
        self.assertAlmostEqual(self.interpreter.global_env.get('pi'), 3.141592653589793)
        self.assertEqual(self.interpreter.global_env.get('sqrt144'), 12.0)
        self.assertEqual(self.interpreter.global_env.get('r'), 5)


if __name__ == '__main__':
    unittest.main()
