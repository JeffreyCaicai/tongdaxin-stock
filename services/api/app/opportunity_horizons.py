"""Versioned technical checklists, not calibrated holding-period probabilities."""
from __future__ import annotations

from datetime import date
from statistics import mean

from .indicators import calculate_indicator_snapshot
from .opportunity_prices import completed_daily_bars, local_timestamp

MODEL = "technical_horizons_v1"
# sessions: fast MA, slow MA, slope lookback, minimum history, stretch threshold
CONFIGS = {5: (5, 20, 5, 30, 8), 20: (20, 60, 5, 65, 15),
           60: (60, 120, 10, 130, 25), 120: (60, 180, 20, 200, 35)}


def assess_horizons(*, bars: list[dict], index_bars: list[dict], as_of: str,
                    regime: str, blocked: bool) -> dict:
    stock, stock_issues = completed_daily_bars(bars, as_of)
    index, index_issues = completed_daily_bars(index_bars, as_of)
    issues = stock_issues + index_issues
    if blocked:
        issues.append("quality_gate_failed")
    if not index or not stock or stock[-1]["trade_date"] != index[-1]["trade_date"]:
        issues.append("unaligned_daily_data")
    elif (local_timestamp(as_of).date() - date.fromisoformat(index[-1]["trade_date"])).days > 10:
        issues.append("stale_daily_data")
    by_date = {row["trade_date"]: row for row in stock}
    results = {}
    for sessions, (fast, slow, lag, required, stretch_limit) in CONFIGS.items():
        result = {"sessions": sessions, "model_version": MODEL, "market_regime": regime, "stance": "insufficient", "score": None,
                  "as_of": stock[-1]["trade_date"] if stock else None, "issues": sorted(set(issues)),
                  "evidence": [], "conditions": None, "metrics": {}}
        results[str(sessions)] = result
        if len(index) < required or len(stock) < required:
            result["issues"].append("insufficient_period_history")
        dates = [row["trade_date"] for row in index[-required:]]
        if any(day not in by_date for day in dates):
            result["issues"].append("missing_period_sessions")
        if result["issues"]:
            continue
        sample = [by_date[day] for day in dates]
        if any(row["volume"] is None or row["volume"] <= 0 for row in sample):
            result["issues"].append("inactive_period_sessions")
            continue
        closes = [row["close"] for row in sample]
        price = closes[-1]
        fast_ma, slow_ma = mean(closes[-fast:]), mean(closes[-slow:])
        previous_slow = mean(closes[-slow-lag:-lag])
        stock_return = (price / closes[-sessions-1] - 1) * 100
        index_return = (index[-1]["close"] / index[-sessions-1]["close"] - 1) * 100
        excess = stock_return - index_return
        indicator = calculate_indicator_snapshot(sample)
        atr = indicator["atr14"]
        volume_ratio = indicator["volume_ratio"]
        stretch_window = max(20, fast)
        deviation = (price / mean(closes[-stretch_window:]) - 1) * 100
        trend = 25 if price > fast_ma > slow_ma and slow_ma > previous_slow else -25 if price < fast_ma else 0
        relative = 15 if excess > 0 else -15 if excess < 0 else 0
        participation = 5 if volume_ratio >= .8 else -5
        volatility = -15 if atr / price * 100 > 6 else 0
        extended = deviation > stretch_limit
        score = max(0, min(100, 50 + trend + relative + participation + volatility - (15 if extended else 0)))
        stance = "favorable" if score >= 75 and trend > 0 and relative > 0 else "avoid" if score < 45 else "wait"
        if extended:
            result["issues"].append("extended")
        if regime in {"downtrend", "high_volatility_pressure", "unknown"}:
            result["issues"].append("market_caution")
        if result["issues"] and stance == "favorable":
            stance = "wait"
        result.update(stance=stance, score=score,
                      evidence=[{"group": "trend", "value": "trend_positive" if trend > 0 else "trend_negative" if trend < 0 else "trend_mixed", "points": trend},
                                {"group": "relative", "value": "relative_positive" if relative > 0 else "relative_negative" if relative < 0 else "relative_flat", "points": relative},
                                {"group": "volume", "value": "volume_confirmed" if participation > 0 else "volume_weak", "points": participation},
                                {"group": "risk", "value": "volatility_high" if volatility else "volatility_normal", "points": volatility - (15 if extended else 0)}],
                      metrics={"return_pct": round(stock_return, 3), "index_return_pct": round(index_return, 3),
                               "excess_pp": round(excess, 3), "ma_deviation_pct": round(deviation, 3),
                               "stretch_ma_window": stretch_window,
                               "volume_ratio": volume_ratio, "atr_pct": round(atr / price * 100, 3)},
                      conditions={"ma_window": fast, "ma_price": round(fast_ma, 3),
                                  "review_below": round(max(0, fast_ma - atr), 3),
                                  "requires": ["close_above_reference", "relative_strength_positive", "volume_confirmation"]})
    results["long_term"] = {"sessions": None, "model_version": MODEL, "stance": "insufficient", "score": None,
                            "as_of": None, "issues": ["fundamentals_unverified"], "evidence": [],
                            "conditions": None, "metrics": {}}
    return results
