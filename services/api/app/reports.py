from __future__ import annotations

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
    for signal in signals:
        action_counts[signal["action"]] = action_counts.get(signal["action"], 0) + 1
        if signal["risk_level"] == "high":
            high_risk_signal_count += 1
            symbol = signal["symbol"]
            if symbol not in high_risk_symbols:
                high_risk_symbols.append(symbol)

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
        "action_counts": action_counts,
        "high_risk_symbols": high_risk_symbols,
        "high_risk_signal_count": high_risk_signal_count,
        "data_quality": {
            "fetch_log_count": len(fetch_logs),
            "failed_fetch_count": len(failed_fetches),
            "failed_fetches": failed_fetches[:10],
        },
        "next_session_focus_keys": [
            "review_high_risk",
            "check_data_quality",
            "compare_with_thesis",
        ],
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
