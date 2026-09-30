from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import HTTPException
from pydantic import ValidationError

from services.api.app.database import connect, init_db
from services.api.app.main import (
    _fetch_kline_and_cache,
    api_analyze_stock_pool_with_decision_engine,
    api_analyze_stock_pool_with_market_source,
    api_generate_daily_review,
    api_generate_workbench_actions,
)
from services.api.app.repository import (
    create_analysis_report,
    create_holding,
    create_stock_pool,
    create_watchlist_item,
    filter_rows_by_symbols,
    get_default_stock_pool,
    upsert_market_klines,
)
from services.api.app.schemas import (
    StockPoolDecisionEngineRequest,
    StockPoolMarketAnalysisRequest,
    WorkbenchActionRequest,
)


def bar(day: str, price: float = 10) -> dict:
    return {"trade_date": day, "open": price, "high": price, "low": price, "close": price}


class AnalysisIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(self.tmp.name) / "integrity.db"
        init_db(path)
        self.db = connect(path)
        self.pool = get_default_stock_pool(self.db)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_empty_filter_is_distinct_from_unscoped_filter(self) -> None:
        rows = [{"symbol": "600519"}]
        self.assertEqual(filter_rows_by_symbols(rows, set()), [])
        self.assertEqual(filter_rows_by_symbols(rows, None), rows)

    def test_empty_pool_analysis_never_includes_external_holdings(self) -> None:
        create_holding(self.db, {"symbol": "600519", "quantity": 100, "cost_price": 10})
        market = api_analyze_stock_pool_with_market_source(
            self.pool["id"], StockPoolMarketAnalysisRequest(source="mock", persist=False), self.db
        )
        self.assertEqual(market["payload"]["items"], [])
        decision = api_analyze_stock_pool_with_decision_engine(
            self.pool["id"],
            StockPoolDecisionEngineRequest(source="mock", persist=False, market_index_symbol=None),
            self.db,
        )
        self.assertEqual(decision["payload"]["items"], [])

    def test_empty_action_pool_does_not_generate_external_signals(self) -> None:
        create_holding(self.db, {"symbol": "600519", "quantity": 100, "cost_price": 10})
        output = api_generate_workbench_actions(
            WorkbenchActionRequest(pool_id=self.pool["id"], prices={"600519": 12}, persist=False), self.db
        )
        self.assertEqual(output["total_holdings"], 0)
        self.assertEqual(output["signals"], [])

    def test_fresh_kline_response_contains_only_fetched_dates(self) -> None:
        upsert_market_klines(self.db, symbol="600519", source="mock", period="daily",
                             bars=[bar("2026-06-19", 19), bar("2026-06-20", 20)])
        provider = mock.Mock(name="provider")
        provider.name = "mock"
        provider.fetch_kline.return_value = [bar("2026-06-10"), bar("2026-06-11")]
        with mock.patch("services.api.app.main.get_market_data_provider", return_value=provider):
            output = _fetch_kline_and_cache(self.db, symbol="600519", source="mock", limit=2)
        self.assertEqual([row["trade_date"] for row in output["bars"]], ["2026-06-10", "2026-06-11"])

    def test_empty_fetched_batch_is_not_a_successful_cached_response(self) -> None:
        upsert_market_klines(self.db, symbol="600519", source="mock", period="daily",
                             bars=[bar("2026-06-20")])
        provider = mock.Mock()
        provider.name = "mock"
        provider.fetch_kline.return_value = []
        with mock.patch("services.api.app.main.get_market_data_provider", return_value=provider):
            with self.assertRaises(HTTPException) as caught:
                _fetch_kline_and_cache(self.db, symbol="600519", source="mock")
        self.assertEqual(caught.exception.status_code, 502)

    def test_duplicate_members_do_not_consume_analysis_limit(self) -> None:
        for symbol in ["600519", "600519", "000001"]:
            create_watchlist_item(self.db, {"pool_id": self.pool["id"], "symbol": symbol,
                                            "priority": 1 if symbol == "600519" else 2})
        calls = []
        def quote(_db, *, symbol, source):
            calls.append(symbol)
            return {"symbol": symbol, "price": 10, "source": source, "fetched_at": "now"}
        with mock.patch("services.api.app.main._fetch_quote_and_cache", side_effect=quote):
            output = api_analyze_stock_pool_with_market_source(
                self.pool["id"], StockPoolMarketAnalysisRequest(source="mock", persist=False, max_symbols=2), self.db
            )
        self.assertEqual(set(calls), {"600519", "000001"})
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(output["payload"]["items"]), 2)

    def test_review_reads_saved_decision_for_selected_pool(self) -> None:
        create_watchlist_item(self.db, {"pool_id": self.pool["id"], "symbol": "600519"})
        saved = create_analysis_report(self.db, report_type="stock_pool_decision_engine", payload={
            "report_type": "stock_pool_decision_engine", "pool": {"id": self.pool["id"]},
            "generated_at": "2026-09-30T01:00:00+00:00", "tool_plan": {"data_source": "mock"},
            "items": [{"symbol": "600519", "probabilities": {"up": .6, "range": .3, "down": .1},
                       "decision": {"key": "watch_candidate"}}],
        })
        output = api_generate_daily_review(persist=False, signal_limit=100, pool_id=self.pool["id"], db=self.db)
        self.assertIn("analysis_report_id", output["payload"])
        self.assertEqual(output["payload"]["analysis_report_id"], saved["id"])
        self.assertEqual(output["payload"]["decision_analysis"]["items"][0]["symbol"], "600519")

    def test_request_uses_exchange_qualified_index_and_fixed_horizon(self) -> None:
        request = StockPoolDecisionEngineRequest()
        self.assertEqual(request.market_index_symbol, "SH000300")
        with self.assertRaises(ValidationError):
            StockPoolDecisionEngineRequest(horizon_days=120)
        with self.assertRaises(ValidationError):
            StockPoolDecisionEngineRequest(period="weekly")

    def test_scoped_review_without_saved_analysis_is_explicit(self) -> None:
        create_watchlist_item(self.db, {"pool_id": self.pool["id"], "symbol": "600519"})
        output = api_generate_daily_review(persist=False, signal_limit=100,
                                          pool_id=self.pool["id"], source="mock", db=self.db)
        self.assertEqual(output["payload"]["decision_review_status"], "not_analyzed")
        self.assertNotIn("decision_analysis", output["payload"])
        self.assertIn("决策引擎", output["payload"]["summary"])

    def test_decision_report_records_its_input_snapshots(self) -> None:
        create_watchlist_item(self.db, {"pool_id": self.pool["id"], "symbol": "600519"})
        calculated = {"report_type": "stock_pool_decision_engine", "pool": {"id": self.pool["id"]},
                      "tool_plan": {"data_source": "mock"}, "scope": {}, "items": []}
        with mock.patch("services.api.app.main.generate_stock_pool_decision_engine", return_value=calculated):
            report = api_analyze_stock_pool_with_decision_engine(
                self.pool["id"], StockPoolDecisionEngineRequest(source="mock", persist=False), self.db
            )["payload"]
        self.assertIn("data_refs", report)
        refs = report["data_refs"]
        self.assertIsNotNone(refs["quotes"][0]["snapshot_id"])
        self.assertEqual(refs["quotes"][0]["symbol"], "600519")
        self.assertEqual(refs["market_index"]["symbol"], "SH000300")
        self.assertIsNotNone(refs["klines"][0]["as_of"])

    def test_decision_comparison_is_scoped_to_source_and_pool(self) -> None:
        create_watchlist_item(self.db, {"pool_id": self.pool["id"], "symbol": "600519"})
        first = api_analyze_stock_pool_with_decision_engine(
            self.pool["id"], StockPoolDecisionEngineRequest(source="mock", persist=True), self.db
        )
        other_pool = create_stock_pool(self.db, {"name": "Other"})
        create_analysis_report(self.db, report_type="stock_pool_decision_engine", payload={
            **first["payload"], "pool": {"id": other_pool["id"]},
        })
        create_analysis_report(self.db, report_type="stock_pool_decision_engine", payload={
            **first["payload"], "tool_plan": {"data_source": "other"},
        })
        second = api_analyze_stock_pool_with_decision_engine(
            self.pool["id"], StockPoolDecisionEngineRequest(source="mock", persist=False), self.db
        )
        comparison = second["payload"]["comparison"]
        self.assertEqual(comparison["previous_report_id"], first["id"])
        self.assertEqual(comparison["items"][0]["symbol"], "600519")
        self.assertEqual(comparison["items"][0]["probability_changes"], {"up": 0, "range": 0, "down": 0})

    def test_unknown_review_pool_is_not_an_empty_valid_pool(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            api_generate_daily_review(persist=False, signal_limit=100, pool_id=999, db=self.db)
        self.assertEqual(caught.exception.status_code, 404)

    def test_members_added_during_fetch_do_not_change_analysis_scope(self) -> None:
        create_watchlist_item(self.db, {"pool_id": self.pool["id"], "symbol": "600519"})
        def quote(_db, *, symbol, source):
            create_watchlist_item(self.db, {"pool_id": self.pool["id"], "symbol": "000001"})
            return {"symbol": symbol, "price": 10, "source": source}
        with mock.patch("services.api.app.main._fetch_quote_and_cache", side_effect=quote):
            output = api_analyze_stock_pool_with_market_source(
                self.pool["id"], StockPoolMarketAnalysisRequest(source="mock", persist=False), self.db
            )
        self.assertEqual([item["symbol"] for item in output["payload"]["items"]], ["600519"])


if __name__ == "__main__":
    unittest.main()
