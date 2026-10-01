import unittest
from unittest import mock

from services.api.app.chan_analysis import analyze_chan_structure
from services.api.app.chan_baseline import analyze_frame, baseline_fingerprint
from services.api.tests.chan_validation_cases import candidate_bars


class ChanBaselineTests(unittest.TestCase):
    def test_frame_matches_original_model_at_same_cutoff(self):
        bars = candidate_bars()
        for count in range(35, len(bars) + 1):
            cutoff = bars[count - 1]["trade_date"] + "T15:00:00+08:00"
            self.assertEqual(analyze_frame(symbol="600519", bars=bars, as_of=cutoff),
                             analyze_chan_structure(symbol="600519", bars=bars[:count], as_of=cutoff))

    def test_changed_fingerprint_refuses_to_run(self):
        with mock.patch("services.api.app.chan_baseline.SOURCE_HASHES", {"chan_analysis.py": "wrong"}):
            with self.assertRaisesRegex(ValueError, "baseline_mismatch"):
                baseline_fingerprint()

    def test_cutoff_and_order_are_explicit(self):
        bars = candidate_bars()
        with self.assertRaises(ValueError):
            analyze_frame(symbol="600519", bars=bars, as_of="2026-02-15T15:00:00")
        with self.assertRaisesRegex(ValueError, "non_increasing"):
            analyze_frame(symbol="600519", bars=bars[::-1], as_of="2026-02-15T15:00:00+08:00")
