"""Fail closed when the frozen daily model or its price/identity dependency changes."""
from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

from . import chan_analysis, repository
from .chan_dataset import digest
from .market_time import bar_time, local_timestamp

SOURCE_HASHES = {
    "chan_analysis.py": "88723b84f88667db5d3a8b903c612fa6fec211f1b15c814e6f2e7e2a9984e332",
    "opportunity_prices.py": "23c896ab207fa31bf3b68d5b9db1637da13175b3b25a77b090fff82f5fbcf2a5",
}
NORMALIZE_HASH = "c63c55755001a7698e3e4a741cb92c5b2abfb9084906bb5876701ce78d5dd25c"
MODEL_VERSION = "daily_pen_overlap_v2"
RULE_CONFIG = {"minimum_bars": 35, "invalidation_mode": "close", "anchor_version": 1,
               "candidate_only": True, "period": "daily"}


def baseline_fingerprint() -> str:
    folder = Path(__file__).parent
    actual = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in SOURCE_HASHES}
    normalize_hash = hashlib.sha256(inspect.getsource(repository.normalize_symbol).encode()).hexdigest()
    if actual != SOURCE_HASHES or normalize_hash != NORMALIZE_HASH or chan_analysis.MODEL_VERSION != MODEL_VERSION:
        raise ValueError("baseline_mismatch")
    return digest({"sources": actual, "normalize_symbol": normalize_hash,
                   "model": MODEL_VERSION, "rules": RULE_CONFIG})


def visible_daily_prefix(bars: list[dict], *, as_of: str) -> list[dict]:
    cutoff, previous, visible = local_timestamp(as_of), "", []
    for bar in bars:
        metadata = bar_time(bar.get("trade_date"), period="daily")
        if local_timestamp(metadata["bar_end_at"]) > cutoff:
            continue
        key = metadata["trade_date"]
        if key <= previous:
            raise ValueError("non_increasing_bars")
        previous = key
        visible.append(bar)
    return visible


def analyze_frame(*, symbol: str, bars: list[dict], as_of: str) -> dict:
    baseline_fingerprint()
    prefix = visible_daily_prefix(bars, as_of=as_of)
    return chan_analysis.analyze_chan_structure(symbol=symbol, bars=prefix, period="daily", as_of=as_of)
