from __future__ import annotations

import unittest

from services.api.app.signal_engine import evaluate_holding_signal


class SignalEngineTests(unittest.TestCase):
    def test_hard_stop_loss_has_high_risk_exit_action(self) -> None:
        holding = {
            "symbol": "600519",
            "cost_price": 100,
            "stop_loss": 92,
            "take_profit": 125,
            "max_loss_pct": 6,
        }

        signal = evaluate_holding_signal(holding, current_price=91)

        self.assertEqual(signal["signal_type"], "hard_stop_loss")
        self.assertEqual(signal["action"], "exit_or_reduce")
        self.assertEqual(signal["risk_level"], "high")

    def test_take_profit_signal(self) -> None:
        holding = {
            "symbol": "000001",
            "cost_price": 10,
            "stop_loss": 9,
            "take_profit": 12,
            "max_loss_pct": 8,
        }

        signal = evaluate_holding_signal(holding, current_price=12.1)

        self.assertEqual(signal["signal_type"], "take_profit")
        self.assertEqual(signal["action"], "trim_or_review")

    def test_hold_observe_when_no_rule_fires(self) -> None:
        holding = {
            "symbol": "300750",
            "cost_price": 200,
            "stop_loss": 180,
            "take_profit": 260,
            "max_loss_pct": 8,
        }

        signal = evaluate_holding_signal(holding, current_price=205)

        self.assertEqual(signal["signal_type"], "hold_observe")
        self.assertEqual(signal["action"], "hold")
        self.assertEqual(signal["risk_level"], "low")


if __name__ == "__main__":
    unittest.main()
