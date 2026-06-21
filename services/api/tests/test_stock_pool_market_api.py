from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from services.api.app.database import connect, init_db
from services.api.app.main import (
    api_analyze_stock_pool_with_market_source,
    api_generate_daily_review,
)
from services.api.app.repository import (
    create_holding,
    create_market_fetch_log,
    create_signal,
    create_stock_pool,
    create_watchlist_item,
    get_default_stock_pool,
)
from services.api.app.schemas import StockPoolMarketAnalysisRequest


class StockPoolMarketApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        init_db(self.db_path)
        self.connection = connect(self.db_path)

    def tearDown(self) -> None:
        self.connection.close()
        self.tmpdir.cleanup()

    def test_market_analysis_uses_ordered_watchlist_symbols(self) -> None:
        pool = get_default_stock_pool(self.connection)
        create_watchlist_item(
            self.connection,
            {"pool_id": pool["id"], "symbol": "603337", "name": "杰克科技", "priority": 2},
        )
        create_watchlist_item(
            self.connection,
            {"pool_id": pool["id"], "symbol": "688630", "name": "芯碁微装", "priority": 1},
        )
        calls: list[str] = []

        def fake_fetch_quote(_db, *, symbol: str, source: str) -> dict:
            calls.append(symbol)
            return {
                "snapshot_id": len(calls),
                "symbol": symbol,
                "name": f"Name {symbol}",
                "source": source,
                "price": 100 + len(calls),
                "fetched_at": "now",
            }

        with mock.patch(
            "services.api.app.main._fetch_quote_and_cache",
            side_effect=fake_fetch_quote,
        ):
            report = api_analyze_stock_pool_with_market_source(
                int(pool["id"]),
                StockPoolMarketAnalysisRequest(
                    source="tdx-official",
                    persist=False,
                    max_symbols=2,
                ),
                self.connection,
            )

        self.assertEqual(calls, ["688630", "603337"])
        self.assertEqual(report["payload"]["report_type"], "stock_pool_market_analysis")
        self.assertEqual(report["payload"]["data_quality"]["quote_count"], 2)
        self.assertEqual(report["payload"]["items"][0]["quote"]["fields"]["price"], 101)

    def test_daily_review_fetch_failures_are_scoped_to_pool(self) -> None:
        pool = get_default_stock_pool(self.connection)
        create_watchlist_item(
            self.connection,
            {"pool_id": pool["id"], "symbol": "603337", "name": "杰克科技"},
        )
        create_holding(
            self.connection,
            {"symbol": "603337", "quantity": 100, "cost_price": 10},
        )
        create_signal(
            self.connection,
            symbol="603337",
            signal_type="hold_observe",
            action="hold",
            strength=0.2,
            price=10.5,
            reason_json={
                "risk_level": "low",
                "reasons": ["Inside plan."],
                "next_check": "Keep watching.",
                "extra": {},
            },
        )
        create_market_fetch_log(
            self.connection,
            symbol="603337",
            source="tdx-official",
            data_type="quote",
            status="error",
            message="pool symbol failed",
        )
        create_market_fetch_log(
            self.connection,
            symbol="688630",
            source="tdx-official",
            data_type="quote",
            status="error",
            message="outside pool failed",
        )

        report = api_generate_daily_review(
            persist=False,
            signal_limit=100,
            pool_id=int(pool["id"]),
            db=self.connection,
        )

        quality = report["payload"]["data_quality"]
        self.assertEqual(quality["failed_fetch_count"], 1)
        self.assertEqual(quality["failed_fetches"][0]["symbol"], "603337")

    def test_daily_review_empty_pool_does_not_fall_back_to_all_data(self) -> None:
        pool = create_stock_pool(self.connection, {"name": "空股票池"})
        create_holding(
            self.connection,
            {"symbol": "600519", "quantity": 100, "cost_price": 100},
        )
        create_signal(
            self.connection,
            symbol="600519",
            signal_type="hold_observe",
            action="hold",
            strength=0.2,
            price=101,
            reason_json={
                "risk_level": "low",
                "reasons": ["Outside empty pool."],
                "next_check": "Wait.",
                "extra": {},
            },
        )
        create_market_fetch_log(
            self.connection,
            symbol="600519",
            source="tdx-official",
            data_type="quote",
            status="error",
            message="outside empty pool",
        )

        report = api_generate_daily_review(
            persist=False,
            signal_limit=100,
            pool_id=int(pool["id"]),
            db=self.connection,
        )

        payload = report["payload"]
        self.assertEqual(payload["holding_count"], 0)
        self.assertEqual(payload["signal_count"], 0)
        self.assertEqual(payload["data_quality"]["failed_fetch_count"], 0)


if __name__ == "__main__":
    unittest.main()
