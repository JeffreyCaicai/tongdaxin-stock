from __future__ import annotations

import json
import unittest
from unittest import mock

from services.api.app.chan_capture import capture_dataset
from services.api.app.chan_replay import replay_symbol
from services.api.app.market_data import MarketDataError, get_market_data_provider
from services.api.tests.chan_validation_cases import candidate_bars, daily_bar


class ChanCaptureTests(unittest.TestCase):
    def capture_official(self, bars):
        rows = [{"Item": [bar["trade_date"].replace("-", ""), "0",
                           *[bar.get(key) for key in ("open", "high", "low", "close", "volume", "amount")]]}
                for bar in bars]
        with mock.patch("services.api.app.market_data._tdx_official_post", return_value={"ListItem": rows}), \
             mock.patch("services.api.app.chan_capture.time.sleep"):
            return capture_dataset(symbols=["600519"], periods=["daily"],
                                   as_of="2026-02-15T15:00:00+08:00")

    def test_official_future_bad_prices_do_not_change_historical_replay(self):
        bars = candidate_bars()
        first = self.capture_official(bars)["series"]["600519"]["daily"]
        baseline = replay_symbol(symbol="600519", bars=first["bars"], quality_issues=first["issues"],
                                 as_of="2026-02-15T15:00:00+08:00")
        self.assertEqual(len(baseline["observations"]), 1)
        for future in [daily_bar("2026-02-16", high=9), *[
                {**daily_bar("2026-02-16"), "close": value} for value in (None, True, float("nan"))]]:
            with self.subTest(future=future):
                data = self.capture_official(bars + [future, daily_bar("2026-02-16", 100)])
                series = data["series"]["600519"]["daily"]
                self.assertEqual(series, first)
                self.assertEqual(replay_symbol(symbol="600519", bars=series["bars"], quality_issues=series["issues"],
                                               as_of=data["as_of"]), baseline)

    def test_official_past_bad_price_is_dated_without_discarding_valid_rows(self):
        bars = candidate_bars()
        bars[-1] = daily_bar(bars[-1]["trade_date"], high=9)
        data = self.capture_official(bars)
        series = data["series"]["600519"]["daily"]
        self.assertEqual(len(series["bars"]), 45)
        self.assertEqual([(i["code"], i["scope"], i["bar_key"]) for i in series["issues"]
                          if i["code"] != "truncated"], [("invalid_ohlc", "bar", "2026-02-15")])
        self.assertEqual(data["collection"]["status"], "partial")
        self.assertEqual(len(replay_symbol(symbol="600519", bars=series["bars"], quality_issues=series["issues"],
                                          as_of=data["as_of"])["observations"]), 1)
        provider = get_market_data_provider("tdx-official")
        with mock.patch("services.api.app.market_data._tdx_official_post",
                        return_value={"ListItem": [{"Item": ["20260215", "0", 10, 9, 8, 10, 100]}]}):
            with self.assertRaises(MarketDataError):
                provider.fetch_kline("600519", period="daily", limit=100)

    def capture(self, fetch, **kwargs):
        provider = mock.Mock()
        provider.fetch_kline_page.side_effect = fetch
        with mock.patch("services.api.app.market_data.get_market_data_provider", return_value=provider), \
             mock.patch("services.api.app.chan_capture.time.sleep"):
            return capture_dataset(symbols=["600519"], periods=["daily"],
                                   as_of="2026-09-30T15:00:00+08:00", **kwargs)

    def test_capture_records_bounded_pagination_and_strips_raw(self):
        offsets = []
        def fetch(symbol, *, period, limit, start, preserve_price_issues):
            self.assertTrue(preserve_price_issues)
            offsets.append((symbol, start))
            return {0: [daily_bar("2026-09-29", token="secret"), daily_bar("2026-09-30", raw="secret")],
                    2: [daily_bar("2026-09-28"), daily_bar("2026-09-29")], 4: []}[start]
        data = self.capture(fetch, page_size=2, max_pages=3)
        self.assertEqual(offsets, [(s, n) for s in ["600519", "SH000300"] for n in [0, 2, 4]])
        self.assertEqual([x["trade_date"] for x in data["series"]["600519"]["daily"]["bars"]],
                         ["2026-09-28", "2026-09-29", "2026-09-30"])
        self.assertNotIn("secret", json.dumps(data))
        self.assertFalse(data["collection"]["history_complete"])
        self.assertEqual(data["price_basis"]["verification"]["status"], "unverified")
        self.assertEqual(data["calendar"]["verification"]["status"], "unverified")
        self.assertNotEqual(data["selection"]["selected_at"], data["as_of"])

    def test_repeated_first_page_stops_with_explicit_failure(self):
        data = self.capture(lambda *a, **kw: [daily_bar("2026-09-30")], page_size=1, max_pages=5)
        self.assertEqual(len(data["collection"]["pages"]), 4)
        self.assertIn("pagination_not_advancing", [x["code"] for x in data["issues"]])
        self.assertEqual(data["collection"]["status"], "partial")

    def test_partial_failure_is_safe_and_limit_is_truncated(self):
        def fetch(*a, **kw):
            if kw["start"]:
                raise MarketDataError("private-token")
            return [daily_bar("2026-09-30")]
        data = self.capture(fetch, page_size=1, max_pages=2)
        self.assertEqual(len(data["series"]["600519"]["daily"]["bars"]), 1)
        self.assertEqual(data["collection"]["status"], "partial")
        self.assertNotIn("private-token", str(data))
        data = self.capture(fetch, page_size=1)
        self.assertIn("truncated", [x["code"] for x in data["issues"]])

    def test_conflicting_boundary_is_removed_not_silently_overwritten(self):
        def fetch(*a, **kw):
            return [daily_bar("2026-09-30")] if not kw["start"] else [daily_bar("2026-09-29"), daily_bar("2026-09-30", 11)]
        data = self.capture(fetch, page_size=2, max_pages=2)
        self.assertIn("conflicting_duplicate", [x["code"] for x in data["issues"]])
        self.assertEqual([x["trade_date"] for x in data["series"]["600519"]["daily"]["bars"]], ["2026-09-29"])

    def test_security_aliases_and_limits(self):
        provider = mock.Mock()
        provider.fetch_kline_page.return_value = []
        with mock.patch("services.api.app.market_data.get_market_data_provider", return_value=provider), \
             mock.patch("services.api.app.chan_capture.time.sleep"):
            data = capture_dataset(symbols=["600519", "sh600519", "1.600519", "000300"], periods=["d", "daily"],
                                   as_of="2026-09-30T15:00:00+08:00")
            self.assertEqual(data["selection"]["symbols"], ["600519", "000300"])
            self.assertEqual(set(data["series"]), {"600519", "000300", "SH000300"})
        for kwargs in [{"max_pages": 6}, {"page_size": 0}, {"max_pages": True}]:
            with self.assertRaises(ValueError):
                self.capture(lambda *a, **kw: [], **kwargs)

    def test_official_empty_page_is_not_an_error_or_malformed_success(self):
        provider = get_market_data_provider("tdx-official")
        with mock.patch("services.api.app.market_data._tdx_official_post", return_value={"ListItem": []}) as post:
            self.assertEqual(provider.fetch_kline_page("SH000300", period="daily", limit=12, start=12), [])
            self.assertEqual(post.call_args.args[1]["Startxh"], 12)
            self.assertEqual(post.call_args.args[1]["Setcode"], 1)
            with self.assertRaises(MarketDataError):
                provider.fetch_kline("SH000300", limit=12)
        for payload in [{}, {"ListItem": "bad"}, {"ListItem": [], "Error": "failed"}]:
            with mock.patch("services.api.app.market_data._tdx_official_post", return_value=payload):
                with self.assertRaises(MarketDataError):
                    provider.fetch_kline_page("600519", period="daily", limit=12, start=12)

    def test_missing_minute_within_returned_range_is_recorded(self):
        provider = mock.Mock()
        provider.fetch_kline_page.return_value = [
            daily_bar("2026-09-30T14:50:00+08:00"), daily_bar("2026-09-30T15:00:00+08:00")]
        with mock.patch("services.api.app.market_data.get_market_data_provider", return_value=provider), \
             mock.patch("services.api.app.chan_capture.time.sleep"):
            data = capture_dataset(symbols=["600519"], periods=["5min"],
                                   as_of="2026-09-30T15:00:00+08:00")
        gaps = [i["bar_key"] for i in data["series"]["600519"]["5min"]["issues"] if i["code"] == "missing_bar"]
        self.assertEqual(gaps, ["2026-09-30T14:55:00+08:00"])
