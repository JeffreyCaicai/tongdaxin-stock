from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

from services.api.app.static_ui import index_html


def run_ui_javascript(case: str) -> subprocess.CompletedProcess:
    script = re.search(r"<script>(.*?)</script>", index_html(), re.DOTALL)
    if script is None:
        raise AssertionError("Workbench script is missing")
    return subprocess.run(
        [shutil.which("node"), str(Path(__file__).with_name("static_ui_runtime.js")), case],
        input=script.group(1), text=True, capture_output=True, timeout=20,
        env={},
    )


@unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
class StaticUiRuntimeTests(unittest.TestCase):
    def test_opportunity_poll_cannot_overwrite_newer_analysis_and_labels_are_bilingual(self):
        self.run_js("opportunities")

    def run_js(self, case: str) -> None:
        result = run_ui_javascript(case)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_partial_holdings_valuation(self) -> None:
        self.run_js("holdings")

    def test_quote_enrichment_rejects_missing_or_nonpositive_prices(self) -> None:
        self.run_js("quotes")

    def test_latest_analysis_wins_cross_action_deferred_races(self) -> None:
        self.run_js("races")

    def test_source_switch_cancels_and_invalidates_analysis(self) -> None:
        self.run_js("source")

    def test_latest_failure_does_not_restore_previous_cached_result(self) -> None:
        self.run_js("failure")

    def test_decision_details_are_compact_bilingual_and_escaped(self) -> None:
        self.run_js("details")

    def test_optional_comparison_is_per_symbol_and_handles_missing_scores(self) -> None:
        self.run_js("comparison")

    def test_decision_request_uses_exchange_qualified_benchmark(self) -> None:
        self.run_js("benchmark")

    def test_daily_review_requests_source_and_renders_saved_decision_context(self) -> None:
        self.run_js("saved-review")

    def test_endpoint_provenance_and_known_chan_signals_are_bilingual(self) -> None:
        self.run_js("provenance-labels")

    def test_scoped_not_analyzed_review_does_not_render_legacy_signals(self) -> None:
        self.run_js("not-analyzed")

    def test_unscoped_daily_review_preserves_legacy_api_compatibility(self) -> None:
        self.run_js("legacy-review")


if __name__ == "__main__":
    unittest.main()
