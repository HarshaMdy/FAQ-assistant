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
    Zero-dependency startup for GET / to guarantee instant page rendering.
    """
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    # Normalize trailing slash
    clean_path = path[:-1] if path.endswith("/") and len(path) > 1 else path

    if method == "GET" and (clean_path == "" or clean_path == "/"):
        body = HTML_TEMPLATE.encode("utf-8")
        status = "200 OK"
        response_headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ]
        start_response(status, response_headers)
        return [body]

    elif method == "POST" and clean_path == "/api/ask":
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
        except (ValueError, TypeError):
            content_length = 0

        request_body = environ["wsgi.input"].read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            req_data = json.loads(request_body)
            query = req_data.get("query", "")
            
            # Lazy import to keep cold-start page loads lightweight
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

    elif method == "GET" and clean_path == "/favicon.ico":
        status = "204 No Content"
        start_response(status, [])
        return [b""]

    else:
        status = "404 Not Found"
        response_headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", "9"),
        ]
        start_response(status, response_headers)
        return [b"Not Found"]

application = app

if __name__ == "__main__":
    from app.web_ui import run_server
    run_server()
