from __future__ import annotations

import unittest
from copy import deepcopy
from unittest import mock

from services.api.app.market_time import completed_bars, decode_tdx_bar_time, normalize_period
from services.api.app.market_data import MarketDataError, get_market_data_provider


class MarketTimeTests(unittest.TestCase):
    def test_seconds_field_preserves_intraday_time(self):
        for period, seconds, clock in [
            ("60m", "41400", "11:30"), ("hour", 50400, "14:00"),
            ("60min", "54000", "15:00"), ("5min", 53400, "14:50"),
            ("5m", 53700, "14:55"),
        ]:
            with self.subTest(seconds=seconds):
                row = decode_tdx_bar_time({"Item": ["20260930", seconds]}, period=period)
                self.assertEqual(row["trade_date"], f"2026-09-30T{clock}:00+08:00")
                self.assertEqual(row["bar_end_at"], row["trade_date"])
                self.assertEqual(row["session_date"], "2026-09-30")
                self.assertIn("unverified", row["time_semantics"])

    def test_daily_key_stays_date_only(self):
        row = decode_tdx_bar_time({"Item": ["20260930", "0"]}, period="day")
        self.assertEqual(row["trade_date"], "2026-09-30")
        self.assertEqual(row["bar_end_at"], "2026-09-30T15:00:00+08:00")
        self.assertEqual(normalize_period("60m"), "60min")
        self.assertEqual(normalize_period("w"), "weekly")
        with self.assertRaises(ValueError):
            normalize_period("invented")

    def test_named_clock_and_array_must_agree(self):
        row = {"Date": "2026-09-30", "Time": "15:00:00", "Item": [20260930, 54000]}
        self.assertEqual(decode_tdx_bar_time(row, period="5min")["session_date"], "2026-09-30")
        for patch in [{"Date": "2026-09-29"}, {"Time": "14:55:00"}]:
            with self.assertRaisesRegex(ValueError, "conflicting"):
                decode_tdx_bar_time({**row, **patch}, period="5min")

    def test_invalid_or_missing_clocks_are_not_guessed(self):
        for period, value in [("60min", x) for x in [None, True, -1, 86400, 34200, 43200, 54300, 53700]] + [
            ("5min", 34200), ("5min", 45000), ("5min", 34501), ("5min", "bad")
        ]:
            with self.subTest(period=period, value=value), self.assertRaises(ValueError):
                decode_tdx_bar_time({"Item": [20260930, value]}, period=period)
        with self.assertRaises(ValueError):
            decode_tdx_bar_time({"Item": [20260230, 54000]}, period="5min")

    def test_completion_uses_timezone_and_ignores_future_damage(self):
        bars = [{"trade_date": f"2026-09-30T{clock}:00+08:00", "open": 10, "high": 11,
                 "low": 9, "close": 10, "volume": None} for clock in ["14:55", "15:00"]]
        original = deepcopy(bars)
        rows, issues = completed_bars(bars, period="5min", as_of="2026-09-30T06:59:59Z")
        self.assertEqual([x["trade_date"] for x in rows], [bars[0]["trade_date"]])
        self.assertEqual(issues, [])
        self.assertEqual(bars, original)
        self.assertEqual(len(completed_bars(bars, period="5min", as_of="2026-09-30T07:00:00Z")[0]), 2)
        bars[-1]["close"] = float("nan")
        self.assertEqual(completed_bars(bars, period="5min", as_of="2026-09-30T06:59:59Z")[1], [])
        with self.assertRaises(ValueError):
            completed_bars(bars, period="5min", as_of="2026-09-30T15:00:00")

    def test_conflicting_duplicates_and_invalid_ohlc_are_unusable(self):
        bar = {"trade_date": "2026-09-30", "open": 10, "high": 11, "low": 9, "close": 10}
        kwargs = {"period": "daily", "as_of": "2026-09-30T15:00:00+08:00"}
        self.assertEqual(len(completed_bars([bar, dict(bar)], **kwargs)[0]), 1)
        rows, issues = completed_bars([bar, {**bar, "close": 11}], **kwargs)
        self.assertEqual(rows, [])
        self.assertEqual(issues[0]["code"], "conflicting_duplicate")
        for value in [True, 0, float("nan"), float("inf"), 12]:
            self.assertEqual(completed_bars([{**bar, "close": value}], **kwargs)[0], [])

    def test_provider_preserves_time_metadata_and_safe_errors(self):
        provider = get_market_data_provider("tdx-official")
        rows = [{"Item": [20260930, s, 10, 11, 9, 10, 100, 1000]} for s in [53400, 53700, 54000]]
        with mock.patch("services.api.app.market_data._tdx_official_post", return_value={"ListItem": rows}):
            bars = provider.fetch_kline("600519", period="5m", limit=3)
        self.assertEqual(len({x["trade_date"] for x in bars}), 3)
        self.assertEqual(bars[-1]["period"], "5min")
        self.assertEqual(bars[-1]["payload"]["bar_end_at"], "2026-09-30T15:00:00+08:00")
        rows[0]["Item"][1] = "private-token"
        with mock.patch("services.api.app.market_data._tdx_official_post", return_value={"ListItem": rows}):
            with self.assertRaises(MarketDataError) as caught:
                provider.fetch_kline("600519", period="5min", limit=3)
        self.assertNotIn("private-token", str(caught.exception))

    def test_provider_rejects_bool_prices_and_conflicting_duplicates(self):
        provider = get_market_data_provider("tdx-official")
        row = {"Item": [20260930, 54000, 10, 11, 9, 10, 100, 1000]}
        for bad in [True, 11]:
            changed = deepcopy(row)
            changed["Item"][5] = bad
            with mock.patch("services.api.app.market_data._tdx_official_post",
                            return_value={"ListItem": [row, changed]}):
                with self.assertRaises(MarketDataError):
                    provider.fetch_kline("600519", period="5min", limit=2)
        with mock.patch("services.api.app.market_data._tdx_official_post",
                        return_value={"ListItem": [row, row]}):
            self.assertEqual(len(provider.fetch_kline("600519", period="5min", limit=2)), 1)
