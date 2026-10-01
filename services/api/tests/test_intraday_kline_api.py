from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from services.api.app.database import connect, init_db
from services.api.app.main import app, get_db
from services.api.app.repository import upsert_market_klines, list_market_klines, create_holding, create_watchlist_item, create_analysis_report


class IntradayKlineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(self.tmp.name) / "test.db"
        init_db(path)
        self.db = connect(path)
        self.kw = dict(symbol="600519", source="tdx-official", period="5min")
        self.bars = [dict(trade_date=f"2026-09-30T{clock}:00+08:00", open=10, high=11, low=9, close=10)
                     for clock in ("14:50", "14:55", "15:00")]

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.tmp.cleanup()

    def test_aliases_and_old_date_rows_do_not_consume_limit(self):
        for period in ["5m", "5min"]:
            upsert_market_klines(self.db, **{**self.kw, "period": period}, bars=self.bars)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM market_klines").fetchone()[0], 3)
        self.db.execute("INSERT INTO market_klines (symbol,source,period,trade_date,open,high,low,close,payload_json,fetched_at) VALUES ('600519','tdx-official','5min','2026-10-01',10,11,9,10,'{}','now')")
        rows = list_market_klines(self.db, **{**self.kw, "period": "5m"}, limit=3)
        self.assertEqual({x["trade_date"] for x in rows}, {x["trade_date"] for x in self.bars})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM market_klines").fetchone()[0], 4)

    def test_batch_conflict_is_atomic_but_later_revision_is_allowed(self):
        with self.assertRaises(ValueError):
            upsert_market_klines(self.db, **self.kw, bars=self.bars + [{**self.bars[0], "close": 11}])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM market_klines").fetchone()[0], 0)
        upsert_market_klines(self.db, **self.kw, bars=self.bars)
        result = upsert_market_klines(self.db, **self.kw, bars=[{**self.bars[0], "close": 11}])
        self.assertEqual(result[0]["close"], 11)
        self.assertEqual([x["trade_date"] for x in result], [self.bars[0]["trade_date"]])

    def test_invalid_late_row_leaves_no_partial_writes(self):
        for broken in ["2026-09-30", "2026-09-30T12:00:00+08:00"]:
            with self.assertRaises(ValueError):
                upsert_market_klines(self.db, **self.kw, bars=self.bars + [{**self.bars[0], "trade_date": broken}])
            self.assertEqual(self.db.execute("SELECT COUNT(*) FROM market_klines").fetchone()[0], 0)

    def test_api_fetch_and_cache_keep_metadata_and_personal_data(self):
        create_holding(self.db, {"symbol": "600519", "quantity": 100, "cost_price": 10})
        create_watchlist_item(self.db, {"symbol": "600519"})
        create_analysis_report(self.db, report_type="test", payload={"keep": True})
        tables = ["holdings", "watchlist", "analysis_reports"]
        before = {table: [tuple(r) for r in self.db.execute(f"SELECT * FROM {table}")] for table in tables}
        app.dependency_overrides[get_db] = lambda: self.db
        client = TestClient(app)
        bars = [{**self.bars[-1], "trade_date": f"2026-09-30T{clock}:00+08:00"} for clock in ("11:30", "14:00", "15:00")]
        provider = mock.Mock(name="provider")
        provider.name = "tdx-official"
        provider.fetch_kline.return_value = bars
        with mock.patch("services.api.app.main.get_market_data_provider", return_value=provider):
            response = client.get("/market/kline/600519?source=tdx-official&period=60m")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["period"], "60min")
        self.assertEqual(payload["count"], 3)
        self.assertEqual(payload["bars"][-1]["bar_end_at"], "2026-09-30T15:00:00+08:00")
        cached = client.get("/market/klines/600519?source=tdx-official&period=hour").json()
        self.assertEqual(cached, payload)
        self.assertEqual({table: [tuple(r) for r in self.db.execute(f"SELECT * FROM {table}")] for table in tables}, before)
        self.assertEqual(client.get("/market/kline/600519?period=invalid").status_code, 422)


if __name__ == "__main__":
    unittest.main()
