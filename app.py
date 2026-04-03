import os
import json
import queue
from flask import Flask, request, jsonify, render_template_string, Response
from main import run_for_email

app = Flask(__name__)

GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "https://github.com/matthewliu10/morning-briefing")

LANDING_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Crypto Morning Briefing</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0a0a0a; color: #e0e0e0;
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; padding: 20px;
  }
  .container { max-width: 520px; width: 100%; text-align: center; }
  h1 { font-size: 2rem; margin-bottom: 8px; color: #fff; }
  .subtitle { color: #888; font-size: 1rem; margin-bottom: 32px; line-height: 1.4; }
  .card {
    background: #161616; border: 1px solid #2a2a2a; border-radius: 12px;
    padding: 32px; margin-bottom: 24px; text-align: left;
  }
  .card p { color: #aaa; font-size: 0.95rem; line-height: 1.6; margin-bottom: 20px; text-align: center; }
  input[type="email"] {
    width: 100%; padding: 14px 16px; border-radius: 8px;
    border: 1px solid #333; background: #0a0a0a; color: #fff;
    font-size: 1rem; margin-bottom: 12px; outline: none;
    transition: border-color 0.2s;
  }
  input[type="email"]:focus { border-color: #4f8ff7; }
  button {
    width: 100%; padding: 14px; border-radius: 8px; border: none;
    background: #4f8ff7; color: #fff; font-size: 1rem; font-weight: 600;
    cursor: pointer; transition: background 0.2s;
  }
  button:hover { background: #3a7de0; }
  button:disabled { background: #333; color: #666; cursor: not-allowed; }

  /* Progress log */
  #log {
    display: none; margin-top: 20px; padding: 16px;
    background: #0a0a0a; border: 1px solid #222; border-radius: 8px;
    font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.8rem;
    max-height: 320px; overflow-y: auto;
  }
  #log.active { display: block; }
  .log-entry {
    padding: 6px 0; border-bottom: 1px solid #1a1a1a;
    display: flex; align-items: center; gap: 10px;
  }
  .log-entry:last-child { border-bottom: none; }
  .log-icon { width: 18px; text-align: center; flex-shrink: 0; }
  .log-text { color: #aaa; }
  .log-entry.loading .log-text { color: #fbbf24; }
  .log-entry.ok .log-text { color: #4ade80; }
  .log-entry.error .log-text { color: #f87171; }
  .log-entry.done .log-text { color: #4ade80; font-weight: 600; }

  .spinner {
    width: 14px; height: 14px; border: 2px solid #333;
    border-top-color: #fbbf24; border-radius: 50%;
    animation: spin 0.8s linear infinite; display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .bottom-links { margin-top: 20px; }
  .code-link {
    display: inline-block; color: #4f8ff7;
    text-decoration: none; font-size: 0.9rem;
  }
  .code-link:hover { text-decoration: underline; }

  .features {
    text-align: left; margin-top: 24px;
    columns: 2; column-gap: 16px;
  }
  .features li {
    color: #666; font-size: 0.8rem; margin-bottom: 6px;
    list-style: none; break-inside: avoid;
  }
  .features li::before { content: "  "; }
</style>
</head>
<body>
<div class="container">
  <h1>Crypto Morning Briefing</h1>
  <p class="subtitle">AI-powered daily brief for crypto portfolio managers.<br>
  Real data. Delivered to your inbox in under 60 seconds.</p>

  <div class="card">
    <p>Enter your email to receive a live briefing with market data, funding rates, KOL tweets, and news.</p>
    <form id="form">
      <input type="email" id="email" placeholder="you@company.com" required>
      <button type="submit" id="btn">Send me a briefing</button>
    </form>
    <div id="log"></div>
  </div>

  <div class="bottom-links">
    <a class="code-link" href="{{ repo_url }}" target="_blank">View source on GitHub</a>
  </div>

  <ul class="features">
    <li>Portfolio PnL</li>
    <li>Funding rates</li>
    <li>KOL Twitter feed</li>
    <li>Trending tokens</li>
    <li>Social sentiment</li>
    <li>News headlines</li>
  </ul>
</div>

<script>
const icons = {
  loading: '<span class="spinner"></span>',
  ok: '&#10003;',
  error: '&#10007;',
  done: '&#10003;'
};

document.getElementById('form').addEventListener('submit', (e) => {
  e.preventDefault();
  const btn = document.getElementById('btn');
  const log = document.getElementById('log');
  const email = document.getElementById('email').value;

  btn.disabled = true;
  btn.textContent = 'Generating...';
  log.innerHTML = '';
  log.className = 'active';

  const evtSource = new EventSource('/stream?email=' + encodeURIComponent(email));

  evtSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // If a "loading" entry for this step exists, replace it
    const existing = document.getElementById('step-' + data.step_id);
    if (existing) {
      existing.className = 'log-entry ' + data.status;
      existing.querySelector('.log-icon').innerHTML = icons[data.status];
      existing.querySelector('.log-text').textContent = data.message;
    } else {
      const entry = document.createElement('div');
      entry.className = 'log-entry ' + data.status;
      entry.id = 'step-' + data.step_id;
      entry.innerHTML = '<span class="log-icon">' + icons[data.status] + '</span>'
                       + '<span class="log-text">' + data.message + '</span>';
      log.appendChild(entry);
    }
    log.scrollTop = log.scrollHeight;

    if (data.status === 'done') {
      evtSource.close();
      btn.disabled = false;
      btn.textContent = 'Send me a briefing';
    }
  };

  evtSource.onerror = () => {
    evtSource.close();
    // Check if we already got a "done" message
    if (!document.querySelector('.log-entry.done')) {
      const entry = document.createElement('div');
      entry.className = 'log-entry error';
      entry.innerHTML = '<span class="log-icon">&#10007;</span>'
                       + '<span class="log-text">Connection lost. Please try again.</span>';
      log.appendChild(entry);
    }
    btn.disabled = false;
    btn.textContent = 'Send me a briefing';
  };
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(LANDING_PAGE, repo_url=GITHUB_REPO_URL)


@app.route("/stream")
def stream():
    email = request.args.get("email", "").strip()
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Invalid email"}), 400

    q = queue.Queue()

    def on_status(step_id, message, status):
        q.put(json.dumps({"step_id": step_id, "message": message, "status": status}))

    def generate():
        import threading
        import traceback

        def worker():
            try:
                run_for_email(email, status_callback=on_status)
            except Exception as e:
                tb = traceback.format_exc()
                print(f"[stream] Worker crashed: {e}\n{tb}")
                q.put(json.dumps({"step_id": "crash", "message": f"Error: {e}", "status": "error"}))
                q.put(json.dumps({"step_id": "done", "message": "Pipeline failed. Check server logs.", "status": "done"}))
            finally:
                q.put(None)  # sentinel

        t = threading.Thread(target=worker)
        t.start()

        try:
            while True:
                item = q.get(timeout=120)
                if item is None:
                    break
                yield f"data: {item}\n\n"
        except queue.Empty:
            print("[stream] Timed out waiting for worker after 120s")
            yield f"data: {json.dumps({'step_id': 'timeout', 'message': 'Request timed out after 120s', 'status': 'error'})}\n\n"
            yield f"data: {json.dumps({'step_id': 'done', 'message': 'Timed out', 'status': 'done'})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# Keep the POST endpoint for backwards compatibility
@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    email = data.get("email", "").strip()
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Invalid email address."}), 400
    try:
        run_for_email(email)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
