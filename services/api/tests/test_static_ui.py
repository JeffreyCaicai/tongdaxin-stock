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


if __name__ == "__main__":
    unittest.main()
