from __future__ import annotations

import unittest
from unittest.mock import patch

from pydantic import ValidationError

from services.api.app.chan_analysis import (
    _build_strokes, _candidate_signal, _detect_centers, _detect_fractals, _merge_contained_bars,
    analyze_chan_structure,
)
from services.api.app.pool_analysis import generate_stock_pool_market_analysis
from services.api.app.schemas import StockPoolChanAnalysisRequest
from services.api.tests.test_chan_analysis import zigzag_bars


class ChanIntegrityTests(unittest.TestCase):
    def candidate(self, low=12.5, center_end=2):
        strokes = [{"direction": "up", "low": 10, "high": 12}] * 3 + [
            {"direction": "up", "low": 11, "high": 15, "end_price": 15},
            {"direction": "down", "low": low, "high": 15, "end_price": low},
        ]
        return _candidate_signal(current_price=13, strokes=strokes, centers=[
            {"lower": 10, "upper": 12, "stroke_end": center_end},
        ])

    def test_third_buy_requires_pullback_outside_center_and_after_formation(self):
        self.assertNotEqual(self.candidate(low=11)["type"], "suspected_third_buy")
        self.assertNotEqual(self.candidate(low=12)["type"], "suspected_third_buy")
        self.assertNotEqual(self.candidate(center_end=4)["type"], "suspected_third_buy")
        self.assertEqual(self.candidate()["type"], "suspected_third_buy")

    def test_third_sell_requires_rebound_below_center(self):
        strokes = [{"direction": "down", "low": 10, "high": 12}] * 3 + [
            {"direction": "down", "low": 8, "high": 11, "end_price": 8},
            {"direction": "up", "low": 8, "high": 11, "end_price": 11},
        ]
        center = {"lower": 10, "upper": 12, "stroke_end": 2}
        signal = _candidate_signal(current_price=9, strokes=strokes, centers=[center])
        self.assertNotEqual(signal["type"], "suspected_third_sell")
        strokes[-1].update(high=9.5, end_price=9.5)
        signal = _candidate_signal(current_price=9, strokes=strokes, centers=[center])
        self.assertEqual(signal["type"], "suspected_third_sell")

    def test_final_stroke_is_provisional_and_excluded_from_center_input(self):
        result = analyze_chan_structure(symbol="600519", bars=zigzag_bars(),
                                        as_of="2026-02-10T16:00:00+08:00")
        strokes = result["chart"]["strokes"]
        self.assertFalse(strokes[-1]["confirmed"])
        self.assertTrue(all(stroke["confirmed"] for stroke in strokes[:-1]))
        self.assertEqual(result["confirmed_stroke_count"], len(strokes) - 1)
        self.assertTrue(all(center["stroke_end"] < len(strokes) - 1 for center in result["chart"]["centers"]))
        self.assertEqual(result["price_origin"], "kline_close")
        self.assertEqual(result["as_of"], "2026-02-10")

    def test_intraday_future_and_malformed_bars_cannot_be_structure_evidence(self):
        bars = zigzag_bars()
        bars[-1]["close"] = float("nan")
        result = analyze_chan_structure(symbol="600519", bars=bars,
                                        as_of="2026-02-10T10:00:00+08:00")
        self.assertEqual(result["as_of"], "2026-02-09")
        self.assertEqual(result["data_quality"]["excluded_bar_count"], 1)
        bars[10]["high"] = 1
        result = analyze_chan_structure(symbol="600519", bars=bars,
                                        as_of="2026-02-10T16:00:00+08:00")
        self.assertEqual(result["signal"]["type"], "data_review")
        self.assertIsNone(result["signal"]["trigger"])
        self.assertIn("invalid_daily_data", result["data_quality"]["issues"])

    def test_stale_or_duplicate_data_disables_action_candidates(self):
        for bars, now, issue in [
            (zigzag_bars(), "2026-03-10T16:00:00+08:00", "stale_kline"),
            (zigzag_bars() * 2, "2026-02-10T16:00:00+08:00", "duplicate_dates"),
        ]:
            result = analyze_chan_structure(symbol="600519", bars=bars, as_of=now)
            self.assertEqual(result["signal"]["type"], "data_review")
            self.assertEqual(result["signal"]["confidence"], "low")
            self.assertIn(issue, result["data_quality"]["issues"])

    def test_non_daily_request_is_rejected_instead_of_using_daily_completion_rules(self):
        with self.assertRaises(ValidationError):
            StockPoolChanAnalysisRequest(period="weekly")

    def test_merged_pivot_uses_extreme_date_not_first_bar_date(self):
        bars = [dict(trade_date=f"2026-02-0{i + 1}", open=low, high=high,
                     low=low, close=high, volume=100)
                for i, (low, high) in enumerate([(8, 10), (9, 12), (8.5, 13), (8, 11)])]
        fractals = _detect_fractals(_merge_contained_bars(bars))
        self.assertEqual(fractals[0]["date"], "2026-02-03")
        self.assertEqual(fractals[0]["confirmed_at"], "2026-02-04")

    def test_separated_centers_are_not_joined_by_price_alone(self):
        strokes = [dict(low=low, high=high, start_date=str(i), end_date=str(i + 1))
                   for i, (low, high) in enumerate(
                       [(10, 14)] * 3 + [(20, 24), (30, 34), (40, 44)] + [(10, 14)] * 3)]
        centers = _detect_centers(strokes)
        self.assertEqual(len(centers), 2)
        touching = [dict(low=low, high=high, start_date=str(i), end_date=str(i + 1))
                    for i, (low, high) in enumerate([(10, 12), (12, 14), (11, 13)])]
        self.assertEqual(_detect_centers(touching), [])

    def test_stroke_bounds_include_internal_wicks_not_just_pivot_prices(self):
        fractals = [dict(type=kind, index=i, date=f"2026-01-{i + 1:02}", price=price)
                    for kind, i, price in [("top", 0, 15), ("bottom", 5, 13), ("top", 10, 16)]]
        bars = [dict(trade_date="2026-01-03", low=11, high=14)]
        self.assertEqual(_build_strokes(fractals, bars=bars)[0]["low"], 11)


class MarketOverviewIntegrityTests(unittest.TestCase):
    def overview(self, quotes, holdings=None):
        with patch("services.api.app.pool_analysis.utc_now", return_value="2026-10-01T01:00:00Z"):
            return generate_stock_pool_market_analysis(
                pool={"id": 1}, watchlist=[{"symbol": symbol} for symbol in quotes],
                holdings=holdings or [], quotes=quotes, source="tdx-official",
            )

    def quote(self, **values):
        return {"price": 11, "previous_close": 10, "fetched_at": "2026-10-01T00:59:00Z",
                "source": "tdx-official", **values}

    def test_fields_breadth_and_legacy_stop_values_are_separate(self):
        result = self.overview({
            "600001": self.quote(amount=123000000, open=10.2, high=11.5, low=10,
                                  payload={"turnover_rate": 2.1}),
            "600002": self.quote(price=9), "600003": self.quote(price=None),
            "600004": self.quote(price=10),
        }, holdings=[{"symbol": "600001", "cost_price": 1, "quantity": 100, "take_profit": 2}])
        fields = result["items"][0]["quote"]["fields"]
        self.assertEqual(fields["pct_change"], 10)
        self.assertEqual(fields["amount"], 123000000)
        self.assertEqual(fields["turnover_rate"], 2.1)
        self.assertEqual(fields["previous_close"], 10)
        self.assertEqual(result["items"][0]["action_hint"], "hold_and_monitor")
        self.assertEqual(result["breadth"], dict(up=1, down=1, flat=1, unknown=1,
                                              sample_size=3, mean_change_pct=0.0))
        self.assertEqual(result["data_quality"]["quote_coverage_pct"], 75)
        self.assertIsNone(fields["market_time"])

    def test_invalid_prices_are_missing_not_zero_returns(self):
        for value in (None, 0, -1, True, "NaN", float("inf")):
            with self.subTest(value=value):
                result = self.overview({"600001": self.quote(price=value, pct_change=0)})
                self.assertEqual(result["data_quality"]["missing_quote_count"], 1)
                self.assertIsNone(result["items"][0]["quote"]["fields"]["pct_change"])
                self.assertEqual(result["breadth"]["unknown"], 1)

    def test_stale_or_unknown_fetch_time_is_not_current_breadth(self):
        for stamp in ("2026-09-20T00:00:00Z", "now", "2026-10-02T00:00:00Z"):
            result = self.overview({"600001": self.quote(fetched_at=stamp)})
            self.assertEqual(result["breadth"]["sample_size"], 0)
            self.assertEqual(result["data_quality"]["fresh_quote_count"], 0)
            self.assertEqual(result["items"][0]["quote"]["fields"]["price"], 11)

    def test_wrong_symbol_and_inconsistent_change_are_visible(self):
        result = self.overview({"600001": self.quote(symbol="600002")})
        self.assertIsNone(result["items"][0]["quote"]["fields"]["price"])
        result = self.overview({"600001": self.quote(pct_change=90)})
        self.assertEqual(result["items"][0]["quote"]["fields"]["pct_change"], 10)
        self.assertIn("change_recomputed", result["items"][0]["quote"]["issues"])

    def test_old_exchange_clock_does_not_become_fresh_on_refetch(self):
        result = self.overview({"600001": self.quote(market_time="2026-09-01T15:00:00+08:00")})
        self.assertEqual(result["data_quality"]["fresh_quote_count"], 0)
        self.assertEqual(result["breadth"]["unknown"], 1)
        self.assertIn("stale_market_time", result["items"][0]["quote"]["issues"])


if __name__ == "__main__":
    unittest.main()
