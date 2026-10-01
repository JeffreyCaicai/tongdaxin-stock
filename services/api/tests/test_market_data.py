from __future__ import annotations

import json
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

from services.api.app.market_data import (
    MarketDataError,
    _eastmoney_price,
    _eastmoney_secid,
    _required_float,
    _safe_float,
    _tdx_code,
    _tdx_official_period,
    _tdx_official_setcode,
    get_market_data_provider,
    search_stock_candidates,
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

    def test_stock_search_normalizes_eastmoney_candidates(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout=None):  # type: ignore[no-untyped-def]
            captured["url"] = request.full_url
            return FakeHttpResponse(
                {
                    "QuotationCodeTable": {
                        "Data": [
                            {"Code": "600519", "Name": "贵州茅台", "MarketType": "SH"},
                            {"Code": "HK0001", "Name": "Not A Share"},
                            {"Code": "688630", "Name": "芯碁微装", "MarketType": "SH"},
                        ]
                    }
                }
            )

        with mock.patch("services.api.app.market_data.urlopen", fake_urlopen):
            candidates = search_stock_candidates("茅台", limit=5)

        self.assertIn("searchapi.eastmoney.com", str(captured["url"]))
        self.assertEqual([item["symbol"] for item in candidates], ["600519", "688630"])
        self.assertEqual(candidates[0]["name"], "贵州茅台")
        self.assertEqual(candidates[0]["source"], "eastmoney-search")

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

        with mock.patch(
            "services.api.app.market_data.get_tdx_api_key", return_value="unit-token"
        ), mock.patch(
            "services.api.app.market_data.get_tdx_api_endpoint", return_value="http://tdx.test/TQLEX"
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

    def test_tdx_official_provider_reads_actual_hq_extremes_and_exchange_clock(self) -> None:
        for day, time_value, expected in [
            ("20260930", "153002", "2026-09-30T15:30:02+08:00"),
            (20260930, 93001, "2026-09-30T09:30:01+08:00"),
            ("20260930", None, None), ("20260230", "153002", None),
        ]:
            with self.subTest(day=day, time_value=time_value):
                payload = {"BaseInfo": {"Code": "688630", "Name": "Example"},
                           "HQInfo": {"Now": 388.68, "Close": 397.17, "MaxP": 404.97,
                                      "MinP": 384.05, "HQDate": day, "HQTime": time_value}}
                with mock.patch("services.api.app.market_data._tdx_official_post", return_value=payload):
                    quote = get_market_data_provider("tdx-official").fetch_quote("688630")
                self.assertEqual(quote["high"], 404.97)
                self.assertEqual(quote["low"], 384.05)
                self.assertEqual(quote["market_time"], expected)

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

        with mock.patch(
            "services.api.app.market_data.get_tdx_api_key", return_value="unit-token"
        ), mock.patch(
            "services.api.app.market_data.get_tdx_api_endpoint", return_value="http://tdx.test/TQLEX"
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
        with mock.patch("services.api.app.market_data.get_tdx_api_key", return_value=None):
            provider = get_market_data_provider("tdx-token")

            with self.assertRaisesRegex(MarketDataError, "TDX_API_KEY is not configured"):
                provider.fetch_quote("600519")

    def test_akshare_provider_reports_missing_optional_dependency(self) -> None:
        provider = get_market_data_provider("akshare")

        with self.assertRaisesRegex(MarketDataError, "AkShare is not installed"):
            provider.fetch_quote("600519")

    def test_official_requests_use_bare_code_and_explicit_market(self) -> None:
        cases = [
            ("SH000300", "SH000300", "000300", "1", "SH", "index"),
            (" sh000300 ", "SH000300", "000300", "1", "SH", "index"),
            ("1.000300", "SH000300", "000300", "1", "SH", "index"),
            ("SH000001", "SH000001", "000001", "1", "SH", "index"),
            ("sz399001", "SZ399001", "399001", "0", "SZ", "index"),
            ("0.399001", "SZ399001", "399001", "0", "SZ", "index"),
            ("bj832000", "BJ832000", "832000", "2", "BJ", "stock"),
            ("2.832000", "BJ832000", "832000", "2", "BJ", "stock"),
            ("000001", "000001", "000001", "0", "SZ", "stock"),
            ("000300", "000300", "000300", "0", "SZ", "stock"),
            ("600519", "600519", "600519", "1", "SH", "stock"),
        ]
        for requested, canonical, code, setcode, market, kind in cases:
            with self.subTest(symbol=requested):
                requests = []

                def fake_urlopen(request, timeout=None):
                    requests.append((request.full_url, json.loads(request.data)))
                    if "PBHQInfo" in request.full_url:
                        return FakeHttpResponse({"HQInfo": {"Now": 3500}})
                    return FakeHttpResponse({"ListItem": [
                        {"Item": [20240620, 0, 3500, 3510, 3490, 3505, 1000, 3505000]}
                    ]})

                with mock.patch(
                    "services.api.app.market_data.get_tdx_api_key", return_value="unit-token"
                ), mock.patch(
                    "services.api.app.market_data.get_tdx_api_endpoint", return_value="http://tdx.test/TQLEX"
                ), mock.patch("services.api.app.market_data.urlopen", fake_urlopen):
                    provider = get_market_data_provider("tdx-official")
                    quote = provider.fetch_quote(requested)
                    bars = provider.fetch_kline(requested, limit=1)

                self.assertIn("PBFXT", requests[1][0])
                self.assertEqual(requests[0][1]["Code"], code)
                self.assertEqual(requests[0][1]["Setcode"], setcode)
                self.assertEqual(requests[1][1]["Code"], code)
                self.assertEqual(requests[1][1]["Setcode"], int(setcode))
                for result in [quote, bars[0]]:
                    self.assertEqual(result["symbol"], canonical)
                    self.assertEqual(result.get("market"), market)
                    self.assertEqual(result.get("instrument_type"), kind)

    def test_eltdx_requests_route_index_kind_without_changing_plain_stocks(self) -> None:
        cases = [
            ("SH000300", "SH000300", "sh000300", "SH", "index"),
            ("sh000300", "SH000300", "sh000300", "SH", "index"),
            ("1.000300", "SH000300", "sh000300", "SH", "index"),
            ("sz399001", "SZ399001", "sz399001", "SZ", "index"),
            ("bj832000", "BJ832000", "bj832000", "BJ", "stock"),
            ("000001", "000001", "sz000001", "SZ", "stock"),
            ("600519", "600519", "sh600519", "SH", "stock"),
        ]
        for requested, canonical, code, market, kind in cases:
            with self.subTest(symbol=requested):
                captured = {}

                class FakeTdxClient:
                    def __init__(self, *, timeout):
                        pass

                    def __enter__(self):
                        return self

                    def __exit__(self, *_args):
                        pass

                    def get_quote(self, codes):
                        captured["quotes"] = codes
                        return [{"price": 3500}]

                    def get_kline(self, period, code, *, count, kind="stock"):
                        captured["kline"] = (period, code, count, kind)
                        return [{"date": "2024-06-20", "open": 3500, "high": 3510,
                                 "low": 3490, "close": 3505}]

                with mock.patch(
                    "services.api.app.market_data._load_eltdx", return_value=(FakeTdxClient, None)
                ):
                    provider = get_market_data_provider("eltdx")
                    quote = provider.fetch_quote(requested)
                    bars = provider.fetch_kline(requested, limit=1)

                self.assertEqual(captured["quotes"], [code])
                self.assertEqual(captured["kline"], ("day", code, 1, kind))
                for result in [quote, bars[0]]:
                    self.assertEqual(result["symbol"], canonical)
                    self.assertEqual(result.get("market"), market)
                    self.assertEqual(result.get("instrument_type"), kind)

    def test_eastmoney_requests_use_qualified_secid_and_canonical_identity(self) -> None:
        cases = [
            ("SH000300", "SH000300", "1.000300", "SH", "index"),
            ("sh000300", "SH000300", "1.000300", "SH", "index"),
            ("1.000300", "SH000300", "1.000300", "SH", "index"),
            ("sz399001", "SZ399001", "0.399001", "SZ", "index"),
            ("bj832000", "BJ832000", "0.832000", "BJ", "stock"),
            ("000001", "000001", "0.000001", "SZ", "stock"),
            ("600519", "600519", "1.600519", "SH", "stock"),
        ]
        for requested, canonical, secid, market, kind in cases:
            with self.subTest(symbol=requested):
                captured = []

                def fake_urlopen(request, timeout=None):
                    captured.append(parse_qs(urlparse(request.full_url).query)["secid"][0])
                    return FakeHttpResponse({"data": {
                        "f43": 350000,
                        "klines": ["2024-06-20,3500,3505,3510,3490,1000,3505000,1,1,5,0"]
                    }})

                with mock.patch("services.api.app.market_data.urlopen", fake_urlopen):
                    provider = get_market_data_provider("eastmoney")
                    quote = provider.fetch_quote(requested)
                    bars = provider.fetch_kline(requested, limit=1)

                self.assertEqual(captured, [secid, secid])
                for result in [quote, bars[0]]:
                    self.assertEqual(result["symbol"], canonical)
                    self.assertEqual(result.get("market"), market)
                    self.assertEqual(result.get("instrument_type"), kind)

    def test_mock_benchmark_aliases_share_canonical_identity(self) -> None:
        provider = get_market_data_provider("mock")
        quote = provider.fetch_quote("1.000300")
        bars = provider.fetch_kline("sh000300", limit=1)
        self.assertEqual(quote["symbol"], "SH000300")
        self.assertEqual(quote["price"], provider.fetch_quote("SH000300")["price"])
        self.assertEqual(bars[0]["symbol"], "SH000300")
        self.assertEqual(quote["market"], "SH")
        self.assertEqual(bars[0]["instrument_type"], "index")

    def test_required_price_parser_rejects_nonfinite_and_nonpositive_values(self) -> None:
        for value in [float("nan"), float("inf"), -float("inf"), "NaN", "inf", "-inf", 0, "0", -1]:
            with self.subTest(value=value):
                with self.assertRaises(MarketDataError):
                    _required_float(value, "price")
        self.assertEqual(_required_float("0.01", "price"), 0.01)
        self.assertEqual(_safe_float(0), 0)

    def test_providers_reject_invalid_required_prices_but_allow_zero_volume(self) -> None:
        class FakeFrame:
            empty = False

            def __init__(self, data):
                self.data = data

            def __getitem__(self, key):
                return self

            @property
            def loc(self):
                return self

            @property
            def iloc(self):
                return self

            def to_dict(self):
                return self.data

            def tail(self, limit):
                return self

            def iterrows(self):
                return iter([(0, self)])

        for source in ["tdx-official", "eltdx", "eastmoney", "akshare"]:
            for field in ["price", "open", "high", "low", "close"]:
                for value in [float("nan"), float("inf"), -float("inf"), "NaN", "inf", 0, -1, 10]:
                    with self.subTest(source=source, field=field, value=value):
                        row = {"open": 10, "high": 11, "low": 9, "close": 10,
                               "price": 10, "volume": 0, "date": "2024-06-20"}
                        row[field] = value

                        def fake_urlopen(request, timeout=None):
                            if source == "tdx-official":
                                return FakeHttpResponse({
                                    "HQInfo": {"Now": row["price"], "Volume": 0},
                                    "ListItem": [{"TradeDate": "2024-06-20", **row}],
                                })
                            return FakeHttpResponse({"data": {
                                "f43": row["price"] * 100 if isinstance(row["price"], (int, float)) else row["price"],
                                "f47": 0,
                                "klines": [",".join(str(item) for item in [
                                    "2024-06-20", row["open"], row["close"], row["high"], row["low"],
                                    0, 0, 0, 0, 0, 0
                                ])],
                            }})

                        class FakeTdxClient:
                            def __init__(self, **kwargs):
                                pass

                            def __enter__(self):
                                return self

                            def __exit__(self, *_args):
                                pass

                            def get_quote(self, codes):
                                return [row]

                            def get_kline(self, *args, **kwargs):
                                return [row]

                        akshare = mock.Mock()
                        akshare.stock_zh_a_spot_em.return_value = FakeFrame({
                            "最新价": row["price"], "成交量": 0
                        })
                        akshare.stock_zh_a_hist.return_value = FakeFrame({
                            "日期": "2024-06-20", "开盘": row["open"], "最高": row["high"],
                            "最低": row["low"], "收盘": row["close"], "成交量": 0
                        })
                        with mock.patch(
                            "services.api.app.market_data.get_tdx_api_key", return_value="unit-token"
                        ), mock.patch(
                            "services.api.app.market_data.get_tdx_api_endpoint", return_value="http://tdx.test/TQLEX"
                        ), mock.patch("services.api.app.market_data.urlopen", fake_urlopen), mock.patch(
                            "services.api.app.market_data._load_eltdx", return_value=(FakeTdxClient, None)
                        ), mock.patch("services.api.app.market_data._load_akshare", return_value=akshare):
                            provider = get_market_data_provider(source)
                            if value != 10:
                                with self.assertRaises(MarketDataError):
                                    if field == "price":
                                        provider.fetch_quote("600519")
                                    else:
                                        provider.fetch_kline("600519", limit=1)
                            else:
                                result = provider.fetch_quote("600519") if field == "price" else provider.fetch_kline("600519", limit=1)[0]
                                self.assertEqual(result["volume"], 0)
                                json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
