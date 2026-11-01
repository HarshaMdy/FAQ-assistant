import sys
import json
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.orchestrator import ask
from app.web_ui import HTML_TEMPLATE, run_server

def app(environ, start_response):
    """
    Standard WSGI Application callable for Vercel Serverless Functions.
    Handles GET / for web UI and POST /api/ask for Q&A orchestration.
    """
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    # Normalize trailing slash for API route
    if path.endswith("/") and len(path) > 1:
        clean_path = path[:-1]
    else:
        clean_path = path

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
            result = ask(query)
        except Exception as e:
            result = {
                "status": "refused",
                "answer": f"Processing error: {str(e)}",
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

# Vercel recognizes both `app` and `application` WSGI callables
application = app

if __name__ == "__main__":
    run_server()
