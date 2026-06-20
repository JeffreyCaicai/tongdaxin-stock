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
from .market_data import MarketDataError, get_market_data_provider
from .repository import (
    create_holding,
    create_market_fetch_log,
    create_market_snapshot,
    create_signal,
    create_watchlist_item,
    delete_holding,
    delete_watchlist_item,
    get_holding,
    get_watchlist_item,
    list_holdings,
    list_market_fetch_logs,
    list_market_klines,
    list_market_snapshots,
    list_signals,
    list_watchlist,
    normalize_symbol,
    update_holding,
    update_watchlist_item,
    upsert_market_klines,
    utc_now,
)
from .schemas import (
    HoldingCreate,
    HoldingOut,
    HoldingUpdate,
    MarketFetchLogOut,
    MarketKlineOut,
    MarketQuoteOut,
    SignalEvaluateRequest,
    SignalOut,
    WatchlistCreate,
    WatchlistOut,
    WatchlistUpdate,
    WorkbenchActionOut,
    WorkbenchActionRequest,
    WorkbenchMarketActionRequest,
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


def _quote_payload_to_output(snapshot: dict, payload: dict) -> dict:
    return {
        "snapshot_id": snapshot["id"],
        "symbol": snapshot["symbol"],
        "source": snapshot["source"],
        "price": payload["price"],
        "open": payload.get("open"),
        "high": payload.get("high"),
        "low": payload.get("low"),
        "previous_close": payload.get("previous_close"),
        "change": payload.get("change"),
        "pct_change": payload.get("pct_change"),
        "volume": payload.get("volume"),
        "amount": payload.get("amount"),
        "fetched_at": snapshot["fetched_at"],
        "payload": payload,
    }


def _fetch_quote_and_cache(
    db: sqlite3.Connection,
    *,
    symbol: str,
    source: str,
) -> dict:
    normalized_symbol = normalize_symbol(symbol)
    try:
        provider = get_market_data_provider(source)
        quote = provider.fetch_quote(normalized_symbol)
        snapshot = create_market_snapshot(
            db,
            symbol=normalized_symbol,
            source=provider.name,
            payload=quote,
            fetched_at=quote.get("fetched_at"),
        )
        create_market_fetch_log(
            db,
            symbol=normalized_symbol,
            source=provider.name,
            data_type="quote",
            status="success",
            message=None,
            fetched_at=snapshot["fetched_at"],
        )
        return _quote_payload_to_output(snapshot, quote)
    except MarketDataError as exc:
        create_market_fetch_log(
            db,
            symbol=normalized_symbol,
            source=source,
            data_type="quote",
            status="error",
            message=str(exc),
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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


@app.get("/market/quote/{symbol}", response_model=MarketQuoteOut)
def api_fetch_market_quote(
    symbol: str,
    source: str = "mock",
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return _fetch_quote_and_cache(db, symbol=symbol, source=source)


@app.get("/market/kline/{symbol}", response_model=MarketKlineOut)
def api_fetch_market_kline(
    symbol: str,
    source: str = "mock",
    period: str = "daily",
    limit: int = Query(default=120, ge=1, le=1000),
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    normalized_symbol = normalize_symbol(symbol)
    try:
        provider = get_market_data_provider(source)
        bars = provider.fetch_kline(normalized_symbol, period=period, limit=limit)
        cached_bars = upsert_market_klines(
            db,
            symbol=normalized_symbol,
            source=provider.name,
            period=period,
            bars=bars,
        )
        create_market_fetch_log(
            db,
            symbol=normalized_symbol,
            source=provider.name,
            data_type="kline",
            status="success",
            message=f"Fetched {len(bars)} {period} bars.",
        )
    except MarketDataError as exc:
        create_market_fetch_log(
            db,
            symbol=normalized_symbol,
            source=source,
            data_type="kline",
            status="error",
            message=str(exc),
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "symbol": normalized_symbol,
        "source": provider.name,
        "period": period,
        "count": len(cached_bars),
        "bars": list(reversed(cached_bars)),
    }


@app.get("/market/snapshots", response_model=list[MarketQuoteOut])
def api_list_market_snapshots(
    symbol: str | None = None,
    source: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    outputs: list[dict] = []
    for snapshot in list_market_snapshots(
        db, symbol=symbol, source=source, limit=limit
    ):
        payload = json.loads(snapshot["payload_json"])
        if "price" in payload:
            outputs.append(_quote_payload_to_output(snapshot, payload))
    return outputs


@app.get("/market/klines/{symbol}", response_model=MarketKlineOut)
def api_list_cached_market_klines(
    symbol: str,
    source: str | None = None,
    period: str = "daily",
    limit: int = Query(default=120, ge=1, le=1000),
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    normalized_symbol = normalize_symbol(symbol)
    bars = list_market_klines(
        db, symbol=normalized_symbol, source=source, period=period, limit=limit
    )
    return {
        "symbol": normalized_symbol,
        "source": source or "any",
        "period": period,
        "count": len(bars),
        "bars": list(reversed(bars)),
    }


@app.get("/market/fetch-logs", response_model=list[MarketFetchLogOut])
def api_list_market_fetch_logs(
    symbol: str | None = None,
    source: str | None = None,
    data_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    return list_market_fetch_logs(
        db,
        symbol=symbol,
        source=source,
        data_type=data_type,
        limit=limit,
    )


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


@app.post("/workbench/actions/from-market", response_model=WorkbenchActionOut)
def api_generate_workbench_actions_from_market(
    payload: WorkbenchMarketActionRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    holdings = list_holdings(db)
    missing_prices: list[str] = []
    signals: list[dict] = []

    for holding in holdings:
        symbol = normalize_symbol(holding["symbol"])
        try:
            quote = _fetch_quote_and_cache(db, symbol=symbol, source=payload.source)
        except HTTPException:
            missing_prices.append(symbol)
            continue

        signal = evaluate_holding_signal(
            holding,
            current_price=quote["price"],
            source_snapshot_id=quote["snapshot_id"],
        )
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
