from __future__ import annotations

from copy import deepcopy

from typing import Any

from .repository import normalize_symbol, utc_now


def generate_stock_report(
    *,
    symbol: str,
    holding: dict[str, Any] | None,
    quote: dict[str, Any],
    indicators: dict[str, Any],
    recent_signals: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized_symbol = normalize_symbol(symbol)
    snapshot = indicators.get("snapshot", indicators)
    latest_signal = recent_signals[0] if recent_signals else None
    price = quote["price"]
    trend = snapshot.get("trend", "unknown")
    ma = snapshot.get("ma", {})
    pnl_text = "No holding record found."
    if holding:
        cost = float(holding["cost_price"])
        pnl_pct = ((price - cost) / cost) * 100
        pnl_text = f"Cost {cost:.3f}, current price {price:.3f}, unrealized P/L {pnl_pct:.2f}%."

    thesis = holding.get("initial_thesis") if holding else None
    risk_points = _risk_points(holding=holding, quote=quote, indicators=snapshot)
    action = latest_signal["action"] if latest_signal else "observe"

    return {
        "report_type": "stock_diagnosis",
        "symbol": normalized_symbol,
        "generated_at": utc_now(),
        "summary": (
            f"{normalized_symbol} is in {trend} technical state. "
            f"Current action focus: {action}."
        ),
        "sections": [
            {
                "title": "Position Context",
                "points": [
                    pnl_text,
                    f"Original thesis: {thesis or 'not recorded'}.",
                    f"Strategy horizon: {holding.get('strategy_horizon') if holding else 'n/a'}.",
                ],
            },
            {
                "title": "Technical Evidence",
                "points": [
                    f"Close {snapshot.get('close')}, MA5 {ma.get('ma5')}, MA20 {ma.get('ma20')}, MA60 {ma.get('ma60')}.",
                    f"MACD histogram {snapshot.get('macd', {}).get('hist')}, RSI14 {snapshot.get('rsi14')}, ATR14 {snapshot.get('atr14')}.",
                    f"Volume ratio versus 20-bar average: {snapshot.get('volume_ratio')}.",
                ],
            },
            {
                "title": "Risk Checklist",
                "points": risk_points,
            },
            {
                "title": "Next Plan",
                "points": [
                    latest_signal["next_check"] if latest_signal else "Wait for a fresh signal before changing the plan.",
                    "Keep manual confirmation before any buy or sell action.",
                ],
            },
        ],
        "data_refs": _data_refs(quote=quote, indicators=snapshot, latest_signal=latest_signal),
    }


def generate_trading_plan(
    *,
    holding: dict[str, Any],
    quote: dict[str, Any],
    indicators: dict[str, Any],
    signal: dict[str, Any],
) -> dict[str, Any]:
    symbol = normalize_symbol(holding["symbol"])
    price = float(quote["price"])
    stop_loss = holding.get("stop_loss")
    take_profit = holding.get("take_profit")

    return {
        "report_type": "trading_plan",
        "symbol": symbol,
        "generated_at": utc_now(),
        "summary": f"{symbol} plan is anchored on action '{signal['action']}' at price {price:.3f}.",
        "plan": {
            "action_signal": signal["action"],
            "risk_level": signal["risk_level"],
            "current_price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_rule": "No automatic order. Execute only after manual review.",
            "next_check": signal["next_check"],
        },
        "evidence": signal["reasons"],
        "data_refs": _data_refs(
            quote=quote,
            indicators=indicators.get("snapshot", indicators),
            latest_signal=signal,
        ),
    }


def generate_daily_review(
    *,
    holdings: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    fetch_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    action_counts: dict[str, int] = {}
    high_risk_signal_count = 0
    high_risk_symbols: list[str] = []
    high_risk_signals: list[dict[str, Any]] = []
    for signal in signals:
        action_counts[signal["action"]] = action_counts.get(signal["action"], 0) + 1
        if signal["risk_level"] == "high":
            high_risk_signal_count += 1
            symbol = signal["symbol"]
            if symbol not in high_risk_symbols:
                high_risk_symbols.append(symbol)
            high_risk_signals.append(signal)

    failed_fetches = [log for log in fetch_logs if log["status"] != "success"]

    return {
        "report_type": "daily_review",
        "generated_at": utc_now(),
        "summary": (
            f"Reviewed {len(holdings)} holdings and {len(signals)} recent signals. "
            f"High-risk symbols: {', '.join(high_risk_symbols) if high_risk_symbols else 'none'}."
        ),
        "holding_count": len(holdings),
        "signal_count": len(signals),
        "holding_details": [_holding_detail(holding) for holding in holdings[:12]],
        "recent_signal_details": [_signal_detail(signal) for signal in signals[:12]],
        "action_counts": action_counts,
        "high_risk_symbols": high_risk_symbols,
        "high_risk_signal_count": high_risk_signal_count,
        "high_risk_signal_details": [
            _signal_detail(signal) for signal in high_risk_signals[:8]
        ],
        "data_quality": {
            "fetch_log_count": len(fetch_logs),
            "failed_fetch_count": len(failed_fetches),
            "failed_fetches": [_fetch_detail(fetch) for fetch in failed_fetches[:10]],
        },
        "next_session_focus_keys": [
            "review_high_risk",
            "check_data_quality",
            "compare_with_thesis",
        ],
    }


def decision_report_comparison(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    previous_items = {item["symbol"]: item for item in previous.get("items", [])}
    current_items = {item["symbol"]: item for item in current.get("items", [])}
    changes = []
    for symbol, item in current_items.items():
        old = previous_items.get(symbol)
        if old is None:
            continue
        old_scores = old.get("probabilities") or {}
        new_scores = item.get("probabilities") or {}
        changes.append({
            "symbol": symbol,
            "previous_probabilities": old_scores,
            "current_probabilities": new_scores,
            "probability_changes": {
                scenario: round(new_scores[scenario] - old_scores[scenario], 4)
                for scenario in ("up", "range", "down")
                if scenario in old_scores and scenario in new_scores
            },
            "previous_decision": (old.get("decision") or {}).get("key"),
            "current_decision": (item.get("decision") or {}).get("key"),
        })
    return {
        "previous_generated_at": previous.get("generated_at"),
        "items": changes,
        "added_symbols": sorted(set(current_items) - set(previous_items)),
        "removed_symbols": sorted(set(previous_items) - set(current_items)),
    }


def generate_decision_review(
    review: dict[str, Any], analysis: dict[str, Any], symbols: set[str] | None
) -> dict[str, Any]:
    analysis = deepcopy(analysis)
    original_symbols = {item["symbol"] for item in analysis.get("items", [])}
    if symbols is not None:
        analysis["items"] = [item for item in analysis.get("items", []) if item["symbol"] in symbols]
    items = analysis.get("items", [])
    analysis.setdefault("scope", {})["symbol_count"] = len(items)
    analysis["review_scope"] = {
        "original_symbol_count": len(original_symbols),
        "not_analyzed_symbols": sorted(symbols - original_symbols) if symbols is not None else [],
        "excluded_symbols": sorted(original_symbols - symbols) if symbols is not None else [],
    }
    counts = dict.fromkeys(("up", "range", "down"), 0)
    for item in items:
        scores = item.get("probabilities") or {}
        if all(isinstance(scores.get(key), (int, float)) for key in counts):
            counts[max(counts, key=lambda key: scores[key])] += 1
    analysis["scenario_counts"] = counts
    quality = analysis.setdefault("data_quality", {})
    for kind in ("quote", "kline"):
        key = f"failed_{kind}_symbols"
        failures = quality.get(key, [])
        quality[key] = [symbol for symbol in failures if symbols is None or symbol in symbols]
        quality[f"failed_{kind}_count"] = len(quality[key])
    scope = analysis["review_scope"]
    if scope["excluded_symbols"] or scope["not_analyzed_symbols"]:
        analysis["summary"] = (
            f"复盘已保存分析：当前股票池可查看 {len(items)} 只股票的历史分析。"
            f"股票池成员已变化，{len(scope['not_analyzed_symbols'])} 只股票尚无本次分析结果；"
            "需重新运行决策引擎更新，以下评分和市场状态仍来自原分析快照。"
        )
        analysis["next_steps"] = [
            "重新分析股票池；尚未分析：" + (", ".join(scope["not_analyzed_symbols"]) or "无"),
            *(analysis.get("next_steps") or []),
        ]
    review["decision_analysis"] = analysis
    review["analysis_generated_at"] = analysis.get("generated_at")
    return review


def _holding_detail(holding: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": holding.get("symbol"),
        "name": holding.get("name"),
        "quantity": holding.get("quantity"),
        "cost_price": holding.get("cost_price"),
        "stop_loss": holding.get("stop_loss"),
        "take_profit": holding.get("take_profit"),
        "initial_thesis": holding.get("initial_thesis"),
    }


def _signal_detail(signal: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": signal.get("id"),
        "symbol": signal.get("symbol"),
        "signal_type": signal.get("signal_type"),
        "action": signal.get("action"),
        "risk_level": signal.get("risk_level"),
        "price": signal.get("price"),
        "strength": signal.get("strength"),
        "created_at": signal.get("created_at"),
        "next_check": signal.get("next_check"),
        "reasons": signal.get("reasons", []),
    }


def _fetch_detail(fetch: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": fetch.get("symbol"),
        "source": fetch.get("source"),
        "data_type": fetch.get("data_type"),
        "status": fetch.get("status"),
        "message": fetch.get("message"),
        "fetched_at": fetch.get("fetched_at"),
    }


def _risk_points(
    *,
    holding: dict[str, Any] | None,
    quote: dict[str, Any],
    indicators: dict[str, Any],
) -> list[str]:
    price = float(quote["price"])
    points: list[str] = []
    if holding and holding.get("stop_loss") is not None:
        stop_loss = float(holding["stop_loss"])
        distance = ((price - stop_loss) / price) * 100
        points.append(f"Distance to planned stop loss: {distance:.2f}%.")
    else:
        points.append("Stop loss is not recorded.")

    ma20 = indicators.get("ma", {}).get("ma20")
    if ma20 is not None:
        points.append(f"Distance to MA20: {((price - ma20) / price) * 100:.2f}%.")

    if indicators.get("trend") == "bearish":
        points.append("Moving-average trend is bearish.")
    if indicators.get("volume_ratio") is not None and indicators["volume_ratio"] < 0.7:
        points.append("Volume is below recent average; signal confirmation may be weak.")
    if len(points) < 2:
        points.append("No immediate technical risk flag from available data.")
    return points


def _data_refs(
    *,
    quote: dict[str, Any],
    indicators: dict[str, Any],
    latest_signal: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    refs = [
        {
            "type": "quote_snapshot",
            "id": quote.get("snapshot_id"),
            "fetched_at": quote.get("fetched_at"),
            "price": quote.get("price"),
        },
        {
            "type": "indicator_snapshot",
            "as_of": indicators.get("as_of"),
            "bars": indicators.get("bars"),
        },
    ]
    if latest_signal:
        refs.append(
            {
                "type": "signal",
                "id": latest_signal.get("id"),
                "signal_type": latest_signal.get("signal_type"),
                "created_at": latest_signal.get("created_at"),
            }
        )
    return refs
