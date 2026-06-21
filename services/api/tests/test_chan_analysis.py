from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from fastapi import HTTPException

from services.api.app.chan_analysis import analyze_chan_structure
from services.api.app.database import connect, init_db
from services.api.app.main import api_analyze_stock_pool_with_chan
from services.api.app.repository import (
    create_watchlist_item,
    get_default_stock_pool,
)
from services.api.app.schemas import StockPoolChanAnalysisRequest


def zigzag_bars() -> list[dict]:
    pivots = [
        (0, 10.0),
        (5, 16.0),
        (10, 12.0),
        (15, 18.0),
        (20, 13.0),
        (25, 19.0),
        (30, 14.0),
        (35, 20.0),
        (40, 17.0),
    ]
    prices: dict[int, float] = {}
    for (start_index, start_price), (end_index, end_price) in zip(pivots, pivots[1:]):
        span = end_index - start_index
        for offset in range(span):
            index = start_index + offset
            prices[index] = start_price + ((end_price - start_price) * offset / span)
    prices[pivots[-1][0]] = pivots[-1][1]

    start = date(2026, 1, 1)
    bars: list[dict] = []
    for index in sorted(prices):
        price = prices[index]
        bars.append(
            {
                "trade_date": (start + timedelta(days=index)).isoformat(),
                "open": price - 0.05,
                "high": price + 0.2,
                "low": price - 0.2,
                "close": price,
                "volume": 1000 + index,
            }
        )
    return bars


class ChanAnalysisTests(unittest.TestCase):
    def test_analyze_chan_structure_returns_explainable_signal(self) -> None:
        analysis = analyze_chan_structure(
            symbol="688630",
            name="芯碁微装",
            bars=zigzag_bars(),
        )

        self.assertEqual(analysis["symbol"], "688630")
        self.assertGreaterEqual(analysis["fractal_count"], 6)
        self.assertGreaterEqual(analysis["stroke_count"], 5)
        self.assertGreaterEqual(analysis["center_count"], 1)
        self.assertIn("type", analysis["signal"])
        self.assertIn("reason", analysis["signal"])
        self.assertIn("latest_strokes", analysis)

    def test_far_above_old_center_waits_for_new_structure(self) -> None:
        bars = zigzag_bars()
        bars.append(
            {
                "trade_date": "2026-02-15",
                "open": 60.0,
                "high": 62.0,
                "low": 59.0,
                "close": 61.5,
                "volume": 2000,
            }
        )

        analysis = analyze_chan_structure(
            symbol="688323",
            name="瑞华泰",
            bars=bars,
        )

        self.assertEqual(analysis["structure"], "远离中枢上方")
        self.assertEqual(analysis["signal"]["type"], "extended_above_center")
        self.assertIn("旧中枢", analysis["signal"]["reason"])
        self.assertIn("等待当前价附近形成新中枢", analysis["signal"]["trigger"])
        self.assertNotIn("回踩不跌回", analysis["signal"]["trigger"])

    def test_stock_pool_chan_api_uses_watchlist_scope_and_reports_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_db(db_path)
            connection = connect(db_path)
            try:
                pool = get_default_stock_pool(connection)
                create_watchlist_item(
                    connection,
                    {"pool_id": pool["id"], "symbol": "603337", "name": "杰克科技", "priority": 2},
                )
                create_watchlist_item(
                    connection,
                    {"pool_id": pool["id"], "symbol": "688630", "name": "芯碁微装", "priority": 1},
                )
                calls: list[str] = []

                def fake_fetch_kline(_db, *, symbol: str, source: str, period: str, limit: int) -> dict:
                    calls.append(symbol)
                    if symbol == "603337":
                        raise HTTPException(status_code=502, detail="kline failed")
                    return {
                        "symbol": symbol,
                        "source": source,
                        "period": period,
                        "count": len(zigzag_bars()),
                        "bars": zigzag_bars(),
                    }

                with mock.patch(
                    "services.api.app.main._fetch_kline_and_cache",
                    side_effect=fake_fetch_kline,
                ):
                    report = api_analyze_stock_pool_with_chan(
                        int(pool["id"]),
                        StockPoolChanAnalysisRequest(
                            source="tdx-official",
                            period="daily",
                            persist=False,
                            max_symbols=2,
                            kline_limit=240,
                        ),
                        connection,
                    )

                payload = report["payload"]
                self.assertEqual(calls, ["688630", "603337"])
                self.assertEqual(payload["report_type"], "stock_pool_chan_analysis")
                self.assertEqual(payload["data_quality"]["failed_symbols"], ["603337"])
                self.assertEqual(len(payload["items"]), 2)
                self.assertEqual(payload["items"][0]["symbol"], "688630")
                self.assertIn("reason", payload["items"][0]["signal"])
                self.assertEqual(payload["items"][1]["signal"]["type"], "complete_market_data")
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
