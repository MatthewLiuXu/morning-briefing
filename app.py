import os
import json
import uuid
import threading
import traceback
from flask import Flask, request, jsonify, render_template_string
from main import run_pipeline
from config import PORTFOLIO_TOKENS, FUNDING_SYMBOLS, CRYPTO_KOLS

app = Flask(__name__)

GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "https://github.com/matthewliu10/morning-briefing")

# In-memory job store
jobs = {}

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
    min-height: 100vh; padding: 20px;
  }
  .page { max-width: 720px; margin: 0 auto; }
  h1 { font-size: 2rem; margin-bottom: 4px; color: #fff; text-align: center; }
  .subtitle { color: #888; font-size: 0.95rem; margin-bottom: 28px; text-align: center; }

  /* Sections */
  .section {
    background: #161616; border: 1px solid #2a2a2a; border-radius: 10px;
    margin-bottom: 16px; overflow: hidden;
  }
  .section-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 18px; cursor: pointer; user-select: none;
  }
  .section-header:hover { background: #1a1a1a; }
  .section-title { font-weight: 600; font-size: 0.95rem; color: #fff; }
  .section-controls { display: flex; align-items: center; gap: 12px; }
  .toggle { position: relative; width: 40px; height: 22px; }
  .toggle input { opacity: 0; width: 0; height: 0; }
  .toggle .slider {
    position: absolute; inset: 0; background: #333; border-radius: 22px;
    cursor: pointer; transition: 0.2s;
  }
  .toggle .slider::before {
    content: ''; position: absolute; width: 16px; height: 16px;
    left: 3px; top: 3px; background: #888; border-radius: 50%; transition: 0.2s;
  }
  .toggle input:checked + .slider { background: #2563eb; }
  .toggle input:checked + .slider::before { transform: translateX(18px); background: #fff; }
  .chevron { color: #666; font-size: 0.8rem; transition: transform 0.2s; }
  .section.open .chevron { transform: rotate(90deg); }
  .section-body { display: none; padding: 0 18px 16px; }
  .section.open .section-body { display: block; }

  /* Tables */
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { text-align: left; color: #666; font-weight: 500; padding: 6px 8px; border-bottom: 1px solid #222; }
  td { padding: 6px 8px; border-bottom: 1px solid #1a1a1a; }
  td input {
    background: #0a0a0a; border: 1px solid #333; border-radius: 4px;
    color: #e0e0e0; padding: 5px 8px; width: 100%; font-size: 0.85rem;
  }
  td input:focus { border-color: #4f8ff7; outline: none; }

  .add-btn, .remove-btn {
    background: none; border: 1px solid #333; border-radius: 4px;
    color: #888; cursor: pointer; font-size: 0.8rem; padding: 4px 10px;
  }
  .add-btn:hover { border-color: #4f8ff7; color: #4f8ff7; }
  .remove-btn { border: none; color: #555; font-size: 1rem; padding: 2px 6px; }
  .remove-btn:hover { color: #f87171; }

  /* KOL chips */
  .chip-grid { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip {
    display: flex; align-items: center; gap: 6px;
    background: #0a0a0a; border: 1px solid #333; border-radius: 6px;
    padding: 6px 12px; cursor: pointer; font-size: 0.85rem; transition: 0.15s;
    user-select: none;
  }
  .chip.selected { border-color: #4f8ff7; background: #1a2744; }
  .chip .check { color: #4f8ff7; font-size: 0.75rem; }

  /* Tag input for funding */
  .tag-container {
    display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
    background: #0a0a0a; border: 1px solid #333; border-radius: 6px;
    padding: 8px 10px; min-height: 38px;
  }
  .tag {
    display: flex; align-items: center; gap: 4px;
    background: #1a2744; border: 1px solid #2563eb40; border-radius: 4px;
    padding: 3px 8px; font-size: 0.8rem; color: #93b4f5;
  }
  .tag .tag-x { cursor: pointer; color: #5580cc; font-size: 0.9rem; }
  .tag .tag-x:hover { color: #f87171; }
  .tag-input {
    background: none; border: none; color: #e0e0e0; font-size: 0.85rem;
    outline: none; min-width: 80px; flex: 1;
  }

  /* Generate button */
  .generate-btn {
    width: 100%; padding: 16px; border-radius: 10px; border: none;
    background: #2563eb; color: #fff; font-size: 1.05rem; font-weight: 600;
    cursor: pointer; transition: background 0.2s; margin-top: 8px;
  }
  .generate-btn:hover { background: #1d4ed8; }
  .generate-btn:disabled { background: #333; color: #666; cursor: not-allowed; }

  /* Progress log */
  #log {
    display: none; margin-top: 16px; padding: 14px;
    background: #161616; border: 1px solid #2a2a2a; border-radius: 10px;
    font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.8rem;
    max-height: 280px; overflow-y: auto;
  }
  #log.active { display: block; }
  .log-entry {
    padding: 5px 0; border-bottom: 1px solid #1a1a1a;
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

  /* Briefing output */
  #briefing {
    display: none; margin-top: 16px; padding: 24px;
    background: #161616; border: 1px solid #2a2a2a; border-radius: 10px;
    font-size: 0.9rem; line-height: 1.7; white-space: pre-wrap;
  }
  #briefing.active { display: block; }
  #briefing h3 { color: #fff; margin-top: 16px; }

  .bottom-links { text-align: center; margin-top: 20px; }
  .code-link { color: #4f8ff7; text-decoration: none; font-size: 0.85rem; }
  .code-link:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="page">
  <h1>Crypto Morning Briefing</h1>
  <p class="subtitle">Configure your data sources, then generate a live AI briefing.</p>

  <!-- Portfolio -->
  <div class="section open" id="sec-portfolio">
    <div class="section-header" onclick="toggleSection('sec-portfolio')">
      <span class="section-title">Portfolio</span>
      <span class="chevron">&#9654;</span>
    </div>
    <div class="section-body">
      <table id="portfolio-table">
        <thead><tr><th>Token ID</th><th>Symbol</th><th>Quantity</th><th>Entry Price</th><th></th></tr></thead>
        <tbody></tbody>
      </table>
      <button class="add-btn" style="margin-top:10px" onclick="addPortfolioRow()">+ Add token</button>
    </div>
  </div>

  <!-- KOLs -->
  <div class="section open" id="sec-kol">
    <div class="section-header" onclick="toggleSection('sec-kol')">
      <span class="section-title">KOL Twitter Feed</span>
      <div class="section-controls">
        <label class="toggle" onclick="event.stopPropagation()">
          <input type="checkbox" id="toggle-kol" checked>
          <span class="slider"></span>
        </label>
        <span class="chevron">&#9654;</span>
      </div>
    </div>
    <div class="section-body">
      <div class="chip-grid" id="kol-chips"></div>
      <div style="margin-top:10px;display:flex;gap:8px">
        <input type="text" id="kol-handle" placeholder="Twitter handle" style="flex:1;background:#0a0a0a;border:1px solid #333;border-radius:4px;color:#e0e0e0;padding:5px 8px;font-size:0.85rem">
        <button class="add-btn" onclick="addKol()">+ Add</button>
      </div>
    </div>
  </div>

  <!-- Funding -->
  <div class="section" id="sec-funding">
    <div class="section-header" onclick="toggleSection('sec-funding')">
      <span class="section-title">Funding Rates</span>
      <div class="section-controls">
        <label class="toggle" onclick="event.stopPropagation()">
          <input type="checkbox" id="toggle-funding" checked>
          <span class="slider"></span>
        </label>
        <span class="chevron">&#9654;</span>
      </div>
    </div>
    <div class="section-body">
      <p style="color:#666;font-size:0.8rem;margin-bottom:8px">Perp symbols to track (e.g. BTCUSDT). Press Enter to add.</p>
      <div class="tag-container" id="funding-tags">
        <input class="tag-input" id="funding-input" placeholder="Add symbol..." onkeydown="if(event.key==='Enter'){addFundingTag();event.preventDefault()}">
      </div>
    </div>
  </div>

  <!-- Market Data -->
  <div class="section" id="sec-market">
    <div class="section-header" onclick="toggleSection('sec-market')">
      <span class="section-title">Market Data</span>
      <div class="section-controls">
        <label class="toggle" onclick="event.stopPropagation()">
          <input type="checkbox" id="toggle-market" checked>
          <span class="slider"></span>
        </label>
        <span class="chevron">&#9654;</span>
      </div>
    </div>
    <div class="section-body">
      <p style="color:#666;font-size:0.8rem">Prices, volumes, and market caps for your portfolio tokens. Sourced from CoinGecko.</p>
    </div>
  </div>

  <!-- Social Metrics -->
  <div class="section" id="sec-social">
    <div class="section-header" onclick="toggleSection('sec-social')">
      <span class="section-title">Social Metrics</span>
      <div class="section-controls">
        <label class="toggle" onclick="event.stopPropagation()">
          <input type="checkbox" id="toggle-social" checked>
          <span class="slider"></span>
        </label>
        <span class="chevron">&#9654;</span>
      </div>
    </div>
    <div class="section-body">
      <p style="color:#666;font-size:0.8rem">Twitter followers and Reddit subscribers for your portfolio tokens. Sourced from CoinPaprika.</p>
    </div>
  </div>

  <!-- Trending -->
  <div class="section" id="sec-trending">
    <div class="section-header" onclick="toggleSection('sec-trending')">
      <span class="section-title">Trending Tokens</span>
      <div class="section-controls">
        <label class="toggle" onclick="event.stopPropagation()">
          <input type="checkbox" id="toggle-trending" checked>
          <span class="slider"></span>
        </label>
        <span class="chevron">&#9654;</span>
      </div>
    </div>
    <div class="section-body">
      <p style="color:#666;font-size:0.8rem">Top trending tokens by search activity from CoinGecko.</p>
    </div>
  </div>

  <!-- News -->
  <div class="section" id="sec-news">
    <div class="section-header" onclick="toggleSection('sec-news')">
      <span class="section-title">News Headlines</span>
      <div class="section-controls">
        <label class="toggle" onclick="event.stopPropagation()">
          <input type="checkbox" id="toggle-news" checked>
          <span class="slider"></span>
        </label>
        <span class="chevron">&#9654;</span>
      </div>
    </div>
    <div class="section-body">
      <p style="color:#666;font-size:0.8rem">Latest crypto news from CoinGecko.</p>
    </div>
  </div>

  <button class="generate-btn" id="gen-btn" onclick="generate()">Generate Briefing</button>
  <div id="log"></div>
  <div id="briefing"></div>

  <div class="bottom-links">
    <a class="code-link" href="{{ repo_url }}" target="_blank">View source on GitHub</a>
  </div>
</div>

<script>
// --- Default data from server ---
const defaultPortfolio = {{ portfolio_json | safe }};
const defaultKols = {{ kols_json | safe }};
const defaultFunding = {{ funding_json | safe }};

// --- State ---
let portfolio = JSON.parse(JSON.stringify(defaultPortfolio));
let kols = JSON.parse(JSON.stringify(defaultKols));
let fundingSymbols = [...defaultFunding];

// --- Section toggle ---
function toggleSection(id) {
  document.getElementById(id).classList.toggle('open');
}

// --- Portfolio table ---
function renderPortfolio() {
  const tbody = document.querySelector('#portfolio-table tbody');
  tbody.innerHTML = '';
  for (const [id, tok] of Object.entries(portfolio)) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input value="${id}" onchange="renamePortfolioRow(this,'${id}')"></td>
      <td><input value="${tok.symbol}" onchange="portfolio['${id}'].symbol=this.value"></td>
      <td><input type="number" value="${tok.quantity}" onchange="portfolio['${id}'].quantity=parseFloat(this.value)||0"></td>
      <td><input type="number" value="${tok.entry_price}" onchange="portfolio['${id}'].entry_price=parseFloat(this.value)||0"></td>
      <td><button class="remove-btn" onclick="delete portfolio['${id}'];renderPortfolio()">&times;</button></td>`;
    tbody.appendChild(tr);
  }
}
function renamePortfolioRow(input, oldId) {
  const newId = input.value.trim();
  if (!newId || newId === oldId) return;
  portfolio[newId] = portfolio[oldId];
  delete portfolio[oldId];
  renderPortfolio();
}
function addPortfolioRow() {
  const id = 'new-token-' + Date.now();
  portfolio[id] = {symbol: '', quantity: 0, entry_price: 0};
  renderPortfolio();
}

// --- KOL chips ---
function renderKols() {
  const container = document.getElementById('kol-chips');
  container.innerHTML = '';
  kols.forEach((k, i) => {
    const chip = document.createElement('div');
    chip.className = 'chip' + (k.selected !== false ? ' selected' : '');
    chip.innerHTML = `<span class="check">${k.selected !== false ? '&#10003;' : ''}</span>
      <span>@${k.handle}</span>`;
    chip.onclick = () => { kols[i].selected = !kols[i].selected; renderKols(); };
    container.appendChild(chip);
  });
}
function addKol() {
  const handle = document.getElementById('kol-handle').value.trim();
  if (!handle) return;
  kols.push({handle, selected: true});
  document.getElementById('kol-handle').value = '';
  renderKols();
}

// --- Funding tags ---
function renderFunding() {
  const container = document.getElementById('funding-tags');
  container.querySelectorAll('.tag').forEach(t => t.remove());
  const input = document.getElementById('funding-input');
  fundingSymbols.forEach((sym, i) => {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.innerHTML = `${sym} <span class="tag-x" onclick="fundingSymbols.splice(${i},1);renderFunding()">&times;</span>`;
    container.insertBefore(tag, input);
  });
}
function addFundingTag() {
  const input = document.getElementById('funding-input');
  const val = input.value.trim().toUpperCase();
  if (val && !fundingSymbols.includes(val)) {
    fundingSymbols.push(val);
    renderFunding();
  }
  input.value = '';
}

// --- Init ---
kols.forEach(k => k.selected = true);
renderPortfolio();
renderKols();
renderFunding();

// --- Generate ---
const icons = {
  loading: '<span class="spinner"></span>',
  ok: '&#10003;', error: '&#10007;', done: '&#10003;'
};

async function generate() {
  const btn = document.getElementById('gen-btn');
  const log = document.getElementById('log');
  const briefingEl = document.getElementById('briefing');
  btn.disabled = true;
  btn.textContent = 'Generating...';
  log.innerHTML = '';
  log.className = 'active';
  briefingEl.className = '';
  briefingEl.textContent = '';

  let seen = 0;

  function renderStep(data) {
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
  }

  const config = {
    portfolio: portfolio,
    funding_symbols: fundingSymbols,
    kols: kols.filter(k => k.selected !== false).map(k => k.handle),
    enabled_sources: {
      market: document.getElementById('toggle-market').checked,
      funding: document.getElementById('toggle-funding').checked,
      social: document.getElementById('toggle-social').checked,
      trending: document.getElementById('toggle-trending').checked,
      news: document.getElementById('toggle-news').checked,
      kol: document.getElementById('toggle-kol').checked,
    }
  };

  try {
    const resp = await fetch('/start', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(config)
    });
    const {job_id} = await resp.json();

    while (true) {
      await new Promise(r => setTimeout(r, 1000));
      const pollResp = await fetch('/status/' + job_id + '?since=' + seen);
      const pollData = await pollResp.json();

      for (const step of pollData.steps) {
        renderStep(step);
        seen++;
      }

      if (pollData.finished) {
        if (pollData.briefing) {
          briefingEl.textContent = pollData.briefing;
          briefingEl.className = 'active';
        }
        if (!document.querySelector('.log-entry.done')) {
          renderStep({step_id: 'done', message: 'Complete!', status: 'done'});
        }
        break;
      }
    }
  } catch (err) {
    renderStep({step_id: 'error', message: 'Request failed: ' + err.message, status: 'error'});
  }

  btn.disabled = false;
  btn.textContent = 'Generate Briefing';
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    portfolio_json = json.dumps({
        tid: {"symbol": t["symbol"], "quantity": t["quantity"], "entry_price": t["entry_price"]}
        for tid, t in PORTFOLIO_TOKENS.items()
    })
    kols_json = json.dumps([{"handle": k} for k in CRYPTO_KOLS])
    funding_json = json.dumps(FUNDING_SYMBOLS)
    return render_template_string(
        LANDING_PAGE,
        repo_url=GITHUB_REPO_URL,
        portfolio_json=portfolio_json,
        kols_json=kols_json,
        funding_json=funding_json,
    )


@app.route("/start", methods=["POST"])
def start():
    config = request.get_json() or {}

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {"steps": [], "finished": False, "briefing": None}

    def on_status(step_id, message, status):
        jobs[job_id]["steps"].append({
            "step_id": step_id, "message": message, "status": status
        })

    def worker():
        try:
            briefing = run_pipeline(config=config, status_callback=on_status)
            jobs[job_id]["briefing"] = briefing
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[job {job_id}] Worker crashed: {e}\n{tb}")
            jobs[job_id]["steps"].append({
                "step_id": "crash", "message": f"Error: {e}", "status": "error"
            })
        finally:
            jobs[job_id]["finished"] = True

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    return jsonify({"ok": True, "job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    since = int(request.args.get("since", 0))
    result = {
        "steps": job["steps"][since:],
        "finished": job["finished"],
    }
    if job["finished"] and job["briefing"]:
        result["briefing"] = job["briefing"]
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
