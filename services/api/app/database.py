from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import PROJECT_ROOT, get_db_path


SCHEMA_PATH = PROJECT_ROOT / "services" / "api" / "app" / "schema.sql"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path | None = None) -> Path:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _run_lightweight_migrations(connection)
    return path


def _run_lightweight_migrations(connection: sqlite3.Connection) -> None:
    watchlist_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(watchlist)")
    }
    if "pool_id" not in watchlist_columns:
        connection.execute("ALTER TABLE watchlist ADD COLUMN pool_id INTEGER")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    default_pool = connection.execute(
        "SELECT id FROM stock_pools WHERE is_default = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if default_pool is None:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO stock_pools (
              name, description, is_default, created_at, updated_at
            )
            VALUES (?, ?, 1, ?, ?)
            """,
            ("默认股票池", "系统默认个人股票池", now, now),
        )
        default_pool_id = int(cursor.lastrowid)
        if default_pool_id == 0:
            row = connection.execute(
                "SELECT id FROM stock_pools WHERE name = ?", ("默认股票池",)
            ).fetchone()
            default_pool_id = int(row["id"])
    else:
        default_pool_id = int(default_pool["id"])

    connection.execute(
        "UPDATE watchlist SET pool_id = ? WHERE pool_id IS NULL",
        (default_pool_id,),
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_watchlist_pool ON watchlist(pool_id)"
    )
    connection.commit()


def get_db() -> Iterator[sqlite3.Connection]:
    init_db()
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
