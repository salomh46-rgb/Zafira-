"""
Zafira Language - std.net moduli
Tarmoq va Web so'rovlari:
- net.get(url, headers=None) -> ZafiraStruct { status: 200, body: "...", ok: true, headers: ... }
- net.post(url, data=None, json=None, headers=None) -> ZafiraStruct
- net.listen(port, handler_fn, max_requests=None, threaded=False) -> Yengil HTTP server
- net.close(server) -> Serverni to'xtatish
"""

import http.server
import ssl
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from src.interpreter import ZafiraError, ZafiraList, ZafiraStruct
from src.std_json import _json_stringify


def _normalize_headers(headers: Optional[Any]) -> Dict[str, str]:
    if headers is None:
        return {}
    if isinstance(headers, ZafiraStruct):
        return {str(k): str(v) for k, v in headers.fields.items()}
    if isinstance(headers, dict):
        return {str(k): str(v) for k, v in headers.items()}
    raise ZafiraError(f"headers struct yoki dict bo'lishi kerak, lekin '{type(headers).__name__}' berildi")


def _get_ssl_context():
    try:
        ctx = ssl._create_unverified_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        return None


def _net_get(url: Any, headers: Optional[Any] = None) -> ZafiraStruct:
    url_str = str(url).strip()
    if not (url_str.startswith('http://') or url_str.startswith('https://')):
        raise ZafiraError(f"Noto'g'ri URL formati: '{url_str}'. URL 'http://' yoki 'https://' bilan boshlanishi kerak")

    req_headers = _normalize_headers(headers)
    if 'User-Agent' not in req_headers and 'user-agent' not in req_headers:
        req_headers['User-Agent'] = 'Zafira-Lang/1.0'

    req = urllib.request.Request(url_str, headers=req_headers, method='GET')
    ctx = _get_ssl_context()

    try:
        kwargs = {'timeout': 30}
        if url_str.startswith('https://') and ctx is not None:
            kwargs['context'] = ctx

        with urllib.request.urlopen(req, **kwargs) as resp:
            status = resp.status
            body_bytes = resp.read()
            body_str = body_bytes.decode('utf-8', errors='replace')
            resp_headers = dict(resp.headers.items())
            return ZafiraStruct('HttpResponse', {
                'status': status,
                'body': body_str,
                'ok': 200 <= status < 400,
                'headers': ZafiraStruct('HttpHeaders', resp_headers)
            })
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')
        resp_headers = dict(e.headers.items()) if e.headers else {}
        try:
            e.close()
        except Exception:
            pass
        return ZafiraStruct('HttpResponse', {
            'status': e.code,
            'body': err_body,
            'ok': False,
            'headers': ZafiraStruct('HttpHeaders', resp_headers)
        })
    except urllib.error.URLError as e:
        raise ZafiraError(f"Tarmoq xatosi (net.get): {e.reason}")
    except Exception as e:
        raise ZafiraError(f"net.get xatosi: {e}")


def _net_post(url: Any, data: Optional[Any] = None, json: Optional[Any] = None, headers: Optional[Any] = None) -> ZafiraStruct:
    url_str = str(url).strip()
    if not (url_str.startswith('http://') or url_str.startswith('https://')):
        raise ZafiraError(f"Noto'g'ri URL formati: '{url_str}'. URL 'http://' yoki 'https://' bilan boshlanishi kerak")

    req_headers = _normalize_headers(headers)
    if 'User-Agent' not in req_headers and 'user-agent' not in req_headers:
        req_headers['User-Agent'] = 'Zafira-Lang/1.0'

    # Agar json None bo'lsa va data struct/dict/list bo'lsa, avtomatik json deb qabul qilamiz
    if json is None and isinstance(data, (ZafiraStruct, ZafiraList, dict, list)):
        json = data
        data = None

    if json is not None:
        body_bytes = _json_stringify(json).encode('utf-8')
        if 'Content-Type' not in req_headers and 'content-type' not in req_headers:
            req_headers['Content-Type'] = 'application/json; charset=utf-8'
    elif data is not None:
        if isinstance(data, bytes):
            body_bytes = data
        else:
            body_bytes = str(data).encode('utf-8')
    else:
        body_bytes = b''

    req = urllib.request.Request(url_str, data=body_bytes, headers=req_headers, method='POST')
    ctx = _get_ssl_context()

    try:
        kwargs = {'timeout': 30}
        if url_str.startswith('https://') and ctx is not None:
            kwargs['context'] = ctx

        with urllib.request.urlopen(req, **kwargs) as resp:
            status = resp.status
            body_bytes = resp.read()
            body_str = body_bytes.decode('utf-8', errors='replace')
            resp_headers = dict(resp.headers.items())
            return ZafiraStruct('HttpResponse', {
                'status': status,
                'body': body_str,
                'ok': 200 <= status < 400,
                'headers': ZafiraStruct('HttpHeaders', resp_headers)
            })
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')
        resp_headers = dict(e.headers.items()) if e.headers else {}
        try:
            e.close()
        except Exception:
            pass
        return ZafiraStruct('HttpResponse', {
            'status': e.code,
            'body': err_body,
            'ok': False,
            'headers': ZafiraStruct('HttpHeaders', resp_headers)
        })
    except urllib.error.URLError as e:
        raise ZafiraError(f"Tarmoq xatosi (net.post): {e.reason}")
    except Exception as e:
        raise ZafiraError(f"net.post xatosi: {e}")


# ─── YENGIL HTTP SERVER (LISTEN) ───

class _ZafiraRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Tinch rejim (konsol toza bo'lishi uchun)
        pass

    def _dispatch(self, method: str):
        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b''
        body_str = body_bytes.decode('utf-8', errors='replace')

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = parsed_url.query

        headers_dict = dict(self.headers.items())
        headers_struct = ZafiraStruct('HttpHeaders', headers_dict)

        req_struct = ZafiraStruct('HttpRequest', {
            'method': method,
            'path': path,
            'query': query,
            'body': body_str,
            'headers': headers_struct
        })

        try:
            handler_fn = self.server.handler_fn
            res = handler_fn(req_struct)

            status_code = 200
            resp_body = b''
            content_type = 'text/plain; charset=utf-8'
            extra_headers = {}

            if isinstance(res, str):
                resp_body = res.encode('utf-8')
            elif isinstance(res, (int, float)):
                resp_body = str(res).encode('utf-8')
            elif isinstance(res, (ZafiraList, list)):
                content_type = 'application/json; charset=utf-8'
                resp_body = _json_stringify(res).encode('utf-8')
            elif isinstance(res, ZafiraStruct):
                has_http_status = (
                    'status' in res.fields
                    and isinstance(res.fields['status'], int)
                    and 100 <= res.fields['status'] <= 599
                )
                if has_http_status and 'body' in res.fields:
                    status_code = res.fields['status']
                    b_val = res.fields.get('body', '')
                    if isinstance(b_val, (ZafiraStruct, ZafiraList, dict, list)):
                        content_type = 'application/json; charset=utf-8'
                        resp_body = _json_stringify(b_val).encode('utf-8')
                    else:
                        resp_body = str(b_val).encode('utf-8')
                    if 'headers' in res.fields:
                        h = res.fields['headers']
                        if isinstance(h, ZafiraStruct):
                            extra_headers = h.fields
                        elif isinstance(h, dict):
                            extra_headers = h
                else:
                    content_type = 'application/json; charset=utf-8'
                    resp_body = _json_stringify(res).encode('utf-8')
            elif res is None:
                status_code = 204
                resp_body = b''
            else:
                resp_body = str(res).encode('utf-8')

            self.send_response(status_code)
            self.send_header('Content-Type', extra_headers.get('Content-Type', content_type))
            self.send_header('Content-Length', str(len(resp_body)))
            for hk, hv in extra_headers.items():
                if hk.lower() not in ('content-type', 'content-length'):
                    self.send_header(str(hk), str(hv))
            self.end_headers()
            self.wfile.write(resp_body)

        except Exception as e:
            err_msg = f"Server xatosi: {e}"
            err_bytes = err_msg.encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(err_bytes)))
            self.end_headers()
            self.wfile.write(err_bytes)

    def do_GET(self): self._dispatch('GET')
    def do_POST(self): self._dispatch('POST')
    def do_PUT(self): self._dispatch('PUT')
    def do_DELETE(self): self._dispatch('DELETE')
    def do_PATCH(self): self._dispatch('PATCH')


class _ZafiraHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, handler_fn):
        self.handler_fn = handler_fn
        super().__init__(server_address, _ZafiraRequestHandler)


def _net_listen(port: Any, handler_fn: Any, max_requests: Optional[Any] = None, threaded: bool = False, host: str = '127.0.0.1') -> Any:
    if not callable(handler_fn):
        raise ZafiraError(f"net.listen() uchun handler funksiya kutilgan, lekin '{type(handler_fn).__name__}' berildi")

    port_num = int(port)
    try:
        server = _ZafiraHTTPServer((host, port_num), handler_fn)
    except Exception as e:
        raise ZafiraError(f"Port {port_num} da server ochib bo'lmadi: {e}")

    def _close_server():
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass

    server_struct = ZafiraStruct('HttpServer', {
        'port': port_num,
        'host': host,
        'close': _close_server,
        'stop': _close_server,
    })

    if threaded:
        th = threading.Thread(target=server.serve_forever, daemon=True)
        th.start()
        return server_struct

    if max_requests is not None:
        count = 0
        limit = int(max_requests)
        while count < limit:
            server.handle_request()
            count += 1
        _close_server()
        return server_struct

    # Bloklovchi asosiy rejim
    print(f"[Zafira net] Server http://{host}:{port_num} manzilida ishga tushdi...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Zafira net] Server to'xtatildi.")
    finally:
        _close_server()
    return server_struct


def _net_close(server_obj: Any):
    """Serverni to'xtatadi."""
    if isinstance(server_obj, ZafiraStruct) and 'close' in server_obj.fields:
        server_obj.fields['close']()
    elif hasattr(server_obj, 'shutdown'):
        server_obj.shutdown()


def create_net_module():
    """std.net ZafiraModule nusxasini yaratadi."""
    from src.stdlib import ZafiraModule
    return ZafiraModule('net', {
        'get': _net_get,
        'post': _net_post,
        'listen': _net_listen,
        'close': _net_close,
    })
