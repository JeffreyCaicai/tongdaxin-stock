from __future__ import annotations

import unittest

from services.api.app.market_data import (
    MarketDataError,
    get_market_data_provider,
)


class MarketDataProviderTests(unittest.TestCase):
    def test_mock_quote_is_normalized_and_repeatable(self) -> None:
        provider = get_market_data_provider("mock")

        quote = provider.fetch_quote(" 600519 ")
        same_quote = provider.fetch_quote("600519")

        self.assertEqual(quote["symbol"], "600519")
        self.assertEqual(quote["price"], same_quote["price"])
        self.assertTrue(quote["is_mock"])

    def test_mock_kline_returns_requested_count(self) -> None:
        provider = get_market_data_provider("mock")

        bars = provider.fetch_kline("000001", limit=7)

        self.assertEqual(len(bars), 7)
        self.assertLessEqual(bars[0]["trade_date"], bars[-1]["trade_date"])
        self.assertIn("close", bars[0])

    def test_unknown_provider_raises_clear_error(self) -> None:
        with self.assertRaises(MarketDataError):
            get_market_data_provider("missing")

    def test_akshare_provider_reports_missing_optional_dependency(self) -> None:
        provider = get_market_data_provider("akshare")

        with self.assertRaisesRegex(MarketDataError, "AkShare is not installed"):
            provider.fetch_quote("600519")


if __name__ == "__main__":
    unittest.main()
