from __future__ import annotations


def index_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>通达信股票工作台</title>
  <style>
    :root {
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f6f8;
      color: #242930;
      --surface: #ffffff;
      --surface-muted: #f4f6f8;
      --line: #dfe3e8;
      --line-strong: #c1cbbd;
      --text-muted: #626b77;
      --accent: #2f5d50;
      --accent-soft: #eef5f1;
    }
    body { margin: 0; }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 24px;
      border-bottom: 1px solid var(--line);
      background: var(--surface);
      position: sticky;
      top: 0;
      z-index: 2;
    }
    h1 { font-size: 20px; margin: 0; letter-spacing: 0; }
    main {
      display: grid;
      grid-template-columns: 232px minmax(0, 1fr);
      min-height: calc(100vh - 58px);
    }
    aside {
      border-right: 1px solid var(--line);
      background: var(--surface);
      padding: 18px;
      position: sticky;
      top: 58px;
      height: calc(100vh - 58px);
      box-sizing: border-box;
      overflow: auto;
    }
    section { min-width: 0; padding: 22px 28px 28px; }
    h2 { font-size: 16px; margin: 0 0 12px; }
    label { display: block; font-size: 12px; color: var(--text-muted); margin: 12px 0 5px; }
    input, textarea, select {
      box-sizing: border-box;
      border: 1px solid #cfd6c9;
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
      background: #fbfcfa;
    }
    input:focus, textarea:focus, select:focus {
      outline: 2px solid #bfd5cc;
      outline-offset: 1px;
    }
    input, textarea { width: 100%; }
    textarea { min-height: 68px; resize: vertical; }
    button {
      border: 1px solid var(--accent);
      background: var(--accent);
      color: white;
      border-radius: 6px;
      padding: 9px 11px;
      font: inherit;
      cursor: pointer;
    }
    button.secondary {
      background: var(--surface);
      color: var(--accent);
    }
    button:hover { filter: brightness(0.98); }
    .header-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; min-width: 0; max-width: 100%; }
    .header-tools select { min-width: 0; max-width: 100%; }
    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
      gap: 16px;
      align-items: start;
    }
    .panel {
      min-width: 0;
      border: 0;
      border-radius: 0;
      background: var(--surface);
      padding: 16px;
      min-height: 160px;
      box-shadow: none;
    }
    .analysis-panel {
      grid-column: 1 / -1;
      min-height: 360px;
      border-color: var(--line-strong);
    }
    .analysis-panel h2 { font-size: 18px; }
    .analysis-panel h3 { font-size: 14px; }
    .opportunity-summary { display:flex; gap:24px; flex-wrap:wrap; padding:12px 0; border-bottom:1px solid var(--line); }
    .opportunity-summary strong { display:block; font-size:22px; font-variant-numeric:tabular-nums; }
    .opportunity-summary span { font-size:12px; color:var(--text-muted); }
    .opportunity-row { padding:16px 0; border-bottom:1px solid var(--line); }
    .opportunity-head { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
    .opportunity-head h3 { margin:0; font-size:16px; }
    .opportunity-head small { font-weight:400; color:var(--text-muted); }
    .opportunity-columns { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; margin-top:12px; }
    .opportunity-columns p { margin:5px 0; font-size:13px; overflow-wrap:anywhere; }
    .opportunity-columns h4 { margin:0; font-size:12px; color:var(--text-muted); }
    .opportunity-score { display:flex; height:6px; width:160px; max-width:100%; overflow:hidden; background:#edf0ea; }
    .opportunity-score i { display:block; height:6px; }
    .opportunity-grade { font-weight:600; color:var(--accent); }
    .opportunity-row[data-level="wait"] .opportunity-grade { color:#936b18; }
    .opportunity-progress { width:100%; accent-color:var(--accent); }
    .horizon-list { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); margin:14px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
    .horizon-item { padding:12px 10px; min-width:0; border-right:1px solid var(--line); font-size:12px; overflow-wrap:anywhere; }
    .horizon-item:last-child { border-right:0; }
    .horizon-item summary { cursor:pointer; min-height:58px; }
    .horizon-item strong, .horizon-item span { display:block; margin-top:5px; }
    .horizon-item p { margin:8px 0; line-height:1.5; }
    .horizon-item[data-stance="favorable"] strong { color:#286d5d; }
    .horizon-item[data-stance="avoid"] strong { color:#a84444; }
    .horizon-item[data-stance="insufficient"] strong { color:var(--text-muted); }
    .tracking-table { min-width:820px; font-variant-numeric:tabular-nums; }
    .tracking-table th, .tracking-table td { white-space:nowrap; word-break:normal; }
    .tracking-table .tracking-identity { white-space:normal; min-width:100px; max-width:160px; }
    .tracking-table small { display:block; color:var(--text-muted); margin-top:4px; }
    .tracking-meta { font-size:12px; color:var(--text-muted); overflow-wrap:anywhere; line-height:1.6; }
    .tracking-history { display:flex; align-items:center; gap:12px; flex-wrap:wrap; padding:12px 0; border-bottom:1px solid var(--line); }
    @media (max-width:1000px) { .horizon-list { grid-template-columns:repeat(2,minmax(0,1fr)); } .horizon-item { border-bottom:1px solid var(--line); } }
    @media (max-width:420px) { .horizon-list { grid-template-columns:1fr; } .horizon-item { border-right:0; } }
    @media (max-width:700px) { .opportunity-columns { grid-template-columns:1fr; gap:10px; } }
    .stock-detail { border-bottom: 1px solid var(--line); padding: 12px 0; }
    .stock-detail summary { cursor: pointer; font-weight: 600; overflow-wrap: anywhere; }
    .stock-detail summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
    .detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 12px; }
    .detail-grid > div { min-width: 0; }
    .detail-grid h3 { font-size: 14px; margin: 8px 0; }
    .detail-grid h4 { font-size: 13px; margin: 12px 0 6px; overflow-wrap: anywhere; }
    .detail-fields { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 6px 12px; font-size: 13px; margin: 8px 0; }
    .detail-fields dt { color: var(--text-muted); overflow-wrap: anywhere; }
    .detail-fields dd { margin: 0; overflow-wrap: anywhere; }
    .evidence-list li { margin-bottom: 12px; overflow-wrap: anywhere; font-size: 13px; }
    .panel-subtitle {
      margin: -2px 0 12px;
      color: var(--text-muted);
      font-size: 13px;
    }
    .table-scroll { min-width: 0; max-width: 100%; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; border-bottom: 1px solid #edf0ea; padding: 8px 6px; vertical-align: top; }
    td { word-break: break-word; }
    th { color: var(--text-muted); font-weight: 600; }
    .holdings-table th,
    .holdings-table td { white-space: nowrap; word-break: normal; }
    .holdings-table .symbol-cell { font-variant-numeric: tabular-nums; }
    .holdings-table .name-cell { min-width: 72px; white-space: normal; }
    .holdings-table .number-cell { text-align: right; font-variant-numeric: tabular-nums; }
    .holdings-table .action-cell { text-align: center; }
    .quantity-input { width: 72px; min-width: 72px; padding: 6px 7px; text-align: right; }
    .price-input { width: 86px; min-width: 86px; padding: 6px 7px; text-align: right; }
    .table-button { padding: 6px 9px; font-size: 12px; white-space: nowrap; }
    .holdings-summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(128px, 1fr));
      gap: 8px;
      margin-bottom: 12px;
    }
    .summary-stat {
      background: var(--surface-muted);
      border-radius: 6px;
      padding: 10px 12px;
    }
    .summary-stat b {
      display: block;
      color: var(--text-muted);
      font-size: 12px;
      margin-bottom: 4px;
    }
    .summary-stat span {
      font-size: 17px;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .gain { color: #b42318; }
    .loss { color: #176b3a; }
    .status { font-size: 13px; color: var(--text-muted); overflow-wrap: anywhere; }
    .summary {
      background: var(--accent-soft);
      border-left: 3px solid var(--accent);
      border-radius: 6px;
      padding: 11px 12px;
      margin: 0;
      font-weight: 600;
      overflow-wrap: anywhere;
    }
    .metric-grid { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 8px; }
    .metric { background: var(--surface-muted); border-radius: 6px; padding: 10px; }
    .metric b { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 3px; }
    .panel-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
    .panel-head h2 { margin: 0; }
    .panel-controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .inline-select { max-width: 150px; padding: 6px 8px; font-size: 13px; }
    ul { margin: 8px 0 0; padding-left: 18px; }
    @media (max-width: 1160px) {
      .metric-grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .holdings-summary { grid-template-columns: repeat(2, minmax(128px, 1fr)); }
      .grid { grid-template-columns: minmax(0, 1fr); }
      .detail-grid { grid-template-columns: 1fr; }
      .analysis-panel { grid-column: auto; }
    }
    @media (max-width: 840px) {
      header { align-items: flex-start; flex-direction: column; }
      main { grid-template-columns: minmax(0, 1fr); }
      aside {
        border-right: 0;
        border-bottom: 1px solid var(--line);
        position: static;
        height: auto;
      }
      section { padding: 16px; }
      .holdings-summary { grid-template-columns: 1fr; }
      .grid { grid-template-columns: minmax(0, 1fr); }
    }
    [hidden] { display: none !important; }
    button:focus-visible, summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
    button:disabled { opacity: .55; cursor: default; }
    .workspace-tabs { display:flex; gap:24px; border-bottom:1px solid var(--line); margin-bottom:12px; }
    .workspace-tabs button { border:0; border-bottom:3px solid transparent; border-radius:0; background:none; color:var(--text-muted); padding:9px 0; font-weight:600; }
    .workspace-tabs button[aria-pressed="true"] { color:var(--accent); border-bottom-color:var(--accent); }
    .workspace-head { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:10px; }
    .workspace-head h2 { font-size:20px; margin:0; }
    .view-tabs { display:flex; gap:4px; flex-wrap:wrap; margin-bottom:12px; }
    .view-tabs button { background:none; color:var(--text-muted); border:0; padding:7px 12px; }
    .view-tabs button[aria-pressed="true"] { background:#e6edeb; color:var(--accent); font-weight:600; }
    .sidebar-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
    .sidebar-head h2 { margin:0; }
    .icon-button { width:32px; height:32px; padding:0; font-size:20px; flex-shrink:0; }
    .sidebar-list { margin-top:12px; }
    .sidebar-stock { display:flex; justify-content:space-between; align-items:center; gap:8px; border:0; border-bottom:1px solid var(--line); border-radius:0; background:none; color:inherit; padding:12px 4px; width:100%; text-align:left; }
    .sidebar-stock span { min-width:0; overflow-wrap:anywhere; }
    .sidebar-stock small { display:block; color:var(--text-muted); margin-top:4px; font-size:12px; font-variant-numeric:tabular-nums; }
    .sidebar-stock[aria-pressed="true"] { background:var(--accent-soft); box-shadow:inset 3px 0 var(--accent); padding-left:10px; }
    .sidebar-stock em { font-style:normal; font-size:11px; color:var(--text-muted); white-space:nowrap; }
    #add-watch-form { border-bottom:1px solid var(--line); padding-bottom:12px; margin-bottom:12px; }
    #add-watch-form .toolbar { gap:6px; }
    #add-watch-form button { font-size:12px; }
    summary { cursor:pointer; }
    .name-correction { margin:10px 0; font-size:12px; color:var(--text-muted); }
    .sidebar-collapsed { grid-template-columns:48px minmax(0,1fr); }
    .sidebar-collapsed aside { padding:12px 8px; }
    .sidebar-collapsed .sidebar-content { display:none; }
    .context-strip { display:flex; align-items:center; gap:12px 24px; flex-wrap:wrap; padding:12px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); font-size:13px; }
    .context-strip b { color:var(--text-muted); font-weight:400; margin-right:6px; }
    .decision-filters { display:flex; gap:8px; flex-wrap:wrap; margin:16px 0; }
    .decision-filters button { font-size:13px; padding:6px 10px; background:none; color:var(--text-muted); border-color:var(--line); }
    .decision-filters button[aria-pressed="true"] { background:var(--accent-soft); border-color:var(--accent); color:var(--accent); }
    .decision-list { table-layout:fixed; }
    .decision-list th:nth-child(1) { width:15%; }
    .decision-list th:nth-child(2) { width:9%; }
    .decision-list th:nth-child(3) { width:14%; }
    .decision-list th:nth-child(4) { width:34%; }
    .decision-list th:nth-child(5) { width:16%; }
    .decision-list th:nth-child(6) { width:12%; }
    .decision-list td { padding:14px 8px; line-height:1.5; overflow-wrap:anywhere; }
    .decision-list small { display:block; color:var(--text-muted); font-size:12px; margin-top:4px; }
    .decision-list .number-cell { text-align:right; font-variant-numeric:tabular-nums; }
    .stock-link { border:0; padding:0; color:var(--accent); background:none; font-weight:600; text-align:left; }
    .risk-flag { display:inline-block; font-size:12px; color:#8d4b17; background:#fff3df; padding:2px 6px; border-radius:4px; }
    .model-details { border-top:1px solid var(--line); padding-top:14px; margin-top:20px; font-size:13px; }
    .model-details > summary { color:var(--text-muted); }
    .insight-toolbar { display:flex; align-items:center; gap:12px; flex-wrap:wrap; padding:12px 0; }
    .insight-toolbar label { display:flex; align-items:center; gap:8px; margin:0; }
    .insight-toolbar select { max-width:190px; padding:6px 8px; font-size:13px; }
    .insight-row { display:grid; grid-template-columns:minmax(120px,1.25fr) repeat(2,minmax(85px,1fr)) minmax(110px,1fr) minmax(100px,1fr) minmax(95px,1fr) 16px; align-items:center; gap:12px; }
    .insight-head { color:var(--text-muted); font-size:12px; padding:10px 0; border-bottom:1px solid var(--line); }
    .insight-stock { border-bottom:1px solid var(--line); }
    .insight-stock > summary { list-style:none; padding:15px 0; font-size:13px; }
    .insight-stock > summary::-webkit-details-marker { display:none; }
    .insight-stock > summary::after { content:'+'; color:var(--text-muted); text-align:center; }
    .insight-stock[open] > summary::after { content:'-'; }
    .insight-stock > summary:hover { background:#f7f9fb; }
    .insight-stock[open] > summary { border-bottom:1px solid var(--line); }
    .insight-cell { min-width:0; overflow-wrap:anywhere; line-height:1.5; }
    .insight-cell .value { display:block; font-variant-numeric:tabular-nums; }
    .insight-cell .numeric { white-space:nowrap; }
    .insight-cell small { display:block; margin-top:4px; font-size:11px; color:var(--text-muted); }
    .insight-cell .mobile-label { display:none; }
    .insight-detail { padding:14px 0 18px; }
    .insight-meta { font-size:12px; color:var(--text-muted); line-height:1.6; overflow-wrap:anywhere; }
    .insight-count { margin-left:auto; font-size:12px; color:var(--text-muted); }
    .insight-badge { display:inline-block; padding:2px 6px; background:#f0f4f7; color:#415466; border-radius:4px; font-size:12px; }
    .insight-badge.caution { background:#fff3df; color:#85520c; }
    .insight-evidence { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:20px; margin:14px 0; }
    .insight-evidence h4 { font-size:12px; color:var(--text-muted); margin:0 0 6px; }
    .insight-evidence p { margin:0; font-size:13px; line-height:1.7; overflow-wrap:anywhere; }
    .chan-chart { display:block; width:100%; height:300px; background:#fafbfd; border-bottom:1px solid var(--line); }
    .chan-chart text { font:11px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:#626b77; }
    .chart-legend { display:flex; align-items:center; flex-wrap:wrap; gap:8px 18px; font-size:12px; color:var(--text-muted); margin:8px 0 16px; }
    .chart-legend span { display:inline-flex; align-items:center; gap:6px; }
    .legend-line { display:inline-block; width:20px; border-top:2px solid #3976b8; }
    .legend-line.draft { border-top-style:dashed; }
    .legend-zone { display:inline-block; width:15px; height:10px; background:#f8e9bb; border:1px solid #b79131; }
    .breadth-bar { display:flex; height:5px; background:#e6e9ed; margin:12px 0; overflow:hidden; }
    .breadth-bar i { display:block; height:5px; }
    .data-alert { border-left:3px solid #b88223; background:#fff8ea; padding:10px 12px; font-size:13px; line-height:1.6; overflow-wrap:anywhere; }
    @media (max-width:1100px) {
      .insight-row { grid-template-columns:1.3fr 1fr 1fr 1fr 16px; gap:10px; }
      .insight-row .secondary-cell { display:none; }
    }
    @media (max-width:600px) {
      .insight-head { display:none; }
      .insight-row { grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px 18px; position:relative; padding-right:18px !important; }
      .insight-row .secondary-cell { display:block; }
      .insight-stock > summary::after { position:absolute; top:16px; right:0; }
      .insight-cell .mobile-label { display:block; margin:0 0 3px; font-size:11px; color:var(--text-muted); }
      .insight-evidence { grid-template-columns:1fr; gap:14px; }
      .insight-toolbar select { max-width:165px; }
      .insight-count { margin-left:0; }
      .chan-chart { height:240px; }
    }
    .analysis-panel { padding:0; background:transparent; }
    .stock-detail { background:white; }
    #review { background:white; padding:18px; }
    #review:empty { display:none; }
    .empty-analysis { padding:40px 0; color:var(--text-muted); }
    .holdings-panel, .watchlist-panel { grid-column:1 / -1; }
    @media (max-width:840px) {
      header { position:static; padding:12px 16px; }
      main, .sidebar-collapsed { grid-template-columns:minmax(0,1fr); }
      aside { padding:12px 16px; }
      .sidebar-list { max-height:180px; overflow:auto; }
      .sidebar-collapsed aside { padding:8px 16px; }
      .workspace-tabs { gap:20px; }
      .workspace-head { align-items:flex-start; }
      .workspace-head h2 { font-size:18px; }
      .workspace-head button { font-size:13px; }
      #review { padding:12px; }
      .decision-list, .decision-list tbody { display:block; }
      .decision-list thead { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); }
      .decision-list tr { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); padding:8px 0; border-bottom:1px solid var(--line); }
      .decision-list td { display:block; min-width:0; padding:6px; border:0; }
      .decision-list td:nth-child(4) { grid-column:1 / -1; }
      .decision-list td::before { content:attr(data-label); display:block; font-size:11px; color:var(--text-muted); margin-bottom:4px; }
      .decision-list .number-cell { text-align:left; }
    }
  </style>
</head>
<body>
  <header>
    <h1 data-i18n="appTitle">通达信股票工作台</h1>
    <div class="header-tools">
      <label for="languageSelect" data-i18n="language" style="margin:0">语言</label>
      <select id="languageSelect" onchange="setLanguage(this.value)">
        <option value="zh">中文</option>
        <option value="en">English</option>
      </select>
      <label for="marketSourceSelect" data-i18n="marketSource" style="margin:0">行情源</label>
      <select id="marketSourceSelect" onchange="setMarketSource(this.value)">
        <option value="tdx-official" data-i18n="tdxOfficialSource">通达信官方 Token</option>
        <option value="tongdaxin" data-i18n="tongdaxinSource">通达信 eltdx</option>
        <option value="eastmoney" data-i18n="eastmoneySource">Eastmoney 兜底</option>
        <option value="akshare" data-i18n="akshareSource">AkShare 真实行情</option>
        <option value="mock" data-i18n="mockSource">Mock 演示行情</option>
      </select>
      <span class="status" id="health" data-i18n="checking">检查中...</span>
    </div>
  </header>
  <main id="workspace-layout">
    <aside>
      <div class="sidebar-head"><h2 class="sidebar-content" data-i18n="myWatchlist">我的关注</h2><button id="sidebar-toggle" class="secondary icon-button" onclick="toggleSidebar()" aria-expanded="true" title="收起关注列表" aria-label="收起关注列表">‹</button></div>
      <div class="sidebar-content">
      <div class="sidebar-head"><span class="status" id="watch-count"></span><button id="add-watch-toggle" class="secondary icon-button" onclick="toggleAddWatch()" aria-expanded="false" title="添加关注股" aria-label="添加关注股">+</button></div>
      <div id="add-watch-form" hidden>
      <label for="symbol" data-i18n="symbolOrName">股票代码或名称</label>
      <input id="symbol" value="" data-i18n-placeholder="symbolOrNamePlaceholder" placeholder="例如：600519 / 贵州茅台" oninput="onSymbolChanged()" onblur="hydrateSymbolFromMarket(false)">
      <details class="name-correction"><summary data-i18n="correctName">修正名称</summary>
      <label for="name" data-i18n="nameOptional">名称</label>
      <input id="name" value="" data-i18n-placeholder="nameOptionalPlaceholder" placeholder="可选，查询后自动填充" oninput="onNameChanged()">
      </details>
      <div class="toolbar" style="margin-top:14px">
        <button onclick="addSymbolToPool()" data-i18n="addWatchSymbolButton">添加关注</button>
        <button class="secondary" onclick="hydrateSymbolFromMarket(true)" data-i18n="fetchQuote">查询行情</button>
        <button class="secondary" onclick="refreshAll()" data-i18n="refresh">刷新</button>
      </div>
      <p class="status" id="quoteStatus"></p>
      </div>
      <label for="watch-search" data-i18n="searchWatchlist">搜索关注</label>
      <input id="watch-search" type="search" oninput="renderSidebar()" autocomplete="off">
      <div id="sidebar-stocks" class="sidebar-list"></div>
      </div>
    </aside>
    <section>
      <nav class="workspace-tabs" aria-label="Workspace">
        <button id="nav-opportunities" onclick="switchWorkspace('opportunities')" data-i18n="navOpportunities" aria-pressed="false">市场机会</button>
        <button id="nav-stocks" onclick="switchWorkspace('stocks')" data-i18n="navStocks" aria-pressed="true">我的股票</button>
        <button id="nav-history" onclick="switchWorkspace('history')" data-i18n="navHistory" aria-pressed="false">分析记录</button>
      </nav>
      <div class="workspace-head"><h2 id="view-title"></h2><button id="update-analysis" onclick="updateActiveView()"></button></div>
      <div id="view-tabs" class="view-tabs" aria-label="Analysis views"></div>
      <p class="status" id="actionStatus" role="status"></p>
      <div class="grid">
        <div id="analysis-panel" class="panel analysis-panel">
          <div id="review"><p class="status" data-i18n="analysisResultHint">这里显示股票池行情分析或每日复盘结果。</p></div>
        </div>
        <div id="watchlist-panel" class="panel watchlist-panel" hidden>
          <h2 data-i18n="poolMembers">股票池</h2>
          <p class="status" id="poolHint"></p>
          <div id="watchlist"></div>
        </div>
        <div id="holdings-panel" class="panel holdings-panel" hidden>
          <h2 data-i18n="holdings">持仓</h2>
          <p class="status" id="holdingsHint"></p>
          <div id="holdings"></div>
        </div>
      </div>
    </section>
  </main>
  <script>
    const translations = {
      zh: {
        navOpportunities: "市场机会", navStocks: "我的股票", navHistory: "分析记录",
        myWatchlist: "我的关注", searchWatchlist: "搜索关注", correctName: "修正名称",
        collapseWatchlist: "收起关注列表", expandWatchlist: "展开关注列表",
        decisionView: "持仓决策", chanView: "缠论结构", quotesView: "行情概览", holdingsView: "持仓与盈亏",
        watchlistView: "关注管理", reviewView: "决策复盘", updateAnalysis: "更新分析", loadRecords: "读取记录",
        emptyAnalysis: "此视图暂无分析结果", startAnalysis: "开始分析",
        allStocks: "全部股票", mainReason: "主要依据", conclusion: "当前判断", details: "查看依据",
        modelDetails: "市场证据与模型详情", analyzedStocks: "分析股票", failedStocks: "数据失败",
        completeStocks: "完整数据", scenarioWeights: "未校准情景权重", noEvidence: "暂无有效证据",
        selectedStock: "已选股票", clearSelection: "清除选择", latestAnalysis: "分析时间",
        noMatchingStocks: "没有符合此筛选条件的股票", scoreCaution: "情景权重未经校准，不代表真实涨跌概率。",
        poolBreadthLabel: "个人股票池样本", stockCount: "只", daysUnit: "交易日",
        appTitle: "通达信股票工作台",
        language: "语言",
        checking: "检查中...",
        running: "运行中",
        addHolding: "新增持仓",
        addWatchSymbol: "添加关注股",
        symbol: "股票代码",
        symbolOrName: "股票代码或名称",
        symbolOrNamePlaceholder: "例如：600519 / 贵州茅台",
        name: "名称",
        nameOptional: "名称",
        nameOptionalPlaceholder: "可选，查询后自动填充",
        quantity: "数量",
        saveQuantity: "保存数量",
        quantityUpdated: "已更新持仓数量",
        holdingAdded: "已加入持仓",
        holdingAlreadyExists: "该股票已在持仓栏",
        addHoldingFromPool: "加入持仓",
        addHoldingFailed: "加入持仓失败",
        holdingUpdated: "已更新持仓",
        costPrice: "成本价",
        stopLoss: "止损价",
        takeProfit: "止盈价",
        thesis: "买入理由",
        add: "添加",
        addWatchSymbolButton: "添加关注",
        addToPool: "加入股票池",
        refresh: "刷新",
        fetchQuote: "查询行情",
        marketSource: "行情源",
        tdxOfficialSource: "通达信官方 Token",
        tongdaxinSource: "通达信 eltdx",
        eastmoneySource: "Eastmoney 兜底",
        akshareSource: "AkShare 真实行情",
        mockSource: "Mock 演示行情",
        quoteLoaded: "已读取行情",
        quoteFailed: "行情读取失败",
        lookupNoMatch: "未找到匹配股票",
        symbolResolved: "已识别股票",
        watchSymbolAdded: "已加入当前股票池",
        watchSymbolExists: "该股票已在当前股票池",
        mockSourceHint: "当前使用演示行情，名称和价格不代表真实市场。",
        officialSourceHint: "当前使用通达信官方 Token 数据源。",
        realSourceHint: "当前使用通达信/真实行情源。若通达信 7709 连接失败，可临时切换 Eastmoney 兜底。",
        runDecisionEngine: "持仓决策引擎",
        decisionEngineFailed: "持仓决策引擎分析失败",
        decisionEngineModel: "决策模型",
        horizonDays: "目标周期",
        scenarioCounts: "情景分布",
        marketRegime: "市场状态",
        regimeConfidence: "状态置信度",
        strategyBias: "策略偏向",
        regimeEvidence: "状态证据",
        analyzePool: "分析股票池行情",
        runChanAnalysis: "缠论结构分析",
        chanAnalysisFailed: "缠论结构分析失败",
        chanPeriod: "周期",
        chanSignalCounts: "信号分布",
        chanSignal: "缠论信号",
        structure: "结构位置",
        confidence: "信心等级",
        center_range: "最近中枢",
        trigger: "触发条件",
        invalidation: "失效条件",
        reason: "判断依据",
        bar_count: "K线数",
        stroke_count: "笔数",
        center_count: "中枢数",
        dailyReview: "生成复盘",
        holdings: "持仓",
        poolMembers: "股票池",
        poolHint: "这里是你的关注名单，行情分析范围由个人股票池决定。",
        signals: "信号",
        analysisResult: "分析结果",
        analysisResultFocus: "这里优先显示股票池级分析、缠论结构和每日复盘明细。",
        analysisResultHint: "这里显示股票池行情分析或每日复盘结果。",
        noData: "暂无数据。",
        quoteMissing: "未取到现价",
        poolAnalysisFailed: "股票池分析失败",
        mcpToolPlan: "MCP 工具计划",
        marketDataSource: "行情源",
        quoteOkCount: "已取行情",
        missingQuotes: "缺行情股票",
        failedSymbols: "失败股票",
        nextSteps: "下一步",
        savedHolding: "已保存持仓",
        updatedHolding: "已更新已有持仓",
        duplicateHoldingNote: "检测到相同股票代码，已更新原持仓，避免重复记录。",
        autoSignalCreated: "已为该股票自动生成最新信号",
        poolHoldingsHint: "正在显示当前股票池中每只股票最新一条持仓。",
        highRiskSymbols: "高风险股票",
        failedFetchCount: "数据拉取失败数",
        holdingDetails: "持仓明细",
        highRiskSignalDetails: "高风险信号明细",
        recentSignalDetails: "近期预测信号",
        failedFetchDetails: "数据拉取失败明细",
        fetchOk: "未发现数据拉取失败",
        reviewedTemplate: "已复盘 {holdings} 条持仓和 {signals} 条近期信号。",
        highRiskSignalCount: "高风险信号数",
        nextFocus: "下一交易日重点",
        focus_review_high_risk: "优先复核高风险信号。",
        focus_check_data_quality: "确认行情/指标数据正常后再参考信号排序。",
        focus_compare_with_thesis: "把任何行动信号和原始买入理由再对照一次。",
        mode: "模式",
        id: "ID",
        priority: "优先级",
        status: "状态",
        source: "来源",
        data_type: "数据类型",
        message: "信息",
        fetched_at: "拉取时间",
        strength: "强度",
        decision: "建议",
        up_probability: "上涨评分",
        range_probability: "震荡评分",
        down_probability: "下跌评分",
        scenarioScores: "情景评分",
        uncalibrated: "模型评分未经校准，不代表未来涨跌的真实概率。",
        calibrationStatus: "校准状态",
        stockDetails: "个股明细",
        factorMetrics: "因子指标与窗口",
        evidence: "证据",
        observation: "观察",
        contribution: "评分贡献",
        regime_weight: "市场状态权重",
        dataQuality: "数据质量与缺失项",
        issues: "缺失或异常",
        unavailable: "未提供",
        price_origin: "价格来源",
        price_origin_quote: "实时报价",
        price_origin_latest_close: "最近K线收盘价",
        price_origin_kline_close: "K线收盘价",
        kline_as_of: "K线截至日期",
        quote_fetched_at: "报价拉取时间",
        window: "窗口",
        windows: "窗口",
        start: "开始",
        end: "结束",
        start_date: "开始日期",
        end_date: "结束日期",
        return_pct: "窗口收益率",
        start_close: "起点收盘价",
        end_close: "终点收盘价",
        calendar_source: "交易日历来源",
        start_lag_calendar_days: "起点滞后自然日",
        end_lag_calendar_days: "终点滞后自然日",
        momentum: "动量",
        relative_strength: "相对强弱",
        attribution: "因子归因",
        mean_reversion: "均值回归",
        return20_pct: "20日收益率",
        return60_pct: "60日收益率",
        volume_ratio: "量比",
        market_index_symbol: "基准指数",
        as_of: "截至日期",
        stock: "个股窗口",
        index: "指数窗口",
        sessions: "交易日数",
        pool_sample_size: "股票池样本数",
        start_lag_sessions: "起点滞后交易日",
        end_lag_sessions: "终点滞后交易日",
        comparison: "与上次分析比较",
        previousGeneratedAt: "上次生成时间",
        previousScores: "上次情景评分",
        currentScores: "本次情景评分",
        scoreChanges: "评分变化（百分点）",
        previousDecision: "上次建议",
        currentDecision: "本次建议",
        savedAnalysis: "已保存分析",
        analysisReportId: "分析报告 ID",
        analysisGeneratedAt: "分析生成时间",
        dailyReviewFailed: "复盘生成失败",
        decisionNotAnalyzed: "当前股票池和行情源暂无已保存分析，请先运行持仓决策引擎。",
        partialValuation: "部分估值",
        noValuation: "暂无可估值持仓",
        pricedHoldings: "已定价持仓",
        unpricedHoldings: "未定价持仓",
        valuationCoverage: "估值覆盖率",
        pricedCost: "已定价持仓成本",
        pricedMarketValue: "已定价持仓市值",
        pricedPnl: "已定价持仓盈亏",
        pricedPnlPct: "已定价持仓收益率",
        pnl_pct: "持仓盈亏",
        evidence_summary: "关键证据",
        momentum_20_pct: "20日动量",
        vs_index_20_pct: "相对指数20日",
        vs_pool_20_pct: "相对股票池20日",
        excess_market_20_pct: "超额大盘20日",
        excess_pool_median_20_pct: "超额股票池20日",
        ma20_deviation_pct: "MA20偏离",
        current_price: "现价",
        market_value: "持仓市值",
        estimated_pnl: "预计盈亏",
        estimated_pnl_pct: "盈亏比例",
        total_cost_basis: "总成本",
        total_market_value: "总市值",
        total_estimated_pnl: "总盈亏",
        total_estimated_pnl_pct: "总收益率",
        save: "保存",
        reasons: "原因",
        next_check: "下一步观察",
        signal_type: "信号类型",
        action: "动作",
        risk_level: "风险",
        action_hint: "行动提示",
        price: "价格",
        created_at: "生成时间",
        cost_price: "成本价",
        stop_loss: "止损价",
        take_profit: "止盈价",
        initial_thesis: "原始理由"
      },
      en: {
        navOpportunities: "Market opportunities", navStocks: "My stocks", navHistory: "Analysis history",
        myWatchlist: "Watchlist", searchWatchlist: "Search watchlist", correctName: "Edit name",
        collapseWatchlist: "Collapse watchlist", expandWatchlist: "Expand watchlist",
        decisionView: "Position analysis", chanView: "Chan structure", quotesView: "Market overview", holdingsView: "Holdings & P/L",
        watchlistView: "Manage watchlist", reviewView: "Decision review", updateAnalysis: "Update analysis", loadRecords: "Load records",
        emptyAnalysis: "No analysis in this view yet", startAnalysis: "Start analysis",
        allStocks: "All stocks", mainReason: "Key evidence", conclusion: "Assessment", details: "View evidence",
        modelDetails: "Market evidence & model details", analyzedStocks: "Stocks analyzed", failedStocks: "Data failures",
        completeStocks: "Complete data", scenarioWeights: "Uncalibrated scenario weights", noEvidence: "No valid evidence",
        selectedStock: "Selected stock", clearSelection: "Clear selection", latestAnalysis: "Analyzed at",
        noMatchingStocks: "No stocks match this filter", scoreCaution: "Scenario weights are not calibrated probabilities.",
        poolBreadthLabel: "Personal watchlist sample", stockCount: "stocks", daysUnit: "sessions",
        appTitle: "Tongdaxin Stock Workbench",
        language: "Language",
        checking: "checking...",
        running: "running",
        addHolding: "Add Holding",
        addWatchSymbol: "Add Watch Symbol",
        symbol: "Symbol",
        symbolOrName: "Symbol or Name",
        symbolOrNamePlaceholder: "e.g. 600519 / Kweichow Moutai",
        name: "Name",
        nameOptional: "Name",
        nameOptionalPlaceholder: "Optional, auto-filled after lookup",
        quantity: "Quantity",
        saveQuantity: "Save Quantity",
        quantityUpdated: "Holding quantity updated",
        holdingAdded: "Added to holdings",
        holdingAlreadyExists: "Already in holdings",
        addHoldingFromPool: "Add Holding",
        addHoldingFailed: "Add holding failed",
        holdingUpdated: "Holding updated",
        costPrice: "Cost Price",
        stopLoss: "Stop Loss",
        takeProfit: "Take Profit",
        thesis: "Thesis",
        add: "Add",
        addWatchSymbolButton: "Add Watch",
        addToPool: "Add to Pool",
        refresh: "Refresh",
        fetchQuote: "Fetch Quote",
        marketSource: "Market Source",
        tdxOfficialSource: "Tongdaxin Official Token",
        tongdaxinSource: "Tongdaxin eltdx",
        eastmoneySource: "Eastmoney Fallback",
        akshareSource: "AkShare Real",
        mockSource: "Mock Demo",
        quoteLoaded: "Quote loaded",
        quoteFailed: "Quote failed",
        lookupNoMatch: "No matching stock found",
        symbolResolved: "Stock resolved",
        watchSymbolAdded: "Added to the current stock pool",
        watchSymbolExists: "This symbol is already in the current stock pool",
        mockSourceHint: "Demo quotes are synthetic and do not represent the real market.",
        officialSourceHint: "Using the official Tongdaxin Token source.",
        realSourceHint: "Using Tongdaxin or a real market data source. If Tongdaxin 7709 fails, switch to Eastmoney fallback.",
        runDecisionEngine: "Position Decision Engine",
        decisionEngineFailed: "Position decision engine failed",
        decisionEngineModel: "Decision model",
        horizonDays: "Horizon",
        scenarioCounts: "Scenario mix",
        marketRegime: "Market Regime",
        regimeConfidence: "Regime Confidence",
        strategyBias: "Strategy Bias",
        regimeEvidence: "Regime Evidence",
        analyzePool: "Analyze Pool Quotes",
        runChanAnalysis: "Chan Structure",
        chanAnalysisFailed: "Chan structure analysis failed",
        chanPeriod: "Period",
        chanSignalCounts: "Signal mix",
        chanSignal: "Chan Signal",
        structure: "Structure",
        confidence: "Confidence",
        center_range: "Latest Center",
        trigger: "Trigger",
        invalidation: "Invalidation",
        reason: "Reason",
        bar_count: "Bars",
        stroke_count: "Strokes",
        center_count: "Centers",
        dailyReview: "Create Review",
        holdings: "Holdings",
        poolMembers: "Stock Pool",
        poolHint: "This is your watchlist. The personal stock pool controls the quote analysis scope.",
        signals: "Signals",
        analysisResult: "Analysis Result",
        analysisResultFocus: "Pool analysis, Chan structure, and daily review details appear here first.",
        analysisResultHint: "Pool quote analysis and daily review results appear here.",
        noData: "No data yet.",
        quoteMissing: "Quote unavailable",
        poolAnalysisFailed: "Pool analysis failed",
        mcpToolPlan: "MCP tool plan",
        marketDataSource: "Market source",
        quoteOkCount: "Quotes loaded",
        missingQuotes: "Missing quotes",
        failedSymbols: "Failed symbols",
        nextSteps: "Next steps",
        savedHolding: "Holding saved",
        updatedHolding: "Existing holding updated",
        duplicateHoldingNote: "Same symbol detected; updated the existing holding to avoid duplicates.",
        autoSignalCreated: "A fresh signal was generated for this symbol",
        poolHoldingsHint: "Showing the latest holding per symbol in the current stock pool.",
        highRiskSymbols: "High-risk symbols",
        failedFetchCount: "Failed fetches",
        holdingDetails: "Holding Details",
        highRiskSignalDetails: "High-risk Signal Details",
        recentSignalDetails: "Recent Prediction Signals",
        failedFetchDetails: "Failed Fetch Details",
        fetchOk: "No failed data fetches",
        reviewedTemplate: "Reviewed {holdings} holdings and {signals} recent signals.",
        highRiskSignalCount: "High-risk signals",
        nextFocus: "Next session focus",
        focus_review_high_risk: "Review high-risk signals first.",
        focus_check_data_quality: "Confirm quote and indicator data before trusting signal rankings.",
        focus_compare_with_thesis: "Compare every action signal with the original position thesis.",
        mode: "mode",
        id: "ID",
        priority: "Priority",
        status: "Status",
        source: "Source",
        data_type: "Data Type",
        message: "Message",
        fetched_at: "Fetched At",
        strength: "Strength",
        decision: "Decision",
        up_probability: "Up score",
        range_probability: "Range score",
        down_probability: "Down score",
        scenarioScores: "Scenario scores",
        uncalibrated: "Model scores are not calibrated and are not actual probabilities of future price moves.",
        calibrationStatus: "Calibration status",
        stockDetails: "Stock details",
        factorMetrics: "Factor metrics and windows",
        evidence: "Evidence",
        observation: "Observation",
        contribution: "Score contribution",
        regime_weight: "Regime weight",
        dataQuality: "Data quality and missing data",
        issues: "Missing or abnormal data",
        unavailable: "Not supplied",
        price_origin: "Price origin",
        price_origin_quote: "Live quote",
        price_origin_latest_close: "Latest K-line close",
        price_origin_kline_close: "K-line close",
        kline_as_of: "K-line as of",
        quote_fetched_at: "Quote fetched at",
        window: "Window",
        windows: "Windows",
        start: "Start",
        end: "End",
        start_date: "Start date",
        end_date: "End date",
        return_pct: "Window return",
        start_close: "Start close",
        end_close: "End close",
        calendar_source: "Trading calendar source",
        start_lag_calendar_days: "Start lag (calendar days)",
        end_lag_calendar_days: "End lag (calendar days)",
        momentum: "Momentum",
        relative_strength: "Relative strength",
        attribution: "Factor attribution",
        mean_reversion: "Mean reversion",
        return20_pct: "20D return",
        return60_pct: "60D return",
        volume_ratio: "Volume ratio",
        market_index_symbol: "Benchmark index",
        as_of: "As of",
        stock: "Stock window",
        index: "Index window",
        sessions: "Trading sessions",
        pool_sample_size: "Pool sample size",
        start_lag_sessions: "Start lag (sessions)",
        end_lag_sessions: "End lag (sessions)",
        comparison: "Comparison with previous analysis",
        previousGeneratedAt: "Previous generation time",
        previousScores: "Previous scenario scores",
        currentScores: "Current scenario scores",
        scoreChanges: "Score changes (percentage points)",
        previousDecision: "Previous decision",
        currentDecision: "Current decision",
        savedAnalysis: "Saved analysis",
        analysisReportId: "Analysis report ID",
        analysisGeneratedAt: "Analysis generated at",
        dailyReviewFailed: "Daily review failed",
        decisionNotAnalyzed: "No saved analysis for this pool and market source. Run the decision engine first.",
        partialValuation: "Partial valuation",
        noValuation: "No holdings can be valued",
        pricedHoldings: "Priced holdings",
        unpricedHoldings: "Unpriced holdings",
        valuationCoverage: "Valuation coverage",
        pricedCost: "Priced holdings cost",
        pricedMarketValue: "Priced holdings value",
        pricedPnl: "Priced holdings P/L",
        pricedPnlPct: "Priced holdings return",
        pnl_pct: "Position P/L",
        evidence_summary: "Key Evidence",
        momentum_20_pct: "20D Momentum",
        vs_index_20_pct: "20D vs Index",
        vs_pool_20_pct: "20D vs Pool",
        excess_market_20_pct: "20D Excess vs Market",
        excess_pool_median_20_pct: "20D Excess vs Pool",
        ma20_deviation_pct: "MA20 Deviation",
        current_price: "Current Price",
        market_value: "Market Value",
        estimated_pnl: "Estimated P/L",
        estimated_pnl_pct: "P/L %",
        total_cost_basis: "Total Cost",
        total_market_value: "Total Value",
        total_estimated_pnl: "Total P/L",
        total_estimated_pnl_pct: "Total Return",
        save: "Save",
        reasons: "Reasons",
        next_check: "Next Check",
        signal_type: "Signal Type",
        action: "Action",
        risk_level: "Risk",
        action_hint: "Action Hint",
        price: "Price",
        created_at: "Created At",
        cost_price: "Cost Price",
        stop_loss: "Stop Loss",
        take_profit: "Take Profit",
        initial_thesis: "Original Thesis"
      }
    };
    Object.assign(translations.zh, {
      periodLabel:"研究周期", periodBaseline:"原版20日名单", period5:"短线 · 5日", period20:"波段 · 20日",
      period60:"中期 · 60日", period120:"中期 · 120日", periodlong_term:"长期 · 基本面",
      periodNote:"周期按交易日计；独立技术检查分 / 100，非胜率。各周期最多展示10只条件较有利或待确认的股票。",
      periodLegacy:"该历史记录未保存分周期评价，不追溯补算。", periodEvidence:"周期依据",
      stance_favorable:"条件较有利", stance_wait:"等待确认", stance_avoid:"暂不支持参与", stance_insufficient:"证据不足", stance_legacy:"当时未记录",
      fundamentals_unverified:"财务、估值、行业和事件证据尚未验证，暂不判断长期参与价值。",
      quality_gate_failed:"未通过行情质量或证券范围检查", unaligned_daily_data:"个股与指数日线末日未对齐",
      stale_daily_data:"日线过期", insufficient_period_history:"该周期历史长度不足", missing_period_sessions:"该周期交易日缺失",
      inactive_period_sessions:"交易日成交量为零或缺失", invalid_daily_data:"日线数据无效", duplicate_dates:"日线日期重复",
      extended:"价格偏离均线较远", market_caution:"大盘偏弱或状态不明，等待进一步确认",
      trend_positive:"价格与均线结构向上", trend_negative:"价格跌破该周期短均线", trend_mixed:"趋势条件尚未齐备",
      relative_positive:"同窗口跑赢指数", relative_negative:"同窗口弱于指数", relative_flat:"与指数表现相近",
      volume_confirmed:"成交量支持", volume_weak:"成交量偏弱", volatility_high:"波动率偏高", volatility_normal:"波动率未触发高波动门槛",
      periodConfirm:"复核条件：收盘保持参考均线上方、相对指数强势且成交量确认。",
      periodReview:"跌破复核参考", periodExcess:"区间超额", periodReturn:"区间涨跌", periodVolume:"量比",
      followupTitle:"推荐后表现", followupOpen:"查看后续表现", followupRefresh:"更新表现", followupCancel:"取消更新",
      followupWindow:"收益观察窗口", followupMethod:"推荐日后下一交易日开盘至第N个交易日收盘；与沪深300严格同日期比较，起终价来自同一批TQFlag=11日线。这里只统计价格表现，不是可执行交易收益；未计费用、滑点、分红现金或涨跌停成交限制。",
      followupCaution:"成熟样本才纳入统计；候选经过预筛选且样本存在重叠，不能据此认定预测准确率或未来胜率。",
      followupNotStarted:"尚未更新后续行情。", followupFailed:"表现更新失败，原始推荐记录未改动。",
      followupRetained:"下方保留上次保存的结果，本次更新尚未产出新结果。请以所示行情日期与评估时间为准。",
      followupSnapshot:"推荐时间", followupAsOf:"行情观察截至", followupUpdated:"结果评估时间", followupOriginal:"查看当时推荐",
      followupBaseGroups:"原版20日名单分组", followupPeriodGroups:"当时分周期判断分组", followupDetails:"逐股结果",
      followupGroup:"当时分组", followupSelected:"入选", followupNotSelected:"未入选", followupExcluded:"数据/范围排除",
      followupMatured:"已到期 / 全部", followupPending:"未到期", followupUnavailable:"无法评估",
      followupMeanReturn:"平均涨跌", followupMeanExcess:"平均超额", followupPositive:"正收益占比", followupDrawdown:"最大回撤",
      followupWorstDrawdown:"最深回撤", followupStockReturn:"个股涨跌", followupIndexReturn:"指数涨跌", followupExcess:"超额（百分点）",
      followupDates:"参考窗口", followupReference:"参考开盘 / 期末收盘", followupState:"观察状态",
      followup_legacy:"当时未记录", followup_pending:"未到期", followup_matured:"已到期", followup_unavailable:"无法评估",
      missing_stock_sessions:"股票交易日缺失或停牌", missing_benchmark:"缺少基准日线", stale_benchmark:"基准行情过期，不能确认是否到期",
      history_window_lost:"返回历史未覆盖推荐日，不能确定起点", unverified_price_basis:"历史价格口径未经确认",
      missing_benchmark_sessions:"已知个股交易日缺少对应指数日线",
      unverified_benchmark:"历史基准未经确认", invalid_snapshot_time:"历史记录时间无效", future_snapshot:"记录时间晚于评估时间",
      outside_stock_scope:"不在A股个股范围内",
      queued:"排队中", running:"运行中", completed:"已完成", cancelled:"已取消", interrupted:"已中断", failed:"失败",
      opportunityReconnect:"进度连接暂时中断，正在重试", opportunityResume:"重新连接进度",
      marketOpportunities:"市场机会推荐", opportunityHistory:"推荐记录", opportunityTitle:"市场机会推荐",
      opportunityScope:"条件选股候选 + 个人关注及持仓", opportunityScan:"扫描", opportunityCandidates:"池外候选",
      opportunityPersonal:"个人股票", opportunitySelected:"入选", opportunityExcluded:"数据或范围不合格",
      opportunityEmpty:"本次没有符合标准的推荐。可展开全部评价查看具体原因。",
      opportunityUnsupported:"市场候选发现需要选择通达信官方 Token 数据源。",
      opportunityFailed:"扫描未完成，请检查连接后重试。已保存的历史记录仍可查看。",
      opportunityCancel:"取消扫描", opportunityCancelled:"扫描已取消", opportunityInterrupted:"扫描因服务重启中断，请重新扫描。",
      opportunityDiscovering:"正在获取市场候选", opportunityAnalyzing:"正在分析日线与证据",
      opportunityAll:"全部评价", opportunityTop:"推荐名单", opportunityOrigin:"来源", opportunityAny:"全部来源",
      opportunityNew:"新发现", opportunityWatched:"已关注", opportunityHeld:"已持仓",
      opportunityPriority:"优先研究", opportunityWait:"等待确认", opportunityNotSelected:"未入选", opportunityInvalid:"数据待补齐/不在范围",
      opportunityBasis:"支持依据", opportunityRisk:"风险与缺口", opportunityConditions:"确认与失效参考",
      opportunityNoOpposition:"现有技术证据未显示明显反对项；基本面和事件风险尚未覆盖。",
      opportunityTechnical:"当前为技术证据筛选；行业、风格、财务和事件尚未覆盖。排序分和情景分数未经胜率校准。",
      opportunityCoverage:"候选来源与覆盖", opportunityPartial:"候选或行情读取有失败，本次覆盖不完整。",
      opportunityScore:"排序分", opportunityAsOf:"日线截至", opportunityAdd:"加入关注", opportunityAdded:"已加入关注",
      opportunityErrors:"失败明细", opportunitySaved:"已保存", opportunityDemo:"模拟数据演示",
      opportunityConfirm:"等待价格在MA20附近企稳，并保持相对指数强势后复核。",
      opportunityInvalidation:"日线收盘低于以下参考价时重新评估原假设",
      opportunityRefresh:"结果按扫描时的数据保存，最新判断请重新扫描。",
      history_under_120:"历史日线不足120根", missing_name:"股票名称缺失", special_treatment:"ST或退市股票",
      low_or_unknown_liquidity:"成交额不足2000万元或缺失", inactive_or_unknown:"成交量为零或缺失",
      price_basis_mismatch:"现价与日线价格口径明显不一致", no_index_outperformance:"20/60日均未跑赢指数",
      high_risk:"技术风险较高", extended_price:"价格偏离均线较远，等待回踩", weak_evidence:"支持证据未达入选标准",
      screen_unavailable:"选股接口失败或无权限", quote_unavailable:"现价读取失败", kline_unavailable:"日线读取失败", index_unavailable:"基准指数读取失败"
    });
    Object.assign(translations.en, {
      periodLabel:"Research horizon", periodBaseline:"Original 20-day shortlist", period5:"Short · 5 sessions", period20:"Swing · 20 sessions",
      period60:"Medium · 60 sessions", period120:"Medium · 120 sessions", periodlong_term:"Long · fundamentals",
      periodNote:"Trading sessions; independent technical checklist scores / 100, not win rates. Each horizon shows up to 10 favorable or confirmation-pending candidates.",
      periodLegacy:"No period assessment was saved for this historical scan; none is backfilled.", periodEvidence:"Horizon evidence",
      stance_favorable:"Favorable conditions", stance_wait:"Await confirmation", stance_avoid:"Participation not supported", stance_insufficient:"Insufficient evidence", stance_legacy:"Not recorded",
      fundamentals_unverified:"Financials, valuation, industry and event evidence remain unverified. No long-term suitability judgment.",
      quality_gate_failed:"Failed data quality or instrument scope checks", unaligned_daily_data:"Stock and benchmark endpoints differ",
      stale_daily_data:"Stale daily bars", insufficient_period_history:"Insufficient history for this horizon", missing_period_sessions:"Missing sessions in this window",
      inactive_period_sessions:"Zero or missing session volume", invalid_daily_data:"Invalid daily data", duplicate_dates:"Duplicate daily dates",
      extended:"Extended from moving average", market_caution:"Weak or unknown market regime; await confirmation",
      trend_positive:"Positive price and moving-average structure", trend_negative:"Price below the horizon's fast MA", trend_mixed:"Trend conditions incomplete",
      relative_positive:"Outperformed the index in the same window", relative_negative:"Underperformed the index in the same window", relative_flat:"Similar performance to index",
      volume_confirmed:"Volume support", volume_weak:"Weak volume", volatility_high:"Elevated volatility", volatility_normal:"Volatility below the high-volatility threshold",
      periodConfirm:"Review conditions: close above reference MA, positive index-relative strength and volume confirmation.",
      periodReview:"Reassess below", periodExcess:"Window excess", periodReturn:"Window return", periodVolume:"Volume ratio",
      followupTitle:"Post-recommendation performance", followupOpen:"View follow-up", followupRefresh:"Update performance", followupCancel:"Cancel update",
      followupWindow:"Return observation window", followupMethod:"Next session open after the recommendation date to the Nth session close; identical dates versus CSI 300, with both endpoints from one TQFlag=11 daily batch. Price observations, not executable trading returns; no costs, slippage, cash dividends or limit-lock execution constraints.",
      followupCaution:"Only matured samples enter statistics. Screened and overlapping samples do not establish predictive accuracy or future win rates.",
      followupNotStarted:"Subsequent prices have not been refreshed.", followupFailed:"Performance update failed. Original recommendations are unchanged.",
      followupRetained:"Previously saved results are shown below. This update has not produced new results; use the displayed price and evaluation dates.",
      followupSnapshot:"Recommendation time", followupAsOf:"Benchmark through", followupUpdated:"Results evaluated at", followupOriginal:"View original scan",
      followupBaseGroups:"Original 20-day shortlist groups", followupPeriodGroups:"Original horizon assessment groups", followupDetails:"Stock-level outcomes",
      followupGroup:"Original group", followupSelected:"Selected", followupNotSelected:"Not selected", followupExcluded:"Quality / scope excluded",
      followupMatured:"Matured / all", followupPending:"Pending", followupUnavailable:"Unavailable",
      followupMeanReturn:"Mean return", followupMeanExcess:"Mean excess", followupPositive:"Positive-return share", followupDrawdown:"Max drawdown",
      followupWorstDrawdown:"Worst drawdown", followupStockReturn:"Stock return", followupIndexReturn:"Index return", followupExcess:"Excess (pp)",
      followupDates:"Observation dates", followupReference:"Reference open / end close", followupState:"Observation status",
      followup_legacy:"Not recorded", followup_pending:"Pending", followup_matured:"Matured", followup_unavailable:"Unavailable",
      missing_stock_sessions:"Missing or suspended stock sessions", missing_benchmark:"Missing benchmark bars", stale_benchmark:"Stale benchmark; maturity unknown",
      history_window_lost:"Returned history does not cover the recommendation date", unverified_price_basis:"Unverified historical price basis",
      missing_benchmark_sessions:"Benchmark bars missing on known stock trading dates",
      unverified_benchmark:"Unverified historical benchmark", invalid_snapshot_time:"Invalid snapshot timestamp", future_snapshot:"Snapshot is later than evaluation time",
      outside_stock_scope:"Outside the A-share stock scope",
      queued:"Queued", running:"Running", completed:"Completed", cancelled:"Cancelled", interrupted:"Interrupted", failed:"Failed",
      opportunityReconnect:"Progress connection interrupted; retrying", opportunityResume:"Reconnect to scan",
      marketOpportunities:"Market Opportunities", opportunityHistory:"Recommendation History", opportunityTitle:"Market Opportunities",
      opportunityScope:"Screened candidates + personal watchlist and holdings", opportunityScan:"Scan", opportunityCandidates:"New candidates",
      opportunityPersonal:"Personal stocks", opportunitySelected:"Selected", opportunityExcluded:"Quality / scope exclusions",
      opportunityEmpty:"No stocks qualified in this scan. Expand all assessments to see why.",
      opportunityUnsupported:"Market discovery requires the official Tongdaxin Token source.",
      opportunityFailed:"Scan failed. Check connectivity and retry. Saved history remains available.",
      opportunityCancel:"Cancel scan", opportunityCancelled:"Scan cancelled", opportunityInterrupted:"Server restart interrupted this scan. Run it again.",
      opportunityDiscovering:"Discovering market candidates", opportunityAnalyzing:"Analyzing daily bars and evidence",
      opportunityAll:"All assessments", opportunityTop:"Shortlist", opportunityOrigin:"Origin", opportunityAny:"All origins",
      opportunityNew:"New discovery", opportunityWatched:"Watching", opportunityHeld:"Held",
      opportunityPriority:"Research first", opportunityWait:"Await confirmation", opportunityNotSelected:"Not selected", opportunityInvalid:"Quality / scope exclusion",
      opportunityBasis:"Supporting evidence", opportunityRisk:"Risks and gaps", opportunityConditions:"Confirmation and invalidation",
      opportunityNoOpposition:"No clear opposing technical evidence. Fundamental and event risks are not covered.",
      opportunityTechnical:"Technical screening only; industry, style, financials and events are not covered. Ranking and scenario scores are uncalibrated.",
      opportunityCoverage:"Candidate sources and coverage", opportunityPartial:"Some candidate or market requests failed; coverage is incomplete.",
      opportunityScore:"Rank score", opportunityAsOf:"Daily bars through", opportunityAdd:"Add to watchlist", opportunityAdded:"Added to watchlist",
      opportunityErrors:"Request failures", opportunitySaved:"Saved", opportunityDemo:"Simulated data",
      opportunityConfirm:"Review after price stabilizes near MA20 and maintains strength versus the index.",
      opportunityInvalidation:"Reassess the thesis if a daily close falls below this reference",
      opportunityRefresh:"Results retain scan-time data. Run a new scan for an updated assessment.",
      history_under_120:"Fewer than 120 daily bars", missing_name:"Missing name", special_treatment:"ST or delisting security",
      low_or_unknown_liquidity:"Turnover below CNY20m or unavailable", inactive_or_unknown:"Zero or missing volume",
      price_basis_mismatch:"Quote and daily-bar prices disagree", no_index_outperformance:"No 20/60-session index outperformance",
      high_risk:"High technical risk", extended_price:"Extended above the moving average", weak_evidence:"Evidence below selection threshold",
      screen_unavailable:"Screener unavailable or unauthorized", quote_unavailable:"Quote unavailable", kline_unavailable:"Daily bars unavailable", index_unavailable:"Benchmark unavailable"
    });
    const enumText = {
      zh: {
        calendar_index: "指数交易日历",
        calendar_pool: "股票池交易日历",
        partial: "部分数据",
        complete: "完整",
        stale: "数据陈旧",
        insufficient: "数据不足",
        missing_quote: "缺报价",
        missing_kline: "缺K线",
        stale_quote: "报价陈旧",
        stale_kline: "K线陈旧",
        stale_index: "指数数据陈旧",
        missing_index: "缺指数数据",
        unavailable_factor_window: "因子窗口不可用",
        invalid_volume: "成交量无效",
        missing_volume: "缺少成交量",
        hold_observe: "持有观察",
        hard_stop_loss: "硬止损",
        take_profit: "止盈复核",
        max_loss_warning: "最大亏损预警",
        trend_break: "趋势破坏",
        volume_breakout: "放量突破",
        pullback_confirm: "回踩确认",
        momentum_weakness: "动能转弱",
        hold: "持有",
        exit_or_reduce: "退出/减仓",
        trim_or_review: "止盈/复核",
        review_risk: "复核风险",
        reduce_or_watch: "减仓/观察",
        breakout_watch: "突破观察",
        hold_or_plan_add: "持有/计划加仓",
        risk_review: "风险复核",
        position_review: "仓位复核",
        wait_confirm: "等待确认",
        avoid_watch: "暂缓观察",
        up: "上涨",
        range: "震荡",
        down: "下跌",
        uptrend: "上升趋势",
        downtrend: "下降趋势",
        high_volatility_pressure: "高波动压力",
        repair: "修复期",
        unknown: "状态不足",
        low: "低",
        medium: "中",
        high: "高",
        complete_market_data: "补齐行情",
        wait_for_structure: "等待结构",
        trend_observe: "趋势观察",
        center_range: "中枢震荡",
        suspected_third_buy: "疑似三买",
        upward_leave: "向上离开中枢",
        extended_above_center: "远离中枢上方",
        suspected_third_sell: "疑似三卖",
        downward_leave: "向下离开中枢",
        extended_below_center: "远离中枢下方",
        review_stop_loss: "复核止损",
        review_take_profit: "复核止盈",
        hold_and_monitor: "持有观察",
        review_buy_zone: "复核买入区间",
        watch_pool_candidate: "观察候选股",
        observe: "观察",
        check_mcp_tool_errors: "检查 MCP 工具错误",
        review_stop_loss_first: "优先复核止损",
        review_take_profit_plan: "复核止盈计划",
        review_pool_candidates: "复核股票池候选",
        watching: "观察中",
        holding: "已持仓",
        paused: "暂停观察",
        success: "成功",
        error: "失败",
        missing: "缺失",
        quote: "行情",
        kline: "K线",
        indicator: "指标"
      },
      en: {
        calendar_index: "Index calendar",
        calendar_pool: "Pool calendar",
        partial: "Partial data",
        complete: "Complete",
        stale: "Stale data",
        insufficient: "Insufficient data",
        missing_quote: "Missing quote",
        missing_kline: "Missing K-line",
        stale_quote: "Stale quote",
        stale_kline: "Stale K-line",
        stale_index: "Stale index data",
        missing_index: "Missing index data",
        unavailable_factor_window: "Factor window unavailable",
        invalid_volume: "Invalid volume",
        missing_volume: "Missing volume",
        hold_observe: "Hold and observe",
        hard_stop_loss: "Hard stop loss",
        take_profit: "Take-profit review",
        max_loss_warning: "Max loss warning",
        trend_break: "Trend break",
        volume_breakout: "Volume breakout",
        pullback_confirm: "Pullback confirmation",
        momentum_weakness: "Momentum weakness",
        hold: "Hold",
        exit_or_reduce: "Exit/reduce",
        trim_or_review: "Trim/review",
        review_risk: "Review risk",
        reduce_or_watch: "Reduce/watch",
        breakout_watch: "Breakout watch",
        hold_or_plan_add: "Hold/plan add",
        risk_review: "Risk review",
        position_review: "Position review",
        wait_confirm: "Wait for confirmation",
        avoid_watch: "Pause watch",
        up: "Up",
        range: "Range",
        down: "Down",
        uptrend: "Uptrend",
        downtrend: "Downtrend",
        high_volatility_pressure: "High-vol pressure",
        repair: "Repair",
        unknown: "Unknown",
        low: "Low",
        medium: "Medium",
        high: "High",
        complete_market_data: "Complete market data",
        wait_for_structure: "Wait for structure",
        trend_observe: "Trend observation",
        center_range: "Center range",
        suspected_third_buy: "Possible third buy",
        upward_leave: "Upward leave",
        extended_above_center: "Extended above center",
        suspected_third_sell: "Possible third sell",
        downward_leave: "Downward leave",
        extended_below_center: "Extended below center",
        review_stop_loss: "Review stop loss",
        review_take_profit: "Review take profit",
        hold_and_monitor: "Hold and monitor",
        review_buy_zone: "Review buy zone",
        watch_pool_candidate: "Watch candidate",
        observe: "Observe",
        check_mcp_tool_errors: "Check MCP tool errors",
        review_stop_loss_first: "Review stop loss first",
        review_take_profit_plan: "Review take-profit plan",
        review_pool_candidates: "Review pool candidates",
        watching: "Watching",
        holding: "Holding",
        paused: "Paused",
        success: "Success",
        error: "Failed",
        missing: "Missing",
        quote: "Quote",
        kline: "K-line",
        indicator: "Indicator"
      }
    };
    Object.assign(translations.zh, {
      structureClose:"结构收盘价", structureDate:"日线截至", centerBand:"参考中枢", chanCandidate:"结构观察",
      chanModelNote:"日线笔级近似模型 · 非严格买卖点 · 不含次级别确认及背驰验证",
      chanChartTitle:"日线 / 笔 / 中枢", stableStroke:"稳定笔", draftStroke:"末端延伸笔", centerLegend:"三笔重叠区",
      chanHealthy:"数据完整", chanReview:"数据待复核", chanCandidates:"笔级候选", chanObservation:"结构观察",
      chanEvidence:"判断依据", chanCondition:"后续确认条件", chanInvalidation:"失效 / 风险条件",
      centerDistance:"距中枢边界", centerAge:"中枢结束后日线数", stableStrokeCount:"稳定笔数",
      inputBarCount:"收到日线", excludedBarCount:"未纳入日线", dataIssues:"数据问题", generatedAt:"分析时间",
      analysisLegacy:"历史报告未保存完整图形或数据质量，请重新分析；不追溯修改历史结果。",
      chartUnavailable:"暂无可绘制的已收盘日线。", chanMethod:"模型口径与边界",
      chanMethodDetail:"仅使用已收盘日线；末端延伸笔不参与中枢与候选判断。中枢为三笔重叠近似，非递归走势中枢。超过10个自然日的数据标为待复核，未接入交易所假期日历。复权口径未统一验证，除权缺口需人工核对。",
      filterLabel:"筛选", sortLabel:"排序", insightAll:"全部", insightReview:"待复核 / 缺失", insightAbove:"中枢上方", insightBelow:"中枢下方", insightInside:"中枢内",
      insightUp:"上涨", insightDown:"下跌", insightDefault:"股票池顺序", insightChangeDesc:"涨幅从高到低", insightChangeAsc:"涨幅从低到高", insightAmountDesc:"成交额从高到低",
      poolQuoteBreadth:"本池报价涨跌", poolQuoteAverage:"本池平均涨跌", quotesCoverage:"有效报价覆盖", freshQuotes:"近期读取报价", quoteUnknown:"未知", quoteFlat:"平盘",
      quoteReadTime:"读取时间", exchangeTime:"行情时间", exchangeTimeUnknown:"行情时间未提供", exchangeTimeCaution:"读取时间不等于交易所行情时间；以下涨跌分布仅代表本股票池，非全市场。",
      quoteChange:"涨跌幅", quoteAmount:"成交额", quoteTurnover:"换手率", quotePrevious:"昨收", quoteOpen:"今开", quoteHigh:"最高", quoteLow:"最低", quoteState:"报价状态",
      quote_success:"已读取", quote_missing:"行情缺失", quote_stale:"行情或读取时间异常", quote_unverified:"时间待核实", stale_market_time:"行情日期超过10个自然日",
      provider_unavailable:"行情服务暂时不可用，请稍后重试", provider_permission:"行情服务权限被拒绝，请检查 Token 权限", provider_key_missing:"本地未配置行情 Token", provider_rate_limit:"行情请求被限流，请稍后重试", provider_error:"行情请求失败，请复核数据源",
      insufficient_bars:"有效日线少于35根", stale_structure:"稳定笔距今超过20根日线", stale_kline:"日线距今超过10个自然日",
      invalid_daily_data:"无效日线已排除", duplicate_dates:"存在重复日线", symbol_mismatch:"返回代码不符", missing_quote:"缺少有效报价",
      change_recomputed:"涨跌幅已按现价与昨收重算", invalid_change:"无效涨跌幅", stale_quote:"读取记录超过24小时", future_quote:"读取时间晚于系统时间", unknown_quote_time:"读取时间无法核实",
      chan_unformed:"结构未成型", chan_no_center:"尚未形成中枢", chan_center_formed:"中枢已形成", chan_above:"中枢上方", chan_below:"中枢下方", chan_inside:"中枢内", chan_extended_above:"远离中枢上方", chan_extended_below:"远离中枢下方"
    });
    Object.assign(translations.en, {
      structureClose:"Structure close", structureDate:"Daily bars through", centerBand:"Reference center", chanCandidate:"Structure observation",
      chanModelNote:"Daily pen-level approximation · Not confirmed buy/sell points · No sublevel or divergence validation",
      chanChartTitle:"Daily bars / strokes / centers", stableStroke:"Stable stroke", draftStroke:"Provisional stroke", centerLegend:"Three-stroke overlap",
      chanHealthy:"Complete data", chanReview:"Data review", chanCandidates:"Pen-level candidates", chanObservation:"Observation",
      chanEvidence:"Evidence", chanCondition:"Confirmation needed", chanInvalidation:"Invalidation / risk",
      centerDistance:"Distance from center edge", centerAge:"Bars since center ended", stableStrokeCount:"Stable strokes",
      inputBarCount:"Received daily bars", excludedBarCount:"Excluded daily bars", dataIssues:"Data issues", generatedAt:"Analyzed at",
      analysisLegacy:"Historical report: chart or quality data was not recorded. Run a new analysis; history stays unchanged.",
      chartUnavailable:"No completed daily bars to plot.", chanMethod:"Model scope and limits",
      chanMethodDetail:"Completed daily bars only. The provisional stroke is excluded from centers and candidates. Centers approximate three overlapping strokes, not recursive structures. Data older than 10 calendar days needs review; exchange holidays are not modeled. Adjustment conventions are unverified; corporate-action gaps need review.",
      filterLabel:"Filter", sortLabel:"Sort", insightAll:"All", insightReview:"Review / missing", insightAbove:"Above center", insightBelow:"Below center", insightInside:"Inside center",
      insightUp:"Rising", insightDown:"Falling", insightDefault:"Pool order", insightChangeDesc:"Change: high to low", insightChangeAsc:"Change: low to high", insightAmountDesc:"Amount: high to low",
      poolQuoteBreadth:"Pool quote breadth", poolQuoteAverage:"Pool mean change", quotesCoverage:"Valid quote coverage", freshQuotes:"Recently fetched quotes", quoteUnknown:"Unknown", quoteFlat:"Flat",
      quoteReadTime:"Fetched at", exchangeTime:"Exchange time", exchangeTimeUnknown:"Exchange time unavailable", exchangeTimeCaution:"Fetch time is not exchange time. Breadth covers this pool only, not the entire market.",
      quoteChange:"Change", quoteAmount:"Amount (CNY)", quoteTurnover:"Turnover", quotePrevious:"Previous close", quoteOpen:"Open", quoteHigh:"High", quoteLow:"Low", quoteState:"Quote status",
      quote_success:"Fetched", quote_missing:"Missing quote", quote_stale:"Timestamp stale / invalid", quote_unverified:"Time unverified", stale_market_time:"Exchange quote older than 10 calendar days",
      provider_unavailable:"Data service temporarily unavailable; try again later", provider_permission:"Data access denied; check token permissions", provider_key_missing:"Data token is not configured locally", provider_rate_limit:"Data requests rate-limited; try again later", provider_error:"Data request failed; review the source",
      insufficient_bars:"Fewer than 35 valid daily bars", stale_structure:"Stable stroke older than 20 bars", stale_kline:"Daily data older than 10 calendar days",
      invalid_daily_data:"Invalid daily bars excluded", duplicate_dates:"Duplicate daily dates", symbol_mismatch:"Returned symbol mismatch", missing_quote:"No valid price",
      change_recomputed:"Change recomputed from price and previous close", invalid_change:"Invalid change", stale_quote:"Fetch record older than 24 hours", future_quote:"Fetch timestamp is in the future", unknown_quote_time:"Fetch time unverified",
      chan_unformed:"Unformed", chan_no_center:"No center yet", chan_center_formed:"Center formed", chan_above:"Above center", chan_below:"Below center", chan_inside:"Inside center", chan_extended_above:"Extended above center", chan_extended_below:"Extended below center"
    });
    Object.assign(enumText.zh, {data_review:"数据待复核"});
    Object.assign(enumText.en, {data_review:"Data review"});
    let currentLanguage = localStorage.getItem("tdx_language") || "zh";
    let cachedHealth = null;
    document.getElementById("languageSelect").value = currentLanguage;
    let currentMarketSource = localStorage.getItem("tdx_market_source") || "tdx-official";
    document.getElementById("marketSourceSelect").value = currentMarketSource;

    async function api(path, options) {
      const response = await fetch(path, options);
      if (!response.ok) {
        const text = await response.text();
        try {
          const payload = JSON.parse(text);
          throw new Error(payload.detail || text);
        } catch (error) {
          if (error instanceof SyntaxError) throw new Error(text);
          throw error;
        }
      }
      return response.json();
    }
    function t(key) {
      return translations[currentLanguage][key] || key;
    }
    function enumLabel(value) {
      return enumText[currentLanguage][value] || value || "";
    }
    function setLanguage(language) {
      currentLanguage = language;
      localStorage.setItem("tdx_language", language);
      document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
      document.title = t("appTitle");
      document.querySelectorAll("[data-i18n]").forEach(node => {
        node.textContent = t(node.dataset.i18n);
      });
      document.querySelectorAll("[data-i18n-placeholder]").forEach(node => {
        node.placeholder = t(node.dataset.i18nPlaceholder);
      });
      rerenderCachedPanels();
      renderSourceStatus();
      if (cachedHealth) renderHealth();
    }
    function setMarketSource(source) {
      currentMarketSource = source;
      document.getElementById("marketSourceSelect").value = source;
      localStorage.setItem("tdx_market_source", source);
      invalidateAnalysis();
      viewReports.clear();
      currentRenderer = null;
      decisionDisplay = null;
      analysisStatus = {key: "analysisResultHint"};
      renderAnalysisStatus();
      ++holdingRenderSeq;
      renderHoldings(cachedHoldings);
      renderSourceStatus();
      const sequence = analysisSeq;
      refreshAll().catch(error => {
        if (sequence !== analysisSeq) return;
        document.getElementById("quoteStatus").textContent = error.message;
      });
    }
    let cachedReview = null;
    let followupSelection = null;
    let opportunityTimer = null;
    let cachedPools = [];
    let cachedWatchlist = [];
    let cachedHoldings = [];
    let analysisSeq = 0;
    let analysisController = null;
    let analysisStatus = {key: "analysisResultHint"};
    let holdingRenderSeq = 0;
    let autoNameValue = "";
    let nameEditedManually = false;
    let activeWorkspace = "stocks";
    let activeView = "decision";
    let selectedStock = "";
    let sidebarCollapsed = false;
    let currentRenderer = null;
    let decisionDisplay = null;
    let chanDisplay = null, overviewDisplay = null;
    let chanFilter = "all", overviewFilter = "all", overviewSort = "default";
    let decisionFilter = "all";
    const viewReports = new Map();
    const workspaceViews = {opportunities:["opportunities"], stocks:["decision", "chan", "quotes", "holdings", "watchlist"], history:["history", "review"]};
    const viewLabels = {opportunities:"navOpportunities", decision:"decisionView", chan:"chanView", quotes:"quotesView", holdings:"holdingsView", watchlist:"watchlistView", history:"opportunityHistory", review:"reviewView"};
    const lastViews = {opportunities:"opportunities", stocks:"decision", history:"history"};

    function rememberView() {
      if (cachedReview) viewReports.set(activeView, {report:cachedReview, renderer:currentRenderer || renderDailyReview});
    }
    function switchWorkspace(workspace) {
      switchView(lastViews[workspace], workspace);
    }
    function switchView(view, workspace = null) {
      const owner = workspace || Object.keys(workspaceViews).find(key => workspaceViews[key].includes(view));
      if (!owner || !workspaceViews[owner].includes(view)) return;
      if (view !== activeView) {
        rememberView();
        invalidateAnalysis();
        activeView = view;
        activeWorkspace = owner;
        lastViews[owner] = view;
        currentRenderer = null;
        decisionDisplay = null;
        decisionFilter = "all";
        analysisStatus = {key:"emptyAnalysis"};
        document.getElementById("actionStatus").textContent = "";
        const saved = viewReports.get(view);
        if (saved) { cachedReview = saved.report; currentRenderer = saved.renderer; }
      }
      renderWorkspace();
      if (cachedReview) renderCachedReview();
      else renderAnalysisStatus();
    }
    function renderWorkspace() {
      for (const key of Object.keys(workspaceViews)) document.getElementById(`nav-${key}`).setAttribute("aria-pressed", String(key === activeWorkspace));
      document.getElementById("view-title").textContent = t(viewLabels[activeView]);
      document.getElementById("view-tabs").innerHTML = workspaceViews[activeWorkspace].length > 1
        ? workspaceViews[activeWorkspace].map(view => `<button aria-pressed="${view === activeView}" onclick="switchView('${view}')">${escapeHtml(t(viewLabels[view]))}</button>`).join("") : "";
      const management = ["holdings", "watchlist"].includes(activeView);
      document.getElementById("analysis-panel").hidden = management;
      document.getElementById("holdings-panel").hidden = activeView !== "holdings";
      document.getElementById("watchlist-panel").hidden = activeView !== "watchlist";
      document.getElementById("update-analysis").textContent = t(management ? "refresh" : activeWorkspace === "history" ? "loadRecords" : "updateAnalysis");
      const toggle = document.getElementById("sidebar-toggle");
      toggle.title = toggle.ariaLabel = t(sidebarCollapsed ? "expandWatchlist" : "collapseWatchlist");
      const add = document.getElementById("add-watch-toggle");
      add.title = add.ariaLabel = t("addWatchSymbol");
    }
    function updateActiveView() {
      return ({opportunities:runOpportunities, decision:runDecisionEngine, chan:runChanAnalysis,
        quotes:analyzePool, holdings:refreshAll, watchlist:refreshAll, history:openOpportunityHistory, review:dailyReview})[activeView]();
    }
    function toggleSidebar() {
      sidebarCollapsed = !sidebarCollapsed;
      document.getElementById("workspace-layout").classList.toggle("sidebar-collapsed", sidebarCollapsed);
      document.getElementById("sidebar-toggle").textContent = sidebarCollapsed ? "›" : "‹";
      document.getElementById("sidebar-toggle").setAttribute("aria-expanded", String(!sidebarCollapsed));
      renderWorkspace();
    }
    function toggleAddWatch() {
      const form = document.getElementById("add-watch-form");
      form.hidden = !form.hidden;
      document.getElementById("add-watch-toggle").setAttribute("aria-expanded", String(!form.hidden));
      if (!form.hidden) document.getElementById("symbol").focus();
    }
    function renderSidebar() {
      const query = document.getElementById("watch-search").value.trim().toLowerCase();
      document.getElementById("watch-count").textContent = `${cachedWatchlist.length} ${t("stockCount")}`;
      document.getElementById("sidebar-stocks").innerHTML = cachedWatchlist.map((row, index) => ({row, index}))
        .filter(({row}) => `${row.symbol} ${row.name || ""}`.toLowerCase().includes(query))
        .map(({row, index}) => `<button class="sidebar-stock" aria-pressed="${row.symbol === selectedStock}" onclick="selectWatchStock(${index})"><span>${escapeHtml(row.name || row.symbol)}<small>${escapeHtml(row.symbol)}</small></span>${cachedHoldings.some(holding => opportunityIdentity(holding.symbol) === opportunityIdentity(row.symbol) && Number(holding.quantity) > 0) ? `<em>${enumLabel("holding")}</em>` : ""}</button>`).join("") || `<p class="status">${t("noData")}</p>`;
    }
    function selectWatchStock(index) {
      const stock = cachedWatchlist[index];
      if (!stock) return;
      selectedStock = stock.symbol;
      switchView("decision");
      renderSidebar();
      if (decisionDisplay) renderDecisionResults();
    }
    function clearStockSelection() {
      selectedStock = "";
      renderSidebar();
      if (decisionDisplay) renderDecisionResults();
    }

    async function checkHealth() {
      cachedHealth = await api("/health");
      renderHealth();
    }
    function renderHealth() {
      const health = cachedHealth;
      document.getElementById("health").textContent = health.mode ? `${t("running")} (${t("mode")}: ${health.mode})` : t("running");
    }
    async function addSymbolToPool() {
      const result = await ensureSymbolInPool();
      await refreshAll();
      if (result === "added") {
        document.getElementById("quoteStatus").textContent = `${t("watchSymbolAdded")}: ${currentSymbol()}`;
      } else if (result === "exists") {
        document.getElementById("quoteStatus").textContent = `${t("watchSymbolExists")}: ${currentSymbol()}`;
      }
    }
    async function ensureSymbolInPool() {
      const quote = await hydrateSymbolFromMarket(false);
      const symbol = currentSymbol();
      if (!symbol) return "missing";
      if (cachedWatchlist.some(row => normalizeSymbolText(row.symbol) === symbol)) return "exists";
      await api("/watchlist", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          pool_id: selectedPoolId(),
          symbol,
          name: document.getElementById("name").value || quote?.payload?.name || quote?.name || "",
          priority: 3
        })
      });
      return "added";
    }
    async function refreshAll() {
      await loadPools();
      cachedWatchlist = await api(`/watchlist?pool_id=${selectedPoolId() || ""}`);
      renderWatchlist(cachedWatchlist);
      cachedHoldings = await api("/holdings");
      await renderHoldings(cachedHoldings);
      renderSidebar();
    }
    async function loadPools() {
      cachedPools = await api("/stock-pools");
      const selected = cachedPools.find(pool => pool.is_default) || cachedPools[0];
      if (selected) {
        localStorage.setItem("tdx_pool_id", String(selected.id));
      } else {
        localStorage.removeItem("tdx_pool_id");
      }
    }
    function selectedPoolId() {
      const selected = cachedPools.find(pool => pool.is_default) || cachedPools[0];
      const value = selected ? selected.id : localStorage.getItem("tdx_pool_id");
      return value ? Number(value) : null;
    }
    function invalidateAnalysis() {
      if (opportunityTimer !== null) clearTimeout(opportunityTimer);
      ++analysisSeq;
      analysisController?.abort();
      analysisController = null;
      cachedReview = null;
    }
    function renderAnalysisStatus() {
      document.getElementById("review").innerHTML = `<p class="empty-analysis" role="status">${escapeHtml(t(analysisStatus.key))}${analysisStatus.message ? `: ${escapeHtml(analysisStatus.message)}` : ""}</p>`;
    }
    async function requestAnalysis(path, options, renderer, errorKey) {
      invalidateAnalysis();
      viewReports.delete(activeView);
      currentRenderer = renderer;
      const sequence = analysisSeq;
      const source = marketSource();
      const controller = new AbortController();
      analysisController = controller;
      document.getElementById("actionStatus").textContent = "";
      analysisStatus = {key: "checking"};
      renderAnalysisStatus();
      const isCurrent = () => sequence === analysisSeq && source === marketSource() && !controller.signal.aborted;
      try {
        const report = await api(path, {...options, signal: controller.signal});
        if (!isCurrent()) return;
        cachedReview = report;
        renderer(report);
      } catch (error) {
        if (!isCurrent()) return;
        cachedReview = null;
        analysisStatus = {key: errorKey, message: error.message};
        renderAnalysisStatus();
      } finally {
        if (sequence === analysisSeq) analysisController = null;
      }
    }
    async function runOpportunities() {
      switchView("opportunities");
      if (!["tdx-official", "mock"].includes(marketSource())) {
        document.getElementById("actionStatus").textContent = t("opportunityUnsupported");
        return;
      }
      if (!selectedPoolId()) return;
      return requestAnalysis(`/stock-pools/${selectedPoolId()}/opportunities`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({source:marketSource(), outside_limit:40})
      }, renderOpportunityJob, "opportunityFailed");
    }
    function renderOpportunityJob(run, retry = 0) {
      if (run.source !== marketSource()) return;
      cachedReview = {...run, report_type:"opportunity_job"};
      if (run.status === "completed") { renderOpportunities(run.result); return; }
      const terminal = {cancelled:"opportunityCancelled", interrupted:"opportunityInterrupted", failed:"opportunityFailed"};
      const p = run.progress || {};
      const active = ["queued", "running"].includes(run.status);
      document.getElementById("review").innerHTML = `<h3>${t("opportunityTitle")}</h3>
        <p role="status">${t(terminal[run.status] || (p.stage === "discovering" ? "opportunityDiscovering" : "opportunityAnalyzing"))} ${active ? `${p.completed || 0} / ${p.total || "-"}` : ""}</p>
        ${active ? `<progress class="opportunity-progress" max="${p.total || 1}" value="${p.completed || 0}"></progress><button class="secondary" onclick="cancelOpportunity('${run.id}')">${t("opportunityCancel")}</button>` : ""}`;
      if (!active) return;
      const sequence = analysisSeq, source = marketSource();
      if (opportunityTimer !== null) clearTimeout(opportunityTimer);
      opportunityTimer = setTimeout(async () => {
        if (sequence !== analysisSeq || source !== marketSource()) return;
        try {
          const next = await api(`/opportunities/${run.id}`);
          if (sequence === analysisSeq && source === marketSource()) {
            document.getElementById("actionStatus").textContent = "";
            renderOpportunityJob(next);
          }
        } catch (error) {
          if (sequence !== analysisSeq || source !== marketSource()) return;
          document.getElementById("actionStatus").textContent = t("opportunityReconnect");
          if (retry < 3) renderOpportunityJob(run, retry + 1);
          else document.getElementById("review").innerHTML += `<button class="secondary" onclick="openOpportunityRun('${run.id}')">${t("opportunityResume")}</button>`;
        }
      }, 1200 * (2 ** retry));
    }
    async function cancelOpportunity(id) {
      try { await api(`/opportunities/${id}`, {method:"DELETE"}); }
      catch (error) { document.getElementById("actionStatus").textContent = error.message; }
    }
    async function openOpportunityHistory() {
      switchView("history");
      if (!selectedPoolId()) return;
      return requestAnalysis(`/stock-pools/${selectedPoolId()}/opportunities?source=${encodeURIComponent(marketSource())}`, {}, renderOpportunityHistory, "opportunityFailed");
    }
    function renderOpportunityHistory(rows) {
      cachedReview = {report_type:"opportunity_history", rows};
      document.getElementById("review").innerHTML = `<h3>${t("opportunityHistory")}</h3>${rows.length ? rows.map(row => `<div class="tracking-history"><button class="secondary" onclick="openOpportunityRun('${row.id}')">${escapeHtml(fullTime(row.created_at))}</button> ${escapeHtml(t(row.status))}${row.status === "completed" ? `<button class="secondary" onclick="openOpportunityFollowup('${row.id}')">${t("followupOpen")}</button>` : ""}</div>`).join("") : `<p>${t("noData")}</p>`}`;
    }
    function openOpportunityRun(id) {
      return requestAnalysis(`/opportunities/${id}`, {}, renderOpportunityJob, "opportunityFailed");
    }
    function opportunityLabel(value) {
      const keys = {new:"opportunityNew", watched:"opportunityWatched", held:"opportunityHeld", priority:"opportunityPriority", wait:"opportunityWait", not_selected:"opportunityNotSelected", excluded:"opportunityInvalid"};
      return t(keys[value] || value) !== value ? t(keys[value] || value) : enumLabel(value);
    }
    function opportunityIdentity(symbol) {
      const text = normalizeSymbolText(symbol).replace(/^1[.]/, "SH").replace(/^0[.]/, "SZ").replace(/^2[.]/, "BJ");
      if (/^SH(?:60|68)[0-9]{4}$/.test(text) || /^SZ(?:00|30)[0-9]{4}$/.test(text)) return text.slice(2);
      if (/^(?:[48][0-9]{5}|92[0-9]{4})$/.test(text)) return `BJ${text}`;
      return text;
    }
    function renderOpportunities(report) {
      const scope = report.scope || {}, d = report.discovery || {};
      const filters = cachedReview?.filters || {origin:"all", view:"top", horizon:"baseline"};
      document.getElementById("review").innerHTML = `<h3>${t("opportunityTitle")}</h3>
        <p class="status">${escapeHtml(report.source)} · ${escapeHtml(shortTime(report.generated_at))} · ${escapeHtml(report.benchmark)} ${d.is_demo ? ` · ${t("opportunityDemo")}` : ""}</p>
        <div class="opportunity-summary">${[[scope.new,"opportunityCandidates"],[scope.personal,"opportunityPersonal"],[scope.recommended,"opportunitySelected"],[scope.excluded,"opportunityExcluded"]].map(([n,key]) => `<div><strong>${n ?? 0}</strong><span>${t(key)}</span></div>`).join("")}</div>
        <p class="status">${t("opportunityTechnical")}</p>
        ${cachedReview?.id ? `<p><button class="secondary" onclick="openOpportunityFollowup('${cachedReview.id}')">${t("followupOpen")}</button></p>` : ""}
        ${d.errors?.length || report.failures?.length ? `<p role="status">${t("opportunityPartial")}</p>` : ""}
        <div class="toolbar"><select id="opportunity-origin" aria-label="${t("opportunityOrigin")}" onchange="renderOpportunityRows()"><option value="all">${t("opportunityAny")}</option>${["new","watched","held"].map(v=>`<option value="${v}">${opportunityLabel(v)}</option>`).join("")}</select>
          <select id="opportunity-view" aria-label="${t("opportunityAll")}" onchange="renderOpportunityRows()"><option value="top">${t("opportunityTop")}</option><option value="all">${t("opportunityAll")} (${scope.analyzed || 0})</option></select>
          <select id="opportunity-horizon" aria-label="${t("periodLabel")}" onchange="renderOpportunityRows()"><option value="baseline">${t("periodBaseline")}</option>${["5","20","60","120","long_term"].map(key=>`<option value="${key}">${t(`period${key}`)}</option>`).join("")}</select></div>
        <p class="tracking-meta">${t("periodNote")}</p>
        <div id="opportunity-rows"></div>
        <details class="stock-detail"><summary>${t("opportunityCoverage")}</summary>
          <p>${t("opportunityScope")} · ${d.candidate_count || 0} / ${scope.analyzed || 0}</p>
          ${(d.queries || []).map(q=>`<p>${escapeHtml(q.query)}<br>${currentLanguage === "zh" ? "读取 / 返回总数" : "Read / reported total"}: ${q.rows_read} / ${q.total}${q.truncated ? (currentLanguage === "zh" ? " · 部分读取" : " · partial") : ""}</p>`).join("")}
          ${(d.errors || []).map(e=>`<p>${escapeHtml(e.theme)}: ${opportunityLabel(e.reason)}</p>`).join("")}
          ${(report.failures || []).map(e=>`<p>${escapeHtml(e.symbol)}: ${opportunityLabel(e.kind)}</p>`).join("")}
          <p>${t("opportunityRefresh")}</p></details>`;
      document.getElementById("opportunity-origin").value = filters.origin;
      document.getElementById("opportunity-view").value = filters.view;
      document.getElementById("opportunity-horizon").value = filters.horizon;
      renderOpportunityRows(report);
    }
    function renderOpportunityRows(provided) {
      const report = provided || cachedReview?.result;
      if (!report) return;
      const origin = document.getElementById("opportunity-origin").value || "all";
      const all = document.getElementById("opportunity-view").value === "all";
      const horizon = document.getElementById("opportunity-horizon").value || "baseline";
      if (cachedReview) cachedReview.filters = {origin, view:all ? "all" : "top", horizon};
      let rows = (report.items || []).filter(item => origin === "all" || item.origin === origin);
      if (!all) {
        rows = horizon === "baseline" ? rows.filter(item => (report.selected || []).includes(item.symbol))
          : rows.filter(item => ["favorable","wait"].includes(item.period_assessments?.[horizon]?.stance))
            .sort((a,b)=>(b.period_assessments[horizon].score || 0)-(a.period_assessments[horizon].score || 0) || a.symbol.localeCompare(b.symbol)).slice(0,10);
      }
      document.getElementById("opportunity-rows").innerHTML = rows.length ? rows.map(item => {
        const reasons = (item.selection_reasons || []).map(opportunityLabel);
        const opposition = (item.opposing_evidence || []).slice(0,2).map(e => `${e.source}: ${e.observation}`);
        const support = (item.supporting_evidence || []).slice(0,3).map(e => `${e.source}: ${e.observation}`);
        const c = item.conditions || {}, p = item.probabilities || {};
        const h = item.period_assessments?.[horizon];
        const grade = horizon === "baseline" ? `${t("periodBaseline")} · ${opportunityLabel(item.level)} · ${t("opportunityScore")} ${item.rank_score}`
          : `${t(`period${horizon}`)} · ${t(`stance_${h?.stance || "legacy"}`)}${h?.score == null ? "" : ` · ${h.score} / 100`}`;
        const added = cachedWatchlist.some(row => opportunityIdentity(row.symbol) === opportunityIdentity(item.symbol));
        return `<article class="opportunity-row" data-level="${escapeHtml(item.level)}">
          <div class="opportunity-head"><h3>${escapeHtml(item.name || item.symbol)} <small>${escapeHtml(item.symbol)} · ${opportunityLabel(item.origin)}</small></h3>
            <span class="opportunity-grade">${escapeHtml(grade)}</span>
            <span>${formatPrice(item.current_price)} <small>${t("opportunityAsOf")} ${escapeHtml(item.data_quality?.kline_as_of || "-")}</small></span></div>
          ${horizon !== "baseline" ? horizonEvidence(h) : `<div class="opportunity-columns"><div><h4>${t("opportunityBasis")}</h4>${support.map(s=>`<p>${escapeHtml(s)}</p>`).join("") || `<p>${t("weak_evidence")}</p>`}</div>
            <div><h4>${t("opportunityRisk")}</h4><p>${t("risk_level")}: ${escapeHtml(enumLabel(item.decision?.risk_level))} · ${t("confidence")}: ${escapeHtml(enumLabel(item.decision?.confidence))}</p>${[...reasons,...opposition].map(s=>`<p>${escapeHtml(s)}</p>`).join("") || `<p>${t("opportunityNoOpposition")}</p>`}</div>
            <div><h4>${t("opportunityConditions")}</h4><p>MA20 ${formatPrice(c.ma20)} · ATR14 ${formatPrice(c.atr14)}</p>
              ${item.level === "excluded" ? `<p>${t("opportunityInvalid")}</p>` : `<p>${t("opportunityConfirm")}</p><p>${t("opportunityInvalidation")}: ${formatPrice(c.review_below)}</p>`}
              <div class="opportunity-score" title="${escapeHtml(scoreVector(p))}">${[[p.up,"#b34848"],[p.range,"#b09236"],[p.down,"#328172"]].map(([v,color])=>`<i style="width:${Math.max(0, Math.min(100, (v || 0)*100))}%;background:${color}"></i>`).join("")}</div><p>${escapeHtml(scoreVector(p))}</p></div></div>`}
          ${horizonDetails(item)}
          ${decisionDetails(item)}
          ${item.origin === "new" ? `<button class="secondary" ${added ? "disabled" : ""} onclick="addOpportunity('${escapeHtml(item.symbol)}',this)">${t(added ? "opportunityAdded" : "opportunityAdd")}</button>` : ""}
        </article>`;
      }).join("") : `<p class="status">${t("opportunityEmpty")}</p>`;
    }
    function horizonEvidence(h) {
      if (!h) return `<p class="tracking-meta">${t("periodLegacy")}</p>`;
      const c = h.conditions, m = h.metrics || {};
      return `<div class="opportunity-columns"><div><h4>${t("periodEvidence")}</h4>${(h.evidence || []).map(e=>`<p>${escapeHtml(t(e.value))}</p>`).join("")}</div>
        <div><h4>${t("opportunityRisk")}</h4>${(h.issues || []).map(issue=>`<p>${escapeHtml(t(issue))}</p>`).join("") || `<p>${t("opportunityNoOpposition")}</p>`}
          <p>${t("periodExcess")}: ${m.excess_pp == null ? "-" : `${formatMoney(m.excess_pp)} pp`}</p></div>
        <div><h4>${t("opportunityConditions")}</h4>${c ? `<p>MA${escapeHtml(c.ma_window)}: ${formatPrice(c.ma_price)} · ${t("periodReview")}: ${formatPrice(c.review_below)}</p><p>${t("periodConfirm")}</p>` : `<p>${t("stance_insufficient")}</p>`}</div></div>`;
    }
    function horizonDetails(item) {
      if (!item.period_assessments) return `<p class="tracking-meta">${t("periodLegacy")}</p>`;
      return `<div class="horizon-list">${["5","20","60","120","long_term"].map(key => {
        const h = item.period_assessments[key];
        if (!h) return "";
        const c = h.conditions, m = h.metrics || {};
        return `<details class="horizon-item" data-stance="${escapeHtml(h.stance)}"><summary>${t(`period${key}`)}<strong>${escapeHtml(t(`stance_${h.stance}`))}</strong><span>${h.score === null || h.score === undefined ? "-" : `${escapeHtml(h.score)} / 100`}</span></summary>
          <p>${t("opportunityAsOf")}: ${escapeHtml(h.as_of || "-")}${h.market_regime ? `<br>${t("marketRegime")}: ${escapeHtml(enumLabel(h.market_regime))}` : ""}</p>
          ${(h.evidence || []).map(e=>`<p>${escapeHtml(t(e.value))} (${e.points > 0 ? "+" : ""}${escapeHtml(e.points)})</p>`).join("")}
          ${(h.issues || []).map(issue=>`<p>${escapeHtml(t(issue))}</p>`).join("")}
          ${c ? `<p>${t("periodReturn")}: ${formatPercent(m.return_pct) || "-"}<br>${t("periodExcess")}: ${formatMoney(m.excess_pp) || "-"} pp<br>${t("periodVolume")}: ${formatPrice(m.volume_ratio)}</p>
            <p>MA${escapeHtml(c.ma_window)}: ${formatPrice(c.ma_price)}<br>${t("periodReview")}: ${formatPrice(c.review_below)}</p><p>${t("periodConfirm")}</p>` : ""}
        </details>`;
      }).join("")}</div>`;
    }
    function fullTime(value) {
      if (!value) return "-";
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? value : date.toLocaleString(currentLanguage === "zh" ? "zh-CN" : "en-US", {timeZone:"Asia/Shanghai",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"});
    }
    function openOpportunityFollowup(id) {
      switchView("history");
      return requestOpportunityFollowup(id, {});
    }
    function refreshOpportunityFollowup(id) {
      return requestOpportunityFollowup(id, {method:"POST"});
    }
    function requestOpportunityFollowup(id, options) {
      return requestAnalysis(`/opportunities/${encodeURIComponent(id)}/followup`, options, renderOpportunityFollowup, "followupFailed");
    }
    async function cancelOpportunityFollowup(id) {
      try { await api(`/opportunities/${encodeURIComponent(id)}/followup`, {method:"DELETE"}); }
      catch (error) { document.getElementById("actionStatus").textContent = error.message; }
    }
    function renderOpportunityFollowup(run, retry = 0) {
      if (run.source !== marketSource()) return;
      const horizon = (followupSelection?.runId === run.run_id && followupSelection?.source === run.source ? followupSelection.horizon : null) || run.followupHorizon || "20";
      cachedReview = {...run, report_type:"opportunity_followup", followupHorizon:horizon};
      followupSelection = {runId:run.run_id, source:run.source, horizon};
      const report = run.result, active = ["running","queued"].includes(run.status), p = run.progress || {};
      document.getElementById("review").innerHTML = `<h3>${t("followupTitle")}${report?.is_demo ? ` · ${t("opportunityDemo")}` : ""}</h3>
        <div class="toolbar"><button class="secondary" onclick="openOpportunityRun('${run.run_id}')">${t("followupOriginal")}</button>
        ${active ? `<button class="secondary" onclick="cancelOpportunityFollowup('${run.run_id}')">${t("followupCancel")}</button>` : `<button onclick="refreshOpportunityFollowup('${run.run_id}')">${t("followupRefresh")}</button>`}</div>
        <p class="tracking-meta">${escapeHtml(run.source)} · ${t("followupSnapshot")}: ${escapeHtml(fullTime(run.generated_at || report?.generated_at))}</p>
        ${active ? `<p role="status">${t("running")} ${p.completed || 0} / ${p.total || 0}</p><progress class="opportunity-progress" max="${p.total || 1}" value="${p.completed || 0}"></progress>` : run.status !== "completed" ? `<p role="status">${t(run.status === "not_started" ? "followupNotStarted" : run.status === "failed" ? "followupFailed" : run.status)}</p>` : ""}
        ${report && run.status !== "completed" ? `<p id="followup-retained" class="data-alert" role="status">${t("followupRetained")}</p>` : ""}
        ${report ? `<p class="tracking-meta">${t("followupAsOf")}: ${escapeHtml(report.benchmark_as_of || "-")} · ${t("followupUpdated")}: ${escapeHtml(fullTime(report.evaluated_at))}</p>
          <label for="followup-horizon">${t("followupWindow")}</label><div class="toolbar"><select id="followup-horizon" onchange="renderFollowupResults()">${["5","20","60","120"].map(key=>`<option value="${key}" ${key === "20" ? "selected" : ""}>${t(`period${key}`)}</option>`).join("")}</select></div>
          <div id="followup-results"></div>` : ""}
        <p class="tracking-meta">${t("followupMethod")}</p><p class="tracking-meta">${t("followupCaution")}</p>`;
      if (report) {
        document.getElementById("followup-horizon").value = horizon;
        renderFollowupResults();
      }
      if (!active) return;
      const sequence = analysisSeq, source = marketSource();
      if (opportunityTimer !== null) clearTimeout(opportunityTimer);
      opportunityTimer = setTimeout(async () => {
        if (sequence !== analysisSeq || source !== marketSource()) return;
        try {
          const next = await api(`/opportunities/${encodeURIComponent(run.run_id)}/followup`);
          if (sequence === analysisSeq && source === marketSource()) {
            document.getElementById("actionStatus").textContent = "";
            renderOpportunityFollowup(next);
          }
        } catch (error) {
          if (sequence !== analysisSeq || source !== marketSource()) return;
          document.getElementById("actionStatus").textContent = t("opportunityReconnect");
          if (retry < 3) renderOpportunityFollowup(run, retry+1);
          else document.getElementById("review").innerHTML += `<button class="secondary" onclick="openOpportunityFollowup('${run.run_id}')">${t("opportunityResume")}</button>`;
        }
      }, 1500 * (2 ** retry));
    }
    function followupGroup(group) {
      return t({selected:"followupSelected",not_selected:"followupNotSelected",excluded:"followupExcluded"}[group] || `stance_${group}`);
    }
    function followupSummaryTable(stats) {
      return `<div class="table-scroll"><table class="tracking-table"><thead><tr>${["followupGroup","followupMatured","followupPending","followupUnavailable","followupMeanReturn","followupMeanExcess","followupPositive","followupWorstDrawdown"].map(key=>`<th>${t(key)}</th>`).join("")}</tr></thead><tbody>
        ${Object.entries(stats || {}).map(([group,s])=>`<tr><td>${escapeHtml(followupGroup(group))}</td><td>${s.matured} / ${s.total}</td><td>${s.pending}</td><td>${s.unavailable}</td><td>${formatPercent(s.mean_return_pct) || "-"}</td><td>${s.mean_excess_pp == null ? "-" : `${formatMoney(s.mean_excess_pp)} pp`}</td><td>${formatProbability(s.positive_fraction) || "-"}</td><td>${formatPercent(s.worst_drawdown_pct) || "-"}</td></tr>`).join("")}</tbody></table></div>`;
    }
    function renderFollowupResults() {
      const report = cachedReview?.result;
      if (!report) return;
      const horizon = document.getElementById("followup-horizon").value || "20";
      cachedReview.followupHorizon = horizon;
      followupSelection = {runId:cachedReview.run_id, source:cachedReview.source, horizon};
      document.getElementById("followup-results").innerHTML = `
        ${(report.issues || []).map(issue=>`<p role="status">${escapeHtml(t(issue))}</p>`).join("")}
        ${report.failures?.length ? `<details class="stock-detail"><summary>${t("opportunityErrors")} (${report.failures.length})</summary>${report.failures.map(f=>`<p>${escapeHtml(f.symbol)}: ${escapeHtml(t(f.kind))}</p>`).join("")}</details>` : ""}
        <h4>${t("followupBaseGroups")}</h4>${followupSummaryTable(report.summary?.[horizon])}
        <details class="stock-detail"><summary>${t("followupPeriodGroups")}</summary>${followupSummaryTable(report.period_summary?.[horizon])}</details>
        <h4>${t("followupDetails")}</h4><div class="table-scroll"><table class="tracking-table"><thead><tr>${["symbol","followupGroup","periodEvidence","followupState","followupStockReturn","followupIndexReturn","followupExcess","followupDrawdown","followupDates"].map(key=>`<th>${t(key)}</th>`).join("")}</tr></thead><tbody>
        ${(report.items || []).map(item=>{
          const o = item.outcomes?.[horizon] || {status:"unavailable"};
          const h = item.period_assessments?.[horizon];
          return `<tr><td class="tracking-identity">${escapeHtml(item.name || item.symbol)}<small>${escapeHtml(item.symbol)}</small></td>
            <td>${escapeHtml(followupGroup(item.group))}</td><td>${escapeHtml(t(`stance_${h?.stance || "legacy"}`))}</td>
            <td>${escapeHtml(t(`followup_${o.status}`))}${(o.issues || []).map(issue=>`<small>${escapeHtml(t(issue))}</small>`).join("")}</td>
            <td>${formatPercent(o.return_pct) || "-"}</td><td>${formatPercent(o.benchmark_return_pct) || "-"}</td><td>${formatMoney(o.excess_pp) || "-"}</td><td>${formatPercent(o.max_drawdown_pct) || "-"}</td>
            <td>${escapeHtml(o.start_date || "-")} ~ ${escapeHtml(o.end_date || "-")}<small>${t("followupReference")}: ${formatPrice(o.reference_open)} / ${formatPrice(o.end_close)}</small></td></tr>`;
        }).join("")}</tbody></table></div>`;
    }
    async function addOpportunity(symbol, button) {
      const item = cachedReview?.result?.items?.find(row => row.symbol === symbol);
      if (!item) return;
      const poolId = selectedPoolId();
      button.disabled = true;
      try {
        const current = await api(`/watchlist?pool_id=${poolId}`);
        if (current.some(row => opportunityIdentity(row.symbol) === opportunityIdentity(symbol))) {
          cachedWatchlist = current;
          button.textContent = t("opportunityAdded");
          return;
        }
        await api("/watchlist", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({pool_id:poolId,symbol:item.symbol,name:item.name,priority:3})});
        await refreshAll();
        button.textContent = t("opportunityAdded");
      } catch (error) { button.disabled = false; document.getElementById("actionStatus").textContent = error.message; }
    }
    async function runDecisionEngine() {
      switchView("decision");
      const poolId = selectedPoolId();
      if (!poolId) return;
      return requestAnalysis(`/stock-pools/${poolId}/decision-engine`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            source: marketSource(),
            period: "daily",
            persist: true,
            max_symbols: 30,
            kline_limit: 240,
            horizon_days: 20,
            market_index_symbol: "SH000300"
          })
        }, renderDecisionEngine, "decisionEngineFailed");
    }
    async function analyzePool() {
      switchView("quotes");
      const poolId = selectedPoolId();
      if (!poolId) return;
      return requestAnalysis(`/stock-pools/${poolId}/market-analysis`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({source: marketSource(), persist: true, max_symbols: 30})
        }, renderPoolAnalysis, "poolAnalysisFailed");
    }
    async function runChanAnalysis() {
      switchView("chan");
      const poolId = selectedPoolId();
      if (!poolId) return;
      return requestAnalysis(`/stock-pools/${poolId}/chan-analysis`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            source: marketSource(),
            period: "daily",
            persist: true,
            max_symbols: 30,
            kline_limit: 240
          })
        }, renderChanAnalysis, "chanAnalysisFailed");
    }
    async function dailyReview() {
      switchView("review");
      return requestAnalysis(`/reports/daily-review?pool_id=${selectedPoolId() || ""}&source=${encodeURIComponent(marketSource())}`,
        {}, renderDailyReview, "dailyReviewFailed");
    }
    async function renderHoldings(rows) {
      const renderSeq = ++holdingRenderSeq;
      const latestRows = latestBySymbol(filterByPoolSymbols(rows));
      document.getElementById("holdingsHint").textContent = t("poolHoldingsHint");
      if (!latestRows.length) {
        document.getElementById("holdings").innerHTML = table([], ["symbol"]);
        return;
      }
      document.getElementById("holdings").innerHTML = `<p class="status">${t("checking")}</p>`;
      const enrichedRows = await Promise.all(latestRows.map(enrichHoldingWithQuote));
      if (renderSeq !== holdingRenderSeq) return;
      document.getElementById("holdings").innerHTML = holdingsTable(enrichedRows);
    }
    async function enrichHoldingWithQuote(row) {
      const quantity = Number(row.quantity || 0);
      const costPrice = Number(row.cost_price || 0);
      try {
        const quote = await api(`/market/quote/${encodeURIComponent(row.symbol)}?source=${encodeURIComponent(marketSource())}`);
        const currentPrice = positivePrice(quote.price);
        const valued = currentPrice !== null && Number.isFinite(quantity) && quantity > 0;
        const marketValue = valued ? quantity * currentPrice : null;
        const estimatedPnl = valued ? quantity * (currentPrice - costPrice) : null;
        const estimatedPnlPct = valued && costPrice > 0 ? ((currentPrice - costPrice) / costPrice) * 100 : null;
        return {
          ...row,
          current_price: currentPrice,
          market_value: marketValue,
          estimated_pnl: estimatedPnl,
          estimated_pnl_pct: estimatedPnlPct
        };
      } catch (error) {
        return {
          ...row,
          current_price: null,
          market_value: null,
          estimated_pnl: null,
          estimated_pnl_pct: null,
          quote_error: error.message
        };
      }
    }
    function holdingsTable(rows) {
      if (!rows.length) return `<p class="status">${t("noData")}</p>`;
      const fields = ["symbol", "name", "quantity", "cost_price", "current_price", "market_value", "estimated_pnl", "estimated_pnl_pct", "save"];
      const head = fields.map(field => `<th>${escapeHtml(t(field))}</th>`).join("");
      const body = rows.map(row => `
        <tr>
          <td class="symbol-cell">${escapeHtml(row.symbol)}</td>
          <td class="name-cell">${escapeHtml(row.name || "")}</td>
          <td class="number-cell"><input class="quantity-input" id="holding-qty-${Number(row.id)}" type="number" min="0" step="1" value="${escapeHtml(row.quantity ?? 0)}"></td>
          <td class="number-cell"><input class="price-input" id="holding-cost-${Number(row.id)}" type="number" min="0.001" step="0.001" value="${escapeHtml(formatOptionalPrice(row.cost_price))}"></td>
          <td class="number-cell">${escapeHtml(formatOptionalPrice(row.current_price) || t("quoteMissing"))}</td>
          <td class="number-cell">${escapeHtml(formatMoney(row.market_value))}</td>
          <td class="number-cell ${pnlClass(row.estimated_pnl)}">${escapeHtml(formatMoney(row.estimated_pnl))}</td>
          <td class="number-cell ${pnlClass(row.estimated_pnl)}">${escapeHtml(formatPercent(row.estimated_pnl_pct))}</td>
          <td class="action-cell"><button class="secondary table-button" onclick="saveHoldingEdit(${Number(row.id)})">${t("save")}</button></td>
        </tr>
      `).join("");
      return `${holdingsSummary(rows)}<div class="table-scroll"><table class="holdings-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }
    function holdingsSummary(rows) {
      const summary = summarizeHoldings(rows);
      const partial = summary.unpricedCount > 0;
      return `
        <p class="status">${!summary.pricedCount ? t("noValuation") : partial ? t("partialValuation") : t("holdings")}
          · ${t("pricedHoldings")}: ${summary.pricedCount} · ${t("unpricedHoldings")}: ${summary.unpricedCount}
          · ${t("valuationCoverage")}: ${formatProbability(summary.coverage) || "-"}
          · ${t("pricedCost")}: ${formatMoney(summary.pricedCost)}</p>
        <div class="holdings-summary">
          ${summaryStat("total_cost_basis", formatMoney(summary.totalCost))}
          ${summaryStat(partial ? "pricedMarketValue" : "total_market_value", formatMoney(summary.totalMarketValue))}
          ${summaryStat(partial ? "pricedPnl" : "total_estimated_pnl", formatMoney(summary.totalPnl), pnlClass(summary.totalPnl))}
          ${summaryStat(partial ? "pricedPnlPct" : "total_estimated_pnl_pct", formatPercent(summary.totalPnlPct), pnlClass(summary.totalPnl))}
        </div>
      `;
    }
    function summaryStat(labelKey, value, className = "") {
      return `<div class="summary-stat"><b>${t(labelKey)}</b><span class="${className}">${escapeHtml(value || "-")}</span></div>`;
    }
    function summarizeHoldings(rows) {
      const summary = rows.reduce((summary, row) => {
        const quantity = Number(row.quantity || 0);
        const costPrice = Number(row.cost_price);
        const currentPrice = positivePrice(row.current_price);
        if (!Number.isFinite(quantity) || quantity <= 0) return summary;
        if (Number.isFinite(costPrice)) {
          summary.totalCost += quantity * costPrice;
        }
        if (Number.isFinite(costPrice) && currentPrice !== null) {
          const costBasis = quantity * costPrice;
          const marketValue = quantity * currentPrice;
          summary.pricedCost += costBasis;
          summary.totalMarketValue += marketValue;
          summary.totalPnl += marketValue - costBasis;
          summary.pricedCount += 1;
        } else {
          summary.unpricedCount += 1;
        }
        return summary;
      }, {totalCost: 0, pricedCost: 0, pricedCount: 0, unpricedCount: 0, coverage: null, totalMarketValue: 0, totalPnl: 0, totalPnlPct: null});
      const count = summary.pricedCount + summary.unpricedCount;
      summary.coverage = count ? summary.pricedCount / count : null;
      if (!summary.pricedCount) {
        summary.totalMarketValue = null;
        summary.totalPnl = null;
        return summary;
      }
      summary.totalPnlPct = summary.pricedCost > 0 ? (summary.totalPnl / summary.pricedCost) * 100 : null;
      return summary;
    }
    function positivePrice(value) {
      if (typeof value !== "number" && typeof value !== "string") return null;
      if (typeof value === "string" && !value.trim()) return null;
      const number = Number(value);
      return Number.isFinite(number) && number > 0 ? number : null;
    }
    async function saveHoldingEdit(holdingId) {
      const quantityInput = document.getElementById(`holding-qty-${holdingId}`);
      const costInput = document.getElementById(`holding-cost-${holdingId}`);
      const quantity = Number(quantityInput?.value);
      const costPrice = Number(costInput?.value);
      if (!Number.isFinite(quantity) || quantity < 0) return;
      if (!Number.isFinite(costPrice) || costPrice <= 0) return;
      const updated = await api(`/holdings/${holdingId}`, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({quantity, cost_price: costPrice})
      });
      cachedHoldings = cachedHoldings.map(row => Number(row.id) === Number(holdingId) ? updated : row);
      document.getElementById("actionStatus").textContent = `${t("holdingUpdated")}: ${updated.symbol}`;
      await renderHoldings(cachedHoldings);
    }
    function renderWatchlist(rows) {
      renderSidebar();
      document.getElementById("poolHint").textContent = t("poolHint");
      const mapped = rows.map(row => ({
        ...row,
        priority: priorityLabel(row.priority),
        status: enumLabel(row.status)
      }));
      document.getElementById("watchlist").innerHTML = watchlistTable(mapped);
    }
    function watchlistTable(rows) {
      if (!rows.length) return `<p class="status">${t("noData")}</p>`;
      const fields = ["symbol", "name", "priority", "status", "action"];
      const head = fields.map(field => `<th>${escapeHtml(t(field))}</th>`).join("");
      const body = rows.map(row => `
        <tr>
          <td>${escapeHtml(row.symbol)}</td>
          <td>${escapeHtml(row.name || "")}</td>
          <td>${escapeHtml(row.priority || "")}</td>
          <td>${escapeHtml(row.status || "")}</td>
          <td><button class="secondary table-button" onclick="addHoldingFromWatchlist('${escapeHtml(row.symbol)}')">${t("addHoldingFromPool")}</button></td>
        </tr>
      `).join("");
      return `<div class="table-scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }
    async function addHoldingFromWatchlist(symbol) {
      const normalized = normalizeSymbolText(symbol);
      if (!normalized) return;
      const existing = latestBySymbol(filterByPoolSymbols(cachedHoldings))
        .find(row => normalizeSymbolText(row.symbol) === normalized);
      if (existing) {
        document.getElementById("actionStatus").textContent = `${t("holdingAlreadyExists")}: ${normalized}`;
        return;
      }
      const item = cachedWatchlist.find(row => normalizeSymbolText(row.symbol) === normalized) || {};
      try {
        const quote = await api(`/market/quote/${encodeURIComponent(normalized)}?source=${encodeURIComponent(marketSource())}`);
        const created = await api("/holdings", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            symbol: normalized,
            name: quote.name || item.name || "",
            market: item.market || "A",
            quantity: 0,
            cost_price: Number(quote.price),
            initial_thesis: item.thesis || ""
          })
        });
        cachedHoldings = [created, ...cachedHoldings];
        document.getElementById("actionStatus").textContent = `${t("holdingAdded")}: ${created.symbol}`;
        await renderHoldings(cachedHoldings);
      } catch (error) {
        document.getElementById("actionStatus").textContent = `${t("addHoldingFailed")}: ${error.message}`;
      }
    }
    function priorityLabel(value) {
      const priority = Number(value);
      if (!Number.isFinite(priority)) return "";
      if (currentLanguage === "zh") {
        if (priority <= 1) return "最高";
        if (priority === 2) return "高";
        if (priority === 3) return "普通";
        if (priority === 4) return "低";
        return "仅观察";
      }
      if (priority <= 1) return "Highest";
      if (priority === 2) return "High";
      if (priority === 3) return "Normal";
      if (priority === 4) return "Low";
      return "Watch only";
    }
    function onSymbolChanged() {
      syncAutoName();
    }
    function onNameChanged() {
      nameEditedManually = true;
    }
    function marketSource() {
      return document.getElementById("marketSourceSelect").value || "tongdaxin";
    }
    async function hydrateSymbolFromMarket(forceMessage) {
      let symbol = currentSymbol();
      const query = lookupText();
      if (!query) return null;
      if (!symbol) {
        try {
          const matches = await api(`/market/search?query=${encodeURIComponent(query)}&source=${encodeURIComponent(marketSource())}&limit=5`);
          if (!matches.length) {
            if (forceMessage) document.getElementById("quoteStatus").textContent = `${t("lookupNoMatch")}: ${query}`;
            return null;
          }
          const match = matches[0];
          document.getElementById("symbol").value = match.symbol;
          if (match.name) {
            const nameInput = document.getElementById("name");
            nameInput.value = match.name;
            autoNameValue = match.name;
            nameEditedManually = false;
          }
          symbol = normalizeSymbolText(match.symbol);
          document.getElementById("quoteStatus").textContent = `${t("symbolResolved")}: ${match.name || query} ${symbol}`;
        } catch (error) {
          document.getElementById("quoteStatus").textContent = `${t("quoteFailed")}: ${error.message}`;
          return null;
        }
      }
      if (marketSource() === "mock") {
        if (forceMessage) renderSourceStatus();
        return null;
      }
      try {
        const quote = await api(`/market/quote/${encodeURIComponent(symbol)}?source=${encodeURIComponent(marketSource())}`);
        const marketName = quote.payload?.name || quote.name || "";
        if (marketName) {
          const nameInput = document.getElementById("name");
          nameInput.value = marketName;
          autoNameValue = marketName;
          nameEditedManually = false;
        }
        document.getElementById("quoteStatus").textContent = `${t("quoteLoaded")}: ${marketName || symbol} ${formatPrice(quote.price)} (${quote.source})`;
        return quote;
      } catch (error) {
        document.getElementById("quoteStatus").textContent = `${t("quoteFailed")}: ${error.message}`;
        return null;
      }
    }
    function currentSymbol() {
      const value = normalizeSymbolText(document.getElementById("symbol").value);
      return /^[0-9]{6}$/.test(value) ? value : "";
    }
    function lookupText() {
      const symbolInput = String(document.getElementById("symbol").value || "").trim();
      if (symbolInput) return symbolInput;
      return String(document.getElementById("name").value || "").trim();
    }
    function poolSymbols() {
      return new Set(cachedWatchlist.map(row => normalizeSymbolText(row.symbol)));
    }
    function filterByPoolSymbols(rows) {
      const symbols = poolSymbols();
      if (!symbols.size) return [];
      return rows.filter(row => symbols.has(normalizeSymbolText(row.symbol)));
    }
    function normalizeSymbolText(value) {
      return String(value || "").trim().toUpperCase();
    }
    function syncAutoName() {
      const rawInput = String(document.getElementById("symbol").value || "").trim();
      if (rawInput && !/^[0-9]{0,6}$/.test(rawInput)) return;
      const nameInput = document.getElementById("name");
      if (nameEditedManually && nameInput.value !== autoNameValue) return;
      autoNameValue = "";
      nameInput.value = autoNameValue;
      nameEditedManually = false;
    }
    function renderSourceStatus() {
      const source = marketSource();
      const text = source === "mock"
        ? t("mockSourceHint")
        : source === "tdx-official"
          ? t("officialSourceHint")
          : t("realSourceHint");
      document.getElementById("quoteStatus").textContent = text;
    }
    function renderDailyReview(report) {
      if (report.report_type === "opportunity_followup") { renderOpportunityFollowup(report); return; }
      if (report.report_type === "opportunity_history") { renderOpportunityHistory(report.rows); return; }
      if (report.report_type === "opportunity_job") { renderOpportunityJob(report); return; }
      const payload = report.payload || report;
      if (payload.decision_analysis) {
        renderDecisionEngine(payload.decision_analysis, {
          reportId: payload.analysis_report_id,
          generatedAt: payload.analysis_generated_at
        });
        return;
      }
      if (payload.decision_review_status === "not_analyzed") {
        document.getElementById("review").innerHTML = `<p class="status">${escapeHtml(t("decisionNotAnalyzed"))}</p>`;
        return;
      }
      if (["stock_pool_mcp_analysis", "stock_pool_market_analysis"].includes(payload.report_type)) {
        renderPoolAnalysis(report);
        return;
      }
      if (payload.report_type === "stock_pool_chan_analysis") {
        renderChanAnalysis(report);
        return;
      }
      if (payload.report_type === "stock_pool_decision_engine") {
        renderDecisionEngine(report);
        return;
      }
      const quality = payload.data_quality || {};
      const focusKeys = payload.next_session_focus_keys || ["review_high_risk", "check_data_quality", "compare_with_thesis"];
      const summary = t("reviewedTemplate")
        .replace("{holdings}", payload.holding_count ?? 0)
        .replace("{signals}", payload.signal_count ?? 0);
      const failedCount = quality.failed_fetch_count ?? 0;
      const fetchText = failedCount === 0 ? t("fetchOk") : failedCount;
      const holdings = (payload.holding_details || []).map(row => ({
        ...row,
        cost_price: formatOptionalPrice(row.cost_price),
        stop_loss: formatOptionalPrice(row.stop_loss),
        take_profit: formatOptionalPrice(row.take_profit)
      }));
      const highRiskSignals = mapSignalDetailRows(payload.high_risk_signal_details || []);
      const recentSignals = mapSignalDetailRows(payload.recent_signal_details || []);
      const failedFetches = (quality.failed_fetches || []).map(row => ({
        ...row,
        data_type: enumLabel(row.data_type),
        status: enumLabel(row.status),
        fetched_at: shortTime(row.fetched_at)
      }));
      document.getElementById("review").innerHTML = `
        <p class="summary">${summary}</p>
        <div class="metric-grid" style="margin-top:10px">
          <div class="metric"><b>${t("highRiskSymbols")}</b>${(payload.high_risk_symbols || []).join(", ") || "-"}</div>
          <div class="metric"><b>${t("highRiskSignalCount")}</b>${payload.high_risk_signal_count ?? 0}</div>
          <div class="metric"><b>${t("failedFetchCount")}</b>${fetchText}</div>
        </div>
        <p class="status" style="margin-top:12px">${t("holdingDetails")}</p>
        ${table(holdings, ["symbol", "name", "quantity", "cost_price", "stop_loss", "take_profit", "initial_thesis"])}
        <p class="status" style="margin-top:12px">${t("highRiskSignalDetails")}</p>
        ${table(highRiskSignals, ["symbol", "signal_type", "action", "risk_level", "price", "created_at", "reasons", "next_check"])}
        <p class="status" style="margin-top:12px">${t("recentSignalDetails")}</p>
        ${table(recentSignals, ["symbol", "signal_type", "action", "risk_level", "price", "created_at", "next_check"])}
        <p class="status" style="margin-top:12px">${t("failedFetchDetails")}</p>
        ${table(failedFetches, ["symbol", "source", "data_type", "status", "message", "fetched_at"])}
        <p class="status" style="margin-top:12px">${t("nextFocus")}</p>
        <ul>${focusKeys.map(key => `<li>${t("focus_" + key)}</li>`).join("")}</ul>
      `;
    }
    function mapSignalDetailRows(rows) {
      return rows.map(row => ({
        ...row,
        signal_type: enumLabel(row.signal_type),
        action: enumLabel(row.action),
        risk_level: enumLabel(row.risk_level),
        price: formatOptionalPrice(row.price),
        strength: row.strength === null || row.strength === undefined ? "" : Number(row.strength).toFixed(2),
        created_at: shortTime(row.created_at),
        reasons: Array.isArray(row.reasons) ? row.reasons.join("; ") : (row.reasons || "")
      }));
    }
    function renderPoolAnalysis(report) {
      const payload = report.payload || report;
      if (payload.report_type === "stock_pool_market_analysis") return renderMarketOverview(payload);
      const quality = payload.data_quality || {};
      const plan = payload.tool_plan || {};
      const isMarketAnalysis = payload.report_type === "stock_pool_market_analysis";
      const rows = (payload.items || []).map(item => ({
        symbol: item.symbol,
        name: item.name || "",
        action_hint: enumLabel(item.action_hint),
        price: item.quote?.fields?.price ?? item.mcp_calls?.quote?.fields?.price ?? ""
      }));
      const metricCells = isMarketAnalysis
        ? `
          <div class="metric"><b>${t("marketDataSource")}</b>${escapeHtml(plan.data_source || plan.quote_tool || "-")}</div>
          <div class="metric"><b>${t("quoteOkCount")}</b>${quality.quote_count ?? 0}</div>
          <div class="metric"><b>${t("missingQuotes")}</b>${quality.missing_quote_count ?? 0}</div>
          <div class="metric"><b>${t("nextSteps")}</b>${(payload.next_steps || []).map(enumLabel).join(", ") || "-"}</div>
        `
        : `
          <div class="metric"><b>${t("mcpToolPlan")}</b>${escapeHtml(plan.quote_tool || "-")} / ${escapeHtml(plan.profile_tool || "-")}</div>
          <div class="metric"><b>${t("missingQuotes")}</b>${quality.missing_quote_count ?? 0}</div>
          <div class="metric"><b>${t("failedSymbols")}</b>${(quality.failed_symbols || []).join(", ") || "-"}</div>
          <div class="metric"><b>${t("nextSteps")}</b>${(payload.next_steps || []).map(enumLabel).join(", ") || "-"}</div>
        `;
      document.getElementById("review").innerHTML = `
        <p class="summary">${escapeHtml(payload.summary || "")}</p>
        <div class="metric-grid" style="margin-top:10px">
          ${metricCells}
        </div>
        <div style="margin-top:12px">${table(rows, ["symbol", "name", "action_hint", "price"])}</div>
      `;
    }
    function renderChanAnalysis(report) {
      const payload = report.payload || report;
      if (chanDisplay !== payload) chanFilter = "all";
      chanDisplay = payload;
      const quality = payload.data_quality || {};
      const items = payload.items || [];
      const candidates = payload.model_version ? items.filter(item => item.signal?.status === "candidate").length : "-";
      document.getElementById("review").innerHTML = `
        <div class="context-strip">
          <span><b>${t("analyzedStocks")}</b>${items.length}</span>
          <span><b>${t("chanHealthy")}</b>${quality.complete_count ?? "-"} / ${items.length}</span>
          <span><b>${t("chanCandidates")}</b>${candidates}</span>
          <span><b>${t("chanReview")}</b>${quality.review_count ?? "-"}</span>
        </div>
        <p class="insight-meta">${escapeHtml(payload.tool_plan?.data_source || "-")} · ${t("generatedAt")}: ${escapeHtml(insightTime(payload.generated_at))}</p>
        <p class="insight-meta">${t("chanModelNote")}</p>
        ${fetchIssueNotice(payload)}
        ${payload.model_version ? "" : `<p class="status">${t("analysisLegacy")}</p>`}
        <div class="insight-toolbar"><label>${t("filterLabel")}<select id="chan-filter" onchange="setChanFilter(this.value)">
          ${insightOptions([["all","insightAll"],["above","insightAbove"],["below","insightBelow"],["inside","insightInside"],["review","insightReview"]], chanFilter)}
        </select></label></div>
        ${insightHeader(["name","structure","structureClose","centerBand","chanCandidate","status"])}
        <div id="chan-results">${chanRowsHtml()}</div>
        <details class="model-details"><summary>${t("chanMethod")}</summary>
          <p class="insight-meta">${t("chanMethodDetail")}</p>
          ${detailFields([["modelDetails", payload.model_version || t("unavailable")], ["failedSymbols", (quality.failed_symbols || []).join(", ") || "-"]])}
          ${currentLanguage === "zh" ? `<p class="insight-meta">${escapeHtml(payload.summary || "")}</p>` : ""}
        </details>
      `;
    }
    function insightNumber(value) {
      if (value === null || value === undefined || value === "" || typeof value === "boolean") return null;
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    }
    function fetchIssueNotice(payload) {
      const issues = Object.values(payload.data_quality?.fetch_issues || {});
      if (!issues.length) return "";
      return `<p class="data-alert" role="status">${[...new Set(issues)].map(issue => `${escapeHtml(t(issue))} (${issues.filter(value => value === issue).length})`).join("; ")}</p>`;
    }
    function insightTime(value) {
      const date = new Date(value || "");
      return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString(currentLanguage === "zh" ? "zh-CN" : "en-GB", {
        timeZone:"Asia/Shanghai", year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit", hourCycle:"h23"
      });
    }
    function insightOptions(options, selected) {
      return options.map(([value, key]) => `<option value="${value}"${value === selected ? " selected" : ""}>${t(key)}</option>`).join("");
    }
    function insightHeader(labels) {
      return `<div class="insight-row insight-head" aria-hidden="true">${labels.map((key, index) => `<span class="${index === 3 || index === 4 ? "secondary-cell" : ""}">${t(key)}</span>`).join("")}<span></span></div>`;
    }
    function insightCell(key, value, {sub = "", numeric = false, secondary = false, tone = ""} = {}) {
      return `<span class="insight-cell${secondary ? " secondary-cell" : ""}"><span class="mobile-label">${t(key)}</span><span class="value ${numeric ? "numeric" : ""} ${tone}">${escapeHtml(value ?? "-")}</span>${sub ? `<small>${escapeHtml(sub)}</small>` : ""}</span>`;
    }
    function signedChange(value) {
      const number = insightNumber(value);
      return number === null ? "-" : `${number > 0 ? "+" : ""}${number.toFixed(2)}%`;
    }
    function quoteAmount(value) {
      const number = insightNumber(value);
      if (number === null) return "-";
      if (currentLanguage === "en") return number >= 1e9 ? `${(number / 1e9).toFixed(2)}B` : `${(number / 1e6).toFixed(2)}M`;
      return number >= 1e8 ? `${(number / 1e8).toFixed(2)}亿` : `${(number / 1e4).toFixed(2)}万`;
    }
    function renderMarketOverview(payload) {
      if (overviewDisplay !== payload) { overviewFilter = "all"; overviewSort = "default"; }
      overviewDisplay = payload;
      const quality = payload.data_quality || {}, breadth = payload.breadth || {}, count = (payload.items || []).length;
      const bar = [["up", "#b84b43"],["down", "#378563"],["flat", "#8e99a7"],["unknown", "#e6e9ed"]]
        .map(([key,color]) => `<i style="width:${count ? Math.max(0, Math.min(100, 100 * (insightNumber(breadth[key]) || 0) / count)) : 0}%;background:${color}"></i>`).join("");
      document.getElementById("review").innerHTML = `
        <div class="context-strip">
          <span><b>${t("quotesCoverage")}</b>${quality.quote_count ?? "-"} / ${count}</span>
          <span><b>${t("freshQuotes")}</b>${quality.fresh_quote_count ?? "-"} / ${count}</span>
          <span><b>${t("poolQuoteAverage")}</b><strong class="${pnlClass(breadth.mean_change_pct)}">${signedChange(breadth.mean_change_pct)}</strong></span>
        </div>
        <div class="context-strip"><b>${t("poolQuoteBreadth")}</b>
          <span class="gain">${t("insightUp")} ${breadth.up ?? "-"}</span><span class="loss">${t("insightDown")} ${breadth.down ?? "-"}</span>
          <span>${t("quoteFlat")} ${breadth.flat ?? "-"}</span><span>${t("quoteUnknown")} ${breadth.unknown ?? "-"}</span>
        </div><div class="breadth-bar" aria-hidden="true">${bar}</div>
        <p class="insight-meta">${escapeHtml(payload.tool_plan?.data_source || "-")} · ${t("generatedAt")}: ${escapeHtml(insightTime(payload.generated_at))}</p>
        <p class="insight-meta">${t("exchangeTimeCaution")}</p>
        ${fetchIssueNotice(payload)}
        ${payload.model_version ? "" : `<p class="status">${t("analysisLegacy")}</p>`}
        <div class="insight-toolbar">
          <label>${t("filterLabel")}<select id="overview-filter" onchange="setOverviewFilter(this.value)">${insightOptions([["all","insightAll"],["up","insightUp"],["down","insightDown"],["review","insightReview"]], overviewFilter)}</select></label>
          <label>${t("sortLabel")}<select id="overview-sort" onchange="setOverviewSort(this.value)">${insightOptions([["default","insightDefault"],["change_desc","insightChangeDesc"],["change_asc","insightChangeAsc"],["amount_desc","insightAmountDesc"]], overviewSort)}</select></label>
        </div>
        ${insightHeader(["name","price","quoteChange","quoteAmount","quoteTurnover","quoteState"])}
        <div id="overview-results">${overviewRowsHtml()}</div>
        <details class="model-details"><summary>${t("dataQuality")}</summary>
          ${detailFields([["failedSymbols", (quality.failed_symbols || []).join(", ") || "-"], ["marketDataSource", payload.tool_plan?.data_source]])}
          ${currentLanguage === "zh" ? `<p class="insight-meta">${escapeHtml(payload.summary || "")}</p>` : ""}
        </details>`;
    }
    function setOverviewFilter(value) {
      overviewFilter = ["all","up","down","review"].includes(value) ? value : "all";
      document.getElementById("overview-results").innerHTML = overviewRowsHtml();
    }
    function setOverviewSort(value) {
      overviewSort = ["default","change_desc","change_asc","amount_desc"].includes(value) ? value : "default";
      document.getElementById("overview-results").innerHTML = overviewRowsHtml();
    }
    function overviewRowsHtml() {
      const rows = (overviewDisplay?.items || []).filter(item => {
        const quote = item.quote || {}, pct = insightNumber(quote.fields?.pct_change);
        if (overviewFilter === "up") return quote.status === "success" && pct !== null && pct > 0;
        if (overviewFilter === "down") return quote.status === "success" && pct !== null && pct < 0;
        if (overviewFilter === "review") return quote.status !== "success" || pct === null;
        return true;
      });
      if (overviewSort !== "default") rows.sort((a,b) => {
        const key = overviewSort === "amount_desc" ? "amount" : "pct_change";
        const av = insightNumber(a.quote?.fields?.[key]), bv = insightNumber(b.quote?.fields?.[key]);
        if (av === null || bv === null) return av === bv ? 0 : av === null ? 1 : -1;
        return overviewSort === "change_asc" ? av - bv : bv - av;
      });
      return rows.map(item => {
        const quote = item.quote || {}, fields = quote.fields || {}, status = quote.status || "unverified";
        return `<details class="insight-stock"><summary class="insight-row">
          ${insightCell("name", item.name || item.symbol, {sub:item.symbol})}
          ${insightCell("price", formatPrice(fields.price), {numeric:true})}
          ${insightCell("quoteChange", signedChange(fields.pct_change), {numeric:true, tone:pnlClass(fields.pct_change)})}
          ${insightCell("quoteAmount", quoteAmount(fields.amount), {numeric:true, secondary:true})}
          ${insightCell("quoteTurnover", formatPercent(fields.turnover_rate) || "-", {numeric:true, secondary:true})}
          ${insightCell("quoteState", t(`quote_${status}`), {sub:fields.market_time ? String(fields.market_time).slice(0,10) : t("exchangeTimeUnknown")})}
        </summary><div class="insight-detail detail-grid"><div>
          ${detailFields([["quotePrevious",formatPrice(fields.previous_close)],["quoteOpen",formatPrice(fields.open)],
            ["quoteHigh",formatPrice(fields.high)],["quoteLow",formatPrice(fields.low)],["quoteAmount",quoteAmount(fields.amount)],["quoteTurnover",formatPercent(fields.turnover_rate) || "-"]])}
        </div><div>${detailFields([["quoteReadTime",insightTime(fields.fetched_at)], ["exchangeTime",fields.market_time ? insightTime(fields.market_time) : t("exchangeTimeUnknown")],
            ["marketDataSource",fields.source || overviewDisplay.tool_plan?.data_source], ["dataIssues",(quote.issues || []).map(t).join("; ") || "-"]])}</div>
        </div></details>`;
      }).join("") || `<p class="status">${t("noMatchingStocks")}</p>`;
    }
    function setChanFilter(value) {
      chanFilter = ["all","above","below","inside","review"].includes(value) ? value : "all";
      document.getElementById("chan-results").innerHTML = chanRowsHtml();
    }
    function chanRowsHtml() {
      const rows = (chanDisplay?.items || []).filter(item => {
        if (chanFilter === "review") return item.data_quality?.status !== "complete";
        if (chanFilter === "all") return true;
        return item.structure_key === chanFilter || item.structure_key === `extended_${chanFilter}`;
      });
      return rows.map((item,index) => {
        const signal = item.signal || {}, quality = item.data_quality || {}, center = item.latest_center;
        const band = center ? `${formatPrice(center.lower)} ~ ${formatPrice(center.upper)}` : "-";
        const text = chanNarrative(item);
        return `<details class="insight-stock"${index === 0 ? " open" : ""}><summary class="insight-row">
          ${insightCell("name", item.name || item.symbol, {sub:item.symbol})}
          ${insightCell("structure", item.structure_key ? t(`chan_${item.structure_key}`) : item.structure || "-")}
          ${insightCell("structureClose", formatPrice(item.current_price), {numeric:true, sub:item.as_of || "-"})}
          ${insightCell("centerBand", band, {secondary:true, sub:signedChange(item.center_distance_pct)})}
          ${insightCell("chanCandidate", enumLabel(signal.type), {secondary:true})}
          ${insightCell("status", quality.status === "complete" ? t("chanHealthy") : t("chanReview"))}
        </summary><div class="insight-detail">
          <div class="opportunity-head"><h3>${escapeHtml(enumLabel(signal.type))}</h3><span class="insight-badge ${quality.status === "complete" ? "" : "caution"}">${signal.status === "candidate" ? t("chanCandidates") : t("chanObservation")} · ${t("confidence")} ${escapeHtml(enumLabel(signal.confidence) || "-")}</span></div>
          <div class="insight-evidence">${[["chanEvidence",text.reason],["chanCondition",text.trigger],["chanInvalidation",text.invalidation]].map(([key,value]) => `<div><h4>${t(key)}</h4><p>${escapeHtml(value || "-")}</p></div>`).join("")}</div>
          <div class="chan-chart-host" data-symbol="${escapeHtml(item.symbol)}">${chanChartHtml(item, index)}</div>
          <div class="chart-legend"><span><i class="legend-line"></i>${t("stableStroke")}</span><span><i class="legend-line draft"></i>${t("draftStroke")}</span><span><i class="legend-zone"></i>${t("centerLegend")}</span></div>
          <div class="detail-grid"><div>${detailFields([["centerBand", band], ["structureDate",item.as_of], ["centerAge",item.center_age_bars], ["centerDistance",signedChange(item.center_distance_pct)]])}</div>
          <div>${detailFields([["stableStrokeCount",item.confirmed_stroke_count], ["bar_count",item.bar_count], ["excludedBarCount",quality.excluded_bar_count],
            ["dataIssues",(quality.issues || []).map(t).join("; ") || "-"]])}</div></div>
        </div></details>`;
      }).join("") || `<p class="status">${t("noMatchingStocks")}</p>`;
    }
    function chanNarrative(item) {
      if (chanDisplay?.model_version !== "daily_pen_overlap_v2") return {
        reason:item.signal?.reason || t("analysisLegacy"),
        trigger:item.signal?.trigger || "-", invalidation:item.signal?.invalidation || "-"
      };
      const type = item.signal?.type, upper = formatPrice(item.latest_center?.upper), lower = formatPrice(item.latest_center?.lower);
      const zh = currentLanguage === "zh";
      const reasons = {
        suspected_third_buy:zh ? "中枢形成后向上离开，稳定回落笔低点仍高于上沿。仅为笔级候选，次级别走势尚未验证。" : "Departure above the center followed by a stable pullback wholly above it. Pen-level candidate only; sublevel structure is unverified.",
        suspected_third_sell:zh ? "中枢形成后向下离开，稳定反弹笔高点仍低于下沿。仅为笔级候选，次级别走势尚未验证。" : "Departure below the center followed by a stable rebound wholly below it. Pen-level candidate only; sublevel structure is unverified.",
        upward_leave:zh ? "收盘价位于中枢上方，尚未得到完整的中枢外回踩确认。" : "The close is above the center; a qualifying outside-center pullback is not yet established.",
        downward_leave:zh ? "收盘价位于中枢下方，尚未得到完整的中枢外反弹确认。" : "The close is below the center; a qualifying outside-center rebound is not yet established.",
        center_range:zh ? "收盘价仍在中枢内，方向没有确认。" : "The close remains inside the center; direction is unresolved.",
        extended_above_center:zh ? "价格已明显远离中枢上沿，旧中枢只是历史参考，不能当成当前三买触发位。" : "Price is extended above the center. This is historical context, not a nearby third-buy trigger.",
        extended_below_center:zh ? "价格已明显远离中枢下沿，旧中枢只是历史参考，不能当成当前三卖触发位。" : "Price is extended below the center. This is historical context, not a nearby third-sell trigger.",
        trend_observe:zh ? "已有稳定笔，但尚未形成三笔重叠区。" : "Stable strokes exist, but no three-stroke overlap has formed.",
        wait_for_structure:zh ? "稳定笔不足或最近稳定笔过旧，等待新的结构。" : "Stable strokes are insufficient or too old. Wait for a new structure.",
        data_review:zh ? "数据质量未通过检查，图中历史结构不能作为当前候选依据。" : "Data quality checks failed. Historical structures are not current candidate evidence.",
        complete_market_data:zh ? "没有可用的已收盘日线，无法判断结构。" : "No usable completed daily bars; structure cannot be assessed."
      };
      let trigger = "-", invalidation = "-";
      if (["suspected_third_buy","upward_leave"].includes(type)) {
        trigger = zh ? `回踩整体守住中枢上沿 ${upper}，并确认次级别向上结构。` : `A pullback must stay above ${upper}, followed by confirmed sublevel strength.`;
        invalidation = zh ? `回踩触及或跌回 ${upper}，候选条件失效。` : `A pullback touching or returning below ${upper} invalidates this setup.`;
      } else if (["suspected_third_sell","downward_leave"].includes(type)) {
        trigger = zh ? `反弹整体低于中枢下沿 ${lower}，并确认次级别向下结构。` : `A rebound must stay below ${lower}, followed by confirmed sublevel weakness.`;
        invalidation = zh ? `反弹触及或收回 ${lower}，候选条件失效。` : `A rebound touching or reclaiming ${lower} invalidates this setup.`;
      } else if (type === "center_range") {
        trigger = zh ? `离开 ${lower} ~ ${upper} 后观察回试结构。` : `Observe a departure and retest outside ${lower} ~ ${upper}.`;
        invalidation = zh ? "后续中枢扩张或形成新中枢时重新评估。" : "Reassess if the center expands or a new center forms.";
      } else if (type?.startsWith("extended_")) {
        trigger = zh ? "等待当前价格附近形成新结构。" : "Wait for a new structure near the current price.";
        invalidation = zh ? "不沿用远处旧中枢作为近端风险边界。" : "Do not use the distant center as a nearby risk boundary.";
      }
      return {reason:reasons[type] || (zh ? item.signal?.reason : enumLabel(type)) || "-", trigger, invalidation};
    }
    function chanChartHtml(item, index) {
      const bars = (item.chart?.bars || []).filter(bar => [bar.open,bar.high,bar.low,bar.close].every(value => insightNumber(value) !== null));
      if (!bars.length) return `<p class="status">${item.chart ? t("chartUnavailable") : t("analysisLegacy")}</p>`;
      const width = Math.max(300, (document.getElementById("review").clientWidth || 796) - 36), height = width < 500 ? 240 : 300;
      const left = 12, right = width - 64, top = 18, bottom = height - 30;
      const rawMin = Math.min(...bars.map(bar => bar.low)), rawMax = Math.max(...bars.map(bar => bar.high));
      const padding = Math.max((rawMax - rawMin) * .08, rawMax * .01, .01);
      const low = rawMin - padding, high = rawMax + padding;
      const y = value => top + (high - value) / (high - low) * (bottom - top);
      const step = (right - left) / bars.length, x = i => left + step * (i + .5);
      const first = bars[0].trade_date, last = bars.at(-1).trade_date;
      const dateIndex = date => bars.findIndex(bar => bar.trade_date >= date);
      const clipId = `chan-clip-${index}`;
      const grid = Array.from({length:4}, (_,i) => {
        const value = low + (high - low) * i / 3, py = y(value);
        return `<line x1="${left}" x2="${right}" y1="${py}" y2="${py}" stroke="#e5e9ee"/><text x="${right + 8}" y="${py + 4}">${formatPrice(value)}</text>`;
      }).join("");
      const centers = (item.chart.centers || []).filter(center => center.end_date >= first && center.start_date <= last
        && insightNumber(center.upper) !== null && insightNumber(center.lower) !== null).map(center => {
        const start = Math.max(0,dateIndex(center.start_date)), end = center.end_date >= last ? bars.length - 1 : dateIndex(center.end_date);
        return `<rect x="${x(start) - step / 2}" y="${y(center.upper)}" width="${Math.max(step, step * (end - start + 1))}" height="${Math.max(0,y(center.lower) - y(center.upper))}" fill="#f8e9bb" fill-opacity=".55" stroke="#b79131"><title>${escapeHtml(`${t("centerBand")}: ${formatPrice(center.lower)} ~ ${formatPrice(center.upper)} / ${center.start_date} ~ ${center.end_date}`)}</title></rect>`;
      }).join("");
      const candles = bars.map((bar,i) => {
        const color = bar.close >= bar.open ? "#b84b43" : "#378563", body = Math.max(1,Math.min(7,step * .65));
        return `<g class="chart-candle"><title>${escapeHtml(`${bar.trade_date} | ${t("quoteOpen")} ${formatPrice(bar.open)} | ${t("quoteHigh")} ${formatPrice(bar.high)} | ${t("quoteLow")} ${formatPrice(bar.low)} | ${t("structureClose")} ${formatPrice(bar.close)}`)}</title><line x1="${x(i)}" x2="${x(i)}" y1="${y(bar.high)}" y2="${y(bar.low)}" stroke="${color}"/><rect x="${x(i) - body / 2}" y="${Math.min(y(bar.open),y(bar.close))}" width="${body}" height="${Math.max(1,Math.abs(y(bar.open) - y(bar.close)))}" fill="${color}"/></g>`;
      }).join("");
      const strokes = (item.chart.strokes || []).filter(stroke => stroke.start_date >= first && stroke.end_date <= last
        && [stroke.start_price,stroke.end_price].every(value => insightNumber(value) !== null)).map(stroke =>
        `<line class="chart-stroke" x1="${x(dateIndex(stroke.start_date))}" x2="${x(dateIndex(stroke.end_date))}" y1="${y(stroke.start_price)}" y2="${y(stroke.end_price)}" stroke="#3976b8" stroke-width="2"${stroke.confirmed ? "" : ' stroke-dasharray="5 4"'}><title>${escapeHtml(`${t(stroke.confirmed ? "stableStroke" : "draftStroke")}: ${stroke.start_date} ~ ${stroke.end_date}`)}</title></line>`
      ).join("");
      return `<svg class="chan-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(`${item.symbol} ${t("chanChartTitle")}`)}"><title>${escapeHtml(t("chanChartTitle"))}</title>
        <defs><clipPath id="${clipId}"><rect x="${left}" y="${top}" width="${right - left}" height="${bottom - top}"/></clipPath></defs>
        ${grid}<g clip-path="url(#${clipId})">${centers}${candles}${strokes}</g>
        <text x="${left}" y="${height - 7}">${escapeHtml(first)}</text><text x="${right}" y="${height - 7}" text-anchor="end">${escapeHtml(last)}</text></svg>`;
    }
    if (typeof window !== "undefined") window.addEventListener("resize", () => {
      if (!chanDisplay || activeView !== "chan") return;
      document.querySelectorAll(".chan-chart-host").forEach((host,index) => {
        const item = chanDisplay.items?.find(item => item.symbol === host.dataset.symbol);
        if (item) host.innerHTML = chanChartHtml(item,index);
      });
    });
    function renderDecisionEngine(report, savedContext = null) {
      const payload = report.payload || report;
      const quality = payload.data_quality || {};
      const regime = payload.market_regime || {};
      const regimeEvidence = (regime.evidence || [])
        .map(entry => `${entry.source || ""}: ${entry.observation || ""}`)
        .filter(Boolean);
      const failedQuotes = quality.failed_quote_symbols || [];
      const failedKlines = quality.failed_kline_symbols || [];
      const calibration = payload.calibration?.status || payload.calibration || "uncalibrated";
      const model = payload.model_version || payload.model || payload.scope?.model || t("unavailable");
      const comparison = payload.comparison || report.comparison;
      decisionDisplay = {payload, comparison};
      const items = payload.items || [];
      const failed = [...new Set([...failedQuotes, ...failedKlines])];
      const complete = items.filter(item => item.data_quality?.status === "complete").length;
      const analysisTime = savedContext?.generatedAt || report.created_at || payload.generated_at;
      document.getElementById("review").innerHTML = `
        <div class="context-strip">
          <span><b>${t("marketRegime")}</b><strong>${escapeHtml(enumLabel(regime.regime) || regime.label || "-")}</strong></span>
          <span><b>${t("analyzedStocks")}</b>${items.length}</span>
          <span><b>${t("completeStocks")}</b>${complete} / ${items.length}</span>
          <span><b>${t("failedStocks")}</b>${failed.length}${failed.length ? ` · ${escapeHtml(failed.join(", "))}` : ""}</span>
          <span><b>${t("horizonDays")}</b>${escapeHtml(String(payload.scope?.horizon_days || "-"))} ${t("daysUnit")}</span>
        </div>
        <p class="status">${t("latestAnalysis")}: ${escapeHtml(analysisTime ? shortTime(analysisTime) : t("unavailable"))} · ${t("scoreCaution")}</p>
        <div id="decision-results">${decisionResultsHtml()}</div>
        <details class="model-details"><summary>${t("modelDetails")}</summary>
          ${savedContext ? `<p class="status">${t("savedAnalysis")} · ${t("analysisReportId")}: ${escapeHtml(savedContext.reportId ?? "-")}
            · ${t("analysisGeneratedAt")}: ${escapeHtml(savedContext.generatedAt || t("unavailable"))}</p>` : ""}
          <p>${escapeHtml(payload.summary || "")}</p>
          <p class="status">${t("decisionEngineModel")}: ${escapeHtml(model)} · ${calibration === "uncalibrated" ? t("uncalibrated") : `${t("calibrationStatus")}: ${escapeHtml(calibration)}`}</p>
          ${detailFields([["regimeConfidence", enumLabel(regime.confidence)], ["strategyBias", regime.strategy_bias?.summary], ["poolBreadthLabel", items.length], ["marketDataSource", payload.tool_plan?.data_source]])}
          <h3>${t("regimeEvidence")}</h3><ul>${regimeEvidence.map(item => `<li>${escapeHtml(item)}</li>`).join("") || `<li>-</li>`}</ul>
          ${quality.unavailable_evidence?.length ? `<h3>${t("dataQuality")}</h3><ul>${quality.unavailable_evidence.map(value => `<li>${escapeHtml(value)}</li>`).join("")}</ul>` : ""}
          <h3>${t("nextSteps")}</h3><ul>${(payload.next_steps || []).map(step => `<li>${escapeHtml(step)}</li>`).join("")}</ul>
        </details>
      `;
    }
    function dominantScenario(item) {
      const scores = ["up", "range", "down"].filter(key => Number.isFinite(item.probabilities?.[key]));
      return scores.sort((a, b) => item.probabilities[b] - item.probabilities[a])[0] || "unknown";
    }
    function setDecisionFilter(value) {
      decisionFilter = value;
      renderDecisionResults();
    }
    function renderDecisionResults() {
      document.getElementById("decision-results").innerHTML = decisionResultsHtml();
    }
    function decisionResultsHtml() {
      const {payload, comparison} = decisionDisplay || {payload:{}};
      const all = payload.items || [];
      const scoped = selectedStock ? all.filter(item => opportunityIdentity(item.symbol) === opportunityIdentity(selectedStock)) : all;
      const counts = Object.fromEntries(["up", "range", "down", "unknown"].map(key => [key, scoped.filter(item => dominantScenario(item) === key).length]));
      const filterKeys = ["all", "up", "range", "down", ...(counts.unknown ? ["unknown"] : [])];
      const rows = scoped.filter(item => decisionFilter === "all" || dominantScenario(item) === decisionFilter);
      const labels = ["symbol", "current_price", "conclusion", "mainReason", "scenarioWeights", "details"];
      return `${selectedStock ? `<p class="status">${t("selectedStock")}: ${escapeHtml(selectedStock)} <button class="stock-link" onclick="clearStockSelection()">${t("clearSelection")}</button></p>` : ""}
        <div class="decision-filters">${filterKeys.map(key => `<button aria-pressed="${decisionFilter === key}" onclick="setDecisionFilter('${key}')">${key === "all" ? t("allStocks") : enumLabel(key)} ${key === "all" ? scoped.length : counts[key]}</button>`).join("")}</div>
        ${rows.length ? `<table class="decision-list" aria-label="${t("scenarioScores")}"><thead><tr>${labels.map(key => `<th scope="col">${t(key)}</th>`).join("")}</tr></thead><tbody>${rows.map((item, index) => {
          const decision = item.decision || {};
          const evidence = (item.evidence || []).filter(entry => entry.observation).slice().sort((a,b) =>
            Math.max(0, ...Object.values(b.contribution || {}).map(value => Math.abs(Number(value) || 0))) - Math.max(0, ...Object.values(a.contribution || {}).map(value => Math.abs(Number(value) || 0)))).slice(0, 2);
          const reason = evidence.map(entry => `${entry.source || ""}: ${readableObservation(entry.observation)}`).join("; ") || t("noEvidence");
          const cells = [
            `<button class="stock-link" onclick="openDecisionDetail(${index})">${escapeHtml(item.name || item.symbol)}</button><small>${escapeHtml(item.symbol)}</small>`,
            escapeHtml(formatOptionalPrice(item.current_price) || "-"),
            `${escapeHtml(decisionLabel(decision))}<small>${t("risk_level")}: <span class="${decision.risk_level === "high" ? "risk-flag" : ""}">${escapeHtml(enumLabel(decision.risk_level) || "-")}</span></small>`,
            escapeHtml(reason),
            ["up", "range", "down"].map(key => `<small>${enumLabel(key)} ${escapeHtml(formatProbability(item.probabilities?.[key]) || "-")}</small>`).join(""),
            `<button class="stock-link" onclick="openDecisionDetail(${index})">${t("details")}</button>`
          ];
          return `<tr>${cells.map((cell, i) => `<td data-label="${t(labels[i])}" class="${i === 1 ? "number-cell" : ""}">${cell}</td>`).join("")}</tr>`;
        }).join("")}</tbody></table>` : `<p class="status">${t("noMatchingStocks")}</p>`}
        ${rows.map((item, index) => decisionDetails(item, comparison, `decision-detail-${index}`)).join("")}`;
    }
    function openDecisionDetail(index) {
      const detail = document.getElementById(`decision-detail-${index}`);
      if (!detail) return;
      detail.open = true;
      detail.scrollIntoView({block:"nearest", behavior:"smooth"});
      detail.querySelector?.("summary")?.focus();
    }
    function readableObservation(value) {
      return String(value ?? t("unavailable")).split(/([a-z][a-z0-9_]+)/)
        .map(part => enumText[currentLanguage][part] || part).join("");
    }
    function detailFields(entries) {
      return `<dl class="detail-fields">${entries.map(([key, value]) => `<dt>${escapeHtml(t(key))}</dt><dd>${escapeHtml(value ?? t("unavailable"))}</dd>`).join("")}</dl>`;
    }
    function factorLabel(key) {
      const translated = t(key);
      if (translated !== key) return translated;
      if (["20", "60"].includes(key)) return `${key}${currentLanguage === "zh" ? "日" : "D"}`;
      const labels = currentLanguage === "zh"
        ? {stock_return: "个股收益", market_return: "大盘收益", pool_average_return: "股票池平均收益", pool_median_return: "股票池中位收益",
          vs_index_: "相对指数", vs_pool_: "相对股票池", excess_market_: "超额大盘", excess_pool_average_: "超额股票池平均", excess_pool_median_: "超额股票池中位", ma: "均线偏离"}
        : {stock_return: "Stock return", market_return: "Market return", pool_average_return: "Pool average return", pool_median_return: "Pool median return",
          vs_index_: "vs index", vs_pool_: "vs pool", excess_market_: "Excess vs market", excess_pool_average_: "Excess vs pool average", excess_pool_median_: "Excess vs pool median", ma: "MA deviation"};
      const match = key.match(/^(stock_return|market_return|pool_average_return|pool_median_return|vs_index_|vs_pool_|excess_market_|excess_pool_average_|excess_pool_median_|ma)(20|60)(?:_deviation)?_pct$/);
      return match ? `${labels[match[1]]} ${match[2]}${currentLanguage === "zh" ? "日" : "D"}` : key.replaceAll("_", " ");
    }
    function factorFields(value, path = []) {
      if (!value || !Object.keys(value).length) return `<p class="status">${t("unavailable")}</p>`;
      const entries = Object.entries(value);
      const fields = entries.filter(([, metric]) => metric === null || typeof metric !== "object").map(([key, metric]) => {
        const formatted = metric === null || metric === undefined ? t("unavailable") : key.endsWith("_pct") ? formatPercent(metric) || t("unavailable") : String(metric);
        const readable = key === "calendar_source" ? enumText[currentLanguage][`calendar_${formatted}`] || formatted
          : key === "status" ? enumLabel(formatted) : formatted;
        return `<dt>${escapeHtml(factorLabel(key))}</dt><dd>${escapeHtml(readable)}</dd>`;
      }).join("");
      const groups = entries.filter(([, metric]) => metric !== null && typeof metric === "object").map(([key, metric]) => {
        const groupPath = [...path, key];
        return `<h4>${escapeHtml(groupPath.map(factorLabel).join(" · "))}</h4>${factorFields(metric, groupPath)}`;
      }).join("");
      return `${fields ? `<dl class="detail-fields">${fields}</dl>` : ""}${groups}`;
    }
    function scoreVector(values, changes = false) {
      return ["up", "range", "down"].map(key => {
        const value = values?.[key];
        const number = value === null || value === undefined || value === "" ? NaN : Number(value);
        const formatted = Number.isFinite(number)
          ? changes ? `${number > 0 ? "+" : ""}${(number * 100).toFixed(1)}` : formatProbability(number)
          : "-";
        return `${enumLabel(key)} ${formatted}`;
      }).join(" / ");
    }
    function decisionLabel(value) {
      return typeof value === "string" ? enumLabel(value) : enumLabel(value?.key) || value?.label || "-";
    }
    function comparisonDetails(symbol, comparison) {
      const entry = comparison?.items?.find(item => item.symbol === symbol);
      if (!entry) return "";
      return `<h3>${t("comparison")}</h3>${detailFields([
        ["previousGeneratedAt", comparison.previous_generated_at],
        ["previousScores", scoreVector(entry.previous_probabilities)],
        ["currentScores", scoreVector(entry.current_probabilities)],
        ["scoreChanges", scoreVector(entry.probability_changes, true)],
        ["previousDecision", decisionLabel(entry.previous_decision)],
        ["currentDecision", decisionLabel(entry.current_decision)]
      ])}`;
    }
    function decisionDetails(item, comparison, id = "") {
      const quality = item.data_quality || {};
      const decision = item.decision || {};
      const priceOrigin = translations[currentLanguage][`price_origin_${item.price_origin}`] || item.price_origin;
      const chanSignals = new Set(["complete_market_data", "wait_for_structure", "trend_observe", "center_range",
        "suspected_third_buy", "upward_leave", "extended_above_center", "suspected_third_sell", "downward_leave", "extended_below_center"]);
      const evidence = (item.evidence || []).map(entry => {
        const observation = String(entry.observation ?? t("unavailable"))
          .split(/([a-z][a-z0-9_]+)/).map(part => chanSignals.has(part) ? enumLabel(part) : part).join("");
        return `<li><strong>${escapeHtml(entry.source || t("unavailable"))}</strong>
          ${detailFields([["observation", observation], ["contribution", Object.entries(entry.contribution || {}).map(([key, value]) => `${enumLabel(key)} ${value ?? "-"}`).join(" / ") || t("unavailable")], ["regime_weight", entry.regime_weight]])}</li>`;
      }).join("");
      return `<details class="stock-detail"${id ? ` id="${escapeHtml(id)}"` : ""}><summary>${escapeHtml(item.symbol)} · ${escapeHtml(item.name || "-")} · ${t("stockDetails")}</summary>
        <div class="detail-grid">
          <div><h3>${t("evidence")}</h3><ul class="evidence-list">${evidence || `<li>${t("unavailable")}</li>`}</ul>
            ${detailFields([["confidence", enumLabel(decision.confidence)], ["pnl_pct", formatPercent(item.position?.pnl_pct) || "-"], ["trigger", decision.trigger || item.chan?.trigger], ["next_check", decision.next_check]])}
            ${comparisonDetails(item.symbol, comparison)}</div>
          <div><h3>${t("factorMetrics")}</h3>${factorFields(item.factor_profile)}
            <h3>${t("dataQuality")}</h3>${detailFields([
              ["status", enumLabel(quality.status) || t("unavailable")],
              ["issues", Array.isArray(quality.issues) ? quality.issues.map(enumLabel).join("; ") || "-" : enumLabel(quality.issues) || t("unavailable")],
              ["price_origin", priceOrigin], ["kline_as_of", quality.kline_as_of],
              ["quote_fetched_at", quality.quote_fetched_at], ["bar_count", quality.bar_count]
            ])}</div>
        </div>
      </details>`;
    }
    function formatPrice(value) {
      if (value === null || value === undefined || value === "") return "-";
      const number = Number(value);
      return Number.isFinite(number) ? number.toFixed(2) : "-";
    }
    function formatOptionalPrice(value) {
      if (value === null || value === undefined || value === "") return "";
      const number = Number(value);
      return Number.isFinite(number) ? number.toFixed(3) : "";
    }
    function formatMoney(value) {
      if (value === null || value === undefined || value === "") return "";
      const number = Number(value);
      return Number.isFinite(number) ? number.toFixed(2) : "";
    }
    function formatPercent(value) {
      if (value === null || value === undefined || value === "") return "";
      const number = Number(value);
      return Number.isFinite(number) ? `${number.toFixed(2)}%` : "";
    }
    function formatProbability(value) {
      if (value === null || value === undefined || value === "") return "";
      const number = Number(value);
      return Number.isFinite(number) ? `${(number * 100).toFixed(1)}%` : "";
    }
    function pnlClass(value) {
      const number = Number(value);
      if (!Number.isFinite(number) || number === 0) return "";
      return number > 0 ? "gain" : "loss";
    }
    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }
    function table(rows, fields) {
      if (!rows.length) return `<p class="status">${t("noData")}</p>`;
      const head = fields.map(field => `<th>${escapeHtml(t(field))}</th>`).join("");
      const body = rows.map(row => `<tr>${fields.map(field => `<td>${escapeHtml(row[field] ?? "")}</td>`).join("")}</tr>`).join("");
      return `<div class="table-scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }
    function latestBySymbol(rows) {
      const seen = new Set();
      const latest = [];
      for (const row of rows) {
        const symbol = normalizeSymbolText(row.symbol);
        if (seen.has(symbol)) continue;
        seen.add(symbol);
        latest.push(row);
      }
      return latest;
    }
    function shortTime(value) {
      if (!value) return "";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString(currentLanguage === "zh" ? "zh-CN" : "en-US", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      });
    }
    function rerenderCachedPanels() {
      renderWorkspace();
      renderWatchlist(cachedWatchlist);
      renderHoldings(cachedHoldings);
      if (cachedReview) renderCachedReview();
      else renderAnalysisStatus();
    }
    function renderCachedReview() {
      const payload = cachedReview?.payload || cachedReview;
      if (payload?.report_type || payload?.decision_analysis || payload?.decision_review_status) renderDailyReview(cachedReview);
      else (currentRenderer || renderDailyReview)(cachedReview);
    }
    async function restoreSavedDecision(sequence) {
      if (sequence !== analysisSeq || activeView !== "decision" || !selectedPoolId()) return;
      const source = marketSource();
      try {
        const report = await api(`/reports/daily-review?persist=false&pool_id=${selectedPoolId()}&source=${encodeURIComponent(source)}`);
        if (sequence !== analysisSeq || source !== marketSource() || activeView !== "decision") return;
        cachedReview = report;
        currentRenderer = renderDailyReview;
        renderCachedReview();
      } catch (error) {
        if (sequence === analysisSeq && source === marketSource()) document.getElementById("actionStatus").textContent = error.message;
      }
    }
    setLanguage(currentLanguage);
    const startupSequence = analysisSeq;
    checkHealth().then(async () => {
      await loadPools();
      await restoreSavedDecision(startupSequence);
      await refreshAll();
    }).catch(error => {
      document.getElementById("health").textContent = error.message;
    });
  </script>
</body>
</html>"""
