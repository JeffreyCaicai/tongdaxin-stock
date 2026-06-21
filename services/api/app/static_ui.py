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
      background: #f3f5f0;
      color: #20231f;
      --surface: #ffffff;
      --surface-muted: #f7f8f5;
      --line: #d9ded4;
      --line-strong: #c1cbbd;
      --text-muted: #5a6255;
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
      grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
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
    section { padding: 22px 28px 28px; }
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
    .header-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
    .action-bar {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 12px;
    }
    .pool-actions {
      margin: 0;
      align-items: center;
      justify-content: flex-start;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
      gap: 16px;
      align-items: start;
    }
    .panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 16px;
      min-height: 160px;
      box-shadow: 0 1px 2px rgba(31, 42, 35, 0.03);
    }
    .analysis-panel {
      grid-column: 1 / -1;
      min-height: 360px;
      border-color: var(--line-strong);
    }
    .analysis-panel h2 { font-size: 18px; }
    .analysis-panel .table-scroll table { min-width: 1180px; }
    .backtest-panel { grid-column: 1 / -1; }
    .panel-subtitle {
      margin: -2px 0 12px;
      color: var(--text-muted);
      font-size: 13px;
    }
    .table-scroll { overflow-x: auto; }
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
    .status { font-size: 13px; color: var(--text-muted); }
    .summary {
      background: var(--accent-soft);
      border-left: 3px solid var(--accent);
      border-radius: 6px;
      padding: 11px 12px;
      margin: 0;
      font-weight: 600;
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
      .grid { grid-template-columns: 1fr; }
      .analysis-panel,
      .backtest-panel { grid-column: auto; }
    }
    @media (max-width: 840px) {
      header { align-items: flex-start; flex-direction: column; }
      main { grid-template-columns: 1fr; }
      aside {
        border-right: 0;
        border-bottom: 1px solid var(--line);
        position: static;
        height: auto;
      }
      section { padding: 16px; }
      .action-bar { align-items: stretch; }
      .action-bar button { flex: 1 1 auto; }
      .holdings-summary { grid-template-columns: 1fr; }
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
      <h2 data-i18n="addWatchSymbol">添加关注股</h2>
      <label data-i18n="symbolOrName">股票代码或名称</label>
      <input id="symbol" value="" data-i18n-placeholder="symbolOrNamePlaceholder" placeholder="例如：600519 / 贵州茅台" oninput="onSymbolChanged()" onblur="hydrateSymbolFromMarket(false)">
      <label data-i18n="nameOptional">名称</label>
      <input id="name" value="" data-i18n-placeholder="nameOptionalPlaceholder" placeholder="可选，查询后自动填充" oninput="onNameChanged()">
      <div class="toolbar" style="margin-top:14px">
        <button onclick="addSymbolToPool()" data-i18n="addWatchSymbolButton">添加关注</button>
        <button class="secondary" onclick="hydrateSymbolFromMarket(true)" data-i18n="fetchQuote">查询行情</button>
        <button class="secondary" onclick="refreshAll()" data-i18n="refresh">刷新</button>
      </div>
      <p class="status" id="quoteStatus"></p>
    </aside>
    <section>
      <div class="action-bar toolbar pool-actions">
        <button onclick="analyzePool()" data-i18n="analyzePool">分析股票池行情</button>
        <button class="secondary" onclick="runChanAnalysis()" data-i18n="runChanAnalysis">缠论结构分析</button>
        <button class="secondary" onclick="dailyReview()" data-i18n="dailyReview">生成复盘</button>
        <button class="secondary" onclick="runBacktest()" data-i18n="runBacktest">MA/成交量回测</button>
      </div>
      <p class="status" id="actionStatus"></p>
      <div class="grid">
        <div class="panel analysis-panel">
          <h2 data-i18n="analysisResult">分析结果</h2>
          <p class="panel-subtitle" data-i18n="analysisResultFocus">这里优先显示股票池级分析、缠论结构和每日复盘明细。</p>
          <div id="review"><p class="status" data-i18n="analysisResultHint">这里显示股票池行情分析或每日复盘结果。</p></div>
        </div>
        <div class="panel watchlist-panel">
          <h2 data-i18n="poolMembers">股票池</h2>
          <p class="status" id="poolHint"></p>
          <div id="watchlist"></div>
        </div>
        <div class="panel holdings-panel">
          <h2 data-i18n="holdings">持仓</h2>
          <p class="status" id="holdingsHint"></p>
          <div id="holdings"></div>
        </div>
        <div class="panel backtest-panel">
          <h2 data-i18n="backtestTool">MA/成交量回测</h2>
          <div id="backtest"><p class="status" data-i18n="backtestHint">使用左侧输入框中的股票代码，按日 K 线跑一套固定的 MA/成交量趋势规则。</p></div>
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
        runBacktest: "MA/成交量回测",
        holdings: "持仓",
        poolMembers: "股票池",
        poolHint: "这里是你的关注名单，行情分析范围由个人股票池决定。",
        signals: "信号",
        analysisResult: "分析结果",
        analysisResultFocus: "这里优先显示股票池级分析、缠论结构和每日复盘明细。",
        analysisResultHint: "这里显示股票池行情分析或每日复盘结果。",
        backtest: "回测",
        backtestTool: "MA/成交量回测",
        backtestHint: "使用左侧输入框中的股票代码，按日 K 线跑一套固定的 MA/成交量趋势规则。",
        backtestStrategy: "策略",
        backtestDataWindow: "K线数量",
        backtestRuleTitle: "当前规则",
        backtestEntryRule: "买入：收盘价站上 MA20，且 MA5 ≥ MA20，趋势不为空头，成交量比 ≥ 1。",
        backtestExitRule: "卖出：亏损达到 {stop}% 止损，盈利达到 {take}% 止盈，或收盘价跌破 MA20 且 MA5 < MA20。",
        backtestAssumption: "这是固定规则的历史模拟，不包含滑点、手续费、仓位管理和人工判断。",
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
        totalTrades: "交易次数",
        winRate: "胜率",
        riskReward: "盈亏比",
        totalReturn: "总收益率",
        maxDrawdown: "最大回撤",
        averageWin: "平均盈利",
        averageLoss: "平均亏损",
        mode: "模式",
        id: "ID",
        priority: "优先级",
        status: "状态",
        source: "来源",
        data_type: "数据类型",
        message: "信息",
        fetched_at: "拉取时间",
        strength: "强度",
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
        next_check: "下一步检查",
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
        runBacktest: "MA/Volume Backtest",
        holdings: "Holdings",
        poolMembers: "Stock Pool",
        poolHint: "This is your watchlist. The personal stock pool controls the quote analysis scope.",
        signals: "Signals",
        analysisResult: "Analysis Result",
        analysisResultFocus: "Pool analysis, Chan structure, and daily review details appear here first.",
        analysisResultHint: "Pool quote analysis and daily review results appear here.",
        backtest: "Backtest",
        backtestTool: "MA/Volume Backtest",
        backtestHint: "Uses the symbol in the left input and runs a fixed MA/volume trend rule over daily K-line bars.",
        backtestStrategy: "Strategy",
        backtestDataWindow: "Bars",
        backtestRuleTitle: "Current rules",
        backtestEntryRule: "Entry: close is above MA20, MA5 >= MA20, trend is not bearish, and volume ratio >= 1.",
        backtestExitRule: "Exit: stop loss at {stop}%, take profit at {take}%, or close below MA20 with MA5 < MA20.",
        backtestAssumption: "This is a fixed-rule historical simulation. It does not include slippage, fees, position sizing, or manual judgment.",
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
        totalTrades: "Total trades",
        winRate: "Win rate",
        riskReward: "Risk/reward",
        totalReturn: "Total return",
        maxDrawdown: "Max drawdown",
        averageWin: "Average win",
        averageLoss: "Average loss",
        mode: "mode",
        id: "ID",
        priority: "Priority",
        status: "Status",
        source: "Source",
        data_type: "Data Type",
        message: "Message",
        fetched_at: "Fetched At",
        strength: "Strength",
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
        wait_for_structure: "等待结构",
        trend_observe: "趋势观察",
        center_range: "中枢震荡",
        suspected_third_buy: "疑似三买",
        upward_leave: "向上离开中枢",
        suspected_third_sell: "疑似三卖",
        downward_leave: "向下离开中枢",
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
        low: "Low",
        medium: "Medium",
        high: "High",
        complete_market_data: "Complete market data",
        wait_for_structure: "Wait for structure",
        trend_observe: "Trend observation",
        center_range: "Center range",
        suspected_third_buy: "Possible third buy",
        upward_leave: "Upward leave",
        suspected_third_sell: "Possible third sell",
        downward_leave: "Downward leave",
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
      refreshAll().catch(error => {
        document.getElementById("quoteStatus").textContent = error.message;
      });
    }
    let cachedReview = null;
    let cachedBacktest = null;
    let cachedPools = [];
    let cachedWatchlist = [];
    let cachedHoldings = [];
    let holdingRenderSeq = 0;
    let autoNameValue = "";
    let nameEditedManually = false;

    async function checkHealth() {
      const health = await api("/health");
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
    async function analyzePool() {
      const poolId = selectedPoolId();
      if (!poolId) return;
      document.getElementById("actionStatus").textContent = "";
      document.getElementById("review").innerHTML = `<p class="summary">${t("checking")}</p>`;
      try {
        cachedReview = await api(`/stock-pools/${poolId}/market-analysis`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({source: marketSource(), persist: true, max_symbols: 30})
        });
        renderPoolAnalysis(cachedReview);
      } catch (error) {
        document.getElementById("review").innerHTML = `<p class="status">${t("poolAnalysisFailed")}: ${escapeHtml(error.message)}</p>`;
      }
    }
    async function runChanAnalysis() {
      const poolId = selectedPoolId();
      if (!poolId) return;
      document.getElementById("actionStatus").textContent = "";
      document.getElementById("review").innerHTML = `<p class="summary">${t("checking")}</p>`;
      try {
        cachedReview = await api(`/stock-pools/${poolId}/chan-analysis`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            source: marketSource(),
            period: "daily",
            persist: true,
            max_symbols: 30,
            kline_limit: 240
          })
        });
        renderChanAnalysis(cachedReview);
      } catch (error) {
        document.getElementById("review").innerHTML = `<p class="status">${t("chanAnalysisFailed")}: ${escapeHtml(error.message)}</p>`;
      }
    }
    async function dailyReview() {
      document.getElementById("actionStatus").textContent = "";
      cachedReview = await api(`/reports/daily-review?pool_id=${selectedPoolId() || ""}`);
      renderDailyReview(cachedReview);
    }
    async function runBacktest() {
      document.getElementById("actionStatus").textContent = "";
      const symbol = document.getElementById("symbol").value || "600519";
      cachedBacktest = await api(`/backtests/${encodeURIComponent(symbol)}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({source: marketSource(), limit: 160, persist: true})
      });
      renderBacktest(cachedBacktest);
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
        const currentPrice = Number(quote.price);
        const marketValue = quantity * currentPrice;
        const estimatedPnl = quantity * (currentPrice - costPrice);
        const estimatedPnlPct = costPrice > 0 ? ((currentPrice - costPrice) / costPrice) * 100 : null;
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
      return `
        <div class="holdings-summary">
          ${summaryStat("total_cost_basis", formatMoney(summary.totalCost))}
          ${summaryStat("total_market_value", formatMoney(summary.totalMarketValue))}
          ${summaryStat("total_estimated_pnl", formatMoney(summary.totalPnl), pnlClass(summary.totalPnl))}
          ${summaryStat("total_estimated_pnl_pct", formatPercent(summary.totalPnlPct), pnlClass(summary.totalPnl))}
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
        const currentPrice = Number(row.current_price);
        if (Number.isFinite(quantity) && Number.isFinite(costPrice)) {
          summary.totalCost += quantity * costPrice;
        }
        if (Number.isFinite(quantity) && Number.isFinite(costPrice) && Number.isFinite(currentPrice)) {
          const costBasis = quantity * costPrice;
          const marketValue = quantity * currentPrice;
          summary.pricedCost += costBasis;
          summary.totalMarketValue += marketValue;
          summary.totalPnl += marketValue - costBasis;
          summary.pricedCount += 1;
        }
        return summary;
      }, {totalCost: 0, pricedCost: 0, pricedCount: 0, totalMarketValue: 0, totalPnl: 0, totalPnlPct: null});
      if (!summary.pricedCount) {
        summary.totalMarketValue = null;
        summary.totalPnl = null;
        return summary;
      }
      summary.totalPnlPct = summary.pricedCost > 0 ? (summary.totalPnl / summary.pricedCost) * 100 : null;
      return summary;
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
      const payload = report.payload || report;
      if (["stock_pool_mcp_analysis", "stock_pool_market_analysis"].includes(payload.report_type)) {
        renderPoolAnalysis(report);
        return;
      }
      if (payload.report_type === "stock_pool_chan_analysis") {
        renderChanAnalysis(report);
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
      const quality = payload.data_quality || {};
      const signalCounts = Object.entries(payload.signal_counts || {})
        .map(([key, value]) => `${enumLabel(key)} ${value}`)
        .join(", ") || "-";
      const rows = (payload.items || []).map(item => {
        const signal = item.signal || {};
        const center = item.latest_center || null;
        return {
          symbol: item.symbol,
          name: item.name || "",
          structure: item.structure || "",
          chanSignal: enumLabel(signal.type) || signal.label || "",
          action: signal.action || "",
          confidence: enumLabel(signal.confidence),
          current_price: formatOptionalPrice(item.current_price),
          center_range: center ? `${formatOptionalPrice(center.lower)} - ${formatOptionalPrice(center.upper)}` : "-",
          trigger: signal.trigger || "-",
          invalidation: signal.invalidation || "-",
          reason: signal.reason || "",
          bar_count: item.bar_count ?? 0,
          stroke_count: item.stroke_count ?? 0,
          center_count: item.center_count ?? 0
        };
      });
      document.getElementById("review").innerHTML = `
        <p class="summary">${escapeHtml(payload.summary || "")}</p>
        <div class="metric-grid" style="margin-top:10px">
          <div class="metric"><b>${t("marketDataSource")}</b>${escapeHtml(payload.tool_plan?.data_source || "-")}</div>
          <div class="metric"><b>${t("chanPeriod")}</b>${escapeHtml(payload.scope?.period || "-")}</div>
          <div class="metric"><b>${t("chanSignalCounts")}</b>${escapeHtml(signalCounts)}</div>
          <div class="metric"><b>${t("failedSymbols")}</b>${(quality.failed_symbols || []).join(", ") || "-"}</div>
        </div>
        <div style="margin-top:12px">${table(rows, [
          "symbol",
          "name",
          "structure",
          "chanSignal",
          "action",
          "confidence",
          "current_price",
          "center_range",
          "trigger",
          "invalidation",
          "reason",
          "bar_count",
          "stroke_count",
          "center_count"
        ])}</div>
      `;
    }
    function renderBacktest(result) {
      const metrics = result.result.metrics;
      const rules = result.result.rules || {};
      const stop = rules.stop_loss_pct ?? result.config?.stop_loss_pct ?? 6;
      const take = rules.take_profit_pct ?? result.config?.take_profit_pct ?? 12;
      document.getElementById("backtest").innerHTML = `
        <p class="summary">${t("backtestStrategy")}: ${escapeHtml(result.strategy_name || result.result.strategy_name || "-")}</p>
        <div class="metric-grid" style="margin-top:10px">
          <div class="metric"><b>${t("marketDataSource")}</b>${escapeHtml(result.source || "-")}</div>
          <div class="metric"><b>${t("backtestDataWindow")}</b>${result.result.bar_count ?? "-"}</div>
        </div>
        <p class="status" style="margin-top:12px">${t("backtestRuleTitle")}</p>
        <ul>
          <li>${t("backtestEntryRule")}</li>
          <li>${t("backtestExitRule").replace("{stop}", stop).replace("{take}", take)}</li>
        </ul>
        <p class="status">${t("backtestAssumption")}</p>
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
      renderWatchlist(cachedWatchlist);
      renderHoldings(cachedHoldings);
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
