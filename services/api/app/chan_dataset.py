"""Strict, immutable research inputs. This module has no provider or config imports."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .market_time import RESEARCH_PERIODS, bar_time, local_timestamp, session_date

MAX_BYTES = 50 * 1024 * 1024
ROOT_FIELDS = {"schema_version", "dataset_id", "created_at", "selection", "source", "as_of",
               "price_basis", "calendar", "series", "issues", "collection"}
BAR_FIELDS = {"trade_date", "session_date", "bar_end_at", "time_semantics",
              "open", "high", "low", "close", "volume", "amount"}


def canonical_json(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                          allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError):
        raise ValueError("invalid_json_value") from None


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def dataset_id(dataset: dict) -> str:
    return digest({k: v for k, v in dataset.items() if k != "dataset_id"})


def canonical_symbol(value: str) -> str:
    value = str(value).strip().upper()
    match = re.fullmatch(r"(?:(SH|SZ|BJ|[012]\.))?([0-9]{6})", value)
    if not match:
        raise ValueError("invalid_symbol")
    exchange, code = match.groups()
    exchange = {"1.": "SH", "0.": "SZ", "2.": "BJ"}.get(exchange, exchange)
    inferred = "SH" if code.startswith(("5", "6", "9")) else "BJ" if code.startswith(("4", "8")) else "SZ"
    if exchange == "SH" and code.startswith("000") or exchange == "SZ" and code.startswith("399"):
        return exchange + code
    return code if exchange is None or exchange == inferred else exchange + code


def _fields(value: object, allowed: set, required: set | None = None) -> None:
    if not isinstance(value, dict) or set(value) - allowed or not (allowed if required is None else required) <= set(value):
        raise ValueError("invalid_dataset_fields")


def validate_verification(value: dict) -> None:
    _fields(value, {"status", "reference", "evidence_sha256"})
    if value["status"] not in {"verified", "unverified"}:
        raise ValueError("invalid_verification")
    if value["status"] == "verified" and not (
        isinstance(value["reference"], str) and 0 < len(value["reference"]) <= 500
        and re.fullmatch(r"[a-f0-9]{64}", str(value["evidence_sha256"]))
    ):
        raise ValueError("verification_evidence_required")


def validate_calendar(calendar: dict) -> None:
    _fields(calendar, {"sessions", "coverage_start", "coverage_end", "source", "version", "verification"})
    validate_verification(calendar["verification"])
    sessions = calendar["sessions"]
    if not isinstance(sessions, list) or len(sessions) > 50000 or sessions != sorted(set(sessions)):
        raise ValueError("invalid_calendar_sessions")
    for day in sessions:
        if session_date(day).isoformat() != day:
            raise ValueError("invalid_calendar_sessions")
    if calendar["coverage_start"] is None or calendar["coverage_end"] is None:
        if sessions or calendar["verification"]["status"] == "verified":
            raise ValueError("calendar_coverage_required")
    else:
        start, end = (session_date(calendar[k]).isoformat() for k in ("coverage_start", "coverage_end"))
        if start > end or any(not start <= day <= end for day in sessions):
            raise ValueError("invalid_calendar_coverage")
    if calendar["verification"]["status"] == "verified" and (not calendar["source"] or not calendar["version"]):
        raise ValueError("calendar_provenance_required")


def _validate_issues(issues: list) -> None:
    if not isinstance(issues, list):
        raise ValueError("invalid_issues")
    for issue in issues:
        _fields(issue, {"code", "symbol", "period", "bar_key", "scope"})
        if not re.fullmatch(r"[a-z_]{1,64}", str(issue["code"])) or issue["scope"] not in {"bar", "series"}:
            raise ValueError("invalid_issue")
        if issue["period"] not in RESEARCH_PERIODS or canonical_symbol(issue["symbol"]) != issue["symbol"]:
            raise ValueError("invalid_issue_identity")
        if issue["scope"] == "bar":
            if bar_time(issue["bar_key"], period=issue["period"])["trade_date"] != issue["bar_key"]:
                raise ValueError("invalid_issue_time")
        elif issue["bar_key"] is not None:
            raise ValueError("invalid_issue_scope")


def validate_dataset(dataset: dict) -> None:
    try:
        _fields(dataset, ROOT_FIELDS)
        if len(canonical_json(dataset)) > MAX_BYTES:
            raise ValueError("dataset_too_large")
        if dataset["dataset_id"] != dataset_id(dataset):
            raise ValueError("dataset_hash_mismatch")
        if dataset["schema_version"] != "chan_dataset_v1" or dataset["source"] not in {"synthetic", "tdx-official"}:
            raise ValueError("unsupported_dataset")
        local_timestamp(dataset["as_of"])
        local_timestamp(dataset["created_at"])
        selection = dataset["selection"]
        _fields(selection, {"symbols", "selected_at", "scope"})
        local_timestamp(selection["selected_at"])
        symbols = selection["symbols"]
        if selection["scope"] != "selected_sample" or not isinstance(symbols, list) or not 1 <= len(symbols) <= 10:
            raise ValueError("invalid_selection")
        if len(set(symbols)) != len(symbols) or any(canonical_symbol(s) != s for s in symbols) or "SH000300" in symbols:
            raise ValueError("invalid_selection")
        basis = dataset["price_basis"]
        _fields(basis, {"parameters", "verification", "point_in_time_verified"})
        _fields(basis["parameters"], {"TQFlag"})
        if basis["parameters"]["TQFlag"] != 11 or basis["point_in_time_verified"] is not False:
            raise ValueError("unsupported_price_basis")
        validate_verification(basis["verification"])
        validate_calendar(dataset["calendar"])
        series = dataset["series"]
        if not isinstance(series, dict) or set(series) - set(symbols) - {"SH000300"} or not set(symbols) <= set(series):
            raise ValueError("invalid_series_selection")
        for symbol, periods in series.items():
            if not isinstance(periods, dict) or not periods or set(periods) - RESEARCH_PERIODS:
                raise ValueError("unsupported_research_period")
            for period, content in periods.items():
                _fields(content, {"bars", "issues"})
                if not isinstance(content["bars"], list) or len(content["bars"]) > 5000:
                    raise ValueError("invalid_series_size")
                previous = ""
                for bar in content["bars"]:
                    _fields(bar, BAR_FIELDS, {"trade_date", "open", "high", "low", "close"})
                    metadata = bar_time(bar["trade_date"], period=period)
                    if metadata["trade_date"] != bar["trade_date"] or bar["trade_date"] <= previous:
                        raise ValueError("non_increasing_bars")
                    for field in ("session_date", "bar_end_at", "time_semantics"):
                        if field in bar and bar[field] != metadata[field]:
                            raise ValueError("conflicting_bar_metadata")
                    for field in ("open", "high", "low", "close", "volume", "amount"):
                        value = bar.get(field)
                        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                            raise ValueError("invalid_price_type")
                    previous = bar["trade_date"]
                _validate_issues(content["issues"])
                if any(i["symbol"] != symbol or i["period"] != period for i in content["issues"]):
                    raise ValueError("issue_series_mismatch")
        _validate_issues(dataset["issues"])
        collection = dataset["collection"]
        _fields(collection, {"parser_version", "page_size", "max_pages", "pages", "status", "history_complete"})
        if collection["history_complete"] is not False or collection["status"] not in {"bounded", "partial"}:
            raise ValueError("unsupported_collection_claim")
        if collection["parser_version"] != "tdx_time_v1":
            raise ValueError("unsupported_parser")
        if type(collection["page_size"]) is not int or not 1 <= collection["page_size"] <= 1000 or type(collection["max_pages"]) is not int or not 1 <= collection["max_pages"] <= 5:
            raise ValueError("invalid_capture_limits")
        if not isinstance(collection["pages"], list) or len(collection["pages"]) > 165:
            raise ValueError("invalid_page_manifest")
        for page in collection["pages"]:
            _fields(page, {"symbol", "period", "start", "limit", "fetched_at", "count", "first", "last", "status"})
            if page["symbol"] not in series or page["period"] not in series[page["symbol"]] or page["status"] not in {"received", "empty", "failed"}:
                raise ValueError("invalid_page_manifest")
            local_timestamp(page["fetched_at"])
    except (TypeError, KeyError, AttributeError, OverflowError):
        raise ValueError("invalid_dataset") from None


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("dataset_too_large")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("dataset_too_large")
    try:
        return json.loads(raw, object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError("invalid_dataset_json") from None


def load_dataset(path: Path) -> dict:
    result = read_json(path)
    validate_dataset(result)
    return result


def write_json_exclusive(path: Path, value: dict) -> None:
    write_bytes_exclusive(path, canonical_json(value))


def write_bytes_exclusive(path: Path, raw: bytes) -> None:
    """A complete temporary file is linked atomically; an existing destination is never replaced."""
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError("output_exists")
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".chan-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def save_dataset(dataset: dict, root: Path) -> Path:
    validate_dataset(dataset)
    directory = Path(root) / dataset["dataset_id"]
    if directory.is_symlink():
        raise ValueError("dataset_directory_symlink")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "dataset.json"
    try:
        write_json_exclusive(path, dataset)
    except FileExistsError:
        if path.is_symlink() or load_dataset(path) != dataset:
            raise ValueError("dataset_path_conflict") from None
    return path
