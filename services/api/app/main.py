from __future__ import annotations

import json
import sqlite3

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Response, status

from .csv_io import (
    HOLDING_CSV_FIELDS,
    WATCHLIST_CSV_FIELDS,
    csv_to_rows,
    rows_to_csv,
)
from .database import get_db, init_db
from .repository import (
    create_holding,
    create_signal,
    create_watchlist_item,
    delete_holding,
    delete_watchlist_item,
    get_holding,
    get_watchlist_item,
    list_holdings,
    list_signals,
    list_watchlist,
    normalize_symbol,
    update_holding,
    update_watchlist_item,
    utc_now,
)
from .schemas import (
    HoldingCreate,
    HoldingOut,
    HoldingUpdate,
    SignalEvaluateRequest,
    SignalOut,
    WatchlistCreate,
    WatchlistOut,
    WatchlistUpdate,
    WorkbenchActionOut,
    WorkbenchActionRequest,
)
from .signal_engine import evaluate_holding_signal


app = FastAPI(
    title="Tongdaxin Stock Local API",
    version="0.1.0",
    description="Local decision-support API for personal A-share portfolio workflows.",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _signal_row_to_output(row: dict) -> dict:
    reason_json = json.loads(row["reason_json"])
    return {
        "id": row["id"],
        "symbol": row["symbol"],
        "signal_type": row["signal_type"],
        "action": row["action"],
        "strength": row["strength"],
        "price": row["price"],
        "risk_level": reason_json["risk_level"],
        "reasons": reason_json["reasons"],
        "next_check": reason_json["next_check"],
        "source_snapshot_id": row["source_snapshot_id"],
        "created_at": row["created_at"],
        "extra": reason_json.get("extra", {}),
    }


def _save_signal(db: sqlite3.Connection, signal: dict) -> dict:
    saved = create_signal(
        db,
        symbol=signal["symbol"],
        signal_type=signal["signal_type"],
        action=signal["action"],
        strength=signal["strength"],
        price=signal["price"],
        reason_json={
            "risk_level": signal["risk_level"],
            "reasons": signal["reasons"],
            "next_check": signal["next_check"],
            "extra": signal["extra"],
        },
        source_snapshot_id=signal["source_snapshot_id"],
    )
    return _signal_row_to_output(saved)


@app.get("/holdings", response_model=list[HoldingOut])
def api_list_holdings(
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    return list_holdings(db)


@app.get("/holdings/export.csv")
def api_export_holdings_csv(
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    content = rows_to_csv(list_holdings(db), HOLDING_CSV_FIELDS)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=holdings.csv"},
    )


@app.post(
    "/holdings/import.csv",
    response_model=list[HoldingOut],
    status_code=status.HTTP_201_CREATED,
)
def api_import_holdings_csv(
    csv_text: str = Body(..., media_type="text/csv"),
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    try:
        rows = csv_to_rows(csv_text, required_fields={"symbol", "cost_price"})
        payloads = [HoldingCreate.model_validate(row) for row in rows]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return [create_holding(db, payload.model_dump()) for payload in payloads]


@app.post("/holdings", response_model=HoldingOut, status_code=status.HTTP_201_CREATED)
def api_create_holding(
    payload: HoldingCreate,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return create_holding(db, payload.model_dump())


@app.get("/holdings/{holding_id}", response_model=HoldingOut)
def api_get_holding(
    holding_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    holding = get_holding(db, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    return holding


@app.patch("/holdings/{holding_id}", response_model=HoldingOut)
def api_update_holding(
    holding_id: int,
    payload: HoldingUpdate,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    holding = update_holding(db, holding_id, payload.model_dump(exclude_unset=True))
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    return holding


@app.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_holding(
    holding_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    if not delete_holding(db, holding_id):
        raise HTTPException(status_code=404, detail="Holding not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/holdings/{holding_id}/signals", response_model=SignalOut)
def api_evaluate_holding_signal(
    holding_id: int,
    payload: SignalEvaluateRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    holding = get_holding(db, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")

    signal = evaluate_holding_signal(
        holding,
        current_price=payload.current_price,
        source_snapshot_id=payload.source_snapshot_id,
    )
    return _save_signal(db, signal)


@app.get("/signals", response_model=list[SignalOut])
def api_list_signals(
    symbol: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    return [
        _signal_row_to_output(row)
        for row in list_signals(db, symbol=symbol, limit=limit)
    ]


@app.post("/workbench/actions", response_model=WorkbenchActionOut)
def api_generate_workbench_actions(
    payload: WorkbenchActionRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    holdings = list_holdings(db)
    price_map = {
        normalize_symbol(symbol): price for symbol, price in payload.prices.items()
    }
    missing_prices: list[str] = []
    signals: list[dict] = []

    for holding in holdings:
        symbol = normalize_symbol(holding["symbol"])
        current_price = price_map.get(symbol)
        if current_price is None:
            missing_prices.append(symbol)
            continue
        signal = evaluate_holding_signal(holding, current_price=current_price)
        signals.append(_save_signal(db, signal) if payload.persist else signal)

    return {
        "generated_at": utc_now(),
        "total_holdings": len(holdings),
        "generated_signals": len(signals),
        "missing_prices": missing_prices,
        "signals": signals,
    }


@app.get("/watchlist", response_model=list[WatchlistOut])
def api_list_watchlist(
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    return list_watchlist(db)


@app.get("/watchlist/export.csv")
def api_export_watchlist_csv(
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    content = rows_to_csv(list_watchlist(db), WATCHLIST_CSV_FIELDS)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=watchlist.csv"},
    )


@app.post(
    "/watchlist/import.csv",
    response_model=list[WatchlistOut],
    status_code=status.HTTP_201_CREATED,
)
def api_import_watchlist_csv(
    csv_text: str = Body(..., media_type="text/csv"),
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    try:
        rows = csv_to_rows(csv_text, required_fields={"symbol"})
        payloads = [WatchlistCreate.model_validate(row) for row in rows]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return [create_watchlist_item(db, payload.model_dump()) for payload in payloads]


@app.post("/watchlist", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def api_create_watchlist_item(
    payload: WatchlistCreate,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return create_watchlist_item(db, payload.model_dump())


@app.get("/watchlist/{item_id}", response_model=WatchlistOut)
def api_get_watchlist_item(
    item_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    item = get_watchlist_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return item


@app.patch("/watchlist/{item_id}", response_model=WatchlistOut)
def api_update_watchlist_item(
    item_id: int,
    payload: WatchlistUpdate,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    item = update_watchlist_item(db, item_id, payload.model_dump(exclude_unset=True))
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return item


@app.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_watchlist_item(
    item_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    if not delete_watchlist_item(db, item_id):
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
