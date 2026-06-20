from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "local.db"
DEFAULT_TDX_API_ENDPOINT = "http://tdxhub.icfqs.com:7615/TQLEX"
_ENV_LOADED = False


def load_env_file(path: Path | None = None) -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        _ENV_LOADED = True
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value
    _ENV_LOADED = True


load_env_file()


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


def get_tdx_api_key() -> str | None:
    return (
        os.getenv("TDX_API_KEY")
        or os.getenv("TDX_API_TOKEN")
        or os.getenv("TDX_OFFICIAL_TOKEN")
    )


def get_tdx_api_endpoint() -> str:
    return (
        os.getenv("TDX_API_DATA_ENDPOINT")
        or os.getenv("TDX_API_ENDPOINT")
        or DEFAULT_TDX_API_ENDPOINT
    )
