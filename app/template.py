# app/template.py
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Groww • HDFC Mutual Fund FAQ Assistant</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #00D09C;
      --primary-hover: #00B386;
      --primary-light: #E8FAF4;
      --primary-border: #A7F3D0;
      --bg: #F8FAFC;
      --card-bg: #FFFFFF;
      --text-main: #0F172A;
      --text-muted: #64748B;
      --text-subtle: #94A3B8;
      --border-color: #E2E8F0;
      --border-light: #F1F5F9;
      --user-bubble: #E6F9F5;
      --user-text: #064E3B;
      --bot-bubble: #FFFFFF;
      --notice-bg: #FFFBEB;
      --notice-border: #FEF3C7;
      --notice-text: #92400E;
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
      --shadow-glow: 0 4px 14px 0 rgba(0, 208, 156, 0.25);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      -webkit-font-smoothing: antialiased;
    }

    body {
      background-color: var(--bg);
      color: var(--text-main);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    /* Top Navigation Bar */
    header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border-color);
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: var(--shadow-sm);
      z-index: 10;
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .brand-logo {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: linear-gradient(135deg, #00D09C 0%, #009671 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #FFFFFF;
      font-weight: 700;
      font-size: 15px;
      letter-spacing: -0.5px;
      box-shadow: 0 2px 8px rgba(0, 208, 156, 0.3);
    }

    .brand-info h1 {
      font-size: 17px;
      font-weight: 700;
      color: var(--text-main);
      letter-spacing: -0.3px;
    }

    .brand-info p {
      font-size: 12.5px;
      color: var(--text-muted);
      margin-top: 1px;
    }

    .header-status {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #F1F5F9;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
      color: #475569;
      border: 1px solid #E2E8F0;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--primary);
      box-shadow: 0 0 0 2px rgba(0, 208, 156, 0.2);
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(0, 208, 156, 0.5); }
      70% { box-shadow: 0 0 0 6px rgba(0, 208, 156, 0); }
      100% { box-shadow: 0 0 0 0 rgba(0, 208, 156, 0); }
    }

    /* Disclaimer Bar */
    .disclaimer-bar {
      background: var(--notice-bg);
      border-bottom: 1px solid var(--notice-border);
      color: var(--notice-text);
      padding: 8px 24px;
      font-size: 12.5px;
      text-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }

    .disclaimer-bar svg {
      flex-shrink: 0;
      width: 15px;
      height: 15px;
      fill: currentColor;
    }

    /* Main Container */
    .main-wrapper {
      flex: 1;
      max-width: 960px;
      width: 100%;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 18px 20px 14px 20px;
    }

    /* Chat Area */
    .chat-container {
      flex: 1;
      overflow-y: auto;
      padding: 10px 4px 18px 4px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      scroll-behavior: smooth;
    }

    .chat-container::-webkit-scrollbar {
      width: 6px;
    }

    .chat-container::-webkit-scrollbar-thumb {
      background-color: #CBD5E1;
      border-radius: 4px;
    }

    /* Message Bubbles */
    .message-row {
      display: flex;
      gap: 10px;
      align-items: flex-start;
      max-width: 82%;
      animation: fadeIn 0.2s ease-in-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .message-row.user-row {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .message-row.bot-row {
      align-self: flex-start;
    }

    .avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .bot-avatar {
      background: #E8FAF4;
      border: 1.5px solid var(--primary-border);
      color: #00D09C;
    }

    .user-avatar {
      background: #F1F5F9;
      border: 1px solid #CBD5E1;
      color: #475569;
    }

    .message-bubble {
      padding: 14px 18px;
      border-radius: 16px;
      font-size: 14.5px;
      line-height: 1.55;
      word-break: break-word;
      position: relative;
    }

    .user-bubble {
      background: var(--user-bubble);
      color: var(--user-text);
      border: 1px solid var(--primary-border);
      border-top-right-radius: 4px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }

    .bot-bubble {
      background: var(--bot-bubble);
      color: var(--text-main);
      border: 1px solid var(--border-color);
      border-top-left-radius: 4px;
      box-shadow: var(--shadow-sm);
    }

    .bot-bubble.refused {
      background: #FEF2F2;
      border-color: #FECACA;
      color: #991B1B;
    }

    /* Welcome Card Styling */
    .welcome-card {
      background: #FFFFFF;
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 22px;
      box-shadow: var(--shadow-sm);
    }

    .welcome-card h2 {
      font-size: 16px;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }

    .welcome-card p {
      font-size: 13.5px;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 14px;
    }

    .schemes-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .scheme-badge {
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      color: #334155;
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 500;
    }

    /* Citations and Metadata */
    .citation-card {
      margin-top: 10px;
      padding-top: 9px;
      border-top: 1px solid #F1F5F9;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .source-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 12px;
      font-weight: 600;
      color: #0284C7;
      background: #F0F9FF;
      border: 1px solid #BAE6FD;
      padding: 4px 10px;
      border-radius: 6px;
      text-decoration: none;
      transition: all 0.2s ease;
    }

    .source-pill:hover {
      background: #E0F2FE;
      color: #0369A1;
      text-decoration: none;
    }

    .sync-timestamp {
      font-size: 11.5px;
      color: var(--text-subtle);
      font-weight: 500;
    }

    /* Loading Indicator */
    .typing-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 2px;
    }

    .typing-dot {
      width: 7px;
      height: 7px;
      background: var(--primary);
      border-radius: 50%;
      animation: typingBounce 1.4s infinite ease-in-out both;
    }

    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }

    @keyframes typingBounce {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
      40% { transform: scale(1); opacity: 1; }
    }

    .searching-label {
      font-size: 13px;
      color: var(--text-muted);
      margin-left: 6px;
      font-weight: 500;
    }

    /* Suggested Questions Section */
    .suggestions-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .suggestions-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .pills-container {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }

    .pill {
      background: #FFFFFF;
      border: 1px solid var(--border-color);
      border-radius: 20px;
      padding: 7px 14px;
      font-size: 12.5px;
      font-weight: 500;
      color: #334155;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      user-select: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }

    .pill:hover {
      border-color: var(--primary);
      color: var(--primary-hover);
      background: var(--primary-light);
      transform: translateY(-1px);
      box-shadow: 0 2px 6px rgba(0, 208, 156, 0.15);
    }

    .pill:active {
      transform: translateY(0);
    }

    .pill-icon {
      font-size: 13px;
    }

    /* Input Dock */
    .input-dock {
      background: #FFFFFF;
      border: 1.5px solid var(--border-color);
      border-radius: 16px;
      padding: 8px 12px 8px 16px;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: var(--shadow-sm);
      transition: all 0.2s ease;
    }

    .input-dock:focus-within {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(0, 208, 156, 0.15);
    }

    .search-icon {
      color: var(--text-subtle);
      width: 18px;
      height: 18px;
      flex-shrink: 0;
    }

    input[type="text"] {
      flex: 1;
      border: none;
      outline: none;
      font-size: 14.5px;
      color: var(--text-main);
      background: transparent;
    }

    input[type="text"]::placeholder {
      color: var(--text-subtle);
    }

    .actions-group {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    button.clear-btn {
      background: transparent;
      border: none;
      color: var(--text-subtle);
      padding: 6px 10px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    button.clear-btn:hover {
      color: #64748B;
      background: #F1F5F9;
    }

    button.send-btn {
      background: var(--primary);
      color: #FFFFFF;
      border: none;
      border-radius: 10px;
      padding: 9px 18px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
      box-shadow: 0 2px 6px rgba(0, 208, 156, 0.25);
    }

    button.send-btn:hover {
      background: var(--primary-hover);
      box-shadow: var(--shadow-glow);
    }

    button.send-btn:disabled {
      background: #CBD5E1;
      cursor: not-allowed;
      box-shadow: none;
    }

    button.send-btn svg {
      width: 14px;
      height: 14px;
      display: inline-block;
      vertical-align: middle;
      flex-shrink: 0;
    }

    /* Responsive adjustments */
    @media (max-width: 640px) {
      header {
        padding: 12px 16px;
      }
      .brand-info h1 {
        font-size: 15px;
      }
      .header-status span {
        display: none;
      }
      .main-wrapper {
        padding: 12px 12px 10px 12px;
      }
      .message-row {
        max-width: 92%;
      }
      .pills-container {
        gap: 6px;
      }
      .pill {
        padding: 6px 12px;
        font-size: 12px;
      }
    }
  </style>
</head>
<body>
  <!-- Header Bar -->
  <header>
    <div class="brand-group">
      <div class="brand-logo">G</div>
      <div class="brand-info">
        <h1>Groww • HDFC Mutual Fund FAQ Assistant</h1>
        <p>Grounded Scheme Intelligence</p>
      </div>
    </div>
    <div class="header-status">
      <div class="status-dot"></div>
      <span>5 Schemes Indexed</span>
    </div>
  </header>

  <!-- Compliance Disclaimer Banner -->
  <div class="disclaimer-bar">
    <svg viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
    </svg>
    <strong>Compliance Notice:</strong> Facts-only assistant. Strictly no investment advice, buy/sell recommendations, or returns computation.
  </div>

  <!-- Chat Wrapper -->
  <div class="main-wrapper">
    <div class="chat-container" id="chatBox">
      <!-- Welcome Message Card -->
      <div class="welcome-card">
        <h2>
          <span>👋</span> Welcome to Groww HDFC Mutual Fund Assistant
        </h2>
        <p>
          I provide strict, fact-grounded answers about HDFC mutual fund direct plans based on official Groww scheme documentation.
          Ask about <strong>expense ratios, exit loads, minimum SIPs, lock-in periods, fund managers, or benchmark indices</strong>.
        </p>
        <div class="schemes-list">
          <span class="scheme-badge">📈 HDFC Large Cap</span>
          <span class="scheme-badge">🚀 HDFC Mid-Cap Opportunities</span>
          <span class="scheme-badge">🌐 HDFC Flexi Cap</span>
          <span class="scheme-badge">🔒 HDFC ELSS Tax Saver</span>
          <span class="scheme-badge">🏢 HDFC AMC Overview</span>
        </div>
      </div>
    </div>

    <!-- Quick Questions Carousel -->
    <div class="suggestions-header">
      <span class="suggestions-title">Frequently Asked Questions</span>
    </div>
    <div class="pills-container">
      <div class="pill" data-query="What is the expense ratio of HDFC Large Cap Fund?">
        <span class="pill-icon">📊</span> Expense ratio of HDFC Large Cap
      </div>
      <div class="pill" data-query="What is the lock-in period for HDFC ELSS Tax Saver Fund?">
        <span class="pill-icon">🔒</span> ELSS lock-in period
      </div>
      <div class="pill" data-query="What is the minimum SIP for HDFC Mid Cap Fund?">
        <span class="pill-icon">💰</span> Minimum SIP for HDFC Mid Cap
      </div>
      <div class="pill" data-query="What is the exit load for HDFC Flexi Cap Fund?">
        <span class="pill-icon">🚪</span> Exit load of HDFC Flexi Cap
      </div>
      <div class="pill" data-query="What is the benchmark index for HDFC Large Cap?">
        <span class="pill-icon">🎯</span> Benchmark for Large Cap
      </div>
      <div class="pill" data-query="Should I invest in HDFC Large Cap?">
        <span class="pill-icon">💡</span> Should I invest?
      </div>
    </div>

    <!-- Input Dock -->
    <div class="input-dock">
      <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
      </svg>
      <input
        type="text"
        id="userInput"
        placeholder="Ask a factual question (e.g. 'What is the exit load for HDFC Flexi Cap?')..."
        autocomplete="off"
      />
      <div class="actions-group">
        <button class="clear-btn" id="clearBtn" title="Clear chat history">Clear</button>
        <button class="send-btn" id="sendBtn">
          <span>Ask</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>
  </div>

  <script>
    (function () {
      var chatBox = document.getElementById('chatBox');
      var userInput = document.getElementById('userInput');
      var sendBtn = document.getElementById('sendBtn');
      var clearBtn = document.getElementById('clearBtn');

      var BOT_ICON_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00D09C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v3"/><rect x="4" y="5" width="16" height="15" rx="3"/><circle cx="9" cy="12" r="1.5" fill="#00D09C"/><circle cx="15" cy="12" r="1.5" fill="#00D09C"/><path d="M9 16h6"/></svg>';
      var USER_ICON_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';

      function formatText(raw) {
        if (!raw) return '';
        var safe = document.createElement('div');
        safe.textContent = String(raw);
        return safe.innerHTML.replace(/\r?\n/g, '<br>');
      }

      function appendMessage(text, sender, meta) {
        meta = meta || {};
        var row = document.createElement('div');
        row.className = 'message-row ' + (sender === 'user' ? 'user-row' : 'bot-row');

        var avatar = document.createElement('div');
        avatar.className = 'avatar ' + (sender === 'user' ? 'user-avatar' : 'bot-avatar');
        avatar.innerHTML = sender === 'user' ? USER_ICON_SVG : BOT_ICON_SVG;

        var bubble = document.createElement('div');
        bubble.className = 'message-bubble ' + (sender === 'user' ? 'user-bubble' : 'bot-bubble') + (meta.refused ? ' refused' : '');

        var html = formatText(text);

        if (meta.source_url) {
          html += '<div class="citation-card">';
          html += '<a class="source-pill" href="' + meta.source_url + '" target="_blank" rel="noopener"><span>↗</span> Official Groww Documentation</a>';
          if (meta.last_updated) {
            html += '<span class="sync-timestamp">Synced: ' + meta.last_updated + '</span>';
          }
          html += '</div>';
        }

        bubble.innerHTML = html;
        row.appendChild(avatar);
        row.appendChild(bubble);

        chatBox.appendChild(row);
        chatBox.scrollTop = chatBox.scrollHeight;
        return row;
      }

      function showLoading() {
        var row = document.createElement('div');
        row.className = 'message-row bot-row';
        row.id = 'loadingIndicator';

        var avatar = document.createElement('div');
        avatar.className = 'avatar bot-avatar';
        avatar.innerHTML = BOT_ICON_SVG;

        var bubble = document.createElement('div');
        bubble.className = 'message-bubble bot-bubble';
        bubble.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div><span class="searching-label">Searching official Groww records...</span></div>';

        row.appendChild(avatar);
        row.appendChild(bubble);
        chatBox.appendChild(row);
        chatBox.scrollTop = chatBox.scrollHeight;
      }

      function hideLoading() {
        var indicator = document.getElementById('loadingIndicator');
        if (indicator) indicator.remove();
      }

      function submitQuery(overrideQuery) {
        var query = (typeof overrideQuery === 'string' ? overrideQuery : userInput.value).trim();
        if (!query) return;

        appendMessage(query, 'user');
        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;

        showLoading();

        fetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query })
        })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          hideLoading();
          appendMessage(data.answer || 'No response generated.', 'bot', {
            refused: data.status === 'refused',
            source_url: data.source_url,
            last_updated: data.last_updated
          });
        })
        .catch(function (err) {
          hideLoading();
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
        chatBox.innerHTML = `
          <div class="welcome-card">
            <h2><span>👋</span> Chat Cleared</h2>
            <p>Ready for your next question about HDFC mutual fund schemes.</p>
          </div>
        `;
        userInput.focus();
      });

      // Quick question pills click handler
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
