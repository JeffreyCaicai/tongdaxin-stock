from __future__ import annotations


def index_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>通达信股票工作台</title>
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
      gap: 16px;
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
    input, textarea, select {
      box-sizing: border-box;
      border: 1px solid #cfd6c9;
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
      background: #fbfcfa;
    }
    input, textarea { width: 100%; }
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
    .header-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
    .pool-bar {
      display: grid;
      grid-template-columns: minmax(180px, 260px) minmax(180px, 1fr) auto auto;
      gap: 8px;
      align-items: end;
      margin-bottom: 14px;
    }
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
    .status { font-size: 13px; color: #5a6255; }
    .summary { background: #f7f8f5; border-radius: 6px; padding: 10px; margin: 0; }
    .metric-grid { display: grid; grid-template-columns: repeat(2, minmax(120px, 1fr)); gap: 8px; }
    .metric { background: #f7f8f5; border-radius: 6px; padding: 10px; }
    .metric b { display: block; font-size: 12px; color: #5a6255; margin-bottom: 3px; }
    .panel-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
    .panel-head h2 { margin: 0; }
    .panel-controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .inline-select { max-width: 150px; padding: 6px 8px; font-size: 13px; }
    ul { margin: 8px 0 0; padding-left: 18px; }
    @media (max-width: 840px) {
      header { align-items: flex-start; flex-direction: column; }
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid #d9ded4; }
      .pool-bar { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
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
  <main>
    <aside>
      <h2 data-i18n="addHolding">新增持仓</h2>
      <label data-i18n="symbol">股票代码</label>
      <input id="symbol" value="600519" oninput="onSymbolChanged()" onblur="hydrateSymbolFromMarket(false)">
      <label data-i18n="name">名称</label>
      <input id="name" value="" oninput="onNameChanged()">
      <label data-i18n="quantity">数量</label>
      <input id="quantity" type="number" value="100">
      <label data-i18n="costPrice">成本价</label>
      <input id="cost_price" type="number" value="95">
      <label data-i18n="stopLoss">止损价</label>
      <input id="stop_loss" type="number" value="88">
      <label data-i18n="takeProfit">止盈价</label>
      <input id="take_profit" type="number" value="120">
      <label data-i18n="thesis">买入理由</label>
      <textarea id="initial_thesis">Manual plan with mock data.</textarea>
      <div class="toolbar" style="margin-top:14px">
        <button onclick="addHolding()" data-i18n="add">添加</button>
        <button class="secondary" onclick="addSymbolToPool()" data-i18n="addToPool">加入股票池</button>
        <button class="secondary" onclick="hydrateSymbolFromMarket(true)" data-i18n="fetchQuote">查询行情</button>
        <button class="secondary" onclick="refreshAll()" data-i18n="refresh">刷新</button>
      </div>
      <p class="status" id="quoteStatus"></p>
    </aside>
    <section>
      <div class="pool-bar">
        <div>
          <label for="poolSelect" data-i18n="selectedPool">当前股票池</label>
          <select id="poolSelect" onchange="setSelectedPool(this.value)"></select>
        </div>
        <div>
          <label for="newPoolName" data-i18n="newPoolName">新股票池</label>
          <input id="newPoolName" data-i18n-placeholder="poolNamePlaceholder" placeholder="例如：短线观察">
        </div>
        <button class="secondary" onclick="createPool()" data-i18n="createPool">创建股票池</button>
        <button onclick="analyzePool()" data-i18n="analyzePool">分析当前池</button>
      </div>
      <div class="toolbar">
        <button class="secondary" onclick="generateSignals()" data-i18n="generatePoolSignals">生成今日信号</button>
        <button class="secondary" onclick="dailyReview()" data-i18n="dailyReview">每日复盘</button>
        <button class="secondary" onclick="runBacktest()" data-i18n="runBacktest">运行回测</button>
      </div>
      <div class="grid">
        <div class="panel">
          <h2 data-i18n="poolMembers">股票池</h2>
          <p class="status" id="poolHint"></p>
          <div id="watchlist"></div>
        </div>
        <div class="panel">
          <div class="panel-head">
            <h2 data-i18n="holdings">持仓</h2>
            <select class="inline-select" id="holdingScope" onchange="renderHoldings(cachedHoldings)">
              <option value="current" data-i18n="currentSymbol">当前股票</option>
              <option value="all" data-i18n="allSymbols">全部股票</option>
            </select>
          </div>
          <p class="status" id="holdingsHint"></p>
          <div id="holdings"></div>
        </div>
        <div class="panel">
          <div class="panel-head">
            <h2 data-i18n="signals">信号</h2>
            <div class="panel-controls">
              <select class="inline-select" id="signalScope" onchange="renderSignals(cachedSignals)">
                <option value="current" data-i18n="currentSymbol">当前股票</option>
                <option value="all" data-i18n="allSymbols">全部股票</option>
              </select>
              <select class="inline-select" id="signalView" onchange="renderSignals(cachedSignals)">
                <option value="latest" data-i18n="latestSignals">最新</option>
                <option value="history" data-i18n="historySignals">历史</option>
              </select>
            </div>
          </div>
          <p class="status" id="signalHint"></p>
          <div id="signals"></div>
        </div>
        <div class="panel">
          <h2 data-i18n="dailyReview">每日复盘</h2>
          <div id="review"></div>
        </div>
        <div class="panel">
          <h2 data-i18n="backtest">回测</h2>
          <div id="backtest"></div>
        </div>
      </div>
    </section>
  </main>
  <script>
    const translations = {
      zh: {
        appTitle: "通达信股票工作台",
        language: "语言",
        checking: "检查中...",
        running: "运行中",
        addHolding: "新增持仓",
        symbol: "股票代码",
        name: "名称",
        quantity: "数量",
        costPrice: "成本价",
        stopLoss: "止损价",
        takeProfit: "止盈价",
        thesis: "买入理由",
        add: "添加",
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
        mockSourceHint: "当前使用演示行情，名称和价格不代表真实市场。",
        officialSourceHint: "当前使用通达信官方 Token 数据源，需要本地配置 TDX_API_KEY。",
        realSourceHint: "当前使用通达信/真实行情源。若通达信 7709 连接失败，可临时切换 Eastmoney 兜底。",
        analyzePool: "分析当前池",
        generatePoolSignals: "生成今日信号",
        dailyReview: "每日复盘",
        runBacktest: "运行回测",
        holdings: "持仓",
        selectedPool: "当前股票池",
        newPoolName: "新股票池",
        poolNamePlaceholder: "例如：短线观察",
        createPool: "创建股票池",
        poolMembers: "股票池",
        poolHint: "当前分析范围由所选股票池决定。",
        signals: "信号",
        backtest: "回测",
        noData: "暂无数据。",
        generatedSignals: "已生成信号",
        poolAnalysisFailed: "股票池分析失败",
        mcpToolPlan: "MCP 工具计划",
        missingQuotes: "缺行情股票",
        failedSymbols: "失败股票",
        nextSteps: "下一步",
        savedHolding: "已保存持仓",
        updatedHolding: "已更新已有持仓",
        duplicateHoldingNote: "检测到相同股票代码，已更新原持仓，避免重复记录。",
        autoSignalCreated: "已为该股票自动生成最新信号",
        currentSymbol: "当前股票",
        allSymbols: "全部股票",
        currentHoldingsHint: "当前只显示输入框中股票的最新持仓。切换到全部股票可查看股票池。",
        allHoldingsHint: "正在显示股票池中每只股票最新一条持仓。",
        latestSignals: "最新",
        historySignals: "历史",
        currentLatestSignalsHint: "当前只显示输入框中股票的最新信号。",
        currentHistorySignalsHint: "当前只显示输入框中股票的最近历史信号。",
        allLatestSignalsHint: "正在显示股票池中每只股票最新一条信号。",
        allHistorySignalsHint: "正在显示最近保存的全股票池历史信号记录。",
        highRiskSymbols: "高风险股票",
        failedFetchCount: "数据拉取失败数",
        fetchOk: "未发现数据拉取失败",
        reviewedTemplate: "已复盘 {holdings} 条持仓和 {signals} 条近期信号。",
        highRiskSignalCount: "高风险信号数",
        nextFocus: "下一交易日重点",
        focus_review_high_risk: "优先复核高风险信号。",
        focus_check_data_quality: "确认行情/指标数据正常后再参考信号排序。",
        focus_compare_with_thesis: "把任何行动信号和原始买入理由再对照一次。",
        totalTrades: "交易次数",
        winRate: "胜率",
        riskReward: "盈亏比",
        totalReturn: "总收益率",
        maxDrawdown: "最大回撤",
        averageWin: "平均盈利",
        averageLoss: "平均亏损",
        mode: "模式",
        id: "ID",
        signal_type: "信号类型",
        action: "动作",
        risk_level: "风险",
        action_hint: "行动提示",
        price: "价格",
        created_at: "生成时间",
        cost_price: "成本价",
        stop_loss: "止损价",
        take_profit: "止盈价"
      },
      en: {
        appTitle: "Tongdaxin Stock Workbench",
        language: "Language",
        checking: "checking...",
        running: "running",
        addHolding: "Add Holding",
        symbol: "Symbol",
        name: "Name",
        quantity: "Quantity",
        costPrice: "Cost Price",
        stopLoss: "Stop Loss",
        takeProfit: "Take Profit",
        thesis: "Thesis",
        add: "Add",
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
        mockSourceHint: "Demo quotes are synthetic and do not represent the real market.",
        officialSourceHint: "Using the official Tongdaxin Token source. Local TDX_API_KEY is required.",
        realSourceHint: "Using Tongdaxin or a real market data source. If Tongdaxin 7709 fails, switch to Eastmoney fallback.",
        analyzePool: "Analyze Pool",
        generatePoolSignals: "Generate Signals",
        dailyReview: "Daily Review",
        runBacktest: "Run Backtest",
        holdings: "Holdings",
        selectedPool: "Current Pool",
        newPoolName: "New Pool",
        poolNamePlaceholder: "Example: Swing Watch",
        createPool: "Create Pool",
        poolMembers: "Stock Pool",
        poolHint: "The selected stock pool controls the analysis scope.",
        signals: "Signals",
        backtest: "Backtest",
        noData: "No data yet.",
        generatedSignals: "Generated signals",
        poolAnalysisFailed: "Pool analysis failed",
        mcpToolPlan: "MCP tool plan",
        missingQuotes: "Missing quotes",
        failedSymbols: "Failed symbols",
        nextSteps: "Next steps",
        savedHolding: "Holding saved",
        updatedHolding: "Existing holding updated",
        duplicateHoldingNote: "Same symbol detected; updated the existing holding to avoid duplicates.",
        autoSignalCreated: "A fresh signal was generated for this symbol",
        currentSymbol: "Current",
        allSymbols: "All Symbols",
        currentHoldingsHint: "Showing only the latest holding for the symbol in the input box.",
        allHoldingsHint: "Showing the latest holding per symbol in the portfolio.",
        latestSignals: "Latest",
        historySignals: "History",
        currentLatestSignalsHint: "Showing only the latest signal for the symbol in the input box.",
        currentHistorySignalsHint: "Showing recent historical signals for the symbol in the input box.",
        allLatestSignalsHint: "Showing the latest signal per symbol in the portfolio.",
        allHistorySignalsHint: "Showing recently saved historical signals across the portfolio.",
        highRiskSymbols: "High-risk symbols",
        failedFetchCount: "Failed fetches",
        fetchOk: "No failed data fetches",
        reviewedTemplate: "Reviewed {holdings} holdings and {signals} recent signals.",
        highRiskSignalCount: "High-risk signals",
        nextFocus: "Next session focus",
        focus_review_high_risk: "Review high-risk signals first.",
        focus_check_data_quality: "Confirm quote and indicator data before trusting signal rankings.",
        focus_compare_with_thesis: "Compare every action signal with the original position thesis.",
        totalTrades: "Total trades",
        winRate: "Win rate",
        riskReward: "Risk/reward",
        totalReturn: "Total return",
        maxDrawdown: "Max drawdown",
        averageWin: "Average win",
        averageLoss: "Average loss",
        mode: "mode",
        id: "ID",
        signal_type: "Signal Type",
        action: "Action",
        risk_level: "Risk",
        action_hint: "Action Hint",
        price: "Price",
        created_at: "Created At",
        cost_price: "Cost Price",
        stop_loss: "Stop Loss",
        take_profit: "Take Profit"
      }
    };
    const enumText = {
      zh: {
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
        low: "低",
        medium: "中",
        high: "高",
        complete_market_data: "补齐行情",
        review_stop_loss: "复核止损",
        review_take_profit: "复核止盈",
        hold_and_monitor: "持有观察",
        review_buy_zone: "复核买入区间",
        watch_pool_candidate: "观察候选股",
        observe: "观察",
        check_mcp_tool_errors: "检查 MCP 工具错误",
        review_stop_loss_first: "优先复核止损",
        review_take_profit_plan: "复核止盈计划",
        review_pool_candidates: "复核股票池候选"
      },
      en: {
        complete_market_data: "Complete market data",
        review_stop_loss: "Review stop loss",
        review_take_profit: "Review take profit",
        hold_and_monitor: "Hold and monitor",
        review_buy_zone: "Review buy zone",
        watch_pool_candidate: "Watch candidate",
        observe: "Observe",
        check_mcp_tool_errors: "Check MCP tool errors",
        review_stop_loss_first: "Review stop loss first",
        review_take_profit_plan: "Review take-profit plan",
        review_pool_candidates: "Review pool candidates"
      }
    };
    let currentLanguage = localStorage.getItem("tdx_language") || "zh";
    document.getElementById("languageSelect").value = currentLanguage;
    let currentMarketSource = localStorage.getItem("tdx_market_source") || "tongdaxin";
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
    }
    function setMarketSource(source) {
      currentMarketSource = source;
      localStorage.setItem("tdx_market_source", source);
      renderSourceStatus();
    }
    function numberValue(id) {
      const value = document.getElementById(id).value;
      return value === "" ? null : Number(value);
    }
    let cachedReview = null;
    let cachedBacktest = null;
    let cachedPools = [];
    let cachedWatchlist = [];
    let cachedHoldings = [];
    let cachedSignals = [];
    let autoNameValue = "";
    let nameEditedManually = false;

    async function checkHealth() {
      const health = await api("/health");
      document.getElementById("health").textContent = health.mode ? `${t("running")} (${t("mode")}: ${health.mode})` : t("running");
    }
    async function addHolding() {
      const quote = await hydrateSymbolFromMarket(false);
      if (!quote && marketSource() !== "mock") return;
      const payload = {
        symbol: document.getElementById("symbol").value,
        name: document.getElementById("name").value,
        market: "SH",
        quantity: numberValue("quantity"),
        cost_price: numberValue("cost_price"),
        stop_loss: numberValue("stop_loss"),
        take_profit: numberValue("take_profit"),
        max_loss_pct: 8,
        initial_thesis: document.getElementById("initial_thesis").value
      };
      const existing = cachedHoldings.find(row => row.symbol === payload.symbol.trim().toUpperCase());
      const saved = await api(existing ? `/holdings/${existing.id}` : "/holdings", {
        method: existing ? "PATCH" : "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      await generateHoldingSignal(saved.id);
      await ensureSymbolInPool();
      document.getElementById("holdingScope").value = "current";
      document.getElementById("signalScope").value = "current";
      const prefix = existing ? t("updatedHolding") + "。 " + t("duplicateHoldingNote") : t("savedHolding");
      document.getElementById("review").innerHTML = `<p class="summary">${prefix}。${t("autoSignalCreated")}。</p>`;
      await refreshAll();
    }
    async function createPool() {
      const name = document.getElementById("newPoolName").value.trim();
      if (!name) return;
      const pool = await api("/stock-pools", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name})
      });
      localStorage.setItem("tdx_pool_id", String(pool.id));
      document.getElementById("newPoolName").value = "";
      await refreshAll();
    }
    async function addSymbolToPool() {
      await ensureSymbolInPool();
      await refreshAll();
    }
    async function ensureSymbolInPool() {
      const quote = await hydrateSymbolFromMarket(false);
      const symbol = currentSymbol();
      if (!symbol || cachedWatchlist.some(row => normalizeSymbolText(row.symbol) === symbol)) return;
      await api("/watchlist", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          pool_id: selectedPoolId(),
          symbol,
          name: document.getElementById("name").value || quote?.payload?.name || quote?.name || "",
          thesis: document.getElementById("initial_thesis").value,
          priority: 3
        })
      });
    }
    async function generateHoldingSignal(holdingId) {
      return api(`/holdings/${holdingId}/signals/from-market`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({source: marketSource(), persist: true, include_technical: false})
      });
    }
    async function refreshAll() {
      await loadPools();
      cachedWatchlist = await api(`/watchlist?pool_id=${selectedPoolId() || ""}`);
      renderWatchlist(cachedWatchlist);
      cachedHoldings = await api("/holdings");
      renderHoldings(cachedHoldings);
      cachedSignals = await api("/signals");
      renderSignals(cachedSignals);
    }
    async function loadPools() {
      cachedPools = await api("/stock-pools");
      const select = document.getElementById("poolSelect");
      const savedPoolId = localStorage.getItem("tdx_pool_id");
      select.innerHTML = cachedPools.map(pool => `<option value="${pool.id}">${pool.name}</option>`).join("");
      const selected = cachedPools.find(pool => String(pool.id) === savedPoolId) || cachedPools[0];
      if (selected) {
        select.value = String(selected.id);
        localStorage.setItem("tdx_pool_id", String(selected.id));
      }
    }
    function setSelectedPool(poolId) {
      localStorage.setItem("tdx_pool_id", poolId);
      refreshAll();
    }
    function selectedPoolId() {
      const value = document.getElementById("poolSelect").value;
      return value ? Number(value) : null;
    }
    async function generateSignals() {
      const result = await api("/workbench/actions/from-market", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({source: marketSource(), persist: true, include_technical: false, pool_id: selectedPoolId()})
      });
      await refreshAll();
      document.getElementById("review").innerHTML = `<p class="summary">${t("generatedSignals")}: ${result.generated_signals}</p>`;
    }
    async function analyzePool() {
      const poolId = selectedPoolId();
      if (!poolId) return;
      document.getElementById("review").innerHTML = `<p class="summary">${t("checking")}</p>`;
      try {
        cachedReview = await api(`/stock-pools/${poolId}/mcp-analysis`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({persist: true, max_symbols: 30, include_profile: true})
        });
        renderPoolAnalysis(cachedReview);
      } catch (error) {
        document.getElementById("review").innerHTML = `<p class="status">${t("poolAnalysisFailed")}: ${escapeHtml(error.message)}</p>`;
      }
    }
    async function dailyReview() {
      cachedReview = await api(`/reports/daily-review?pool_id=${selectedPoolId() || ""}`);
      renderDailyReview(cachedReview);
    }
    async function runBacktest() {
      const symbol = document.getElementById("symbol").value || "600519";
      cachedBacktest = await api(`/backtests/${encodeURIComponent(symbol)}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({source: marketSource(), limit: 160, persist: true})
      });
      renderBacktest(cachedBacktest);
    }
    function renderHoldings(rows) {
      const scope = document.getElementById("holdingScope").value;
      const latestRows = latestBySymbol(filterByPoolSymbols(rows));
      const selectedRows = scope === "current" ? filterCurrentSymbol(latestRows) : latestRows;
      document.getElementById("holdingsHint").textContent = scope === "current" ? t("currentHoldingsHint") : t("allHoldingsHint");
      document.getElementById("holdings").innerHTML = table(selectedRows, ["id", "symbol", "name", "quantity", "cost_price", "stop_loss", "take_profit"]);
    }
    function renderSignals(rows) {
      const view = document.getElementById("signalView").value;
      const scope = document.getElementById("signalScope").value;
      const poolRows = filterByPoolSymbols(rows);
      const scopedRows = scope === "current" ? filterCurrentSymbol(poolRows) : poolRows;
      const selectedRows = view === "latest" ? latestBySymbol(scopedRows) : scopedRows.slice(0, 12);
      const hintKey = scope === "current"
        ? (view === "latest" ? "currentLatestSignalsHint" : "currentHistorySignalsHint")
        : (view === "latest" ? "allLatestSignalsHint" : "allHistorySignalsHint");
      document.getElementById("signalHint").textContent = t(hintKey);
      const mapped = selectedRows.map(row => ({
        ...row,
        signal_type: enumLabel(row.signal_type),
        action: enumLabel(row.action),
        risk_level: enumLabel(row.risk_level),
        created_at: shortTime(row.created_at)
      }));
      document.getElementById("signals").innerHTML = table(mapped, ["symbol", "signal_type", "action", "risk_level", "price", "created_at"]);
    }
    function renderWatchlist(rows) {
      document.getElementById("poolHint").textContent = t("poolHint");
      document.getElementById("watchlist").innerHTML = table(rows, ["symbol", "name", "priority", "status"]);
    }
    function onSymbolChanged() {
      syncAutoName();
      renderHoldings(cachedHoldings);
      renderSignals(cachedSignals);
    }
    function onNameChanged() {
      nameEditedManually = true;
    }
    function marketSource() {
      return document.getElementById("marketSourceSelect").value || "tongdaxin";
    }
    async function hydrateSymbolFromMarket(forceMessage) {
      const symbol = currentSymbol();
      if (!symbol) return null;
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
      return normalizeSymbolText(document.getElementById("symbol").value);
    }
    function filterCurrentSymbol(rows) {
      const symbol = currentSymbol();
      if (!symbol) return rows;
      return rows.filter(row => normalizeSymbolText(row.symbol) === symbol);
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
      const symbol = currentSymbol();
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
      const payload = report.payload || report;
      if (payload.report_type === "stock_pool_mcp_analysis") {
        renderPoolAnalysis(report);
        return;
      }
      const quality = payload.data_quality || {};
      const focusKeys = payload.next_session_focus_keys || ["review_high_risk", "check_data_quality", "compare_with_thesis"];
      const summary = t("reviewedTemplate")
        .replace("{holdings}", payload.holding_count ?? 0)
        .replace("{signals}", payload.signal_count ?? 0);
      const failedCount = quality.failed_fetch_count ?? 0;
      const fetchText = failedCount === 0 ? t("fetchOk") : failedCount;
      document.getElementById("review").innerHTML = `
        <p class="summary">${summary}</p>
        <div class="metric-grid" style="margin-top:10px">
          <div class="metric"><b>${t("highRiskSymbols")}</b>${(payload.high_risk_symbols || []).join(", ") || "-"}</div>
          <div class="metric"><b>${t("highRiskSignalCount")}</b>${payload.high_risk_signal_count ?? 0}</div>
          <div class="metric"><b>${t("failedFetchCount")}</b>${fetchText}</div>
        </div>
        <p class="status" style="margin-top:12px">${t("nextFocus")}</p>
        <ul>${focusKeys.map(key => `<li>${t("focus_" + key)}</li>`).join("")}</ul>
      `;
    }
    function renderPoolAnalysis(report) {
      const payload = report.payload || report;
      const quality = payload.data_quality || {};
      const plan = payload.tool_plan || {};
      const rows = (payload.items || []).map(item => ({
        symbol: item.symbol,
        name: item.name || "",
        action_hint: enumLabel(item.action_hint),
        price: item.mcp_calls?.quote?.fields?.price ?? ""
      }));
      document.getElementById("review").innerHTML = `
        <p class="summary">${escapeHtml(payload.summary || "")}</p>
        <div class="metric-grid" style="margin-top:10px">
          <div class="metric"><b>${t("mcpToolPlan")}</b>${escapeHtml(plan.quote_tool || "-")} / ${escapeHtml(plan.profile_tool || "-")}</div>
          <div class="metric"><b>${t("missingQuotes")}</b>${quality.missing_quote_count ?? 0}</div>
          <div class="metric"><b>${t("failedSymbols")}</b>${(quality.failed_symbols || []).join(", ") || "-"}</div>
          <div class="metric"><b>${t("nextSteps")}</b>${(payload.next_steps || []).map(enumLabel).join(", ") || "-"}</div>
        </div>
        <div style="margin-top:12px">${table(rows, ["symbol", "name", "action_hint", "price"])}</div>
      `;
    }
    function renderBacktest(result) {
      const metrics = result.result.metrics;
      document.getElementById("backtest").innerHTML = `
        <div class="metric-grid">
          ${metric("totalTrades", metrics.total_trades)}
          ${metric("winRate", percent(metrics.win_rate))}
          ${metric("riskReward", metrics.risk_reward_ratio ?? "-")}
          ${metric("totalReturn", percent(metrics.total_return_pct / 100))}
          ${metric("maxDrawdown", `${metrics.max_drawdown_pct}%`)}
          ${metric("averageWin", `${metrics.average_win_pct}%`)}
          ${metric("averageLoss", `${metrics.average_loss_pct}%`)}
        </div>
      `;
    }
    function metric(labelKey, value) {
      return `<div class="metric"><b>${t(labelKey)}</b>${value}</div>`;
    }
    function percent(value) {
      if (value === null || value === undefined) return "-";
      return `${(Number(value) * 100).toFixed(2)}%`;
    }
    function formatPrice(value) {
      if (value === null || value === undefined || value === "") return "-";
      return Number(value).toFixed(2);
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
      return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
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
      renderWatchlist(cachedWatchlist);
      renderHoldings(cachedHoldings);
      renderSignals(cachedSignals);
      if (cachedReview) renderDailyReview(cachedReview);
      if (cachedBacktest) renderBacktest(cachedBacktest);
    }
    setLanguage(currentLanguage);
    checkHealth().then(refreshAll).catch(error => {
      document.getElementById("health").textContent = error.message;
    });
  </script>
</body>
</html>"""
