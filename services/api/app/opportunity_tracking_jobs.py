"""Bounded, cancellable follow-ups; original recommendation snapshots stay immutable."""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from pathlib import Path

from .database import connect
from .market_data import get_market_data_provider
from .opportunity_discovery import canonical_stock
from .opportunity_tracking import evaluate_followup
from .repository import utc_now

_lock = threading.Lock()
_active: dict[str, threading.Event] = {}


def read_followup(db, run: dict) -> dict:
    row = db.execute("SELECT * FROM opportunity_followups WHERE run_id=?", (run["id"],)).fetchone()
    result = {"run_id": run["id"], "source": run["source"], "report_type": "opportunity_followup",
              "generated_at": (run.get("result") or {}).get("generated_at"),
              "status": "not_started", "progress": {}, "result": None}
    if row:
        result.update(dict(row))
        result["progress"] = json.loads(result.pop("progress_json"))
        result["result"] = json.loads(result.pop("result_json") or "null")
    return result


def _write(path, run_id, status, progress, result=None):
    with closing(connect(path)) as db:
        db.execute("UPDATE opportunity_followups SET status=?,updated_at=?,progress_json=?,result_json=COALESCE(?,result_json) WHERE run_id=?",
                   (status, utc_now(), json.dumps(progress), json.dumps(result, ensure_ascii=False) if result is not None else None, run_id))
        db.commit()


def start_followup(db, *, path: Path, run: dict) -> dict:
    with _lock:
        if run["id"] in _active:
            return read_followup(db, run)
        if _active:
            raise RuntimeError("Another follow-up is running")
        now = utc_now()
        progress = {"completed": 0, "total": len(run["result"].get("items", []))}
        db.execute("""INSERT INTO opportunity_followups VALUES (?, 'queued', ?, ?, ?, NULL)
                   ON CONFLICT(run_id) DO UPDATE SET status='queued',requested_at=excluded.requested_at,
                   updated_at=excluded.updated_at,progress_json=excluded.progress_json""",
                   (run["id"], now, now, json.dumps(progress)))
        db.commit()
        cancel = threading.Event()
        _active[run["id"]] = cancel
        threading.Thread(target=_worker, args=(path, run, now, cancel, progress), daemon=True).start()
        return read_followup(db, run)


def cancel_followup(run_id: str) -> bool:
    with _lock:
        event = _active.get(run_id)
        if event:
            event.set()
            return True
        return False


def _worker(path, run, as_of, cancel, progress):
    run_id = run["id"]
    try:
        _write(path, run_id, "running", progress)
        failures, klines = [], {}
        def fetch(symbol):
            if cancel.is_set():
                return symbol, [], None
            if symbol != "SH000300" and canonical_stock(symbol) is None:
                return symbol, [], "outside_stock_scope"
            try:
                return symbol, get_market_data_provider(run["source"]).fetch_kline(symbol, limit=1000), None
            except Exception:
                return symbol, [], "kline_unavailable"
        _, index, error = fetch("SH000300")
        if error:
            failures.append({"symbol": "SH000300", "kind": error})
        symbols = list(dict.fromkeys(item["symbol"] for item in run["result"].get("items", [])))
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetch, symbol) for symbol in symbols] if not cancel.is_set() else []
            for future in as_completed(futures):
                if cancel.is_set():
                    for pending in futures:
                        pending.cancel()
                    break
                symbol, bars, error = future.result()
                klines[symbol] = bars
                if error:
                    failures.append({"symbol": symbol, "kind": error})
                progress["completed"] += 1
                _write(path, run_id, "running", progress)
        report = None
        if not cancel.is_set():
            report = evaluate_followup(report=run["result"], klines=klines, index_bars=index, as_of=as_of)
            report["failures"] = failures
        with _lock:
            _write(path, run_id, "cancelled" if cancel.is_set() else "completed", progress, report if not cancel.is_set() else None)
            _active.pop(run_id, None)
    except Exception:
        _write(path, run_id, "failed", progress)
    finally:
        with _lock:
            _active.pop(run_id, None)
