"""Self-contained, escaped research reports from fixed inputs; no network or application state."""
from __future__ import annotations

from html import escape
from math import isfinite

from .chan_dataset import canonical_json
from .market_time import completed_bars, local_timestamp


LABELS = {
    "checked": ("覆盖已核对", "Coverage checked"), "limited": ("覆盖未核实", "Coverage unverified"),
    "review": ("需要复核", "Review required"), "verified": ("已核实", "Verified"),
    "unverified": ("未核实", "Unverified"), "candidate": ("候选观察", "Candidate observation"),
    "withdrawn": ("候选撤回", "Candidate withdrawn"), "invalidated": ("收盘失效", "Invalidated at close"),
    "boundary_touch": ("盘中触及边界", "Intraday boundary touch"),
    "data_unavailable": ("数据不可用", "Data unavailable"), "matured": ("已到期", "Matured"),
    "pending": ("尚未到期", "Pending"), "unavailable": ("不可评估", "Unavailable"),
    "up": ("向上候选", "Upward candidate"), "down": ("向下候选", "Downward candidate"),
    "missing_session": ("缺少交易日数据", "Missing session"),
    "invalid_ohlc": ("价格无效", "Invalid OHLC prices"),
    "calendar_conflict": ("价格日期与日历冲突", "Price date conflicts with calendar"),
    "provider_unavailable": ("数据源不可用", "Provider unavailable"),
    "truncated": ("采集深度有限", "Bounded history"),
    "unverified_calendar": ("交易日历未核实", "Trading calendar unverified"),
    "unverified_price_basis": ("价格口径未核实", "Price basis unverified"),
    "horizon_not_matured": ("观察周期尚未结束", "Observation window not yet complete"),
    "calendar_coverage_insufficient": ("日历覆盖不足", "Calendar coverage insufficient"),
    "observation_calendar_conflict": ("候选日期与日历冲突", "Observation date conflicts with calendar"),
    "benchmark_calendar_conflict": ("基准日期与日历冲突", "Benchmark date conflicts with calendar"),
    "invalid_numeric_outcome": ("计算结果无效", "Invalid numeric outcome"),
    "wait_for_structure": ("等待结构", "Insufficient structure"),
    "complete_market_data": ("补齐行情", "Market data needed"),
    "trend_observe": ("趋势观察", "Trend observation"), "center_range": ("中枢震荡", "Within center"),
    "extended_above_center": ("远离中枢上方", "Extended above center"),
    "extended_below_center": ("远离中枢下方", "Extended below center"),
    "suspected_third_buy": ("疑似三买观察", "Third-buy candidate observation"),
    "suspected_third_sell": ("疑似三卖观察", "Third-sell candidate observation"),
    "upward_leave": ("向上离开中枢", "Upward departure from center"),
    "downward_leave": ("向下离开中枢", "Downward departure from center"),
    "observe": ("观察", "Observation"),
}
for _subject, _zh, _en in (("stock", "个股", "Stock"), ("benchmark", "基准", "Benchmark")):
    for _suffix, _zh_reason, _en_reason in (("missing_session", "缺少交易日数据", "missing session"),
                                          ("data_quality", "数据质量异常", "data quality issue"),
                                          ("volume_unavailable", "缺少有效成交量", "volume unavailable")):
        LABELS[f"{_subject}_{_suffix}"] = (_zh + _zh_reason, _en + " " + _en_reason)

CSS = """
:root{color-scheme:light;font:15px/1.6 system-ui,-apple-system,sans-serif;color:#232927;background:#f4f6f7}
*{box-sizing:border-box;letter-spacing:0}body{margin:0}main{max-width:1180px;margin:auto;background:white;padding:32px 40px}
h1{font-size:28px;line-height:1.3;margin:8px 0 12px}h2{font-size:21px;margin:0}h3{font-size:16px;margin:24px 0 8px}
p{margin:8px 0}a{color:#22634f;text-underline-offset:3px}a:focus-visible,summary:focus-visible{outline:3px solid #447fbb;outline-offset:3px}
header{border-bottom:2px solid #2c6856;padding-bottom:24px}.eyebrow,.muted,figcaption{color:#5e686c;font-size:13px}
.notice{border-left:3px solid #c78826;background:#fff8e9;padding:10px 14px;margin-top:14px}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-bottom:1px solid #dce2e2;padding:16px 0;gap:16px}
.metrics strong{display:block;font-size:24px;font-variant-numeric:tabular-nums}.metrics span{font-size:13px;color:#5e686c}
nav{display:flex;flex-wrap:wrap;gap:12px 24px;padding:16px 0}section{border-top:1px solid #dce2e2;padding:24px 0;scroll-margin-top:16px;min-width:0}
.heading{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.badge{font-size:13px;color:#425f6e}
.review,.invalidated,.unavailable{color:#a13a37}.candidate,.matured,.checked{color:#22634f}.limited,.pending,.data_unavailable{color:#805b1c}
.facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px 20px;margin:16px 0}.facts dt{font-size:13px;color:#5e686c}.facts dd{margin:2px 0 0;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.table-wrap,.chart-wrap{overflow-x:auto;max-width:100%}table{border-collapse:collapse;width:100%;font-size:14px;text-align:left}
th{color:#5e686c;font-size:12px;font-weight:600;background:#f7f9fa}th,td{padding:10px 12px;border-bottom:1px solid #e5eaea;vertical-align:top}
th:first-child,td:first-child{padding-left:0}td.num{font-variant-numeric:tabular-nums;white-space:nowrap}td.wrap{min-width:180px;overflow-wrap:anywhere}
summary{cursor:pointer;font-weight:600;padding:10px 0}details{border-top:1px solid #e5eaea;margin-top:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 ui-monospace,monospace;background:#f7f9fa;padding:12px}
code{font:12px ui-monospace,monospace;overflow-wrap:anywhere}.event-code{display:block;color:#687177;font-size:11px}.empty{color:#805b1c;background:#fff8e9;padding:12px 16px}
figure{margin:16px 0}svg{display:block;width:100%;min-width:580px;height:auto}svg text{font:11px system-ui,sans-serif;fill:#5e686c}figcaption{margin-top:6px}
footer{padding-top:20px;border-top:1px solid #dce2e2;color:#5e686c;font-size:13px}li{margin:5px 0}
@media(max-width:640px){main{padding:20px 16px}h1{font-size:24px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.facts{grid-template-columns:1fr 1fr}th,td{padding:8px}section{padding:20px 0}}
@media print{body{background:white}main{max-width:none;padding:0}nav{display:none}.table-wrap,.chart-wrap{overflow:visible}svg{min-width:0}th,td{font-size:10px;padding:5px}h2,h3{break-after:avoid}tr,figure{break-inside:avoid}}
"""


def _text(value):
    return escape("-" if value is None else str(value), quote=True)


def _number(value, suffix=""):
    return "-" if value is None else f"{value:,.2f}{suffix}"


def _table(headers, rows):
    head = "".join(f'<th scope="col">{_text(h)}</th>' for h in headers)
    body = "".join("<tr>" + "".join(f'<td class="{kind}">{cell}</td>' for cell, kind in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap" tabindex="0"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _chart(dataset, quality, observations, tr):
    symbol, as_of = quality["symbol"], quality["as_of"]
    raw = dataset["series"][symbol].get("daily", {"bars": []})["bars"]
    rows, _ = completed_bars(raw, period="daily", as_of=as_of)
    blocked = {i["bar_key"] for i in quality["issues"] if i["scope"] == "bar" and i["code"] != "truncated"}
    prices = {r["trade_date"]: r["close"] for r in rows if r["trade_date"] not in blocked}
    visible_days = {r["trade_date"] for r in raw if local_timestamp(r["trade_date"] + "T15:00:00+08:00") <= local_timestamp(as_of)}
    days = sorted(visible_days | blocked)[-160:]
    values = [prices[d] for d in days if d in prices]
    if not values:
        return f'<p class="empty">{tr("无有效价格可绘图。", "No valid prices to chart.")}</p>'
    # Scale before padding so finite extreme inputs cannot overflow SVG coordinates.
    scale = max(values)
    low, high = min(values) / scale, 1.0
    pad = max((high - low) * .1, .01)
    low, high = max(0, low - pad), high + pad
    if not isfinite(high * scale):
        high = 1.0
    x = lambda i: 70 + i * 810 / max(1, len(days) - 1)
    y = lambda price: 230 - (price / scale - low) / (high - low) * 200
    fragments, segment = [], []
    for i, day in enumerate(days):
        if day in prices:
            segment.append(f"{x(i):.2f},{y(prices[day]):.2f}")
        elif segment:
            fragments.append(segment)
            segment = []
    if segment:
        fragments.append(segment)
    title = tr("历史收盘价", "Historical close") + " · " + symbol
    svg = [f'<svg viewBox="0 0 900 275" role="img" aria-label="{_text(title)}"><title>{_text(title)}</title>']
    for ratio in (0, .5, 1):
        price = (low + (high - low) * ratio) * scale
        tick = f"{price:.3g}" if price >= 1e9 or 0 < price < .005 else _number(price)
        svg.append(f'<line x1="70" x2="880" y1="{230 - ratio * 200:.2f}" y2="{230 - ratio * 200:.2f}" stroke="#e5eaea"/>'
                   f'<text x="60" y="{234 - ratio * 200:.2f}" text-anchor="end">{tick}</text>')
    for points in fragments:
        svg.append(f'<polyline data-symbol="{_text(symbol)}" points="{" ".join(points)}" fill="none" stroke="#2c6856" stroke-width="2"/>')
        if len(points) == 1:
            px, py = points[0].split(",")
            svg.append(f'<circle cx="{px}" cy="{py}" r="2" fill="#2c6856"/>')
    for i in sorted({0, len(days) // 2, len(days) - 1}):
        anchor = "start" if i == 0 else "end" if i == len(days) - 1 else "middle"
        svg.append(f'<text x="{x(i):.2f}" y="255" text-anchor="{anchor}">{days[i]}</text>')
    for observation in observations:
        day = observation["first_seen_at"][:10]
        if day in days and day in prices:
            label = tr("首次候选", "First candidate") + " " + day
            svg.append(f'<circle cx="{x(days.index(day)):.2f}" cy="{y(prices[day]):.2f}" r="4" fill="#b56c28">'
                       f'<title>{_text(label)}</title></circle>')
    svg.append("</svg>")
    caption = tr("输入收盘价，非实时行情；圆点为候选首次出现，缺数处断线。", "Input closes, not live quotes; dots mark first candidates, gaps remain disconnected.")
    extent = f"{days[0]} ~ {days[-1]}"
    return '<figure><div class="chart-wrap">' + "".join(svg) + f'</div><figcaption>{caption} {extent}</figcaption></figure>'


def render_report(dataset: dict, report: dict, *, language: str = "zh") -> str:
    if language not in {"zh", "en"}:
        raise ValueError("unsupported_report_language")
    tr = lambda zh, en: zh if language == "zh" else en
    label = lambda code: LABELS.get(code, (code, code))[language == "en"]
    badge = lambda code: f'<span class="badge {_text(code)}">{_text(label(code))}</span>'
    quality = report["data_quality"]
    title = tr("缠论验证报告", "Chan research report")
    parts = [f'<!doctype html><html lang="{tr("zh-CN", "en")}"><head><meta charset="utf-8">'
             '<meta name="viewport" content="width=device-width, initial-scale=1">'
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
             f'<title>{title}</title><style>{CSS}</style></head><body><main><header>'
             f'<div class="eyebrow">{tr("通达信 · 固定样本研究", "Tongdaxin · Fixed-sample research")}</div><h1>{title}</h1>'
             f'<p>{tr("回放截止", "Replay cutoff")}: <time>{_text(report["as_of"])}</time></p>'
             f'<p class="muted">{tr("数据源", "Source")}: {_text(dataset["source"])} · {_text(report["model_version"])}</p>']
    if dataset["source"] == "synthetic":
        parts.append(f'<p class="notice">{tr("合成测试数据，不是真实市场结果。", "Synthetic test data, not actual market results.")}</p>')
    parts.append(f'<p class="notice">{tr("笔级候选研究，非确定买卖点；尚未验证胜率或预测效果。", "Pen-level candidate research, not confirmed buy/sell points; predictive effectiveness remains unvalidated.")}</p></header>')
    metrics = [(len(quality["items"]), tr("研究证券", "Securities")), (len(report["observations"]), tr("历史候选", "Historical candidates")),
               (quality["review_count"], tr("需要数据复核", "Need data review")), (quality["limited_count"], tr("覆盖未核实", "Coverage unverified"))]
    parts.append('<div class="metrics">' + "".join(f'<div><strong>{n}</strong><span>{s}</span></div>' for n, s in metrics) + '</div>')
    parts.append('<nav aria-label="' + tr("报告目录", "Report contents") + '">' + "".join(
        f'<a href="#stock-{_text(q["symbol"])}">{_text(q["symbol"])}</a>' for q in quality["items"]) + f'<a href="#provenance">{tr("数据依据", "Provenance")}</a></nav>')
    parts.append(f'<p>{tr("交易日历", "Calendar")}: {_text(label(quality["calendar_verification"]))} · '
                 f'{tr("价格口径", "Price basis")}: {_text(label(quality["price_basis_verification"]))}</p>')
    for q in quality["items"]:
        symbol = q["symbol"]
        observations = [o for o in report["observations"] if o["symbol"] == symbol]
        frames = [f for f in report["frames"] if f["symbol"] == symbol]
        parts.append(f'<section id="stock-{_text(symbol)}"><div class="heading"><h2>{_text(symbol)}</h2>{badge(q["status"])}</div>')
        facts = [(tr("有效日线 / 应有交易日", "Valid bars / expected sessions"), f'{q["valid_bar_count"]} / {q["expected_session_count"] if q["expected_session_count"] is not None else tr("未核实", "Unverified")}'),
                 (tr("首个有效收盘日", "First valid close date"), (q["first_bar_at"] or "-")[:10]),
                 (tr("最后有效收盘日", "Last valid close date"), (q["last_bar_at"] or "-")[:10])]
        parts.append('<dl class="facts">' + "".join(f'<div><dt>{name}</dt><dd>{_text(value)}</dd></div>' for name, value in facts) + '</dl>')
        if q["valid_bar_count"] < report["config"]["minimum_bars"]:
            parts.append(f'<p class="empty">{tr("数据不足，无法评估候选。", "Insufficient data to evaluate candidates.")}</p>')
        elif q["status"] == "review":
            parts.append(f'<p class="empty">{tr("数据异常限制当前结构判断，历史候选不等于当前仍有效。", "Data issues restrict the current structure assessment; historical candidates may no longer be valid.")}</p>')
        if frames:
            last = frames[-1]
            parts.append(f'<p class="muted">{tr("最后回放时点", "Last replay frame")}: {_text(last["at"])} · '
                         f'{tr("候选判定资格", "Candidate evaluation eligible")}: {tr("是", "Yes") if last["eligible"] else tr("否", "No")}</p>')
            parts.append(f'<h3>{tr("最近原模型结构", "Latest baseline structure")}: {_text(label(last["signal"]["type"]))}</h3>')
            if not last["eligible"]:
                parts.append(f'<p class="review">{tr("该时点不具备新候选判定资格。", "This frame is not eligible for new candidates.")}</p>')
            if language == "zh":
                parts.append(f'<p>{_text(last["signal"].get("reason"))}</p>')
            parts.append(f'<details><summary>{tr("原始结构依据", "Source structure evidence (original language)")}</summary>'
                         f'<pre>{_text(canonical_json({"signal": last["signal"], "quality": last["data_quality"]}).decode())}</pre></details>')
        parts.append(_chart(dataset, q, observations, tr))
        if not observations:
            parts.append(f'<p>{tr("未记录有效候选。", "No valid candidate recorded.")}</p>')
        for index, observation in enumerate(observations, 1):
            oid = observation["observation_id"]
            events = [e for e in report["events"] if e["observation_id"] == oid]
            states = [e for e in events if e["type"] != "boundary_touch"]
            current = states[-1]["type"] if states else "candidate"
            parts.append(f'<h3>{index:02d} · {_text(label(observation["direction"]))} · {badge(current)}</h3>')
            parts.append(f'<p>{tr("首次观察", "First observed")}: {_text(observation["first_seen_at"])} · '
                         f'{tr("结构端点", "Structure pivot")}: {_text(observation["pivot_at"])}</p>'
                         f'<p>{tr("首次冻结边界", "First frozen boundary")}: {_number(observation["frozen_boundary"])} · '
                         f'{tr("收盘价触及或越过边界记为失效，盘中触及单列。", "A close at or beyond the boundary invalidates; intraday touches are separate.")}</p>')
            outcome_item = next(item for item in report["price_observations"]["items"] if item["observation_id"] == oid)
            rows = []
            for horizon, outcome in outcome_item["outcomes"].items():
                reason = label(outcome["issue"]) if outcome["issue"] else tr("同日起止，价格观察", "Date-aligned price observation")
                if outcome["overlapping"]:
                    reason += tr("；窗口重叠，非独立样本", "; overlapping, non-independent sample")
                date_range = f'{outcome["start_date"]} ~ {outcome["end_date"]}' if outcome["start_date"] else "-"
                rows.append([(_text(horizon), "num"), (badge(outcome["status"]), "num"),
                             (_number(outcome["return_pct"], "%"), "num"), (_number(outcome["benchmark_return_pct"], "%"), "num"),
                             (_number(outcome["excess_pp"]), "num"), (_number(outcome["max_drawdown_pct"], "%"), "num"),
                             (_text(date_range) + '<br>' + _text(reason), "wrap")])
            parts.append(_table([tr("交易日", "Sessions"), tr("状态", "Status"), tr("个股涨跌", "Stock change"),
                                 tr("基准涨跌", "Benchmark change"), tr("超额 / 百分点", "Excess / pp"),
                                 tr("收盘回撤", "Close drawdown"), tr("观察区间与依据", "Window and evidence")], rows))
            parts.append(f'<details><summary>{tr("候选生命周期与首次依据", "Candidate lifecycle and initial evidence")}</summary>')
            parts.append(_table([tr("时间", "Time"), tr("状态事件", "State event"), tr("边界 / 收盘", "Boundary / close")], [
                [(_text(e["at"]), "num"), (badge(e["type"]) + f'<code class="event-code">{_text(e["type"])}</code>', "wrap"),
                 (_number(e["details"].get("boundary")) + " / " + _number(e["details"].get("close")), "num")] for e in events]))
            parts.append(f'<pre>{_text(canonical_json({"observation_id": oid, "data_hash": observation["data_hash"], "evidence": observation["evidence"]}).decode())}</pre></details>')
        if q["issues"]:
            parts.append(f'<details><summary>{tr("数据问题明细", "Data issues")} ({len(q["issues"])})</summary>')
            parts.append(_table([tr("日期", "Date"), tr("问题", "Issue")], [
                [(_text(i["bar_key"] or tr("整段数据", "Entire series")), "num"),
                 (_text(label(i["code"])) + f'<code class="event-code">{_text(i["code"])}</code>', "wrap")] for i in q["issues"]]))
            parts.append('</details>')
        parts.append('</section>')
    benchmark = quality["benchmark"]
    parts.append(f'<section id="provenance"><h2>{tr("数据依据与限制", "Provenance and limitations")}</h2>'
                 f'<p>SH000300 · {badge(benchmark["status"])} · {tr("有效日线", "Valid daily bars")}: {benchmark["valid_bar_count"]} · '
                 f'{tr("最后有效收盘", "Last valid close")}: {_text(benchmark["last_bar_at"])}</p>')
    limits = [("仅研究选定样本，存在样本选择和幸存者偏差；重叠观察不等于独立样本。", "Selected samples only, with selection and survivorship bias; overlapping observations are not independent."),
              ("起点为首次候选之后下一交易日开盘，终点为第 N 个交易日收盘；下跌候选不反号为做空利润。", "Windows start at the next session open and end at the Nth close; downward candidates are not simulated short profits."),
              ("日历和价格口径未核实、缺数或窗口未到期时不填收益数值。", "Unverified calendar or price basis, missing data and immature windows do not produce return values."),
              ("历史深度有限，不声明历史完整。历史重建不证明供应商在当时已返回相同数据。", "History is bounded, not complete. Reconstruction does not prove the provider exposed the same data at the historical time."),
              ("价格观察不含手续费、滑点、分红与成交约束，不是实盘收益或未来胜率。", "Price observations exclude fees, slippage, dividends and execution constraints; they are not realized returns or future win rates.")]
    parts.append('<ul>' + "".join(f'<li>{tr(zh, en)}</li>' for zh, en in limits) + '</ul>')
    manifest = {key: report[key] for key in ("dataset_id", "model_version", "baseline_fingerprint", "config", "as_of", "input")}
    parts.append(f'<details><summary>{tr("固定输入与核验记录", "Fixed inputs and verification records")}</summary><pre>{_text(canonical_json(manifest).decode())}</pre></details></section>'
                 f'<footer>{tr("离线研究报告", "Offline research report")} · chan_report_v1 · <code>{_text(report["dataset_id"])}</code></footer></main></body></html>')
    return "".join(parts)
