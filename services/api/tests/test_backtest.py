from __future__ import annotations

import unittest

from services.api.app.backtest import (
    run_ma_volume_backtest,
    review_signal_outcomes,
)
from services.api.app.market_data import get_market_data_provider


class BacktestTests(unittest.TestCase):
    def test_run_ma_volume_backtest_returns_metrics(self) -> None:
        provider = get_market_data_provider("mock")
        bars = provider.fetch_kline("600519", limit=160)

        result = run_ma_volume_backtest(symbol="600519", bars=bars)

        self.assertEqual(result["strategy_name"], "ma_volume_trend_v1")
        self.assertEqual(result["bar_count"], 160)
        self.assertIn("win_rate", result["metrics"])
        self.assertIn("max_drawdown_pct", result["metrics"])
        self.assertIn("risk_reward_ratio", result["metrics"])
        self.assertIn("trades", result)

    def test_review_signal_outcomes_marks_favorable_move(self) -> None:
        reviews = review_signal_outcomes(
            signals=[
                {
                    "id": 1,
                    "symbol": "000001",
                    "action": "hold",
                    "signal_type": "hold_observe",
                    "price": 10,
                }
            ],
            latest_prices={"000001": 10.2},
        )

        self.assertEqual(reviews[0]["outcome"], "favorable")
        self.assertEqual(reviews[0]["move_pct"], 2.0)


if __name__ == "__main__":
    unittest.main()
