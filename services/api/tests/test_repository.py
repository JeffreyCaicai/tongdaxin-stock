from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.api.app.database import connect, init_db
from services.api.app.repository import (
    create_holding,
    create_signal,
    create_watchlist_item,
    delete_holding,
    get_holding,
    list_holdings,
    list_signals,
    list_watchlist,
    update_holding,
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


if __name__ == "__main__":
    unittest.main()
