from __future__ import annotations

import unittest
import shutil
import re
from html.parser import HTMLParser

from services.api.app.static_ui import index_html
from services.api.tests.test_static_ui_runtime import run_ui_javascript


class DecisionMarkupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.columns = []
        self.summary_count = 0
        self.detail_count = 0
        self.detail_depth = 0
        self.tables_in_details = 0
        self.table_count = 0
        self.unsafe_tags = []
        self.definition_depth = 0
        self.nested_definitions = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "details":
            self.detail_count += 1
            self.detail_depth += 1
        if tag == "summary" and self.detail_depth:
            self.summary_count += 1
        if tag == "th":
            self.columns.append(dict(attrs))
        if tag == "dl":
            if self.definition_depth:
                self.nested_definitions += 1
            self.definition_depth += 1
        if tag == "table" and self.detail_depth:
            self.tables_in_details += 1
        if tag == "table":
            self.table_count += 1
        if tag in {"script", "img"}:
            self.unsafe_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "details":
            self.detail_depth -= 1
        if tag == "dl":
            self.definition_depth -= 1


class StaticUiTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_not_analyzed_markup_has_no_legacy_review_tables(self) -> None:
        result = run_ui_javascript("not-analyzed-markup")
        self.assertEqual(result.returncode, 0, result.stderr)
        parser = DecisionMarkupParser()
        parser.feed(result.stdout)
        self.assertEqual(parser.table_count, 0)
        self.assertEqual(parser.columns, [])
        self.assertIn("请先运行持仓决策引擎", result.stdout)

    def test_responsive_containers_constrain_intrinsic_table_width(self) -> None:
        style = re.search(r"<style>(.*?)</style>", index_html(), re.DOTALL).group(1)

        def declarations(selector: str) -> dict:
            rules = re.findall(re.escape(selector) + r"\s*\{([^{}]*)\}", style)
            return dict(re.findall(r"([\w-]+)\s*:\s*([^;]+);", " ".join(rules)))

        for selector in ["section", ".panel", ".header-tools"]:
            self.assertEqual(declarations(selector).get("min-width"), "0", selector)
        self.assertEqual(declarations("main").get("grid-template-columns"), "minmax(0, 1fr)")
        self.assertEqual(declarations(".grid").get("grid-template-columns"), "minmax(0, 1fr)")
        self.assertEqual(declarations(".table-scroll").get("max-width"), "100%")
        self.assertEqual(declarations(".table-scroll").get("overflow-x"), "auto")
        self.assertEqual(declarations(".header-tools select").get("max-width"), "100%")
        self.assertEqual(declarations(".status").get("overflow-wrap"), "anywhere")
        self.assertNotIn("overflow-x", declarations("body"))

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_rendered_decision_overview_and_native_details_are_accessible(self) -> None:
        result = run_ui_javascript("markup")
        self.assertEqual(result.returncode, 0, result.stderr)
        parser = DecisionMarkupParser()
        parser.feed(result.stdout)
        self.assertEqual(len(parser.columns), 6)
        self.assertTrue(all(column.get("scope") == "col" for column in parser.columns))
        self.assertEqual(parser.detail_count, 2)
        self.assertEqual(parser.summary_count, 2)
        self.assertEqual(parser.tables_in_details, 0)
        self.assertEqual(parser.nested_definitions, 0, "Nested window fields must not shrink repeatedly on mobile")
        self.assertEqual(parser.unsafe_tags, [])

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

    def test_workbench_uses_selected_pool_as_primary_scope(self) -> None:
        html = index_html()

        self.assertIn("selectedPoolId", html)
        self.assertIn("poolHoldingsHint", html)
        self.assertNotIn('id="poolName"', html)
        self.assertNotIn("personalPool", html)
        self.assertNotIn('id="poolSelect"', html)
        self.assertNotIn("setSelectedPool", html)
        self.assertNotIn('id="holdingScope"', html)
        self.assertNotIn('id="signalScope"', html)
        self.assertNotIn("currentHoldingsHint", html)
        self.assertNotIn("currentLatestSignalsHint", html)
        self.assertNotIn("filterCurrentSymbol", html)

    def test_watch_symbol_form_rerenders_and_updates_auto_name(self) -> None:
        html = index_html()

        self.assertIn("添加关注股", html)
        self.assertIn('id="symbol" value="" data-i18n-placeholder="symbolOrNamePlaceholder"', html)
        self.assertIn('id="name" value="" data-i18n-placeholder="nameOptionalPlaceholder"', html)
        self.assertIn('oninput="onNameChanged()"', html)
        self.assertIn("symbolOrName", html)
        self.assertIn("/market/search", html)
        self.assertIn("lookupText", html)
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

    def test_contextual_update_keeps_all_existing_analysis_endpoints(self) -> None:
        html = index_html()

        self.assertIn('class="workspace-tabs"', html)
        self.assertIn('onclick="updateActiveView()"', html)
        self.assertIn('decision:runDecisionEngine', html)
        self.assertIn("function runDecisionEngine()", html)
        self.assertIn("/decision-engine", html)
        self.assertIn("renderDecisionEngine", html)
        self.assertIn("stock_pool_decision_engine", html)
        self.assertIn("formatProbability", html)
        self.assertIn("market_index_symbol", html)
        self.assertIn("marketRegime", html)
        self.assertIn("regimeConfidence", html)
        self.assertIn("strategyBias", html)
        self.assertIn("regimeEvidence", html)
        self.assertIn("momentum_20_pct", html)
        self.assertIn("vs_index_20_pct", html)
        self.assertIn("vs_pool_20_pct", html)
        self.assertIn("excess_market_20_pct", html)
        self.assertIn("excess_pool_median_20_pct", html)
        self.assertIn("ma20_deviation_pct", html)
        self.assertIn('quotes:analyzePool', html)
        self.assertIn("function analyzePool()", html)
        self.assertIn("/market-analysis", html)
        self.assertIn('chan:runChanAnalysis', html)
        self.assertIn("function runChanAnalysis()", html)
        self.assertIn("/chan-analysis", html)
        self.assertIn("renderChanAnalysis", html)
        self.assertIn("stock_pool_chan_analysis", html)
        self.assertIn("marketDataSource", html)
        self.assertIn("renderPoolAnalysis", html)
        self.assertNotIn('onclick="generateSignals()"', html)
        self.assertNotIn('id="newPoolName"', html)
        self.assertNotIn('onclick="createPool()"', html)
        self.assertNotIn("function createPool()", html)

    def test_stock_pool_workflow_labels_are_user_facing(self) -> None:
        html = index_html()

        self.assertIn("持仓决策引擎", html)
        self.assertIn("分析股票池行情", html)
        self.assertIn("缠论结构分析", html)
        self.assertIn("加入持仓", html)
        self.assertIn("分析结果", html)
        self.assertIn("analysis-panel", html)
        self.assertIn("analysisResultFocus", html)
        self.assertIn("analysisResultHint", html)
        self.assertIn('id="actionStatus"', html)
        self.assertIn("priority: \"优先级\"", html)
        self.assertIn("status: \"状态\"", html)
        self.assertIn("watching: \"观察中\"", html)
        self.assertIn("function priorityLabel", html)
        self.assertIn("watchlistTable", html)
        self.assertIn("addHoldingFromWatchlist", html)
        self.assertIn("trigger", html)
        self.assertIn("invalidation", html)
        self.assertIn("extended_above_center", html)
        self.assertIn("extended_below_center", html)

    def test_trade_signal_panel_is_not_rendered_as_primary_ui(self) -> None:
        html = index_html()

        self.assertNotIn('id="signals"', html)
        self.assertNotIn('id="signalView"', html)
        self.assertNotIn('class="panel signals-panel"', html)
        self.assertNotIn('onclick="generateSignals()"', html)

    def test_backtest_panel_is_not_rendered_as_primary_ui(self) -> None:
        html = index_html()

        self.assertNotIn("MA/成交量回测", html)
        self.assertNotIn("MA/Volume Backtest", html)
        self.assertNotIn('class="panel backtest-panel"', html)
        self.assertNotIn('id="backtest"', html)
        self.assertNotIn('onclick="runBacktest()"', html)
        self.assertNotIn("function runBacktest()", html)
        self.assertNotIn("function renderBacktest", html)

    def test_daily_review_renders_detail_tables(self) -> None:
        html = index_html()

        self.assertIn("holdingDetails", html)
        self.assertIn("highRiskSignalDetails", html)
        self.assertIn("recentSignalDetails", html)
        self.assertIn("failedFetchDetails", html)
        self.assertIn("mapSignalDetailRows", html)
        self.assertIn("formatOptionalPrice", html)
        self.assertIn('["symbol", "signal_type", "action", "risk_level", "price", "created_at", "reasons", "next_check"]', html)

    def test_holdings_panel_shows_price_pnl_and_editable_quantity(self) -> None:
        html = index_html()

        self.assertIn("current_price", html)
        self.assertIn("market_value", html)
        self.assertIn("estimated_pnl", html)
        self.assertIn("estimated_pnl_pct", html)
        self.assertIn("total_cost_basis", html)
        self.assertIn("total_market_value", html)
        self.assertIn("total_estimated_pnl", html)
        self.assertIn("total_estimated_pnl_pct", html)
        self.assertIn("holdingsSummary", html)
        self.assertIn("summarizeHoldings", html)
        self.assertIn('class="holdings-summary"', html)
        self.assertIn('class="summary-stat"', html)
        self.assertIn("saveHoldingEdit", html)
        self.assertIn('method: "PATCH"', html)
        self.assertIn('class="quantity-input"', html)
        self.assertIn('class="price-input"', html)
        self.assertIn("cost_price: costPrice", html)
        self.assertIn('class="holdings-table"', html)
        self.assertIn('class="number-cell"', html)
        self.assertIn("white-space: nowrap", html)
        self.assertIn("formatMoney", html)
        self.assertNotIn('table(latestRows, ["id", "symbol", "name", "quantity", "cost_price", "stop_loss", "take_profit"])', html)


if __name__ == "__main__":
    unittest.main()
