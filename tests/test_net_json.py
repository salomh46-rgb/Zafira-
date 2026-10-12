"""
Zafira Language - Web & Network (std.json va std.net) Testlari
std.json va std.net modullarini 100% to'liq sinovdan o'tkazish
"""

import io
import json
import socket
import sys
import unittest
from typing import Any

from src.interpreter import Interpreter, ZafiraError, ZafiraList, ZafiraStruct
from src.lexer import Lexer
from src.parser import Parser
from src.std_json import _json_parse, _json_stringify, create_json_module
from src.std_net import _net_close, _net_get, _net_listen, _net_post, create_net_module
from src.stdlib import load_stdlib_module
from src.type_checker import TypeChecker


def get_free_port() -> int:
    """Bo'sh tarmoq portini topadi."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class TestNetJson(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    def run_code(self, source: str) -> Any:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check(program)
        return self.interpreter.run(program)

    # ══════════════════════════════════════════════════════════════
    # 1. STD.JSON UNIT SINOVLARI
    # ══════════════════════════════════════════════════════════════

    def test_json_parse_object(self):
        json_str = '{"name": "Jasper", "age": 25, "active": true, "pi": 3.14}'
        res = _json_parse(json_str)
        self.assertIsInstance(res, ZafiraStruct)
        self.assertEqual(res.fields['name'], "Jasper")
        self.assertEqual(res.fields['age'], 25)
        self.assertTrue(res.fields['active'])
        self.assertEqual(res.fields['pi'], 3.14)

    def test_json_parse_nested(self):
        json_str = '{"user": {"username": "jasper", "roles": ["admin", "dev"]}, "total": 1}'
        res = _json_parse(json_str)
        self.assertIsInstance(res, ZafiraStruct)
        user = res.fields['user']
        self.assertIsInstance(user, ZafiraStruct)
        self.assertEqual(user.fields['username'], "jasper")
        roles = user.fields['roles']
        self.assertIsInstance(roles, ZafiraList)
        self.assertEqual(roles.items, ["admin", "dev"])
        self.assertEqual(res.fields['total'], 1)

    def test_json_parse_list(self):
        json_str = '[1, 2, "uch", false, null]'
        res = _json_parse(json_str)
        self.assertIsInstance(res, ZafiraList)
        self.assertEqual(len(res.items), 5)
        self.assertEqual(res.items[0], 1)
        self.assertEqual(res.items[2], "uch")
        self.assertFalse(res.items[3])
        self.assertIsNone(res.items[4])

    def test_json_parse_primitives(self):
        self.assertEqual(_json_parse('"salom"'), "salom")
        self.assertEqual(_json_parse('42'), 42)
        self.assertEqual(_json_parse('3.14'), 3.14)
        self.assertTrue(_json_parse('true'))
        self.assertFalse(_json_parse('false'))
        self.assertIsNone(_json_parse('null'))

    def test_json_parse_invalid(self):
        with self.assertRaises(ZafiraError):
            _json_parse('{invalid json}')
        with self.assertRaises(ZafiraError):
            _json_parse(123)  # str emas

    def test_json_stringify_object(self):
        struct = ZafiraStruct('User', {'name': 'Jasper', 'age': 25})
        res = _json_stringify(struct)
        data = json.loads(res)
        self.assertEqual(data, {'name': 'Jasper', 'age': 25})

    def test_json_stringify_list(self):
        zlist = ZafiraList([10, "yigirma", True, None])
        res = _json_stringify(zlist)
        data = json.loads(res)
        self.assertEqual(data, [10, "yigirma", True, None])

    def test_json_stringify_indent(self):
        struct = ZafiraStruct('Config', {'host': 'localhost', 'port': 8080})
        res = _json_stringify(struct, indent=2)
        self.assertIn('\n', res)
        self.assertIn('  "host": "localhost"', res)

    def test_json_stringify_nested(self):
        inner = ZafiraStruct('Inner', {'x': 100})
        outer = ZafiraStruct('Outer', {'inner': inner, 'items': ZafiraList([1, 2])})
        res = _json_stringify(outer)
        data = json.loads(res)
        self.assertEqual(data, {'inner': {'x': 100}, 'items': [1, 2]})

    def test_json_in_zafira_code(self):
        code = """
        import std.json
        let raw = "{\\\"til\\\": \\\"Zafira\\\", \\\"yil\\\": 2026, \\\"tezlik\\\": [1, 2, 3]}"
        let data = json.parse(raw)
        let til_nomi = data.til
        let yil_qiymati = data.yil
        let birinchi_tezlik = data.tezlik[0]
        let qayta_matn = json.stringify(data)
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('til_nomi'), "Zafira")
        self.assertEqual(env.get('yil_qiymati'), 2026)
        self.assertEqual(env.get('birinchi_tezlik'), 1)
        parsed_again = json.loads(env.get('qayta_matn'))
        self.assertEqual(parsed_again['til'], "Zafira")

    def test_json_struct_index_access(self):
        code = """
        import std.json
        let data = json.parse("{\\\"kalit\\\": \\\"qiymat\\\"}")
        let olingan = data["kalit"]
        data["kalit"] = "yangi_qiymat"
        let yangilangan = data.kalit
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('olingan'), "qiymat")
        self.assertEqual(env.get('yangilangan'), "yangi_qiymat")

    # ══════════════════════════════════════════════════════════════
    # 2. STD.NET UNIT SINOVLARI
    # ══════════════════════════════════════════════════════════════

    def test_net_local_http_server_and_client(self):
        port = get_free_port()

        def handler(req):
            if req.fields['path'] == '/salom':
                return "Salom Zafira"
            if req.fields['path'] == '/json':
                return ZafiraStruct('Resp', {'status': 'OK', 'kod': 200})
            if req.fields['path'] == '/echo':
                return f"Qabul: {req.fields['body']}"
            if req.fields['path'] == '/custom_status':
                return ZafiraStruct('HttpResp', {'status': 201, 'body': 'Yaratildi'})
            return ZafiraStruct('HttpResp', {'status': 404, 'body': 'Topilmadi'})

        srv = _net_listen(port, handler, threaded=True)
        try:
            # 1. Oddiy GET
            res1 = _net_get(f"http://127.0.0.1:{port}/salom")
            self.assertEqual(res1.fields['status'], 200)
            self.assertTrue(res1.fields['ok'])
            self.assertEqual(res1.fields['body'], "Salom Zafira")

            # 2. JSON qaytaruvchi GET
            res2 = _net_get(f"http://127.0.0.1:{port}/json")
            self.assertEqual(res2.fields['status'], 200)
            self.assertTrue(res2.fields['ok'])
            data = json.loads(res2.fields['body'])
            self.assertEqual(data['status'], 'OK')
            self.assertEqual(data['kod'], 200)

            # 3. POST so'rov matn bilan
            res3 = _net_post(f"http://127.0.0.1:{port}/echo", data="test_xabar")
            self.assertEqual(res3.fields['status'], 200)
            self.assertEqual(res3.fields['body'], "Qabul: test_xabar")

            # 4. POST so'rov JSON bilan
            payload = ZafiraStruct('Msg', {'ism': 'Jasper'})
            res4 = _net_post(f"http://127.0.0.1:{port}/echo", json=payload)
            self.assertEqual(res4.fields['status'], 200)
            self.assertIn('"ism": "Jasper"', res4.fields['body'])

            # 5. Maxsus status (201)
            res5 = _net_get(f"http://127.0.0.1:{port}/custom_status")
            self.assertEqual(res5.fields['status'], 201)
            self.assertTrue(res5.fields['ok'])
            self.assertEqual(res5.fields['body'], "Yaratildi")

            # 6. 404 Not Found
            res6 = _net_get(f"http://127.0.0.1:{port}/mavjud_emas")
            self.assertEqual(res6.fields['status'], 404)
            self.assertFalse(res6.fields['ok'])
            self.assertEqual(res6.fields['body'], "Topilmadi")

        finally:
            _net_close(srv)

    def test_net_custom_headers(self):
        port = get_free_port()

        def handler(req):
            headers = req.fields['headers'].fields
            auth = headers.get('authorization', headers.get('Authorization', ''))
            return f"Auth: {auth}"

        srv = _net_listen(port, handler, threaded=True)
        try:
            custom_headers = ZafiraStruct('Headers', {'Authorization': 'Bearer ZAFIRA_SECRET'})
            res = _net_get(f"http://127.0.0.1:{port}/check", headers=custom_headers)
            self.assertEqual(res.fields['status'], 200)
            self.assertEqual(res.fields['body'], "Auth: Bearer ZAFIRA_SECRET")
        finally:
            _net_close(srv)

    def test_net_invalid_url(self):
        with self.assertRaises(ZafiraError):
            _net_get("ftp://localhost/test")
        with self.assertRaises(ZafiraError):
            _net_get("faqat_matn")

    def test_net_connection_refused(self):
        # Yopiq portga so'rov yuborilganda ZafiraError chiqishi kerak
        closed_port = get_free_port()
        with self.assertRaises(ZafiraError):
            _net_get(f"http://127.0.0.1:{closed_port}/fail")

    def test_net_in_zafira_code(self):
        port = get_free_port()
        code = f"""
        import std.json
        import std.net

        fn my_handler(req) {{
            if req.path == "/api/ping" {{
                return json.parse("{{\\\"pong\\\": true}}")
            }}
            return "Boshqa sahifa"
        }}

        let srv = net.listen({port}, my_handler, null, true)
        let resp = net.get("http://127.0.0.1:{port}/api/ping")
        let status_kodi = resp.status
        let ok_holati = resp.ok
        let json_body = json.parse(resp.body)
        let pong_natija = json_body.pong
        srv.close()
        """
        self.run_code(code)
        env = self.interpreter.global_env
        self.assertEqual(env.get('status_kodi'), 200)
        self.assertTrue(env.get('ok_holati'))
        self.assertTrue(env.get('pong_natija'))


if __name__ == '__main__':
    unittest.main()
