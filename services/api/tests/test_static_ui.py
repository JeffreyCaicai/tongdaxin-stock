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

    def test_watch_symbol_form_rerenders_and_updates_auto_name(self) -> None:
        html = index_html()

        self.assertIn("添加关注股", html)
        self.assertIn('id="symbol" value="600519" oninput="onSymbolChanged()"', html)
        self.assertIn('id="name" value="" oninput="onNameChanged()"', html)
        self.assertIn('onclick="addSymbolToPool()" data-i18n="addWatchSymbolButton"', html)
        self.assertNotIn('id="quantity"', html)
        self.assertNotIn('id="cost_price"', html)
        self.assertNotIn('id="stop_loss"', html)
        self.assertNotIn('id="take_profit"', html)
        self.assertNotIn('id="initial_thesis"', html)
        self.assertNotIn("function addHolding()", html)
        self.assertNotIn("draftPlanFromQuote", html)
        self.assertNotIn("Manual plan with mock data.", html)
        self.assertIn("function onSymbolChanged()", html)
        self.assertIn("syncAutoName", html)
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
