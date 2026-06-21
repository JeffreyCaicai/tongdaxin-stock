from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from services.api.app.database import connect, init_db
from services.api.app.decision_engine import generate_stock_pool_decision_engine
from services.api.app.main import api_analyze_stock_pool_with_decision_engine
from services.api.app.repository import (
    create_holding,
    create_watchlist_item,
    get_default_stock_pool,
)
from services.api.app.schemas import StockPoolDecisionEngineRequest


def trend_bars(start_price: float = 80.0, days: int = 90, step: float = 0.45) -> list[dict]:
    start = date(2026, 1, 1)
    bars: list[dict] = []
    for index in range(days):
        close = start_price + index * step
        bars.append(
            {
                "trade_date": (start + timedelta(days=index)).isoformat(),
                "open": close - 0.2,
                "high": close + 0.8,
                "low": close - 0.8,
                "close": close,
                "volume": 1000 + index * 10,
            }
        )
    return bars


def mixed_bars(
    start_price: float = 80.0,
    days: int = 90,
    step: float = 0.45,
    *,
    final_price: float | None = None,
    volume: float = 1000,
) -> list[dict]:
    bars = trend_bars(start_price=start_price, days=days, step=step)
    for index, bar in enumerate(bars):
        bar["volume"] = volume + index * 4
    if final_price is not None:
        bars[-1] = {
            **bars[-1],
            "open": final_price - 0.1,
            "high": final_price + 0.5,
            "low": final_price - 0.5,
            "close": final_price,
            "volume": volume * 0.62,
        }
    return bars


def factor_return_bars(
    *,
    latest_price: float = 100.0,
    return20_pct: float = 0.0,
    return60_pct: float = 0.0,
    days: int = 90,
) -> list[dict]:
    start = date(2026, 1, 1)
    price_20 = latest_price / (1 + return20_pct / 100)
    price_60 = latest_price / (1 + return60_pct / 100)
    bars: list[dict] = []
    for index in range(days):
        if index <= days - 61:
            close = price_60
        elif index <= days - 21:
            progress = (index - (days - 61)) / 40
            close = price_60 + (price_20 - price_60) * progress
        else:
            progress = (index - (days - 21)) / 20
            close = price_20 + (latest_price - price_20) * progress
        bars.append(
            {
                "trade_date": (start + timedelta(days=index)).isoformat(),
                "open": close - 0.2,
                "high": close + 0.6,
                "low": close - 0.6,
                "close": close,
                "volume": 1200 + index * 5,
            }
        )
    return bars


class DecisionEngineTests(unittest.TestCase):
    def test_decision_engine_returns_probabilities_and_evidence(self) -> None:
        bars = trend_bars()
        report = generate_stock_pool_decision_engine(
            pool={"id": 1, "name": "默认股票池"},
            watchlist=[{"id": 1, "symbol": "688630", "name": "芯碁微装", "priority": 1}],
            holdings=[{"id": 1, "symbol": "688630", "quantity": 100, "cost_price": 95}],
            quotes={
                "688630": {
                    "symbol": "688630",
                    "name": "芯碁微装",
                    "price": bars[-1]["close"],
                    "pct_change": 2.1,
                }
            },
            kline_by_symbol={"688630": bars},
            source="tdx-official",
            horizon_days=20,
            index_bars=trend_bars(start_price=3000, days=120, step=5),
        )

        item = report["items"][0]
        probabilities = item["probabilities"]
        self.assertEqual(report["report_type"], "stock_pool_decision_engine")
        self.assertEqual(report["market_regime"]["regime"], "uptrend")
        self.assertIn("rule_state_machine", report["tool_plan"]["market_regime_model"])
        self.assertIn("市场状态", {component["source"] for component in item["prior"]["components"]})
        self.assertAlmostEqual(sum(probabilities.values()), 1, places=3)
        self.assertGreater(probabilities["up"], probabilities["down"])
        self.assertIn("MA趋势", {entry["source"] for entry in item["evidence"]})
        self.assertTrue(all("category" in entry for entry in item["evidence"]))
        self.assertTrue(any("regime_weight" in entry for entry in item["evidence"]))
        self.assertIn(item["decision"]["key"], {"hold_observe", "position_review", "wait_confirm"})
        self.assertTrue(item["evidence_summary"])

    def test_decision_engine_adds_factor_evidence_conditioned_by_regime(self) -> None:
        strong_bars = mixed_bars(start_price=50, days=100, step=0.65, final_price=112)
        peer_bars = mixed_bars(start_price=50, days=100, step=0.12, final_price=62)
        index_bars = mixed_bars(start_price=3000, days=120, step=0.8, final_price=3105)

        report = generate_stock_pool_decision_engine(
            pool={"id": 1, "name": "默认股票池"},
            watchlist=[
                {"id": 1, "symbol": "688630", "name": "芯碁微装", "priority": 1},
                {"id": 2, "symbol": "603337", "name": "杰克科技", "priority": 2},
            ],
            holdings=[],
            quotes={
                "688630": {"symbol": "688630", "name": "芯碁微装", "price": 112, "pct_change": 2.4},
                "603337": {"symbol": "603337", "name": "杰克科技", "price": 62, "pct_change": 0.2},
            },
            kline_by_symbol={"688630": strong_bars, "603337": peer_bars},
            source="tdx-official",
            horizon_days=20,
            index_bars=index_bars,
        )

        item = next(row for row in report["items"] if row["symbol"] == "688630")
        sources = {entry["source"] for entry in item["evidence"]}
        self.assertIn("中期动量", sources)
        self.assertIn("指数相对强弱", sources)
        self.assertIn("股票池相对强弱", sources)
        self.assertIn("均值回归位置", sources)
        self.assertIn("factor_profile", item)
        self.assertGreater(item["factor_profile"]["relative_strength"]["vs_index_20_pct"], 0)
        self.assertGreater(item["factor_profile"]["relative_strength"]["vs_pool_20_pct"], 0)
        self.assertTrue(
            any(entry["source"] == "中期动量" and entry["regime_weight"] > 1 for entry in item["evidence"])
        )

    def test_decision_engine_separates_common_factor_rise_from_specific_strength(self) -> None:
        weak_absolute_bars = factor_return_bars(
            latest_price=105,
            return20_pct=5,
            return60_pct=12,
        )
        peer_a_bars = factor_return_bars(latest_price=118, return20_pct=18, return60_pct=24)
        peer_b_bars = factor_return_bars(latest_price=120, return20_pct=20, return60_pct=26)
        index_bars = factor_return_bars(latest_price=3400, return20_pct=14, return60_pct=18, days=120)

        report = generate_stock_pool_decision_engine(
            pool={"id": 1, "name": "默认股票池"},
            watchlist=[
                {"id": 1, "symbol": "600519", "name": "贵州茅台", "priority": 1},
                {"id": 2, "symbol": "688630", "name": "芯碁微装", "priority": 2},
                {"id": 3, "symbol": "603337", "name": "杰克科技", "priority": 3},
            ],
            holdings=[],
            quotes={
                "600519": {"symbol": "600519", "name": "贵州茅台", "price": 105, "pct_change": 0.8},
                "688630": {"symbol": "688630", "name": "芯碁微装", "price": 118, "pct_change": 2.1},
                "603337": {"symbol": "603337", "name": "杰克科技", "price": 120, "pct_change": 2.4},
            },
            kline_by_symbol={
                "600519": weak_absolute_bars,
                "688630": peer_a_bars,
                "603337": peer_b_bars,
            },
            source="tdx-official",
            horizon_days=20,
            index_bars=index_bars,
        )

        item = next(row for row in report["items"] if row["symbol"] == "600519")
        attribution = item["factor_profile"]["attribution"]
        self.assertAlmostEqual(attribution["stock_return20_pct"], 5.0, places=2)
        self.assertAlmostEqual(attribution["market_return20_pct"], 14.0, places=2)
        self.assertAlmostEqual(attribution["pool_median_return20_pct"], 18.0, places=2)
        self.assertAlmostEqual(attribution["excess_market_20_pct"], -9.0, places=2)
        self.assertAlmostEqual(attribution["excess_pool_median_20_pct"], -13.0, places=2)
        evidence = next(entry for entry in item["evidence"] if entry["source"] == "因子归因")
        self.assertIn("共同因子", evidence["observation"])
        self.assertGreater(evidence["contribution"]["down"], evidence["contribution"]["up"])

    def test_decision_engine_api_uses_watchlist_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_db(db_path)
            connection = connect(db_path)
            try:
                pool = get_default_stock_pool(connection)
                create_watchlist_item(
                    connection,
                    {"pool_id": pool["id"], "symbol": "688630", "name": "芯碁微装", "priority": 1},
                )
                create_holding(
                    connection,
                    {"symbol": "688630", "name": "芯碁微装", "quantity": 100, "cost_price": 95},
                )
                calls: list[tuple[str, str]] = []
                bars = trend_bars()

                def fake_fetch_quote(_db, *, symbol: str, source: str) -> dict:
                    calls.append(("quote", symbol))
                    return {
                        "snapshot_id": 1,
                        "symbol": symbol,
                        "name": "芯碁微装",
                        "source": source,
                        "price": bars[-1]["close"],
                        "pct_change": 2.1,
                        "fetched_at": "now",
                    }

                def fake_fetch_kline(_db, *, symbol: str, source: str, period: str, limit: int) -> dict:
                    calls.append(("kline", symbol))
                    return {
                        "symbol": symbol,
                        "source": source,
                        "period": period,
                        "count": len(bars),
                        "bars": bars,
                    }

                with (
                    mock.patch("services.api.app.main._fetch_quote_and_cache", side_effect=fake_fetch_quote),
                    mock.patch("services.api.app.main._fetch_kline_and_cache", side_effect=fake_fetch_kline),
                ):
                    report = api_analyze_stock_pool_with_decision_engine(
                        int(pool["id"]),
                        StockPoolDecisionEngineRequest(
                            source="tdx-official",
                            persist=False,
                            max_symbols=1,
                            horizon_days=20,
                        ),
                        connection,
                    )

                payload = report["payload"]
                self.assertEqual(calls, [("kline", "000300"), ("quote", "688630"), ("kline", "688630")])
                self.assertEqual(payload["report_type"], "stock_pool_decision_engine")
                self.assertEqual(payload["scope"]["horizon_days"], 20)
                self.assertEqual(payload["scope"]["market_index_symbol"], "000300")
                self.assertIn("market_regime", payload)
                self.assertEqual(payload["data_quality"]["failed_quote_count"], 0)
                self.assertEqual(payload["items"][0]["symbol"], "688630")
                self.assertIn("probabilities", payload["items"][0])
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
