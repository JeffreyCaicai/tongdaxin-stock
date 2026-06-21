from __future__ import annotations

from typing import Any


REGIME_LABELS = {
    "uptrend": "上升趋势",
    "downtrend": "下降趋势",
    "range": "震荡",
    "high_volatility_pressure": "高波动压力",
    "repair": "修复期",
    "unknown": "状态不足",
}

REGIME_KEYS = (
    "uptrend",
    "downtrend",
    "range",
    "high_volatility_pressure",
    "repair",
)


def infer_market_regime(
    *,
    index_bars: list[dict[str, Any]] | None = None,
    pool_quotes: dict[str, dict[str, Any]] | None = None,
    pool_kline_by_symbol: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    scores = {key: 0.0 for key in REGIME_KEYS}
    evidence: list[dict[str, Any]] = []
    index_stats = _index_stats(index_bars or [])
    breadth = _market_breadth(pool_quotes or {})
    pool_trend = _pool_trend(pool_kline_by_symbol or {})

    _score_index_trend(scores, evidence, index_stats)
    _score_market_breadth(scores, evidence, breadth)
    _score_pool_trend(scores, evidence, pool_trend)
    _score_volatility_pressure(scores, evidence, index_stats, breadth)
    _score_repair(scores, evidence, index_stats, breadth)
    _score_range(scores, evidence, index_stats)

    if not evidence or max(scores.values()) <= 0:
        regime = "unknown"
        confidence = "low"
    else:
        regime = max(scores, key=lambda key: scores[key])
        confidence = _confidence(scores, regime)

    return {
        "model": "rule_state_machine_v1",
        "regime": regime,
        "label": REGIME_LABELS.get(regime, regime),
        "confidence": confidence,
        "scores": {key: round(value, 4) for key, value in scores.items()},
        "evidence": evidence,
        "index": index_stats,
        "breadth": breadth,
        "pool_trend": pool_trend,
        "strategy_bias": _strategy_bias(regime),
    }


def _index_stats(bars: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(bars, key=lambda bar: str(bar.get("trade_date") or ""))
    closes = [_to_float(bar.get("close")) for bar in ordered]
    closes = [value for value in closes if value is not None]
    if len(closes) < 35:
        return {
            "bar_count": len(closes),
            "current": closes[-1] if closes else None,
            "ma20": None,
            "ma60": None,
            "ma20_slope_pct": None,
            "return20_pct": None,
            "return60_pct": None,
            "avg_range20_pct": None,
            "ma20_crosses_30": None,
        }

    ma20_series = _rolling_sma(closes, 20)
    ma60_series = _rolling_sma(closes, 60)
    ma20 = ma20_series[-1]
    ma60 = ma60_series[-1] if ma60_series else None
    ma20_previous = ma20_series[-11] if len(ma20_series) >= 11 else None
    current = closes[-1]
    return20 = _return_pct(closes, 20)
    return60 = _return_pct(closes, 60)
    ranges = []
    for bar in ordered[-20:]:
        high = _to_float(bar.get("high"))
        low = _to_float(bar.get("low"))
        close = _to_float(bar.get("close"))
        if high is None or low is None or close in {None, 0}:
            continue
        ranges.append((high - low) / float(close) * 100)

    return {
        "bar_count": len(closes),
        "current": round(current, 4),
        "ma20": round(ma20, 4) if ma20 is not None else None,
        "ma60": round(ma60, 4) if ma60 is not None else None,
        "ma20_slope_pct": _safe_pct(ma20, ma20_previous),
        "return20_pct": round(return20, 4) if return20 is not None else None,
        "return60_pct": round(return60, 4) if return60 is not None else None,
        "avg_range20_pct": round(sum(ranges) / len(ranges), 4) if ranges else None,
        "ma20_crosses_30": _ma_crosses(closes, ma20_series, 30),
    }


def _market_breadth(quotes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    changes = [
        float(quote["pct_change"])
        for quote in quotes.values()
        if quote.get("pct_change") is not None
    ]
    if not changes:
        return {
            "sample_size": 0,
            "positive_ratio": None,
            "weak_ratio": None,
            "average_pct_change": None,
        }
    return {
        "sample_size": len(changes),
        "positive_ratio": sum(1 for value in changes if value > 0) / len(changes),
        "weak_ratio": sum(1 for value in changes if value <= -1) / len(changes),
        "average_pct_change": sum(changes) / len(changes),
    }


def _pool_trend(kline_by_symbol: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    trend_votes: list[str] = []
    for bars in kline_by_symbol.values():
        ordered = sorted(bars, key=lambda bar: str(bar.get("trade_date") or ""))
        closes = [_to_float(bar.get("close")) for bar in ordered]
        closes = [value for value in closes if value is not None]
        if len(closes) < 30:
            continue
        ma20 = _sma(closes[-20:])
        ma20_previous = _sma(closes[-30:-10])
        current = closes[-1]
        if ma20 is None or ma20_previous is None:
            continue
        if current > ma20 and ma20 > ma20_previous:
            trend_votes.append("up")
        elif current < ma20 and ma20 < ma20_previous:
            trend_votes.append("down")
        else:
            trend_votes.append("range")
    if not trend_votes:
        return {"sample_size": 0, "up_ratio": None, "down_ratio": None, "range_ratio": None}
    return {
        "sample_size": len(trend_votes),
        "up_ratio": trend_votes.count("up") / len(trend_votes),
        "down_ratio": trend_votes.count("down") / len(trend_votes),
        "range_ratio": trend_votes.count("range") / len(trend_votes),
    }


def _score_index_trend(
    scores: dict[str, float],
    evidence: list[dict[str, Any]],
    stats: dict[str, Any],
) -> None:
    current = stats.get("current")
    ma20 = stats.get("ma20")
    ma60 = stats.get("ma60")
    slope = stats.get("ma20_slope_pct")
    return60 = stats.get("return60_pct")
    if current is None or ma20 is None:
        return
    if ma60 is not None and current > ma20 > ma60 and (slope or 0) > 0 and (return60 or 0) > 0:
        _add_score(
            scores,
            evidence,
            source="指数趋势",
            observation="指数位于 MA20/MA60 上方，MA20 斜率向上",
            contribution={"uptrend": 0.56, "downtrend": -0.18, "range": -0.08},
        )
    elif ma60 is not None and current < ma20 < ma60 and (slope or 0) < 0:
        _add_score(
            scores,
            evidence,
            source="指数趋势",
            observation="指数位于 MA20/MA60 下方，MA20 斜率向下",
            contribution={"downtrend": 0.52, "high_volatility_pressure": 0.18, "uptrend": -0.14},
        )
    elif current > ma20 and ma60 is not None and current < ma60:
        _add_score(
            scores,
            evidence,
            source="指数趋势",
            observation="指数站回 MA20，但仍未收复 MA60",
            contribution={"repair": 0.36, "range": 0.12, "downtrend": -0.06},
        )


def _score_market_breadth(
    scores: dict[str, float],
    evidence: list[dict[str, Any]],
    breadth: dict[str, Any],
) -> None:
    positive_ratio = breadth.get("positive_ratio")
    weak_ratio = breadth.get("weak_ratio")
    average_pct_change = breadth.get("average_pct_change")
    if positive_ratio is not None and positive_ratio >= 0.62:
        _add_score(
            scores,
            evidence,
            source="股票池宽度",
            observation=f"上涨占比 {positive_ratio:.0%}，平均涨跌幅 {(average_pct_change or 0):.2f}%",
            contribution={"uptrend": 0.28, "repair": 0.1, "downtrend": -0.08},
        )
    if weak_ratio is not None and weak_ratio >= 0.5:
        _add_score(
            scores,
            evidence,
            source="股票池宽度",
            observation=f"跌幅超过 1% 的股票占比 {weak_ratio:.0%}",
            contribution={"high_volatility_pressure": 0.28, "downtrend": 0.18, "uptrend": -0.08},
        )
    if average_pct_change is not None and average_pct_change <= -1:
        _add_score(
            scores,
            evidence,
            source="股票池宽度",
            observation=f"股票池平均涨跌幅 {average_pct_change:.2f}%",
            contribution={"high_volatility_pressure": 0.18, "downtrend": 0.14},
        )


def _score_pool_trend(
    scores: dict[str, float],
    evidence: list[dict[str, Any]],
    pool_trend: dict[str, Any],
) -> None:
    up_ratio = pool_trend.get("up_ratio")
    down_ratio = pool_trend.get("down_ratio")
    range_ratio = pool_trend.get("range_ratio")
    if up_ratio is not None and up_ratio >= 0.6:
        _add_score(
            scores,
            evidence,
            source="股票池趋势",
            observation=f"股票池内 {up_ratio:.0%} 的样本处于 MA20 上行结构",
            contribution={"uptrend": 0.2, "repair": 0.08},
        )
    if down_ratio is not None and down_ratio >= 0.5:
        _add_score(
            scores,
            evidence,
            source="股票池趋势",
            observation=f"股票池内 {down_ratio:.0%} 的样本处于 MA20 下行结构",
            contribution={"downtrend": 0.2, "high_volatility_pressure": 0.08},
        )
    if range_ratio is not None and range_ratio >= 0.6:
        _add_score(
            scores,
            evidence,
            source="股票池趋势",
            observation=f"股票池内 {range_ratio:.0%} 的样本趋势不明确",
            contribution={"range": 0.18},
        )


def _score_volatility_pressure(
    scores: dict[str, float],
    evidence: list[dict[str, Any]],
    stats: dict[str, Any],
    breadth: dict[str, Any],
) -> None:
    avg_range = stats.get("avg_range20_pct")
    return20 = stats.get("return20_pct")
    weak_ratio = breadth.get("weak_ratio")
    if avg_range is None:
        return
    if avg_range >= 2.6 and ((return20 or 0) <= -4 or (weak_ratio or 0) >= 0.45):
        _add_score(
            scores,
            evidence,
            source="波动压力",
            observation=f"20日平均振幅 {avg_range:.2f}%，且指数/股票池走弱",
            contribution={
                "high_volatility_pressure": 0.68,
                "downtrend": 0.12,
                "uptrend": -0.1,
                "repair": -0.06,
            },
        )
    elif avg_range >= 2.6:
        _add_score(
            scores,
            evidence,
            source="波动压力",
            observation=f"20日平均振幅 {avg_range:.2f}%，波动抬升",
            contribution={"range": 0.12, "high_volatility_pressure": 0.16},
        )


def _score_repair(
    scores: dict[str, float],
    evidence: list[dict[str, Any]],
    stats: dict[str, Any],
    breadth: dict[str, Any],
) -> None:
    current = stats.get("current")
    ma20 = stats.get("ma20")
    ma60 = stats.get("ma60")
    return20 = stats.get("return20_pct")
    positive_ratio = breadth.get("positive_ratio")
    if current is None or ma20 is None or ma60 is None:
        return
    if current > ma20 and current < ma60 and (return20 or 0) > 0 and (positive_ratio or 0) >= 0.45:
        _add_score(
            scores,
            evidence,
            source="修复条件",
            observation="指数止跌并站回 MA20，但中期趋势尚未完全恢复",
            contribution={"repair": 0.34, "range": 0.12, "downtrend": -0.08},
        )


def _score_range(
    scores: dict[str, float],
    evidence: list[dict[str, Any]],
    stats: dict[str, Any],
) -> None:
    return20 = stats.get("return20_pct")
    slope = stats.get("ma20_slope_pct")
    crosses = stats.get("ma20_crosses_30")
    if crosses is not None and crosses >= 4:
        _add_score(
            scores,
            evidence,
            source="震荡特征",
            observation=f"近30根K线反复穿越 MA20 {crosses} 次",
            contribution={"range": 0.34, "uptrend": -0.06, "downtrend": -0.06},
        )
    elif return20 is not None and abs(return20) <= 2 and slope is not None and abs(slope) <= 0.3:
        _add_score(
            scores,
            evidence,
            source="震荡特征",
            observation="20日涨跌幅和 MA20 斜率都较低",
            contribution={"range": 0.24},
        )


def _strategy_bias(regime: str) -> dict[str, Any]:
    weights_by_regime = {
        "uptrend": {
            "trend": 1.2,
            "breakout": 1.18,
            "mean_reversion": 0.92,
            "risk": 0.95,
        },
        "downtrend": {
            "trend": 0.82,
            "breakout": 0.72,
            "mean_reversion": 0.86,
            "risk": 1.3,
        },
        "range": {
            "trend": 0.86,
            "breakout": 0.76,
            "mean_reversion": 1.2,
            "risk": 1.02,
        },
        "high_volatility_pressure": {
            "trend": 0.76,
            "breakout": 0.64,
            "mean_reversion": 0.78,
            "risk": 1.42,
        },
        "repair": {
            "trend": 0.96,
            "breakout": 0.9,
            "mean_reversion": 1.1,
            "risk": 1.1,
        },
        "unknown": {
            "trend": 1.0,
            "breakout": 1.0,
            "mean_reversion": 1.0,
            "risk": 1.0,
        },
    }
    summary_by_regime = {
        "uptrend": "顺势和突破证据权重提高，普通回撤风险权重略降。",
        "downtrend": "风险证据权重提高，突破和趋势跟随证据需要折扣。",
        "range": "均值回归和中枢内证据权重提高，追突破证据折扣。",
        "high_volatility_pressure": "风险证据显著加权，突破、趋势和超跌修复证据都需要降权。",
        "repair": "修复期重视回踩确认，风险证据仍保持偏高权重。",
        "unknown": "市场状态证据不足，暂不调整个股证据权重。",
    }
    return {
        "weights": weights_by_regime.get(regime, weights_by_regime["unknown"]),
        "summary": summary_by_regime.get(regime, summary_by_regime["unknown"]),
    }


def _confidence(scores: dict[str, float], regime: str) -> str:
    ordered = sorted(scores.values(), reverse=True)
    if len(ordered) < 2 or scores[regime] <= 0:
        return "low"
    margin = ordered[0] - ordered[1]
    if margin >= 0.28 and scores[regime] >= 0.5:
        return "high"
    if margin >= 0.12:
        return "medium"
    return "low"


def _add_score(
    scores: dict[str, float],
    evidence: list[dict[str, Any]],
    *,
    source: str,
    observation: str,
    contribution: dict[str, float],
) -> None:
    for key, value in contribution.items():
        if key in scores:
            scores[key] += value
    evidence.append(
        {
            "source": source,
            "observation": observation,
            "contribution": {
                key: round(contribution.get(key, 0), 4)
                for key in REGIME_KEYS
            },
        }
    )


def _rolling_sma(values: list[float], window: int) -> list[float]:
    if len(values) < window:
        return []
    return [
        sum(values[index - window:index]) / window
        for index in range(window, len(values) + 1)
    ]


def _sma(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _return_pct(values: list[float], window: int) -> float | None:
    if len(values) <= window:
        return None
    previous = values[-window - 1]
    current = values[-1]
    if previous == 0:
        return None
    return (current - previous) / previous * 100


def _safe_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in {None, 0}:
        return None
    return round((current - float(previous)) / float(previous) * 100, 4)


def _ma_crosses(closes: list[float], ma_series: list[float], lookback: int) -> int | None:
    if not ma_series:
        return None
    aligned = list(zip(closes[-len(ma_series):], ma_series))
    recent = aligned[-lookback:]
    states = [1 if close >= ma else -1 for close, ma in recent]
    if len(states) < 2:
        return None
    return sum(1 for previous, current in zip(states, states[1:]) if previous != current)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
