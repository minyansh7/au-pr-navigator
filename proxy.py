#!/usr/bin/env python3
"""
Local CORS proxy for AU/PR Navigator.
Bridges the HTML dashboard to the Anthropic API (browser can't call it directly).

Usage:
  python3 proxy.py --key sk-ant-YOUR_KEY
  ANTHROPIC_API_KEY=sk-ant-... python3 proxy.py
  python3 proxy.py --port 8765   # default port
"""
import json, os, sys, ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import HTTPError

PORT = 8765
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def parse_args():
    global PORT, API_KEY
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--key" and i + 1 < len(args):
            API_KEY = args[i + 1]; i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            PORT = int(args[i + 1]); i += 2
        else:
            i += 1


class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"ok": True}).encode()
            self.send_response(200); self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path != "/messages":
            self.send_response(404); self.end_headers(); return

        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))
        key = payload.pop("apiKey", None) or API_KEY

        if not key:
            err = json.dumps({"error": "No API key — set ANTHROPIC_API_KEY or pass --key"}).encode()
            self.send_response(400); self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(err); return

        req = Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, context=ssl.create_default_context()) as resp:
                self.send_response(200); self._cors()
                self.send_header("Content-Type",
                                  resp.headers.get("Content-Type", "text/event-stream"))
                self.end_headers()
                while True:
                    chunk = resp.read(512)
                    if not chunk: break
                    self.wfile.write(chunk); self.wfile.flush()
        except HTTPError as e:
            body = e.read()
            self.send_response(e.code); self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(body)


if __name__ == "__main__":
    parse_args()
    server = HTTPServer(("localhost", PORT), ProxyHandler)
    print(f"\n🚀  AU/PR Navigator proxy  →  http://localhost:{PORT}")
    print(f"   API key : {'SET ✓' if API_KEY else 'NOT SET — pass --key sk-ant-...'}")
    print(f"   Next    : open au_pr_strategy.html in browser, click Run Strategy\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Proxy stopped.")
