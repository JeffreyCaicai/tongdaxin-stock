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
      min-width: 0;
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
    @media (max-width:700px) { .opportunity-columns { grid-template-columns:1fr; gap:10px; } }
    .decision-overview table { table-layout: fixed; }
    .decision-overview th, .decision-overview td { overflow-wrap: anywhere; }
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
      .decision-overview table, .decision-overview tbody { display: block; }
      .decision-overview thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
      .decision-overview tr { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-bottom: 1px solid var(--line); }
      .decision-overview td { display: block; border: 0; min-width: 0; padding: 8px 4px; }
      .decision-overview td::before { content: attr(data-label); display: block; color: var(--text-muted); font-size: 11px; margin-bottom: 3px; }
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
      .action-bar { align-items: stretch; }
      .action-bar button { flex: 1 1 auto; }
      .holdings-summary { grid-template-columns: 1fr; }
      .grid { grid-template-columns: minmax(0, 1fr); }
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
        <button onclick="runOpportunities()" data-i18n="marketOpportunities">市场机会推荐</button>
        <button class="secondary" onclick="openOpportunityHistory()" data-i18n="opportunityHistory">推荐记录</button>
        <button onclick="runDecisionEngine()" data-i18n="runDecisionEngine">持仓决策引擎</button>
        <button onclick="analyzePool()" data-i18n="analyzePool">分析股票池行情</button>
        <button class="secondary" onclick="runChanAnalysis()" data-i18n="runChanAnalysis">缠论结构分析</button>
        <button class="secondary" onclick="dailyReview()" data-i18n="dailyReview">生成复盘</button>
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
      outside_stock_scope:"不在A股个股范围内",
      queued:"排队中", running:"运行中", completed:"已完成", cancelled:"已取消", interrupted:"已中断", failed:"失败",
      opportunityReconnect:"进度连接暂时中断，正在重试", opportunityResume:"重新连接进度",
      marketOpportunities:"市场机会推荐", opportunityHistory:"推荐记录", opportunityTitle:"市场机会推荐 · 20交易日",
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
      outside_stock_scope:"Outside the A-share stock scope",
      queued:"Queued", running:"Running", completed:"Completed", cancelled:"Cancelled", interrupted:"Interrupted", failed:"Failed",
      opportunityReconnect:"Progress connection interrupted; retrying", opportunityResume:"Reconnect to scan",
      marketOpportunities:"Market Opportunities", opportunityHistory:"Recommendation History", opportunityTitle:"Market Opportunities · 20 sessions",
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
      document.getElementById("review").innerHTML = `<p class="status">${escapeHtml(t(analysisStatus.key))}${analysisStatus.message ? `: ${escapeHtml(analysisStatus.message)}` : ""}</p>`;
    }
    async function requestAnalysis(path, options, renderer, errorKey) {
      invalidateAnalysis();
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
      if (!selectedPoolId()) return;
      return requestAnalysis(`/stock-pools/${selectedPoolId()}/opportunities?source=${encodeURIComponent(marketSource())}`, {}, renderOpportunityHistory, "opportunityFailed");
    }
    function renderOpportunityHistory(rows) {
      cachedReview = {report_type:"opportunity_history", rows};
      document.getElementById("review").innerHTML = `<h3>${t("opportunityHistory")}</h3>${rows.length ? rows.map(row => `<p><button class="secondary" onclick="openOpportunityRun('${row.id}')">${escapeHtml(shortTime(row.created_at))}</button> ${escapeHtml(t(row.status))}</p>`).join("") : `<p>${t("noData")}</p>`}`;
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
      document.getElementById("review").innerHTML = `<h3>${t("opportunityTitle")}</h3>
        <p class="status">${escapeHtml(report.source)} · ${escapeHtml(shortTime(report.generated_at))} · ${escapeHtml(report.benchmark)} ${d.is_demo ? ` · ${t("opportunityDemo")}` : ""}</p>
        <div class="opportunity-summary">${[[scope.new,"opportunityCandidates"],[scope.personal,"opportunityPersonal"],[scope.recommended,"opportunitySelected"],[scope.excluded,"opportunityExcluded"]].map(([n,key]) => `<div><strong>${n ?? 0}</strong><span>${t(key)}</span></div>`).join("")}</div>
        <p class="status">${t("opportunityTechnical")}</p>
        ${d.errors?.length || report.failures?.length ? `<p role="status">${t("opportunityPartial")}</p>` : ""}
        <div class="toolbar"><select id="opportunity-origin" aria-label="${t("opportunityOrigin")}" onchange="renderOpportunityRows()"><option value="all">${t("opportunityAny")}</option>${["new","watched","held"].map(v=>`<option value="${v}">${opportunityLabel(v)}</option>`).join("")}</select>
          <select id="opportunity-view" aria-label="${t("opportunityAll")}" onchange="renderOpportunityRows()"><option value="top">${t("opportunityTop")}</option><option value="all">${t("opportunityAll")} (${scope.analyzed || 0})</option></select></div>
        <div id="opportunity-rows"></div>
        <details class="stock-detail"><summary>${t("opportunityCoverage")}</summary>
          <p>${t("opportunityScope")} · ${d.candidate_count || 0} / ${scope.analyzed || 0}</p>
          ${(d.queries || []).map(q=>`<p>${escapeHtml(q.query)}<br>${currentLanguage === "zh" ? "读取 / 返回总数" : "Read / reported total"}: ${q.rows_read} / ${q.total}${q.truncated ? (currentLanguage === "zh" ? " · 部分读取" : " · partial") : ""}</p>`).join("")}
          ${(d.errors || []).map(e=>`<p>${escapeHtml(e.theme)}: ${opportunityLabel(e.reason)}</p>`).join("")}
          ${(report.failures || []).map(e=>`<p>${escapeHtml(e.symbol)}: ${opportunityLabel(e.kind)}</p>`).join("")}
          <p>${t("opportunityRefresh")}</p></details>`;
      renderOpportunityRows(report);
    }
    function renderOpportunityRows(provided) {
      const report = provided || cachedReview?.result;
      if (!report) return;
      const origin = document.getElementById("opportunity-origin").value || "all";
      const all = document.getElementById("opportunity-view").value === "all";
      const rows = (report.items || []).filter(item => (all || report.selected.includes(item.symbol)) && (origin === "all" || item.origin === origin));
      document.getElementById("opportunity-rows").innerHTML = rows.length ? rows.map(item => {
        const reasons = (item.selection_reasons || []).map(opportunityLabel);
        const opposition = (item.opposing_evidence || []).slice(0,2).map(e => `${e.source}: ${e.observation}`);
        const support = (item.supporting_evidence || []).slice(0,3).map(e => `${e.source}: ${e.observation}`);
        const c = item.conditions || {}, p = item.probabilities || {};
        const added = cachedWatchlist.some(row => opportunityIdentity(row.symbol) === opportunityIdentity(item.symbol));
        return `<article class="opportunity-row" data-level="${escapeHtml(item.level)}">
          <div class="opportunity-head"><h3>${escapeHtml(item.name || item.symbol)} <small>${escapeHtml(item.symbol)} · ${opportunityLabel(item.origin)}</small></h3>
            <span class="opportunity-grade">${opportunityLabel(item.level)} · ${t("opportunityScore")} ${item.rank_score}</span>
            <span>${formatPrice(item.current_price)} <small>${t("opportunityAsOf")} ${escapeHtml(item.data_quality?.kline_as_of || "-")}</small></span></div>
          <div class="opportunity-columns"><div><h4>${t("opportunityBasis")}</h4>${support.map(s=>`<p>${escapeHtml(s)}</p>`).join("") || `<p>${t("weak_evidence")}</p>`}</div>
            <div><h4>${t("opportunityRisk")}</h4><p>${t("risk_level")}: ${escapeHtml(enumLabel(item.decision?.risk_level))} · ${t("confidence")}: ${escapeHtml(enumLabel(item.decision?.confidence))}</p>${[...reasons,...opposition].map(s=>`<p>${escapeHtml(s)}</p>`).join("") || `<p>${t("opportunityNoOpposition")}</p>`}</div>
            <div><h4>${t("opportunityConditions")}</h4><p>MA20 ${formatPrice(c.ma20)} · ATR14 ${formatPrice(c.atr14)}</p>
              ${item.level === "excluded" ? `<p>${t("opportunityInvalid")}</p>` : `<p>${t("opportunityConfirm")}</p><p>${t("opportunityInvalidation")}: ${formatPrice(c.review_below)}</p>`}
              <div class="opportunity-score" title="${escapeHtml(scoreVector(p))}">${[[p.up,"#b34848"],[p.range,"#b09236"],[p.down,"#328172"]].map(([v,color])=>`<i style="width:${Math.max(0, Math.min(100, (v || 0)*100))}%;background:${color}"></i>`).join("")}</div><p>${escapeHtml(scoreVector(p))}</p></div></div>
          ${decisionDetails(item)}
          ${item.origin === "new" ? `<button class="secondary" ${added ? "disabled" : ""} onclick="addOpportunity('${escapeHtml(item.symbol)}',this)">${t(added ? "opportunityAdded" : "opportunityAdd")}</button>` : ""}
        </article>`;
      }).join("") : `<p class="status">${t("opportunityEmpty")}</p>`;
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
      const poolId = selectedPoolId();
      if (!poolId) return;
      return requestAnalysis(`/stock-pools/${poolId}/market-analysis`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({source: marketSource(), persist: true, max_symbols: 30})
        }, renderPoolAnalysis, "poolAnalysisFailed");
    }
    async function runChanAnalysis() {
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
    function renderDecisionEngine(report, savedContext = null) {
      const payload = report.payload || report;
      const quality = payload.data_quality || {};
      const counts = payload.scenario_counts || {};
      const regime = payload.market_regime || {};
      const scenarioCounts = ["up", "range", "down"]
        .map(key => `${enumLabel(key)} ${counts[key] ?? 0}`)
        .join(", ");
      const regimeEvidence = (regime.evidence || [])
        .slice(0, 3)
        .map(entry => `${entry.source || ""}: ${entry.observation || ""}`)
        .filter(Boolean);
      const rows = (payload.items || []).map(item => {
        const probabilities = item.probabilities || {};
        const decision = item.decision || {};
        return {
          symbol: item.symbol,
          name: item.name || "",
          current_price: formatOptionalPrice(item.current_price),
          up_probability: formatProbability(probabilities.up),
          range_probability: formatProbability(probabilities.range),
          down_probability: formatProbability(probabilities.down),
          decision: enumLabel(decision.key) || decision.label || "",
          risk_level: enumLabel(decision.risk_level),
          confidence: enumLabel(decision.confidence)
        };
      });
      const failedQuotes = quality.failed_quote_symbols || [];
      const failedKlines = quality.failed_kline_symbols || [];
      const calibration = payload.calibration?.status || payload.calibration || "uncalibrated";
      const model = payload.model_version || payload.model || payload.scope?.model || t("unavailable");
      const comparison = payload.comparison || report.comparison;
      document.getElementById("review").innerHTML = `
        ${savedContext ? `<p class="status">${t("savedAnalysis")} · ${t("analysisReportId")}: ${escapeHtml(savedContext.reportId ?? "-")}
          · ${t("analysisGeneratedAt")}: ${escapeHtml(savedContext.generatedAt || t("unavailable"))}</p>` : ""}
        <p class="summary">${escapeHtml(payload.summary || "")}</p>
        <p class="status">${t("decisionEngineModel")}: ${escapeHtml(model)} · ${calibration === "uncalibrated" ? t("uncalibrated") : `${t("calibrationStatus")}: ${escapeHtml(calibration)}`}</p>
        <div class="metric-grid" style="margin-top:10px">
          <div class="metric"><b>${t("marketRegime")}</b>${escapeHtml(enumLabel(regime.regime) || regime.label || "-")}</div>
          <div class="metric"><b>${t("regimeConfidence")}</b>${escapeHtml(enumLabel(regime.confidence) || "-")}</div>
          <div class="metric"><b>${t("strategyBias")}</b>${escapeHtml(regime.strategy_bias?.summary || "-")}</div>
          <div class="metric"><b>${t("horizonDays")}</b>${escapeHtml(String(payload.scope?.horizon_days || "-"))}</div>
          <div class="metric"><b>${t("scenarioCounts")}</b>${escapeHtml(scenarioCounts || "-")}</div>
          <div class="metric"><b>${t("failedSymbols")}</b>${escapeHtml([...failedQuotes, ...failedKlines].join(", ") || "-")}</div>
        </div>
        <p class="status" style="margin-top:12px">${t("regimeEvidence")}</p>
        <ul>${regimeEvidence.map(item => `<li>${escapeHtml(item)}</li>`).join("") || `<li>${escapeHtml("-")}</li>`}</ul>
        <h3>${t("scenarioScores")}</h3>
        ${decisionOverview(rows)}
        ${(payload.items || []).map(item => decisionDetails(item, comparison)).join("")}
        ${quality.unavailable_evidence?.length ? `<h3>${t("dataQuality")}</h3><ul>${quality.unavailable_evidence.map(value => `<li>${escapeHtml(value)}</li>`).join("")}</ul>` : ""}
        <p class="status" style="margin-top:12px">${t("nextSteps")}</p>
        <ul>${(payload.next_steps || []).map(step => `<li>${escapeHtml(step)}</li>`).join("")}</ul>
      `;
    }
    function decisionOverview(rows) {
      if (!rows.length) return `<p class="status">${t("noData")}</p>`;
      const fields = ["symbol", "name", "current_price", "up_probability", "range_probability", "down_probability", "decision", "risk_level", "confidence"];
      return `<div class="decision-overview"><table aria-label="${escapeHtml(t("scenarioScores"))}">
        <thead><tr>${fields.map(field => `<th scope="col">${escapeHtml(t(field))}</th>`).join("")}</tr></thead>
        <tbody>${rows.map(row => `<tr>${fields.map(field => `<td data-label="${escapeHtml(t(field))}">${escapeHtml(row[field] || "-")}</td>`).join("")}</tr>`).join("")}</tbody>
      </table></div>`;
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
    function decisionDetails(item, comparison) {
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
      return `<details class="stock-detail"><summary>${escapeHtml(item.symbol)} · ${escapeHtml(item.name || "-")} · ${t("stockDetails")}</summary>
        <div class="detail-grid">
          <div><h3>${t("evidence")}</h3><ul class="evidence-list">${evidence || `<li>${t("unavailable")}</li>`}</ul>
            ${detailFields([["pnl_pct", formatPercent(item.position?.pnl_pct) || "-"], ["trigger", decision.trigger || item.chan?.trigger], ["next_check", decision.next_check]])}
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
      renderWatchlist(cachedWatchlist);
      renderHoldings(cachedHoldings);
      if (cachedReview) renderDailyReview(cachedReview);
      else renderAnalysisStatus();
    }
    setLanguage(currentLanguage);
    checkHealth().then(refreshAll).catch(error => {
      document.getElementById("health").textContent = error.message;
    });
  </script>
</body>
</html>"""
