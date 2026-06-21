from __future__ import annotations

import math
from typing import Any

from .chan_analysis import analyze_chan_structure
from .indicators import calculate_indicator_snapshot
from .market_regime import infer_market_regime
from .repository import normalize_symbol, utc_now


SCENARIOS = ("up", "range", "down")
SOFTMAX_TEMPERATURE = 1.35


def generate_stock_pool_decision_engine(
    *,
    pool: dict[str, Any],
    watchlist: list[dict[str, Any]],
    holdings: list[dict[str, Any]],
    quotes: dict[str, dict[str, Any]],
    kline_by_symbol: dict[str, list[dict[str, Any]]],
    source: str,
    period: str = "daily",
    horizon_days: int = 20,
    index_bars: list[dict[str, Any]] | None = None,
    market_index_symbol: str | None = None,
    market_regime: dict[str, Any] | None = None,
    failed_quote_symbols: list[str] | None = None,
    failed_kline_symbols: list[str] | None = None,
    failed_market_index_symbol: str | None = None,
    max_symbols: int = 30,
) -> dict[str, Any]:
    max_symbols = max(1, min(int(max_symbols), 100))
    horizon_days = max(5, min(int(horizon_days), 120))
    ordered_symbols = _symbol_order(watchlist=watchlist, holdings=holdings)[:max_symbols]
    holdings_by_symbol = {
        normalize_symbol(str(holding["symbol"])): holding for holding in holdings
    }
    watchlist_by_symbol = {
        normalize_symbol(str(item["symbol"])): item for item in watchlist
    }
    pool_context = _pool_context(quotes)
    market_regime = market_regime or infer_market_regime(
        index_bars=index_bars or [],
        pool_quotes=quotes,
        pool_kline_by_symbol=kline_by_symbol,
    )

    items = [
        _decision_item(
            symbol=symbol,
            watchlist_item=watchlist_by_symbol.get(symbol),
            holding=holdings_by_symbol.get(symbol),
            quote=quotes.get(symbol),
            bars=kline_by_symbol.get(symbol) or [],
            pool_context=pool_context,
            market_regime=market_regime,
            period=period,
            horizon_days=horizon_days,
        )
        for symbol in ordered_symbols
    ]

    failed_quote_symbols = [normalize_symbol(symbol) for symbol in (failed_quote_symbols or [])]
    failed_kline_symbols = [normalize_symbol(symbol) for symbol in (failed_kline_symbols or [])]
    pool_name = pool.get("name") or f"Pool {pool.get('id')}"
    return {
        "report_type": "stock_pool_decision_engine",
        "symbol": None,
        "generated_at": utc_now(),
        "summary": (
            f"已用 {source} 的行情与 {period} K线完成“{pool_name}”持仓决策引擎分析："
            f"{len(items)} 只股票，目标周期约 {horizon_days} 日。"
        ),
        "pool": {
            "id": pool.get("id"),
            "name": pool_name,
            "description": pool.get("description"),
        },
        "scope": {
            "symbol_limit": max_symbols,
            "symbol_count": len(items),
            "period": period,
            "horizon_days": horizon_days,
            "market_index_symbol": market_index_symbol,
        },
        "tool_plan": {
            "data_source": source,
            "quote_tool": "quote",
            "kline_tool": "daily_kline",
            "model": "bayesian_evidence_softmax_v1",
            "market_regime_model": market_regime.get("model", "rule_state_machine_v1"),
        },
        "market_regime": market_regime,
        "data_quality": {
            "failed_quote_count": len(failed_quote_symbols),
            "failed_quote_symbols": failed_quote_symbols,
            "failed_kline_count": len(failed_kline_symbols),
            "failed_kline_symbols": failed_kline_symbols,
            "failed_market_index_symbol": failed_market_index_symbol,
            "unavailable_evidence": [
                "行业状态",
                "基本面变化",
                "事件催化",
                "历史相似样本库",
            ],
        },
        "scenario_counts": _scenario_counts(items),
        "items": items,
        "next_steps": _next_steps(items, failed_quote_symbols, failed_kline_symbols),
    }


def _decision_item(
    *,
    symbol: str,
    watchlist_item: dict[str, Any] | None,
    holding: dict[str, Any] | None,
    quote: dict[str, Any] | None,
    bars: list[dict[str, Any]],
    pool_context: dict[str, Any],
    market_regime: dict[str, Any],
    period: str,
    horizon_days: int,
) -> dict[str, Any]:
    name = (
        (quote or {}).get("name")
        or (watchlist_item or {}).get("name")
        or (holding or {}).get("name")
    )
    current_price = _current_price(quote, bars)
    indicator = calculate_indicator_snapshot(bars) if bars else {"bars": 0}
    chan = (
        analyze_chan_structure(symbol=symbol, name=name, bars=bars, period=period)
        if bars
        else None
    )
    position = _position_context(holding, current_price)

    prior = _prior_scores(
        pool_context=pool_context,
        indicator=indicator,
        current_price=current_price,
        market_regime=market_regime,
    )
    evidence = _evidence_entries(
        quote=quote,
        bars=bars,
        indicator=indicator,
        chan=chan,
        position=position,
        pool_context=pool_context,
        current_price=current_price,
    )
    _apply_regime_weights(evidence, market_regime)
    z_scores = prior["scores"].copy()
    for entry in evidence:
        for scenario in SCENARIOS:
            z_scores[scenario] += float(entry["contribution"].get(scenario, 0))
    probabilities = _softmax(z_scores)
    decision = _decision(probabilities=probabilities, position=position, evidence=evidence)
    top_evidence = _top_evidence(evidence)

    return {
        "symbol": symbol,
        "name": name,
        "horizon_days": horizon_days,
        "current_price": current_price,
        "position": position,
        "indicator": {
            "trend": indicator.get("trend"),
            "ma": indicator.get("ma", {}),
            "volume_ratio": indicator.get("volume_ratio"),
            "rsi14": indicator.get("rsi14"),
            "atr14": indicator.get("atr14"),
            "recent_high_20": indicator.get("recent_high_20"),
            "recent_low_20": indicator.get("recent_low_20"),
        },
        "chan": {
            "structure": chan.get("structure") if chan else None,
            "signal_type": chan.get("signal", {}).get("type") if chan else None,
            "signal_label": chan.get("signal", {}).get("label") if chan else None,
            "reason": chan.get("signal", {}).get("reason") if chan else None,
        },
        "prior": prior,
        "evidence": evidence,
        "z_scores": {key: round(value, 4) for key, value in z_scores.items()},
        "probabilities": probabilities,
        "decision": decision,
        "top_evidence": top_evidence,
        "evidence_summary": "；".join(top_evidence) if top_evidence else "证据不足",
    }


def _prior_scores(
    *,
    pool_context: dict[str, Any],
    indicator: dict[str, Any],
    current_price: float | None,
    market_regime: dict[str, Any] | None,
) -> dict[str, Any]:
    scores = {scenario: 0.0 for scenario in SCENARIOS}
    components: list[dict[str, Any]] = []

    positive_ratio = pool_context.get("positive_ratio")
    average_pct_change = pool_context.get("average_pct_change")
    if positive_ratio is not None:
        if positive_ratio >= 0.6:
            _apply_component(
                scores,
                components,
                "股票池短线广度",
                f"上涨股票占比 {positive_ratio:.0%}",
                {"up": 0.18, "range": 0.03, "down": -0.08},
            )
        elif positive_ratio <= 0.4:
            _apply_component(
                scores,
                components,
                "股票池短线广度",
                f"上涨股票占比 {positive_ratio:.0%}",
                {"up": -0.08, "range": 0.03, "down": 0.18},
            )
    if average_pct_change is not None:
        if average_pct_change >= 1:
            _apply_component(
                scores,
                components,
                "股票池平均涨跌",
                f"平均涨跌幅 {average_pct_change:.2f}%",
                {"up": 0.12, "range": 0, "down": -0.06},
            )
        elif average_pct_change <= -1:
            _apply_component(
                scores,
                components,
                "股票池平均涨跌",
                f"平均涨跌幅 {average_pct_change:.2f}%",
                {"up": -0.06, "range": 0, "down": 0.12},
            )

    regime = (market_regime or {}).get("regime")
    if regime:
        component = _market_regime_prior(regime)
        if component:
            _apply_component(
                scores,
                components,
                "市场状态",
                f"{(market_regime or {}).get('label') or regime} / {(market_regime or {}).get('confidence') or 'low'}",
                component,
            )

    atr_pct = _atr_pct(indicator, current_price)
    if atr_pct is not None:
        if atr_pct >= 5:
            _apply_component(
                scores,
                components,
                "波动率区间",
                f"ATR14/价格 {atr_pct:.2f}%",
                {"up": -0.05, "range": 0.14, "down": 0.12},
            )
        elif atr_pct <= 1.5:
            _apply_component(
                scores,
                components,
                "波动率区间",
                f"ATR14/价格 {atr_pct:.2f}%",
                {"up": 0.03, "range": 0.12, "down": -0.04},
            )

    return {"scores": scores, "components": components}


def _evidence_entries(
    *,
    quote: dict[str, Any] | None,
    bars: list[dict[str, Any]],
    indicator: dict[str, Any],
    chan: dict[str, Any] | None,
    position: dict[str, Any] | None,
    pool_context: dict[str, Any],
    current_price: float | None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    _ma_evidence(entries, indicator, current_price)
    _volume_evidence(entries, indicator, bars)
    _relative_strength_evidence(entries, quote, pool_context)
    _chan_evidence(entries, chan)
    _position_evidence(entries, position)
    _price_location_evidence(entries, indicator, current_price)
    return entries


def _ma_evidence(entries: list[dict[str, Any]], indicator: dict[str, Any], current_price: float | None) -> None:
    trend = indicator.get("trend")
    ma = indicator.get("ma", {})
    ma20 = _to_float(ma.get("ma20"))
    if trend == "bullish":
        _add_evidence(entries, "MA趋势", "MA5 位于 MA20 上方，趋势偏多", up=0.5, range=-0.05, down=-0.18, category="trend")
    elif trend == "bearish":
        _add_evidence(entries, "MA趋势", "MA5 位于 MA20 下方，趋势偏弱", up=-0.18, range=-0.05, down=0.5, category="trend")
    elif trend == "neutral":
        _add_evidence(entries, "MA趋势", "均线结构中性", up=0.02, range=0.22, down=0.02, category="mean_reversion")
    if current_price is not None and ma20:
        if current_price >= ma20:
            _add_evidence(entries, "趋势位置", f"现价位于 MA20 上方 {((current_price / ma20) - 1) * 100:.2f}%", up=0.2, range=0.02, down=-0.08, category="trend")
        else:
            _add_evidence(entries, "趋势位置", f"现价位于 MA20 下方 {((current_price / ma20) - 1) * 100:.2f}%", up=-0.08, range=0.02, down=0.2, category="risk")


def _volume_evidence(entries: list[dict[str, Any]], indicator: dict[str, Any], bars: list[dict[str, Any]]) -> None:
    volume_ratio = _to_float(indicator.get("volume_ratio"))
    recent_return = _return_pct(bars, 5)
    if volume_ratio is None:
        return
    if volume_ratio >= 1.5 and (recent_return or 0) >= 0:
        _add_evidence(entries, "成交量", f"成交量比 {volume_ratio:.2f}，放量配合上涨", up=0.26, range=-0.04, down=0.02, category="breakout")
    elif volume_ratio >= 1.5:
        _add_evidence(entries, "成交量", f"成交量比 {volume_ratio:.2f}，放量但价格未走强", up=-0.02, range=0.08, down=0.2, category="risk")
    elif volume_ratio <= 0.7:
        _add_evidence(entries, "成交量", f"成交量比 {volume_ratio:.2f}，缩量等待方向", up=-0.04, range=0.22, down=0.03, category="mean_reversion")


def _relative_strength_evidence(
    entries: list[dict[str, Any]],
    quote: dict[str, Any] | None,
    pool_context: dict[str, Any],
) -> None:
    pct_change = _to_float((quote or {}).get("pct_change"))
    average_pct_change = pool_context.get("average_pct_change")
    if pct_change is None or average_pct_change is None:
        return
    relative = pct_change - average_pct_change
    if relative >= 1:
        _add_evidence(entries, "相对强弱", f"涨跌幅强于股票池均值 {relative:.2f} 个百分点", up=0.25, range=0.02, down=-0.08, category="trend")
    elif relative <= -1:
        _add_evidence(entries, "相对强弱", f"涨跌幅弱于股票池均值 {abs(relative):.2f} 个百分点", up=-0.08, range=0.02, down=0.25, category="risk")
    else:
        _add_evidence(entries, "相对强弱", "与股票池均值接近", up=0.02, range=0.1, down=0.02, category="mean_reversion")


def _chan_evidence(entries: list[dict[str, Any]], chan: dict[str, Any] | None) -> None:
    signal_type = (chan or {}).get("signal", {}).get("type")
    structure = (chan or {}).get("structure")
    if signal_type in {"suspected_third_buy", "upward_leave"}:
        _add_evidence(entries, "缠论结构", f"{structure or ''} / {signal_type}", up=0.34, range=0.03, down=-0.08, category="breakout")
    elif signal_type == "extended_above_center":
        _add_evidence(entries, "缠论结构", "远离旧中枢上方，等待当前价附近新结构", up=0.08, range=0.24, down=0.12, category="risk")
    elif signal_type == "center_range":
        _add_evidence(entries, "缠论结构", "中枢震荡，方向未选择", up=0.02, range=0.3, down=0.02, category="mean_reversion")
    elif signal_type in {"suspected_third_sell", "downward_leave"}:
        _add_evidence(entries, "缠论结构", f"{structure or ''} / {signal_type}", up=-0.08, range=0.02, down=0.34, category="risk")
    elif signal_type == "extended_below_center":
        _add_evidence(entries, "缠论结构", "远离旧中枢下方，等待当前价附近新结构", up=0.02, range=0.18, down=0.22, category="risk")
    elif signal_type:
        _add_evidence(entries, "缠论结构", f"结构信号 {signal_type}", up=0, range=0.08, down=0, category="mean_reversion")


def _position_evidence(entries: list[dict[str, Any]], position: dict[str, Any] | None) -> None:
    if not position:
        _add_evidence(entries, "持仓状态", "未持仓，仅作为候选观察", up=0, range=0.08, down=0, category="mean_reversion")
        return
    pnl_pct = _to_float(position.get("pnl_pct"))
    if pnl_pct is None:
        return
    if pnl_pct >= 30:
        _add_evidence(entries, "持仓盈亏", f"浮盈 {pnl_pct:.2f}%，回撤敏感度提高", up=0.02, range=0.18, down=0.24, category="risk")
    elif pnl_pct >= 10:
        _add_evidence(entries, "持仓盈亏", f"浮盈 {pnl_pct:.2f}%，趋势仍需确认", up=0.1, range=0.12, down=0.04, category="mean_reversion")
    elif pnl_pct <= -8:
        _add_evidence(entries, "持仓盈亏", f"浮亏 {pnl_pct:.2f}%，风险证据抬升", up=-0.08, range=0.04, down=0.24, category="risk")
    else:
        _add_evidence(entries, "持仓盈亏", f"盈亏 {pnl_pct:.2f}%，接近成本区", up=0.03, range=0.12, down=0.03, category="mean_reversion")


def _price_location_evidence(
    entries: list[dict[str, Any]],
    indicator: dict[str, Any],
    current_price: float | None,
) -> None:
    if current_price is None:
        return
    high_20 = _to_float(indicator.get("recent_high_20"))
    low_20 = _to_float(indicator.get("recent_low_20"))
    if high_20 and current_price >= high_20 * 0.98:
        _add_evidence(entries, "价格位置", "接近20日高位，强势但追高风险增加", up=0.16, range=0.04, down=0.08, category="breakout")
    if low_20 and current_price <= low_20 * 1.03:
        _add_evidence(entries, "价格位置", "接近20日低位，弱势修复仍需确认", up=-0.04, range=0.08, down=0.18, category="risk")


def _decision(
    *,
    probabilities: dict[str, float],
    position: dict[str, Any] | None,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    up = probabilities["up"]
    range_prob = probabilities["range"]
    down = probabilities["down"]
    risk_level = _risk_level(down=down, evidence=evidence)
    if position:
        if risk_level == "high":
            key = "risk_review"
            label = "风险复核"
        elif up >= 0.5 and down < 0.3:
            key = "hold_observe"
            label = "持有观察"
        elif range_prob >= 0.42:
            key = "position_review"
            label = "仓位复核"
        else:
            key = "wait_confirm"
            label = "等待确认"
    else:
        if up >= 0.55 and down < 0.28:
            key = "watch_candidate"
            label = "重点观察"
        elif down >= 0.4:
            key = "avoid_watch"
            label = "暂缓观察"
        else:
            key = "wait_confirm"
            label = "等待确认"

    return {
        "key": key,
        "label": label,
        "risk_level": risk_level,
        "confidence": _confidence(max(probabilities.values())),
        "next_check": _next_check(key, probabilities),
    }


def _risk_level(*, down: float, evidence: list[dict[str, Any]]) -> str:
    risk_score = down
    if any(entry["source"] == "持仓盈亏" and entry["contribution"]["down"] >= 0.2 for entry in evidence):
        risk_score += 0.08
    if risk_score >= 0.48:
        return "high"
    if risk_score >= 0.34:
        return "medium"
    return "low"


def _confidence(max_probability: float) -> str:
    if max_probability >= 0.58:
        return "high"
    if max_probability >= 0.45:
        return "medium"
    return "low"


def _next_check(key: str, probabilities: dict[str, float]) -> str:
    if key == "risk_review":
        return "复核下跌情景证据是否继续增强，并检查持仓风险敞口。"
    if key == "hold_observe":
        return "观察上涨证据能否延续，重点看 MA、成交量和相对强弱。"
    if key == "position_review":
        return "等待震荡区间方向选择，复核持仓成本和浮盈回撤承受度。"
    if key == "watch_candidate":
        return "等待概率优势与价格触发条件同时出现，再纳入重点跟踪。"
    if key == "avoid_watch":
        return "先等待下跌证据降温或重新形成向上结构。"
    dominant = max(probabilities, key=lambda key: probabilities[key])
    return f"当前以{_scenario_label(dominant)}情景为主，等待更多证据确认。"


def _scenario_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {scenario: 0 for scenario in SCENARIOS}
    for item in items:
        probabilities = item.get("probabilities") or {}
        if probabilities:
            scenario = max(probabilities, key=lambda key: probabilities[key])
            counts[scenario] += 1
    return counts


def _next_steps(
    items: list[dict[str, Any]],
    failed_quote_symbols: list[str],
    failed_kline_symbols: list[str],
) -> list[str]:
    steps: list[str] = []
    if failed_quote_symbols:
        steps.append("补齐行情失败股票的现价数据")
    if failed_kline_symbols:
        steps.append("补齐K线失败股票的趋势和缠论证据")
    if any(item.get("decision", {}).get("risk_level") == "high" for item in items):
        steps.append("优先复核高风险持仓的证据账本")
    if any(item.get("decision", {}).get("key") == "watch_candidate" for item in items):
        steps.append("跟踪上涨概率占优但尚未持仓的候选股")
    if not steps:
        steps.append("等待新行情更新后继续观察概率变化")
    return steps


def _pool_context(quotes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    changes = [
        float(quote["pct_change"])
        for quote in quotes.values()
        if quote.get("pct_change") is not None
    ]
    if not changes:
        return {"average_pct_change": None, "positive_ratio": None}
    return {
        "average_pct_change": sum(changes) / len(changes),
        "positive_ratio": sum(1 for value in changes if value > 0) / len(changes),
    }


def _symbol_order(watchlist: list[dict[str, Any]], holdings: list[dict[str, Any]]) -> list[str]:
    ordered_watchlist = sorted(
        watchlist,
        key=lambda row: (
            int(row.get("priority") or 99),
            str(row.get("updated_at") or ""),
            int(row.get("id") or 0),
        ),
    )
    symbols: list[str] = []
    seen: set[str] = set()
    for row in ordered_watchlist + holdings:
        symbol = normalize_symbol(str(row["symbol"]))
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def _position_context(holding: dict[str, Any] | None, current_price: float | None) -> dict[str, Any] | None:
    if holding is None:
        return None
    quantity = _to_float(holding.get("quantity")) or 0
    cost_price = _to_float(holding.get("cost_price"))
    market_value = quantity * current_price if current_price is not None else None
    pnl = (
        quantity * (current_price - cost_price)
        if current_price is not None and cost_price is not None
        else None
    )
    pnl_pct = (
        ((current_price - cost_price) / cost_price) * 100
        if current_price is not None and cost_price not in {None, 0}
        else None
    )
    return {
        "holding_id": holding.get("id"),
        "quantity": quantity,
        "cost_price": cost_price,
        "market_value": round(market_value, 4) if market_value is not None else None,
        "pnl": round(pnl, 4) if pnl is not None else None,
        "pnl_pct": round(pnl_pct, 4) if pnl_pct is not None else None,
    }


def _current_price(quote: dict[str, Any] | None, bars: list[dict[str, Any]]) -> float | None:
    quote_price = _to_float((quote or {}).get("price"))
    if quote_price is not None:
        return quote_price
    if bars:
        ordered = sorted(bars, key=lambda bar: str(bar["trade_date"]))
        return _to_float(ordered[-1].get("close"))
    return None


def _return_pct(bars: list[dict[str, Any]], window: int) -> float | None:
    if len(bars) < 2:
        return None
    ordered = sorted(bars, key=lambda bar: str(bar["trade_date"]))
    last = _to_float(ordered[-1].get("close"))
    previous = _to_float(ordered[max(0, len(ordered) - window - 1)].get("close"))
    if last is None or previous in {None, 0}:
        return None
    return ((last - previous) / previous) * 100


def _atr_pct(indicator: dict[str, Any], current_price: float | None) -> float | None:
    atr = _to_float(indicator.get("atr14"))
    if atr is None or current_price in {None, 0}:
        return None
    return (atr / float(current_price)) * 100


def _apply_component(
    scores: dict[str, float],
    components: list[dict[str, Any]],
    source: str,
    observation: str,
    contribution: dict[str, float],
) -> None:
    for scenario in SCENARIOS:
        scores[scenario] += contribution.get(scenario, 0)
    components.append(
        {
            "source": source,
            "observation": observation,
            "contribution": {scenario: round(contribution.get(scenario, 0), 4) for scenario in SCENARIOS},
        }
    )


def _market_regime_prior(regime: str) -> dict[str, float] | None:
    priors = {
        "uptrend": {"up": 0.32, "range": 0.05, "down": -0.12},
        "downtrend": {"up": -0.12, "range": 0.05, "down": 0.32},
        "range": {"up": 0.02, "range": 0.28, "down": 0.02},
        "high_volatility_pressure": {"up": -0.16, "range": 0.18, "down": 0.35},
        "repair": {"up": 0.14, "range": 0.2, "down": -0.05},
    }
    return priors.get(regime)


def _apply_regime_weights(
    entries: list[dict[str, Any]],
    market_regime: dict[str, Any] | None,
) -> None:
    weights = ((market_regime or {}).get("strategy_bias") or {}).get("weights") or {}
    for entry in entries:
        category = str(entry.get("category") or "technical")
        weight = _to_float(weights.get(category)) or 1.0
        entry["regime_weight"] = round(weight, 4)
        entry["contribution"] = {
            scenario: round(float(entry["contribution"].get(scenario, 0)) * weight, 4)
            for scenario in SCENARIOS
        }


def _add_evidence(
    entries: list[dict[str, Any]],
    source: str,
    observation: str,
    *,
    up: float = 0,
    range: float = 0,  # noqa: A002 - scenario name is user-facing.
    down: float = 0,
    confidence: str = "medium",
    category: str = "technical",
) -> None:
    entries.append(
        {
            "source": source,
            "observation": observation,
            "category": category,
            "contribution": {
                "up": round(up, 4),
                "range": round(range, 4),
                "down": round(down, 4),
            },
            "confidence": confidence,
        }
    )


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    scaled = {key: value / SOFTMAX_TEMPERATURE for key, value in scores.items()}
    max_score = max(scaled.values())
    exp_values = {key: math.exp(value - max_score) for key, value in scaled.items()}
    total = sum(exp_values.values())
    return {key: round(value / total, 4) for key, value in exp_values.items()}


def _top_evidence(entries: list[dict[str, Any]], limit: int = 3) -> list[str]:
    scored = sorted(
        entries,
        key=lambda entry: max(abs(float(value)) for value in entry["contribution"].values()),
        reverse=True,
    )
    return [
        f"{entry['source']}：{entry['observation']}"
        for entry in scored[:limit]
    ]


def _scenario_label(scenario: str) -> str:
    return {
        "up": "上涨",
        "range": "震荡",
        "down": "下跌",
    }.get(scenario, scenario)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
