from __future__ import annotations

from datetime import date
from typing import Any

from .opportunity_prices import completed_daily_bars, local_timestamp
from .repository import normalize_symbol, utc_now

MODEL_VERSION = "daily_pen_overlap_v2"


def analyze_chan_structure(
    *,
    symbol: str,
    bars: list[dict[str, Any]],
    name: str | None = None,
    period: str = "daily",
    as_of: str | None = None,
) -> dict[str, Any]:
    if period != "daily":
        raise ValueError("Chan structure currently supports completed daily bars only")
    generated_at = as_of or utc_now()
    normalized_symbol = normalize_symbol(symbol)
    ordered, issues = completed_daily_bars(bars, generated_at)
    latest_date = ordered[-1]["trade_date"] if ordered else None
    age_days = ((local_timestamp(generated_at).date() - date.fromisoformat(latest_date)).days
                if latest_date else None)
    if age_days is not None and age_days > 10:
        issues.append("stale_kline")
    if len(ordered) < 35:
        issues.append("insufficient_bars")
    merged = _merge_contained_bars(ordered)
    fractals = _detect_fractals(merged)
    strokes = _build_strokes(fractals, bars=ordered)
    stable_strokes = [stroke for stroke in strokes if stroke["confirmed"]]
    centers = _detect_centers(stable_strokes)
    current_price = float(ordered[-1]["close"]) if ordered else None
    signal = _candidate_signal(
        current_price=current_price,
        strokes=stable_strokes,
        centers=centers,
    )
    if not ordered:
        signal = _signal("complete_market_data", "补齐K线", "数据复核",
                         "没有可用的已收盘日线，不能判断结构。", confidence="low")
    elif issues:
        signal = _signal("data_review", "数据待复核", "数据复核",
                         "K线存在缺损、重复、陈旧或样本不足，历史结构仅作参考。", confidence="low")
    last_stroke_age = (sum(bar["trade_date"] > stable_strokes[-1]["end_date"] for bar in ordered)
                       if stable_strokes else None)
    if not issues and last_stroke_age is not None and last_stroke_age > 20:
        issues.append("stale_structure")
        signal = _signal("wait_for_structure", "等待新结构", "观察",
                         "最近稳定笔距今超过20根日线，旧候选不再作为当前触发依据。", confidence="low")
    signal["status"] = "candidate" if signal["type"].startswith("suspected_third_") else "observation"
    center = centers[-1] if centers else None
    structure = _structure_label(strokes=stable_strokes, centers=centers, current_price=current_price)

    return {
        "symbol": normalized_symbol,
        "name": name,
        "period": period,
        "model_version": MODEL_VERSION,
        "as_of": latest_date,
        "price_origin": "kline_close",
        "data_quality": {
            "status": "missing" if not ordered else "partial" if issues else "complete",
            "issues": sorted(set(issues)), "input_bar_count": len(bars),
            "excluded_bar_count": len(bars) - len(ordered), "age_days": age_days,
        },
        "bar_count": len(ordered),
        "merged_bar_count": len(merged),
        "fractal_count": len(fractals),
        "stroke_count": len(strokes),
        "confirmed_stroke_count": len(stable_strokes),
        "last_stable_stroke_age_bars": last_stroke_age,
        "center_count": len(centers),
        "current_price": current_price,
        "structure": structure,
        "structure_key": {
            "结构未成型": "unformed", "趋势段观察": "no_center", "中枢已形成": "center_formed",
            "远离中枢上方": "extended_above", "中枢上方": "above",
            "远离中枢下方": "extended_below", "中枢下方": "below", "中枢震荡": "inside",
        }[structure],
        "signal": signal,
        "latest_center": center,
        "center_age_bars": sum(bar["trade_date"] > center["end_date"] for bar in ordered) if center else None,
        "center_distance_pct": (
            round((current_price / (center["upper"] if current_price > center["upper"] else center["lower"]) - 1) * 100, 2)
            if center and current_price and not center["lower"] <= current_price <= center["upper"]
            else 0.0 if center else None
        ),
        "latest_strokes": strokes[-5:],
        "latest_fractals": fractals[-6:],
        "chart": {"bars": [{key: bar[key] for key in ("trade_date", "open", "high", "low", "close")}
                           for bar in ordered[-160:]], "strokes": strokes, "centers": centers},
    }


def generate_stock_pool_chan_analysis(
    *,
    pool: dict[str, Any],
    watchlist: list[dict[str, Any]],
    kline_by_symbol: dict[str, list[dict[str, Any]]],
    source: str,
    period: str = "daily",
    failed_symbols: list[str] | None = None,
    fetch_issues: dict[str, str] | None = None,
    max_symbols: int = 30,
) -> dict[str, Any]:
    max_symbols = max(1, min(int(max_symbols), 100))
    ordered_symbols = _watchlist_symbol_order(watchlist)[:max_symbols]
    watchlist_by_symbol = {
        normalize_symbol(str(item["symbol"])): item for item in watchlist
    }
    items: list[dict[str, Any]] = []
    generated_at = utc_now()

    for symbol in ordered_symbols:
        bars = kline_by_symbol.get(symbol) or []
        item = watchlist_by_symbol.get(symbol)
        items.append(analyze_chan_structure(
            symbol=symbol, name=item.get("name") if item else None,
            bars=bars, period=period, as_of=generated_at,
        ))
        if symbol in (fetch_issues or {}):
            items[-1]["data_quality"]["issues"].append(fetch_issues[symbol])

    signal_counts: dict[str, int] = {}
    for item in items:
        signal_type = str(item.get("signal", {}).get("type") or "unknown")
        signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1

    failed_symbols = [normalize_symbol(symbol) for symbol in (failed_symbols or [])]
    pool_name = pool.get("name") or f"Pool {pool.get('id')}"
    return {
        "report_type": "stock_pool_chan_analysis",
        "symbol": None,
        "generated_at": generated_at,
        "model_version": MODEL_VERSION,
        "limitations": ["pen_overlap_proxy", "no_sublevel_confirmation", "adjustment_unverified",
                        "calendar_age_not_exchange_calendar"],
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
            "kline_tool": "PBFXT" if source == "tdx-official" else source,
        },
        "data_quality": {
            "failed_symbol_count": len(failed_symbols),
            "failed_symbols": failed_symbols,
            "fetch_issues": fetch_issues or {},
            "complete_count": sum(item["data_quality"]["status"] == "complete" for item in items),
            "review_count": sum(item["data_quality"]["status"] != "complete" for item in items),
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
            for key in ("high", "low"):
                if (bar[key] >= last[key] if direction >= 0 else bar[key] <= last[key]):
                    last[key] = bar[key]
                    last[f"{key}_date"] = bar[f"{key}_date"]
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
        if (current["high"] > max(previous["high"], following["high"])
                and current["low"] > max(previous["low"], following["low"])):
            fractals.append({**_fractal("top", index, current, current["high"]),
                             "confirmed_at": following["end_date"]})
        if (current["low"] < min(previous["low"], following["low"])
                and current["high"] < min(previous["high"], following["high"])):
            fractals.append({**_fractal("bottom", index, current, current["low"]),
                             "confirmed_at": following["end_date"]})
    return fractals


def _build_strokes(
    fractals: list[dict[str, Any]], min_distance: int = 4, *, bars: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
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
        price_ordered = (fractal["price"] > last["price"] if fractal["type"] == "top"
                         else fractal["price"] < last["price"])
        if fractal["index"] - last["index"] >= min_distance and price_ordered:
            pivots.append(fractal)

    strokes: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(zip(pivots, pivots[1:])):
        direction = "up" if start["type"] == "bottom" and end["type"] == "top" else "down"
        interval = [bar for bar in (bars or []) if start["date"] <= bar["trade_date"] <= end["date"]]
        strokes.append(
            {
                "direction": direction,
                "start_date": start["date"],
                "end_date": end["date"],
                "start_price": start["price"],
                "end_price": end["price"],
                "high": max([start["price"], end["price"]] + [bar["high"] for bar in interval]),
                "low": min([start["price"], end["price"]] + [bar["low"] for bar in interval]),
                "bar_span": end["index"] - start["index"],
                # A following opposite pivot locks this endpoint in the current snapshot.
                "confirmed": index < len(pivots) - 2,
                "confirmed_at": pivots[index + 2].get("confirmed_at") if index < len(pivots) - 2 else None,
            }
        )
    return strokes


def _detect_centers(strokes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    centers: list[dict[str, Any]] = []
    for index in range(0, max(0, len(strokes) - 2)):
        group = strokes[index : index + 3]
        lower = max(stroke["low"] for stroke in group)
        upper = min(stroke["high"] for stroke in group)
        if lower < upper:
            center = {
                "start_date": group[0]["start_date"],
                "end_date": group[-1]["end_date"],
                "lower": round(lower, 4),
                "upper": round(upper, 4),
                "stroke_start": index,
                "stroke_end": index + 2,
            }
            if (centers and center["stroke_start"] <= centers[-1]["stroke_end"]
                    and _center_overlaps(centers[-1], center)):
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
        if _is_extended_from_center(current_price=current_price, boundary=upper, lower=lower, upper=upper):
            return _signal(
                "extended_above_center",
                "远离中枢上方",
                "观察，等待新结构",
                (
                    f"当前价 {current_price:.3f} 已明显远离最近中枢上沿 {upper:.3f}，"
                    "旧中枢只能说明历史离开，不能再当作近端三买触发位。"
                ),
                trigger=(
                    f"等待当前价附近形成新中枢，或回踩不破最近一笔低点 "
                    f"{latest_stroke['low']:.3f} 后再转强。"
                ),
                invalidation=f"跌破最近一笔低点 {latest_stroke['low']:.3f} 后重新评估强弱。",
            )
        if (latest_stroke["direction"] == "down" and latest_stroke["low"] > upper
                and len(strokes) - 1 > latest_center["stroke_end"]
                and strokes[-2]["direction"] == "up" and strokes[-2]["end_price"] > upper):
            return _signal(
                "suspected_third_buy",
                "疑似三买观察",
                "等待回踩确认",
                "中枢形成后向上离开，随后稳定回落笔低点仍高于上沿。仅为笔级候选，未确认次级别走势。",
                trigger=f"后续回踩继续守住 {upper:.3f}，并确认次级别向上结构。",
                invalidation=f"跌回中枢上沿 {upper:.3f} 下方。",
            )
        return _signal(
            "upward_leave",
            "向上离开中枢",
            "观察回踩结构",
            "价格在中枢上方运行，但尚未完成回踩确认。",
            trigger=f"回踩确认不跌回 {upper:.3f}。",
            invalidation=f"重新跌回 {upper:.3f} 下方。",
        )
    if current_price < lower:
        if _is_extended_from_center(current_price=current_price, boundary=lower, lower=lower, upper=upper):
            return _signal(
                "extended_below_center",
                "远离中枢下方",
                "观察，等待新结构",
                (
                    f"当前价 {current_price:.3f} 已明显远离最近中枢下沿 {lower:.3f}，"
                    "旧中枢只能说明历史离开，不能再当作近端三卖触发位。"
                ),
                trigger=(
                    f"等待当前价附近形成新中枢，或反抽不过最近一笔高点 "
                    f"{latest_stroke['high']:.3f} 后再转弱。"
                ),
                invalidation=f"突破最近一笔高点 {latest_stroke['high']:.3f} 后重新评估强弱。",
            )
        if (latest_stroke["direction"] == "up" and latest_stroke["high"] < lower
                and len(strokes) - 1 > latest_center["stroke_end"]
                and strokes[-2]["direction"] == "down" and strokes[-2]["end_price"] < lower):
            return _signal(
                "suspected_third_sell",
                "疑似三卖观察",
                "复核下行风险",
                "中枢形成后向下离开，随后稳定反弹笔高点仍低于下沿。仅为笔级候选，未确认次级别走势。",
                trigger=f"后续反弹仍不能收回 {lower:.3f}，并确认次级别向下结构。",
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
        if _is_extended_from_center(
            current_price=current_price,
            boundary=float(center["upper"]),
            lower=float(center["lower"]),
            upper=float(center["upper"]),
        ):
            return "远离中枢上方"
        return "中枢上方"
    if current_price < center["lower"]:
        if _is_extended_from_center(
            current_price=current_price,
            boundary=float(center["lower"]),
            lower=float(center["lower"]),
            upper=float(center["upper"]),
        ):
            return "远离中枢下方"
        return "中枢下方"
    return "中枢震荡"


def _is_extended_from_center(
    *,
    current_price: float,
    boundary: float,
    lower: float,
    upper: float,
) -> bool:
    center_width = max(upper - lower, abs(boundary) * 0.02, 0.01)
    extension = abs(current_price - boundary)
    limit = max(center_width * 2, abs(boundary) * 0.12)
    return extension > limit


def _bar(raw: dict[str, Any]) -> dict[str, Any]:
    trade_date = str(raw["trade_date"])
    return {
        "trade_date": trade_date,
        "end_date": trade_date,
        "high_date": trade_date,
        "low_date": trade_date,
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
        "date": bar["high_date" if kind == "top" else "low_date"],
        "price": round(price, 4),
        "high": round(bar["high"], 4),
        "low": round(bar["low"], 4),
    }


def _is_more_extreme(candidate: dict[str, Any], current: dict[str, Any]) -> bool:
    if candidate["type"] == "top":
        return candidate["price"] >= current["price"]
    return candidate["price"] <= current["price"]


def _center_overlaps(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return max(left["lower"], right["lower"]) < min(left["upper"], right["upper"])


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
