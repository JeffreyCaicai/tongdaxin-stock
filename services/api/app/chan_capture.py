"""Bounded acquisition only; replay never imports this module."""
from __future__ import annotations

from datetime import datetime, timezone
import time

from .chan_dataset import canonical_symbol, dataset_id, validate_calendar, validate_dataset
from .market_time import (
    RESEARCH_PERIODS, bar_time, completed_bars, decode_tdx_bar_time, local_timestamp,
    normalize_period, quality_issue,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def capture_dataset(*, symbols: list[str], periods: list[str], as_of: str, page_size: int = 1000,
                    max_pages: int = 1, calendar: dict | None = None) -> dict:
    cutoff = local_timestamp(as_of).isoformat()
    symbols = list(dict.fromkeys(canonical_symbol(s) for s in symbols))
    symbols = [s for s in symbols if s != "SH000300"]
    periods = list(dict.fromkeys(normalize_period(p) for p in periods))
    if not 1 <= len(symbols) <= 10 or not periods or set(periods) - RESEARCH_PERIODS:
        raise ValueError("invalid_capture_selection")
    if type(page_size) is not int or not 1 <= page_size <= 1000 or type(max_pages) is not int or not 1 <= max_pages <= 5:
        raise ValueError("invalid_capture_limits")
    unverified = {"status": "unverified", "reference": None, "evidence_sha256": None}
    calendar = calendar if calendar is not None else {
        "sessions": [], "coverage_start": None, "coverage_end": None,
        "source": None, "version": None, "verification": dict(unverified),
    }
    validate_calendar(calendar)
    # Import authentication only after validating user input, and only on this acquisition path.
    from .market_data import MarketDataError, get_market_data_provider
    provider = get_market_data_provider("tdx-official")
    started = _now()
    dataset = {"schema_version": "chan_dataset_v1", "dataset_id": "", "created_at": started,
               "selection": {"symbols": symbols, "selected_at": started, "scope": "selected_sample"},
               "source": "tdx-official", "as_of": cutoff,
               "price_basis": {"parameters": {"TQFlag": 11}, "point_in_time_verified": False,
                               "verification": dict(unverified)},
               "calendar": calendar, "series": {}, "issues": [],
               "collection": {"parser_version": "tdx_time_v1", "page_size": page_size,
                              "max_pages": max_pages, "pages": [], "status": "bounded", "history_complete": False}}
    called = False
    for symbol in symbols + ["SH000300"]:
        dataset["series"][symbol] = {}
        for period in periods:
            accumulated, issues, oldest = [], [], None
            for page_number in range(max_pages):
                if called:
                    time.sleep(0.5)
                called = True
                page = {"symbol": symbol, "period": period, "start": page_number * page_size,
                        "limit": page_size, "fetched_at": _now(), "count": 0,
                        "first": None, "last": None, "status": "failed"}
                dataset["collection"]["pages"].append(page)
                try:
                    rows = provider.fetch_kline_page(symbol, period=period, limit=page_size, start=page["start"])
                    if not isinstance(rows, list) or len(rows) > page_size:
                        raise ValueError("invalid_page_size")
                    page["count"] = len(rows)
                    page["status"] = "received" if rows else "empty"
                    if not rows:
                        break
                    cleaned, page_issues = completed_bars(rows, period=period, as_of=cutoff)
                    issues.extend(page_issues)
                    # Use returned times, including newer-than-cutoff rows, to verify pagination direction.
                    keys = sorted(bar_time(r["trade_date"], period=period)["trade_date"] for r in rows)
                    page["first"], page["last"] = keys[0], keys[-1]
                    if oldest is not None and keys[0] >= oldest:
                        issues.append(quality_issue("pagination_not_advancing", period=period))
                        dataset["collection"]["status"] = "partial"
                        break
                    oldest = keys[0]
                    accumulated.extend(cleaned)
                except (MarketDataError, ValueError, TypeError, KeyError):
                    page["status"] = "failed"
                    issues.append(quality_issue("provider_unavailable", period=period))
                    dataset["collection"]["status"] = "partial"
                    break
            else:
                issues.append(quality_issue("truncated", period=period))
            bars, merged_issues = completed_bars(accumulated, period=period, as_of=cutoff)
            issues.extend(merged_issues)
            # A corrupt occurrence must not be repaired by an equal-time row from another page.
            blocked = {i["bar_key"] for i in issues if i["scope"] == "bar"}
            bars = [b for b in bars if b["trade_date"] not in blocked]
            if calendar["verification"]["status"] == "verified" and bars:
                first, last = bars[0]["session_date"], bars[-1]["session_date"]
                expected = [d for d in calendar["sessions"] if first <= d <= last]
                present = {b["session_date"] for b in bars}
                for day in expected:
                    if day not in present:
                        key = day if period == "daily" else day + "T15:00:00+08:00"
                        issues.append(quality_issue("missing_session", period=period, bar_key=key))
            if period != "daily" and bars:
                present = {b["trade_date"] for b in bars}
                days = {b["session_date"] for b in bars}
                for day in sorted(days):
                    for seconds in range(34500, 54001, 300):
                        try:
                            key = decode_tdx_bar_time({"Item": [day, seconds]}, period=period)["trade_date"]
                        except ValueError:
                            continue
                        if bars[0]["trade_date"] <= key <= bars[-1]["trade_date"] and key not in present:
                            issues.append(quality_issue("missing_bar", period=period, bar_key=key))
            if any(i["code"] != "truncated" for i in issues):
                dataset["collection"]["status"] = "partial"
            issues = [{**i, "symbol": symbol} for i in issues]
            dataset["series"][symbol][period] = {"bars": bars, "issues": issues}
            dataset["issues"].extend(issues)
    dataset["dataset_id"] = dataset_id(dataset)
    validate_dataset(dataset)
    return dataset
