from __future__ import annotations

import copy
import unittest

from scripts.validate_chan import _frame, _replay
from services.api.tests.chan_validation_cases import controlled_bars, make_dataset, rehash


class ChanQualityTests(unittest.TestCase):
    def setUp(self):
        self.bars = controlled_bars(36)
        self.as_of = "2026-02-05T15:00:00+08:00"
        self.data = make_dataset(series={"600519": {"daily": self.bars[:-1]}},
                                 sessions=[b["trade_date"] for b in self.bars], as_of=self.as_of)

    def quality(self, report):
        self.assertIn("data_quality", report)
        return report["data_quality"]["items"][0]

    def test_verified_calendar_exposes_trailing_missing_session(self):
        report = _replay(self.data, self.as_of)
        item = self.quality(report)
        self.assertEqual(item["valid_bar_count"], 35)
        self.assertEqual(item["expected_session_count"], 36)
        self.assertEqual(item["missing_sessions"], ["2026-02-05"])
        self.assertEqual(item["status"], "review")
        self.assertEqual(report["frames"][-1]["at"], self.as_of)
        self.assertFalse(report["frames"][-1]["eligible"])
        frame = _frame(self.data, "600519", self.as_of)
        self.assertFalse(frame["eligible_for_observation"])
        self.assertEqual(self.quality(frame), item)

    def test_unverified_calendar_never_invents_missing_sessions(self):
        self.data["calendar"]["verification"]["status"] = "unverified"
        item = self.quality(_replay(rehash(self.data), self.as_of))
        self.assertIsNone(item["expected_session_count"])
        self.assertEqual(item["missing_sessions"], [])
        self.assertEqual(item["status"], "limited")
        self.assertEqual(item["last_bar_at"], "2026-02-04T15:00:00+08:00")

    def test_future_bar_and_issue_do_not_change_visible_quality(self):
        before = self.quality(_replay(self.data, "2026-02-04T15:00:00+08:00"))
        data = copy.deepcopy(self.data)
        data["series"]["600519"]["daily"]["bars"].append(self.bars[-1])
        data["issues"].append({"symbol": "600519", "period": "daily", "scope": "bar",
                               "bar_key": "2026-02-05", "code": "invalid_ohlc"})
        after = self.quality(_replay(rehash(data), "2026-02-04T15:00:00+08:00"))
        self.assertEqual(before, after)

    def test_root_and_series_issues_are_deduplicated_and_bad_bars_excluded(self):
        issue = {"symbol": "600519", "period": "daily", "scope": "bar",
                 "bar_key": "2026-01-02", "code": "invalid_ohlc"}
        self.data["issues"] = [issue]
        self.data["series"]["600519"]["daily"]["issues"] = [issue]
        item = self.quality(_replay(rehash(self.data), self.as_of))
        self.assertEqual(item["valid_bar_count"], 34)
        self.assertEqual(sum(i["code"] == "invalid_ohlc" for i in item["issues"]), 1)

    def test_calendar_end_and_unknown_time_failures_are_not_called_complete(self):
        self.data["calendar"]["sessions"] = self.data["calendar"]["sessions"][:-1]
        self.data["calendar"]["coverage_end"] = "2026-02-04"
        item = self.quality(_replay(rehash(self.data), self.as_of))
        self.assertFalse(item["calendar_coverage_complete"])
        self.assertIsNone(item["expected_session_count"])
        self.assertEqual(item["status"], "limited")
        self.data["issues"] = [{"symbol": "600519", "period": "daily", "scope": "series",
                                "bar_key": None, "code": "provider_unavailable"}]
        item = self.quality(_replay(rehash(self.data), self.as_of))
        self.assertEqual(item["status"], "review")

    def test_off_calendar_prices_block_observation_eligibility(self):
        self.data["calendar"]["sessions"].remove("2026-01-02")
        frame = _frame(rehash(self.data), "600519", "2026-02-04T15:00:00+08:00")
        self.assertFalse(frame["eligible_for_observation"])
        item = self.quality(frame)
        self.assertIn("calendar_conflict", [i["code"] for i in item["issues"]])

    def test_valid_date_range_excludes_flagged_endpoint_prices(self):
        self.data["issues"] = [{"symbol": "600519", "period": "daily", "scope": "bar",
                                "bar_key": day, "code": "invalid_ohlc"}
                               for day in ("2026-01-01", "2026-02-04")]
        item = self.quality(_replay(rehash(self.data), self.as_of))
        self.assertEqual(item["first_bar_at"], "2026-01-02T15:00:00+08:00")
        self.assertEqual(item["last_bar_at"], "2026-02-03T15:00:00+08:00")
