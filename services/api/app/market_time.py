"""Time and price validation without configuration, I/O, or a market calendar."""
from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")
RESEARCH_PERIODS = {"daily", "5min", "60min"}


def normalize_period(period: str) -> str:
    aliases = {"day": "daily", "d": "daily", "week": "weekly", "w": "weekly",
               "month": "monthly", "m": "monthly", "hour": "60min"}
    aliases.update({f"{n}m": f"{n}min" for n in (1, 5, 15, 30, 60)})
    value = aliases.get(str(period).strip().lower(), str(period).strip().lower())
    if value not in {"daily", "weekly", "monthly", "1min", "5min", "15min", "30min", "60min"}:
        raise ValueError("unsupported_period")
    return value


def local_timestamp(value: str) -> datetime:
    try:
        stamp = datetime.fromisoformat(value)
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError
        return stamp.astimezone(SHANGHAI)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("timezone_required_or_invalid_timestamp") from None


def session_date(value: object) -> date:
    text = str(value)
    try:
        if len(text) == 8 and text.isascii() and text.isdigit():
            return datetime.strptime(text, "%Y%m%d").date()
        if len(text) == 10:
            return date.fromisoformat(text)
    except ValueError:
        pass
    raise ValueError("invalid_session_date")


def _seconds(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("invalid_bar_clock")
    text = str(value)
    if text.isascii() and text.isdigit():
        result = int(text)
    else:
        try:
            clock = time.fromisoformat(text)
            if clock.tzinfo or clock.microsecond:
                raise ValueError
            result = clock.hour * 3600 + clock.minute * 60 + clock.second
        except ValueError:
            raise ValueError("invalid_bar_clock") from None
    if not 0 <= result < 86400:
        raise ValueError("invalid_bar_clock")
    return result


def _check_endpoint(seconds: int, period: str) -> None:
    if period == "60min":
        valid = seconds in (37800, 41400, 50400, 54000)
    elif period == "5min":
        valid = seconds % 300 == 0 and (34500 <= seconds <= 41400 or 47100 <= seconds <= 54000)
    else:
        raise ValueError("unverified_period")
    if not valid:
        raise ValueError("invalid_bar_endpoint")


def decode_tdx_bar_time(row: dict, *, period: str) -> dict:
    period = normalize_period(period)
    if period not in RESEARCH_PERIODS:
        raise ValueError("unverified_period")
    values = row.get("Item", row.get("item", []))
    values = values if isinstance(values, list) else []
    days = [session_date(row[key]) for key in ("TradeDate", "trade_date", "Date", "date", "日期")
            if row.get(key) is not None]
    if values:
        days.append(session_date(values[0]))
    if not days:
        raise ValueError("missing_bar_date")
    if len(set(days)) != 1:
        raise ValueError("conflicting_bar_date")
    day = days[0]
    seconds = 54000
    if period != "daily":
        clocks = [_seconds(row[key]) for key in ("Time", "time", "时间") if row.get(key) is not None]
        if len(values) > 1:
            clocks.append(_seconds(values[1]))
        if not clocks:
            raise ValueError("missing_bar_clock")
        if len(set(clocks)) != 1:
            raise ValueError("conflicting_bar_clock")
        seconds = clocks[0]
        _check_endpoint(seconds, period)
    end = (datetime.combine(day, time(), SHANGHAI) + timedelta(seconds=seconds)).isoformat()
    return {"trade_date": day.isoformat() if period == "daily" else end,
            "session_date": day.isoformat(), "bar_end_at": end,
            "time_semantics": "daily_close" if period == "daily" else "bar_end_assumed_unverified"}


def bar_time(value: object, *, period: str) -> dict:
    period = normalize_period(period)
    if period == "daily":
        return decode_tdx_bar_time({"Date": value}, period=period)
    stamp = local_timestamp(value)
    if stamp.microsecond:
        raise ValueError("invalid_bar_endpoint")
    seconds = stamp.hour * 3600 + stamp.minute * 60 + stamp.second
    _check_endpoint(seconds, period)
    return {"trade_date": stamp.isoformat(), "session_date": stamp.date().isoformat(),
            "bar_end_at": stamp.isoformat(), "time_semantics": "bar_end_assumed_unverified"}


def finite_number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def price_values(row: dict) -> dict:
    prices = {field: finite_number(row.get(field)) for field in ("open", "high", "low", "close")}
    if any(value is None or value <= 0 for value in prices.values()):
        raise ValueError("invalid_ohlc")
    if not prices["low"] <= min(prices["open"], prices["close"]) <= max(prices["open"], prices["close"]) <= prices["high"]:
        raise ValueError("invalid_ohlc")
    return {**prices, "volume": finite_number(row.get("volume")), "amount": finite_number(row.get("amount"))}


def quality_issue(code: str, *, period: str, bar_key: str | None = None, symbol: str = "") -> dict:
    return {"code": code, "symbol": symbol, "period": period, "bar_key": bar_key,
            "scope": "bar" if bar_key else "series"}


def completed_bars(bars: list[dict], *, period: str, as_of: str) -> tuple[list[dict], list[dict]]:
    period = normalize_period(period)
    cutoff = local_timestamp(as_of)
    by_key, blocked, issues = {}, set(), []
    for row in bars:
        key = None
        try:
            metadata = bar_time(row.get("trade_date"), period=period)
            key = metadata["trade_date"]
            if local_timestamp(metadata["bar_end_at"]) > cutoff:
                continue
            prices = price_values(row)
            normalized = {**prices, **metadata}
            if key in by_key and by_key[key] != normalized:
                raise ValueError("conflicting_duplicate")
            by_key[key] = normalized
        except (ValueError, AttributeError):
            code = "invalid_bar_time" if key is None else "invalid_ohlc"
            if key in by_key:
                code = "conflicting_duplicate"
            issues.append(quality_issue(code, period=period, bar_key=key))
            blocked.add(key)
    return [by_key[key] for key in sorted(by_key) if key not in blocked], issues
