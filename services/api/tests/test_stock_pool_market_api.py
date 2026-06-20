from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from services.api.app.database import connect, init_db
from services.api.app.main import api_analyze_stock_pool_with_market_source
from services.api.app.repository import (
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


if __name__ == "__main__":
    unittest.main()
