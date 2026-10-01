"""Strict, completed daily inputs shared by horizon assessment and follow-up."""
from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")


def local_timestamp(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must include its timezone")
    return timestamp.astimezone(SHANGHAI)


def completed_date(as_of: str) -> date:
    local = local_timestamp(as_of)
    return local.date() if local.time() >= time(15, 0) else local.date() - timedelta(days=1)


def finite_number(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def completed_daily_bars(bars: list[dict], as_of: str) -> tuple[list[dict], list[str]]:
    cutoff = completed_date(as_of)
    rows, issues = {}, set()
    for bar in bars:
        try:
            day = date.fromisoformat(str(bar.get("trade_date", ""))[:10])
        except ValueError:
            issues.add("invalid_daily_data")
            continue
        if day > cutoff:
            continue
        key = day.isoformat()
        if key in rows:
            issues.add("duplicate_dates")
        prices = {key: finite_number(bar.get(key)) for key in ("open", "high", "low", "close")}
        if any(p is None or p <= 0 for p in prices.values()) or not (
            prices["low"] <= min(prices["open"], prices["close"])
            <= max(prices["open"], prices["close"]) <= prices["high"]
        ):
            issues.add("invalid_daily_data")
            continue
        rows[key] = {**bar, **prices, "trade_date": key, "volume": finite_number(bar.get("volume"))}
    return [rows[key] for key in sorted(rows)], sorted(issues)
