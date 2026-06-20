from __future__ import annotations

from typing import Any


def evaluate_holding_signal(
    holding: dict[str, Any],
    *,
    current_price: float,
    source_snapshot_id: int | None = None,
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
) -> dict[str, Any]:
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
        "extra": {"pnl_pct": round(pnl_pct, 4)},
    }


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
