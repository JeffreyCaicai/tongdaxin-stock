from __future__ import annotations

import unittest

from services.api.app.reports import (
    generate_daily_review,
    generate_stock_report,
    generate_trading_plan,
)


class ReportTests(unittest.TestCase):
    def test_stock_report_includes_data_refs(self) -> None:
        report = generate_stock_report(
            symbol="600519",
            holding={
                "symbol": "600519",
                "cost_price": 100,
                "strategy_horizon": "swing",
                "initial_thesis": "Trend follow.",
                "stop_loss": 90,
            },
            quote={
                "snapshot_id": 1,
                "price": 105,
                "fetched_at": "2026-06-20T00:00:00+00:00",
            },
            indicators={
                "snapshot": {
                    "trend": "bullish",
                    "close": 105,
                    "as_of": "2026-06-20",
                    "bars": 80,
                    "ma": {"ma5": 104, "ma20": 100, "ma60": 98},
                    "macd": {"hist": 0.2},
                    "rsi14": 60,
                    "atr14": 2,
                    "volume_ratio": 1.2,
                }
            },
            recent_signals=[],
        )

        self.assertEqual(report["report_type"], "stock_diagnosis")
        self.assertEqual(report["symbol"], "600519")
        self.assertGreaterEqual(len(report["data_refs"]), 2)

    def test_trading_plan_uses_signal_evidence(self) -> None:
        report = generate_trading_plan(
            holding={"symbol": "000001", "stop_loss": 9, "take_profit": 12},
            quote={"snapshot_id": 2, "price": 10.5, "fetched_at": "now"},
            indicators={"snapshot": {"as_of": "2026-06-20", "bars": 80}},
            signal={
                "id": None,
                "symbol": "000001",
                "action": "hold",
                "risk_level": "low",
                "next_check": "Wait.",
                "reasons": ["No trigger."],
                "signal_type": "hold_observe",
                "created_at": None,
            },
        )

        self.assertEqual(report["report_type"], "trading_plan")
        self.assertEqual(report["plan"]["action_signal"], "hold")
        self.assertEqual(report["evidence"], ["No trigger."])

    def test_daily_review_counts_actions(self) -> None:
        report = generate_daily_review(
            holdings=[{"symbol": "600519"}],
            signals=[
                {
                    "symbol": "600519",
                    "action": "hold",
                    "risk_level": "low",
                    "signal_type": "hold_observe",
                    "price": 100,
                    "reasons": ["No trigger."],
                },
                {
                    "symbol": "000001",
                    "action": "review_risk",
                    "risk_level": "high",
                    "signal_type": "hard_stop_loss",
                    "price": 9,
                    "reasons": ["Below stop."],
                },
                {
                    "symbol": "000001",
                    "action": "review_risk",
                    "risk_level": "high",
                    "signal_type": "hard_stop_loss",
                    "price": 8.8,
                    "reasons": ["Still below stop."],
                },
            ],
            fetch_logs=[
                {"symbol": "600519", "status": "success"},
                {
                    "symbol": "000001",
                    "source": "tdx-official",
                    "data_type": "quote",
                    "status": "error",
                    "message": "timeout",
                },
            ],
        )

        self.assertEqual(report["report_type"], "daily_review")
        self.assertEqual(report["action_counts"]["hold"], 1)
        self.assertEqual(report["data_quality"]["failed_fetch_count"], 1)
        self.assertEqual(report["high_risk_symbols"], ["000001"])
        self.assertEqual(report["high_risk_signal_count"], 2)
        self.assertEqual(report["holding_details"][0]["symbol"], "600519")
        self.assertEqual(report["recent_signal_details"][0]["symbol"], "600519")
        self.assertEqual(report["high_risk_signal_details"][0]["symbol"], "000001")
        self.assertEqual(report["data_quality"]["failed_fetches"][0]["message"], "timeout")
        self.assertIn("check_data_quality", report["next_session_focus_keys"])


if __name__ == "__main__":
    unittest.main()
