"""Synthetic research fixtures, never a source of live verification metadata."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, timedelta


def rehash(dataset):
    dataset["dataset_id"] = hashlib.sha256(json.dumps(
        {key: value for key, value in dataset.items() if key != "dataset_id"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode()).hexdigest()
    return dataset


def verification(verified=True):
    return {"status": "verified" if verified else "unverified",
            "reference": "synthetic-fixture" if verified else None,
            "evidence_sha256": "1" * 64 if verified else None}


def daily_bar(day, close=10, **kwargs):
    return {"trade_date": day, "open": close, "high": close + 1, "low": close - 1,
            "close": close, "volume": 100, "amount": None, **kwargs}


def candidate_bars():
    pivots = [11, 10, 12, 10.5, 12, 10.5, 14, 12.7, 14.5, 13.8]
    bars = []
    for index in range((len(pivots) - 1) * 5 + 1):
        segment = min(index // 5, len(pivots) - 2)
        price = pivots[segment] + (pivots[segment + 1] - pivots[segment]) * (index - segment * 5) / 5
        bars.append(daily_bar((date(2026, 1, 1) + timedelta(days=index)).isoformat(), price,
                              high=price + .1, low=price - .1))
    return bars


def controlled_bars(count=40):
    return [daily_bar((date(2026, 1, 1) + timedelta(days=i)).isoformat(), 13, low=12.5, high=14)
            for i in range(count)]


def controlled_analyzer(states=None, *, direction="up", upper=12, lower=10):
    def analyze(*, symbol, bars, as_of):
        current = (states or {}).get(len(bars), "candidate")
        strokes = [{"direction": "up" if i % 2 == 0 else "down", "start_date": f"2026-01-{i*5+1:02}",
                    "end_date": f"2026-01-{i*5+6:02}", "confirmed": True, "confirmed_at": "2026-01-25"}
                   for i in range(3)]
        return {"signal": {"type": ("suspected_third_buy" if direction == "up" else "suspected_third_sell")
                           if current == "candidate" else "center_range", "status": current,
                           "reason": "synthetic", "trigger": "synthetic", "invalidation": "synthetic"},
                "data_quality": {"status": "partial" if current == "missing" else "complete", "issues": []},
                "latest_center": {"lower": lower, "upper": upper + (len(bars) - 35) * .05,
                                  "stroke_start": 0, "stroke_end": 2, "start_date": "2026-01-01",
                                  "end_date": bars[-1]["trade_date"]},
                "structure_key": "above", "chart": {"strokes": strokes}, "current_price": bars[-1]["close"]}
    return analyze


def make_dataset(*, series, sessions, as_of, calendar_verified=True, basis_verified=True):
    return rehash({
        "schema_version": "chan_dataset_v1", "dataset_id": "", "created_at": as_of,
        "selection": {"symbols": [s for s in series if s != "SH000300"],
                      "selected_at": as_of, "scope": "selected_sample"},
        "source": "synthetic", "as_of": as_of,
        "price_basis": {"parameters": {"TQFlag": 11}, "point_in_time_verified": False,
                        "verification": verification(basis_verified)},
        "calendar": {"sessions": sessions, "coverage_start": sessions[0], "coverage_end": sessions[-1],
                     "source": "synthetic", "version": "fixture-v1", "verification": verification(calendar_verified)},
        "series": {s: {p: {"bars": copy.deepcopy(bars), "issues": []} for p, bars in periods.items()}
                   for s, periods in series.items()},
        "issues": [], "collection": {"parser_version": "tdx_time_v1", "page_size": 1000,
                                      "max_pages": 1, "pages": [], "status": "bounded", "history_complete": False},
    })
