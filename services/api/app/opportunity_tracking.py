"""Forward price observation of immutable scan cohorts; not a trading backtest."""
from __future__ import annotations

from datetime import date
from statistics import mean

from .opportunity_prices import completed_daily_bars, local_timestamp

SESSIONS = (5, 20, 60, 120)
MODEL = "opportunity_followup_v1"


def _drawdown(prices: list[float]) -> float:
    peak, worst = prices[0], 0.0
    for price in prices:
        peak = max(peak, price)
        worst = min(worst, (price / peak - 1) * 100)
    return round(worst, 4)


def _aggregate(rows: list[dict], sessions: str) -> dict:
    outcomes = [row["outcomes"][sessions] for row in rows]
    matured = [row for row in outcomes if row["status"] == "matured"]
    return {"total": len(rows), "matured": len(matured),
            "pending": sum(row["status"] == "pending" for row in outcomes),
            "unavailable": sum(row["status"] == "unavailable" for row in outcomes),
            "mean_return_pct": round(mean(row["return_pct"] for row in matured), 4) if matured else None,
            "mean_excess_pp": round(mean(row["excess_pp"] for row in matured), 4) if matured else None,
            "positive_fraction": sum(row["return_pct"] > 0 for row in matured) / len(matured) if matured else None,
            "worst_drawdown_pct": min(row["max_drawdown_pct"] for row in matured) if matured else None}


def evaluate_followup(*, report: dict, klines: dict, index_bars: list[dict], as_of: str) -> dict:
    index, issues = completed_daily_bars(index_bars, as_of)
    signal_date = None
    try:
        signal_date = local_timestamp(report["generated_at"]).date().isoformat()
        if local_timestamp(report["generated_at"]) > local_timestamp(as_of):
            issues.append("future_snapshot")
    except (ValueError, KeyError, TypeError):
        issues.append("invalid_snapshot_time")
    if report.get("source") not in {"tdx-official", "mock"} or report.get("price_basis", {}).get("tdx_kline_TQFlag") != 11:
        issues.append("unverified_price_basis")
    if report.get("benchmark") != "SH000300":
        issues.append("unverified_benchmark")
    if not index:
        issues.append("missing_benchmark")
    elif signal_date and index[0]["trade_date"] > signal_date:
        issues.append("history_window_lost")
    calendar = [row for row in index if signal_date and row["trade_date"] > signal_date]
    index_dates = {row["trade_date"] for row in index}
    stale_index = bool(index and (local_timestamp(as_of).date() - date.fromisoformat(index[-1]["trade_date"])).days > 10)
    items = []
    selected = set(report.get("selected", []))
    for item in report.get("items", []):
        stock, stock_issues = completed_daily_bars(klines.get(item["symbol"], []), as_of)
        prices = {row["trade_date"]: row for row in stock}
        outcomes = {}
        for sessions in SESSIONS:
            outcome = {"status": "unavailable", "issues": list(issues), "sessions": sessions,
                       "start_date": calendar[0]["trade_date"] if calendar else None,
                       "end_date": calendar[sessions-1]["trade_date"] if len(calendar) >= sessions else None,
                       "reference_open": None, "end_close": None,
                       "return_pct": None, "benchmark_return_pct": None, "excess_pp": None,
                       "max_drawdown_pct": None}
            outcomes[str(sessions)] = outcome
            if issues:
                continue
            window_end = outcome["end_date"] or (stock[-1]["trade_date"] if stock else signal_date)
            if any(signal_date < row["trade_date"] <= window_end and row["trade_date"] not in index_dates
                   and row["volume"] is not None and row["volume"] > 0 for row in stock):
                outcome["issues"] = ["missing_benchmark_sessions"]
                continue
            if len(calendar) < sessions:
                if stale_index:
                    outcome["issues"] = ["stale_benchmark"]
                else:
                    outcome["status"] = "pending"
                continue
            sample = calendar[:sessions]
            if stock_issues or any(row["trade_date"] not in prices for row in sample):
                outcome["issues"] = stock_issues or ["missing_stock_sessions"]
                continue
            window = [prices[row["trade_date"]] for row in sample]
            if any(row["volume"] is None or row["volume"] <= 0 for row in window):
                outcome["issues"] = ["inactive_period_sessions"]
                continue
            start, end = window[0]["open"], window[-1]["close"]
            stock_return = (end / start - 1) * 100
            index_return = (sample[-1]["close"] / sample[0]["open"] - 1) * 100
            outcome.update(status="matured", reference_open=start, end_close=end,
                           return_pct=round(stock_return, 4), benchmark_return_pct=round(index_return, 4),
                           excess_pp=round(stock_return - index_return, 4),
                           max_drawdown_pct=_drawdown([start, *[row["close"] for row in window]]))
        group = "selected" if item["symbol"] in selected else "excluded" if item.get("level") == "excluded" else "not_selected"
        items.append({"symbol": item["symbol"], "name": item.get("name"), "origin": item.get("origin"),
                      "group": group, "level": item.get("level"), "rank_score": item.get("rank_score"),
                      "period_assessments": item.get("period_assessments"), "outcomes": outcomes})
    return {"report_type": "opportunity_followup_result", "model_version": MODEL,
            "recommendation_model": report.get("model_version"), "source": report.get("source"),
            "is_demo": report.get("source") == "mock", "generated_at": report.get("generated_at"),
            "evaluated_at": as_of, "signal_date": signal_date,
            "benchmark": report.get("benchmark"), "benchmark_as_of": index[-1]["trade_date"] if index else None,
            "issues": sorted(set(issues)), "items": items,
            "summary": {str(sessions): {group: _aggregate([row for row in items if row["group"] == group], str(sessions))
                                        for group in ("selected", "not_selected", "excluded")} for sessions in SESSIONS},
            "period_summary": {str(sessions): {
                stance: _aggregate([row for row in items
                    if (row["period_assessments"] or {}).get(str(sessions), {}).get("stance", "legacy") == stance], str(sessions))
                for stance in ("favorable", "wait", "avoid", "insufficient", "legacy")
            } for sessions in SESSIONS},
            "method": {"start": "next_session_open", "end": "nth_session_close", "calendar": "SH000300_daily",
                       "basis": "same_fetch_TQFlag11", "drawdown": "reference_open_then_daily_closes",
                       "execution_costs_included": False, "tradeability_checked": False,
                       "limitations": ["price_performance_not_trade_pnl", "screened_cohort_not_market", "overlapping_samples_not_independent"]}}
