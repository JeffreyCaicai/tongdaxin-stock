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

WATCHLIST_FIELDS = {
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


def get_holding(connection: sqlite3.Connection, holding_id: int) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM holdings WHERE id = ?", (holding_id,)
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


def list_watchlist(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT * FROM watchlist ORDER BY priority ASC, updated_at DESC, id DESC"
    ).fetchall()
    return [dict(row) for row in rows]


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
