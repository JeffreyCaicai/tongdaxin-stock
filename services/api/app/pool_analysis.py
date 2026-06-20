from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .mcp_tools import McpServerConfig, McpStdioClient
from .repository import normalize_symbol, utc_now


QUOTE_TOOL_CANDIDATES = (
    "tdx_quotes",
    "tdx_quote",
    "quotes",
    "quote",
    "get_quote",
    "get_quotes",
    "fetch_quote",
    "stock_quote",
)

PROFILE_TOOL_CANDIDATES = (
    "tdx_lookup_stock",
    "tdx_company_info",
    "tdx_api_data",
    "tdx_f10",
    "company_info",
    "stock_profile",
    "f10",
)

QUOTE_TOOL_KEYWORDS = ("quote", "quotes", "snapshot", "行情")
PROFILE_TOOL_KEYWORDS = ("lookup", "company", "profile", "info", "f10", "公司", "基本面")
PRICE_KEYS = ("price", "current_price", "last_price", "close", "最新价", "现价")
NAME_KEYS = ("name", "stock_name", "security_name", "股票名称", "名称")


def generate_stock_pool_mcp_analysis(
    *,
    pool: dict[str, Any],
    holdings: list[dict[str, Any]],
    watchlist: list[dict[str, Any]],
    max_symbols: int = 30,
    quote_tool: str | None = None,
    profile_tool: str | None = None,
    include_profile: bool = True,
    quote_arguments: dict[str, Any] | None = None,
    profile_arguments: dict[str, Any] | None = None,
    mcp_config: McpServerConfig | None = None,
) -> dict[str, Any]:
    max_symbols = max(1, min(int(max_symbols), 100))
    pool_symbols = _pool_symbol_order(holdings=holdings, watchlist=watchlist)[:max_symbols]
    holding_by_symbol = {
        normalize_symbol(str(holding["symbol"])): holding for holding in holdings
    }
    watchlist_by_symbol = {
        normalize_symbol(str(item["symbol"])): item for item in watchlist
    }

    with McpStdioClient(mcp_config or _default_config()) as client:
        client.initialize()
        tools = client.list_tools()
        quote_tool_row = _select_tool(
            tools=tools,
            requested=quote_tool,
            candidates=QUOTE_TOOL_CANDIDATES,
            keywords=QUOTE_TOOL_KEYWORDS,
        )
        profile_tool_row = (
            _select_tool(
                tools=tools,
                requested=profile_tool,
                candidates=PROFILE_TOOL_CANDIDATES,
                keywords=PROFILE_TOOL_KEYWORDS,
            )
            if include_profile
            else None
        )

        items = [
            _analyze_symbol(
                client=client,
                symbol=symbol,
                holding=holding_by_symbol.get(symbol),
                watchlist_item=watchlist_by_symbol.get(symbol),
                quote_tool=quote_tool_row,
                profile_tool=profile_tool_row,
                quote_arguments=quote_arguments,
                profile_arguments=profile_arguments,
            )
            for symbol in pool_symbols
        ]

    return _build_pool_report(
        pool=pool,
        holdings=holdings,
        watchlist=watchlist,
        tools=tools,
        quote_tool=quote_tool_row,
        profile_tool=profile_tool_row,
        include_profile=include_profile,
        items=items,
        symbol_limit=max_symbols,
    )


def generate_stock_pool_market_analysis(
    *,
    pool: dict[str, Any],
    holdings: list[dict[str, Any]],
    watchlist: list[dict[str, Any]],
    quotes: dict[str, dict[str, Any]],
    source: str,
    failed_symbols: list[str] | None = None,
    max_symbols: int = 30,
) -> dict[str, Any]:
    max_symbols = max(1, min(int(max_symbols), 100))
    pool_symbols = _pool_symbol_order(holdings=holdings, watchlist=watchlist)[:max_symbols]
    holding_by_symbol = {
        normalize_symbol(str(holding["symbol"])): holding for holding in holdings
    }
    watchlist_by_symbol = {
        normalize_symbol(str(item["symbol"])): item for item in watchlist
    }

    items: list[dict[str, Any]] = []
    for symbol in pool_symbols:
        quote = quotes.get(symbol)
        price = quote.get("price") if quote else None
        holding = holding_by_symbol.get(symbol)
        watchlist_item = watchlist_by_symbol.get(symbol)
        name = _first_non_none(
            quote.get("name") if quote else None,
            holding.get("name") if holding else None,
            watchlist_item.get("name") if watchlist_item else None,
        )
        items.append(
            {
                "symbol": symbol,
                "name": name,
                "position": _position_context(holding, price),
                "watchlist": _watchlist_context(watchlist_item),
                "quote": {
                    "status": "success" if quote else "missing",
                    "fields": {
                        "price": price,
                        "name": quote.get("name") if quote else None,
                        "source": quote.get("source") if quote else source,
                        "snapshot_id": quote.get("snapshot_id") if quote else None,
                        "fetched_at": quote.get("fetched_at") if quote else None,
                    },
                },
                "mcp_calls": {},
                "action_hint": _action_hint(
                    holding=holding,
                    watchlist_item=watchlist_item,
                    price=price,
                ),
            }
        )

    failed_symbols = [normalize_symbol(symbol) for symbol in (failed_symbols or [])]
    missing_quote_items = [
        item for item in items if item["action_hint"] == "complete_market_data"
    ]
    action_counts: dict[str, int] = {}
    for item in items:
        action = item["action_hint"]
        action_counts[action] = action_counts.get(action, 0) + 1

    pool_name = pool.get("name") or f"Pool {pool.get('id')}"
    quote_count = len(items) - len(missing_quote_items)
    return {
        "report_type": "stock_pool_market_analysis",
        "symbol": None,
        "generated_at": utc_now(),
        "summary": (
            f"已用 {source} 分析股票池“{pool_name}”：共 {len(items)} 只，"
            f"{quote_count} 只有行情，{len(missing_quote_items)} 只需补齐行情。"
        ),
        "pool": {
            "id": pool.get("id"),
            "name": pool_name,
            "description": pool.get("description"),
        },
        "scope": {
            "symbol_limit": max_symbols,
            "symbol_count": len(items),
            "holding_count": len(holdings),
            "watchlist_count": len(watchlist),
        },
        "tool_plan": {
            "server": None,
            "data_source": source,
            "quote_tool": source,
            "profile_tool": None,
            "missing_tools": [],
        },
        "action_counts": action_counts,
        "data_quality": {
            "failed_symbol_count": len(failed_symbols),
            "missing_quote_count": len(missing_quote_items),
            "quote_count": quote_count,
            "failed_symbols": failed_symbols,
        },
        "items": items,
        "next_steps": _next_steps(
            missing_quote_count=len(missing_quote_items),
            failed_count=len(failed_symbols),
            action_counts=action_counts,
        ),
    }


def _default_config() -> McpServerConfig:
    from .mcp_tools import eltdx_mcp_config

    return eltdx_mcp_config()


def _pool_symbol_order(
    *,
    holdings: list[dict[str, Any]],
    watchlist: list[dict[str, Any]],
) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    ordered_rows = sorted(
        watchlist,
        key=lambda row: (
            int(row.get("priority") or 99),
            str(row.get("updated_at") or ""),
            int(row.get("id") or 0),
        ),
    )
    for row in ordered_rows + holdings:
        symbol = normalize_symbol(str(row["symbol"]))
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def _select_tool(
    *,
    tools: list[dict[str, Any]],
    requested: str | None,
    candidates: tuple[str, ...],
    keywords: tuple[str, ...],
) -> dict[str, Any] | None:
    if not tools:
        return None
    if requested:
        for tool in tools:
            if str(tool.get("name", "")).lower() == requested.lower():
                return tool
        return None

    scored: list[tuple[int, dict[str, Any]]] = []
    candidate_set = {candidate.lower() for candidate in candidates}
    for tool in tools:
        name = str(tool.get("name", ""))
        lower_name = name.lower()
        description = str(tool.get("description", "")).lower()
        haystack = f"{lower_name} {description}"
        score = 0
        if lower_name in candidate_set:
            score += 100
        for index, candidate in enumerate(candidates):
            if candidate.lower() in lower_name:
                score += 70 - index
        for keyword in keywords:
            if keyword.lower() in haystack:
                score += 20
        if score:
            scored.append((score, tool))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def _analyze_symbol(
    *,
    client: McpStdioClient,
    symbol: str,
    holding: dict[str, Any] | None,
    watchlist_item: dict[str, Any] | None,
    quote_tool: dict[str, Any] | None,
    profile_tool: dict[str, Any] | None,
    quote_arguments: dict[str, Any] | None,
    profile_arguments: dict[str, Any] | None,
) -> dict[str, Any]:
    calls: dict[str, Any] = {}
    quote_summary: dict[str, Any] | None = None
    profile_summary: dict[str, Any] | None = None

    if quote_tool is None:
        calls["quote"] = {"status": "skipped", "message": "No quote-like MCP tool found."}
    else:
        args = _tool_arguments(quote_tool, symbol, quote_arguments)
        quote_summary = _call_and_summarize(client, quote_tool, args)
        calls["quote"] = quote_summary

    if profile_tool is None:
        calls["profile"] = {
            "status": "skipped",
            "message": "No profile/F10-like MCP tool found.",
        }
    else:
        args = _tool_arguments(profile_tool, symbol, profile_arguments)
        profile_summary = _call_and_summarize(client, profile_tool, args)
        calls["profile"] = profile_summary

    price = _first_non_none(
        (quote_summary or {}).get("fields", {}).get("price"),
        _recursive_find((quote_summary or {}).get("raw", {}), PRICE_KEYS),
    )
    name = _first_non_none(
        (profile_summary or {}).get("fields", {}).get("name"),
        (quote_summary or {}).get("fields", {}).get("name"),
        _recursive_find((profile_summary or {}).get("raw", {}), NAME_KEYS),
        holding.get("name") if holding else None,
        watchlist_item.get("name") if watchlist_item else None,
    )

    return {
        "symbol": symbol,
        "name": name,
        "position": _position_context(holding, price),
        "watchlist": _watchlist_context(watchlist_item),
        "mcp_calls": calls,
        "action_hint": _action_hint(holding=holding, watchlist_item=watchlist_item, price=price),
    }


def _call_and_summarize(
    client: McpStdioClient,
    tool: dict[str, Any],
    arguments: dict[str, Any],
) -> dict[str, Any]:
    tool_name = str(tool.get("name", ""))
    try:
        result = client.call_tool(tool_name, arguments)
    except Exception as exc:  # Keep one failed symbol from blocking the pool report.
        return {
            "tool_name": tool_name,
            "arguments": arguments,
            "status": "error",
            "message": str(exc),
        }
    summary = _summarize_mcp_result(result)
    summary.update(
        {
            "tool_name": tool_name,
            "arguments": arguments,
            "status": "error" if result.get("isError") else "success",
            "raw": result,
        }
    )
    return summary


def _tool_arguments(
    tool: dict[str, Any],
    symbol: str,
    template: dict[str, Any] | None,
) -> dict[str, Any]:
    if template:
        return _fill_placeholders(template, symbol)

    schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    properties = schema.get("properties", {}) if isinstance(schema, Mapping) else {}
    required = schema.get("required", []) if isinstance(schema, Mapping) else []
    keys = list(dict.fromkeys(list(required) + list(properties.keys())))
    if not keys:
        return {"symbol": symbol}

    args: dict[str, Any] = {}
    for key in keys:
        value = _argument_value_for_key(key, symbol, properties.get(key, {}))
        if value is not None:
            args[key] = value
    if not args:
        args["symbol"] = symbol
    return args


def _argument_value_for_key(key: str, symbol: str, property_schema: Any) -> Any:
    lower_key = key.lower()
    tdx_code = _tdx_code(symbol)
    market = "SH" if symbol.startswith(("6", "9")) else "SZ"
    if "market" in lower_key:
        return market
    if "tdx" in lower_key and "code" in lower_key:
        return tdx_code
    if lower_key in {"symbol", "stock", "stock_symbol"}:
        return symbol
    if lower_key in {"symbols", "stocks"}:
        return [symbol]
    if lower_key in {"code", "stock_code", "security_code", "sec_code"}:
        return tdx_code
    if lower_key in {"codes", "stock_codes", "security_codes"}:
        schema_type = (
            property_schema.get("type")
            if isinstance(property_schema, Mapping)
            else None
        )
        return [tdx_code] if schema_type == "array" else tdx_code
    if lower_key in {"seed_code"}:
        return tdx_code
    if lower_key in {"tdx_code", "full_code"}:
        return tdx_code
    if lower_key in {"tdx_codes", "full_codes"}:
        return [tdx_code]
    return None


def _fill_placeholders(value: Any, symbol: str) -> Any:
    tdx_code = _tdx_code(symbol)
    market = "SH" if symbol.startswith(("6", "9")) else "SZ"
    if isinstance(value, str):
        return (
            value.replace("{symbol}", symbol)
            .replace("{tdx_code}", tdx_code)
            .replace("{market}", market)
        )
    if isinstance(value, list):
        return [_fill_placeholders(item, symbol) for item in value]
    if isinstance(value, dict):
        return {key: _fill_placeholders(item, symbol) for key, item in value.items()}
    return value


def _summarize_mcp_result(result: dict[str, Any]) -> dict[str, Any]:
    text = _content_text(result)
    fields = {
        "price": _to_float(_recursive_find(result, PRICE_KEYS)),
        "name": _recursive_find(result, NAME_KEYS),
    }
    fields = {key: value for key, value in fields.items() if value is not None}
    return {
        "is_error": bool(result.get("isError")),
        "text": text[:1200],
        "fields": fields,
    }


def _content_text(result: dict[str, Any]) -> str:
    content = result.get("content", [])
    chunks: list[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, Mapping) and isinstance(item.get("text"), str):
                chunks.append(item["text"])
    if not chunks and "structuredContent" in result:
        chunks.append(str(result["structuredContent"]))
    return "\n".join(chunks)


def _recursive_find(value: Any, keys: tuple[str, ...]) -> Any:
    key_set = {key.lower() for key in keys}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in key_set:
                return item
        for item in value.values():
            found = _recursive_find(item, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _recursive_find(item, keys)
            if found is not None:
                return found
    return None


def _position_context(holding: dict[str, Any] | None, price: Any) -> dict[str, Any] | None:
    if holding is None:
        return None
    cost_price = _to_float(holding.get("cost_price"))
    current_price = _to_float(price)
    pnl_pct = None
    if cost_price and current_price:
        pnl_pct = round(((current_price - cost_price) / cost_price) * 100, 2)
    return {
        "holding_id": holding.get("id"),
        "quantity": holding.get("quantity"),
        "cost_price": holding.get("cost_price"),
        "stop_loss": holding.get("stop_loss"),
        "take_profit": holding.get("take_profit"),
        "pnl_pct": pnl_pct,
    }


def _watchlist_context(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        "watchlist_id": item.get("id"),
        "priority": item.get("priority"),
        "status": item.get("status"),
        "thesis": item.get("thesis"),
        "trigger_condition": item.get("trigger_condition"),
        "invalidation_condition": item.get("invalidation_condition"),
    }


def _action_hint(
    *,
    holding: dict[str, Any] | None,
    watchlist_item: dict[str, Any] | None,
    price: Any,
) -> str:
    current_price = _to_float(price)
    if current_price is None:
        return "complete_market_data"
    if holding:
        stop_loss = _to_float(holding.get("stop_loss"))
        take_profit = _to_float(holding.get("take_profit"))
        if stop_loss and current_price <= stop_loss:
            return "review_stop_loss"
        if take_profit and current_price >= take_profit:
            return "review_take_profit"
        return "hold_and_monitor"
    if watchlist_item:
        low = _to_float(watchlist_item.get("buy_zone_low"))
        high = _to_float(watchlist_item.get("buy_zone_high"))
        if low and high and low <= current_price <= high:
            return "review_buy_zone"
        return "watch_pool_candidate"
    return "observe"


def _build_pool_report(
    *,
    pool: dict[str, Any],
    holdings: list[dict[str, Any]],
    watchlist: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    quote_tool: dict[str, Any] | None,
    profile_tool: dict[str, Any] | None,
    include_profile: bool,
    items: list[dict[str, Any]],
    symbol_limit: int,
) -> dict[str, Any]:
    failed_items = [
        item
        for item in items
        if any(call.get("status") == "error" for call in item["mcp_calls"].values())
    ]
    missing_quote_items = [
        item for item in items if item["action_hint"] == "complete_market_data"
    ]
    action_counts: dict[str, int] = {}
    for item in items:
        action = item["action_hint"]
        action_counts[action] = action_counts.get(action, 0) + 1

    pool_name = pool.get("name") or f"Pool {pool.get('id')}"
    return {
        "report_type": "stock_pool_mcp_analysis",
        "symbol": None,
        "generated_at": utc_now(),
        "summary": (
            f"Analyzed stock pool '{pool_name}' with {len(items)} symbols via MCP. "
            f"{len(missing_quote_items)} symbols still need market data review."
        ),
        "pool": {
            "id": pool.get("id"),
            "name": pool_name,
            "description": pool.get("description"),
        },
        "scope": {
            "symbol_limit": symbol_limit,
            "symbol_count": len(items),
            "holding_count": len(holdings),
            "watchlist_count": len(watchlist),
        },
        "tool_plan": {
            "server": "eltdx-mcp",
            "available_tools": [tool.get("name") for tool in tools],
            "quote_tool": quote_tool.get("name") if quote_tool else None,
            "profile_tool": profile_tool.get("name") if profile_tool else None,
            "missing_tools": [
                label
                for label, tool in (("quote", quote_tool), ("profile", profile_tool))
                if tool is None and (label != "profile" or include_profile)
            ],
        },
        "action_counts": action_counts,
        "data_quality": {
            "failed_symbol_count": len(failed_items),
            "missing_quote_count": len(missing_quote_items),
            "failed_symbols": [item["symbol"] for item in failed_items],
        },
        "items": items,
        "next_steps": _next_steps(
            missing_quote_count=len(missing_quote_items),
            failed_count=len(failed_items),
            action_counts=action_counts,
        ),
    }


def _next_steps(
    *,
    missing_quote_count: int,
    failed_count: int,
    action_counts: dict[str, int],
) -> list[str]:
    steps = []
    if failed_count:
        steps.append("check_mcp_tool_errors")
    if missing_quote_count:
        steps.append("complete_market_data")
    if action_counts.get("review_stop_loss"):
        steps.append("review_stop_loss_first")
    if action_counts.get("review_take_profit"):
        steps.append("review_take_profit_plan")
    if not steps:
        steps.append("review_pool_candidates")
    return steps


def _tdx_code(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    prefix = "sh" if normalized.startswith(("6", "9")) else "sz"
    return f"{prefix}{normalized}"


def _first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
