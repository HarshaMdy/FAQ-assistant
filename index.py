import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.web_ui import RequestHandler

# Vercel Python Serverless Function entrypoint
class handler(RequestHandler):
    pass

# Fallback alias for WSGI/ASGI checkers
app = handler

if __name__ == "__main__":
    from app.web_ui import run_server
    run_server()
