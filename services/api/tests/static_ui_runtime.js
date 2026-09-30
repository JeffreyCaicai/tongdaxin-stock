const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const script = fs.readFileSync(0, 'utf8');

function setup() {
  const elements = new Map();
  const storage = new Map([['tdx_pool_id', '1']]);
  const requests = [];
  const timers = [];
  const document = {
    documentElement: {},
    querySelectorAll: () => [],
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, {value: '', innerHTML: '', textContent: ''});
      return elements.get(id);
    },
  };
  const context = vm.createContext({
    document, AbortController, console,
    setTimeout: callback => {timers.push(callback); return timers.length;},
    clearTimeout: id => {timers[id - 1] = null;},
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value),
      removeItem: key => storage.delete(key),
    },
    // No real network: deferred transport deliberately ignores abort to exercise sequence guards.
    fetch(path, options = {}) {
      return new Promise((resolve, reject) => requests.push({path, options, resolve, reject}));
    },
  });
  vm.runInContext(script, context);
  return {
    run: code => vm.runInContext(code, context),
    html: () => document.getElementById('review').innerHTML,
    requests, document,
    timers,
    latest: () => requests.at(-1),
  };
}

function resolve(request, value) {
  request.resolve({ok: true, json: async () => value});
}

const actions = ['runDecisionEngine', 'analyzePool', 'runChanAnalysis', 'dailyReview'];
const types = ['stock_pool_decision_engine', 'stock_pool_market_analysis', 'stock_pool_chan_analysis', 'daily_review'];
function report(action, marker) {
  return {payload: {report_type: types[actions.indexOf(action)], summary: marker,
    holding_count: marker, items: [], data_quality: {}}};
}

const item = {
  symbol: 'SH600001', name: '<img onerror="bad">', current_price: 12,
  probabilities: {up: 0.6, range: 0.3, down: 0.1},
  decision: {key: 'hold_observe', risk_level: 'medium', confidence: 'low',
    trigger: 'cross <13>', next_check: 'check & wait'},
  position: {pnl_pct: 20},
  evidence: [{source: 'MA<script>', observation: 'rising & steady',
    contribution: {up: 0.4, range: -0.1, down: 0}, regime_weight: 1.25}],
  factor_profile: {momentum: {return20_pct: 9, return60_pct: null,
    window: {start: '2026-08-01', end: '2026-09-01'}},
    as_of: '2026-09-29', windows: {'20': {start: '2026-08-31', end: '2026-09-29',
      stock: {status: 'complete', start_date: '2026-08-31', end_date: '2026-09-29'},
      index: {status: 'stale', start_date: '2026-08-30', end_date: '2026-09-28'}, pool_sample_size: 2}},
    relative_strength: {vs_index_20_pct: 3, vs_pool_20_pct: 2},
    attribution: {excess_market_20_pct: 3, excess_pool_median_20_pct: 1},
    mean_reversion: {ma20_deviation_pct: 4, volume_ratio: 1.2}},
  data_quality: {status: 'partial', issues: ['missing <volume>'],
    quote_fetched_at: '2026-09-30T14:20:00Z', kline_as_of: '2026-09-29', bar_count: 42},
  price_origin: 'kline_close',
};
const decisionReport = {model_version: 'v-test', calibration: 'uncalibrated', items: [item]};

async function main() {
  const caseName = process.argv[2];
  const app = setup();
  if (caseName === 'holdings') {
    const rows = [{quantity: 10, cost_price: 10, current_price: 12},
      {quantity: 20, cost_price: 5, current_price: null},
      {quantity: 0, cost_price: 100, current_price: 120}];
    const summary = app.run(`summarizeHoldings(${JSON.stringify(rows)})`);
    assert.equal(summary.totalCost, 200);
    assert.equal(summary.pricedCost, 100);
    assert.equal(summary.totalMarketValue, 120);
    assert.equal(summary.totalPnl, 20);
    assert.equal(summary.totalPnlPct, 20);
    assert.equal(summary.pricedCount, 1);
    assert.equal(summary.unpricedCount, 1);
    assert.equal(summary.coverage, 0.5);
    for (const price of [null, undefined, '', ' ', 0, -1, Infinity, NaN, 'oops']) {
      const missing = app.run('summarizeHoldings')([{quantity: 1, cost_price: 10, current_price: price}]);
      assert.equal(missing.totalMarketValue, null, `price=${price}`);
      assert.equal(missing.totalPnl, null);
      assert.equal(missing.totalPnlPct, null);
      assert.equal(missing.unpricedCount, 1);
    }
    const empty = app.run('summarizeHoldings')([{quantity: 0, cost_price: 10, current_price: 12}]);
    assert.equal(empty.pricedCount, 0);
    assert.equal(empty.unpricedCount, 0);
    assert.equal(empty.coverage, null);
    const complete = app.run('summarizeHoldings')([{quantity: 2, cost_price: 5, current_price: '6'}]);
    assert.equal(complete.coverage, 1);
    assert.equal(complete.totalMarketValue, 12);
    assert.equal(complete.totalPnlPct, 20);
    const invalidQuantities = app.run('summarizeHoldings')([
      {quantity: -1, cost_price: 10, current_price: 12},
      {quantity: 'bad', cost_price: 10, current_price: 12},
    ]);
    assert.equal(invalidQuantities.totalCost, 0);
    assert.equal(invalidQuantities.pricedCount, 0);
    assert.equal(invalidQuantities.unpricedCount, 0);
    for (const [lang, label, subset] of [['zh', '部分估值', '已定价持仓'], ['en', 'Partial valuation', 'Priced holdings']]) {
      app.run(`currentLanguage = '${lang}'`);
      const html = app.run(`holdingsSummary(${JSON.stringify(rows)})`);
      assert.ok(html.includes(label), html);
      assert.ok(html.includes(subset), html);
      assert.ok(html.includes('50.0%'), html);
      assert.ok(html.includes('20.00%'), html);
    }
  } else if (caseName === 'quotes') {
    for (const price of [null, '', ' ', 0, -3, 'invalid']) {
      const promise = app.run('enrichHoldingWithQuote({quantity: 10, cost_price: 10})');
      resolve(app.latest(), {price});
      const row = await promise;
      assert.equal(row.current_price, null, `price=${price}`);
      assert.equal(row.market_value, null);
      assert.equal(row.estimated_pnl, null);
    }
    const promise = app.run('enrichHoldingWithQuote({quantity: 0, cost_price: 10})');
    resolve(app.latest(), {price: 12});
    assert.equal((await promise).estimated_pnl_pct, null);
  } else if (caseName === 'races') {
    for (const older of actions) for (const newer of actions)
      for (const failOld of [false, true]) for (const failNew of [false, true])
        for (const oldFirst of [false, true]) {
      const race = setup();
      const oldPromise = race.run(`${older}()`);
      const oldRequest = race.latest();
      const newPromise = race.run(`${newer}()`);
      const newRequest = race.latest();
      const settleOld = async () => {
        if (failOld) oldRequest.reject(new Error('STALE ERROR'));
        else resolve(oldRequest, report(older, 'STALE'));
        await oldPromise;
      };
      if (oldFirst) {
        const loading = race.html();
        await settleOld();
        assert.equal(race.html(), loading);
        assert.equal(race.run('cachedReview'), null);
      }
      if (failNew) newRequest.reject(new Error('LATEST ERROR'));
      else resolve(newRequest, report(newer, 'LATEST'));
      await newPromise;
      const html = race.html();
      if (!oldFirst) await settleOld();
      assert.equal(race.html(), html, `${older} -> ${newer}, error=${failOld}`);
      assert.equal(race.run('cachedReview?.payload.summary ?? null'), failNew ? null : 'LATEST');
      assert.equal(oldRequest.options.signal?.aborted, true);
    }
  } else if (caseName === 'source') {
    app.run(`cachedReview = ${JSON.stringify(report('runDecisionEngine', 'CACHED'))}; renderDailyReview(cachedReview)`);
    app.run("setMarketSource('eastmoney'); setLanguage('en')");
    assert.equal(app.run('cachedReview'), null);
    assert.ok(!app.html().includes('CACHED'));
    for (const action of actions) for (const failOld of [false, true]) {
      const source = setup();
      source.run(`cachedReview = ${JSON.stringify(report('runDecisionEngine', 'CACHED'))}; renderDailyReview(cachedReview)`);
      const pending = source.run(`${action}()`);
      const request = source.latest();
      source.run("setMarketSource('eastmoney')");
      assert.equal(source.run('cachedReview'), null);
      assert.equal(source.run('marketSource()'), 'eastmoney');
      assert.equal(request.options.signal?.aborted, true);
      const html = source.html();
      if (failOld) request.reject(new Error('STALE SOURCE ERROR'));
      else resolve(request, report(action, 'STALE SOURCE'));
      await pending;
      source.run("setLanguage('en')");
      assert.ok(!source.html().includes('CACHED'));
      assert.ok(!source.html().includes('STALE'));
      assert.ok(!html.includes('checking'));
    }
  } else if (caseName === 'failure') {
    for (const action of actions) {
      const failed = setup();
      failed.run(`cachedReview = ${JSON.stringify(report('runDecisionEngine', 'CACHED'))}`);
      const pending = failed.run(`${action}()`);
      failed.latest().reject(new Error('LATEST ERROR <unsafe>'));
      await pending;
      assert.equal(failed.run('cachedReview'), null);
      assert.ok(failed.html().includes('LATEST ERROR &lt;unsafe&gt;'));
      failed.run("setLanguage('en')");
      assert.ok(!failed.html().includes('CACHED'));
    }
  } else if (caseName === 'details') {
    for (const [lang, score, warning] of [['zh', '情景评分', '未经校准'], ['en', 'Scenario scores', 'not calibrated']]) {
      app.run(`currentLanguage = '${lang}'; renderDecisionEngine(${JSON.stringify({payload: decisionReport})})`);
      const html = app.html();
      const header = html.match(/<thead>(.*?)<\/thead>/s)[1];
      assert.equal((header.match(/<th(?:\s|>)/g) || []).length, 9);
      assert.ok(!header.includes('概率') && !header.includes('Prob.'));
      assert.ok(html.includes('<details') && html.includes('<summary'));
      assert.ok(html.includes(score) && html.includes(warning));
      assert.ok(html.includes(lang === 'zh' ? '部分数据' : 'Partial data'));
      for (const value of ['v-test', '1.25', '0.4', '-0.1', '0', '9.00%', '3.00%',
        '2026-08-01', '2026-09-01', '2026-09-29', '2026-09-30T14:20:00Z',
        '42', 'missing &lt;volume&gt;', 'cross &lt;13&gt;', 'check &amp; wait',
        'MA&lt;script&gt;', 'rising &amp; steady']) assert.ok(html.includes(value), value);
      assert.ok(!html.includes('<img') && !html.includes('<script>'));
      const details = html.match(/<details[^>]*>(.*?)<\/details>/s)[1];
      assert.ok(!details.includes('<table'), 'Detailed prose must not live in a wide table');
    }
    app.run('renderDecisionEngine({calibration: {status: "uncalibrated"}, items: [{symbol: "EMPTY", factor_profile: {}, data_quality: {}}]})');
    assert.ok(!app.html().includes('undefined') && !app.html().includes('NaN'));
    assert.ok(app.html().includes('not calibrated'));
  } else if (caseName === 'comparison') {
    const comparison = {previous_generated_at: '2026-09-28T12:00:00Z', items: [{
      symbol: 'SH600001', previous_probabilities: {up: 0.4, range: 0.4, down: null},
      current_probabilities: {up: 0.6, range: 0.3, down: 0.1},
      probability_changes: {up: 0.2, range: -0.1, down: null},
      previous_decision: {key: 'wait_confirm'}, current_decision: {key: 'hold_observe'},
    }]};
    const second = {symbol: 'SZ000002', name: 'Other', probabilities: {}, decision: {}};
    for (const lang of ['zh', 'en']) {
      app.run(`currentLanguage = '${lang}'; renderDecisionEngine(${JSON.stringify({payload: {...decisionReport, items: [second, item], comparison}})})`);
      const html = app.html();
      const details = [...html.matchAll(/<details[^>]*>(.*?)<\/details>/gs)].map(match => match[1]);
      assert.equal(details.length, 2, 'Each stock needs its own expandable detail');
      assert.ok(!details[0].includes('2026-09-28T12:00:00Z'));
      assert.ok(details[1].includes('2026-09-28T12:00:00Z'));
      assert.ok(details[1].includes('+20.0') && details[1].includes('-10.0'));
      assert.ok(details[1].includes('40.0%') && details[1].includes('60.0%'));
      assert.ok(!details[1].includes('null') && !details[1].includes('NaN'));
      assert.ok(details[1].includes(lang === 'zh' ? '等待确认' : 'Wait for confirmation'));
    }
    app.run(`renderDecisionEngine(${JSON.stringify(decisionReport)})`);
    assert.ok(!app.html().includes('2026-09-28T12:00:00Z'));
    comparison.items[0].previous_decision = 'wait_confirm';
    comparison.items[0].current_decision = 'hold_observe';
    app.run(`renderDecisionEngine(${JSON.stringify({...decisionReport, comparison})})`);
    assert.ok(app.html().includes('Wait for confirmation') && app.html().includes('Hold and observe'));
    assert.ok(app.html().includes('Down -'));
  } else if (caseName === 'benchmark') {
    const pending = app.run('runDecisionEngine()');
    assert.equal(JSON.parse(app.latest().options.body).market_index_symbol, 'SH000300');
    resolve(app.latest(), decisionReport);
    await pending;
  } else if (caseName === 'saved-review') {
    const pending = app.run('dailyReview()');
    assert.equal(app.latest().path, '/reports/daily-review?pool_id=1&source=tdx-official');
    const saved = {payload: {report_type: 'daily_review', decision_review_status: 'saved_analysis', decision_analysis: {...decisionReport, comparison: {
      previous_generated_at: '2026-09-28T12:00:00Z', items: [{symbol: 'SH600001',
        probability_changes: {up: 0.2}, previous_decision: 'wait_confirm', current_decision: 'hold_observe'}],
    }},
      analysis_report_id: 77, analysis_generated_at: '2026-09-30T12:34:56Z'}};
    resolve(app.latest(), saved);
    await pending;
    for (const [lang, label] of [['zh', '已保存分析'], ['en', 'Saved analysis']]) {
      app.run(`setLanguage('${lang}')`);
      assert.ok(app.html().includes(label));
      assert.ok(app.html().includes('77') && app.html().includes('2026-09-30T12:34:56Z'));
      assert.ok(app.html().includes('v-test') && app.html().includes('<details'));
      assert.ok(app.html().includes('+20.0') && app.html().includes('2026-09-28T12:00:00Z'));
    }
  } else if (caseName === 'markup') {
    app.run(`renderDecisionEngine(${JSON.stringify(decisionReport)})`);
    process.stdout.write(app.html());
  } else if (caseName === 'not-analyzed' || caseName === 'not-analyzed-markup') {
    const missing = {payload: {report_type: 'daily_review', decision_review_status: 'not_analyzed',
      holding_count: 1, signal_count: 1, recent_signal_details: [{symbol: 'LEGACY_SIGNAL_MUST_NOT_RENDER',
        signal_type: 'trend_break', action: 'exit_or_reduce', risk_level: 'high', price: 10}]}};
    if (caseName === 'not-analyzed-markup') {
      app.run(`renderDailyReview(${JSON.stringify(missing)})`);
      process.stdout.write(app.html());
      return;
    }
    const pending = app.run('dailyReview()');
    resolve(app.latest(), missing);
    await pending;
    for (const [lang, label] of [['zh', '当前股票池和行情源暂无已保存分析，请先运行持仓决策引擎。'],
      ['en', 'No saved analysis for this pool and market source. Run the decision engine first.']]) {
      app.run(`setLanguage('${lang}')`);
      assert.ok(app.html().includes(label), app.html());
      assert.ok(!app.html().includes('<table') && !app.html().includes('LEGACY_SIGNAL_MUST_NOT_RENDER'));
      assert.ok(!app.html().includes(lang === 'zh' ? '近期预测信号' : 'Recent Prediction Signals'));
    }
    app.run(`renderDailyReview(${JSON.stringify({payload: {...missing.payload, decision_analysis: decisionReport}})})`);
    assert.ok(app.html().includes('v-test'), 'Attached decision analysis has priority over the status guard');
    assert.ok(!app.html().includes('Run the decision engine first.'));
  } else if (caseName === 'legacy-review') {
    app.run("localStorage.removeItem('tdx_pool_id')");
    const pending = app.run('dailyReview()');
    assert.equal(app.latest().path, '/reports/daily-review?pool_id=&source=tdx-official');
    resolve(app.latest(), {payload: {report_type: 'daily_review', holding_count: 1, signal_count: 1,
      recent_signal_details: [{symbol: 'LEGACY_COMPATIBILITY', signal_type: 'trend_break',
        action: 'exit_or_reduce', risk_level: 'high', price: 10}]}});
    await pending;
    for (const lang of ['zh', 'en']) {
      app.run(`setLanguage('${lang}')`);
      assert.ok(app.html().includes('LEGACY_COMPATIBILITY'));
      assert.ok(app.html().includes(lang === 'zh' ? '近期预测信号' : 'Recent Prediction Signals'));
    }
  } else if (caseName === 'provenance-labels') {
    const endpoint = {return_pct: 1.5, start_close: 10, end_close: 10.15,
      calendar_source: 'index', start_lag_calendar_days: 1, end_lag_calendar_days: 0};
    for (const lang of ['zh', 'en']) {
      app.run(`currentLanguage = '${lang}'`);
      const labels = lang === 'zh'
        ? ['窗口收益率', '起点收盘价', '终点收盘价', '交易日历来源', '起点滞后自然日', '终点滞后自然日']
        : ['Window return', 'Start close', 'End close', 'Trading calendar source', 'Start lag (calendar days)', 'End lag (calendar days)'];
      const html = app.run(`factorFields(${JSON.stringify(endpoint)})`);
      for (const label of labels) assert.ok(html.includes(`<dt>${label}</dt>`), label);
      assert.ok(html.includes('<dd>1.50%</dd>'));
      assert.ok(html.includes(`<dd>${lang === 'zh' ? '指数交易日历' : 'Index calendar'}</dd>`));
      const pool = app.run('factorFields({calendar_source: "pool"})');
      assert.ok(pool.includes(`<dd>${lang === 'zh' ? '股票池交易日历' : 'Pool calendar'}</dd>`));
      const volume = {...item, data_quality: {...item.data_quality, issues: ['invalid_volume', 'missing_volume']}};
      app.run(`renderDecisionEngine(${JSON.stringify({items: [volume]})})`);
      assert.ok(app.html().includes(lang === 'zh' ? '成交量无效' : 'Invalid volume'));
      assert.ok(app.html().includes(lang === 'zh' ? '缺少成交量' : 'Missing volume'));
      assert.ok(!app.html().includes('invalid_volume') && !app.html().includes('missing_volume'));
      for (const [origin, zh, en] of [['quote', '实时报价', 'Live quote'],
        ['latest_close', '最近K线收盘价', 'Latest K-line close'], ['kline_close', 'K线收盘价', 'K-line close']]) {
        const stock = {...item, price_origin: origin, evidence: [{source: 'Chan',
          observation: 'suspected_third_buy / extended_above_center / custom_center_range_variant <tag>',
          contribution: {up: 0.4}, regime_weight: 1}]};
        app.run(`renderDecisionEngine(${JSON.stringify({items: [stock]})})`);
        const rendered = app.html();
        assert.ok(rendered.includes(`<dd>${lang === 'zh' ? zh : en}</dd>`));
        assert.ok(rendered.includes(lang === 'zh' ? '疑似三买' : 'Possible third buy'));
        assert.ok(rendered.includes(lang === 'zh' ? '远离中枢上方' : 'Extended above center'));
        assert.ok(!rendered.includes('suspected_third_buy') && !rendered.includes('extended_above_center'));
        assert.ok(rendered.includes('custom_center_range_variant &lt;tag&gt;'));
      }
      const unknown = app.run('decisionDetails({symbol: "X", price_origin: "custom<origin>"})');
      assert.ok(unknown.includes('custom&lt;origin&gt;'));
      assert.ok(!unknown.includes('price_origin_custom'));
    }
  } else if (caseName === 'opportunities') {
    const scan = app.run('runOpportunities()');
    assert.equal(app.latest().path, '/stock-pools/1/opportunities');
    resolve(app.latest(), {id:'abc',status:'running',source:'tdx-official',progress:{stage:'analyzing',completed:1,total:40}});
    await scan;
    assert.ok(app.html().includes('1 / 40'));
    const poll = app.timers.at(-1)();
    const old = app.latest();
    const analysis = app.run('runDecisionEngine()');
    resolve(app.latest(), {items:[],summary:'NEWER_ANALYSIS'});
    await analysis;
    resolve(old,{id:'abc',status:'completed',source:'tdx-official',result:{items:[],selected:[],scope:{}}});
    await poll;
    assert.ok(app.html().includes('NEWER_ANALYSIS'));
    const result = {items:[{...item,symbol:'600036',origin:'new',level:'wait',selection_reasons:['extended_price'],
      rank_score:60,conditions:{ma20:10,atr14:1,review_below:9},supporting_evidence:[],opposing_evidence:[]}],selected:['600036'],scope:{new:1},discovery:{}};
    app.run(`renderOpportunityJob(${JSON.stringify({source:'tdx-official',status:'completed',result})})`);
    const rows = app.document.getElementById('opportunity-rows').innerHTML;
    assert.ok(rows.includes('等待确认') && rows.includes('价格偏离均线较远'));
    assert.ok(!rows.includes('<img onerror'));
    app.run("setLanguage('en')");
    assert.ok(app.document.getElementById('opportunity-rows').innerHTML.includes('Await confirmation'));
    app.run("cachedWatchlist = [{symbol:'SH600036'}]; renderOpportunityRows()");
    assert.ok(app.document.getElementById('opportunity-rows').innerHTML.includes('disabled'));
    const add = app.run("addOpportunity('600036',{disabled:false,textContent:''})");
    assert.equal(app.latest().path, '/watchlist?pool_id=1');
    const count = app.requests.length;
    resolve(app.latest(),[{symbol:'SH600036'}]);
    await add;
    assert.equal(app.requests.length,count,'Existing alias must not create another watchlist entry');
    app.run("renderOpportunityHistory([{id:'abc',status:'completed',created_at:'2026-10-01'}]); setLanguage('zh')");
    assert.ok(app.html().includes('推荐记录') && app.html().includes('已完成'));
    app.run("renderOpportunityJob({id:'abc',source:'tdx-official',status:'running',progress:{}})");
    const failedPoll = app.timers.at(-1)();
    app.latest().reject(new Error('offline'));
    await failedPoll;
    const retryPoll = app.timers.at(-1)();
    resolve(app.latest(),{id:'abc',source:'tdx-official',status:'completed',result:{items:[],selected:[],scope:{}}});
    await retryPoll;
    assert.ok(app.html().includes('市场机会推荐'));
    assert.ok(!app.html().includes('取消扫描'));
  } else throw new Error(`Unknown test case: ${caseName}`);
}

main().catch(error => {console.error(error); process.exitCode = 1;});
