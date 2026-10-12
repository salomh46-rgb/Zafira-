"""
Unit tests for Zafira Online Studio & Playground Server
Fayl: tests/test_playground.py
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import threading
import unittest

# Loyiha ildiz yo'lini qo'shish
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.playground_server import (
    execute_zafira_code,
    create_server,
    ast_to_dict,
    format_ast_tree,
    PLAYGROUND_DIR
)


class TestPlaygroundExecution(unittest.TestCase):
    """execute_zafira_code funksiyasi bo'yicha birlik testlari"""

    def test_hello_world_execution(self):
        code = 'let x = "Zafira"\nprint("Salom " + x)'
        res = execute_zafira_code(code)
        self.assertIsNone(res["error"])
        self.assertIn("Salom Zafira", res["stdout"])
        self.assertTrue(len(res["tokens"]) > 0)
        self.assertIn("Program", res["ast"])
        self.assertIsNotNone(res["ast_tree"])
        self.assertEqual(res["ast_tree"]["_type"], "Program")

    def test_math_and_function(self):
        code = """
        fn qoshish(a, b) {
            return a + b
        }
        let natija = qoshish(40, 2)
        print("Natija: " + String(natija))
        """
        res = execute_zafira_code(code)
        self.assertIsNone(res["error"])
        self.assertIn("Natija: 42", res["stdout"])

    def test_seal_invariant_pass_and_fail(self):
        # Muvaffaqiyatli seal chaqiruvi
        code_pass = """
        seal fn bolish(a: Int, b: Int) -> Float
            where b > 0
        {
            return a / b
        }
        print(bolish(10, 2))
        """
        res_pass = execute_zafira_code(code_pass)
        self.assertIsNone(res_pass["error"])
        self.assertIn("5", res_pass["stdout"])

        # Invariant buzilganda (where b > 0 buziladi)
        code_fail = """
        seal fn bolish(a: Int, b: Int) -> Float
            where b > 0
        {
            return a / b
        }
        print(bolish(10, 0))
        """
        res_fail = execute_zafira_code(code_fail)
        self.assertIsNotNone(res_fail["error"])
        self.assertTrue("invarianti" in res_fail["error"] or "buzildi" in res_fail["error"])

    def test_lexer_error_capture(self):
        # Tugallanmagan satr
        code = 'let x = "tugallanmagan satr'
        res = execute_zafira_code(code)
        self.assertIsNotNone(res["error"])
        self.assertIn("Lekser Xatosi", res["error"])

    def test_parser_error_capture(self):
        # Noto'g'ri sintaksis
        code = "fn ( { let ="
        res = execute_zafira_code(code)
        self.assertIsNotNone(res["error"])
        self.assertIn("Parser Xatosi", res["error"])

    def test_runtime_error_capture(self):
        # Nolga bo'lish
        code = "print(10 / 0)"
        res = execute_zafira_code(code)
        self.assertIsNotNone(res["error"])
        self.assertIn("Nolga bo'lish", res["error"])

    def test_tokens_structure(self):
        code = "let son = 123"
        res = execute_zafira_code(code)
        self.assertIsNone(res["error"])
        tokens = res["tokens"]
        types = [t["type"] for t in tokens]
        self.assertIn("LET", types)
        self.assertIn("IDENT", types)
        self.assertIn("ASSIGN", types)
        self.assertIn("INT", types)

        # Token obyekti maydonlarini tekshirish
        tok0 = tokens[0]
        self.assertEqual(tok0["type"], "LET")
        self.assertEqual(tok0["value"], "let")
        self.assertEqual(tok0["line"], 1)

    def test_timeout_protection(self):
        # Cheksiz tsikl
        code = "while true { let x = 1 }"
        res = execute_zafira_code(code, timeout_seconds=0.6)
        self.assertIsNotNone(res["error"])
        self.assertIn("Vaqt Tugadi", res["error"])


class TestPlaygroundServerHTTP(unittest.TestCase):
    """Playground HTTP serveri va API endpointlari bo'yicha integratsion testlar"""

    @classmethod
    def setUpClass(cls):
        # Bo'sh portda serverni ishga tushirish
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        cls.port = s.getsockname()[1]
        s.close()

        cls.httpd = create_server(host='127.0.0.1', port=cls.port)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.2)  # Server ko'tarilishi uchun kutish

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def test_health_endpoint(self):
        req = urllib.request.Request(self._url('/api/health'))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertEqual(data.get("status"), "ok")
            self.assertIn("version", data)

    def test_api_run_success(self):
        payload = json.dumps({"code": "print(100 + 25)"}).encode('utf-8')
        req = urllib.request.Request(
            self._url('/api/run'),
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertIsNone(data.get("error"))
            self.assertIn("125", data.get("stdout"))
            self.assertIn("Program", data.get("ast"))
            self.assertTrue(len(data.get("tokens")) > 0)

    def test_api_run_error(self):
        payload = json.dumps({"code": "print(noma_lum_nom)"}).encode('utf-8')
        req = urllib.request.Request(
            self._url('/api/run'),
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertIsNotNone(data.get("error"))
            self.assertIn("aniqlanmagan", data.get("error"))

    def test_static_index_html(self):
        req = urllib.request.Request(self._url('/'))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode('utf-8')
            self.assertIn("ZAFIRA ONLINE STUDIO", content)
            self.assertIn("code-editor", content)

    def test_static_app_js(self):
        req = urllib.request.Request(self._url('/app.js'))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode('utf-8')
            self.assertIn("TEMPLATES", content)
            self.assertIn("runCode", content)

    def test_static_style_css(self):
        req = urllib.request.Request(self._url('/style.css'))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode('utf-8')
            self.assertIn("--bg-deep", content)
            self.assertIn("#0ea5e9", content)

    def test_static_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(self._url('/mavjud_emas_fayl.xyz'))
        self.assertEqual(ctx.exception.code, 404)


class TestPlaygroundTemplates(unittest.TestCase):
    """Playgroundda taqdim etilgan 5 ta tayyor andozalar to'liq ishlashini sinash"""

    def test_template_hello(self):
        code = """
        let nomi = "Zafira"
        let versiya = 0.1
        const YARATUVCHI = "Jasper"
        print("Salom, " + nomi)
        fn salomlash(ism) { return "Assalomu alaykum, " + ism }
        print(salomlash("Jasper"))
        """
        res = execute_zafira_code(code)
        self.assertIsNone(res["error"])
        self.assertIn("Salom, Zafira", res["stdout"])
        self.assertIn("Assalomu alaykum, Jasper", res["stdout"])

    def test_template_factorial(self):
        code = """
        seal fn faktorial(n: Int) -> Int
            where n >= 0
        {
            if n <= 1 { return 1 }
            return n * faktorial(n - 1)
        }
        print(faktorial(5))
        """
        res = execute_zafira_code(code)
        self.assertIsNone(res["error"])
        self.assertIn("120", res["stdout"])

    def test_template_ai_tensors(self):
        code = """
        import std.ai
        let v1 = ai.tensor([1.0, 2.0, 3.0])
        let v2 = ai.tensor([4.0, 5.0, 6.0])
        print(v1.dot(v2))
        run @gpu {
            print("GPU bloki")
        }
        """
        res = execute_zafira_code(code)
        self.assertIsNone(res["error"])
        self.assertIn("32.0", res["stdout"])
        self.assertIn("GPU bloki", res["stdout"])

    def test_template_web_json(self):
        code = """
        import std.json
        let obj = json.parse("{\\"nomi\\": \\"Zafira\\", \\"yosh\\": 1}")
        print(obj.nomi)
        let s = json.stringify([1, 2, 3])
        print(s)
        """
        res = execute_zafira_code(code)
        self.assertIsNone(res["error"])
        self.assertIn("Zafira", res["stdout"])
        self.assertIn("[1, 2, 3]", res["stdout"])

    def test_template_async_pipeline(self):
        code = """
        struct Task { id: Int, nom: String }
        async fn bajar(t) {
            print("Task: " + t.nom)
            return "Bajarildi"
        }
        let t = Task(1, "Yuklash")
        let res = await bajar(t)
        print("Holat: " + res)
        """
        res = execute_zafira_code(code)
        self.assertIsNone(res["error"])
        self.assertIn("Task: Yuklash", res["stdout"])
        self.assertIn("Holat: Bajarildi", res["stdout"])


if __name__ == '__main__':
    unittest.main()
