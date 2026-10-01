from __future__ import annotations

import copy
import unittest
from datetime import date, timedelta

from services.api.app import opportunities


def daily_bars(closes, start=date(2025, 1, 2)):
    rows, day = [], start
    for close in closes:
        while day.weekday() > 4:
            day += timedelta(days=1)
        rows.append({"trade_date": day.isoformat(), "open": close, "close": close,
                     "high": close * 1.01, "low": close * .99, "volume": 1_000_000})
        day += timedelta(days=1)
    return rows


class HorizonTests(unittest.TestCase):
    def evaluate(self, bars, index=None, **overrides):
        self.assertTrue(hasattr(opportunities, "assess_horizons"), "Independent horizon assessments are missing")
        args = dict(bars=bars, index_bars=index or daily_bars([100] * len(bars)),
                    as_of=bars[-1]["trade_date"] + "T16:00:00+08:00", regime="uptrend", blocked=False)
        args.update(overrides)
        return opportunities.assess_horizons(**args)

    def test_recent_reversal_and_longer_trend_have_different_assessments(self):
        bars = daily_bars([100 + i * .1 for i in range(215)] + [121, 120.8, 120.5, 120.2, 119.8])
        result = self.evaluate(bars)
        self.assertEqual(result["5"]["stance"], "avoid")
        self.assertEqual(result["60"]["stance"], "favorable")
        self.assertNotEqual(result["5"]["score"], result["60"]["score"])
        self.assertEqual(result["long_term"]["stance"], "insufficient")
        self.assertIn("fundamentals_unverified", result["long_term"]["issues"])

    def test_short_history_does_not_invent_medium_term_evidence(self):
        result = self.evaluate(daily_bars([100 + i * .1 for i in range(70)]))
        self.assertIsNotNone(result["5"]["score"])
        self.assertEqual(result["120"]["stance"], "insufficient")
        self.assertIsNone(result["120"]["score"])

    def test_future_and_unclosed_bar_cannot_change_assessment(self):
        bars = daily_bars([100 + i * .1 for i in range(220)])
        end = bars[-2]["trade_date"]
        expected = self.evaluate(bars[:-1])
        result = self.evaluate(bars, as_of=bars[-1]["trade_date"] + "T14:59:00+08:00")
        self.assertEqual(result["20"]["as_of"], end)
        self.assertEqual(result["20"]["score"], expected["20"]["score"])

    def test_duplicate_missing_endpoint_and_exclusion_are_not_positive(self):
        bars = daily_bars([100 + i * .1 for i in range(220)])
        duplicate = copy.deepcopy(bars) + [bars[-1]]
        self.assertEqual(self.evaluate(duplicate)["5"]["stance"], "insufficient")
        index = daily_bars([100] * 220)
        self.assertEqual(self.evaluate(bars[:-1], index, as_of=bars[-1]["trade_date"] + "T16:00:00+08:00")["5"]["stance"], "insufficient")
        self.assertEqual(self.evaluate(bars, blocked=True)["20"]["stance"], "insufficient")

    def test_extended_short_term_and_stress_market_wait_for_confirmation(self):
        bars = daily_bars([100 + i * .1 for i in range(215)] + [123, 125, 128, 132, 137])
        result = self.evaluate(bars)
        self.assertEqual(result["5"]["stance"], "wait")
        self.assertIn("extended", result["5"]["issues"])
        steady = daily_bars([100 + i * .1 for i in range(220)])
        self.assertEqual(self.evaluate(steady, regime="high_volatility_pressure")["60"]["stance"], "wait")


if __name__ == "__main__":
    unittest.main()
