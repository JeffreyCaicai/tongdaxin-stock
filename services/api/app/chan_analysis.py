from __future__ import annotations

from typing import Any

from .repository import normalize_symbol, utc_now


def analyze_chan_structure(
    *,
    symbol: str,
    bars: list[dict[str, Any]],
    name: str | None = None,
    period: str = "daily",
) -> dict[str, Any]:
    normalized_symbol = normalize_symbol(symbol)
    ordered = sorted(bars, key=lambda bar: str(bar["trade_date"]))
    merged = _merge_contained_bars(ordered)
    fractals = _detect_fractals(merged)
    strokes = _build_strokes(fractals)
    centers = _detect_centers(strokes)
    current_price = float(ordered[-1]["close"]) if ordered else None
    signal = _candidate_signal(
        current_price=current_price,
        strokes=strokes,
        centers=centers,
    )

    return {
        "symbol": normalized_symbol,
        "name": name,
        "period": period,
        "bar_count": len(ordered),
        "merged_bar_count": len(merged),
        "fractal_count": len(fractals),
        "stroke_count": len(strokes),
        "center_count": len(centers),
        "current_price": current_price,
        "structure": _structure_label(strokes=strokes, centers=centers, current_price=current_price),
        "signal": signal,
        "latest_center": centers[-1] if centers else None,
        "latest_strokes": strokes[-5:],
        "latest_fractals": fractals[-6:],
    }


def generate_stock_pool_chan_analysis(
    *,
    pool: dict[str, Any],
    watchlist: list[dict[str, Any]],
    kline_by_symbol: dict[str, list[dict[str, Any]]],
    source: str,
    period: str = "daily",
    failed_symbols: list[str] | None = None,
    max_symbols: int = 30,
) -> dict[str, Any]:
    max_symbols = max(1, min(int(max_symbols), 100))
    ordered_symbols = _watchlist_symbol_order(watchlist)[:max_symbols]
    watchlist_by_symbol = {
        normalize_symbol(str(item["symbol"])): item for item in watchlist
    }
    items: list[dict[str, Any]] = []

    for symbol in ordered_symbols:
        bars = kline_by_symbol.get(symbol) or []
        item = watchlist_by_symbol.get(symbol)
        if bars:
            items.append(
                analyze_chan_structure(
                    symbol=symbol,
                    name=item.get("name") if item else None,
                    bars=bars,
                    period=period,
                )
            )
        else:
            items.append(
                {
                    "symbol": symbol,
                    "name": item.get("name") if item else None,
                    "period": period,
                    "bar_count": 0,
                    "merged_bar_count": 0,
                    "fractal_count": 0,
                    "stroke_count": 0,
                    "center_count": 0,
                    "current_price": None,
                    "structure": "insufficient_data",
                    "signal": {
                        "type": "complete_market_data",
                        "label": "补齐K线",
                        "action": "先补齐K线数据",
                        "confidence": "low",
                        "reason": "没有可用K线，无法识别分型、笔和中枢。",
                        "trigger": None,
                        "invalidation": None,
                    },
                    "latest_center": None,
                    "latest_strokes": [],
                    "latest_fractals": [],
                }
            )

    signal_counts: dict[str, int] = {}
    for item in items:
        signal_type = str(item.get("signal", {}).get("type") or "unknown")
        signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1

    failed_symbols = [normalize_symbol(symbol) for symbol in (failed_symbols or [])]
    pool_name = pool.get("name") or f"Pool {pool.get('id')}"
    return {
        "report_type": "stock_pool_chan_analysis",
        "symbol": None,
        "generated_at": utc_now(),
        "summary": (
            f"已用 {source} 的 {period} K线完成“{pool_name}”缠论结构分析："
            f"{len(items)} 只股票，{len(failed_symbols)} 只K线拉取失败。"
        ),
        "pool": {
            "id": pool.get("id"),
            "name": pool_name,
            "description": pool.get("description"),
        },
        "scope": {
            "symbol_limit": max_symbols,
            "symbol_count": len(items),
            "period": period,
        },
        "tool_plan": {
            "data_source": source,
            "kline_tool": "PBFXT",
        },
        "data_quality": {
            "failed_symbol_count": len(failed_symbols),
            "failed_symbols": failed_symbols,
        },
        "signal_counts": signal_counts,
        "items": items,
        "next_steps": _pool_next_steps(items, failed_symbols),
    }


def _merge_contained_bars(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for raw in bars:
        bar = _bar(raw)
        if not merged:
            merged.append(bar)
            continue
        last = merged[-1]
        if _contains(last, bar) or _contains(bar, last):
            direction = _merge_direction(merged, bar)
            if direction >= 0:
                last["high"] = max(last["high"], bar["high"])
                last["low"] = max(last["low"], bar["low"])
            else:
                last["high"] = min(last["high"], bar["high"])
                last["low"] = min(last["low"], bar["low"])
            last["close"] = bar["close"]
            last["end_date"] = bar["trade_date"]
            last["volume"] = (last.get("volume") or 0) + (bar.get("volume") or 0)
            continue
        merged.append(bar)
    return merged


def _detect_fractals(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fractals: list[dict[str, Any]] = []
    for index in range(1, len(bars) - 1):
        previous = bars[index - 1]
        current = bars[index]
        following = bars[index + 1]
        if current["high"] > previous["high"] and current["high"] > following["high"]:
            fractals.append(_fractal("top", index, current, current["high"]))
        if current["low"] < previous["low"] and current["low"] < following["low"]:
            fractals.append(_fractal("bottom", index, current, current["low"]))
    return fractals


def _build_strokes(fractals: list[dict[str, Any]], min_distance: int = 4) -> list[dict[str, Any]]:
    pivots: list[dict[str, Any]] = []
    for fractal in fractals:
        if not pivots:
            pivots.append(fractal)
            continue
        last = pivots[-1]
        if fractal["type"] == last["type"]:
            if _is_more_extreme(fractal, last):
                pivots[-1] = fractal
            continue
        if fractal["index"] - last["index"] >= min_distance:
            pivots.append(fractal)

    strokes: list[dict[str, Any]] = []
    for start, end in zip(pivots, pivots[1:]):
        direction = "up" if start["type"] == "bottom" and end["type"] == "top" else "down"
        strokes.append(
            {
                "direction": direction,
                "start_date": start["date"],
                "end_date": end["date"],
                "start_price": start["price"],
                "end_price": end["price"],
                "high": max(start["price"], end["price"]),
                "low": min(start["price"], end["price"]),
                "bar_span": end["index"] - start["index"],
            }
        )
    return strokes


def _detect_centers(strokes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    centers: list[dict[str, Any]] = []
    for index in range(0, max(0, len(strokes) - 2)):
        group = strokes[index : index + 3]
        lower = max(stroke["low"] for stroke in group)
        upper = min(stroke["high"] for stroke in group)
        if lower <= upper:
            center = {
                "start_date": group[0]["start_date"],
                "end_date": group[-1]["end_date"],
                "lower": round(lower, 4),
                "upper": round(upper, 4),
                "stroke_start": index,
                "stroke_end": index + 2,
            }
            if centers and _center_overlaps(centers[-1], center):
                centers[-1]["end_date"] = center["end_date"]
                centers[-1]["lower"] = max(centers[-1]["lower"], center["lower"])
                centers[-1]["upper"] = min(centers[-1]["upper"], center["upper"])
                centers[-1]["stroke_end"] = center["stroke_end"]
            else:
                centers.append(center)
    return centers


def _candidate_signal(
    *,
    current_price: float | None,
    strokes: list[dict[str, Any]],
    centers: list[dict[str, Any]],
) -> dict[str, Any]:
    if current_price is None:
        return _signal(
            "complete_market_data",
            "补齐行情",
            "先补齐行情",
            "缺少当前价格，无法判断结构位置。",
        )
    if len(strokes) < 3:
        return _signal(
            "wait_for_structure",
            "等待结构",
            "观察",
            "笔数量不足，暂不生成买卖候选。",
        )
    latest_stroke = strokes[-1]
    latest_center = centers[-1] if centers else None
    if latest_center is None:
        return _signal(
            "trend_observe",
            "趋势观察",
            "观察",
            "已有笔结构但尚未形成三笔重叠中枢。",
            trigger=None,
            invalidation=_stroke_invalidation(latest_stroke),
        )

    lower = float(latest_center["lower"])
    upper = float(latest_center["upper"])
    if lower <= current_price <= upper:
        return _signal(
            "center_range",
            "中枢震荡",
            "观察，不追买",
            "当前价仍在最近中枢内，方向尚未离开中枢。",
            trigger=f"有效离开中枢上沿 {upper:.3f} 后再观察回抽。",
            invalidation=f"跌破中枢下沿 {lower:.3f} 代表结构转弱。",
        )
    if current_price > upper:
        if latest_stroke["direction"] == "down":
            return _signal(
                "suspected_third_buy",
                "疑似三买观察",
                "等待回踩确认",
                "价格位于中枢上方，最近一笔为回落笔，若回踩不回中枢，可视为三买候选。",
                trigger=f"回踩不跌回 {upper:.3f}，再出现向上笔。",
                invalidation=f"跌回中枢上沿 {upper:.3f} 下方。",
            )
        return _signal(
            "upward_leave",
            "向上离开中枢",
            "持有/观察",
            "价格在中枢上方运行，但尚未完成回踩确认。",
            trigger=f"回踩确认不跌回 {upper:.3f}。",
            invalidation=f"重新跌回 {upper:.3f} 下方。",
        )
    if current_price < lower:
        if latest_stroke["direction"] == "up":
            return _signal(
                "suspected_third_sell",
                "疑似三卖观察",
                "减仓/风控",
                "价格位于中枢下方，最近一笔为反抽笔，若反抽不回中枢，可视为三卖候选。",
                trigger=f"反抽不站回 {lower:.3f}，再出现向下笔。",
                invalidation=f"重新站回中枢下沿 {lower:.3f} 上方。",
            )
        return _signal(
            "downward_leave",
            "向下离开中枢",
            "风控优先",
            "价格在中枢下方运行，结构偏弱。",
            trigger=f"反抽不能收回 {lower:.3f}。",
            invalidation=f"重新站回 {lower:.3f} 上方。",
        )
    return _signal("observe", "观察", "观察", "结构位置中性。")


def _structure_label(
    *,
    strokes: list[dict[str, Any]],
    centers: list[dict[str, Any]],
    current_price: float | None,
) -> str:
    if len(strokes) < 3:
        return "结构未成型"
    if not centers:
        return "趋势段观察"
    center = centers[-1]
    if current_price is None:
        return "中枢已形成"
    if current_price > center["upper"]:
        return "中枢上方"
    if current_price < center["lower"]:
        return "中枢下方"
    return "中枢震荡"


def _bar(raw: dict[str, Any]) -> dict[str, Any]:
    trade_date = str(raw["trade_date"])
    return {
        "trade_date": trade_date,
        "end_date": trade_date,
        "open": float(raw["open"]),
        "high": float(raw["high"]),
        "low": float(raw["low"]),
        "close": float(raw["close"]),
        "volume": float(raw.get("volume") or 0),
    }


def _contains(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left["high"] >= right["high"] and left["low"] <= right["low"]


def _merge_direction(merged: list[dict[str, Any]], current: dict[str, Any]) -> int:
    if len(merged) >= 2:
        previous = merged[-2]
        last = merged[-1]
        if last["high"] > previous["high"] and last["low"] > previous["low"]:
            return 1
        if last["high"] < previous["high"] and last["low"] < previous["low"]:
            return -1
    return 1 if current["close"] >= merged[-1]["close"] else -1


def _fractal(kind: str, index: int, bar: dict[str, Any], price: float) -> dict[str, Any]:
    return {
        "type": kind,
        "index": index,
        "date": bar["trade_date"],
        "price": round(price, 4),
        "high": round(bar["high"], 4),
        "low": round(bar["low"], 4),
    }


def _is_more_extreme(candidate: dict[str, Any], current: dict[str, Any]) -> bool:
    if candidate["type"] == "top":
        return candidate["price"] >= current["price"]
    return candidate["price"] <= current["price"]


def _center_overlaps(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return max(left["lower"], right["lower"]) <= min(left["upper"], right["upper"])


def _signal(
    signal_type: str,
    label: str,
    action: str,
    reason: str,
    *,
    trigger: str | None = None,
    invalidation: str | None = None,
    confidence: str = "medium",
) -> dict[str, Any]:
    return {
        "type": signal_type,
        "label": label,
        "action": action,
        "confidence": confidence,
        "reason": reason,
        "trigger": trigger,
        "invalidation": invalidation,
    }


def _stroke_invalidation(stroke: dict[str, Any]) -> str:
    if stroke["direction"] == "up":
        return f"跌破最近上行笔起点 {stroke['start_price']:.3f}。"
    return f"突破最近下行笔起点 {stroke['start_price']:.3f}。"


def _watchlist_symbol_order(watchlist: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(
        watchlist,
        key=lambda row: (
            int(row.get("priority") or 99),
            str(row.get("updated_at") or ""),
            int(row.get("id") or 0),
        ),
    )
    symbols: list[str] = []
    seen: set[str] = set()
    for row in ordered:
        symbol = normalize_symbol(str(row["symbol"]))
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def _pool_next_steps(items: list[dict[str, Any]], failed_symbols: list[str]) -> list[str]:
    steps: list[str] = []
    if failed_symbols:
        steps.append("补齐失败股票的K线数据")
    if any(item.get("signal", {}).get("type") in {"suspected_third_buy", "upward_leave"} for item in items):
        steps.append("优先观察中枢上方且等待回踩确认的股票")
    if any(item.get("signal", {}).get("type") in {"suspected_third_sell", "downward_leave"} for item in items):
        steps.append("优先处理跌破中枢或疑似三卖的风险股票")
    if not steps:
        steps.append("等待更多K线形成清晰分型、笔和中枢")
    return steps
