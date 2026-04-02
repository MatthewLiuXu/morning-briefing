import os
import threading
from flask import Flask, request, jsonify, render_template_string
from main import run_for_email

app = Flask(__name__)

GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "https://github.com/yourname/morning-briefing")

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
  .container { max-width: 480px; width: 100%; text-align: center; }
  h1 { font-size: 2rem; margin-bottom: 8px; color: #fff; }
  .subtitle { color: #888; font-size: 1rem; margin-bottom: 32px; }
  .card {
    background: #161616; border: 1px solid #2a2a2a; border-radius: 12px;
    padding: 32px; margin-bottom: 24px;
  }
  .card p { color: #aaa; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px; }
  input[type="email"] {
    width: 100%; padding: 14px 16px; border-radius: 8px;
    border: 1px solid #333; background: #0a0a0a; color: #fff;
    font-size: 1rem; margin-bottom: 12px; outline: none;
  }
  input[type="email"]:focus { border-color: #4f8ff7; }
  button {
    width: 100%; padding: 14px; border-radius: 8px; border: none;
    background: #4f8ff7; color: #fff; font-size: 1rem; font-weight: 600;
    cursor: pointer; transition: background 0.2s;
  }
  button:hover { background: #3a7de0; }
  button:disabled { background: #333; cursor: not-allowed; }
  .status { margin-top: 16px; font-size: 0.9rem; min-height: 24px; }
  .status.success { color: #4ade80; }
  .status.error { color: #f87171; }
  .status.loading { color: #fbbf24; }
  .code-link {
    display: inline-block; margin-top: 8px; color: #4f8ff7;
    text-decoration: none; font-size: 0.9rem;
  }
  .code-link:hover { text-decoration: underline; }
  .features { text-align: left; margin-top: 24px; }
  .features li { color: #888; font-size: 0.85rem; margin-bottom: 8px; list-style: none; }
  .features li::before { content: "→ "; color: #4f8ff7; }
</style>
</head>
<body>
<div class="container">
  <h1>Crypto Morning Briefing</h1>
  <p class="subtitle">AI-powered daily brief for crypto portfolio managers</p>
  <div class="card">
    <p>Get a sample morning briefing delivered to your inbox — real market data, funding rates, social sentiment, and news synthesized by Claude AI.</p>
    <form id="form">
      <input type="email" id="email" placeholder="you@company.com" required>
      <button type="submit" id="btn">Send me a briefing</button>
    </form>
    <div class="status" id="status"></div>
  </div>
  <a class="code-link" href="{{ repo_url }}" target="_blank">View the source code on GitHub ↗</a>
  <ul class="features">
    <li>Portfolio PnL tracking with overnight change</li>
    <li>Perpetual funding rates from Hyperliquid</li>
    <li>Social sentiment via CoinPaprika + CoinGecko trending</li>
    <li>News headlines with portfolio implications</li>
    <li>All synthesized into a 2-minute read by Claude</li>
  </ul>
</div>
<script>
document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('btn');
  const status = document.getElementById('status');
  const email = document.getElementById('email').value;
  btn.disabled = true;
  btn.textContent = 'Generating briefing...';
  status.className = 'status loading';
  status.textContent = 'Fetching market data and generating your brief — this takes ~30 seconds...';
  try {
    const resp = await fetch('/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await resp.json();
    if (data.ok) {
      status.className = 'status success';
      status.textContent = 'Briefing sent! Check your inbox.';
    } else {
      status.className = 'status error';
      status.textContent = data.error || 'Something went wrong.';
    }
  } catch (err) {
    status.className = 'status error';
    status.textContent = 'Network error — please try again.';
  }
  btn.disabled = false;
  btn.textContent = 'Send me a briefing';
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(LANDING_PAGE, repo_url=GITHUB_REPO_URL)


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
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
