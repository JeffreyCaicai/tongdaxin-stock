"""Asset-only ranking with explicit quality gates and auditable non-selections."""
from __future__ import annotations

import math
from .decision_engine import generate_stock_pool_decision_engine
from .repository import normalize_symbol, utc_now
from .opportunity_discovery import canonical_stock
from .opportunity_horizons import MODEL as HORIZON_MODEL, assess_horizons
from .opportunity_prices import completed_daily_bars
from .market_regime import infer_market_regime

MODEL = "market_opportunities_v2"


def merge_candidates(discovered: list[dict], watchlist: list[dict], holdings: list[dict], limit: int) -> list[dict]:
    items = {}
    for item in watchlist:
        symbol = canonical_stock(item["symbol"]) or normalize_symbol(item["symbol"])
        items[symbol] = {"symbol": symbol, "name": item.get("name"), "origin": "watched", "themes": []}
    for item in holdings:
        symbol = canonical_stock(item["symbol"]) or normalize_symbol(item["symbol"])
        if float(item.get("quantity") or 0) > 0:
            items[symbol] = {"symbol": symbol, "name": item.get("name"), "origin": "held", "themes": []}
    added = 0
    for item in discovered:
        symbol = canonical_stock(item["symbol"])
        if symbol is None:
            continue
        if symbol in items:
            items[symbol]["themes"] = item.get("themes", [])
        elif added < limit:
            items[symbol] = {**item, "symbol": symbol, "origin": "new"}
            added += 1
    return list(items.values())


def number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def classify(item: dict, quote: dict, bars: list[dict]) -> dict:
    quality = item["data_quality"]
    reasons = list(quality["issues"])
    if canonical_stock(item["symbol"]) is None:
        reasons.append("outside_stock_scope")
    if quality["bar_count"] < 120:
        reasons.append("history_under_120")
    name = (item.get("name") or "").upper()
    if not name:
        reasons.append("missing_name")
    if "ST" in name or "退" in name:
        reasons.append("special_treatment")
    amount = number(quote.get("amount"))
    volume = number(quote.get("volume"))
    if amount is None or amount < 20_000_000:
        reasons.append("low_or_unknown_liquidity")
    if volume is None or volume <= 0:
        reasons.append("inactive_or_unknown")
    price = number(item.get("current_price"))
    last_close = number(bars[-1].get("close")) if bars else None
    if price and last_close and abs(price / last_close - 1) > 0.25:
        reasons.append("price_basis_mismatch")
    p = item["probabilities"]
    decision = item["decision"]
    factors = item["factor_profile"]
    rs = factors["relative_strength"]
    strong = any((number(rs.get(key)) or 0) > 0 for key in ("vs_index_20_pct", "vs_index_60_pct"))
    stretch = number(factors["mean_reversion"].get("ma20_deviation_pct"))
    rsi = number(item["indicator"].get("rsi14"))
    overheated = (stretch is not None and stretch > 15) or (rsi is not None and rsi > 80)
    level = "excluded" if reasons else "not_selected"
    if not reasons:
        if decision["risk_level"] == "high":
            reasons.append("high_risk")
        elif not strong:
            reasons.append("no_index_outperformance")
        elif p["up"] >= 0.50 and p["down"] < 0.30 and not overheated:
            level = "priority"
        elif p["up"] >= 0.42 and p["up"] > p["down"]:
            level = "wait"
            if overheated:
                reasons.append("extended_price")
        else:
            reasons.append("weak_evidence")
    ma20 = number(item["indicator"].get("ma", {}).get("ma20"))
    atr = number(item["indicator"].get("atr14"))
    negative = [e for e in item["evidence"] if e["contribution"].get("down", 0) > e["contribution"].get("up", 0)]
    positive = [e for e in item["evidence"] if e["contribution"].get("up", 0) > e["contribution"].get("down", 0)]
    return {**item, "level": level, "selection_reasons": sorted(set(reasons)),
            "rank_score": round(50 + 50 * (p["up"] - p["down"]), 2),
            "supporting_evidence": positive, "opposing_evidence": negative,
            "conditions": {"ma20": ma20, "atr14": atr,
                           "review_below": round(ma20 - atr, 3) if ma20 and atr else None,
                           "extended": overheated},
            "amount": amount}


def build_opportunity_report(*, candidates: list[dict], quotes: dict, klines: dict,
                             index_bars: list[dict], source: str, discovery: dict,
                             failures: list[dict], pool: dict) -> dict:
    items, regime = [], {}
    generated_at = utc_now()
    closed_index, index_issues = completed_daily_bars(index_bars, generated_at)
    period_regime = infer_market_regime(index_bars=closed_index if not index_issues else [])
    for start in range(0, len(candidates), 100):
        batch = candidates[start:start + 100]
        # The asset-only path excludes selected-sample breadth and holding P/L.
        report = generate_stock_pool_decision_engine(
            pool=pool, watchlist=batch, holdings=[], quotes=quotes, kline_by_symbol=klines,
            index_bars=index_bars, market_index_symbol="SH000300", source=source,
            max_symbols=100, asset_only=True,
        )
        regime = report["market_regime"]
        metadata = {row["symbol"]: row for row in batch}
        for item in report["items"]:
            result = classify(item, quotes.get(item["symbol"], {}), klines.get(item["symbol"], []))
            result.update(origin=metadata[item["symbol"]]["origin"], themes=metadata[item["symbol"]].get("themes", []))
            result["period_assessments"] = assess_horizons(
                bars=klines.get(item["symbol"], []), index_bars=index_bars, as_of=generated_at,
                regime=period_regime["regime"], blocked=result["level"] == "excluded",
            )
            items.append(result)
    items.sort(key=lambda x: ({"priority": 0, "wait": 1, "not_selected": 2, "excluded": 3}[x["level"]], -x["rank_score"], x["symbol"]))
    selected = [row["symbol"] for row in items if row["level"] in {"priority", "wait"}][:10]
    return {"report_type": "market_opportunities", "model_version": MODEL,
            "generated_at": generated_at, "source": source, "pool": pool,
            "period_assessment_model": HORIZON_MODEL, "period_market_regime": period_regime,
            "horizon_sessions": 20, "period": "daily", "benchmark": "SH000300",
            "calibration": "uncalibrated", "market_regime": regime,
            "discovery": discovery, "failures": failures, "items": items, "selected": selected,
            "scope": {"analyzed": len(items), "new": sum(x["origin"] == "new" for x in items),
                      "personal": sum(x["origin"] != "new" for x in items), "recommended": len(selected),
                      "excluded": sum(x["level"] == "excluded" for x in items)},
            "limitations": ["technical_only", "no_industry_or_style", "uncalibrated", "screened_subset"],
            "price_basis": {"tdx_kline_TQFlag": 11, "quote": "latest", "kline_limit": 240}}
