from __future__ import annotations

import json
import os
import unittest
from unittest import mock

from services.api.app.market_data import (
    MarketDataError,
    _eastmoney_price,
    _eastmoney_secid,
    _tdx_code,
    _tdx_official_period,
    _tdx_official_setcode,
    get_market_data_provider,
)


class FakeHttpResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


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

    def test_tdx_official_provider_builds_token_quote_request(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["headers"] = dict(request.header_items())
            return FakeHttpResponse(
                {
                    "BaseInfo": {"Code": "600519", "Name": "贵州茅台"},
                    "HQInfo": {
                        "Now": 1215,
                        "Close": 1200,
                        "Open": 1201,
                        "High": 1220,
                        "Low": 1190,
                        "Volume": 10000,
                        "Amount": 12150000,
                    },
                    "CalcInfo": {"CAZAF": 1.25},
                }
            )

        with mock.patch.dict(
            os.environ,
            {
                "TDX_API_KEY": "unit-token",
                "TDX_API_DATA_ENDPOINT": "http://tdx.test/TQLEX",
            },
            clear=True,
        ), mock.patch("services.api.app.market_data.urlopen", fake_urlopen):
            provider = get_market_data_provider("tdx-official")
            quote = provider.fetch_quote("600519")

        self.assertEqual(provider.name, "tdx-official")
        self.assertEqual(captured["url"], "http://tdx.test/TQLEX?Entry=TdxShare.PBHQInfo")
        self.assertEqual(captured["timeout"], 15)
        self.assertEqual(captured["body"]["Code"], "600519")
        self.assertEqual(captured["body"]["Setcode"], "1")
        headers = {str(key).lower(): value for key, value in captured["headers"].items()}
        self.assertEqual(headers["token"], "unit-token")
        self.assertEqual(quote["name"], "贵州茅台")
        self.assertEqual(quote["price"], 1215.0)
        self.assertEqual(quote["pct_change"], 1.25)

    def test_tdx_official_provider_normalizes_kline_items(self) -> None:
        def fake_urlopen(request, timeout=None):  # type: ignore[no-untyped-def]
            body = json.loads(request.data.decode("utf-8"))
            self.assertEqual(body["Period"], 4)
            self.assertEqual(body["WantNum"], 2)
            return FakeHttpResponse(
                {
                    "ListItem": [
                        {"Item": [20240619, 0, 10, 11, 9.8, 10.5, 1000, 10500]},
                        {"Item": [20240620, 0, 10.5, 12, 10.2, 11.8, 2000, 23600]},
                    ]
                }
            )

        with mock.patch.dict(
            os.environ,
            {
                "TDX_API_KEY": "unit-token",
                "TDX_API_DATA_ENDPOINT": "http://tdx.test/TQLEX",
            },
            clear=True,
        ), mock.patch("services.api.app.market_data.urlopen", fake_urlopen):
            bars = get_market_data_provider("openclaw").fetch_kline("000001", limit=2)

        self.assertEqual(len(bars), 2)
        self.assertEqual(bars[0]["trade_date"], "2024-06-19")
        self.assertEqual(bars[0]["open"], 10.0)
        self.assertEqual(bars[1]["close"], 11.8)
        self.assertEqual(bars[1]["amount"], 23600.0)

    def test_tdx_official_helpers_map_market_and_period(self) -> None:
        self.assertEqual(_tdx_official_setcode("600519"), "1")
        self.assertEqual(_tdx_official_setcode("688630"), "1")
        self.assertEqual(_tdx_official_setcode("000001"), "0")
        self.assertEqual(_tdx_official_setcode("300750"), "0")
        self.assertEqual(_tdx_official_setcode("832000"), "2")
        self.assertEqual(_tdx_official_period("daily"), "4")
        self.assertEqual(_tdx_official_period("weekly"), "5")
        self.assertEqual(_tdx_official_period("monthly"), "6")

    def test_tdx_official_provider_reports_missing_token(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            provider = get_market_data_provider("tdx-token")

            with self.assertRaisesRegex(MarketDataError, "TDX_API_KEY is not configured"):
                provider.fetch_quote("600519")

    def test_akshare_provider_reports_missing_optional_dependency(self) -> None:
        provider = get_market_data_provider("akshare")

        with self.assertRaisesRegex(MarketDataError, "AkShare is not installed"):
            provider.fetch_quote("600519")


if __name__ == "__main__":
    unittest.main()
