"""
Zafira Language - std.ffi Moduli Testlari
C FFI (Foreign Function Interface) kutubxonasining barcha imkoniyatlari,
C turlari (c_int, c_float, c_string, c_bool), libc/msvcrt/kernel32 yuklash,
funksiyalarni chaqirish, xatoliklarni ushlash va TypeChecker integratsiyasi.
"""

import os
import sys
import unittest
from typing import Any

from src.interpreter import Interpreter, ZafiraError, ZafiraList, ZafiraStruct, Environment
from src.lexer import Lexer
from src.parser import Parser
from src.stdlib import load_stdlib_module, STDLIB_MODULES
from src.std_ffi import (
    CValue,
    FfiLibrary,
    _ffi_load,
    _ffi_libc,
    _ffi_c_int,
    _ffi_c_float,
    _ffi_c_double,
    _ffi_c_string,
    _ffi_c_bool,
    _ffi_call_global,
    _ffi_has_symbol_global,
    create_ffi_module,
)
from src.type_checker import TypeChecker, TypeCheckError


class TestStdFfiPythonUnit(unittest.TestCase):
    """std.ffi modulining Python birlik (unit) testlari."""

    def test_load_standard_libc(self):
        # libc / c / None yuklash
        lib1 = _ffi_load("libc")
        self.assertIsInstance(lib1, FfiLibrary)
        self.assertEqual(lib1.fields['name'], "libc")

        lib2 = _ffi_load("c")
        self.assertIsInstance(lib2, FfiLibrary)

        lib3 = _ffi_libc()
        self.assertIsInstance(lib3, FfiLibrary)

        lib_default = _ffi_load(None)
        self.assertIsInstance(lib_default, FfiLibrary)

    def test_load_non_existent_library(self):
        # Mavjud bo'lmagan kutubxona ZafiraError chiqarishi kerak
        with self.assertRaises(ZafiraError) as ctx:
            _ffi_load("mutlaqo_mavjud_bolmagan_kutubxona_12345")
        self.assertIn("FFI xatosi", str(ctx.exception))

    def test_load_invalid_argument_type(self):
        # lib_name satr bo'lmasa xato
        with self.assertRaises(ZafiraError) as ctx:
            _ffi_load(12345)
        self.assertIn("satr (String) bo'lishi kerak", str(ctx.exception))

    def test_has_symbol(self):
        libc = _ffi_libc()
        has_symbol_fn = libc.fields['has_symbol']

        # Standart C funksiyalari mavjud bo'lishi kerak
        self.assertTrue(has_symbol_fn("abs"))
        self.assertTrue(has_symbol_fn("puts"))
        self.assertTrue(has_symbol_fn("sqrt"))

        # Mavjud bo'lmagan simvol False qaytarishi kerak
        self.assertFalse(has_symbol_fn("fake_c_symbol_xyz987"))
        self.assertFalse(has_symbol_fn(""))

        # Noto'g'ri tur berilganda ZafiraError
        with self.assertRaises(ZafiraError):
            has_symbol_fn(999)

    def test_c_value_wrappers(self):
        # c_int
        c_i = _ffi_c_int(42)
        self.assertIsInstance(c_i, CValue)
        self.assertEqual(c_i.fields['type'], 'int')
        self.assertEqual(c_i.fields['value'], 42)

        # c_int noto'g'ri qiymat
        with self.assertRaises(ZafiraError):
            _ffi_c_int("bu_son_emas")

        # c_float
        c_f = _ffi_c_float(3.14)
        self.assertIsInstance(c_f, CValue)
        self.assertEqual(c_f.fields['type'], 'float')
        self.assertAlmostEqual(c_f.fields['value'], 3.14, places=2)

        with self.assertRaises(ZafiraError):
            _ffi_c_float("haqiqiy_emas")

        # c_double
        c_d = _ffi_c_double(2.718)
        self.assertIsInstance(c_d, CValue)
        self.assertEqual(c_d.fields['type'], 'double')

        # c_string
        c_s = _ffi_c_string("Salom")
        self.assertIsInstance(c_s, CValue)
        self.assertEqual(c_s.fields['type'], 'string')
        self.assertEqual(c_s.fields['value'], "Salom")

        # c_string None va bytes
        c_s_null = _ffi_c_string(None)
        self.assertIsNone(c_s_null.fields['value'])
        c_s_bytes = _ffi_c_string(b"TestBytes")
        self.assertEqual(c_s_bytes.fields['value'], "TestBytes")

        # c_bool
        c_b = _ffi_c_bool(True)
        self.assertEqual(c_b.fields['value'], True)

    def test_call_c_math_functions(self):
        libc = _ffi_libc()
        call_fn = libc.fields['call']

        # abs oddiy int bilan
        res_abs = call_fn("abs", [-88], "int")
        self.assertEqual(res_abs, 88)

        # abs c_int bilan
        ci = _ffi_c_int(-42)
        res_abs_c = call_fn("abs", [ci], "int")
        self.assertEqual(res_abs_c, 42)

        # sqrt oddiy float bilan
        res_sqrt = call_fn("sqrt", [81.0], "float")
        self.assertEqual(res_sqrt, 9.0)

        # sqrt c_float bilan
        cf = _ffi_c_float(25.0)
        res_sqrt_c = call_fn("sqrt", [cf], "float")
        self.assertEqual(res_sqrt_c, 5.0)

        # pow
        res_pow = call_fn("pow", [3.0, 3.0], "float")
        self.assertEqual(res_pow, 27.0)

    def test_call_c_string_functions(self):
        libc = _ffi_libc()
        call_fn = libc.fields['call']

        # strlen
        res_len = call_fn("strlen", ["Antigravity FFI"], "int")
        self.assertEqual(res_len, 15)

        # strlen c_string bilan
        cs = _ffi_c_string("Zafira")
        res_len_c = call_fn("strlen", [cs], "int")
        self.assertEqual(res_len_c, 6)

        # puts
        res_puts = call_fn("puts", ["Unit test puts() text"])
        self.assertIsInstance(res_puts, int)

    def test_call_errors(self):
        libc = _ffi_libc()
        call_fn = libc.fields['call']

        # Funksiya nomi satr bo'lmasa
        with self.assertRaises(ZafiraError):
            call_fn(12345)

        # Funksiya topilmasa
        with self.assertRaises(ZafiraError) as ctx:
            call_fn("mutlaqo_topilmas_funksiya_xyz")
        self.assertIn("topilmadi", str(ctx.exception))

        # Qaytarish turi noma'lum bo'lsa
        with self.assertRaises(ZafiraError) as ctx:
            call_fn("abs", [1], "noma_lum_tur_xyz")
        self.assertIn("Noma'lum qaytarish turi", str(ctx.exception))

    def test_global_ffi_helpers(self):
        libc = _ffi_libc()

        # ffi.has_symbol(lib, name)
        self.assertTrue(_ffi_has_symbol_global(libc, "abs"))
        self.assertFalse(_ffi_has_symbol_global(libc, "fake_xyz"))

        # ffi.call(lib, "abs", [-15])
        self.assertEqual(_ffi_call_global(libc, "abs", [-15]), 15)

        # Noto'g'ri lib bilan xato
        with self.assertRaises(ZafiraError):
            _ffi_has_symbol_global("not_a_lib", "abs")
        with self.assertRaises(ZafiraError):
            _ffi_call_global("not_a_lib", "abs", [-1])


class TestStdFfiModuleRegistration(unittest.TestCase):
    """std.ffi modulining stdlib ro'yxatiga ulanishi testlari."""

    def test_module_registered_in_stdlib(self):
        self.assertIn('ffi', STDLIB_MODULES)
        mod = STDLIB_MODULES['ffi']
        self.assertEqual(mod.type_name, 'std.ffi')
        self.assertIn('load', mod.fields)
        self.assertIn('c_int', mod.fields)
        self.assertIn('c_float', mod.fields)
        self.assertIn('c_string', mod.fields)
        self.assertIn('has_symbol', mod.fields)
        self.assertIn('call', mod.fields)

    def test_load_stdlib_module(self):
        env = Environment()
        load_stdlib_module('std.ffi', env)
        self.assertTrue(env.has('ffi'))
        self.assertEqual(env.get('ffi').type_name, 'std.ffi')

    def test_load_stdlib_module_alias(self):
        env = Environment()
        load_stdlib_module('std.ffi', env, alias='cffi')
        self.assertTrue(env.has('cffi'))
        self.assertEqual(env.get('cffi').type_name, 'std.ffi')


class TestTypeCheckerFfi(unittest.TestCase):
    """std.ffi modulining statik tip tekshiruvi (TypeChecker) testlari."""

    def check_code(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        return checker.check(program)

    def test_type_checker_valid_ffi_calls(self):
        code = """
        import std.ffi

        seal fn test_ffi() -> Int {
            let lib = ffi.load("libc")
            let ok: Bool = lib.has_symbol("abs")
            let abs_val: Int = lib.call("abs", [-10], "int")
            let ci = ffi.c_int(5)
            let cf = ffi.c_float(2.0)
            let cs = ffi.c_string("abc")
            return abs_val
        }
        """
        # Xatoliksiz o'tishi kerak
        self.check_code(code)

    def test_type_checker_invalid_ffi_function(self):
        code = """
        import std.ffi

        let bad = ffi.not_a_real_ffi_function()
        """
        with self.assertRaises(TypeCheckError) as ctx:
            self.check_code(code)
        self.assertIn("std.ffi modulida 'not_a_real_ffi_function' funksiyasi mavjud emas", str(ctx.exception))

    def test_type_checker_invalid_library_method(self):
        code = """
        import std.ffi

        let lib = ffi.load("libc")
        lib.bad_method_call()
        """
        with self.assertRaises(TypeCheckError) as ctx:
            self.check_code(code)
        self.assertIn("FfiLibrary strukturasida 'bad_method_call' metodi mavjud emas", str(ctx.exception))


class TestZafiraFfiEndToEnd(unittest.TestCase):
    """Zafira tili orqali std.ffi ning to'liq integratsion testlari."""

    def setUp(self):
        self.interpreter = Interpreter()

    def tearDown(self):
        self.interpreter.close()

    def run_code(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check(program)
        return self.interpreter.run(program)

    def test_zafira_ffi_math_operations(self):
        code = """
        import std.ffi

        let libc = ffi.load("libc")
        let abs_res = libc.call("abs", [-77], "int")
        let sqrt_res = libc.call("sqrt", [100.0], "float")
        let pow_res = libc.call("pow", [2.0, 4.0], "float")
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('abs_res'), 77)
        self.assertEqual(env.get('sqrt_res'), 10.0)
        self.assertEqual(env.get('pow_res'), 16.0)

    def test_zafira_ffi_string_operations(self):
        code = """
        import std.ffi

        let libc = ffi.libc()
        let s = "Salom Dunyo"
        let uzunlik = libc.call("strlen", [s], "int")
        let puts_ret = libc.call("puts", ["Zafira test text"])
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('uzunlik'), 11)
        self.assertGreaterEqual(env.get('puts_ret'), 0)

    def test_zafira_ffi_c_types_usage(self):
        code = """
        import std.ffi

        let libc = ffi.load("libc")

        let my_int = ffi.c_int(-500)
        let int_val = my_int.value
        let int_type = my_int.type
        let abs_from_c_type = libc.call("abs", [my_int], "int")

        let my_flt = ffi.c_float(36.0)
        let flt_val = my_flt.value
        let flt_type = my_flt.type
        let sqrt_from_c_type = libc.call("sqrt", [my_flt], "float")

        let my_str = ffi.c_string("Toshkent")
        let str_val = my_str.value
        let str_type = my_str.type
        let len_from_c_type = libc.call("strlen", [my_str], "int")
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('int_val'), -500)
        self.assertEqual(env.get('int_type'), 'int')
        self.assertEqual(env.get('abs_from_c_type'), 500)

        self.assertEqual(env.get('flt_val'), 36.0)
        self.assertEqual(env.get('flt_type'), 'float')
        self.assertEqual(env.get('sqrt_from_c_type'), 6.0)

        self.assertEqual(env.get('str_val'), "Toshkent")
        self.assertEqual(env.get('str_type'), 'string')
        self.assertEqual(env.get('len_from_c_type'), 8)

    def test_zafira_ffi_has_symbol(self):
        code = """
        import std.ffi

        let libc = ffi.load("libc")
        let has_abs = libc.has_symbol("abs")
        let has_puts = libc.has_symbol("puts")
        let has_sqrt = libc.has_symbol("sqrt")
        let has_fake = libc.has_symbol("mutlaqo_yoq_funksiya_123")
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('has_abs'))
        self.assertTrue(env.get('has_puts'))
        self.assertTrue(env.get('has_sqrt'))
        self.assertFalse(env.get('has_fake'))

    def test_zafira_ffi_alias_import(self):
        code = """
        import std.ffi as cffi

        let libc = cffi.load("libc")
        let res = libc.call("abs", [-33])
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('res'), 33)

    def test_zafira_ffi_try_catch_error_handling(self):
        code = """
        import std.ffi

        let lib_xato = false
        let func_xato = false

        try {
            let bad_lib = ffi.load("yoq_kutubxona_xyz_999")
        } catch (e) {
            lib_xato = true
        }

        try {
            let libc = ffi.load("libc")
            libc.call("topilmas_c_funksiya_777")
        } catch (e2) {
            func_xato = true
        }
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('lib_xato'))
        self.assertTrue(env.get('func_xato'))

    @unittest.skipUnless(sys.platform.startswith('win'), "Faqat Windows tizimida kernel32 mavjud")
    def test_zafira_ffi_windows_kernel32(self):
        code = """
        import std.ffi

        let k32 = ffi.load("kernel32")
        let has_pid = k32.has_symbol("GetCurrentProcessId")
        let pid = k32.call("GetCurrentProcessId", [], "int")
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertTrue(env.get('has_pid'))
        self.assertIsInstance(env.get('pid'), int)
        self.assertGreater(env.get('pid'), 0)


if __name__ == '__main__':
    unittest.main()
