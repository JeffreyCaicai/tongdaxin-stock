from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.api.app.database import connect, init_db
from services.api.app.repository import (
    create_analysis_report,
    create_backtest,
    create_holding,
    create_market_fetch_log,
    create_market_snapshot,
    create_signal,
    create_watchlist_item,
    delete_holding,
    get_holding,
    list_holdings,
    list_analysis_reports,
    list_backtests,
    list_market_fetch_logs,
    list_market_klines,
    list_market_snapshots,
    list_signals,
    list_watchlist,
    update_holding,
    upsert_market_klines,
)


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        init_db(self.db_path)
        self.connection = connect(self.db_path)

    def tearDown(self) -> None:
        self.connection.close()
        self.tmpdir.cleanup()

    def test_create_update_delete_holding(self) -> None:
        holding = create_holding(
            self.connection,
            {
                "symbol": " 600519 ",
                "name": "Kweichow Moutai",
                "market": "SH",
                "quantity": 100,
                "cost_price": 1500,
                "stop_loss": 1380,
                "take_profit": 1800,
                "max_loss_pct": 8,
            },
        )

        self.assertEqual(holding["symbol"], "600519")
        self.assertEqual(len(list_holdings(self.connection)), 1)

        updated = update_holding(
            self.connection,
            holding["id"],
            {"quantity": 120, "notes": "Raised position after plan review."},
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["quantity"], 120)
        saved = get_holding(self.connection, holding["id"])
        self.assertEqual(saved["notes"], "Raised position after plan review.")
        self.assertTrue(delete_holding(self.connection, holding["id"]))
        self.assertEqual(list_holdings(self.connection), [])

    def test_create_watchlist_item(self) -> None:
        item = create_watchlist_item(
            self.connection,
            {
                "symbol": "000001",
                "name": "Ping An Bank",
                "market": "SZ",
                "thesis": "Watch for sector confirmation.",
                "priority": 2,
            },
        )

        self.assertEqual(item["symbol"], "000001")
        self.assertEqual(list_watchlist(self.connection)[0]["priority"], 2)

    def test_list_signals_can_filter_by_symbol(self) -> None:
        create_signal(
            self.connection,
            symbol="600519",
            signal_type="hold_observe",
            action="hold",
            strength=0.35,
            price=1500,
            reason_json={
                "risk_level": "low",
                "reasons": ["No trigger."],
                "next_check": "Wait.",
                "extra": {},
            },
        )
        create_signal(
            self.connection,
            symbol="000001",
            signal_type="take_profit",
            action="trim_or_review",
            strength=0.85,
            price=12,
            reason_json={
                "risk_level": "medium",
                "reasons": ["Target reached."],
                "next_check": "Review.",
                "extra": {},
            },
        )

        signals = list_signals(self.connection, symbol="600519")

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["symbol"], "600519")

    def test_market_snapshot_and_fetch_log_are_persisted(self) -> None:
        snapshot = create_market_snapshot(
            self.connection,
            symbol="600519",
            source="mock",
            payload={"price": 1500.5},
        )
        log = create_market_fetch_log(
            self.connection,
            symbol="600519",
            source="mock",
            data_type="quote",
            status="success",
        )

        self.assertEqual(snapshot["symbol"], "600519")
        self.assertEqual(log["status"], "success")
        self.assertEqual(len(list_market_snapshots(self.connection, symbol="600519")), 1)
        self.assertEqual(len(list_market_fetch_logs(self.connection, symbol="600519")), 1)

    def test_market_klines_are_upserted(self) -> None:
        bars = [
            {
                "trade_date": "2026-06-19",
                "open": 10,
                "high": 11,
                "low": 9.8,
                "close": 10.5,
                "volume": 1000,
                "amount": 10500,
            },
            {
                "trade_date": "2026-06-20",
                "open": 10.5,
                "high": 11.2,
                "low": 10.1,
                "close": 11,
                "volume": 1200,
                "amount": 13200,
            },
        ]

        upsert_market_klines(
            self.connection,
            symbol="000001",
            source="mock",
            period="daily",
            bars=bars,
        )
        upsert_market_klines(
            self.connection,
            symbol="000001",
            source="mock",
            period="daily",
            bars=[{**bars[0], "close": 10.8}],
        )

        saved = list_market_klines(
            self.connection, symbol="000001", source="mock", period="daily"
        )

        self.assertEqual(len(saved), 2)
        self.assertEqual(saved[-1]["close"], 10.8)

    def test_analysis_report_is_persisted(self) -> None:
        report = create_analysis_report(
            self.connection,
            report_type="daily_review",
            symbol=None,
            payload={"summary": "Reviewed."},
        )

        saved = list_analysis_reports(self.connection, report_type="daily_review")

        self.assertEqual(report["report_type"], "daily_review")
        self.assertEqual(len(saved), 1)
        self.assertIn("Reviewed", saved[0]["payload_json"])

    def test_backtest_is_persisted(self) -> None:
        backtest = create_backtest(
            self.connection,
            symbol="600519",
            source="mock",
            strategy_name="ma_volume_trend_v1",
            config={"limit": 120},
            result={"metrics": {"win_rate": 0.5}},
        )

        saved = list_backtests(
            self.connection,
            symbol="600519",
            strategy_name="ma_volume_trend_v1",
        )

        self.assertEqual(backtest["symbol"], "600519")
        self.assertEqual(len(saved), 1)
        self.assertIn("win_rate", saved[0]["result_json"])


if __name__ == "__main__":
    unittest.main()
