from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "local.db"


def resolve_project_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def get_db_path() -> Path:
    return resolve_project_path(os.getenv("TDX_STOCK_DB_PATH"), DEFAULT_DB_PATH)


def get_api_host() -> str:
    return os.getenv("TDX_STOCK_API_HOST", "127.0.0.1")


def get_api_port() -> int:
    raw_port = os.getenv("TDX_STOCK_API_PORT", "8765")
    return int(raw_port)
