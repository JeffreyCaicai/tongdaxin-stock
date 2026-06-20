from __future__ import annotations

from typing import Any


MA_WINDOWS = (5, 10, 20, 60)


def calculate_indicator_snapshot(bars: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = _ordered_bars(bars)
    if not ordered:
        return {"bars": 0}

    closes = [_as_float(bar["close"]) for bar in ordered]
    highs = [_as_float(bar["high"]) for bar in ordered]
    lows = [_as_float(bar["low"]) for bar in ordered]
    volumes = [_as_float(bar.get("volume")) for bar in ordered]

    ma = {f"ma{window}": _last_sma(closes, window) for window in MA_WINDOWS}
    volume_ma5 = _last_sma(volumes, 5)
    volume_ma20 = _last_sma(volumes, 20)
    macd = _last_macd(closes)
    rsi14 = _last_rsi(closes, 14)
    atr14 = _last_atr(highs, lows, closes, 14)
    recent_high_20 = max(highs[-20:]) if len(highs) >= 1 else None
    recent_low_20 = min(lows[-20:]) if len(lows) >= 1 else None
    latest_volume = volumes[-1]
    volume_ratio = (
        round(latest_volume / volume_ma20, 4)
        if latest_volume is not None and volume_ma20
        else None
    )

    return {
        "bars": len(ordered),
        "as_of": ordered[-1]["trade_date"],
        "close": round(closes[-1], 4),
        "ma": ma,
        "macd": macd,
        "rsi14": rsi14,
        "atr14": atr14,
        "volume_ma5": volume_ma5,
        "volume_ma20": volume_ma20,
        "volume_ratio": volume_ratio,
        "recent_high_20": round(recent_high_20, 4) if recent_high_20 else None,
        "recent_low_20": round(recent_low_20, 4) if recent_low_20 else None,
        "trend": _trend_label(ma),
    }


def build_indicator_series(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = _ordered_bars(bars)
    series: list[dict[str, Any]] = []
    for index in range(len(ordered)):
        window = ordered[: index + 1]
        snapshot = calculate_indicator_snapshot(window)
        series.append({"trade_date": ordered[index]["trade_date"], **snapshot})
    return series


def _ordered_bars(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(bars, key=lambda bar: str(bar["trade_date"]))


def _last_sma(values: list[float | None], window: int) -> float | None:
    clean_values = [value for value in values if value is not None]
    if len(clean_values) < window:
        return None
    sample = clean_values[-window:]
    return round(sum(sample) / window, 4)


def _ema(values: list[float], window: int) -> list[float]:
    if not values:
        return []
    multiplier = 2 / (window + 1)
    output = [values[0]]
    for value in values[1:]:
        output.append((value - output[-1]) * multiplier + output[-1])
    return output


def _last_macd(closes: list[float]) -> dict[str, float | None]:
    if len(closes) < 35:
        return {"dif": None, "dea": None, "hist": None}
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    dif_values = [fast - slow for fast, slow in zip(ema12, ema26)]
    dea_values = _ema(dif_values, 9)
    dif = dif_values[-1]
    dea = dea_values[-1]
    hist = (dif - dea) * 2
    return {"dif": round(dif, 4), "dea": round(dea, 4), "hist": round(hist, 4)}


def _last_rsi(closes: list[float], window: int) -> float | None:
    if len(closes) <= window:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for previous, current in zip(closes[-window - 1 : -1], closes[-window:]):
        change = current - previous
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    average_gain = sum(gains) / window
    average_loss = sum(losses) / window
    if average_loss == 0:
        return 100.0
    rs = average_gain / average_loss
    return round(100 - (100 / (1 + rs)), 4)


def _last_atr(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    window: int,
) -> float | None:
    if len(closes) <= window:
        return None
    true_ranges: list[float] = []
    for index in range(1, len(closes)):
        high = highs[index]
        low = lows[index]
        previous_close = closes[index - 1]
        true_ranges.append(
            max(high - low, abs(high - previous_close), abs(low - previous_close))
        )
    return round(sum(true_ranges[-window:]) / window, 4)


def _trend_label(ma: dict[str, float | None]) -> str:
    ma5 = ma.get("ma5")
    ma20 = ma.get("ma20")
    ma60 = ma.get("ma60")
    if ma5 is None or ma20 is None:
        return "unknown"
    if ma5 > ma20 and (ma60 is None or ma20 >= ma60):
        return "bullish"
    if ma5 < ma20 and (ma60 is None or ma20 <= ma60):
        return "bearish"
    return "neutral"


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
