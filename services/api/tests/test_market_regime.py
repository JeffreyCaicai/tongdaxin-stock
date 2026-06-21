from __future__ import annotations

import unittest
from datetime import date, timedelta

from services.api.app.market_regime import infer_market_regime


def trend_bars(
    *,
    start_price: float,
    days: int = 120,
    step: float = 4.0,
    volume: float = 1000,
) -> list[dict]:
    start = date(2026, 1, 1)
    bars: list[dict] = []
    for index in range(days):
        close = start_price + index * step
        bars.append(
            {
                "trade_date": (start + timedelta(days=index)).isoformat(),
                "open": close - step * 0.25,
                "high": close + max(step, 1),
                "low": close - max(step, 1),
                "close": close,
                "volume": volume + index * 8,
            }
        )
    return bars


def volatile_down_bars() -> list[dict]:
    start = date(2026, 1, 1)
    price = 3600.0
    bars: list[dict] = []
    for index in range(120):
        price -= 7 + (index % 5) * 2
        high = price + 35 + (index % 4) * 12
        low = price - 45 - (index % 3) * 15
        bars.append(
            {
                "trade_date": (start + timedelta(days=index)).isoformat(),
                "open": price + 12,
                "high": high,
                "low": low,
                "close": price,
                "volume": 2000 + index * 30,
            }
        )
    return bars


class MarketRegimeTests(unittest.TestCase):
    def test_identifies_uptrend_with_positive_breadth(self) -> None:
        regime = infer_market_regime(
            index_bars=trend_bars(start_price=3000),
            pool_quotes={
                "688630": {"pct_change": 1.8},
                "603337": {"pct_change": 0.7},
                "688323": {"pct_change": 2.2},
            },
            pool_kline_by_symbol={
                "688630": trend_bars(start_price=50, step=0.5),
                "603337": trend_bars(start_price=18, step=0.2),
            },
        )

        self.assertEqual(regime["regime"], "uptrend")
        self.assertIn(regime["confidence"], {"medium", "high"})
        self.assertGreater(regime["strategy_bias"]["weights"]["trend"], 1)
        self.assertGreater(regime["strategy_bias"]["weights"]["breakout"], 1)
        self.assertIn("指数趋势", {entry["source"] for entry in regime["evidence"]})

    def test_identifies_high_volatility_pressure(self) -> None:
        regime = infer_market_regime(
            index_bars=volatile_down_bars(),
            pool_quotes={
                "688630": {"pct_change": -4.2},
                "603337": {"pct_change": -2.6},
                "688323": {"pct_change": -1.7},
                "600519": {"pct_change": 0.1},
            },
            pool_kline_by_symbol={},
        )

        self.assertEqual(regime["regime"], "high_volatility_pressure")
        self.assertGreater(regime["strategy_bias"]["weights"]["risk"], 1)
        self.assertLess(regime["strategy_bias"]["weights"]["breakout"], 1)
        self.assertIn("波动压力", {entry["source"] for entry in regime["evidence"]})


if __name__ == "__main__":
    unittest.main()
