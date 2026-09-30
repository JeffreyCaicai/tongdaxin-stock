"""Bounded upstream screening. A screening result is only a candidate."""
from __future__ import annotations

import re
from .market_data import MarketDataError, _tdx_official_post

QUERIES = (
    ("trend", "非ST，上市天数大于180，成交额大于1亿元，20日涨幅大于0，60日涨幅大于0，按成交额从大到小排序"),
    ("pullback", "非ST，上市天数大于180，成交额大于1亿元，股价大于60日均线，5日涨幅小于0，60日涨幅大于0，按成交额从大到小排序"),
    ("strength", "非ST，上市天数大于180，成交额大于1亿元，20日涨幅大于0，按20日涨幅从大到小排序"),
)


def canonical_stock(symbol: str, market: str | None = None) -> str | None:
    value = symbol.strip().upper()
    if len(value) == 8 and value[0:2] in {"0.", "1.", "2."}:
        value = {"0": "SZ", "1": "SH", "2": "BJ"}[value[0]] + value[2:]
    prefix = value[:2] if value[:2] in {"SH", "SZ", "BJ"} else None
    code = value[2:] if prefix else value
    expected = (
        "SH" if re.fullmatch(r"(?:60|68)\d{4}", code)
        else "SZ" if re.fullmatch(r"(?:00|30)\d{4}", code)
        else "BJ" if re.fullmatch(r"(?:[48]\d{5}|92\d{4})", code)
        else None
    )
    supplied = {"0": "SZ", "1": "SH", "2": "BJ"}.get(market) if market is not None else expected
    if expected is None or supplied != expected or (prefix and prefix != expected):
        return None
    return f"BJ{code}" if expected == "BJ" else code


def parse_screen(raw: object) -> dict:
    if not isinstance(raw, list) or len(raw) < 3:
        raise MarketDataError("Invalid screener table")
    meta, headers = raw[:2]
    if not isinstance(meta, list) or len(meta) < 5 or not isinstance(headers, list):
        raise MarketDataError("Invalid screener metadata")
    try:
        code, total = int(meta[0]), int(meta[2])
    except (ValueError, TypeError):
        raise MarketDataError("Invalid screener status") from None
    if code != 0:
        raise MarketDataError(f"Screener rejected request (code {code})")
    if not {"sec_code", "sec_name", "market"}.issubset(headers):
        raise MarketDataError("Screener security columns missing")
    items = []
    for row in raw[3:]:
        if not isinstance(row, list):
            continue
        data = dict(zip(headers, row))
        market = str(data.get("market", ""))
        symbol = canonical_stock(str(data.get("sec_code", "")), market)
        if symbol is None:
            continue
        items.append({"symbol": symbol, "name": str(data.get("sec_name") or ""), "market": market})
    return {"total": total, "items": items, "row_count": len(raw[3:])}


def discover_candidates(source: str, limit: int, cancelled=lambda: False) -> dict:
    if source == "mock":
        return {"source": "mock", "queries": [], "errors": [], "candidate_count": 3,
                "items": [{"symbol": code, "name": f"Mock {code}", "themes": ["trend"]}
                          for code in ("600036", "000333", "603087")], "is_demo": True}
    if source != "tdx-official":
        raise MarketDataError("Market discovery requires tdx-official")
    groups, queries, errors = [], [], []
    for theme, query in QUERIES:
        group, total, rows, pages = [], 0, 0, 0
        for page in (1, 2):
            if cancelled():
                break
            try:
                result = parse_screen(_tdx_official_post("JNLPSE:wendaQuery", [{
                    "message": query, "rang": "AG", "pageNo": str(page), "pageSize": "20",
                }]))
            except Exception:
                # Upstream errors can echo request content; never persist raw errors.
                errors.append({"theme": theme, "page": page, "reason": "screen_unavailable"})
                break
            pages += 1
            total = result["total"]
            rows += result["row_count"]
            group.extend({**item, "themes": [theme]} for item in result["items"])
            if result["row_count"] < 20 or rows >= total:
                break
        queries.append({"theme": theme, "query": query, "total": total, "rows_read": rows,
                        "pages_read": pages, "truncated": rows < total})
        groups.append(group)
    unique = {}
    for index in range(max((len(g) for g in groups), default=0)):
        for group in groups:
            if index >= len(group):
                continue
            item = group[index]
            if item["symbol"] in unique:
                old = unique[item["symbol"]]
                old["themes"] = sorted(set(old["themes"] + item["themes"]))
            else:
                unique[item["symbol"]] = item
    return {"source": source, "queries": queries, "errors": errors,
            "candidate_count": len(unique), "items": list(unique.values())[:limit], "is_demo": False}
