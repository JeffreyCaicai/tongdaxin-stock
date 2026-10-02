from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import tempfile
import time
import threading
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from services.api.app.database import connect, init_db, get_db
from services.api.app.main import app
from services.api.app.opportunity_jobs import recover_runs

from services.api.tests.test_opportunity_horizons import daily_bars


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.report = {"generated_at": "2026-01-05T08:00:00+00:00", "source": "tdx-official",
                       "model_version": "market_opportunities_v1", "benchmark": "SH000300",
                       "price_basis": {"tdx_kline_TQFlag": 11}, "selected": ["600001"],
                       "items": [{"symbol": "600001", "name": "A", "level": "priority", "origin": "new"},
                                 {"symbol": "600002", "name": "B", "level": "not_selected", "origin": "held"}]}
        self.stock = daily_bars([10, 100, 12, 9, 10, 11, 13], start=date(2026, 1, 2))
        self.stock[2]["open"] = 10
        self.stock[2]["low"] = 9.9
        self.index = daily_bars([100, 100, 100, 101, 102, 103, 110], start=date(2026, 1, 2))

    def evaluate(self, **overrides):
        module = "services.api.app.opportunity_tracking"
        self.assertIsNotNone(importlib.util.find_spec(module), "Recommendation outcome tracking is missing")
        args = dict(report=self.report, klines={"600001": self.stock, "600002": self.stock},
                    index_bars=self.index, as_of="2026-01-12T16:00:00+08:00")
        args.update(overrides)
        return importlib.import_module(module).evaluate_followup(**args)

    def test_next_session_open_same_window_and_pending_denominator(self):
        result = self.evaluate()
        row = result["items"][0]["outcomes"]["5"]
        self.assertEqual(row["status"], "matured")
        self.assertEqual((row["start_date"], row["end_date"]), ("2026-01-06", "2026-01-12"))
        self.assertAlmostEqual(row["return_pct"], 30)
        self.assertAlmostEqual(row["benchmark_return_pct"], 10)
        self.assertAlmostEqual(row["excess_pp"], 20)
        self.assertAlmostEqual(row["max_drawdown_pct"], -25)
        self.assertEqual(result["items"][0]["outcomes"]["20"]["status"], "pending")
        self.assertEqual(result["summary"]["5"]["selected"]["matured"], 1)
        self.assertEqual(result["summary"]["5"]["not_selected"]["matured"], 1)
        self.assertIsNone(result["summary"]["20"]["selected"]["positive_fraction"])

    def test_missing_stock_session_is_unavailable_not_zero_or_false_success(self):
        result = self.evaluate(klines={"600001": self.stock[:3] + self.stock[4:]})
        self.assertEqual(result["items"][0]["outcomes"]["5"]["status"], "unavailable")
        self.assertIsNone(result["items"][0]["outcomes"]["5"]["return_pct"])
        self.assertEqual(result["summary"]["5"]["selected"]["matured"], 0)

    def test_unmatured_windows_reject_missing_or_invalid_observed_stock_data(self):
        invalid_price = copy.deepcopy(self.stock)
        invalid_price[3]["close"] = None
        no_volume = copy.deepcopy(self.stock)
        no_volume[3]["volume"] = 0
        missing_volume = copy.deepcopy(self.stock)
        missing_volume[3]["volume"] = None
        cases = [
            ([], "missing_stock_sessions"),
            (self.stock[:3] + self.stock[4:], "missing_stock_sessions"),
            (invalid_price, "invalid_daily_data"),
            (no_volume, "inactive_period_sessions"),
            (missing_volume, "inactive_period_sessions"),
            (self.stock + [self.stock[3]], "duplicate_dates"),
        ]
        # Only Jan 6, 7 and 8 have elapsed; none of the four windows is mature.
        for stock, issue in cases:
            with self.subTest(issue=issue, bars=len(stock)):
                result = self.evaluate(klines={"600001": stock}, as_of="2026-01-08T16:00:00+08:00")
                for horizon in ("5", "20", "60", "120"):
                    outcome = result["items"][0]["outcomes"][horizon]
                    self.assertEqual(outcome["status"], "unavailable")
                    self.assertIn(issue, outcome["issues"])
                    self.assertEqual(outcome["start_date"], "2026-01-06")
                    self.assertIsNone(outcome["end_date"])
                    for metric in ("reference_open", "end_close", "return_pct", "benchmark_return_pct",
                                   "excess_pp", "max_drawdown_pct"):
                        self.assertIsNone(outcome[metric])
                    self.assertEqual(result["summary"][horizon]["selected"]["pending"], 0)
                    self.assertEqual(result["summary"][horizon]["selected"]["unavailable"], 1)
                    self.assertEqual(result["period_summary"][horizon]["legacy"]["unavailable"], 2)

    def test_pending_requires_only_sessions_completed_so_far(self):
        for as_of, stock in (("2026-01-05T16:00:00+08:00", []),
                             ("2026-01-08T14:59:00+08:00", self.stock[:4]),
                             ("2026-01-08T16:00:00+08:00", self.stock[:5])):
            with self.subTest(as_of=as_of):
                result = self.evaluate(klines={"600001": stock}, as_of=as_of)
                for outcome in result["items"][0]["outcomes"].values():
                    self.assertEqual(outcome["status"], "pending")
                    self.assertEqual(outcome["issues"], [])
                    self.assertIsNone(outcome["return_pct"])

    def test_pending_ignores_dated_stock_defects_before_the_observation_window(self):
        invalid_history = copy.deepcopy(self.stock)
        invalid_history[0]["close"] = None
        invalid_signal_day = copy.deepcopy(self.stock)
        invalid_signal_day[1]["low"] = 0
        for stock in (invalid_history, invalid_signal_day, self.stock + [self.stock[0]]):
            for as_of in ("2026-01-05T16:00:00+08:00", "2026-01-08T16:00:00+08:00"):
                with self.subTest(as_of=as_of, bars=len(stock)):
                    result = self.evaluate(klines={"600001": stock}, as_of=as_of)
                    for outcome in result["items"][0]["outcomes"].values():
                        self.assertEqual(outcome["status"], "pending")
                        self.assertEqual(outcome["issues"], [])

    def test_longer_window_gap_does_not_erase_matured_short_window(self):
        stock = daily_bars([10] * 10, start=date(2026, 1, 2))
        index = daily_bars([100] * 10, start=date(2026, 1, 2))
        result = self.evaluate(klines={"600001": stock[:7] + stock[8:]}, index_bars=index,
                               as_of="2026-01-15T16:00:00+08:00")
        outcomes = result["items"][0]["outcomes"]
        self.assertEqual(outcomes["5"]["status"], "matured")
        self.assertEqual(outcomes["5"]["return_pct"], 0)
        self.assertEqual(outcomes["5"]["end_date"], "2026-01-12")
        self.assertEqual(outcomes["20"]["status"], "unavailable")
        self.assertIn("missing_stock_sessions", outcomes["20"]["issues"])

    def test_shanghai_signal_date_and_intraday_close_cutoff(self):
        report = {**self.report, "generated_at": "2026-01-05T17:00:00+00:00"}
        result = self.evaluate(report=report)
        self.assertEqual(result["signal_date"], "2026-01-06")
        self.assertEqual(result["items"][0]["outcomes"]["5"]["status"], "pending")
        result = self.evaluate(as_of="2026-01-12T14:59:00+08:00")
        self.assertEqual(result["items"][0]["outcomes"]["5"]["status"], "pending")

    def test_truncated_calendar_invalid_basis_and_duplicate_dates_rejected(self):
        for overrides in ({"index_bars": self.index[2:]},
                          {"index_bars": self.index + [self.index[-1]]},
                          {"report": {**self.report, "price_basis": {}}}):
            with self.subTest(overrides=overrides):
                result = self.evaluate(**overrides)
                self.assertEqual(result["items"][0]["outcomes"]["5"]["status"], "unavailable")

    def test_snapshot_is_not_mutated_and_rebased_prices_keep_same_returns(self):
        before = copy.deepcopy(self.report)
        rebased = [{**r, **{k: r[k] * .5 for k in ("open", "high", "low", "close")}} for r in self.stock]
        result = self.evaluate(klines={"600001": rebased})
        self.assertEqual(result["items"][0]["outcomes"]["5"]["return_pct"], 30)
        self.assertEqual(before, self.report)
        self.assertIsNone(result["items"][0]["period_assessments"])

    def test_period_cohorts_and_legacy_are_separated(self):
        report = copy.deepcopy(self.report)
        report["items"][0]["period_assessments"] = {"5": {"stance": "avoid"}}
        result = self.evaluate(report=report)
        self.assertEqual(result["period_summary"]["5"]["avoid"]["matured"], 1)
        self.assertEqual(result["period_summary"]["5"]["legacy"]["matured"], 1)
        self.assertEqual(result["period_summary"]["5"]["favorable"]["matured"], 0)

    def test_benchmark_gap_cannot_shorten_a_known_stock_window(self):
        # Stock traded Jan 7, so a missing benchmark Jan 7 is not a holiday.
        index = self.index[:3] + self.index[4:]
        result = self.evaluate(index_bars=index)
        outcome = result["items"][0]["outcomes"]["5"]
        self.assertEqual(outcome["status"], "unavailable")
        self.assertIn("missing_benchmark_sessions", outcome["issues"])

    def test_naive_timestamp_and_zero_volume_are_unavailable(self):
        result = self.evaluate(report={**self.report,"generated_at":"2026-01-05T08:00:00"})
        self.assertIn("invalid_snapshot_time", result["items"][0]["outcomes"]["5"]["issues"])
        stock = copy.deepcopy(self.stock)
        stock[3]["volume"] = 0
        result = self.evaluate(klines={"600001":stock})
        self.assertEqual(result["items"][0]["outcomes"]["5"]["status"], "unavailable")


class TrackingApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.db"
        init_db(self.path)
        self.db = connect(self.path)
        self.addCleanup(self.db.close)
        self.report = {"generated_at": "2026-01-05T08:00:00+00:00", "source": "tdx-official",
                       "model_version": "market_opportunities_v1", "benchmark": "SH000300",
                       "price_basis": {"tdx_kline_TQFlag": 11}, "selected": ["600001"],
                       "items": [{"symbol": "600001", "level": "priority"}]}
        self.original = json.dumps(self.report)
        self.db.execute("INSERT INTO opportunity_runs VALUES ('old',1,'tdx-official','completed',?,?,?,?)",
                        (self.report["generated_at"], self.report["generated_at"], "{}", self.original))
        self.db.commit()
        def dependency():
            db = connect(self.path)
            try:
                yield db
            finally:
                db.close()
        app.dependency_overrides[get_db] = dependency
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)

    def wait_for_job(self):
        for _ in range(200):
            result = self.client.get("/opportunities/old/followup").json()
            if result["status"] not in {"queued", "running"}:
                return result
            time.sleep(.01)
        self.fail("Follow-up did not finish")

    def test_followup_read_is_readonly_refresh_persists_without_rewriting_scan(self):
        response = self.client.get("/opportunities/old/followup")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "not_started")
        self.assertEqual(self.db.execute("SELECT count(*) FROM opportunity_followups").fetchone()[0], 0)
        class Provider:
            def fetch_kline(self, symbol, *, limit):
                return daily_bars([10 + i for i in range(140)], start=date(2026, 1, 2))
        with patch("services.api.app.opportunity_tracking_jobs.get_market_data_provider", return_value=Provider()):
            response = self.client.post("/opportunities/old/followup")
            self.assertEqual(response.status_code, 202)
            result = self.wait_for_job()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"]["summary"]["5"]["selected"]["matured"], 1)
        self.assertEqual(self.db.execute("SELECT result_json FROM opportunity_runs WHERE id='old'").fetchone()[0], self.original)
        self.assertEqual(self.db.execute("SELECT count(*) FROM watchlist").fetchone()[0], 0)

    def test_errors_are_sanitized_and_no_success_returns_for_missing_prices(self):
        self.assertEqual(self.client.get("/opportunities/old/followup").status_code, 200)
        with patch("services.api.app.opportunity_tracking_jobs.get_market_data_provider", side_effect=RuntimeError("secret-token")):
            self.assertEqual(self.client.post("/opportunities/old/followup").status_code, 202)
            result = self.wait_for_job()
        self.assertNotIn("secret-token", str(result))
        self.assertEqual(result["result"]["summary"]["5"]["selected"]["unavailable"], 1)

    def test_stock_fetch_failure_before_maturity_is_saved_as_unavailable(self):
        class Provider:
            def fetch_kline(self, symbol, *, limit):
                if symbol != "SH000300":
                    raise RuntimeError("private-provider-detail")
                return daily_bars([100] * 5, start=date(2026, 1, 2))
        with patch("services.api.app.opportunity_tracking_jobs.get_market_data_provider", return_value=Provider()), \
             patch("services.api.app.opportunity_tracking_jobs.utc_now", return_value="2026-01-08T08:00:00+00:00"):
            self.assertEqual(self.client.post("/opportunities/old/followup").status_code, 202)
            result = self.wait_for_job()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"]["failures"], [{"symbol": "600001", "kind": "kline_unavailable"}])
        self.assertNotIn("private-provider-detail", str(result))
        for outcome in result["result"]["items"][0]["outcomes"].values():
            self.assertEqual(outcome["status"], "unavailable")
            self.assertIn("missing_stock_sessions", outcome["issues"])
        self.assertEqual(self.db.execute("SELECT result_json FROM opportunity_runs WHERE id='old'").fetchone()[0], self.original)

    def test_failed_refresh_keeps_saved_result_and_its_evaluation_time(self):
        saved = json.dumps({"evaluated_at": "2026-01-08T08:00:00Z", "items": [], "summary": {}})
        self.db.execute("INSERT INTO opportunity_followups VALUES ('old','completed',?,?,?,?)",
                        ("2026-01-08T08:00:00Z", "2026-01-08T08:00:00Z", "{}", saved))
        self.db.commit()
        class MalformedProvider:
            def fetch_kline(self, symbol, *, limit):
                return None
        with patch("services.api.app.opportunity_tracking_jobs.get_market_data_provider", return_value=MalformedProvider()):
            self.assertEqual(self.client.post("/opportunities/old/followup").status_code, 202)
            result = self.wait_for_job()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["result"]["evaluated_at"], "2026-01-08T08:00:00Z")
        self.assertEqual(self.db.execute("SELECT result_json FROM opportunity_followups WHERE run_id='old'").fetchone()[0], saved)
        self.assertEqual(self.db.execute("SELECT result_json FROM opportunity_runs WHERE id='old'").fetchone()[0], self.original)

    def test_missing_incomplete_and_cancel_recovery(self):
        self.assertEqual(self.client.get("/opportunities/missing/followup").status_code, 404)
        self.db.execute("UPDATE opportunity_runs SET status='running' WHERE id='old'")
        self.db.commit()
        self.assertEqual(self.client.post("/opportunities/old/followup").status_code, 409)
        self.db.execute("UPDATE opportunity_runs SET status='completed' WHERE id='old'")
        saved = json.dumps({"evaluated_at": "2026-01-08T08:00:00Z", "items": [], "summary": {}})
        self.db.execute("INSERT INTO opportunity_followups VALUES ('old','completed',?,?,?,?)",
                        ("2026-01-08T08:00:00Z", "2026-01-08T08:00:00Z", "{}", saved))
        self.db.commit()
        entered, release = threading.Event(), threading.Event()
        class Provider:
            def fetch_kline(self, symbol, *, limit):
                entered.set()
                release.wait(3)
                return []
        try:
            with patch("services.api.app.opportunity_tracking_jobs.get_market_data_provider", return_value=Provider()):
                self.assertEqual(self.client.post("/opportunities/old/followup").status_code, 202)
                self.assertTrue(entered.wait(3))
                self.assertTrue(self.client.delete("/opportunities/old/followup").json()["cancel_requested"])
                release.set()
                self.assertEqual(self.wait_for_job()["status"], "cancelled")
                self.assertEqual(self.db.execute("SELECT result_json FROM opportunity_followups WHERE run_id='old'").fetchone()[0], saved)
        finally:
            release.set()
        self.db.execute("UPDATE opportunity_followups SET status='running'")
        self.db.commit()
        recover_runs(self.db)
        self.assertEqual(self.client.get("/opportunities/old/followup").json()["status"], "interrupted")
        self.assertEqual(self.db.execute("SELECT result_json FROM opportunity_followups WHERE run_id='old'").fetchone()[0], saved)


if __name__ == "__main__":
    unittest.main()
