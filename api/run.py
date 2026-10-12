import json
import sys
import os
from http.server import BaseHTTPRequestHandler

# Loyiha ildiz katalogini Python yo'liga qo'shish
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.playground_server import execute_zafira_code


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))

        # DoS / OOM himoyasi (maksimal 64 KB)
        if content_length > 64 * 1024:
            err_res = json.dumps({"error": "So'rov hajmi juda katta (maksimal 64 KB)"}, ensure_ascii=False).encode("utf-8")
            self.send_response(413)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(err_res)))
            self.end_headers()
            self.wfile.write(err_res)
            return

        body = self.rfile.read(content_length).decode("utf-8", errors="replace")
        
        try:
            payload = json.loads(body)
            source = payload.get("source") or payload.get("code") or ""
        except Exception:
            source = body

        # Xavfsiz sandbox rejimida bajarish
        result = execute_zafira_code(source, timeout_seconds=6.0, safe_mode=True)
        res_bytes = json.dumps(result, ensure_ascii=False).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(res_bytes)))
        self.end_headers()
        self.wfile.write(res_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        res = {
            "status": "ok",
            "language": "Zafira",
            "version": "1.0.0",
            "edition": "Silicon-Native LTS",
            "author": "Javohirbek Asqarov (Jasper)"
        }
        res_bytes = json.dumps(res, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(res_bytes)))
        self.end_headers()
        self.wfile.write(res_bytes)
