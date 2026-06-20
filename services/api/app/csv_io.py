from __future__ import annotations

import csv
from io import StringIO
from typing import Any, Iterable


HOLDING_CSV_FIELDS = [
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
]

WATCHLIST_CSV_FIELDS = [
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
]

NUMERIC_FIELDS = {
    "quantity",
    "cost_price",
    "stop_loss",
    "take_profit",
    "max_loss_pct",
    "buy_zone_low",
    "buy_zone_high",
}

INTEGER_FIELDS = {"priority"}


def rows_to_csv(rows: Iterable[dict[str, Any]], fields: list[str]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field) for field in fields})
    return output.getvalue()


def csv_to_rows(csv_text: str, *, required_fields: set[str]) -> list[dict[str, Any]]:
    input_file = StringIO(csv_text)
    reader = csv.DictReader(input_file)
    if reader.fieldnames is None:
        raise ValueError("CSV header is required")

    missing = required_fields - set(reader.fieldnames)
    if missing:
        missing_fields = ", ".join(sorted(missing))
        raise ValueError(f"CSV missing required fields: {missing_fields}")

    rows: list[dict[str, Any]] = []
    for index, row in enumerate(reader, start=2):
        normalized = {key: _normalize_value(key, value) for key, value in row.items()}
        if not any(value is not None for value in normalized.values()):
            continue
        rows.append(normalized)
        if not normalized.get("symbol"):
            raise ValueError(f"Row {index} is missing symbol")
    return rows


def _normalize_value(key: str, value: str | None) -> Any:
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    if key in NUMERIC_FIELDS:
        return float(stripped)
    if key in INTEGER_FIELDS:
        return int(stripped)
    return stripped
