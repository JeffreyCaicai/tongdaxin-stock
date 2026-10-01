"""Date-aligned price observations, not executable returns or predictive probabilities."""
from __future__ import annotations

from datetime import timedelta, time

from .chan_dataset import canonical_symbol, validate_dataset
from .market_time import completed_bars, finite_number, local_timestamp

HORIZONS = (5, 20, 60)


def _base_outcome() -> dict:
    return {"status": "unavailable", "issue": None, "start_date": None, "end_date": None,
            "benchmark_start_date": None, "benchmark_end_date": None, "entry_open": None,
            "end_close": None, "return_pct": None, "benchmark_return_pct": None, "excess_pp": None,
            "max_drawdown_pct": None, "overlapping": False}


def _window_outcome(observation, horizon, dataset, cutoff, cutoff_day, series):
    outcome = _base_outcome()
    calendar = dataset["calendar"]
    signal_day = local_timestamp(observation["first_seen_at"]).date().isoformat()
    if calendar["verification"]["status"] != "verified":
        outcome["issue"] = "unverified_calendar"
        return outcome
    if dataset["price_basis"]["verification"]["status"] != "verified":
        outcome["issue"] = "unverified_price_basis"
        return outcome
    days = calendar["sessions"]
    window = [d for d in days if d > signal_day][:horizon]
    covered = calendar["coverage_start"] <= signal_day <= calendar["coverage_end"]
    if not covered or (len(window) < horizon and calendar["coverage_end"] < cutoff_day):
        outcome["issue"] = "calendar_coverage_insufficient"
        return outcome
    if signal_day not in days:
        outcome["issue"] = "observation_calendar_conflict"
        return outcome
    scope_end = min(window[-1], cutoff_day) if len(window) == horizon else cutoff_day
    elapsed = [d for d in window if d <= cutoff_day]
    benchmark, bench_issues = series.get("SH000300", ({}, []))
    stock, stock_issues = series.get(observation["symbol"], ({}, []))
    if any(signal_day <= d <= scope_end and d not in days for d in benchmark):
        outcome["issue"] = "benchmark_calendar_conflict"
        return outcome
    for label, rows, issues in [("benchmark", benchmark, bench_issues), ("stock", stock, stock_issues)]:
        blockers = [i for i in issues if i["code"] != "truncated" and (i["scope"] == "series" or
                    signal_day < i["bar_key"][:10] <= scope_end)]
        if blockers:
            outcome["issue"] = label + "_data_quality"
            return outcome
        if any(d not in rows for d in elapsed):
            outcome["issue"] = label + "_missing_session"
            return outcome
        if any(rows[d]["volume"] is None or rows[d]["volume"] <= 0 for d in elapsed):
            outcome["issue"] = label + "_volume_unavailable"
            return outcome
    if len(elapsed) < horizon:
        outcome.update(status="pending", issue="horizon_not_matured")
        return outcome
    first, last = window[0], window[-1]
    entry, end = stock[first]["open"], stock[last]["close"]
    change = (end / entry - 1) * 100
    benchmark_change = (benchmark[last]["close"] / benchmark[first]["open"] - 1) * 100
    peak, drawdown = entry, 0.0
    for day in window:
        price = stock[day]["close"]
        peak = max(peak, price)
        drawdown = min(drawdown, (price / peak - 1) * 100)
    excess = change - benchmark_change
    if any(finite_number(n) is None for n in (change, benchmark_change, drawdown, excess)):
        outcome["issue"] = "invalid_numeric_outcome"
        return outcome
    outcome.update(status="matured", start_date=first, end_date=last, benchmark_start_date=first,
                   benchmark_end_date=last, entry_open=entry, end_close=end, return_pct=change,
                   benchmark_return_pct=benchmark_change, excess_pp=excess, max_drawdown_pct=drawdown)
    return outcome


def _mark_overlaps(items, sessions):
    # Adjacent windows in start-date order reveal overlap; retain the longest active endpoint.
    for horizon in HORIZONS:
        intervals = []
        for item in items:
            signal_day = local_timestamp(item["first_seen_at"]).date().isoformat()
            window = [d for d in sessions if d > signal_day][:horizon]
            if window:
                intervals.append((window[0], window[-1], item["outcomes"][str(horizon)]))
        end, owner = "", None
        for start, finish, outcome in sorted(intervals, key=lambda x: x[:2]):
            if owner is not None and start <= end:
                owner["overlapping"] = outcome["overlapping"] = True
            if finish > end:
                end, owner = finish, outcome


def evaluate_observations(*, observations: list[dict], dataset: dict, as_of: str) -> dict:
    validate_dataset(dataset)
    cutoff = local_timestamp(as_of)
    cutoff_day = (cutoff.date() if cutoff.time() >= time(15) else cutoff.date() - timedelta(days=1)).isoformat()
    unique = {}
    for observation in observations:
        if observation.get("direction") not in {"up", "down"} or canonical_symbol(observation.get("symbol")) not in dataset["selection"]["symbols"]:
            raise ValueError("invalid_observation_identity")
        if local_timestamp(observation["first_seen_at"]) > cutoff:
            raise ValueError("observation_not_visible")
        key = observation["observation_id"]
        if not isinstance(key, str) or not key:
            raise ValueError("invalid_observation_id")
        if key in unique and unique[key] != observation:
            raise ValueError("conflicting_observation_id")
        unique[key] = observation
    series = {}
    for symbol, periods in dataset["series"].items():
        content = periods.get("daily", {"bars": [], "issues": []})
        bars, issues = completed_bars(content["bars"], period="daily", as_of=as_of)
        issues += content["issues"] + [i for i in dataset["issues"] if i["symbol"] == symbol and i["period"] == "daily"]
        series[symbol] = ({bar["trade_date"]: bar for bar in bars}, issues)
    result = {"items": [], "summary": {}, "issues": [], "method": {
        "horizons": list(HORIZONS), "primary_horizon": 20, "scope": "selected_sample",
        "overlapping_samples_not_independent": True, "execution_costs_included": False,
        "tradeability_checked": False, "dividends_included": False, "short_returns_simulated": False,
        "price_basis_verification": dataset["price_basis"]["verification"]["status"],
        "calendar_verification": dataset["calendar"]["verification"]["status"],
    }}
    for observation in unique.values():
        result["items"].append({**{k: observation[k] for k in ("observation_id", "symbol", "direction", "first_seen_at")},
            "outcomes": {str(n): _window_outcome(observation, n, dataset, cutoff, cutoff_day, series) for n in HORIZONS}})
    _mark_overlaps(result["items"], dataset["calendar"]["sessions"])
    for horizon in HORIZONS:
        result["summary"][str(horizon)] = {}
        for direction in ("up", "down"):
            rows = [item["outcomes"][str(horizon)] for item in result["items"] if item["direction"] == direction]
            matured = [r for r in rows if r["status"] == "matured"]
            result["summary"][str(horizon)][direction] = {
                "total": len(rows), **{status: sum(r["status"] == status for r in rows)
                                       for status in ("matured", "pending", "unavailable")},
                **{"mean_" + field: sum(r[field] for r in matured) / len(matured) if matured else None
                   for field in ("return_pct", "excess_pp", "max_drawdown_pct")},
            }
    result["issues"] = sorted({r["issue"] for item in result["items"] for r in item["outcomes"].values()
                               if r["status"] == "unavailable" and r["issue"]})
    return result
