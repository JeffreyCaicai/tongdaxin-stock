from __future__ import annotations


def index_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tongdaxin Stock Workbench</title>
  <style>
    :root {
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f7f8f5;
      color: #20231f;
    }
    body { margin: 0; }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 24px;
      border-bottom: 1px solid #d9ded4;
      background: #ffffff;
      position: sticky;
      top: 0;
      z-index: 2;
    }
    h1 { font-size: 20px; margin: 0; letter-spacing: 0; }
    main {
      display: grid;
      grid-template-columns: minmax(280px, 360px) 1fr;
      min-height: calc(100vh - 66px);
    }
    aside {
      border-right: 1px solid #d9ded4;
      background: #ffffff;
      padding: 18px;
    }
    section { padding: 18px 24px; }
    h2 { font-size: 15px; margin: 0 0 12px; }
    label { display: block; font-size: 12px; color: #5a6255; margin: 12px 0 5px; }
    input, textarea {
      box-sizing: border-box;
      width: 100%;
      border: 1px solid #cfd6c9;
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
      background: #fbfcfa;
    }
    textarea { min-height: 68px; resize: vertical; }
    button {
      border: 1px solid #2f5d50;
      background: #2f5d50;
      color: white;
      border-radius: 6px;
      padding: 9px 11px;
      font: inherit;
      cursor: pointer;
    }
    button.secondary {
      background: #ffffff;
      color: #2f5d50;
    }
    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(260px, 1fr)); gap: 14px; }
    .panel {
      border: 1px solid #d9ded4;
      border-radius: 8px;
      background: #ffffff;
      padding: 14px;
      min-height: 180px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; border-bottom: 1px solid #edf0ea; padding: 8px 6px; vertical-align: top; }
    th { color: #5a6255; font-weight: 600; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #f7f8f5;
      border-radius: 6px;
      padding: 10px;
      max-height: 360px;
      overflow: auto;
    }
    .status { font-size: 13px; color: #5a6255; }
    @media (max-width: 840px) {
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid #d9ded4; }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Tongdaxin Stock Workbench</h1>
    <span class="status" id="health">checking...</span>
  </header>
  <main>
    <aside>
      <h2>Add Holding</h2>
      <label>Symbol</label>
      <input id="symbol" value="600519">
      <label>Name</label>
      <input id="name" value="Mock Moutai">
      <label>Quantity</label>
      <input id="quantity" type="number" value="100">
      <label>Cost Price</label>
      <input id="cost_price" type="number" value="95">
      <label>Stop Loss</label>
      <input id="stop_loss" type="number" value="88">
      <label>Take Profit</label>
      <input id="take_profit" type="number" value="120">
      <label>Thesis</label>
      <textarea id="initial_thesis">Manual plan with mock data.</textarea>
      <div class="toolbar" style="margin-top:14px">
        <button onclick="addHolding()">Add</button>
        <button class="secondary" onclick="refreshAll()">Refresh</button>
      </div>
    </aside>
    <section>
      <div class="toolbar">
        <button onclick="generateSignals()">Generate Signals</button>
        <button class="secondary" onclick="dailyReview()">Daily Review</button>
        <button class="secondary" onclick="runBacktest()">Run Backtest</button>
      </div>
      <div class="grid">
        <div class="panel">
          <h2>Holdings</h2>
          <div id="holdings"></div>
        </div>
        <div class="panel">
          <h2>Signals</h2>
          <div id="signals"></div>
        </div>
        <div class="panel">
          <h2>Daily Review</h2>
          <pre id="review"></pre>
        </div>
        <div class="panel">
          <h2>Backtest</h2>
          <pre id="backtest"></pre>
        </div>
      </div>
    </section>
  </main>
  <script>
    async function api(path, options) {
      const response = await fetch(path, options);
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    }
    function numberValue(id) {
      const value = document.getElementById(id).value;
      return value === "" ? null : Number(value);
    }
    async function checkHealth() {
      const health = await api("/health");
      document.getElementById("health").textContent = health.mode ? `running (${health.mode})` : "running";
    }
    async function addHolding() {
      await api("/holdings", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          symbol: document.getElementById("symbol").value,
          name: document.getElementById("name").value,
          market: "SH",
          quantity: numberValue("quantity"),
          cost_price: numberValue("cost_price"),
          stop_loss: numberValue("stop_loss"),
          take_profit: numberValue("take_profit"),
          max_loss_pct: 8,
          initial_thesis: document.getElementById("initial_thesis").value
        })
      });
      await refreshAll();
    }
    async function refreshAll() {
      const holdings = await api("/holdings");
      renderHoldings(holdings);
      const signals = await api("/signals");
      renderSignals(signals);
    }
    async function generateSignals() {
      await api("/workbench/actions/from-market", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({source: "mock", persist: true, include_technical: true})
      });
      await refreshAll();
    }
    async function dailyReview() {
      const review = await api("/reports/daily-review");
      document.getElementById("review").textContent = JSON.stringify(review, null, 2);
    }
    async function runBacktest() {
      const symbol = document.getElementById("symbol").value || "600519";
      const result = await api(`/backtests/${encodeURIComponent(symbol)}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({source: "mock", limit: 160, persist: true})
      });
      document.getElementById("backtest").textContent = JSON.stringify(result.result.metrics, null, 2);
    }
    function renderHoldings(rows) {
      document.getElementById("holdings").innerHTML = table(rows, ["id", "symbol", "name", "quantity", "cost_price", "stop_loss", "take_profit"]);
    }
    function renderSignals(rows) {
      document.getElementById("signals").innerHTML = table(rows.slice(0, 12), ["symbol", "signal_type", "action", "risk_level", "price"]);
    }
    function table(rows, fields) {
      if (!rows.length) return "<p class='status'>No data yet.</p>";
      const head = fields.map(field => `<th>${field}</th>`).join("");
      const body = rows.map(row => `<tr>${fields.map(field => `<td>${row[field] ?? ""}</td>`).join("")}</tr>`).join("");
      return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
    }
    checkHealth().then(refreshAll).catch(error => {
      document.getElementById("health").textContent = error.message;
    });
  </script>
</body>
</html>"""
