# app/template.py
HTML_TEMPLATE = r"""<!DOCTYPE html>
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
    .pill { background: var(--card-bg); border: 1px solid var(--border); border-radius: 20px; padding: 6px 14px; font-size: 12.5px; color: #334155; cursor: pointer; transition: all 0.2s; user-select: none; }
    .pill:hover { border-color: var(--primary); color: var(--primary-dark); background: #f0fdf9; }
    .input-row { display: flex; gap: 10px; background: var(--card-bg); padding: 12px; border-radius: 12px; border: 1px solid var(--border); }
    input[type="text"] { flex: 1; border: none; outline: none; font-size: 14.5px; padding: 6px; }
    button.send-btn { background: var(--primary); color: white; border: none; border-radius: 8px; padding: 8px 18px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
    button.send-btn:hover { background: var(--primary-dark); }
    button.send-btn:disabled { background: #94a3b8; cursor: not-allowed; }
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
      <div class="pill" data-query="What is the expense ratio of HDFC Large Cap Fund?">Expense ratio of HDFC Large Cap</div>
      <div class="pill" data-query="What is the lock-in period for HDFC ELSS Tax Saver Fund?">ELSS lock-in period</div>
      <div class="pill" data-query="What is the minimum SIP for HDFC Mid Cap Fund?">Minimum SIP for HDFC Mid Cap</div>
      <div class="pill" data-query="What is the exit load for HDFC Flexi Cap Fund?">Exit load of HDFC Flexi Cap</div>
      <div class="pill" data-query="Should I invest in HDFC Large Cap?">Should I invest? (Test Refusal)</div>
    </div>

    <div class="input-row">
      <input type="text" id="userInput" placeholder="Ask a factual question (e.g. 'What is the exit load for HDFC Flexi Cap?')..." autocomplete="off" />
      <button class="send-btn" id="sendBtn">Ask</button>
      <button class="clear-btn" id="clearBtn">Clear</button>
    </div>
  </div>

  <script>
    (function () {
      var chatBox = document.getElementById('chatBox');
      var userInput = document.getElementById('userInput');
      var sendBtn = document.getElementById('sendBtn');
      var clearBtn = document.getElementById('clearBtn');

      function formatText(raw) {
        if (!raw) return '';
        var safe = document.createElement('div');
        safe.textContent = String(raw);
        return safe.innerHTML.replace(/\r?\n/g, '<br>');
      }

      function appendMessage(text, sender, meta) {
        meta = meta || {};
        var msg = document.createElement('div');
        msg.className = 'message ' + sender + '-msg' + (meta.refused ? ' refused' : '');

        var html = formatText(text);
        if (meta.source_url) {
          html += '<br><a class="source-link" href="' + meta.source_url + '" target="_blank" rel="noopener">Source: Official Groww Scheme Documentation ↗</a>';
        }
        if (meta.last_updated) {
          html += '<div class="updated-time">Last Synced: ' + meta.last_updated + '</div>';
        }
        msg.innerHTML = html;
        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
        return msg;
      }

      function submitQuery(overrideQuery) {
        var query = (typeof overrideQuery === 'string' ? overrideQuery : userInput.value).trim();
        if (!query) return;

        appendMessage(query, 'user');
        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;

        var loadingMsg = appendMessage('Searching official records...', 'bot');
        loadingMsg.id = 'loadingIndicator';

        fetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query })
        })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          var indicator = document.getElementById('loadingIndicator');
          if (indicator) indicator.remove();

          appendMessage(data.answer || 'No response generated.', 'bot', {
            refused: data.status === 'refused',
            source_url: data.source_url,
            last_updated: data.last_updated
          });
        })
        .catch(function (err) {
          var indicator = document.getElementById('loadingIndicator');
          if (indicator) indicator.remove();
          appendMessage('Error retrieving answer: ' + err.message, 'bot', { refused: true });
        })
        .finally(function () {
          userInput.disabled = false;
          sendBtn.disabled = false;
          userInput.focus();
        });
      }

      // Event listeners
      userInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          submitQuery();
        }
      });

      sendBtn.addEventListener('click', function (e) {
        e.preventDefault();
        submitQuery();
      });

      clearBtn.addEventListener('click', function () {
        chatBox.innerHTML = '<div class="message bot-msg">👋 <strong>Welcome!</strong> Chat cleared. How can I assist you with HDFC scheme factual data?</div>';
        userInput.focus();
      });

      // Delegate pill clicks
      var pills = document.querySelectorAll('.pill');
      pills.forEach(function (pill) {
        pill.addEventListener('click', function () {
          var q = this.getAttribute('data-query');
          if (q) {
            userInput.value = q;
            submitQuery(q);
          }
        });
      });

      userInput.focus();
    })();
  </script>
</body>
</html>
"""
