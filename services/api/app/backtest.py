from __future__ import annotations

from typing import Any

from .indicators import calculate_indicator_snapshot
from .repository import normalize_symbol, utc_now


DEFAULT_STRATEGY = "ma_volume_trend_v1"


def run_ma_volume_backtest(
    *,
    symbol: str,
    bars: list[dict[str, Any]],
    initial_equity: float = 100000.0,
    stop_loss_pct: float = 6.0,
    take_profit_pct: float = 12.0,
) -> dict[str, Any]:
    ordered = sorted(bars, key=lambda bar: str(bar["trade_date"]))
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []
    equity = initial_equity
    peak_equity = initial_equity
    max_drawdown_pct = 0.0
    open_trade: dict[str, Any] | None = None

    for index, bar in enumerate(ordered):
        close = float(bar["close"])
        snapshot = calculate_indicator_snapshot(ordered[: index + 1])

        if open_trade:
            entry_price = float(open_trade["entry_price"])
            pnl_pct = ((close - entry_price) / entry_price) * 100
            exit_reason = None
            if pnl_pct <= -stop_loss_pct:
                exit_reason = "stop_loss"
            elif pnl_pct >= take_profit_pct:
                exit_reason = "take_profit"
            elif _exit_signal(snapshot, close):
                exit_reason = "trend_exit"

            if exit_reason:
                trade_return = pnl_pct / 100
                equity = equity * (1 + trade_return)
                open_trade.update(
                    {
                        "exit_date": bar["trade_date"],
                        "exit_price": round(close, 4),
                        "exit_reason": exit_reason,
                        "return_pct": round(pnl_pct, 4),
                    }
                )
                trades.append(open_trade)
                open_trade = None

        if open_trade is None and _entry_signal(snapshot, close):
            open_trade = {
                "symbol": normalize_symbol(symbol),
                "entry_date": bar["trade_date"],
                "entry_price": round(close, 4),
                "entry_reason": "ma_volume_trend",
            }

        peak_equity = max(peak_equity, equity)
        drawdown_pct = ((equity - peak_equity) / peak_equity) * 100
        max_drawdown_pct = min(max_drawdown_pct, drawdown_pct)
        equity_curve.append(
            {
                "trade_date": bar["trade_date"],
                "equity": round(equity, 4),
                "drawdown_pct": round(drawdown_pct, 4),
            }
        )

    if open_trade and ordered:
        close = float(ordered[-1]["close"])
        entry_price = float(open_trade["entry_price"])
        pnl_pct = ((close - entry_price) / entry_price) * 100
        open_trade.update(
            {
                "exit_date": ordered[-1]["trade_date"],
                "exit_price": round(close, 4),
                "exit_reason": "end_of_data",
                "return_pct": round(pnl_pct, 4),
            }
        )
        trades.append(open_trade)

    metrics = _metrics(trades, initial_equity, equity, max_drawdown_pct)
    return {
        "strategy_name": DEFAULT_STRATEGY,
        "symbol": normalize_symbol(symbol),
        "generated_at": utc_now(),
        "bar_count": len(ordered),
        "metrics": metrics,
        "trades": trades,
        "equity_curve": equity_curve,
        "rules": {
            "entry": "Close above MA20 with MA5 >= MA20, trend not bearish, and volume ratio >= 1.0.",
            "exit": "Stop loss, take profit, or close below MA20 with bearish short MA structure.",
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
        },
    }


def review_signal_outcomes(
    *,
    signals: list[dict[str, Any]],
    latest_prices: dict[str, float],
) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for signal in signals:
        symbol = normalize_symbol(signal["symbol"])
        current_price = latest_prices.get(symbol)
        if current_price is None or signal.get("price") is None:
            outcome = "unverified"
            move_pct = None
        else:
            entry_price = float(signal["price"])
            move_pct = ((current_price - entry_price) / entry_price) * 100
            outcome = _outcome_for_action(signal["action"], move_pct)
        reviews.append(
            {
                "signal_id": signal.get("id"),
                "symbol": symbol,
                "action": signal["action"],
                "signal_type": signal["signal_type"],
                "signal_price": signal.get("price"),
                "current_price": current_price,
                "move_pct": round(move_pct, 4) if move_pct is not None else None,
                "outcome": outcome,
            }
        )
    return reviews


def _entry_signal(snapshot: dict[str, Any], close: float) -> bool:
    ma = snapshot.get("ma", {})
    ma5 = ma.get("ma5")
    ma20 = ma.get("ma20")
    if ma5 is None or ma20 is None:
        return False
    return (
        close >= ma20
        and ma5 >= ma20
        and snapshot.get("trend") != "bearish"
        and (snapshot.get("volume_ratio") or 0) >= 1.0
    )


def _exit_signal(snapshot: dict[str, Any], close: float) -> bool:
    ma = snapshot.get("ma", {})
    ma5 = ma.get("ma5")
    ma20 = ma.get("ma20")
    if ma5 is None or ma20 is None:
        return False
    return close < ma20 and ma5 < ma20


def _metrics(
    trades: list[dict[str, Any]],
    initial_equity: float,
    ending_equity: float,
    max_drawdown_pct: float,
) -> dict[str, Any]:
    wins = [trade for trade in trades if trade["return_pct"] > 0]
    losses = [trade for trade in trades if trade["return_pct"] <= 0]
    average_win = sum(trade["return_pct"] for trade in wins) / len(wins) if wins else 0
    average_loss = (
        abs(sum(trade["return_pct"] for trade in losses) / len(losses))
        if losses
        else 0
    )
    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / len(trades), 4) if trades else 0,
        "average_win_pct": round(average_win, 4),
        "average_loss_pct": round(average_loss, 4),
        "risk_reward_ratio": round(average_win / average_loss, 4)
        if average_loss
        else None,
        "total_return_pct": round(((ending_equity - initial_equity) / initial_equity) * 100, 4),
        "max_drawdown_pct": round(abs(max_drawdown_pct), 4),
    }


def _outcome_for_action(action: str, move_pct: float) -> str:
    if action in {"hold", "hold_or_plan_add", "breakout_watch"}:
        if move_pct > 1:
            return "favorable"
        if move_pct < -1:
            return "unfavorable"
        return "neutral"
    if action in {"exit_or_reduce", "reduce_or_watch", "review_risk", "trim_or_review"}:
        if move_pct < -1:
            return "risk_reduced_or_warning_valid"
        if move_pct > 1:
            return "early_or_false_warning"
        return "neutral"
    return "neutral"
