"""
Zafira Language - std.env va std.datetime Modullari Testlari
std.env va std.datetime ning barcha funksiyalari, xatolik holatlari va Zafira integratsiyasini 100% to'liq sinovdan o'tkazish.
"""

import datetime
import os
import sys
import time
import unittest

from src.interpreter import Interpreter, ZafiraError, ZafiraList, ZafiraStruct, Environment
from src.lexer import Lexer
from src.parser import Parser
from src.stdlib import load_stdlib_module, STDLIB_MODULES
from src.std_env import (
    _env_get,
    _env_set,
    _env_has,
    _env_remove,
    _env_all,
    _env_args,
    _env_os,
    _env_cwd,
    set_custom_args,
    create_env_module,
)
from src.std_datetime import (
    _datetime_now,
    _datetime_timestamp,
    _datetime_format,
    _datetime_sleep,
    _datetime_sleep_ms,
    create_datetime_module,
)
from src.type_checker import TypeChecker, TypeCheckError


class TestStdEnvUnit(unittest.TestCase):
    """std.env modulining Python birlik (unit) testlari."""

    def setUp(self):
        self.test_key = "ZAFIRA_ENV_TEST_VAR_123"
        if self.test_key in os.environ:
            del os.environ[self.test_key]

    def tearDown(self):
        if self.test_key in os.environ:
            del os.environ[self.test_key]
        set_custom_args(None)

    def test_env_set_get_has_remove(self):
        # has -> False
        self.assertFalse(_env_has(self.test_key))
        # get default
        self.assertIsNone(_env_get(self.test_key))
        self.assertEqual(_env_get(self.test_key, "boshlangich"), "boshlangich")

        # set
        _env_set(self.test_key, "salom_dunyo")
        self.assertTrue(_env_has(self.test_key))
        self.assertEqual(_env_get(self.test_key), "salom_dunyo")

        # set non-string val
        _env_set(self.test_key, 999)
        self.assertEqual(_env_get(self.test_key), "999")

        # remove
        _env_remove(self.test_key)
        self.assertFalse(_env_has(self.test_key))
        self.assertIsNone(_env_get(self.test_key))

    def test_env_errors_on_invalid_keys(self):
        with self.assertRaises(ZafiraError):
            _env_get(123)
        with self.assertRaises(ZafiraError):
            _env_set(None, "val")
        with self.assertRaises(ZafiraError):
            _env_has([])
        with self.assertRaises(ZafiraError):
            _env_remove({})

    def test_env_all(self):
        _env_set(self.test_key, "hammasi_uchun")
        all_env = _env_all()
        self.assertIsInstance(all_env, ZafiraStruct)
        self.assertEqual(all_env.fields[self.test_key], "hammasi_uchun")

    def test_env_args(self):
        set_custom_args(["zafira", "run", "app.zf", "--verbose"])
        args = _env_args()
        self.assertIsInstance(args, ZafiraList)
        self.assertEqual(args.items, ["zafira", "run", "app.zf", "--verbose"])

        set_custom_args(None)
        default_args = _env_args()
        self.assertEqual(default_args.items, [str(a) for a in sys.argv])

    def test_env_os(self):
        os_name = _env_os()
        self.assertIn(os_name, ["windows", "linux", "darwin"])

    def test_env_cwd(self):
        cwd = _env_cwd()
        self.assertEqual(cwd, os.getcwd())

    def test_create_env_module(self):
        mod = create_env_module()
        self.assertEqual(mod.name, "env")
        for fn_name in ['get', 'set', 'has', 'remove', 'all', 'args', 'os', 'cwd']:
            self.assertIn(fn_name, mod.fields)


class TestStdDatetimeUnit(unittest.TestCase):
    """std.datetime modulining Python birlik (unit) testlari."""

    def test_datetime_now(self):
        now_struct = _datetime_now()
        self.assertIsInstance(now_struct, ZafiraStruct)
        self.assertEqual(now_struct.type_name, "DateTime")
        curr = datetime.datetime.now()
        self.assertEqual(now_struct.fields['year'], curr.year)
        self.assertEqual(now_struct.fields['month'], curr.month)
        self.assertIn('day', now_struct.fields)
        self.assertIn('hour', now_struct.fields)
        self.assertIn('minute', now_struct.fields)
        self.assertIn('second', now_struct.fields)
        self.assertIn('iso', now_struct.fields)
        self.assertTrue(isinstance(now_struct.fields['iso'], str))

    def test_datetime_timestamp(self):
        ts = _datetime_timestamp()
        self.assertIsInstance(ts, float)
        self.assertAlmostEqual(ts, time.time(), delta=2.0)

    def test_datetime_format(self):
        # 1. format(None, fmt)
        res_current = _datetime_format(None, "%Y-%m-%d")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(res_current, today)

        # 2. format(timestamp, fmt)
        fixed_ts = 1609459200.0  # 2021-01-01 00:00:00 (UTC/local)
        expected_year = datetime.datetime.fromtimestamp(fixed_ts).strftime("%Y")
        res_ts = _datetime_format(fixed_ts, "%Y")
        self.assertEqual(res_ts, expected_year)

        # 3. format("%Y-%m-%d") (1 ta argument varianti)
        res_1arg = _datetime_format("%Y")
        self.assertEqual(res_1arg, str(datetime.datetime.now().year))

        # 4. format(ZafiraStruct, fmt)
        now_st = _datetime_now()
        res_st = _datetime_format(now_st, "%Y")
        self.assertEqual(res_st, str(now_st.fields['year']))

    def test_datetime_format_errors(self):
        with self.assertRaises(ZafiraError):
            _datetime_format(None, 12345)  # format satri string emas
        with self.assertRaises(ZafiraError):
            _datetime_format("yaroqsiz_vaqt", "%Y")

    def test_datetime_sleep_and_sleep_ms(self):
        t0 = time.time()
        _datetime_sleep_ms(20)
        dt_ms = time.time() - t0
        self.assertGreaterEqual(dt_ms, 0.015)

        t1 = time.time()
        _datetime_sleep(0.02)
        dt_s = time.time() - t1
        self.assertGreaterEqual(dt_s, 0.015)

    def test_datetime_sleep_negative_errors(self):
        with self.assertRaises(ZafiraError):
            _datetime_sleep(-1)
        with self.assertRaises(ZafiraError):
            _datetime_sleep_ms(-10)

    def test_create_datetime_module(self):
        mod = create_datetime_module()
        self.assertEqual(mod.name, "datetime")
        for fn_name in ['now', 'timestamp', 'format', 'sleep', 'sleep_ms']:
            self.assertIn(fn_name, mod.fields)


class TestEnvDatetimeIntegration(unittest.TestCase):
    """Zafira tili skriptlari orqali std.env va std.datetime integratsiya testlari."""

    def setUp(self):
        self.interpreter = Interpreter()
        self.test_key = "ZAFIRA_INTEG_VAR"
        if self.test_key in os.environ:
            del os.environ[self.test_key]

    def tearDown(self):
        if self.test_key in os.environ:
            del os.environ[self.test_key]

    def run_code(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check(program)
        return self.interpreter.run(program)

    def test_zafira_env_operations(self):
        code = f"""
        import std.env

        let os_name = env.os()
        let cwd_name = env.cwd()
        let args_lst = env.args()

        env.set("{self.test_key}", "42")
        let mavjud = env.has("{self.test_key}")
        let qiymat = env.get("{self.test_key}")
        let default_val = env.get("NOT_FOUND_XYZ", "def_ok")

        let all_env = env.all()
        let val_from_all = all_env["{self.test_key}"]

        env.remove("{self.test_key}")
        let keyin_mavjud = env.has("{self.test_key}")
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertIn(env.get('os_name'), ["windows", "linux", "darwin"])
        self.assertEqual(env.get('cwd_name'), os.getcwd())
        self.assertIsInstance(env.get('args_lst'), ZafiraList)
        self.assertTrue(env.get('mavjud'))
        self.assertEqual(env.get('qiymat'), "42")
        self.assertEqual(env.get('default_val'), "def_ok")
        self.assertEqual(env.get('val_from_all'), "42")
        self.assertFalse(env.get('keyin_mavjud'))

    def test_zafira_datetime_operations(self):
        code = """
        import std.datetime

        let vaqt = datetime.now()
        let y = vaqt.year
        let m = vaqt.month
        let d = vaqt.day
        let iso_str = vaqt.iso

        let ts = datetime.timestamp()
        let formatlangan = datetime.format(null, "%Y")
        datetime.sleep_ms(10)
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('y'), datetime.datetime.now().year)
        self.assertEqual(env.get('m'), datetime.datetime.now().month)
        self.assertIsInstance(env.get('ts'), float)
        self.assertEqual(env.get('formatlangan'), str(datetime.datetime.now().year))

    def test_zafira_aliased_imports(self):
        code = """
        import std.env as my_env
        import std.datetime as dt

        let sys_os = my_env.os()
        let now_iso = dt.now().iso
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertIn(env.get('sys_os'), ["windows", "linux", "darwin"])
        self.assertIsInstance(env.get('now_iso'), str)

    def test_type_checker_env_and_datetime(self):
        code = """
        import std.env
        import std.datetime

        seal fn test_env_types() -> String {
            let o: String = env.os()
            let c: String = env.cwd()
            let b: Bool = env.has("PATH")
            let a: List = env.args()
            env.set("KEY_TEMP", "VAL")
            env.remove("KEY_TEMP")
            return o
        }

        seal fn test_dt_types() -> Float {
            let ts: Float = datetime.timestamp()
            let s: String = datetime.format(null, "%Y")
            datetime.sleep_ms(5)
            datetime.sleep(0.001)
            return ts
        }

        let os_res = test_env_types()
        let ts_res = test_dt_types()
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertIn(env.get('os_res'), ["windows", "linux", "darwin"])
        self.assertIsInstance(env.get('ts_res'), float)

    def test_type_checker_unknown_member_errors(self):
        # env unknown member
        code_env = """
        import std.env
        env.noma_lum_metod()
        """
        p_env = Parser(Lexer(code_env).tokenize()).parse()
        with self.assertRaises(TypeCheckError):
            TypeChecker().check(p_env)

        # datetime unknown member
        code_dt = """
        import std.datetime
        datetime.mavjud_emas()
        """
        p_dt = Parser(Lexer(code_dt).tokenize()).parse()
        with self.assertRaises(TypeCheckError):
            TypeChecker().check(p_dt)


if __name__ == '__main__':
    unittest.main()
