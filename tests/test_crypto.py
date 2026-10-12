"""
Zafira Language - std.crypto Moduli Testlari
std.crypto modulining barcha funksiyalari, xatolik holatlari, type checking va Zafira integratsiyasini 100% to'liq sinovdan o'tkazish.
"""

import base64
import hashlib
import hmac
import re
import unittest

from src.interpreter import Interpreter, ZafiraError, ZafiraList, Environment
from src.lexer import Lexer
from src.parser import Parser
from src.stdlib import load_stdlib_module, STDLIB_MODULES
from src.std_crypto import (
    _crypto_sha256,
    _crypto_sha512,
    _crypto_md5,
    _crypto_hmac_sha256,
    _crypto_base64_encode,
    _crypto_base64_decode,
    _crypto_uuid,
    _crypto_random_bytes,
    _crypto_random_hex,
    create_crypto_module,
)
from src.type_checker import TypeChecker, TypeCheckError


class TestStdCryptoUnit(unittest.TestCase):
    """std.crypto modulining Python birlik (unit) testlari."""

    # ─── 1. SHA-256 ───
    def test_sha256_known_vectors(self):
        self.assertEqual(
            _crypto_sha256("hello"),
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        )
        self.assertEqual(
            _crypto_sha256(""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        self.assertEqual(
            _crypto_sha256("Zafira 2026"),
            hashlib.sha256("Zafira 2026".encode('utf-8')).hexdigest()
        )

    def test_sha256_errors(self):
        with self.assertRaises(ZafiraError):
            _crypto_sha256(None)
        with self.assertRaises(ZafiraError):
            _crypto_sha256(12345)
        with self.assertRaises(ZafiraError):
            _crypto_sha256()
        with self.assertRaises(ZafiraError):
            _crypto_sha256("a", "b")

    # ─── 2. SHA-512 ───
    def test_sha512_known_vectors(self):
        self.assertEqual(
            _crypto_sha512("hello"),
            hashlib.sha512("hello".encode('utf-8')).hexdigest()
        )
        self.assertEqual(
            _crypto_sha512(""),
            hashlib.sha512("".encode('utf-8')).hexdigest()
        )

    def test_sha512_errors(self):
        with self.assertRaises(ZafiraError):
            _crypto_sha512(None)
        with self.assertRaises(ZafiraError):
            _crypto_sha512(999)
        with self.assertRaises(ZafiraError):
            _crypto_sha512()
        with self.assertRaises(ZafiraError):
            _crypto_sha512("x", "y")

    # ─── 3. MD5 ───
    def test_md5_known_vectors(self):
        self.assertEqual(
            _crypto_md5("hello"),
            "5d41402abc4b2a76b9719d911017c592"
        )
        self.assertEqual(
            _crypto_md5(""),
            "d41d8cd98f00b204e9800998ecf8427e"
        )

    def test_md5_errors(self):
        with self.assertRaises(ZafiraError):
            _crypto_md5(None)
        with self.assertRaises(ZafiraError):
            _crypto_md5(["not_str"])
        with self.assertRaises(ZafiraError):
            _crypto_md5()

    # ─── 4. HMAC-SHA256 ───
    def test_hmac_sha256_known_vectors(self):
        key = "secret"
        message = "hello"
        expected = hmac.new(key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
        self.assertEqual(_crypto_hmac_sha256(key, message), expected)
        self.assertEqual(_crypto_hmac_sha256(key, message), "88aab3ede8d3adf94d26ab90d3bafd4a2083070c3bcce9c014ee04a443847c0b")

    def test_hmac_sha256_errors(self):
        with self.assertRaises(ZafiraError):
            _crypto_hmac_sha256(None, "message")
        with self.assertRaises(ZafiraError):
            _crypto_hmac_sha256("key", None)
        with self.assertRaises(ZafiraError):
            _crypto_hmac_sha256(123, "message")
        with self.assertRaises(ZafiraError):
            _crypto_hmac_sha256("key", 456)
        with self.assertRaises(ZafiraError):
            _crypto_hmac_sha256("key")
        with self.assertRaises(ZafiraError):
            _crypto_hmac_sha256("key", "msg", "extra")

    # ─── 5. BASE64 ENCODE / DECODE ───
    def test_base64_encode_and_decode(self):
        text = "Zafira 2026 - Qattiq, tiniq, sinmas sapfir!"
        encoded = _crypto_base64_encode(text)
        self.assertEqual(encoded, base64.b64encode(text.encode('utf-8')).decode('utf-8'))
        decoded = _crypto_base64_decode(encoded)
        self.assertEqual(decoded, text)

        # Bo'sh matn
        self.assertEqual(_crypto_base64_encode(""), "")
        self.assertEqual(_crypto_base64_decode(""), "")

    def test_base64_errors(self):
        with self.assertRaises(ZafiraError):
            _crypto_base64_encode(None)
        with self.assertRaises(ZafiraError):
            _crypto_base64_encode(123)
        with self.assertRaises(ZafiraError):
            _crypto_base64_decode(None)
        with self.assertRaises(ZafiraError):
            _crypto_base64_decode(456)
        with self.assertRaises(ZafiraError):
            _crypto_base64_decode("noto'g'ri_base64_belgilar!#@")
        with self.assertRaises(ZafiraError):
            _crypto_base64_decode("abc")  # Noto'g'ri padding

    # ─── 6. UUID v4 ───
    def test_uuid(self):
        u1 = _crypto_uuid()
        u2 = _crypto_uuid()
        self.assertIsInstance(u1, str)
        self.assertEqual(len(u1), 36)
        self.assertNotEqual(u1, u2)
        # UUID v4 format tekshiruvi: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        self.assertTrue(bool(re.match(pattern, u1)))
        self.assertTrue(bool(re.match(pattern, u2)))

    def test_uuid_errors(self):
        with self.assertRaises(ZafiraError):
            _crypto_uuid("arg_bo'lmasligi_kerak")

    # ─── 7. RANDOM_BYTES ───
    def test_random_bytes(self):
        res = _crypto_random_bytes(16)
        self.assertIsInstance(res, ZafiraList)
        self.assertEqual(len(res.items), 16)
        for b in res.items:
            self.assertIsInstance(b, int)
            self.assertTrue(0 <= b <= 255)

        # 0 bayt
        res_empty = _crypto_random_bytes(0)
        self.assertEqual(len(res_empty.items), 0)

    def test_random_bytes_errors(self):
        with self.assertRaises(ZafiraError):
            _crypto_random_bytes(None)
        with self.assertRaises(ZafiraError):
            _crypto_random_bytes(-5)
        with self.assertRaises(ZafiraError):
            _crypto_random_bytes("16")
        with self.assertRaises(ZafiraError):
            _crypto_random_bytes(True)
        with self.assertRaises(ZafiraError):
            _crypto_random_bytes()

    # ─── 8. RANDOM_HEX ───
    def test_random_hex(self):
        hex_tok = _crypto_random_hex(16)
        self.assertIsInstance(hex_tok, str)
        self.assertEqual(len(hex_tok), 32)
        self.assertTrue(bool(re.match(r'^[0-9a-f]{32}$', hex_tok)))

        hex_empty = _crypto_random_hex(0)
        self.assertEqual(hex_empty, "")

    def test_random_hex_errors(self):
        with self.assertRaises(ZafiraError):
            _crypto_random_hex(None)
        with self.assertRaises(ZafiraError):
            _crypto_random_hex(-1)
        with self.assertRaises(ZafiraError):
            _crypto_random_hex("8")
        with self.assertRaises(ZafiraError):
            _crypto_random_hex(False)
        with self.assertRaises(ZafiraError):
            _crypto_random_hex()


class TestStdCryptoModuleRegistration(unittest.TestCase):
    """std.crypto moduli ro'yxatga olinishi va STDLIB integratsiyasi testlari."""

    def test_module_structure(self):
        mod = create_crypto_module()
        self.assertEqual(mod.name, "crypto")
        self.assertEqual(mod.type_name, "std.crypto")
        expected_keys = {
            'sha256', 'sha512', 'md5', 'hmac_sha256',
            'base64_encode', 'base64_decode',
            'uuid', 'random_bytes', 'random_hex'
        }
        self.assertTrue(expected_keys.issubset(set(mod.fields.keys())))

    def test_stdlib_modules_dict(self):
        self.assertIn('crypto', STDLIB_MODULES)
        self.assertEqual(STDLIB_MODULES['crypto'].name, 'crypto')

    def test_load_stdlib_module(self):
        env = Environment()
        load_stdlib_module('std.crypto', env)
        self.assertTrue(env.has('crypto'))
        mod = env.get('crypto')
        self.assertEqual(mod.name, 'crypto')

    def test_load_stdlib_module_alias(self):
        env = Environment()
        load_stdlib_module('std.crypto', env, alias='my_crypto')
        self.assertTrue(env.has('my_crypto'))
        mod = env.get('my_crypto')
        self.assertEqual(mod.name, 'crypto')


class TestTypeCheckerCrypto(unittest.TestCase):
    """std.crypto moduli uchun statik tip tekshiruvi (TypeChecker) testlari."""

    def check_code(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check(program)
        return program

    def test_type_checker_success(self):
        code = """
        import std.crypto

        seal fn test_crypto_types() -> String {
            let h256: String = crypto.sha256("test")
            let h512: String = crypto.sha512("test")
            let md: String = crypto.md5("test")
            let hm: String = crypto.hmac_sha256("key", "msg")
            let b64e: String = crypto.base64_encode("hello")
            let b64d: String = crypto.base64_decode(b64e)
            let u: String = crypto.uuid()
            let rx: String = crypto.random_hex(16)
            let rb: List = crypto.random_bytes(8)
            return h256
        }
        """
        self.check_code(code)

    def test_type_checker_invalid_member(self):
        code = """
        import std.crypto

        seal fn test_invalid() -> String {
            return crypto.not_existing_func()
        }
        """
        with self.assertRaises(TypeCheckError) as ctx:
            self.check_code(code)
        self.assertIn("std.crypto modulida 'not_existing_func' funksiyasi mavjud emas", str(ctx.exception))

    def test_type_checker_invalid_property(self):
        code = """
        import std.crypto

        seal fn test_prop() -> Any {
            let f = crypto.invalid_property
            return f
        }
        """
        with self.assertRaises(TypeCheckError) as ctx:
            self.check_code(code)
        self.assertIn("std.crypto modulida 'invalid_property' a'zosi mavjud emas", str(ctx.exception))

    def test_type_checker_type_mismatch(self):
        code = """
        import std.crypto

        seal fn test_mismatch() -> Int {
            let x: Int = crypto.sha256("test")
            return x
        }
        """
        with self.assertRaises(TypeCheckError):
            self.check_code(code)


class TestZafiraCryptoIntegration(unittest.TestCase):
    """Zafira tilida std.crypto modulining to'liq ijro integratsiya testlari."""

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

    def test_zafira_crypto_basic_operations(self):
        code = """
        import std.crypto

        let matn = "Zafira 2026"
        let h256 = crypto.sha256(matn)
        let h512 = crypto.sha512(matn)
        let hmd5 = crypto.md5(matn)
        let hm = crypto.hmac_sha256("kalit", matn)

        let b64 = crypto.base64_encode(matn)
        let tiklangan = crypto.base64_decode(b64)

        let uid = crypto.uuid()
        let r_hex = crypto.random_hex(16)
        let r_bytes = crypto.random_bytes(10)
        let bytes_len = r_bytes.len
        """
        self.run_code(code)
        env = self.interpreter.global_env

        self.assertEqual(env.get('h256'), hashlib.sha256("Zafira 2026".encode('utf-8')).hexdigest())
        self.assertEqual(env.get('h512'), hashlib.sha512("Zafira 2026".encode('utf-8')).hexdigest())
        self.assertEqual(env.get('hmd5'), hashlib.md5("Zafira 2026".encode('utf-8')).hexdigest())
        self.assertEqual(
            env.get('hm'),
            hmac.new("kalit".encode('utf-8'), "Zafira 2026".encode('utf-8'), hashlib.sha256).hexdigest()
        )
        self.assertEqual(env.get('tiklangan'), "Zafira 2026")
        self.assertEqual(len(env.get('uid')), 36)
        self.assertEqual(len(env.get('r_hex')), 32)
        self.assertIsInstance(env.get('r_bytes'), ZafiraList)
        self.assertEqual(env.get('bytes_len'), 10)

    def test_zafira_crypto_aliased_import(self):
        code = """
        import std.crypto as cr

        let h = cr.sha256("aliased_test")
        let tok = cr.random_hex(8)
        let u = cr.uuid()
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('h'), hashlib.sha256("aliased_test".encode('utf-8')).hexdigest())
        self.assertEqual(len(env.get('tok')), 16)
        self.assertEqual(len(env.get('u')), 36)

    def test_zafira_crypto_error_handling(self):
        code = """
        import std.crypto

        let xato_b64 = "yo'q"
        try {
            crypto.base64_decode("noto'g'ri_b64!#?")
        } catch (e) {
            xato_b64 = "ushlandi"
        }

        let xato_null = "yo'q"
        try {
            crypto.sha256(null)
        } catch (e) {
            xato_null = "ushlandi"
        }
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('xato_b64'), "ushlandi")
        self.assertEqual(env.get('xato_null'), "ushlandi")


if __name__ == '__main__':
    unittest.main()
