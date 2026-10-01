"""Synthetic research fixtures, never a source of live verification metadata."""
from __future__ import annotations

import copy
import hashlib
import json


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
