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

    def test_workbench_uses_selected_pool_as_primary_scope(self) -> None:
        html = index_html()

        self.assertIn('id="poolName"', html)
        self.assertIn("personalPool", html)
        self.assertIn("selectedPoolId", html)
        self.assertIn("poolHoldingsHint", html)
        self.assertIn("poolLatestSignalsHint", html)
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

        self.assertIn('class="pool-bar"', html)
        self.assertIn('class="toolbar pool-actions"', html)
        self.assertIn('onclick="analyzePool()"', html)
        self.assertIn("function analyzePool()", html)
        self.assertIn("/market-analysis", html)
        self.assertIn('onclick="runChanAnalysis()"', html)
        self.assertIn("function runChanAnalysis()", html)
        self.assertIn("/chan-analysis", html)
        self.assertIn("renderChanAnalysis", html)
        self.assertIn("stock_pool_chan_analysis", html)
        self.assertIn("marketDataSource", html)
        self.assertIn("renderPoolAnalysis", html)
        self.assertIn('onclick="generateSignals()"', html)
        self.assertNotIn('id="newPoolName"', html)
        self.assertNotIn('onclick="createPool()"', html)
        self.assertNotIn("function createPool()", html)

    def test_stock_pool_workflow_labels_are_user_facing(self) -> None:
        html = index_html()

        self.assertIn("分析股票池行情", html)
        self.assertIn("缠论结构分析", html)
        self.assertIn("生成持仓提示", html)
        self.assertIn("MA/成交量回测", html)
        self.assertIn("交易提示", html)
        self.assertIn("分析结果", html)
        self.assertIn("analysisResultHint", html)
        self.assertIn('id="actionStatus"', html)
        self.assertIn("priority: \"优先级\"", html)
        self.assertIn("status: \"状态\"", html)
        self.assertIn("watching: \"观察中\"", html)
        self.assertIn("function priorityLabel", html)
        self.assertIn("noTradeHints", html)
        self.assertIn("trigger", html)
        self.assertIn("invalidation", html)

    def test_generate_signals_uses_action_status_not_analysis_result(self) -> None:
        html = index_html()

        self.assertIn(
            'document.getElementById("actionStatus").textContent = t("operationDoneTemplate")',
            html,
        )
        self.assertNotIn(
            'document.getElementById("review").innerHTML = `<p class="summary">${t("generatedSignals")}',
            html,
        )

    def test_backtest_panel_explains_strategy_rules(self) -> None:
        html = index_html()

        self.assertIn("backtestHint", html)
        self.assertIn("backtestRuleTitle", html)
        self.assertIn("backtestEntryRule", html)
        self.assertIn("backtestExitRule", html)
        self.assertIn("backtestAssumption", html)
        self.assertIn("MA20", html)
        self.assertIn("成交量比", html)

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
        self.assertIn("saveHoldingQuantity", html)
        self.assertIn('method: "PATCH"', html)
        self.assertIn('class="quantity-input"', html)
        self.assertIn('class="holdings-table"', html)
        self.assertIn('class="number-cell"', html)
        self.assertIn("white-space: nowrap", html)
        self.assertIn("formatMoney", html)
        self.assertNotIn('table(latestRows, ["id", "symbol", "name", "quantity", "cost_price", "stop_loss", "take_profit"])', html)


if __name__ == "__main__":
    unittest.main()
