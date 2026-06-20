from __future__ import annotations

import unittest

from services.api.app.static_ui import index_html


class StaticUiTests(unittest.TestCase):
    def test_workbench_contains_language_switcher(self) -> None:
        html = index_html()

        self.assertIn('id="languageSelect"', html)
        self.assertIn("通达信股票工作台", html)
        self.assertIn("Tongdaxin Stock Workbench", html)
        self.assertIn("setLanguage", html)

    def test_workbench_defaults_to_current_symbol_scope(self) -> None:
        html = index_html()

        self.assertIn('id="holdingScope"', html)
        self.assertIn('id="signalScope"', html)
        self.assertIn('value="current"', html)
        self.assertIn("currentHoldingsHint", html)
        self.assertIn("currentLatestSignalsHint", html)
        self.assertIn("filterCurrentSymbol", html)

    def test_symbol_input_rerenders_and_updates_auto_name(self) -> None:
        html = index_html()

        self.assertIn('id="symbol" value="600519" oninput="onSymbolChanged()"', html)
        self.assertIn('id="name" value="Mock 600519" oninput="onNameChanged()"', html)
        self.assertIn("function onSymbolChanged()", html)
        self.assertIn("syncAutoName", html)


if __name__ == "__main__":
    unittest.main()
