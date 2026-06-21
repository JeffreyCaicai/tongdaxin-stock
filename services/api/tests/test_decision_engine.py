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
