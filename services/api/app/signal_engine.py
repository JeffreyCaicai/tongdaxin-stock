from __future__ import annotations

from typing import Any


def evaluate_holding_signal(
    holding: dict[str, Any],
    *,
    current_price: float,
    source_snapshot_id: int | None = None,
    indicators: dict[str, Any] | None = None,
) -> dict[str, Any]:
    symbol = str(holding["symbol"]).upper()
    cost_price = float(holding["cost_price"])
    stop_loss = _to_float(holding.get("stop_loss"))
    take_profit = _to_float(holding.get("take_profit"))
    max_loss_pct = _to_float(holding.get("max_loss_pct"))

    pnl_pct = ((current_price - cost_price) / cost_price) * 100
    reasons: list[str] = [
        f"Current price {current_price:.3f}, cost price {cost_price:.3f}, unrealized P/L {pnl_pct:.2f}%."
    ]

    if stop_loss is not None and current_price <= stop_loss:
        reasons.append(f"Price is at or below planned stop loss {stop_loss:.3f}.")
        return _signal(
            symbol=symbol,
            signal_type="hard_stop_loss",
            action="exit_or_reduce",
            strength=1.0,
            price=current_price,
            risk_level="high",
            reasons=reasons,
            next_check="Confirm liquidity, position size and whether the stop-loss plan is still valid.",
            source_snapshot_id=source_snapshot_id,
            pnl_pct=pnl_pct,
        )

    if take_profit is not None and current_price >= take_profit:
        reasons.append(f"Price is at or above planned take profit {take_profit:.3f}.")
        return _signal(
            symbol=symbol,
            signal_type="take_profit",
            action="trim_or_review",
            strength=0.85,
            price=current_price,
            risk_level="medium",
            reasons=reasons,
            next_check="Review trend strength and decide whether to trim, trail, or hold.",
            source_snapshot_id=source_snapshot_id,
            pnl_pct=pnl_pct,
        )

    if max_loss_pct is not None and pnl_pct <= -max_loss_pct:
        reasons.append(
            f"Loss has reached configured max tolerated loss {max_loss_pct:.2f}%."
        )
        return _signal(
            symbol=symbol,
            signal_type="max_loss_warning",
            action="review_risk",
            strength=0.75,
            price=current_price,
            risk_level="high",
            reasons=reasons,
            next_check="Check whether the position should be reduced before the hard stop.",
            source_snapshot_id=source_snapshot_id,
            pnl_pct=pnl_pct,
        )

    if indicators and indicators.get("bars", 0) > 0:
        technical_signal = _evaluate_technical_rules(
            symbol=symbol,
            current_price=current_price,
            reasons=reasons,
            source_snapshot_id=source_snapshot_id,
            pnl_pct=pnl_pct,
            indicators=indicators,
        )
        if technical_signal is not None:
            return technical_signal

    reasons.append("No stop-loss, take-profit, or max-loss trigger fired.")
    return _signal(
        symbol=symbol,
        signal_type="hold_observe",
        action="hold",
        strength=0.35,
        price=current_price,
        risk_level="low" if pnl_pct >= 0 else "medium",
        reasons=reasons,
        next_check="Wait for price, trend, volume, or plan-level confirmation.",
        source_snapshot_id=source_snapshot_id,
        pnl_pct=pnl_pct,
    )


def _signal(
    *,
    symbol: str,
    signal_type: str,
    action: str,
    strength: float,
    price: float,
    risk_level: str,
    reasons: list[str],
    next_check: str,
    source_snapshot_id: int | None,
    pnl_pct: float,
    indicators: dict[str, Any] | None = None,
) -> dict[str, Any]:
    extra = {"pnl_pct": round(pnl_pct, 4)}
    if indicators:
        extra["indicators"] = indicators
    return {
        "symbol": symbol,
        "signal_type": signal_type,
        "action": action,
        "strength": strength,
        "price": price,
        "risk_level": risk_level,
        "reasons": reasons,
        "next_check": next_check,
        "source_snapshot_id": source_snapshot_id,
        "extra": extra,
    }


def _evaluate_technical_rules(
    *,
    symbol: str,
    current_price: float,
    reasons: list[str],
    source_snapshot_id: int | None,
    pnl_pct: float,
    indicators: dict[str, Any],
) -> dict[str, Any] | None:
    ma = indicators.get("ma", {})
    ma5 = _to_float(ma.get("ma5"))
    ma20 = _to_float(ma.get("ma20"))
    ma60 = _to_float(ma.get("ma60"))
    rsi14 = _to_float(indicators.get("rsi14"))
    atr14 = _to_float(indicators.get("atr14"))
    volume_ratio = _to_float(indicators.get("volume_ratio"))
    recent_high_20 = _to_float(indicators.get("recent_high_20"))
    macd_hist = _to_float(indicators.get("macd", {}).get("hist"))
    trend = str(indicators.get("trend", "unknown"))

    reasons.append(
        f"Technical snapshot as of {indicators.get('as_of')}: trend={trend}, "
        f"MA5={_fmt(ma5)}, MA20={_fmt(ma20)}, RSI14={_fmt(rsi14)}, "
        f"ATR14={_fmt(atr14)}, volume ratio={_fmt(volume_ratio)}."
    )

    if ma20 is not None and current_price < ma20 and ma5 is not None and ma5 < ma20:
        reasons.append("Price is below MA20 and MA5 is also below MA20, indicating trend damage.")
        return _signal(
            symbol=symbol,
            signal_type="trend_break",
            action="reduce_or_watch",
            strength=0.82,
            price=current_price,
            risk_level="high" if pnl_pct < 0 else "medium",
            reasons=reasons,
            next_check="Check whether price can reclaim MA20 with improving volume.",
            source_snapshot_id=source_snapshot_id,
            pnl_pct=pnl_pct,
            indicators=indicators,
        )

    if (
        recent_high_20 is not None
        and current_price >= recent_high_20 * 0.995
        and volume_ratio is not None
        and volume_ratio >= 1.4
        and trend in {"bullish", "neutral"}
    ):
        reasons.append("Price is testing the recent 20-bar high with volume expansion.")
        return _signal(
            symbol=symbol,
            signal_type="volume_breakout",
            action="breakout_watch",
            strength=0.78,
            price=current_price,
            risk_level="medium",
            reasons=reasons,
            next_check="Wait for close above resistance and avoid chasing if volume fades.",
            source_snapshot_id=source_snapshot_id,
            pnl_pct=pnl_pct,
            indicators=indicators,
        )

    if (
        ma20 is not None
        and atr14 is not None
        and abs(current_price - ma20) <= atr14 * 0.6
        and ma5 is not None
        and ma5 >= ma20
        and (rsi14 is None or 35 <= rsi14 <= 68)
    ):
        reasons.append("Price is near MA20 while short-term trend remains above it.")
        return _signal(
            symbol=symbol,
            signal_type="pullback_confirm",
            action="hold_or_plan_add",
            strength=0.66,
            price=current_price,
            risk_level="medium",
            reasons=reasons,
            next_check="Look for stabilization near MA20 and define invalidation before adding.",
            source_snapshot_id=source_snapshot_id,
            pnl_pct=pnl_pct,
            indicators=indicators,
        )

    if macd_hist is not None and macd_hist < 0 and trend == "bearish":
        reasons.append("MACD histogram is negative while moving averages are bearish.")
        return _signal(
            symbol=symbol,
            signal_type="momentum_weakness",
            action="review_risk",
            strength=0.62,
            price=current_price,
            risk_level="medium",
            reasons=reasons,
            next_check="Avoid adding until momentum and trend stop deteriorating.",
            source_snapshot_id=source_snapshot_id,
            pnl_pct=pnl_pct,
            indicators=indicators,
        )

    return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"
