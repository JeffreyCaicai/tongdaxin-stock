from __future__ import annotations

import unittest

from services.api.app.indicators import calculate_indicator_snapshot
from services.api.app.market_data import get_market_data_provider


class IndicatorTests(unittest.TestCase):
    def test_indicator_snapshot_contains_required_metrics(self) -> None:
        provider = get_market_data_provider("mock")
        bars = provider.fetch_kline("600519", limit=80)

        snapshot = calculate_indicator_snapshot(bars)

        self.assertEqual(snapshot["bars"], 80)
        self.assertIn("ma5", snapshot["ma"])
        self.assertIn("ma60", snapshot["ma"])
        self.assertIn("hist", snapshot["macd"])
        self.assertIsNotNone(snapshot["rsi14"])
        self.assertIsNotNone(snapshot["atr14"])
        self.assertIsNotNone(snapshot["volume_ma20"])
        self.assertIn(snapshot["trend"], {"bullish", "bearish", "neutral", "unknown"})


if __name__ == "__main__":
    unittest.main()
