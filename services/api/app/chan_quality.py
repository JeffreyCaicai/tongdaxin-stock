"""Cutoff-aware diagnostics for fixed research input, without guessing trading sessions."""
from __future__ import annotations

from datetime import time, timedelta

from .market_time import completed_bars, local_timestamp, quality_issue


def daily_quality(dataset: dict, symbol: str, as_of: str) -> dict:
    cutoff = local_timestamp(as_of)
    cutoff_day = (cutoff.date() if cutoff.time() >= time(15) else cutoff.date() - timedelta(days=1)).isoformat()
    content = dataset["series"].get(symbol, {}).get("daily", {"bars": [], "issues": []})
    visible = [bar for bar in content["bars"] if bar["trade_date"] <= cutoff_day]
    bars, discovered = completed_bars(visible, period="daily", as_of=as_of)
    issues = content["issues"] + [i for i in dataset["issues"] if i["symbol"] == symbol and i["period"] == "daily"]
    issues = [dict(i) for i in issues if i["scope"] == "series" or i["bar_key"] <= cutoff_day]
    issues.extend({**i, "symbol": symbol} for i in discovered)
    calendar = dataset["calendar"]
    verified = calendar["verification"]["status"] == "verified"
    first_day = visible[0]["trade_date"] if visible else None
    covered = bool(verified and first_day and calendar["coverage_start"] <= first_day
                   and cutoff_day <= calendar["coverage_end"])
    expected = [day for day in calendar["sessions"] if first_day and first_day <= day <= cutoff_day] if verified else []
    present = {bar["trade_date"] for bar in visible}
    missing = sorted(set(expected) - present)
    issues.extend(quality_issue("missing_session", symbol=symbol, period="daily", bar_key=day) for day in missing)
    if verified:
        sessions = set(calendar["sessions"])
        issues.extend(quality_issue("calendar_conflict", symbol=symbol, period="daily", bar_key=day)
                      for day in present if calendar["coverage_start"] <= day <= calendar["coverage_end"] and day not in sessions)
    unique = {(i["scope"], i["bar_key"] or "", i["code"]): i for i in issues}
    issues = [unique[key] for key in sorted(unique)]
    blocked = {i["bar_key"] for i in issues if i["scope"] == "bar" and i["code"] != "truncated"}
    valid = [bar for bar in bars if bar["trade_date"] not in blocked]
    needs_review = len(valid) < 35 or any(i["code"] != "truncated" for i in issues)
    return {"symbol": symbol, "period": "daily", "as_of": cutoff.isoformat(),
            "status": "review" if needs_review else "checked" if covered else "limited",
            "input_bar_count": len(visible), "valid_bar_count": len(valid),
            "first_bar_at": valid[0]["bar_end_at"] if valid else None,
            "last_bar_at": valid[-1]["bar_end_at"] if valid else None,
            "expected_session_count": len(expected) if covered else None,
            "calendar_coverage_complete": covered if verified else None,
            "missing_sessions": missing, "issues": issues, "history_complete": False}


def dataset_quality(dataset: dict, as_of: str, symbols: list[str] | None = None) -> dict:
    items = [daily_quality(dataset, symbol, as_of) for symbol in
             (dataset["selection"]["symbols"] if symbols is None else symbols)]
    return {"items": items, "benchmark": daily_quality(dataset, "SH000300", as_of),
            "review_count": sum(item["status"] == "review" for item in items),
            "limited_count": sum(item["status"] == "limited" for item in items),
            "calendar_verification": dataset["calendar"]["verification"]["status"],
            "price_basis_verification": dataset["price_basis"]["verification"]["status"]}
