from __future__ import annotations

import json
import sqlite3

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse

from .backtest import run_ma_volume_backtest, review_signal_outcomes
from .csv_io import (
    HOLDING_CSV_FIELDS,
    WATCHLIST_CSV_FIELDS,
    csv_to_rows,
    rows_to_csv,
)
from .database import get_db, init_db
from .indicators import calculate_indicator_snapshot
from .market_data import MarketDataError, get_market_data_provider
from .mcp_tools import McpToolError, call_eltdx_mcp_tool, list_eltdx_mcp_tools
from .pool_analysis import (
    generate_stock_pool_market_analysis,
    generate_stock_pool_mcp_analysis,
)
from .repository import (
    create_analysis_report,
    create_backtest,
    create_holding,
    create_stock_pool,
    create_market_fetch_log,
    create_market_snapshot,
    create_signal,
    create_watchlist_item,
    delete_holding,
    delete_stock_pool,
    delete_watchlist_item,
    get_holding,
    get_holding_by_symbol,
    get_stock_pool,
    get_watchlist_item,
    latest_by_symbol,
    filter_rows_by_symbols,
    list_holdings,
    list_analysis_reports,
    list_backtests,
    list_market_fetch_logs,
    list_market_klines,
    list_market_snapshots,
    list_signals,
    list_stock_pools,
    list_watchlist,
    normalize_symbol,
    pool_symbols,
    update_holding,
    update_stock_pool,
    update_watchlist_item,
    upsert_market_klines,
    utc_now,
)
from .reports import (
    generate_daily_review,
    generate_stock_report,
    generate_trading_plan,
)
from .schemas import (
    BacktestOut,
    BacktestRequest,
    HoldingCreate,
    HoldingOut,
    HoldingUpdate,
    IndicatorSnapshotOut,
    MarketFetchLogOut,
    MarketKlineOut,
    MarketQuoteOut,
    McpToolCallOut,
    McpToolCallRequest,
    McpToolListOut,
    ReportOut,
    SignalEvaluateRequest,
    SignalOut,
    SignalReviewOut,
    StockPoolMarketAnalysisRequest,
    StockPoolMcpAnalysisRequest,
    StockPoolCreate,
    StockPoolOut,
    StockPoolUpdate,
    WatchlistCreate,
    WatchlistOut,
    WatchlistUpdate,
    WorkbenchActionOut,
    WorkbenchActionRequest,
    WorkbenchMarketActionRequest,
)
from .signal_engine import evaluate_holding_signal
from .static_ui import index_html


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


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return index_html()


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


def _report_row_to_output(row: dict) -> dict:
    return {
        "id": row["id"],
        "report_type": row["report_type"],
        "symbol": row["symbol"],
        "created_at": row["created_at"],
        "payload": json.loads(row["payload_json"]),
    }


def _save_report(
    db: sqlite3.Connection,
    *,
    report: dict,
    persist: bool,
) -> dict:
    if not persist:
        return {
            "id": None,
            "report_type": report["report_type"],
            "symbol": report.get("symbol"),
            "created_at": report.get("generated_at"),
            "payload": report,
        }
    saved = create_analysis_report(
        db,
        report_type=report["report_type"],
        symbol=report.get("symbol"),
        payload=report,
        created_at=report.get("generated_at"),
    )
    return _report_row_to_output(saved)


def _backtest_row_to_output(row: dict) -> dict:
    return {
        "id": row["id"],
        "symbol": row["symbol"],
        "source": row["source"],
        "strategy_name": row["strategy_name"],
        "created_at": row["created_at"],
        "config": json.loads(row["config_json"]),
        "result": json.loads(row["result_json"]),
    }


def _save_backtest(
    db: sqlite3.Connection,
    *,
    symbol: str,
    source: str,
    strategy_name: str,
    config: dict,
    result: dict,
    persist: bool,
) -> dict:
    if not persist:
        return {
            "id": None,
            "symbol": normalize_symbol(symbol),
            "source": source,
            "strategy_name": strategy_name,
            "created_at": result.get("generated_at"),
            "config": config,
            "result": result,
        }
    saved = create_backtest(
        db,
        symbol=symbol,
        source=source,
        strategy_name=strategy_name,
        config=config,
        result=result,
        created_at=result.get("generated_at"),
    )
    return _backtest_row_to_output(saved)


def _quote_payload_to_output(snapshot: dict, payload: dict) -> dict:
    return {
        "snapshot_id": snapshot["id"],
        "symbol": snapshot["symbol"],
        "name": payload.get("name"),
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


def _sync_holding_name_from_quote(
    db: sqlite3.Connection,
    holding: dict,
    quote: dict,
) -> None:
    payload = quote.get("payload") or quote
    name = payload.get("name")
    if not name or payload.get("is_mock"):
        return
    if holding.get("name") == name:
        return
    update_holding(db, int(holding["id"]), {"name": name})


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


def _fetch_kline_and_cache(
    db: sqlite3.Connection,
    *,
    symbol: str,
    source: str,
    period: str = "daily",
    limit: int = 120,
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
        return {
            "symbol": normalized_symbol,
            "source": provider.name,
            "period": period,
            "count": len(cached_bars),
            "bars": list(reversed(cached_bars)),
        }
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


def _indicator_snapshot_for_symbol(
    db: sqlite3.Connection,
    *,
    symbol: str,
    source: str,
    period: str = "daily",
    limit: int = 120,
    refresh: bool = False,
) -> dict:
    normalized_symbol = normalize_symbol(symbol)
    if refresh:
        kline = _fetch_kline_and_cache(
            db,
            symbol=normalized_symbol,
            source=source,
            period=period,
            limit=limit,
        )
        bars = kline["bars"]
        actual_source = kline["source"]
    else:
        bars = list(reversed(list_market_klines(
            db,
            symbol=normalized_symbol,
            source=source,
            period=period,
            limit=limit,
        )))
        actual_source = source
        if not bars:
            kline = _fetch_kline_and_cache(
                db,
                symbol=normalized_symbol,
                source=source,
                period=period,
                limit=limit,
            )
            bars = kline["bars"]
            actual_source = kline["source"]

    return {
        "symbol": normalized_symbol,
        "source": actual_source,
        "period": period,
        "snapshot": calculate_indicator_snapshot(bars),
    }


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


@app.post("/holdings/{holding_id}/signals/from-market", response_model=SignalOut)
def api_evaluate_holding_signal_from_market(
    holding_id: int,
    payload: WorkbenchMarketActionRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    holding = get_holding(db, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")

    symbol = normalize_symbol(holding["symbol"])
    quote = _fetch_quote_and_cache(db, symbol=symbol, source=payload.source)
    _sync_holding_name_from_quote(db, holding, quote)
    indicators = (
        _indicator_snapshot_for_symbol(
            db,
            symbol=symbol,
            source=payload.source,
            limit=payload.kline_limit,
            refresh=True,
        )["snapshot"]
        if payload.include_technical
        else None
    )
    signal = evaluate_holding_signal(
        holding,
        current_price=quote["price"],
        source_snapshot_id=quote["snapshot_id"],
        indicators=indicators,
    )
    return _save_signal(db, signal) if payload.persist else signal


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


@app.get("/reports", response_model=list[ReportOut])
def api_list_reports(
    report_type: str | None = None,
    symbol: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    return [
        _report_row_to_output(row)
        for row in list_analysis_reports(
            db,
            report_type=report_type,
            symbol=symbol,
            limit=limit,
        )
    ]


@app.get("/backtests", response_model=list[BacktestOut])
def api_list_backtests(
    symbol: str | None = None,
    strategy_name: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    return [
        _backtest_row_to_output(row)
        for row in list_backtests(
            db,
            symbol=symbol,
            strategy_name=strategy_name,
            limit=limit,
        )
    ]


@app.post("/backtests/{symbol}", response_model=BacktestOut)
def api_run_backtest(
    symbol: str,
    payload: BacktestRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    normalized_symbol = normalize_symbol(symbol)
    kline = _fetch_kline_and_cache(
        db,
        symbol=normalized_symbol,
        source=payload.source,
        period=payload.period,
        limit=payload.limit,
    )
    result = run_ma_volume_backtest(
        symbol=normalized_symbol,
        bars=kline["bars"],
        initial_equity=payload.initial_equity,
        stop_loss_pct=payload.stop_loss_pct,
        take_profit_pct=payload.take_profit_pct,
    )
    config = payload.model_dump(exclude={"persist"})
    return _save_backtest(
        db,
        symbol=normalized_symbol,
        source=kline["source"],
        strategy_name=result["strategy_name"],
        config=config,
        result=result,
        persist=payload.persist,
    )


@app.get("/reviews/signals", response_model=SignalReviewOut)
def api_review_signals(
    source: str = "tongdaxin",
    limit: int = Query(default=100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    signals = [_signal_row_to_output(row) for row in list_signals(db, limit=limit)]
    latest_prices: dict[str, float] = {}
    for signal in signals:
        symbol = normalize_symbol(signal["symbol"])
        if symbol not in latest_prices:
            quote = _fetch_quote_and_cache(db, symbol=symbol, source=source)
            latest_prices[symbol] = quote["price"]
    reviews = review_signal_outcomes(signals=signals, latest_prices=latest_prices)
    return {"generated_at": utc_now(), "count": len(reviews), "reviews": reviews}


@app.get("/market/quote/{symbol}", response_model=MarketQuoteOut)
def api_fetch_market_quote(
    symbol: str,
    source: str = "tongdaxin",
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return _fetch_quote_and_cache(db, symbol=symbol, source=source)


@app.get("/market/kline/{symbol}", response_model=MarketKlineOut)
def api_fetch_market_kline(
    symbol: str,
    source: str = "tongdaxin",
    period: str = "daily",
    limit: int = Query(default=120, ge=1, le=1000),
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return _fetch_kline_and_cache(
        db, symbol=symbol, source=source, period=period, limit=limit
    )


@app.get("/market/indicators/{symbol}", response_model=IndicatorSnapshotOut)
def api_get_market_indicators(
    symbol: str,
    source: str = "tongdaxin",
    period: str = "daily",
    limit: int = Query(default=120, ge=35, le=1000),
    refresh: bool = False,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return _indicator_snapshot_for_symbol(
        db,
        symbol=symbol,
        source=source,
        period=period,
        limit=limit,
        refresh=refresh,
    )


@app.get("/reports/stock/{symbol}", response_model=ReportOut)
def api_generate_stock_report(
    symbol: str,
    source: str = "tongdaxin",
    refresh: bool = True,
    persist: bool = True,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    normalized_symbol = normalize_symbol(symbol)
    holding = get_holding_by_symbol(db, normalized_symbol)
    quote = _fetch_quote_and_cache(db, symbol=normalized_symbol, source=source)
    indicators = _indicator_snapshot_for_symbol(
        db,
        symbol=normalized_symbol,
        source=source,
        refresh=refresh,
    )
    recent_signals = [
        _signal_row_to_output(row)
        for row in list_signals(db, symbol=normalized_symbol, limit=5)
    ]
    report = generate_stock_report(
        symbol=normalized_symbol,
        holding=holding,
        quote=quote,
        indicators=indicators,
        recent_signals=recent_signals,
    )
    return _save_report(db, report=report, persist=persist)


@app.get("/reports/trading-plan/{holding_id}", response_model=ReportOut)
def api_generate_trading_plan(
    holding_id: int,
    source: str = "tongdaxin",
    persist: bool = True,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    holding = get_holding(db, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")

    symbol = normalize_symbol(holding["symbol"])
    quote = _fetch_quote_and_cache(db, symbol=symbol, source=source)
    indicators = _indicator_snapshot_for_symbol(
        db, symbol=symbol, source=source, refresh=True
    )
    signal = evaluate_holding_signal(
        holding,
        current_price=quote["price"],
        source_snapshot_id=quote["snapshot_id"],
        indicators=indicators["snapshot"],
    )
    report = generate_trading_plan(
        holding=holding,
        quote=quote,
        indicators=indicators,
        signal=signal,
    )
    return _save_report(db, report=report, persist=persist)


@app.get("/reports/daily-review", response_model=ReportOut)
def api_generate_daily_review(
    persist: bool = True,
    signal_limit: int = Query(default=100, ge=1, le=500),
    pool_id: int | None = None,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    symbols = pool_symbols(db, pool_id)
    signals = [
        signal
        for signal in [_signal_row_to_output(row) for row in list_signals(db, limit=signal_limit)]
        if not symbols or normalize_symbol(signal["symbol"]) in symbols
    ]
    report = generate_daily_review(
        holdings=filter_rows_by_symbols(latest_by_symbol(list_holdings(db)), symbols),
        signals=signals,
        fetch_logs=list_market_fetch_logs(db, limit=signal_limit),
    )
    return _save_report(db, report=report, persist=persist)


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


def _list_tongdaxin_mcp_tools() -> dict:
    try:
        return {
            "server": "eltdx-mcp",
            "tools": list_eltdx_mcp_tools(),
        }
    except McpToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _call_tongdaxin_mcp_tool(tool_name: str, payload: McpToolCallRequest) -> dict:
    try:
        return {
            "server": "eltdx-mcp",
            "tool_name": tool_name,
            "result": call_eltdx_mcp_tool(tool_name, payload.arguments),
        }
    except McpToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/mcp/eltdx/tools", response_model=McpToolListOut)
def api_list_eltdx_tools() -> dict:
    return _list_tongdaxin_mcp_tools()


@app.get("/mcp/tongdaxin/tools", response_model=McpToolListOut)
def api_list_tongdaxin_tools() -> dict:
    return _list_tongdaxin_mcp_tools()


@app.post("/mcp/eltdx/tools/{tool_name}", response_model=McpToolCallOut)
def api_call_eltdx_tool(tool_name: str, payload: McpToolCallRequest) -> dict:
    return _call_tongdaxin_mcp_tool(tool_name, payload)


@app.post("/mcp/tongdaxin/tools/{tool_name}", response_model=McpToolCallOut)
def api_call_tongdaxin_tool(tool_name: str, payload: McpToolCallRequest) -> dict:
    return _call_tongdaxin_mcp_tool(tool_name, payload)


@app.post("/workbench/actions", response_model=WorkbenchActionOut)
def api_generate_workbench_actions(
    payload: WorkbenchActionRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    symbols = pool_symbols(db, payload.pool_id)
    holdings = filter_rows_by_symbols(latest_by_symbol(list_holdings(db)), symbols)
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
    symbols = pool_symbols(db, payload.pool_id)
    holdings = filter_rows_by_symbols(latest_by_symbol(list_holdings(db)), symbols)
    missing_prices: list[str] = []
    signals: list[dict] = []

    for holding in holdings:
        symbol = normalize_symbol(holding["symbol"])
        try:
            quote = _fetch_quote_and_cache(db, symbol=symbol, source=payload.source)
        except HTTPException:
            missing_prices.append(symbol)
            continue
        _sync_holding_name_from_quote(db, holding, quote)

        signal = evaluate_holding_signal(
            holding,
            current_price=quote["price"],
            source_snapshot_id=quote["snapshot_id"],
            indicators=(
                _indicator_snapshot_for_symbol(
                    db,
                    symbol=symbol,
                    source=payload.source,
                    limit=payload.kline_limit,
                    refresh=True,
                )["snapshot"]
                if payload.include_technical
                else None
            ),
        )
        signals.append(_save_signal(db, signal) if payload.persist else signal)

    return {
        "generated_at": utc_now(),
        "total_holdings": len(holdings),
        "generated_signals": len(signals),
        "missing_prices": missing_prices,
        "signals": signals,
    }


@app.get("/stock-pools", response_model=list[StockPoolOut])
def api_list_stock_pools(
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    return list_stock_pools(db)


@app.post("/stock-pools", response_model=StockPoolOut, status_code=status.HTTP_201_CREATED)
def api_create_stock_pool(
    payload: StockPoolCreate,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return create_stock_pool(db, payload.model_dump())


@app.patch("/stock-pools/{pool_id}", response_model=StockPoolOut)
def api_update_stock_pool(
    pool_id: int,
    payload: StockPoolUpdate,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    pool = update_stock_pool(db, pool_id, payload.model_dump(exclude_unset=True))
    if pool is None:
        raise HTTPException(status_code=404, detail="Stock pool not found")
    return pool


@app.delete("/stock-pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_stock_pool(
    pool_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    if not delete_stock_pool(db, pool_id):
        raise HTTPException(status_code=404, detail="Stock pool not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/stock-pools/{pool_id}/mcp-analysis", response_model=ReportOut)
def api_analyze_stock_pool_with_mcp(
    pool_id: int,
    payload: StockPoolMcpAnalysisRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    pool = get_stock_pool(db, pool_id)
    if pool is None:
        raise HTTPException(status_code=404, detail="Stock pool not found")
    symbols = pool_symbols(db, pool_id)
    try:
        report = generate_stock_pool_mcp_analysis(
            pool=pool,
            holdings=filter_rows_by_symbols(
                latest_by_symbol(list_holdings(db)), symbols
            ),
            watchlist=list_watchlist(db, pool_id=pool_id),
            max_symbols=payload.max_symbols,
            quote_tool=payload.quote_tool,
            profile_tool=payload.profile_tool,
            include_profile=payload.include_profile,
            quote_arguments=payload.quote_arguments,
            profile_arguments=payload.profile_arguments,
        )
    except McpToolError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _save_report(db, report=report, persist=payload.persist)


@app.post("/stock-pools/{pool_id}/market-analysis", response_model=ReportOut)
def api_analyze_stock_pool_with_market_source(
    pool_id: int,
    payload: StockPoolMarketAnalysisRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    pool = get_stock_pool(db, pool_id)
    if pool is None:
        raise HTTPException(status_code=404, detail="Stock pool not found")

    symbols = pool_symbols(db, pool_id)[: payload.max_symbols]
    quotes: dict[str, dict] = {}
    failed_symbols: list[str] = []
    watchlist = list_watchlist(db, pool_id=pool_id)
    watchlist_by_symbol = {
        normalize_symbol(str(item["symbol"])): item for item in watchlist
    }

    for symbol in symbols:
        normalized_symbol = normalize_symbol(symbol)
        try:
            quote = _fetch_quote_and_cache(
                db,
                symbol=normalized_symbol,
                source=payload.source,
            )
        except HTTPException:
            failed_symbols.append(normalized_symbol)
            continue
        quotes[normalized_symbol] = quote
        watchlist_item = watchlist_by_symbol.get(normalized_symbol)
        if watchlist_item and quote.get("name") and not watchlist_item.get("name"):
            update_watchlist_item(db, int(watchlist_item["id"]), {"name": quote["name"]})

    refreshed_watchlist = list_watchlist(db, pool_id=pool_id)
    report = generate_stock_pool_market_analysis(
        pool=pool,
        holdings=filter_rows_by_symbols(
            latest_by_symbol(list_holdings(db)), symbols
        ),
        watchlist=refreshed_watchlist,
        quotes=quotes,
        source=payload.source,
        failed_symbols=failed_symbols,
        max_symbols=payload.max_symbols,
    )
    return _save_report(db, report=report, persist=payload.persist)


@app.get("/watchlist", response_model=list[WatchlistOut])
def api_list_watchlist(
    pool_id: int | None = None,
    db: sqlite3.Connection = Depends(get_db),
) -> list[dict]:
    if pool_id is not None and get_stock_pool(db, pool_id) is None:
        raise HTTPException(status_code=404, detail="Stock pool not found")
    return list_watchlist(db, pool_id=pool_id)


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
