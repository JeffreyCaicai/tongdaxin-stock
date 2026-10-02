import copy
import unittest
from datetime import date, timedelta

from services.api.app.chan_replay import replay_symbol
from services.api.app.chan_analysis import analyze_chan_structure
from services.api.tests.chan_validation_cases import candidate_bars, controlled_analyzer, controlled_bars, daily_bar


class ChanReplayTests(unittest.TestCase):
    def run_replay(self, bars=None, analyzer=None, issues=None, as_of="2026-04-01T15:00:00+08:00"):
        return replay_symbol(symbol="600519", bars=controlled_bars() if bars is None else bars,
                             as_of=as_of, quality_issues=issues or [], analyzer=analyzer)

    def test_actual_candidate_events_are_prefix_invariant(self):
        bars = candidate_bars()
        first = self.run_replay(bars)
        self.assertTrue(first["observations"])
        extended = bars + [daily_bar("2026-02-16", 100), daily_bar("2026-02-17", 1),
                           daily_bar("2026-12-01", close=float("nan"))]
        later = self.run_replay(extended)
        self.assertEqual(later["frames"][:len(first["frames"])], first["frames"])
        self.assertEqual(later["events"][:len(first["events"])], first["events"])
        self.assertEqual(self.run_replay(bars), first)
        for frame in first["frames"]:
            result = analyze_chan_structure(symbol="600519", bars=[b for b in bars if b["trade_date"] <= frame["at"][:10]], as_of=frame["at"])
            self.assertEqual(frame["signal"], result["signal"])
            self.assertEqual(frame["latest_center"], result["latest_center"])
        self.assertTrue(all(x["confirmed_at"] is None for x in first["observations"]))
        self.assertNotIn("rule_confirmed", [e["type"] for e in first["events"]])

    def test_continuous_candidate_and_extending_center_stay_one_observation(self):
        result = self.run_replay(analyzer=controlled_analyzer())
        self.assertEqual(len(result["observations"]), 1)
        observation = result["observations"][0]
        self.assertEqual(observation["frozen_boundary"], 12)
        self.assertEqual(observation["first_seen_at"], "2026-02-04T15:00:00+08:00")
        self.assertEqual([e["type"] for e in result["events"]], ["candidate"])

    def test_close_invalidates_but_intraday_touch_only_records_risk(self):
        bars = controlled_bars(38)
        bars[35]["low"] = 11.9
        bars[36] = daily_bar(bars[36]["trade_date"], 12)
        result = self.run_replay(bars, controlled_analyzer())
        self.assertEqual(len(result["observations"]), 1)
        invalid = [e for e in result["events"] if e["type"] == "invalidated"]
        self.assertEqual([e["at"] for e in invalid], ["2026-02-06T15:00:00+08:00"])
        self.assertIn("boundary_touch", [e["type"] for e in result["events"]])
        self.assertEqual(result["observations"][0]["status"], "candidate")

    def test_sell_candidate_uses_frozen_lower_boundary(self):
        bars = [daily_bar(b["trade_date"], 9, high=9.5) for b in controlled_bars(37)]
        bars[-1] = daily_bar(bars[-1]["trade_date"], 10)
        result = self.run_replay(bars, controlled_analyzer(direction="down"))
        self.assertEqual(result["observations"][0]["frozen_boundary"], 10)
        self.assertEqual(result["events"][-1]["type"], "invalidated")

    def test_data_gap_does_not_rearm_but_valid_withdrawal_does(self):
        gap = self.run_replay(analyzer=controlled_analyzer({36: "missing"}))
        self.assertEqual(len(gap["observations"]), 1)
        self.assertEqual([e["type"] for e in gap["events"]], ["candidate", "data_unavailable", "candidate"])
        withdrawn = self.run_replay(analyzer=controlled_analyzer({36: "observation"}))
        self.assertEqual(len(withdrawn["observations"]), 2)
        self.assertTrue(withdrawn["observations"][1]["overlapping_episode"])
        self.assertEqual([e["type"] for e in withdrawn["events"]], ["candidate", "withdrawn", "candidate"])

    def test_missing_final_session_records_unavailable_without_inventing_prices(self):
        bars = controlled_bars(35)
        issue = {"code": "missing_session", "symbol": "600519", "period": "daily",
                 "scope": "bar", "bar_key": "2026-02-05"}
        before = self.run_replay(bars, controlled_analyzer(), [issue], "2026-02-05T14:59:59+08:00")
        after = self.run_replay(bars, controlled_analyzer(), [issue], "2026-02-05T15:00:00+08:00")
        self.assertEqual([e["type"] for e in before["events"]], ["candidate"])
        self.assertEqual([e["type"] for e in after["events"]], ["candidate", "data_unavailable"])
        self.assertEqual(after["events"][-1]["at"], "2026-02-05T15:00:00+08:00")
        self.assertFalse(after["frames"][-1]["boundary_tracking_eligible"])
        self.assertEqual(after["frames"][-1]["bar_count"], 35)
        self.assertEqual(after["observations"], before["observations"])
        self.assertEqual(after["frames"][:-1], before["frames"])

    def test_internal_missing_session_is_not_silently_skipped(self):
        bars = controlled_bars(37)
        bars.pop(35)
        issue = {"code": "invalid_ohlc", "symbol": "600519", "period": "daily",
                 "scope": "bar", "bar_key": "2026-02-05"}
        result = self.run_replay(bars, controlled_analyzer(), [issue])
        self.assertEqual([f["at"][:10] for f in result["frames"]],
                         ["2026-02-04", "2026-02-05", "2026-02-06"])
        self.assertEqual(result["events"][-1]["at"][:10], "2026-02-05")
        self.assertEqual(len(result["observations"]), 1)

    def test_withdrawn_observation_keeps_tracking_frozen_invalidation(self):
        bars = controlled_bars(38)
        bars[-1] = daily_bar(bars[-1]["trade_date"], 12)
        result = self.run_replay(bars, controlled_analyzer({36: "observation", 37: "observation", 38: "observation"}))
        self.assertEqual([e["type"] for e in result["events"]], ["candidate", "withdrawn", "invalidated"])

    def test_stale_structure_still_invalidates_at_trustworthy_current_close(self):
        bars = candidate_bars() + [daily_bar((date(2026, 2, 16) + timedelta(days=i)).isoformat(),
                                            13.8, high=13.9, low=13.7) for i in range(40)]
        before = self.run_replay(bars[:-1])
        bars[-1] = daily_bar(bars[-1]["trade_date"], 11, high=11.1, low=10.9)
        result = self.run_replay(bars)
        self.assertIn("stale_structure", result["frames"][-1]["data_quality"]["issues"])
        self.assertFalse(result["frames"][-1]["eligible"])
        self.assertTrue(result["frames"][-1]["boundary_tracking_eligible"])
        self.assertEqual(result["observations"], before["observations"])
        invalid = [e for e in result["events"] if e["type"] == "invalidated"]
        self.assertEqual(len(invalid), 1)
        self.assertEqual(invalid[0]["at"], "2026-03-27T15:00:00+08:00")
        self.assertEqual(invalid[0]["details"], {"close": 11, "boundary": 12.1})
        self.assertEqual(result["events"][:len(before["events"])], before["events"])

    def test_untrustworthy_current_price_never_triggers_invalidation(self):
        for source in ("price", "bar_issue", "series_issue"):
            with self.subTest(source=source):
                bars = controlled_bars(36)
                bars[-1] = daily_bar(bars[-1]["trade_date"], 11)
                issues = []
                if source == "price":
                    bars[-1]["high"] = 10
                else:
                    issues = [{"code": "invalid_ohlc", "symbol": "600519", "period": "daily",
                               "scope": "bar" if source == "bar_issue" else "series",
                               "bar_key": bars[-1]["trade_date"] if source == "bar_issue" else None}]
                result = self.run_replay(bars, controlled_analyzer(), issues)
                if source == "series_issue":
                    self.assertEqual(result["observations"], [])
                else:
                    self.assertEqual(len(result["observations"]), 1)
                    self.assertEqual(result["events"][-1]["type"], "data_unavailable")
                self.assertNotIn("invalidated", [e["type"] for e in result["events"]])

    def test_stale_sell_candidate_keeps_frozen_boundary_tracking(self):
        base = controlled_analyzer(direction="down")
        def stale(*, symbol, bars, as_of):
            result = base(symbol=symbol, bars=bars, as_of=as_of)
            if len(bars) > 35:
                result["data_quality"] = {"status": "partial", "issues": ["stale_structure"]}
            return result
        bars = [daily_bar(b["trade_date"], 9, high=9.5) for b in controlled_bars(37)]
        bars[35]["high"] = 10.1
        bars[-1] = daily_bar(bars[-1]["trade_date"], 10)
        result = self.run_replay(bars, stale)
        self.assertEqual(len(result["observations"]), 1)
        self.assertEqual([e["type"] for e in result["events"]],
                         ["candidate", "boundary_touch", "data_unavailable", "invalidated"])

    def test_future_quality_issue_cannot_poison_past(self):
        issue = {"code": "missing_session", "symbol": "600519", "period": "daily", "scope": "bar", "bar_key": "2026-02-06"}
        result = self.run_replay(analyzer=controlled_analyzer(), issues=[issue])
        first = self.run_replay(analyzer=controlled_analyzer(), as_of="2026-02-05T15:00:00+08:00")
        self.assertEqual(result["events"][:len(first["events"])], first["events"])
        self.assertEqual(result["events"][-1]["type"], "data_unavailable")
        issue.update(scope="series", bar_key=None)
        self.assertEqual(self.run_replay(analyzer=controlled_analyzer(), issues=[issue])["observations"], [])

    def test_insufficient_and_unformed_are_normal_outputs(self):
        result = self.run_replay(controlled_bars(10))
        self.assertEqual(result["observations"], [])
        self.assertIn("insufficient_bars", result["issues"])
        result = self.run_replay(controlled_bars(40))
        self.assertEqual(result["observations"], [])
        self.assertTrue(result["frames"])
