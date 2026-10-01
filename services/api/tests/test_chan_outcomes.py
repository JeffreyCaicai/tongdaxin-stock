from __future__ import annotations

import copy
from datetime import date, timedelta
import unittest

from services.api.app.chan_outcomes import evaluate_observations
from services.api.tests.chan_validation_cases import daily_bar, make_dataset, rehash


class ChanOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.sessions = [(date(2026, 1, 1) + timedelta(days=i)).isoformat() for i in range(66)]
        bars = [daily_bar(d, price) for d, price in zip(self.sessions, [10, 13, 15, 12, 14, 15])]
        bars[1].update(open=12, low=11)
        index = [daily_bar(d, price) for d, price in zip(self.sessions, [100, 102, 104, 106, 108, 110])]
        index[1].update(open=100, low=99)
        self.as_of = "2026-01-06T15:00:00+08:00"
        self.dataset = make_dataset(series={"600519": {"daily": bars}, "SH000300": {"daily": index}},
                                    sessions=self.sessions, as_of=self.as_of)
        self.observations = [{"observation_id": "a" * 64, "symbol": "600519", "direction": "up",
                              "first_seen_at": "2026-01-01T15:00:00+08:00", "status": "candidate"}]

    def evaluate(self, data=None, observations=None, as_of=None):
        return evaluate_observations(observations=self.observations if observations is None else observations,
                                     dataset=rehash(data or self.dataset), as_of=as_of or self.as_of)

    def outcome(self, **kwargs):
        return self.evaluate(**kwargs)["items"][0]["outcomes"]["5"]

    def test_returns_start_after_signal_was_observable(self):
        result = self.outcome()
        self.assertEqual(result["status"], "matured")
        self.assertAlmostEqual(result["return_pct"], 25)
        self.assertAlmostEqual(result["benchmark_return_pct"], 10)
        self.assertAlmostEqual(result["excess_pp"], 15)
        self.assertAlmostEqual(result["max_drawdown_pct"], -20)
        self.assertEqual(result["start_date"], "2026-01-02")
        self.assertEqual(result["end_date"], "2026-01-06")

    def test_negative_candidates_are_price_observations_not_shorts(self):
        self.observations[0]["direction"] = "down"
        self.observations[0]["status"] = "withdrawn"
        result = self.evaluate()
        self.assertAlmostEqual(result["items"][0]["outcomes"]["5"]["return_pct"], 25)
        self.assertEqual(result["summary"]["5"]["down"]["matured"], 1)
        self.assertEqual(result["summary"]["5"]["up"]["matured"], 0)

    def test_pending_is_distinct_from_an_elapsed_missing_bar(self):
        pending = self.outcome(as_of="2026-01-04T14:59:59+08:00")
        self.assertEqual(pending["status"], "pending")
        self.assertIsNone(pending["return_pct"])
        for symbol in ["600519", "SH000300"]:
            data = copy.deepcopy(self.dataset)
            data["series"][symbol]["daily"]["bars"].pop(2)
            outcome = self.outcome(data=data)
            self.assertEqual(outcome["status"], "unavailable")
            self.assertIsNone(outcome["return_pct"])
            self.assertIn("missing", outcome["issue"])

    def test_unverified_or_insufficient_calendar_and_basis_block_metrics(self):
        for target, expected in [("calendar", "unverified_calendar"), ("price_basis", "unverified_price_basis")]:
            data = copy.deepcopy(self.dataset)
            data[target]["verification"]["status"] = "unverified"
            outcome = self.outcome(data=data)
            self.assertEqual(outcome["issue"], expected)
            self.assertIsNone(outcome["return_pct"])
        data = copy.deepcopy(self.dataset)
        data["calendar"]["sessions"] = self.sessions[:3]
        data["calendar"]["coverage_end"] = self.sessions[2]
        self.assertEqual(self.outcome(data=data)["issue"], "calendar_coverage_insufficient")

    def test_zero_negative_or_missing_volume_is_not_a_tradable_observation(self):
        for volume in [0, -1, None]:
            for symbol in ["600519", "SH000300"]:
                data = copy.deepcopy(self.dataset)
                data["series"][symbol]["daily"]["bars"][2]["volume"] = volume
                self.assertEqual(self.outcome(data=data)["status"], "unavailable")

    def test_calendar_conflict_and_bad_prices_cannot_be_ignored(self):
        data = copy.deepcopy(self.dataset)
        data["calendar"]["sessions"].pop(2)
        self.assertEqual(self.outcome(data=data)["issue"], "benchmark_calendar_conflict")
        data = copy.deepcopy(self.dataset)
        data["series"]["600519"]["daily"]["bars"][2]["close"] = 0
        self.assertEqual(self.outcome(data=data)["status"], "unavailable")

    def test_future_append_cannot_change_earlier_outcome(self):
        before = self.evaluate()
        data = copy.deepcopy(self.dataset)
        for symbol in data["series"]:
            data["series"][symbol]["daily"]["bars"].append(daily_bar("2026-01-07", 10000))
        after = self.evaluate(data=data)
        self.assertEqual(before, after)

    def test_deduplication_overlap_and_empty_group_summary(self):
        duplicate = self.evaluate(observations=self.observations * 2)
        self.assertEqual(len(duplicate["items"]), 1)
        second = {**self.observations[0], "observation_id": "b" * 64,
                  "first_seen_at": "2026-01-02T15:00:00+08:00"}
        result = self.evaluate(observations=self.observations + [second])
        self.assertTrue(all(item["outcomes"]["5"]["overlapping"] for item in result["items"]))
        self.assertEqual(result["summary"]["5"]["up"]["matured"], 1)
        self.assertEqual(result["summary"]["5"]["up"]["pending"], 1)
        self.assertIsNone(result["summary"]["20"]["up"]["mean_return_pct"])
        self.assertNotIn("win_rate", str(result))
        self.assertFalse(result["method"]["execution_costs_included"])
        self.assertEqual(self.evaluate(observations=[])["items"], [])
