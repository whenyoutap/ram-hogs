"""The dashboard's local server: 127.0.0.1 only. Every /api call needs this run's random token in a header (other sites can't
set it), the Host must be this machine, and an Origin, when present, must be this server. Static files come only from web/."""
import json, mimetypes, secrets, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import engine

WEB = Path(__file__).resolve().parent.parent / "web"
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"


def serve(port, open_browser=True, top=12):
    token = secrets.token_urlsafe(24)
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def send(self, code, body, ctype):
            self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Security-Policy", CSP)
            self.send_header("X-Content-Type-Options", "nosniff"); self.send_header("Referrer-Policy", "no-referrer"); self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            if self.headers.get("Host") not in hosts: return self.send(403, b"forbidden host", "text/plain")
            o = self.headers.get("Origin")
            if o and o != "http://" + self.headers.get("Host"): return self.send(403, b"forbidden origin", "text/plain")   # scheme, host and port must all match
            path = urlparse(self.path).path
            if path == "/api/snapshot":
                if self.headers.get("X-Token") != token: return self.send(403, b"bad token", "text/plain")
                return self.send(200, json.dumps(engine.snapshot(top=top)).encode(), "application/json")
            if path == "/":
                html = (WEB / "index.html").read_text().replace("__TOKEN__", token)
                return self.send(200, html.encode(), "text/html; charset=utf-8")
            f = (WEB / path.lstrip("/")).resolve()
            if WEB.resolve() not in f.parents or not f.is_file(): return self.send(404, b"not found", "text/plain")
            return self.send(200, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    url = f"http://127.0.0.1:{port}/"
    print(f"RAM hogs dashboard: {url}  (this computer only; Ctrl+C to stop)")
    if open_browser: webbrowser.open(url)
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\nstopped")
