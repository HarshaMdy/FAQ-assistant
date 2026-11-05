# app/web_ui.py
"""
Phase 8: Standalone Interactive Web Chat UI
Built with Python's standard library ThreadingHTTPServer. Zero external UI dependencies required.
Pre-warms the retriever and model on startup for instant response latency.
"""

import sys
import json
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.orchestrator import ask
from pipeline.retriever import get_retriever
from app.template import HTML_TEMPLATE

DISCLAIMER_TEXT = "Facts-only. No investment advice."


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/ask":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                query = data.get("query", "")
                result = ask(query)
            except Exception as e:
                result = {
                    "status": "refused",
                    "answer": f"Processing error: {str(e)}",
                    "source_url": "",
                    "last_updated": "",
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        sys.stderr.write(f"[WebUI] {args[0]} - {args[1]}\n")


def run_server(port=7860):
    print("[WebUI] Initializing retriever...")
    try:
        get_retriever()
    except Exception as e:
        print(f"[WebUI] Note: Using fallback disk retriever: {e}")
    print("[WebUI] Ready for incoming requests.")

    server = ThreadingHTTPServer(("127.0.0.1", port), RequestHandler)
    print(f"\n=======================================================")
    print(f" HDFC Mutual Fund FAQ Assistant — Web UI Running")
    print(f" Local URL: http://127.0.0.1:{port}")
    print(f" Disclaimer: Facts-only. No investment advice.")
    print(f" Press Ctrl+C to stop.")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[WebUI] Server stopped.")


if __name__ == "__main__":
    port = 7860
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
