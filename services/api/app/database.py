from __future__ import annotations

import sqlite3
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
    return path


def get_db() -> Iterator[sqlite3.Connection]:
    init_db()
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
