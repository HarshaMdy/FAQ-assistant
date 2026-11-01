import os
import sys
import json
import traceback
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure serverless writable cache directories
os.environ.setdefault("HF_HOME", "/tmp/huggingface")
os.environ.setdefault("TORCH_HOME", "/tmp/torch")

from app.template import HTML_TEMPLATE

def app(environ, start_response):
    """
    Standard WSGI Application callable for Vercel Serverless Functions.
    Handles any GET request with the web UI and any POST with the Q&A pipeline.
    """
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    # Handle favicon
    if "favicon.ico" in path:
        status = "204 No Content"
        start_response(status, [])
        return [b""]

    # All GET requests serve the interactive Chat UI
    if method == "GET":
        body = HTML_TEMPLATE.encode("utf-8")
        status = "200 OK"
        response_headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ]
        start_response(status, response_headers)
        return [body]

    # POST requests handle Q&A queries
    if method == "POST":
        try:
            raw_len = environ.get("CONTENT_LENGTH")
            content_length = int(raw_len) if raw_len else 0
        except (ValueError, TypeError):
            content_length = 0

        try:
            if content_length > 0:
                raw_bytes = environ["wsgi.input"].read(content_length)
            else:
                raw_bytes = environ["wsgi.input"].read()
            request_body = raw_bytes.decode("utf-8") if raw_bytes else "{}"
        except Exception:
            request_body = "{}"

        try:
            req_data = json.loads(request_body) if request_body.strip() else {}
            query = req_data.get("query", "").strip()

            from app.orchestrator import ask
            result = ask(query)
        except Exception as e:
            traceback.print_exc()
            result = {
                "status": "refused",
                "answer": f"Service notice: {str(e)}",
                "source_url": "",
                "last_updated": "",
            }

        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        status = "200 OK"
        response_headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ]
        start_response(status, response_headers)
        return [body]

    status = "405 Method Not Allowed"
    response_headers = [("Content-Type", "text/plain")]
    start_response(status, response_headers)
    return [b"Method Not Allowed"]

application = app

if __name__ == "__main__":
    from app.web_ui import run_server
    run_server()
