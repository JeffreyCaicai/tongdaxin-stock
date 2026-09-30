"""Single local scan worker; each database operation owns its connection."""
from __future__ import annotations

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from pathlib import Path

from .database import connect
from .market_data import get_market_data_provider
from .opportunity_discovery import discover_candidates, canonical_stock
from .opportunities import build_opportunity_report, merge_candidates
from .repository import utc_now

_lock = threading.Lock()
_active: dict[str, threading.Event] = {}


def read_run(db, run_id: str) -> dict | None:
    row = db.execute("SELECT * FROM opportunity_runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["progress"] = json.loads(result.pop("progress_json"))
    result["result"] = json.loads(result.pop("result_json") or "null")
    return result


def recover_runs(db) -> None:
    db.execute("UPDATE opportunity_runs SET status = 'interrupted', updated_at = ? WHERE status IN ('queued', 'running')", (utc_now(),))
    db.commit()


def _update(path: Path, run_id: str, status: str, progress: dict, result=None):
    with closing(connect(path)) as db:
        db.execute("UPDATE opportunity_runs SET status=?, progress_json=?, result_json=?, updated_at=? WHERE id=?",
                   (status, json.dumps(progress, ensure_ascii=False), json.dumps(result, ensure_ascii=False) if result is not None else None, utc_now(), run_id))
        db.commit()


def start_run(db, *, path: Path, pool: dict, watchlist: list[dict], holdings: list[dict], source: str, limit: int) -> dict:
    with _lock:
        if _active:
            active_id = next(iter(_active))
            existing = read_run(db, active_id)
            if existing and existing["pool_id"] == pool["id"] and existing["source"] == source:
                return existing
            raise RuntimeError("Another scan is running")
        run_id, now = uuid.uuid4().hex, utc_now()
        progress = {"stage": "discovering", "completed": 0, "total": 0}
        db.execute("INSERT INTO opportunity_runs VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
                   (run_id, pool["id"], source, "queued", now, now, json.dumps(progress)))
        db.commit()
        cancel = threading.Event()
        _active[run_id] = cancel
        thread = threading.Thread(target=_worker, args=(path, run_id, cancel, pool, watchlist, holdings, source, limit), daemon=True)
        thread.start()
        return read_run(db, run_id)


def cancel_run(run_id: str) -> bool:
    with _lock:
        cancel = _active.get(run_id)
        if cancel is not None:
            cancel.set()
            return True
    return False


def _worker(path, run_id, cancel, pool, watchlist, holdings, source, limit):
    progress = {"stage": "discovering", "completed": 0, "total": 0}
    try:
        _update(path, run_id, "running", progress)
        discovery = discover_candidates(source, 120, cancel.is_set)
        candidates = merge_candidates(discovery.pop("items"), watchlist, holdings, limit)
        discovery["outside_limit"] = limit
        progress.update(stage="analyzing", total=len(candidates))
        _update(path, run_id, "running", progress)
        quotes, klines, failures = {}, {}, []
        index_bars = []
        if not cancel.is_set():
            try:
                index_bars = get_market_data_provider(source).fetch_kline("SH000300", limit=240)
            except Exception:
                failures.append({"symbol": "SH000300", "kind": "index_unavailable"})

        def fetch(candidate):
            symbol = candidate["symbol"]
            q, bars, errors = None, [], []
            if canonical_stock(symbol) is None:
                return symbol, q, bars, [{"symbol": symbol, "kind": "outside_stock_scope"}]
            if cancel.is_set():
                return symbol, q, bars, errors
            provider = get_market_data_provider(source)
            try:
                q = provider.fetch_quote(symbol)
            except Exception:
                errors.append({"symbol": symbol, "kind": "quote_unavailable"})
            if not cancel.is_set():
                try:
                    bars = provider.fetch_kline(symbol, limit=240)
                except Exception:
                    errors.append({"symbol": symbol, "kind": "kline_unavailable"})
            return symbol, q, bars, errors

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetch, item) for item in candidates] if not cancel.is_set() else []
            for future in as_completed(futures):
                if cancel.is_set():
                    for pending in futures:
                        pending.cancel()
                    break
                symbol, quote, bars, errors = future.result()
                if quote:
                    quotes[symbol] = quote
                if bars:
                    klines[symbol] = bars
                failures.extend(errors)
                progress["completed"] += 1
                _update(path, run_id, "running", progress)
        if cancel.is_set():
            _update(path, run_id, "cancelled", progress)
            return
        report = build_opportunity_report(candidates=candidates, quotes=quotes, klines=klines,
                                          index_bars=index_bars, source=source, discovery=discovery,
                                          failures=failures, pool=pool)
        with _lock:
            if cancel.is_set():
                _update(path, run_id, "cancelled", progress)
            else:
                progress["stage"] = "completed"
                _update(path, run_id, "completed", progress, report)
            _active.pop(run_id, None)
    except Exception:
        progress["stage"] = "scan_failed"
        _update(path, run_id, "failed", progress)
    finally:
        with _lock:
            _active.pop(run_id, None)
