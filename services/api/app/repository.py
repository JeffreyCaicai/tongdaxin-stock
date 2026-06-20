from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any


HOLDING_FIELDS = {
    "symbol",
    "name",
    "market",
    "quantity",
    "cost_price",
    "strategy_horizon",
    "initial_thesis",
    "stop_loss",
    "take_profit",
    "max_loss_pct",
    "notes",
}

STOCK_POOL_FIELDS = {
    "name",
    "description",
    "is_default",
}

WATCHLIST_FIELDS = {
    "pool_id",
    "symbol",
    "name",
    "market",
    "thesis",
    "buy_zone_low",
    "buy_zone_high",
    "trigger_condition",
    "invalidation_condition",
    "priority",
    "status",
    "notes",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def list_holdings(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT * FROM holdings ORDER BY updated_at DESC, id DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def latest_by_symbol(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        symbol = normalize_symbol(str(row["symbol"]))
        if symbol in seen:
            continue
        seen.add(symbol)
        latest.append(row)
    return latest


def get_holding(connection: sqlite3.Connection, holding_id: int) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM holdings WHERE id = ?", (holding_id,)
    ).fetchone()
    return row_to_dict(row)


def get_holding_by_symbol(
    connection: sqlite3.Connection, symbol: str
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT * FROM holdings
        WHERE symbol = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """,
        (normalize_symbol(symbol),),
    ).fetchone()
    return row_to_dict(row)


def create_holding(connection: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    data = {
        key: value
        for key, value in payload.items()
        if key in HOLDING_FIELDS and value is not None
    }
    data["symbol"] = normalize_symbol(data["symbol"])
    data["created_at"] = now
    data["updated_at"] = now

    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    cursor = connection.execute(
        f"INSERT INTO holdings ({columns}) VALUES ({placeholders})",
        tuple(data.values()),
    )
    connection.commit()
    created = get_holding(connection, int(cursor.lastrowid))
    assert created is not None
    return created


def update_holding(
    connection: sqlite3.Connection, holding_id: int, payload: dict[str, Any]
) -> dict[str, Any] | None:
    if get_holding(connection, holding_id) is None:
        return None

    data = {
        key: value
        for key, value in payload.items()
        if key in HOLDING_FIELDS and value is not None
    }
    if "symbol" in data:
        data["symbol"] = normalize_symbol(data["symbol"])
    if not data:
        return get_holding(connection, holding_id)

    data["updated_at"] = utc_now()
    assignments = ", ".join(f"{key} = ?" for key in data)
    connection.execute(
        f"UPDATE holdings SET {assignments} WHERE id = ?",
        tuple(data.values()) + (holding_id,),
    )
    connection.commit()
    return get_holding(connection, holding_id)


def delete_holding(connection: sqlite3.Connection, holding_id: int) -> bool:
    cursor = connection.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
    connection.commit()
    return cursor.rowcount > 0


def list_stock_pools(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT * FROM stock_pools ORDER BY is_default DESC, updated_at DESC, id DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def get_stock_pool(
    connection: sqlite3.Connection, pool_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM stock_pools WHERE id = ?", (pool_id,)
    ).fetchone()
    return row_to_dict(row)


def get_default_stock_pool(connection: sqlite3.Connection) -> dict[str, Any]:
    row = connection.execute(
        "SELECT * FROM stock_pools WHERE is_default = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if row is None:
        return create_stock_pool(
            connection,
            {
                "name": "默认股票池",
                "description": "系统默认个人股票池",
                "is_default": True,
            },
        )
    return dict(row)


def create_stock_pool(
    connection: sqlite3.Connection, payload: dict[str, Any]
) -> dict[str, Any]:
    now = utc_now()
    data = {
        key: value
        for key, value in payload.items()
        if key in STOCK_POOL_FIELDS and value is not None
    }
    data.setdefault("name", "默认股票池")
    data["is_default"] = 1 if data.get("is_default") else 0
    data["created_at"] = now
    data["updated_at"] = now
    if data["is_default"]:
        connection.execute("UPDATE stock_pools SET is_default = 0")

    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    cursor = connection.execute(
        f"INSERT INTO stock_pools ({columns}) VALUES ({placeholders})",
        tuple(data.values()),
    )
    connection.commit()
    created = get_stock_pool(connection, int(cursor.lastrowid))
    assert created is not None
    return created


def update_stock_pool(
    connection: sqlite3.Connection, pool_id: int, payload: dict[str, Any]
) -> dict[str, Any] | None:
    if get_stock_pool(connection, pool_id) is None:
        return None
    data = {
        key: value
        for key, value in payload.items()
        if key in STOCK_POOL_FIELDS and value is not None
    }
    if not data:
        return get_stock_pool(connection, pool_id)
    if "is_default" in data:
        data["is_default"] = 1 if data["is_default"] else 0
        if data["is_default"]:
            connection.execute("UPDATE stock_pools SET is_default = 0")
    data["updated_at"] = utc_now()
    assignments = ", ".join(f"{key} = ?" for key in data)
    connection.execute(
        f"UPDATE stock_pools SET {assignments} WHERE id = ?",
        tuple(data.values()) + (pool_id,),
    )
    connection.commit()
    return get_stock_pool(connection, pool_id)


def delete_stock_pool(connection: sqlite3.Connection, pool_id: int) -> bool:
    pool = get_stock_pool(connection, pool_id)
    if pool is None or pool["is_default"]:
        return False
    default_pool_id = int(get_default_stock_pool(connection)["id"])
    connection.execute(
        "UPDATE watchlist SET pool_id = ? WHERE pool_id = ?",
        (default_pool_id, pool_id),
    )
    cursor = connection.execute("DELETE FROM stock_pools WHERE id = ?", (pool_id,))
    connection.commit()
    return cursor.rowcount > 0


def list_watchlist(
    connection: sqlite3.Connection, *, pool_id: int | None = None
) -> list[dict[str, Any]]:
    if pool_id is not None:
        rows = connection.execute(
            """
            SELECT * FROM watchlist
            WHERE pool_id = ?
            ORDER BY priority ASC, updated_at DESC, id DESC
            """,
            (pool_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    rows = connection.execute(
        "SELECT * FROM watchlist ORDER BY priority ASC, updated_at DESC, id DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def pool_symbols(connection: sqlite3.Connection, pool_id: int | None) -> set[str]:
    if pool_id is None:
        return set()
    return {
        normalize_symbol(row["symbol"])
        for row in list_watchlist(connection, pool_id=pool_id)
    }


def filter_rows_by_symbols(
    rows: list[dict[str, Any]], symbols: set[str]
) -> list[dict[str, Any]]:
    if not symbols:
        return rows
    return [row for row in rows if normalize_symbol(row["symbol"]) in symbols]


def get_watchlist_item(
    connection: sqlite3.Connection, item_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM watchlist WHERE id = ?", (item_id,)
    ).fetchone()
    return row_to_dict(row)


def create_watchlist_item(
    connection: sqlite3.Connection, payload: dict[str, Any]
) -> dict[str, Any]:
    now = utc_now()
    data = {
        key: value
        for key, value in payload.items()
        if key in WATCHLIST_FIELDS and value is not None
    }
    data["symbol"] = normalize_symbol(data["symbol"])
    if data.get("pool_id") is None:
        data["pool_id"] = get_default_stock_pool(connection)["id"]
    data["created_at"] = now
    data["updated_at"] = now

    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    cursor = connection.execute(
        f"INSERT INTO watchlist ({columns}) VALUES ({placeholders})",
        tuple(data.values()),
    )
    connection.commit()
    created = get_watchlist_item(connection, int(cursor.lastrowid))
    assert created is not None
    return created


def update_watchlist_item(
    connection: sqlite3.Connection, item_id: int, payload: dict[str, Any]
) -> dict[str, Any] | None:
    if get_watchlist_item(connection, item_id) is None:
        return None

    data = {
        key: value
        for key, value in payload.items()
        if key in WATCHLIST_FIELDS and value is not None
    }
    if "symbol" in data:
        data["symbol"] = normalize_symbol(data["symbol"])
    if not data:
        return get_watchlist_item(connection, item_id)

    data["updated_at"] = utc_now()
    assignments = ", ".join(f"{key} = ?" for key in data)
    connection.execute(
        f"UPDATE watchlist SET {assignments} WHERE id = ?",
        tuple(data.values()) + (item_id,),
    )
    connection.commit()
    return get_watchlist_item(connection, item_id)


def delete_watchlist_item(connection: sqlite3.Connection, item_id: int) -> bool:
    cursor = connection.execute("DELETE FROM watchlist WHERE id = ?", (item_id,))
    connection.commit()
    return cursor.rowcount > 0


def create_signal(
    connection: sqlite3.Connection,
    *,
    symbol: str,
    signal_type: str,
    action: str,
    strength: float,
    price: float,
    reason_json: dict[str, Any],
    source_snapshot_id: int | None = None,
) -> dict[str, Any]:
    created_at = utc_now()
    cursor = connection.execute(
        """
        INSERT INTO signals (
          symbol, signal_type, action, strength, price, reason_json,
          source_snapshot_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            normalize_symbol(symbol),
            signal_type,
            action,
            strength,
            price,
            json.dumps(reason_json, ensure_ascii=False),
            source_snapshot_id,
            created_at,
        ),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM signals WHERE id = ?", (int(cursor.lastrowid),)
    ).fetchone()
    created = row_to_dict(row)
    assert created is not None
    return created


def list_signals(
    connection: sqlite3.Connection,
    *,
    symbol: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    if symbol:
        rows = connection.execute(
            """
            SELECT * FROM signals
            WHERE symbol = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (normalize_symbol(symbol), limit),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT * FROM signals
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_market_snapshot(
    connection: sqlite3.Connection,
    *,
    symbol: str,
    source: str,
    payload: dict[str, Any],
    fetched_at: str | None = None,
) -> dict[str, Any]:
    fetched_at = fetched_at or utc_now()
    cursor = connection.execute(
        """
        INSERT INTO market_snapshots (symbol, source, payload_json, fetched_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            normalize_symbol(symbol),
            source,
            json.dumps(payload, ensure_ascii=False),
            fetched_at,
        ),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM market_snapshots WHERE id = ?", (int(cursor.lastrowid),)
    ).fetchone()
    created = row_to_dict(row)
    assert created is not None
    return created


def list_market_snapshots(
    connection: sqlite3.Connection,
    *,
    symbol: str | None = None,
    source: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    clauses: list[str] = []
    params: list[Any] = []
    if symbol:
        clauses.append("symbol = ?")
        params.append(normalize_symbol(symbol))
    if source:
        clauses.append("source = ?")
        params.append(source)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(
        f"""
        SELECT * FROM market_snapshots
        {where_clause}
        ORDER BY fetched_at DESC, id DESC
        LIMIT ?
        """,
        tuple(params + [limit]),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_market_klines(
    connection: sqlite3.Connection,
    *,
    symbol: str,
    source: str,
    period: str,
    bars: list[dict[str, Any]],
    fetched_at: str | None = None,
) -> list[dict[str, Any]]:
    fetched_at = fetched_at or utc_now()
    normalized_symbol = normalize_symbol(symbol)
    for bar in bars:
        connection.execute(
            """
            INSERT INTO market_klines (
              symbol, source, period, trade_date, open, high, low, close,
              volume, amount, payload_json, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, source, period, trade_date) DO UPDATE SET
              open = excluded.open,
              high = excluded.high,
              low = excluded.low,
              close = excluded.close,
              volume = excluded.volume,
              amount = excluded.amount,
              payload_json = excluded.payload_json,
              fetched_at = excluded.fetched_at
            """,
            (
                normalized_symbol,
                source,
                period,
                bar["trade_date"],
                bar["open"],
                bar["high"],
                bar["low"],
                bar["close"],
                bar.get("volume"),
                bar.get("amount"),
                json.dumps(bar.get("payload", bar), ensure_ascii=False),
                fetched_at,
            ),
        )
    connection.commit()
    return list_market_klines(
        connection,
        symbol=normalized_symbol,
        source=source,
        period=period,
        limit=len(bars) if bars else 1,
    )


def list_market_klines(
    connection: sqlite3.Connection,
    *,
    symbol: str,
    source: str | None = None,
    period: str = "daily",
    limit: int = 120,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 1000))
    clauses = ["symbol = ?", "period = ?"]
    params: list[Any] = [normalize_symbol(symbol), period]
    if source:
        clauses.append("source = ?")
        params.append(source)

    rows = connection.execute(
        f"""
        SELECT * FROM market_klines
        WHERE {' AND '.join(clauses)}
        ORDER BY trade_date DESC
        LIMIT ?
        """,
        tuple(params + [limit]),
    ).fetchall()
    return [dict(row) for row in rows]


def create_market_fetch_log(
    connection: sqlite3.Connection,
    *,
    symbol: str,
    source: str,
    data_type: str,
    status: str,
    message: str | None = None,
    fetched_at: str | None = None,
) -> dict[str, Any]:
    fetched_at = fetched_at or utc_now()
    cursor = connection.execute(
        """
        INSERT INTO market_fetch_logs (
          symbol, source, data_type, status, message, fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (normalize_symbol(symbol), source, data_type, status, message, fetched_at),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM market_fetch_logs WHERE id = ?", (int(cursor.lastrowid),)
    ).fetchone()
    created = row_to_dict(row)
    assert created is not None
    return created


def list_market_fetch_logs(
    connection: sqlite3.Connection,
    *,
    symbol: str | None = None,
    source: str | None = None,
    data_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    clauses: list[str] = []
    params: list[Any] = []
    if symbol:
        clauses.append("symbol = ?")
        params.append(normalize_symbol(symbol))
    if source:
        clauses.append("source = ?")
        params.append(source)
    if data_type:
        clauses.append("data_type = ?")
        params.append(data_type)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(
        f"""
        SELECT * FROM market_fetch_logs
        {where_clause}
        ORDER BY fetched_at DESC, id DESC
        LIMIT ?
        """,
        tuple(params + [limit]),
    ).fetchall()
    return [dict(row) for row in rows]


def create_analysis_report(
    connection: sqlite3.Connection,
    *,
    report_type: str,
    payload: dict[str, Any],
    symbol: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    created_at = created_at or utc_now()
    cursor = connection.execute(
        """
        INSERT INTO analysis_reports (
          report_type, symbol, payload_json, created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            report_type,
            normalize_symbol(symbol) if symbol else None,
            json.dumps(payload, ensure_ascii=False),
            created_at,
        ),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM analysis_reports WHERE id = ?", (int(cursor.lastrowid),)
    ).fetchone()
    created = row_to_dict(row)
    assert created is not None
    return created


def list_analysis_reports(
    connection: sqlite3.Connection,
    *,
    report_type: str | None = None,
    symbol: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    clauses: list[str] = []
    params: list[Any] = []
    if report_type:
        clauses.append("report_type = ?")
        params.append(report_type)
    if symbol:
        clauses.append("symbol = ?")
        params.append(normalize_symbol(symbol))

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(
        f"""
        SELECT * FROM analysis_reports
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        tuple(params + [limit]),
    ).fetchall()
    return [dict(row) for row in rows]


def create_backtest(
    connection: sqlite3.Connection,
    *,
    symbol: str,
    source: str,
    strategy_name: str,
    config: dict[str, Any],
    result: dict[str, Any],
    created_at: str | None = None,
) -> dict[str, Any]:
    created_at = created_at or utc_now()
    cursor = connection.execute(
        """
        INSERT INTO backtests (
          symbol, source, strategy_name, config_json, result_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            normalize_symbol(symbol),
            source,
            strategy_name,
            json.dumps(config, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
            created_at,
        ),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM backtests WHERE id = ?", (int(cursor.lastrowid),)
    ).fetchone()
    created = row_to_dict(row)
    assert created is not None
    return created


def list_backtests(
    connection: sqlite3.Connection,
    *,
    symbol: str | None = None,
    strategy_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    clauses: list[str] = []
    params: list[Any] = []
    if symbol:
        clauses.append("symbol = ?")
        params.append(normalize_symbol(symbol))
    if strategy_name:
        clauses.append("strategy_name = ?")
        params.append(strategy_name)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(
        f"""
        SELECT * FROM backtests
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        tuple(params + [limit]),
    ).fetchall()
    return [dict(row) for row in rows]
