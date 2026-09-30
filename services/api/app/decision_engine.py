from __future__ import annotations

import math
from datetime import date
from typing import Any

from .chan_analysis import analyze_chan_structure
from .indicators import calculate_indicator_snapshot
from .market_regime import infer_market_regime
from .repository import normalize_symbol, utc_now


SCENARIOS = ("up", "range", "down")
SOFTMAX_TEMPERATURE = 1.35
MODEL_VERSION = "rule_based_scenario_v1"
STALE_AFTER_CALENDAR_DAYS = 7
MAX_ENDPOINT_LAG_SESSIONS = 3


def generate_stock_pool_decision_engine(
    *,
    pool: dict[str, Any],
    watchlist: list[dict[str, Any]],
    holdings: list[dict[str, Any]],
    quotes: dict[str, dict[str, Any]],
    kline_by_symbol: dict[str, list[dict[str, Any]]],
    source: str,
    period: str = "daily",
    horizon_days: int = 20,
    index_bars: list[dict[str, Any]] | None = None,
    market_index_symbol: str | None = None,
    market_regime: dict[str, Any] | None = None,
    failed_quote_symbols: list[str] | None = None,
    failed_kline_symbols: list[str] | None = None,
    failed_market_index_symbol: str | None = None,
    max_symbols: int = 30,
    asset_only: bool = False,
) -> dict[str, Any]:
    if period != "daily":
        raise ValueError("This v1 model supports only daily bars.")
    if type(horizon_days) is not int or horizon_days != 20:
        raise ValueError("This v1 model supports only a 20-trading-session horizon.")
    max_symbols = max(1, min(int(max_symbols), 100))
    generated_at = utc_now()
    ordered_symbols = _symbol_order(watchlist=watchlist, holdings=holdings)[:max_symbols]
    holdings_by_symbol = {} if asset_only else {
        normalize_symbol(str(holding["symbol"])): holding for holding in holdings
    }
    watchlist_by_symbol = {
        normalize_symbol(str(item["symbol"])): item for item in watchlist
    }
    shared = _shared_inputs(
        quotes=quotes, kline_by_symbol=kline_by_symbol,
        index_bars=index_bars or [], generated_at=generated_at,
    )
    pool_context = _pool_context(shared["quotes"])
    factor_context = _factor_context(
        index_bars=index_bars or [], kline_by_symbol=kline_by_symbol, generated_at=generated_at,
        calendar_index_bars=(index_bars or []) if shared["index"] else [],
        calendar_kline_by_symbol=shared["klines"],
    )
    if asset_only:
        # Screened candidates are a selected sample, not market breadth or peers.
        pool_context = {}
        factor_context["pool"] = {"sample_size": 0, "sample_size20": 0, "sample_size60": 0}
        market_regime = infer_market_regime(
            index_bars=shared["index"], pool_quotes={}, pool_kline_by_symbol={},
        )
    quality = shared["data_quality"]
    supplied_quality = (market_regime or {}).get("data_quality") or {}
    supplied_degraded = (
        supplied_quality.get("degraded", False)
        or supplied_quality.get("status") in {"stale", "insufficient"}
    )
    if supplied_degraded:
        quality = {
            **quality,
            "status": "partial" if quality["status"] == "complete" else quality["status"],
            "degraded": True,
            "issues": [*quality["issues"], "excluded_supplied_regime"],
        }
    if (
        market_regime is None or quality["excluded_quote_symbols"]
        or quality["excluded_kline_symbols"] or "stale_index" in quality["issues"]
        or "invalid_index_bars" in quality["issues"] or supplied_degraded
        or not (shared["quotes"] or shared["klines"] or shared["index"])
    ):
        market_regime = infer_market_regime(
            index_bars=shared["index"], pool_quotes={} if asset_only else shared["quotes"],
            pool_kline_by_symbol={} if asset_only else shared["klines"],
        )
    market_regime = {
        **market_regime,
        "confidence": _cap_confidence(
            market_regime.get("confidence", "low"),
            "low" if quality["status"] in {"stale", "insufficient"}
            else "medium" if quality["degraded"] else "high",
        ),
        "data_quality": quality,
    }

    items = [
        _decision_item(
            symbol=symbol,
            watchlist_item=watchlist_by_symbol.get(symbol),
            holding=holdings_by_symbol.get(symbol),
            quote=quotes.get(symbol),
            bars=kline_by_symbol.get(symbol) or [],
            pool_context=pool_context,
            factor_context=factor_context,
            market_regime=market_regime,
            period=period,
            horizon_days=horizon_days,
            generated_at=generated_at,
        )
        for symbol in ordered_symbols
    ]

    failed_quote_symbols = [normalize_symbol(symbol) for symbol in (failed_quote_symbols or [])]
    failed_kline_symbols = [normalize_symbol(symbol) for symbol in (failed_kline_symbols or [])]
    pool_name = pool.get("name") or f"Pool {pool.get('id')}"
    return {
        "report_type": "stock_pool_decision_engine",
        "symbol": None,
        "model_version": MODEL_VERSION,
        "asset_only": asset_only,
        "period": period,
        "generated_at": generated_at,
        "calibration": {
            "status": "uncalibrated",
            "score_type": "rule_based_scenario_scores",
            "is_calibrated_probability": False,
            "method": "evidence_weighted_softmax",
            "temperature": SOFTMAX_TEMPERATURE,
        },
        "provenance": {
            "source": source,
            "period": period,
            "generated_at": generated_at,
            "as_of": factor_context["as_of"],
            "calendar_source": factor_context["calendar_source"],
            "market_index_symbol": market_index_symbol,
            "windows": factor_context["windows"],
            "stale_after_calendar_days": STALE_AFTER_CALENDAR_DAYS,
            "max_endpoint_lag_sessions": MAX_ENDPOINT_LAG_SESSIONS,
        },
        "summary": (
            f"已用 {source} 的行情与 {period} K线完成“{pool_name}”持仓决策引擎分析："
            f"{len(items)} 只股票，目标周期 {horizon_days} 个交易日；情景分数未经校准。"
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
            "horizon_days": horizon_days,
            "horizon_sessions": horizon_days,
            "market_index_symbol": market_index_symbol,
        },
        "tool_plan": {
            "data_source": source,
            "quote_tool": "quote",
            "kline_tool": "daily_kline",
            "model": MODEL_VERSION,
            "market_regime_model": market_regime.get("model", "rule_state_machine_v1"),
        },
        "market_regime": market_regime,
        "data_quality": {
            "failed_quote_count": len(failed_quote_symbols),
            "failed_quote_symbols": failed_quote_symbols,
            "failed_kline_count": len(failed_kline_symbols),
            "failed_kline_symbols": failed_kline_symbols,
            "failed_market_index_symbol": failed_market_index_symbol,
            "unavailable_evidence": [
                "行业状态",
                "行业归因",
                "市值/成长价值风格归因",
                "基本面变化",
                "事件催化",
                "历史相似样本库",
            ],
        },
        "scenario_counts": _scenario_counts(items),
        "items": items,
        "next_steps": _next_steps(items, failed_quote_symbols, failed_kline_symbols),
    }


def _decision_item(
    *,
    symbol: str,
    watchlist_item: dict[str, Any] | None,
    holding: dict[str, Any] | None,
    quote: dict[str, Any] | None,
    bars: list[dict[str, Any]],
    pool_context: dict[str, Any],
    factor_context: dict[str, Any],
    market_regime: dict[str, Any],
    period: str,
    horizon_days: int,
    generated_at: str,
) -> dict[str, Any]:
    name = (
        (quote or {}).get("name")
        or (watchlist_item or {}).get("name")
        or (holding or {}).get("name")
    )
    raw_bars = bars
    bars = _clean_bars(bars)
    data_quality = _item_data_quality(
        symbol=symbol, quote=quote, raw_bars=raw_bars, bars=bars,
        factor_context=factor_context, generated_at=generated_at,
    )
    # Retain raw quality/provenance, but do not score a stale individual series.
    if any(issue in data_quality["issues"] for issue in ("stale_kline", "stale_factor_window")):
        bars = []
    scoring_quote = _fresh_quote(quote, generated_at)
    current_price = _current_price(scoring_quote, bars)
    price_origin = (
        "quote" if scoring_quote is not None
        else "latest_close" if current_price is not None else None
    )
    indicator = calculate_indicator_snapshot(bars) if bars else {"bars": 0}
    if len(bars) < 20 or any(bar["volume"] is None for bar in bars[-20:]):
        indicator["volume_ratio"] = None
    chan = (
        analyze_chan_structure(symbol=symbol, name=name, bars=bars, period=period)
        if bars
        else None
    )
    position = _position_context(holding, current_price)
    factor_profile = _factor_profile(
        symbol=symbol,
        bars=bars,
        indicator=indicator,
        current_price=current_price,
        factor_context=factor_context,
    )

    prior = _prior_scores(
        pool_context=pool_context,
        indicator=indicator,
        current_price=current_price,
        market_regime=market_regime,
    )
    evidence = _evidence_entries(
        quote=scoring_quote,
        bars=bars,
        indicator=indicator,
        chan=chan,
        position=position,
        pool_context=pool_context,
        factor_profile=factor_profile,
        current_price=current_price,
    )
    _apply_regime_weights(evidence, market_regime)
    z_scores = prior["scores"].copy()
    for entry in evidence:
        for scenario in SCENARIOS:
            z_scores[scenario] += float(entry["contribution"].get(scenario, 0))
    probabilities = _softmax(z_scores)
    decision = _decision(probabilities=probabilities, position=position, evidence=evidence)
    if data_quality["status"] == "stale":
        decision.update(
            key="wait_confirm", label="等待确认",
            next_check="补齐新鲜行情和K线后重新评估。",
        )
    if not evidence:
        data_quality["issues"].append("no_evidence")
        if data_quality["status"] != "stale":
            data_quality["status"] = "insufficient"
    ceiling = (
        "low" if data_quality["status"] in {"insufficient", "stale"}
        else "medium" if data_quality["issues"] else "high"
    )
    decision["confidence"] = _cap_confidence(decision["confidence"], ceiling)
    for entry in evidence:
        entry["confidence"] = _cap_confidence(entry["confidence"], ceiling)
    top_evidence = _top_evidence(evidence)

    return {
        "symbol": symbol,
        "name": name,
        "horizon_days": horizon_days,
        "horizon_sessions": horizon_days,
        "current_price": current_price,
        "price_origin": price_origin,
        "data_quality": data_quality,
        "position": position,
        "indicator": {
            "trend": indicator.get("trend"),
            "ma": indicator.get("ma", {}),
            "volume_ratio": indicator.get("volume_ratio"),
            "rsi14": indicator.get("rsi14"),
            "atr14": indicator.get("atr14"),
            "recent_high_20": indicator.get("recent_high_20"),
            "recent_low_20": indicator.get("recent_low_20"),
        },
        "factor_profile": factor_profile,
        "chan": {
            "structure": chan.get("structure") if chan else None,
            "signal_type": chan.get("signal", {}).get("type") if chan else None,
            "signal_label": chan.get("signal", {}).get("label") if chan else None,
            "reason": chan.get("signal", {}).get("reason") if chan else None,
        },
        "prior": prior,
        "evidence": evidence,
        "z_scores": {key: round(value, 4) for key, value in z_scores.items()},
        "probabilities": probabilities,
        "decision": decision,
        "top_evidence": top_evidence,
        "evidence_summary": "；".join(top_evidence) if top_evidence else "证据不足",
    }


def _prior_scores(
    *,
    pool_context: dict[str, Any],
    indicator: dict[str, Any],
    current_price: float | None,
    market_regime: dict[str, Any] | None,
) -> dict[str, Any]:
    scores = {scenario: 0.0 for scenario in SCENARIOS}
    components: list[dict[str, Any]] = []

    positive_ratio = pool_context.get("positive_ratio")
    average_pct_change = pool_context.get("average_pct_change")
    if positive_ratio is not None:
        if positive_ratio >= 0.6:
            _apply_component(
                scores,
                components,
                "股票池短线广度",
                f"上涨股票占比 {positive_ratio:.0%}",
                {"up": 0.18, "range": 0.03, "down": -0.08},
            )
        elif positive_ratio <= 0.4:
            _apply_component(
                scores,
                components,
                "股票池短线广度",
                f"上涨股票占比 {positive_ratio:.0%}",
                {"up": -0.08, "range": 0.03, "down": 0.18},
            )
    if average_pct_change is not None:
        if average_pct_change >= 1:
            _apply_component(
                scores,
                components,
                "股票池平均涨跌",
                f"平均涨跌幅 {average_pct_change:.2f}%",
                {"up": 0.12, "range": 0, "down": -0.06},
            )
        elif average_pct_change <= -1:
            _apply_component(
                scores,
                components,
                "股票池平均涨跌",
                f"平均涨跌幅 {average_pct_change:.2f}%",
                {"up": -0.06, "range": 0, "down": 0.12},
            )

    regime = (market_regime or {}).get("regime")
    if regime:
        component = _market_regime_prior(regime)
        if component:
            _apply_component(
                scores,
                components,
                "市场状态",
                f"{(market_regime or {}).get('label') or regime} / {(market_regime or {}).get('confidence') or 'low'}",
                component,
            )

    atr_pct = _atr_pct(indicator, current_price)
    if atr_pct is not None:
        if atr_pct >= 5:
            _apply_component(
                scores,
                components,
                "波动率区间",
                f"ATR14/价格 {atr_pct:.2f}%",
                {"up": -0.05, "range": 0.14, "down": 0.12},
            )
        elif atr_pct <= 1.5:
            _apply_component(
                scores,
                components,
                "波动率区间",
                f"ATR14/价格 {atr_pct:.2f}%",
                {"up": 0.03, "range": 0.12, "down": -0.04},
            )

    return {"scores": scores, "components": components}


def _evidence_entries(
    *,
    quote: dict[str, Any] | None,
    bars: list[dict[str, Any]],
    indicator: dict[str, Any],
    chan: dict[str, Any] | None,
    position: dict[str, Any] | None,
    pool_context: dict[str, Any],
    factor_profile: dict[str, Any],
    current_price: float | None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not bars and quote is None and current_price is None:
        return entries
    _ma_evidence(entries, indicator, current_price)
    _volume_evidence(entries, indicator, bars)
    _momentum_factor_evidence(entries, factor_profile)
    _relative_strength_evidence(entries, quote, pool_context)
    _relative_strength_factor_evidence(entries, factor_profile)
    _factor_attribution_evidence(entries, factor_profile)
    _mean_reversion_factor_evidence(entries, factor_profile)
    _chan_evidence(entries, chan)
    _position_evidence(entries, position)
    _price_location_evidence(entries, indicator, current_price)
    return entries


def _ma_evidence(entries: list[dict[str, Any]], indicator: dict[str, Any], current_price: float | None) -> None:
    trend = indicator.get("trend")
    ma = indicator.get("ma", {})
    ma20 = _to_float(ma.get("ma20"))
    if trend == "bullish":
        _add_evidence(entries, "MA趋势", "MA5 位于 MA20 上方，趋势偏多", up=0.5, range=-0.05, down=-0.18, category="trend")
    elif trend == "bearish":
        _add_evidence(entries, "MA趋势", "MA5 位于 MA20 下方，趋势偏弱", up=-0.18, range=-0.05, down=0.5, category="trend")
    elif trend == "neutral":
        _add_evidence(entries, "MA趋势", "均线结构中性", up=0.02, range=0.22, down=0.02, category="mean_reversion")
    if current_price is not None and ma20:
        if current_price >= ma20:
            _add_evidence(entries, "趋势位置", f"现价位于 MA20 上方 {((current_price / ma20) - 1) * 100:.2f}%", up=0.2, range=0.02, down=-0.08, category="trend")
        else:
            _add_evidence(entries, "趋势位置", f"现价位于 MA20 下方 {((current_price / ma20) - 1) * 100:.2f}%", up=-0.08, range=0.02, down=0.2, category="risk")


def _volume_evidence(entries: list[dict[str, Any]], indicator: dict[str, Any], bars: list[dict[str, Any]]) -> None:
    volume_ratio = _to_float(indicator.get("volume_ratio"))
    recent_return = _return_pct(bars, 5)
    if volume_ratio is None:
        return
    if volume_ratio >= 1.5 and (recent_return or 0) >= 0:
        _add_evidence(entries, "成交量", f"成交量比 {volume_ratio:.2f}，放量配合上涨", up=0.26, range=-0.04, down=0.02, category="breakout")
    elif volume_ratio >= 1.5:
        _add_evidence(entries, "成交量", f"成交量比 {volume_ratio:.2f}，放量但价格未走强", up=-0.02, range=0.08, down=0.2, category="risk")
    elif volume_ratio <= 0.7:
        _add_evidence(entries, "成交量", f"成交量比 {volume_ratio:.2f}，缩量等待方向", up=-0.04, range=0.22, down=0.03, category="mean_reversion")


def _momentum_factor_evidence(entries: list[dict[str, Any]], factor_profile: dict[str, Any]) -> None:
    momentum = factor_profile.get("momentum") or {}
    return20 = _to_float(momentum.get("return20_pct"))
    return60 = _to_float(momentum.get("return60_pct"))
    if return20 is None or return60 is None:
        return
    if return20 >= 8 and return60 >= 15:
        _add_evidence(
            entries,
            "中期动量",
            f"20日收益 {return20:.2f}%，60日收益 {return60:.2f}%，收益延续较强",
            up=0.3,
            range=-0.04,
            down=-0.1,
            category="trend",
        )
    elif return20 >= 4 and return60 >= 8:
        _add_evidence(
            entries,
            "中期动量",
            f"20日收益 {return20:.2f}%，60日收益 {return60:.2f}%，中期动量偏强",
            up=0.18,
            range=0.02,
            down=-0.06,
            category="trend",
        )
    elif return20 <= -8 and return60 <= -12:
        _add_evidence(
            entries,
            "中期动量",
            f"20日收益 {return20:.2f}%，60日收益 {return60:.2f}%，弱势延续",
            up=-0.1,
            range=-0.02,
            down=0.3,
            category="risk",
        )
    elif abs(return20) <= 2 and abs(return60) <= 4:
        _add_evidence(
            entries,
            "中期动量",
            f"20日收益 {return20:.2f}%，60日收益 {return60:.2f}%，方向不明显",
            up=0.01,
            range=0.14,
            down=0.01,
            category="mean_reversion",
        )


def _relative_strength_evidence(
    entries: list[dict[str, Any]],
    quote: dict[str, Any] | None,
    pool_context: dict[str, Any],
) -> None:
    pct_change = _to_float((quote or {}).get("pct_change"))
    average_pct_change = pool_context.get("average_pct_change")
    if pct_change is None or average_pct_change is None:
        return
    relative = pct_change - average_pct_change
    if relative >= 1:
        _add_evidence(entries, "相对强弱", f"涨跌幅强于股票池均值 {relative:.2f} 个百分点", up=0.25, range=0.02, down=-0.08, category="trend")
    elif relative <= -1:
        _add_evidence(entries, "相对强弱", f"涨跌幅弱于股票池均值 {abs(relative):.2f} 个百分点", up=-0.08, range=0.02, down=0.25, category="risk")
    else:
        _add_evidence(entries, "相对强弱", "与股票池均值接近", up=0.02, range=0.1, down=0.02, category="mean_reversion")


def _relative_strength_factor_evidence(entries: list[dict[str, Any]], factor_profile: dict[str, Any]) -> None:
    momentum = factor_profile.get("momentum") or {}
    relative = factor_profile.get("relative_strength") or {}
    return20 = _to_float(momentum.get("return20_pct"))
    vs_index_20 = _to_float(relative.get("vs_index_20_pct"))
    vs_index_60 = _to_float(relative.get("vs_index_60_pct"))
    vs_pool_20 = _to_float(relative.get("vs_pool_20_pct"))
    vs_pool_60 = _to_float(relative.get("vs_pool_60_pct"))

    if vs_index_20 is not None or vs_index_60 is not None:
        if (vs_index_20 or 0) >= 5 or (vs_index_60 or 0) >= 8:
            _add_evidence(
                entries,
                "指数相对强弱",
                f"20日相对指数 {vs_index_20 or 0:.2f}%，60日相对指数 {vs_index_60 or 0:.2f}%",
                up=0.24,
                range=0.02,
                down=-0.08,
                category="trend",
            )
        elif (return20 or 0) > 0 and (vs_index_20 or 0) <= -5:
            _add_evidence(
                entries,
                "指数相对强弱",
                f"20日仍上涨 {return20:.2f}%，但弱于指数 {abs(vs_index_20 or 0):.2f}%",
                up=-0.06,
                range=0.08,
                down=0.16,
                category="risk",
            )
        elif (vs_index_20 or 0) <= -5 or (vs_index_60 or 0) <= -8:
            _add_evidence(
                entries,
                "指数相对强弱",
                f"20日相对指数 {vs_index_20 or 0:.2f}%，60日相对指数 {vs_index_60 or 0:.2f}%",
                up=-0.08,
                range=0.02,
                down=0.22,
                category="risk",
            )

    if vs_pool_20 is not None or vs_pool_60 is not None:
        if (vs_pool_20 or 0) >= 3 or (vs_pool_60 or 0) >= 6:
            _add_evidence(
                entries,
                "股票池相对强弱",
                f"20日强于股票池均值 {vs_pool_20 or 0:.2f}%，60日强于均值 {vs_pool_60 or 0:.2f}%",
                up=0.18,
                range=0.02,
                down=-0.06,
                category="trend",
            )
        elif (return20 or 0) > 0 and (vs_pool_20 or 0) <= -3:
            _add_evidence(
                entries,
                "股票池相对强弱",
                f"20日仍上涨 {return20:.2f}%，但弱于股票池均值 {abs(vs_pool_20 or 0):.2f}%",
                up=-0.04,
                range=0.08,
                down=0.14,
                category="risk",
            )
        elif (vs_pool_20 or 0) <= -3 or (vs_pool_60 or 0) <= -6:
            _add_evidence(
                entries,
                "股票池相对强弱",
                f"20日相对股票池 {vs_pool_20 or 0:.2f}%，60日相对股票池 {vs_pool_60 or 0:.2f}%",
                up=-0.06,
                range=0.02,
                down=0.18,
                category="risk",
            )


def _factor_attribution_evidence(entries: list[dict[str, Any]], factor_profile: dict[str, Any]) -> None:
    attribution = factor_profile.get("attribution") or {}
    return20 = _to_float(attribution.get("stock_return20_pct"))
    excess_market_20 = _to_float(attribution.get("excess_market_20_pct"))
    excess_pool_average_20 = _to_float(attribution.get("excess_pool_average_20_pct"))
    excess_pool_median_20 = _to_float(attribution.get("excess_pool_median_20_pct"))
    if excess_market_20 is None and excess_pool_average_20 is None and excess_pool_median_20 is None:
        return

    pool_reference = (
        excess_pool_median_20
        if excess_pool_median_20 is not None
        else excess_pool_average_20
    )
    pool_label = (
        f"股票池中位数 {pool_reference:.2f}%"
        if excess_pool_median_20 is not None
        else f"股票池均值 {pool_reference:.2f}%"
        if pool_reference is not None
        else "股票池暂无可比数据"
    )
    market_label = (
        f"大盘 {excess_market_20:.2f}%"
        if excess_market_20 is not None
        else "大盘暂无可比数据"
    )

    if (
        return20 is not None
        and return20 > 0
        and (excess_market_20 is not None and excess_market_20 <= -4)
        and (pool_reference is not None and pool_reference <= -3)
    ):
        _add_evidence(
            entries,
            "因子归因",
            f"20日上涨 {return20:.2f}%，但相对{market_label}、相对{pool_label}，更像共同因子带动",
            up=-0.08,
            range=0.08,
            down=0.2,
            category="risk",
        )
    elif (
        excess_market_20 is not None
        and excess_market_20 >= 5
        and (pool_reference is None or pool_reference >= 3)
    ):
        _add_evidence(
            entries,
            "因子归因",
            f"20日相对{market_label}、相对{pool_label}，个股残差强势较明显",
            up=0.22,
            range=0.02,
            down=-0.08,
            category="trend",
        )
    elif (
        return20 is not None
        and return20 > 0
        and excess_market_20 is not None
        and abs(excess_market_20) <= 2
        and pool_reference is not None
        and abs(pool_reference) <= 2
    ):
        _add_evidence(
            entries,
            "因子归因",
            f"20日上涨 {return20:.2f}%，但相对{market_label}、相对{pool_label}都接近，先按共同因子上涨处理",
            up=0.02,
            range=0.12,
            down=0.02,
            category="mean_reversion",
        )


def _mean_reversion_factor_evidence(entries: list[dict[str, Any]], factor_profile: dict[str, Any]) -> None:
    momentum = factor_profile.get("momentum") or {}
    mean_reversion = factor_profile.get("mean_reversion") or {}
    return20 = _to_float(momentum.get("return20_pct"))
    ma20_deviation = _to_float(mean_reversion.get("ma20_deviation_pct"))
    ma60_deviation = _to_float(mean_reversion.get("ma60_deviation_pct"))
    volume_ratio = _to_float(mean_reversion.get("volume_ratio"))
    if ma20_deviation is None:
        return

    if -3 <= ma20_deviation <= 5 and volume_ratio is not None and volume_ratio <= 0.85 and (return20 or 0) > 0:
        _add_evidence(
            entries,
            "均值回归位置",
            f"价格在 MA20 附近 {ma20_deviation:.2f}%，量能比 {volume_ratio or 0:.2f}，偏缩量回踩",
            up=0.18,
            range=0.1,
            down=-0.04,
            category="mean_reversion",
        )
    elif ma20_deviation >= 12:
        _add_evidence(
            entries,
            "均值回归位置",
            f"价格偏离 MA20 {ma20_deviation:.2f}%，短线回归压力上升",
            up=-0.04,
            range=0.18,
            down=0.12,
            category="mean_reversion",
        )
    elif ma20_deviation <= -8:
        _add_evidence(
            entries,
            "均值回归位置",
            f"价格低于 MA20 {abs(ma20_deviation):.2f}%，弱势修复仍需确认",
            up=-0.06,
            range=0.08,
            down=0.18,
            category="risk",
        )
    elif ma60_deviation is not None and ma60_deviation >= 25:
        _add_evidence(
            entries,
            "均值回归位置",
            f"价格偏离 MA60 {ma60_deviation:.2f}%，中期乖离偏高",
            up=-0.02,
            range=0.16,
            down=0.1,
            category="mean_reversion",
        )


def _chan_evidence(entries: list[dict[str, Any]], chan: dict[str, Any] | None) -> None:
    signal_type = (chan or {}).get("signal", {}).get("type")
    structure = (chan or {}).get("structure")
    if signal_type in {"suspected_third_buy", "upward_leave"}:
        _add_evidence(entries, "缠论结构", f"{structure or ''} / {signal_type}", up=0.34, range=0.03, down=-0.08, category="breakout")
    elif signal_type == "extended_above_center":
        _add_evidence(entries, "缠论结构", "远离旧中枢上方，等待当前价附近新结构", up=0.08, range=0.24, down=0.12, category="risk")
    elif signal_type == "center_range":
        _add_evidence(entries, "缠论结构", "中枢震荡，方向未选择", up=0.02, range=0.3, down=0.02, category="mean_reversion")
    elif signal_type in {"suspected_third_sell", "downward_leave"}:
        _add_evidence(entries, "缠论结构", f"{structure or ''} / {signal_type}", up=-0.08, range=0.02, down=0.34, category="risk")
    elif signal_type == "extended_below_center":
        _add_evidence(entries, "缠论结构", "远离旧中枢下方，等待当前价附近新结构", up=0.02, range=0.18, down=0.22, category="risk")
    elif signal_type:
        _add_evidence(entries, "缠论结构", f"结构信号 {signal_type}", up=0, range=0.08, down=0, category="mean_reversion")


def _position_evidence(entries: list[dict[str, Any]], position: dict[str, Any] | None) -> None:
    if not position:
        _add_evidence(entries, "持仓状态", "未持仓，仅作为候选观察", up=0, range=0.08, down=0, category="mean_reversion")
        return
    pnl_pct = _to_float(position.get("pnl_pct"))
    if pnl_pct is None:
        return
    if pnl_pct >= 30:
        _add_evidence(entries, "持仓盈亏", f"浮盈 {pnl_pct:.2f}%，回撤敏感度提高", up=0.02, range=0.18, down=0.24, category="risk")
    elif pnl_pct >= 10:
        _add_evidence(entries, "持仓盈亏", f"浮盈 {pnl_pct:.2f}%，趋势仍需确认", up=0.1, range=0.12, down=0.04, category="mean_reversion")
    elif pnl_pct <= -8:
        _add_evidence(entries, "持仓盈亏", f"浮亏 {pnl_pct:.2f}%，风险证据抬升", up=-0.08, range=0.04, down=0.24, category="risk")
    else:
        _add_evidence(entries, "持仓盈亏", f"盈亏 {pnl_pct:.2f}%，接近成本区", up=0.03, range=0.12, down=0.03, category="mean_reversion")


def _price_location_evidence(
    entries: list[dict[str, Any]],
    indicator: dict[str, Any],
    current_price: float | None,
) -> None:
    if current_price is None:
        return
    high_20 = _to_float(indicator.get("recent_high_20"))
    low_20 = _to_float(indicator.get("recent_low_20"))
    if high_20 and current_price >= high_20 * 0.98:
        _add_evidence(entries, "价格位置", "接近20日高位，强势但追高风险增加", up=0.16, range=0.04, down=0.08, category="breakout")
    if low_20 and current_price <= low_20 * 1.03:
        _add_evidence(entries, "价格位置", "接近20日低位，弱势修复仍需确认", up=-0.04, range=0.08, down=0.18, category="risk")


def _decision(
    *,
    probabilities: dict[str, float],
    position: dict[str, Any] | None,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    up = probabilities["up"]
    range_prob = probabilities["range"]
    down = probabilities["down"]
    risk_level = _risk_level(down=down, evidence=evidence)
    if position:
        if risk_level == "high":
            key = "risk_review"
            label = "风险复核"
        elif up >= 0.5 and down < 0.3:
            key = "hold_observe"
            label = "持有观察"
        elif range_prob >= 0.42:
            key = "position_review"
            label = "仓位复核"
        else:
            key = "wait_confirm"
            label = "等待确认"
    else:
        if up >= 0.55 and down < 0.28:
            key = "watch_candidate"
            label = "重点观察"
        elif down >= 0.4:
            key = "avoid_watch"
            label = "暂缓观察"
        else:
            key = "wait_confirm"
            label = "等待确认"

    return {
        "key": key,
        "label": label,
        "risk_level": risk_level,
        "confidence": _confidence(max(probabilities.values())),
        "next_check": _next_check(key, probabilities),
    }


def _risk_level(*, down: float, evidence: list[dict[str, Any]]) -> str:
    risk_score = down
    if any(entry["source"] == "持仓盈亏" and entry["contribution"]["down"] >= 0.2 for entry in evidence):
        risk_score += 0.08
    if risk_score >= 0.48:
        return "high"
    if risk_score >= 0.34:
        return "medium"
    return "low"


def _confidence(max_probability: float) -> str:
    if max_probability >= 0.58:
        return "high"
    if max_probability >= 0.45:
        return "medium"
    return "low"


def _next_check(key: str, probabilities: dict[str, float]) -> str:
    if key == "risk_review":
        return "复核下跌情景证据是否继续增强，并检查持仓风险敞口。"
    if key == "hold_observe":
        return "观察上涨证据能否延续，重点看 MA、成交量和相对强弱。"
    if key == "position_review":
        return "等待震荡区间方向选择，复核持仓成本和浮盈回撤承受度。"
    if key == "watch_candidate":
        return "等待概率优势与价格触发条件同时出现，再纳入重点跟踪。"
    if key == "avoid_watch":
        return "先等待下跌证据降温或重新形成向上结构。"
    dominant = max(probabilities, key=lambda key: probabilities[key])
    return f"当前以{_scenario_label(dominant)}情景为主，等待更多证据确认。"


def _scenario_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {scenario: 0 for scenario in SCENARIOS}
    for item in items:
        probabilities = item.get("probabilities") or {}
        if probabilities:
            scenario = max(probabilities, key=lambda key: probabilities[key])
            counts[scenario] += 1
    return counts


def _next_steps(
    items: list[dict[str, Any]],
    failed_quote_symbols: list[str],
    failed_kline_symbols: list[str],
) -> list[str]:
    steps: list[str] = []
    if failed_quote_symbols:
        steps.append("补齐行情失败股票的现价数据")
    if failed_kline_symbols:
        steps.append("补齐K线失败股票的趋势和缠论证据")
    if any(item.get("decision", {}).get("risk_level") == "high" for item in items):
        steps.append("优先复核高风险持仓的证据账本")
    if any(item.get("decision", {}).get("key") == "watch_candidate" for item in items):
        steps.append("跟踪上涨概率占优但尚未持仓的候选股")
    if not steps:
        steps.append("等待新行情更新后继续观察概率变化")
    return steps


def _pool_context(quotes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    changes = [
        value
        for quote in quotes.values()
        if (value := _to_float(quote.get("pct_change"))) is not None
    ]
    if not changes:
        return {"average_pct_change": None, "positive_ratio": None}
    return {
        "average_pct_change": sum(changes) / len(changes),
        "positive_ratio": sum(1 for value in changes if value > 0) / len(changes),
    }


def _factor_context(
    *,
    index_bars: list[dict[str, Any]],
    kline_by_symbol: dict[str, list[dict[str, Any]]],
    generated_at: str,
    calendar_index_bars: list[dict[str, Any]] | None = None,
    calendar_kline_by_symbol: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    index_dates = [bar["trade_date"] for bar in _dated_bars(
        index_bars if calendar_index_bars is None else calendar_index_bars
    )]
    calendar_pool = kline_by_symbol if calendar_kline_by_symbol is None else calendar_kline_by_symbol
    calendar = index_dates or sorted({
        bar["trade_date"] for bars in calendar_pool.values() for bar in _dated_bars(bars)
    })
    if not calendar:
        calendar = sorted({
            bar["trade_date"] for bars in kline_by_symbol.values() for bar in _dated_bars(bars)
        })
    as_of = calendar[-1] if calendar else None
    calendar_source = "index" if index_dates else "pool"
    windows = {
        str(sessions): {
            "start": calendar[-sessions - 1] if len(calendar) > sessions else None,
            "end": as_of,
            "as_of": as_of,
            "sessions": sessions,
            "calendar_source": calendar_source,
        }
        for sessions in (20, 60)
    }

    def window_returns(bars: list[dict[str, Any]]) -> dict[str, Any]:
        endpoints = {
            key: _window_return(bars, window, calendar, generated_at)
            for key, window in windows.items()
        }
        return {
            "return20_pct": endpoints["20"]["return_pct"],
            "return60_pct": endpoints["60"]["return_pct"],
            "windows": endpoints,
        }

    symbol_returns = {
        normalize_symbol(symbol): window_returns(bars)
        for symbol, bars in kline_by_symbol.items()
    }
    return {
        "as_of": as_of,
        "calendar": calendar,
        "calendar_source": calendar_source,
        "windows": windows,
        "index": window_returns(index_bars),
        "pool": {
            "sample_size": len(symbol_returns),
            "sample_size20": sum(row["return20_pct"] is not None for row in symbol_returns.values()),
            "sample_size60": sum(row["return60_pct"] is not None for row in symbol_returns.values()),
            "average_return20_pct": _round_optional(
                _average_optional(row.get("return20_pct") for row in symbol_returns.values())
            ),
            "average_return60_pct": _round_optional(
                _average_optional(row.get("return60_pct") for row in symbol_returns.values())
            ),
            "median_return20_pct": _round_optional(
                _median_optional(row.get("return20_pct") for row in symbol_returns.values())
            ),
            "median_return60_pct": _round_optional(
                _median_optional(row.get("return60_pct") for row in symbol_returns.values())
            ),
        },
        "symbols": symbol_returns,
    }


def _trade_date(value: Any) -> str | None:
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError:
        return None


def _dated_bars(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_date = {
        trade_date: {**bar, "trade_date": trade_date}
        for bar in bars if (trade_date := _trade_date(bar.get("trade_date"))) is not None
    }
    return [by_date[key] for key in sorted(by_date)]


def _clean_bars(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean = []
    for bar in _dated_bars(bars):
        prices = _valid_ohlc(bar)
        if prices is None:
            continue
        clean.append({**bar, **prices, "volume": _valid_volume(bar.get("volume"))})
    return clean


def _valid_ohlc(bar: dict[str, Any]) -> dict[str, float] | None:
    prices = {key: _positive_price(bar.get(key)) for key in ("open", "high", "low", "close")}
    if any(value is None for value in prices.values()):
        return None
    if not (
        prices["low"] <= min(prices["open"], prices["close"])
        <= max(prices["open"], prices["close"]) <= prices["high"]
    ):
        return None
    return prices


def _valid_volume(value: Any) -> float | None:
    volume = None if isinstance(value, bool) else _to_float(value)
    return volume if volume is not None and volume >= 0 else None


def _fresh_quote(quote: dict[str, Any] | None, generated_at: str) -> dict[str, Any] | None:
    price = _positive_price((quote or {}).get("price"))
    if price is None or _stale_date((quote or {}).get("fetched_at"), generated_at):
        return None
    return {**quote, "price": price, "pct_change": _to_float(quote.get("pct_change"))}


def _series_is_stale(bars: list[dict[str, Any]], calendar: list[str], generated_at: str) -> bool:
    return bool(bars and (
        _stale_date(bars[-1]["trade_date"], generated_at)
        or sum(day > bars[-1]["trade_date"] for day in calendar) > MAX_ENDPOINT_LAG_SESSIONS
    ))


def _shared_inputs(
    *, quotes: dict[str, dict[str, Any]], kline_by_symbol: dict[str, list[dict[str, Any]]],
    index_bars: list[dict[str, Any]], generated_at: str,
) -> dict[str, Any]:
    clean_index = _clean_bars(index_bars)
    clean_klines = {symbol: _clean_bars(bars) for symbol, bars in kline_by_symbol.items()}
    calendar = sorted({
        bar["trade_date"] for bars in [clean_index, *clean_klines.values()] for bar in bars
    })
    fresh_quotes = {
        symbol: fresh for symbol, quote in quotes.items()
        if (fresh := _fresh_quote(quote, generated_at)) is not None
    }
    fresh_klines = {
        symbol: bars for symbol, bars in clean_klines.items()
        if bars and not _series_is_stale(bars, calendar, generated_at)
    }
    fresh_index = clean_index if not _series_is_stale(clean_index, calendar, generated_at) else []
    excluded_quotes = sorted(set(quotes) - set(fresh_quotes))
    excluded_klines = sorted(set(kline_by_symbol) - set(fresh_klines))
    issues = []
    if _series_is_stale(clean_index, calendar, generated_at):
        issues.append("stale_index")
    elif len(clean_index) != len(index_bars):
        issues.append("invalid_index_bars")
    elif len(clean_index) < 60:
        issues.append("insufficient_index" if clean_index else "missing_index")
    if excluded_quotes:
        issues.append("excluded_quotes")
    if excluded_klines:
        issues.append("excluded_klines")
    if any(len(clean_klines[symbol]) != len(bars) for symbol, bars in kline_by_symbol.items()):
        issues.append("invalid_pool_bars")
    has_fresh = bool(fresh_quotes or fresh_klines or fresh_index)
    has_stale = (
        "stale_index" in issues
        or any(_stale_date(quote.get("fetched_at"), generated_at) for quote in quotes.values())
        or any(_series_is_stale(bars, calendar, generated_at) for bars in clean_klines.values())
    )
    status = (
        "stale" if not has_fresh and has_stale
        else "insufficient" if not has_fresh
        else "partial" if issues else "complete"
    )
    return {
        "quotes": fresh_quotes, "klines": fresh_klines, "index": fresh_index,
        "data_quality": {
            "status": status, "degraded": status != "complete", "issues": issues,
            "excluded_quote_symbols": excluded_quotes,
            "excluded_kline_symbols": excluded_klines,
            "index_as_of": _dated_bars(index_bars)[-1]["trade_date"] if _dated_bars(index_bars) else None,
            "eligible_index_as_of": fresh_index[-1]["trade_date"] if fresh_index else None,
        },
    }


def _stale_date(value: str | None, generated_at: str) -> bool:
    trade_date = _trade_date(value)
    reference_date = _trade_date(generated_at)
    return bool(
        trade_date and reference_date
        and (date.fromisoformat(reference_date) - date.fromisoformat(trade_date)).days > STALE_AFTER_CALENDAR_DAYS
    )


def _window_return(
    bars: list[dict[str, Any]], window: dict[str, Any], calendar: list[str], generated_at: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "insufficient" if window["start"] is None else "missing",
        "return_pct": None,
        "start_date": None, "end_date": None,
        "start_close": None, "end_close": None,
        "start_lag_sessions": None, "end_lag_sessions": None,
        "start_lag_calendar_days": None, "end_lag_calendar_days": None,
        "as_of": None,
    }
    ordered = _dated_bars(bars)
    result["as_of"] = ordered[-1]["trade_date"] if ordered else None
    if window["start"] is None or not ordered:
        return result
    # Keep invalid endpoint records visible; never look past a bad close to fabricate a return.
    for label in ("start", "end"):
        available = [bar for bar in ordered if bar["trade_date"] <= window[label]]
        if not available:
            return result
        endpoint = available[-1]
        result[f"{label}_date"] = endpoint["trade_date"]
        result[f"{label}_close"] = _positive_price(endpoint.get("close"))
        result[f"{label}_lag_sessions"] = sum(endpoint["trade_date"] < day <= window[label] for day in calendar)
        result[f"{label}_lag_calendar_days"] = (
            date.fromisoformat(window[label]) - date.fromisoformat(endpoint["trade_date"])
        ).days
    endpoints = [bar for bar in ordered if bar["trade_date"] in {result["start_date"], result["end_date"]}]
    if (
        result["start_close"] is None or result["end_close"] is None
        or any(_valid_ohlc(bar) is None for bar in endpoints)
    ):
        result["status"] = "invalid"
    elif (
        max(result["start_lag_sessions"], result["end_lag_sessions"]) > MAX_ENDPOINT_LAG_SESSIONS
        or max(result["start_lag_calendar_days"], result["end_lag_calendar_days"]) > STALE_AFTER_CALENDAR_DAYS
        or _stale_date(result["end_date"], generated_at)
    ):
        result["status"] = "stale"
    else:
        result["status"] = "complete"
        result["return_pct"] = _round_optional((result["end_close"] / result["start_close"] - 1) * 100)
    return result


def _item_data_quality(
    *, symbol: str, quote: dict[str, Any] | None, raw_bars: list[dict[str, Any]],
    bars: list[dict[str, Any]], factor_context: dict[str, Any], generated_at: str,
) -> dict[str, Any]:
    issues = []
    if _positive_price((quote or {}).get("price")) is None:
        issues.append("missing_quote")
        if quote is not None:
            issues.append("invalid_quote_price")
    if not bars:
        issues.append("missing_kline")
    if len(bars) < 60:
        issues.append("insufficient_kline")
    if len(bars) != len(raw_bars):
        issues.append("invalid_kline_bars")
    if any(bar["volume"] is None for bar in bars):
        issues.append("invalid_volume")
    kline_as_of = bars[-1]["trade_date"] if bars else None
    calendar = factor_context["calendar"]
    if kline_as_of and (
        _stale_date(kline_as_of, generated_at)
        or sum(day > kline_as_of for day in calendar) > MAX_ENDPOINT_LAG_SESSIONS
    ):
        issues.append("stale_kline")
    quote_fetched_at = (quote or {}).get("fetched_at")
    if quote_fetched_at and _stale_date(quote_fetched_at, generated_at):
        issues.append("stale_quote")
    index_windows = factor_context["index"]["windows"]
    if any(endpoint["status"] != "complete" for endpoint in index_windows.values()):
        issues.append(
            "stale_index" if any(row["status"] == "stale" for row in index_windows.values())
            else "missing_index"
        )
    stock_windows = (factor_context["symbols"].get(normalize_symbol(symbol)) or {}).get("windows", {})
    if any(endpoint["status"] != "complete" for endpoint in stock_windows.values()):
        issues.append("unavailable_factor_window")
    if any(endpoint["status"] == "stale" for endpoint in stock_windows.values()):
        issues.append("stale_factor_window")
    status = (
        "stale" if any(issue in issues for issue in ("stale_kline", "stale_quote", "stale_factor_window"))
        else "insufficient" if len(bars) < 60
        else "partial" if issues else "complete"
    )
    return {
        "status": status, "issues": issues,
        "quote_fetched_at": quote_fetched_at,
        "kline_as_of": kline_as_of, "bar_count": len(bars),
    }


def _cap_confidence(confidence: str, ceiling: str) -> str:
    levels = ("low", "medium", "high")
    return levels[min(levels.index(confidence), levels.index(ceiling))]


def _factor_profile(
    *,
    symbol: str,
    bars: list[dict[str, Any]],
    indicator: dict[str, Any],
    current_price: float | None,
    factor_context: dict[str, Any],
) -> dict[str, Any]:
    normalized_symbol = normalize_symbol(symbol)
    symbol_returns = (factor_context.get("symbols") or {}).get(normalized_symbol, {})
    return20 = _to_float(symbol_returns.get("return20_pct"))
    return60 = _to_float(symbol_returns.get("return60_pct"))
    index_context = factor_context.get("index") or {}
    pool_context = factor_context.get("pool") or {}
    index_return20 = _to_float(index_context.get("return20_pct"))
    index_return60 = _to_float(index_context.get("return60_pct"))
    pool_average_return20 = _to_float(pool_context.get("average_return20_pct"))
    pool_average_return60 = _to_float(pool_context.get("average_return60_pct"))
    pool_median_return20 = _to_float(pool_context.get("median_return20_pct"))
    pool_median_return60 = _to_float(pool_context.get("median_return60_pct"))
    ma = indicator.get("ma", {})
    ma20 = _to_float(ma.get("ma20"))
    ma60 = _to_float(ma.get("ma60"))
    return {
        "as_of": factor_context["as_of"],
        "windows": {
            key: {
                **window,
                "stock": symbol_returns.get("windows", {}).get(key),
                "index": index_context["windows"][key],
                "pool_sample_size": pool_context[f"sample_size{key}"],
            }
            for key, window in factor_context["windows"].items()
        },
        "momentum": {
            "return20_pct": _round_optional(return20),
            "return60_pct": _round_optional(return60),
        },
        "relative_strength": {
            "vs_index_20_pct": _round_optional(_diff_optional(return20, index_context.get("return20_pct"))),
            "vs_index_60_pct": _round_optional(_diff_optional(return60, index_context.get("return60_pct"))),
            "vs_pool_20_pct": _round_optional(_diff_optional(return20, pool_context.get("average_return20_pct"))),
            "vs_pool_60_pct": _round_optional(_diff_optional(return60, pool_context.get("average_return60_pct"))),
        },
        "mean_reversion": {
            "ma20_deviation_pct": _round_optional(_price_deviation_pct(current_price, ma20)),
            "ma60_deviation_pct": _round_optional(_price_deviation_pct(current_price, ma60)),
            "volume_ratio": _round_optional(_to_float(indicator.get("volume_ratio"))),
        },
        "attribution": {
            "stock_return20_pct": _round_optional(return20),
            "stock_return60_pct": _round_optional(return60),
            "market_return20_pct": _round_optional(index_return20),
            "market_return60_pct": _round_optional(index_return60),
            "pool_average_return20_pct": _round_optional(pool_average_return20),
            "pool_average_return60_pct": _round_optional(pool_average_return60),
            "pool_median_return20_pct": _round_optional(pool_median_return20),
            "pool_median_return60_pct": _round_optional(pool_median_return60),
            "excess_market_20_pct": _round_optional(_diff_optional(return20, index_return20)),
            "excess_market_60_pct": _round_optional(_diff_optional(return60, index_return60)),
            "excess_pool_average_20_pct": _round_optional(_diff_optional(return20, pool_average_return20)),
            "excess_pool_average_60_pct": _round_optional(_diff_optional(return60, pool_average_return60)),
            "excess_pool_median_20_pct": _round_optional(_diff_optional(return20, pool_median_return20)),
            "excess_pool_median_60_pct": _round_optional(_diff_optional(return60, pool_median_return60)),
        },
    }


def _symbol_order(watchlist: list[dict[str, Any]], holdings: list[dict[str, Any]]) -> list[str]:
    ordered_watchlist = sorted(
        watchlist,
        key=lambda row: (
            int(row.get("priority") or 99),
            str(row.get("updated_at") or ""),
            int(row.get("id") or 0),
        ),
    )
    symbols: list[str] = []
    seen: set[str] = set()
    for row in ordered_watchlist + holdings:
        symbol = normalize_symbol(str(row["symbol"]))
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def _position_context(holding: dict[str, Any] | None, current_price: float | None) -> dict[str, Any] | None:
    if holding is None:
        return None
    quantity = _to_float(holding.get("quantity")) or 0
    cost_price = _positive_price(holding.get("cost_price"))
    market_value = quantity * current_price if current_price is not None else None
    pnl = (
        quantity * (current_price - cost_price)
        if current_price is not None and cost_price is not None
        else None
    )
    pnl_pct = (
        ((current_price - cost_price) / cost_price) * 100
        if current_price is not None and cost_price not in {None, 0}
        else None
    )
    return {
        "holding_id": holding.get("id"),
        "quantity": quantity,
        "cost_price": cost_price,
        "market_value": round(market_value, 4) if market_value is not None else None,
        "pnl": round(pnl, 4) if pnl is not None else None,
        "pnl_pct": round(pnl_pct, 4) if pnl_pct is not None else None,
    }


def _current_price(quote: dict[str, Any] | None, bars: list[dict[str, Any]]) -> float | None:
    quote_price = _positive_price((quote or {}).get("price"))
    if quote_price is not None:
        return quote_price
    if bars:
        ordered = sorted(bars, key=lambda bar: str(bar["trade_date"]))
        return _positive_price(ordered[-1].get("close"))
    return None


def _return_pct(bars: list[dict[str, Any]], window: int) -> float | None:
    if len(bars) < 2:
        return None
    ordered = sorted(bars, key=lambda bar: str(bar["trade_date"]))
    last = _positive_price(ordered[-1].get("close"))
    previous = _positive_price(ordered[max(0, len(ordered) - window - 1)].get("close"))
    if last is None or previous in {None, 0}:
        return None
    return ((last - previous) / previous) * 100


def _atr_pct(indicator: dict[str, Any], current_price: float | None) -> float | None:
    atr = _to_float(indicator.get("atr14"))
    if atr is None or current_price in {None, 0}:
        return None
    return (atr / float(current_price)) * 100


def _price_deviation_pct(price: float | None, baseline: float | None) -> float | None:
    if price is None or baseline in {None, 0}:
        return None
    return (float(price) / float(baseline) - 1) * 100


def _diff_optional(left: Any, right: Any) -> float | None:
    left_value = _to_float(left)
    right_value = _to_float(right)
    if left_value is None or right_value is None:
        return None
    return left_value - right_value


def _average_optional(values: Any) -> float | None:
    numbers = [_to_float(value) for value in values]
    numbers = [value for value in numbers if value is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _median_optional(values: Any) -> float | None:
    numbers = sorted(value for value in (_to_float(value) for value in values) if value is not None)
    if not numbers:
        return None
    middle = len(numbers) // 2
    if len(numbers) % 2:
        return numbers[middle]
    return (numbers[middle - 1] + numbers[middle]) / 2


def _round_optional(value: Any, digits: int = 4) -> float | None:
    number = _to_float(value)
    return round(number, digits) if number is not None else None


def _apply_component(
    scores: dict[str, float],
    components: list[dict[str, Any]],
    source: str,
    observation: str,
    contribution: dict[str, float],
) -> None:
    for scenario in SCENARIOS:
        scores[scenario] += contribution.get(scenario, 0)
    components.append(
        {
            "source": source,
            "observation": observation,
            "contribution": {scenario: round(contribution.get(scenario, 0), 4) for scenario in SCENARIOS},
        }
    )


def _market_regime_prior(regime: str) -> dict[str, float] | None:
    priors = {
        "uptrend": {"up": 0.32, "range": 0.05, "down": -0.12},
        "downtrend": {"up": -0.12, "range": 0.05, "down": 0.32},
        "range": {"up": 0.02, "range": 0.28, "down": 0.02},
        "high_volatility_pressure": {"up": -0.16, "range": 0.18, "down": 0.35},
        "repair": {"up": 0.14, "range": 0.2, "down": -0.05},
    }
    return priors.get(regime)


def _apply_regime_weights(
    entries: list[dict[str, Any]],
    market_regime: dict[str, Any] | None,
) -> None:
    weights = ((market_regime or {}).get("strategy_bias") or {}).get("weights") or {}
    for entry in entries:
        category = str(entry.get("category") or "technical")
        weight = _to_float(weights.get(category)) or 1.0
        entry["regime_weight"] = round(weight, 4)
        entry["contribution"] = {
            scenario: round(float(entry["contribution"].get(scenario, 0)) * weight, 4)
            for scenario in SCENARIOS
        }


def _add_evidence(
    entries: list[dict[str, Any]],
    source: str,
    observation: str,
    *,
    up: float = 0,
    range: float = 0,  # noqa: A002 - scenario name is user-facing.
    down: float = 0,
    confidence: str = "medium",
    category: str = "technical",
) -> None:
    entries.append(
        {
            "source": source,
            "observation": observation,
            "category": category,
            "contribution": {
                "up": round(up, 4),
                "range": round(range, 4),
                "down": round(down, 4),
            },
            "confidence": confidence,
        }
    )


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    scaled = {key: value / SOFTMAX_TEMPERATURE for key, value in scores.items()}
    max_score = max(scaled.values())
    exp_values = {key: math.exp(value - max_score) for key, value in scaled.items()}
    total = sum(exp_values.values())
    return {key: round(value / total, 4) for key, value in exp_values.items()}


def _top_evidence(entries: list[dict[str, Any]], limit: int = 3) -> list[str]:
    scored = sorted(
        entries,
        key=lambda entry: max(abs(float(value)) for value in entry["contribution"].values()),
        reverse=True,
    )
    return [
        f"{entry['source']}：{entry['observation']}"
        for entry in scored[:limit]
    ]


def _scenario_label(scenario: str) -> str:
    return {
        "up": "上涨",
        "range": "震荡",
        "down": "下跌",
    }.get(scenario, scenario)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _positive_price(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    number = _to_float(value)
    return number if number is not None and number > 0 else None
