from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.run_api import FallbackHandler, _workbench_actions_from_market
from services.api.app.database import connect, init_db
from services.api.app.repository import create_holding, create_signal, get_default_stock_pool


class FallbackScopeTests(unittest.TestCase):
    def test_unscoped_actions_still_include_holdings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fallback.db"
            init_db(path)
            with connect(path) as db:
                create_holding(db, {"symbol": "600519", "quantity": 100, "cost_price": 10})
                result = _workbench_actions_from_market(db, {"source": "mock", "persist": False})
                self.assertEqual(result["total_holdings"], 1)

    def test_empty_pool_daily_review_does_not_show_external_signals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fallback.db"
            init_db(path)
            with connect(path) as db:
                pool = get_default_stock_pool(db)
                create_holding(db, {"symbol": "600519", "quantity": 100, "cost_price": 10})
                create_signal(db, symbol="600519", signal_type="hold_observe", action="hold",
                              strength=.2, price=10, reason_json={"risk_level": "low", "reasons": [],
                                                                "next_check": "wait", "extra": {}})
                handler = object.__new__(FallbackHandler)
                handler.path = f"/reports/daily-review?pool_id={pool['id']}"
                outputs = []
                handler._send_json = lambda value, **kwargs: outputs.append(value)
                with mock.patch("scripts.run_api.connect", return_value=db):
                    handler.do_GET()
                self.assertEqual(outputs[0]["holding_count"], 0)
                self.assertEqual(outputs[0]["signal_count"], 0)


if __name__ == "__main__":
    unittest.main()
