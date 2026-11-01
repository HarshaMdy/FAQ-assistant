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

DISCLAIMER_TEXT = "Facts-only. No investment advice."

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HDFC Mutual Fund FAQ Assistant</title>
  <style>
    :root {
      --primary: #00d09c;
      --primary-dark: #00b386;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #1e293b;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --user-bubble: #e6f9f5;
      --bot-bubble: #f1f5f9;
      --warning-bg: #fffbeb;
      --warning-border: #fef08a;
      --warning-text: #854d0e;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background-color: var(--bg); color: var(--text); display: flex; flex-direction: column; height: 100vh; }
    header { background: var(--card-bg); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }
    .header-title { display: flex; align-items: center; gap: 12px; }
    .logo-badge { background: #00d09c; color: white; font-weight: bold; padding: 6px 10px; border-radius: 8px; font-size: 14px; }
    .disclaimer-banner { background: var(--warning-bg); border-bottom: 1px solid var(--warning-border); color: var(--warning-text); padding: 10px 24px; font-size: 13px; text-align: center; }
    .container { flex: 1; max-width: 900px; width: 100%; margin: 0 auto; display: flex; flex-direction: column; overflow: hidden; padding: 16px; }
    .chat-box { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 14px; }
    .message { max-width: 80%; padding: 14px 18px; border-radius: 12px; line-height: 1.5; font-size: 14.5px; }
    .user-msg { align-self: flex-end; background: var(--user-bubble); color: #064e3b; border: 1px solid #a7f3d0; border-bottom-right-radius: 2px; }
    .bot-msg { align-self: flex-start; background: var(--bot-bubble); border: 1px solid var(--border); border-bottom-left-radius: 2px; }
    .bot-msg.refused { background: #fff5f5; border-color: #fed7d7; color: #9b2c2c; }
    .source-link { display: inline-block; margin-top: 8px; font-size: 12px; color: #0284c7; text-decoration: none; font-weight: 500; }
    .source-link:hover { text-decoration: underline; }
    .updated-time { font-size: 11px; color: var(--text-muted); margin-top: 6px; }
    .pills-container { padding: 10px 0; display: flex; flex-wrap: wrap; gap: 8px; }
    .pill { background: var(--card-bg); border: 1px solid var(--border); border-radius: 20px; padding: 6px 14px; font-size: 12.5px; color: #334155; cursor: pointer; transition: all 0.2s; }
    .pill:hover { border-color: var(--primary); color: var(--primary-dark); background: #f0fdf9; }
    .input-row { display: flex; gap: 10px; background: var(--card-bg); padding: 12px; border-radius: 12px; border: 1px solid var(--border); }
    input[type="text"] { flex: 1; border: none; outline: none; font-size: 14.5px; padding: 6px; }
    button.send-btn { background: var(--primary); color: white; border: none; border-radius: 8px; padding: 8px 18px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
    button.send-btn:hover { background: var(--primary-dark); }
    button.clear-btn { background: transparent; border: 1px solid var(--border); color: var(--text-muted); border-radius: 8px; padding: 8px 14px; cursor: pointer; }
    button.clear-btn:hover { background: #f1f5f9; }
  </style>
</head>
<body>
  <header>
    <div class="header-title">
      <div class="logo-badge">Groww MF</div>
      <div>
        <h2 style="font-size: 18px;">HDFC Mutual Fund FAQ Assistant</h2>
        <span style="font-size: 12px; color: var(--text-muted);">Factual Scheme Q&A • Official Groww Public Pages</span>
      </div>
    </div>
  </header>

  <div class="disclaimer-banner">
    <strong>Notice:</strong> Facts-only. No investment advice. This assistant does not give portfolio advice or compute returns.
  </div>

  <div class="container">
    <div class="chat-box" id="chatBox">
      <div class="message bot-msg">
        👋 <strong>Welcome!</strong> I answer factual questions about HDFC mutual fund schemes based strictly on official Groww public documentation.
        <br><br>
        Ask about <em>expense ratios, exit loads, minimum SIP amounts, lock-in periods, or benchmarks</em>.
      </div>
    </div>

    <div class="pills-container">
      <span style="font-size: 12px; color: var(--text-muted); align-self: center;">Examples:</span>
      <div class="pill" onclick="sendExample('What is the expense ratio of HDFC Large Cap Fund?')">Expense ratio of HDFC Large Cap</div>
      <div class="pill" onclick="sendExample('What is the lock-in period for HDFC ELSS Tax Saver Fund?')">ELSS lock-in period</div>
      <div class="pill" onclick="sendExample('What is the minimum SIP for HDFC Mid Cap Fund?')">Minimum SIP for HDFC Mid Cap</div>
      <div class="pill" onclick="sendExample('What is the exit load for HDFC Flexi Cap Fund?')">Exit load of HDFC Flexi Cap</div>
      <div class="pill" onclick="sendExample('Should I invest in HDFC Large Cap?')">Should I invest? (Test Refusal)</div>
    </div>

    <div class="input-row">
      <input type="text" id="userInput" placeholder="Ask a factual question (e.g. 'What is the exit load for HDFC Flexi Cap?')..." onkeydown="if(event.key==='Enter') sendMessage()" />
      <button class="send-btn" id="sendBtn" onclick="sendMessage()">Ask</button>
      <button class="clear-btn" onclick="clearChat()">Clear</button>
    </div>
  </div>

  <script>
    const chatBox = document.getElementById('chatBox');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');

    function appendMessage(text, role, meta = {}) {
      const msg = document.createElement('div');
      msg.className = 'message ' + (role === 'user' ? 'user-msg' : 'bot-msg');
      if (meta.refused) msg.classList.add('refused');

      const safeText = String(text || '');
      let html = safeText.split('\\n').join('<br>');
      if (meta.source_url) {
        html += '<br><a class="source-link" href="' + meta.source_url + '" target="_blank">🔗 Official Source: ' + meta.source_url + '</a>';
      }
      if (meta.last_updated) {
        html += '<div class="updated-time">🕒 Last updated from sources: ' + meta.last_updated + '</div>';
      }
      msg.innerHTML = html;
      chatBox.appendChild(msg);
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    function sendExample(q) {
      userInput.value = q;
      sendMessage();
    }

    async function sendMessage() {
      const q = userInput.value.trim();
      if (!q) return;

      appendMessage(q, 'user');
      userInput.value = '';
      userInput.disabled = true;
      sendBtn.disabled = true;

      const loadingMsg = document.createElement('div');
      loadingMsg.className = 'message bot-msg';
      loadingMsg.id = 'loadingIndicator';
      loadingMsg.innerText = 'Searching official records...';
      chatBox.appendChild(loadingMsg);
      chatBox.scrollTop = chatBox.scrollHeight;

      try {
        const resp = await fetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: q })
        });
        const data = await resp.json();
        const indicator = document.getElementById('loadingIndicator');
        if (indicator) indicator.remove();

        appendMessage(data.answer, 'bot', {
          source_url: data.source_url,
          last_updated: data.last_updated,
          refused: data.status === 'refused'
        });
      } catch (err) {
        const indicator = document.getElementById('loadingIndicator');
        if (indicator) indicator.remove();
        appendMessage('Error retrieving answer: ' + err.message, 'bot', { refused: true });
      } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
      }
    }

    function clearChat() {
      chatBox.innerHTML = `
        <div class="message bot-msg">
          👋 <strong>Welcome!</strong> Chat cleared. How can I assist you with HDFC scheme factual data?
        </div>
      `;
    }
  </script>
</body>
</html>
"""


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
        # Clean logging
        sys.stderr.write(f"[WebUI] {args[0]} - {args[1]}\n")


def run_server(port=7860):
    # Pre-warm the retriever model in memory so queries respond instantly
    print("[WebUI] Pre-warming embedding model and vector store...")
    get_retriever()
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
