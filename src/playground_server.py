"""
Zafira Language - Web Interactive Playground Server
Backend server for Zafira Online Studio.

Endpoints:
- GET  /              -> Serves playground/index.html
- GET  /<static>      -> Serves static files from playground/
- POST /api/run       -> Executes Zafira code, returns { stdout, error, ast, tokens }
- GET  /api/health    -> Health status { status: 'ok', version: ... }
"""

import os
import sys
import json
import io
import pprint
import contextlib
import threading
import webbrowser
import http.server
from typing import Dict, Any, List, Optional

# Loyiha ildiz yo'lini aniqlash
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

PLAYGROUND_DIR = os.path.join(ROOT_DIR, 'playground')

from src.lexer import Lexer, LexerError, Token
from src.parser import Parser, ParseError, Node, Program
from src.interpreter import Interpreter, ZafiraError, _zf_str
from src.type_checker import TypeChecker, TypeCheckError


def ast_to_dict(node: Any) -> Any:
    """AST daraxtini JSON-serializable lug'atga aylantiradi"""
    if node is None:
        return None
    if isinstance(node, (int, float, str, bool)):
        return node
    if isinstance(node, list):
        return [ast_to_dict(item) for item in node]
    if isinstance(node, tuple):
        return [ast_to_dict(item) for item in node]
    if hasattr(node, '__dataclass_fields__'):
        res = {"_type": type(node).__name__}
        for field_name in node.__dataclass_fields__:
            val = getattr(node, field_name)
            res[field_name] = ast_to_dict(val)
        return res
    return str(node)


def format_ast_tree(node: Any, indent: int = 0) -> str:
    """AST tugunlarini chiroyli iyerarxik matn ko'rinishida formatlaydi"""
    prefix = "  " * indent
    if node is None:
        return f"{prefix}None\n"
    if isinstance(node, (int, float, str, bool)):
        return f"{prefix}{repr(node)}\n"
    if isinstance(node, list):
        if not node:
            return f"{prefix}[]\n"
        out = ""
        for i, item in enumerate(node):
            out += format_ast_tree(item, indent)
        return out
    if hasattr(node, '__dataclass_fields__'):
        out = f"{prefix}▸ {type(node).__name__}\n"
        for field_name in node.__dataclass_fields__:
            val = getattr(node, field_name)
            if isinstance(val, (list, Node)) or hasattr(val, '__dataclass_fields__'):
                out += f"{prefix}  .{field_name}:\n"
                out += format_ast_tree(val, indent + 2)
            else:
                out += f"{prefix}  .{field_name} = {val!r}\n"
        return out
    return f"{prefix}{node!r}\n"


def execute_zafira_code(source: str, timeout_seconds: float = 8.0) -> Dict[str, Any]:
    """
    Zafira kodini tokenizatsiya, tahlil (parsing), tip tekshiruvi va ijro qiladi.
    Natijada: { stdout, error, ast, tokens, execution_time_ms, ... } qaytaradi.
    """
    import time
    start_time = time.perf_counter()

    tokens_list: List[Dict[str, Any]] = []
    tokens_text = ""
    ast_formatted = ""
    ast_dict = None
    stdout_output = ""
    error_msg: Optional[str] = None
    result_val: Optional[str] = None

    # 1. TOKENIZATSIYA
    try:
        lexer = Lexer(source)
        raw_tokens = lexer.tokenize()
        tokens_list = [
            {
                "type": tok.type.name,
                "value": tok.value,
                "line": tok.line,
                "col": tok.col,
                "repr": repr(tok)
            }
            for tok in raw_tokens
        ]
        tokens_text = "\n".join(
            f"L{t['line']:02d}:C{t['col']:02d}  {t['type']:<15} {t['value']!r}"
            for t in tokens_list
        )
    except LexerError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return {
            "stdout": "",
            "error": f"[Lekser Xatosi] {e}",
            "ast": "",
            "ast_tree": None,
            "tokens": [],
            "tokens_text": "",
            "execution_time_ms": round(elapsed, 2)
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return {
            "stdout": "",
            "error": f"[Lekser Ichki Xatosi] {type(e).__name__}: {e}",
            "ast": "",
            "ast_tree": None,
            "tokens": [],
            "tokens_text": "",
            "execution_time_ms": round(elapsed, 2)
        }

    # 2. PARSING (AST)
    program: Optional[Program] = None
    try:
        parser = Parser(raw_tokens)
        program = parser.parse()
        ast_formatted = format_ast_tree(program)
        ast_dict = ast_to_dict(program)
    except ParseError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return {
            "stdout": "",
            "error": f"[Parser Xatosi] {e}",
            "ast": "",
            "ast_tree": None,
            "tokens": tokens_list,
            "tokens_text": tokens_text,
            "execution_time_ms": round(elapsed, 2)
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return {
            "stdout": "",
            "error": f"[Parser Ichki Xatosi] {type(e).__name__}: {e}",
            "ast": "",
            "ast_tree": None,
            "tokens": tokens_list,
            "tokens_text": tokens_text,
            "execution_time_ms": round(elapsed, 2)
        }

    # 3. TYPE CHECKING (Seal funksiyalar va invariantlar)
    try:
        checker = TypeChecker()
        checker.check(program)
    except TypeCheckError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return {
            "stdout": "",
            "error": f"[Tip Xatosi] {e}",
            "ast": ast_formatted,
            "ast_tree": ast_dict,
            "tokens": tokens_list,
            "tokens_text": tokens_text,
            "execution_time_ms": round(elapsed, 2)
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return {
            "stdout": "",
            "error": f"[Tip Tekshiruvi Xatosi] {type(e).__name__}: {e}",
            "ast": ast_formatted,
            "ast_tree": ast_dict,
            "tokens": tokens_list,
            "tokens_text": tokens_text,
            "execution_time_ms": round(elapsed, 2)
        }

    # 4. IJRO (INTERPRETATION) - Thread orqali timeout himoyasi bilan
    exec_result: Dict[str, Any] = {"stdout": "", "error": None, "return": None}

    def _run_worker():
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                interpreter = Interpreter()
                ret = interpreter.run(program)
                exec_result["return"] = ret
            exec_result["stdout"] = stdout_buf.getvalue() + (stderr_buf.getvalue() or "")
        except ZafiraError as ze:
            exec_result["stdout"] = stdout_buf.getvalue()
            exec_result["error"] = f"[Ijro Xatosi] {ze}"
        except Exception as ex:
            exec_result["stdout"] = stdout_buf.getvalue()
            exec_result["error"] = f"[Tizim Xatosi] {type(ex).__name__}: {ex}"

    runner_thread = threading.Thread(target=_run_worker, daemon=True)
    runner_thread.start()
    runner_thread.join(timeout=timeout_seconds)

    if runner_thread.is_alive():
        error_msg = f"[Vaqt Tugadi] Dastur ijrosi belgilangan {timeout_seconds} soniyadan oshib ketdi (cheksiz tsikl?)"
        stdout_output = exec_result.get("stdout", "")
    else:
        stdout_output = exec_result.get("stdout", "")
        error_msg = exec_result.get("error")
        if exec_result.get("return") is not None:
            result_val = _zf_str(exec_result["return"])

    elapsed = (time.perf_counter() - start_time) * 1000

    return {
        "stdout": stdout_output,
        "error": error_msg,
        "ast": ast_formatted,
        "ast_tree": ast_dict,
        "tokens": tokens_list,
        "tokens_text": tokens_text,
        "result": result_val,
        "execution_time_ms": round(elapsed, 2)
    }


class PlaygroundRequestHandler(http.server.BaseHTTPRequestHandler):
    """Playground HTTP so'rovlarini qabul qiluvchi handler"""

    server_version = "ZafiraPlayground/1.0"

    def _set_headers(self, status: int = 200, content_type: str = "application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(status=204)

    def do_GET(self):
        url_path = self.path.split('?')[0].split('#')[0]

        # Health tekshiruvi
        if url_path == '/api/health':
            self._set_headers(status=200, content_type="application/json; charset=utf-8")
            data = {"status": "ok", "version": "0.1.0-alpha", "engine": "Zafira Silicon Runtime"}
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        # Statik fayllar yo'li
        if url_path in ('', '/'):
            req_file = 'index.html'
        else:
            req_file = url_path.lstrip('/')

        file_path = os.path.join(PLAYGROUND_DIR, req_file)

        # Xavfsizlik: playground papkasidan tashqariga chiqishni taqiqlash
        real_file_path = os.path.abspath(file_path)
        if not real_file_path.startswith(os.path.abspath(PLAYGROUND_DIR)):
            self._set_headers(status=403, content_type="text/plain; charset=utf-8")
            self.wfile.write(b"403 Taqiqlangan")
            return

        if not os.path.isfile(real_file_path):
            self._set_headers(status=404, content_type="text/plain; charset=utf-8")
            self.wfile.write(b"404 Fayl topilmadi")
            return

        # Content-Type ni aniqlash
        ext = os.path.splitext(real_file_path)[1].lower()
        mime_types = {
            '.html': 'text/html; charset=utf-8',
            '.css': 'text/css; charset=utf-8',
            '.js': 'application/javascript; charset=utf-8',
            '.json': 'application/json; charset=utf-8',
            '.svg': 'image/svg+xml',
            '.png': 'image/png',
            '.ico': 'image/x-icon',
            '.zf': 'text/plain; charset=utf-8',
        }
        content_type = mime_types.get(ext, 'application/octet-stream')

        try:
            with open(real_file_path, 'rb') as f:
                content = f.read()
            self._set_headers(status=200, content_type=content_type)
            self.wfile.write(content)
        except Exception as e:
            self._set_headers(status=500, content_type="text/plain; charset=utf-8")
            self.wfile.write(f"500 Server xatosi: {e}".encode('utf-8'))

    def do_POST(self):
        url_path = self.path.split('?')[0].split('#')[0]

        if url_path == '/api/run':
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length).decode('utf-8', errors='replace')

            # Kodni JSON yoki to'g'ridan-to'g'ri matndan olish
            code = ""
            try:
                data = json.loads(post_body)
                code = data.get("code", "")
            except Exception:
                code = post_body

            # Kodni bajarish
            result = execute_zafira_code(code)

            self._set_headers(status=200, content_type="application/json; charset=utf-8")
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            return

        self._set_headers(status=404, content_type="application/json; charset=utf-8")
        self.wfile.write(json.dumps({"error": "Endpoint topilmadi"}).encode('utf-8'))

    def log_message(self, format, *args):
        # Jimjit rejim (testlar va konsol toza bo'lishi uchun)
        if os.environ.get('ZAFIRA_DEBUG_SERVER'):
            super().log_message(format, *args)


def create_server(host: str = "127.0.0.1", port: int = 5000) -> http.server.ThreadingHTTPServer:
    """Threading HTTP server obyektini yaratadi"""
    server_address = (host, port)
    httpd = http.server.ThreadingHTTPServer(server_address, PlaygroundRequestHandler)
    return httpd


def start_playground_server(port: int = 5000, host: str = "127.0.0.1", open_browser: bool = True):
    """Playground serverini ishga tushiradi"""
    # Windows terminalda UTF-8
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

    httpd = create_server(host, port)
    url = f"http://{host}:{port}/"

    banner = f"""
╔══════════════════════════════════════════════════════╗
║   🔷  Z A F I R A   O N L I N E   S T U D I O  🔷    ║
║        Web Interactive Playground v0.1.0-alpha       ║
╚══════════════════════════════════════════════════════╝
  📍 Manzil:     {url}
  📁 Papka:      {PLAYGROUND_DIR}
  ⚡ Holati:     Faol (Server ishlamoqda)
  🛑 To'xtatish: Ctrl + C bosing
"""
    print(banner, flush=True)

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🔷 Zafira Online Studio to'xtatildi. Xayr!")
    finally:
        httpd.server_close()


if __name__ == '__main__':
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    start_playground_server(port=port, open_browser=True)
