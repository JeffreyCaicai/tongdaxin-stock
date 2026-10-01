from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .database import get_db
from .opportunity_jobs import cancel_run, read_run, start_run
from .opportunity_tracking_jobs import cancel_followup, read_followup, start_followup
from .repository import get_stock_pool, latest_by_symbol, list_holdings, list_watchlist

router = APIRouter()


class OpportunityRequest(BaseModel):
    source: Literal["tdx-official", "mock"] = "tdx-official"
    outside_limit: int = Field(default=40, ge=10, le=80)


@router.post("/stock-pools/{pool_id}/opportunities", status_code=202)
def create_scan(pool_id: int, payload: OpportunityRequest, db: sqlite3.Connection = Depends(get_db)):
    pool = get_stock_pool(db, pool_id)
    if pool is None:
        raise HTTPException(404, "Stock pool not found")
    watchlist = latest_by_symbol(list_watchlist(db, pool_id=pool_id))
    holdings = latest_by_symbol(list_holdings(db))
    path = Path(db.execute("PRAGMA database_list").fetchone()[2])
    try:
        return start_run(db, path=path, pool=pool, watchlist=watchlist, holdings=holdings,
                         source=payload.source, limit=payload.outside_limit)
    except RuntimeError:
        raise HTTPException(409, "Another opportunity scan is running; wait or cancel it first") from None


@router.get("/stock-pools/{pool_id}/opportunities")
def scan_history(pool_id: int, source: str = "tdx-official", db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT id, status, created_at, updated_at FROM opportunity_runs WHERE pool_id=? AND source=? ORDER BY created_at DESC, rowid DESC LIMIT 20", (pool_id, source)).fetchall()
    return [dict(row) for row in rows]


@router.get("/opportunities/{run_id}")
def get_scan(run_id: str, db: sqlite3.Connection = Depends(get_db)):
    run = read_run(db, run_id)
    if run is None:
        raise HTTPException(404, "Scan not found")
    return run


@router.delete("/opportunities/{run_id}")
def stop_scan(run_id: str, db: sqlite3.Connection = Depends(get_db)):
    if read_run(db, run_id) is None:
        raise HTTPException(404, "Scan not found")
    return {"cancel_requested": cancel_run(run_id)}


@router.get("/opportunities/{run_id}/followup")
def get_followup(run_id: str, db: sqlite3.Connection = Depends(get_db)):
    run = get_scan(run_id, db)
    return read_followup(db, run)


@router.post("/opportunities/{run_id}/followup", status_code=202)
def refresh_followup(run_id: str, db: sqlite3.Connection = Depends(get_db)):
    run = get_scan(run_id, db)
    if run["status"] != "completed" or not run["result"]:
        raise HTTPException(409, "Follow-up requires a completed recommendation snapshot")
    if run["source"] not in {"tdx-official", "mock"}:
        raise HTTPException(422, "Unsupported follow-up source")
    path = Path(db.execute("PRAGMA database_list").fetchone()[2])
    try:
        return start_followup(db, path=path, run=run)
    except RuntimeError:
        raise HTTPException(409, "Another follow-up is running; wait or cancel it first") from None


@router.delete("/opportunities/{run_id}/followup")
def stop_followup(run_id: str, db: sqlite3.Connection = Depends(get_db)):
    get_scan(run_id, db)
    return {"cancel_requested": cancel_followup(run_id)}
