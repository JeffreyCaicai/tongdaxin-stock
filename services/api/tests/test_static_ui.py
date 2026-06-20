from __future__ import annotations

import unittest

from services.api.app.static_ui import index_html


class StaticUiTests(unittest.TestCase):
    def test_workbench_contains_language_switcher(self) -> None:
        html = index_html()

        self.assertIn('id="languageSelect"', html)
        self.assertIn('id="marketSourceSelect"', html)
        self.assertIn('value="tdx-official"', html)
        self.assertIn('value="tongdaxin"', html)
        self.assertIn("通达信股票工作台", html)
        self.assertIn("Tongdaxin Stock Workbench", html)
        self.assertIn("setLanguage", html)
        self.assertIn("tdxOfficialSource", html)
        self.assertIn("tongdaxinSource", html)
        self.assertIn("eastmoneySource", html)

    def test_workbench_defaults_to_current_symbol_scope(self) -> None:
        html = index_html()

        self.assertIn('id="holdingScope"', html)
        self.assertIn('id="signalScope"', html)
        self.assertIn('id="poolSelect"', html)
        self.assertIn("selectedPoolId", html)
        self.assertIn('value="current"', html)
        self.assertIn("currentHoldingsHint", html)
        self.assertIn("currentLatestSignalsHint", html)
        self.assertIn("filterCurrentSymbol", html)

    def test_symbol_input_rerenders_and_updates_auto_name(self) -> None:
        html = index_html()

        self.assertIn('id="symbol" value="600519" oninput="onSymbolChanged()"', html)
        self.assertIn('id="name" value="" oninput="onNameChanged()"', html)
        self.assertIn('id="cost_price" type="number" value="" oninput="onPlanChanged()"', html)
        self.assertIn('id="stop_loss" type="number" value="" oninput="onPlanChanged()"', html)
        self.assertIn('id="take_profit" type="number" value="" oninput="onPlanChanged()"', html)
        self.assertIn("thesisPlaceholder", html)
        self.assertNotIn("Manual plan with mock data.", html)
        self.assertIn("function onSymbolChanged()", html)
        self.assertIn("syncAutoName", html)
        self.assertIn("draftPlanFromQuote", html)
        self.assertIn("hydrateSymbolFromMarket", html)

    def test_pool_analysis_button_uses_mcp_endpoint(self) -> None:
        html = index_html()

        self.assertIn('onclick="analyzePool()"', html)
        self.assertIn("function analyzePool()", html)
        self.assertIn("/mcp-analysis", html)
        self.assertIn("renderPoolAnalysis", html)
        self.assertIn('onclick="generateSignals()"', html)


if __name__ == "__main__":
    unittest.main()
