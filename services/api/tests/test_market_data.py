from __future__ import annotations

import unittest

from services.api.app.market_data import (
    MarketDataError,
    _eastmoney_price,
    _eastmoney_secid,
    _tdx_code,
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

    def test_eastmoney_helpers_normalize_market_and_price(self) -> None:
        self.assertEqual(_eastmoney_secid("600519"), "1.600519")
        self.assertEqual(_eastmoney_secid("688630"), "1.688630")
        self.assertEqual(_eastmoney_secid("000001"), "0.000001")
        self.assertEqual(_eastmoney_price(50200), 502.0)

    def test_eastmoney_provider_can_be_selected_without_optional_dependency(self) -> None:
        provider = get_market_data_provider("eastmoney")

        self.assertEqual(provider.name, "eastmoney")

    def test_tongdaxin_provider_is_primary_source_alias(self) -> None:
        provider = get_market_data_provider("tongdaxin")

        self.assertEqual(provider.name, "eltdx")
        self.assertEqual(_tdx_code("600519"), "sh600519")
        self.assertEqual(_tdx_code("000001"), "sz000001")

    def test_akshare_provider_reports_missing_optional_dependency(self) -> None:
        provider = get_market_data_provider("akshare")

        with self.assertRaisesRegex(MarketDataError, "AkShare is not installed"):
            provider.fetch_quote("600519")


if __name__ == "__main__":
    unittest.main()
