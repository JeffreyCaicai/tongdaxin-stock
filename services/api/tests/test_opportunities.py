from __future__ import annotations

import copy
import tempfile
import time
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from services.api.app.database import connect, init_db, get_db
from services.api.app.main import app
from services.api.app.opportunity_discovery import parse_screen, discover_candidates, canonical_stock
from services.api.app.opportunities import merge_candidates, build_opportunity_report, classify
from services.api.app.opportunity_jobs import read_run, recover_runs, start_run, cancel_run
from services.api.app.market_data import MarketDataError
from services.api.app.decision_engine import generate_stock_pool_decision_engine
from services.api.tests.test_decision_engine import trend_bars


class DiscoveryTests(unittest.TestCase):
    def test_exchange_aliases_and_stock_scope(self):
        self.assertEqual(canonical_stock("SH600036"), "600036")
        self.assertEqual(canonical_stock("1.600036"), "600036")
        self.assertEqual(canonical_stock("920001", "2"), "BJ920001")
        self.assertIsNone(canonical_stock("920001", "1"))
        self.assertIsNone(canonical_stock("SH000300"))
        self.assertIsNone(canonical_stock("510300"))
        rows=merge_candidates([{"symbol":"600036"}], [{"symbol":"SH600036"}], [],40)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["origin"],"watched")

    def test_strict_table_and_code_identity(self):
        raw = [[0,"",4,"",4], ["sec_code","sec_name","market"], [],
               ["000001","Stock","0"], ["600036","Bank","1"],
               ["000300","Index","1"], ["510300","ETF","1"]]
        self.assertEqual([x["symbol"] for x in parse_screen(raw)["items"]], ["000001","600036"])
        for bad in ({"error":"token"}, [[-1,"denied",0,"",0],[],[]], [[0,"",0,"",0],["unknown"],[]]):
            with self.assertRaises(MarketDataError): parse_screen(bad)

    def test_partial_discovery_and_no_raw_errors(self):
        raw = [[0,"",1,"",1],["sec_code","sec_name","market"],[],["600036","Bank","1"]]
        with patch("services.api.app.opportunity_discovery._tdx_official_post", side_effect=[raw, RuntimeError("secret"), raw]):
            result = discover_candidates("tdx-official", 40)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertNotIn("secret", str(result))

    def test_merge_deduplicates_and_never_caps_personal_stocks(self):
        pool = [{"symbol":f"600{i:03}","name":"X"} for i in range(110)]
        rows = merge_candidates([{"symbol":"600000"},{"symbol":"000333"},{"symbol":"600999"}], pool,
                                [{"symbol":"600000","quantity":5,"cost_price":999}], 1)
        self.assertEqual(len(rows),111)
        self.assertEqual(rows[0]["origin"],"held")
        self.assertEqual(rows[-1]["symbol"],"000333")


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch("services.api.app.decision_engine.utc_now", return_value="2026-05-01T00:00:00+00:00")
        self.clock.start(); self.addCleanup(self.clock.stop)
        self.bars = trend_bars(days=150, step=.12)
        self.quote = {"symbol":"600036","name":"Bank","price":self.bars[-1]["close"],"volume":1000000,
                      "amount":100000000,"fetched_at":"2026-04-30T15:00:00+00:00"}
        self.args = dict(pool={"id":1,"name":"Pool"},watchlist=[{"symbol":"600036"}],holdings=[],
                         quotes={"600036":self.quote},kline_by_symbol={"600036":self.bars},source="mock",
                         index_bars=trend_bars(days=150,step=.04),market_index_symbol="SH000300",asset_only=True)

    def test_scores_independent_of_cost_and_other_candidates(self):
        base = generate_stock_pool_decision_engine(**self.args)["items"][0]
        changed = copy.deepcopy(self.args)
        changed["holdings"] = [{"symbol":"600036","quantity":900,"cost_price":1}]
        changed["watchlist"].append({"symbol":"000333"})
        changed["quotes"]["000333"] = {**self.quote,"symbol":"000333","pct_change":-90}
        changed["kline_by_symbol"]["000333"] = trend_bars(days=150,step=-.3)
        result = generate_stock_pool_decision_engine(**changed)["items"][0]
        self.assertEqual(base["probabilities"], result["probabilities"])
        self.assertEqual(base["prior"], result["prior"])
        self.assertIsNone(result["position"])

    def test_quality_gates_and_empty_shortlist(self):
        args = dict(candidates=[{"symbol":"600036","origin":"new"}], quotes={"600036":self.quote},
                    klines={"600036":self.bars}, index_bars=self.args["index_bars"], source="mock",
                    discovery={},failures=[],pool=self.args["pool"])
        args["quotes"]["600036"] = {**self.quote,"amount":None}
        report = build_opportunity_report(**args)
        self.assertEqual(report["selected"],[])
        self.assertIn("low_or_unknown_liquidity",report["items"][0]["selection_reasons"])
        args["quotes"]["600036"] = self.quote
        args["index_bars"] = []
        report = build_opportunity_report(**args)
        self.assertEqual(report["selected"],[])
        self.assertIn("missing_index",report["items"][0]["selection_reasons"])

    def test_priority_and_extended_wait(self):
        item = generate_stock_pool_decision_engine(**self.args)["items"][0]
        item["probabilities"] = {"up":.65,"range":.25,"down":.10}
        item["decision"]["risk_level"] = "medium"
        item["indicator"]["rsi14"] = 60
        self.assertEqual(classify(item,self.quote,self.bars)["level"], "priority")
        item["indicator"]["rsi14"] = 90
        self.assertEqual(classify(item,self.quote,self.bars)["level"], "wait")
        item["data_quality"]["issues"].append("stale_quote")
        self.assertEqual(classify(item,self.quote,self.bars)["level"], "excluded")

    def test_personal_etf_is_excluded_even_with_strong_scores(self):
        item = generate_stock_pool_decision_engine(**self.args)["items"][0]
        item.update(symbol="510300", probabilities={"up":.9,"range":.05,"down":.05})
        self.assertIn("outside_stock_scope",classify(item,self.quote,self.bars)["selection_reasons"])
        self.assertEqual(classify(item,self.quote,self.bars)["level"],"excluded")


class JobTests(unittest.TestCase):
    def test_cancel_during_scoring_cannot_commit_completed_result(self):
        entered, release = threading.Event(), threading.Event()
        def blocked_report(**kwargs):
            entered.set()
            release.wait(3)
            return {"items":[]}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.db";init_db(path);db=connect(path)
            try:
                with patch("services.api.app.opportunity_jobs.build_opportunity_report", side_effect=blocked_report):
                    run=start_run(db,path=path,pool={"id":1},watchlist=[],holdings=[],source="mock",limit=10)
                    self.assertTrue(entered.wait(3))
                    self.assertEqual(start_run(db,path=path,pool={"id":1},watchlist=[],holdings=[],source="mock",limit=10)["id"],run["id"])
                    self.assertTrue(cancel_run(run["id"]))
                    release.set()
                    for _ in range(100):
                        result=read_run(db,run["id"])
                        if result["status"] == "cancelled": break
                        time.sleep(.01)
                    self.assertEqual(result["status"],"cancelled")
                    self.assertIsNone(result["result"])
            finally:
                release.set();db.close()

    def test_persistence_and_restart_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.db"; init_db(path)
            db=connect(path)
            try:
                run=start_run(db,path=path,pool={"id":1,"name":"Test"},watchlist=[],holdings=[],source="mock",limit=10)
                for _ in range(100):
                    saved=read_run(db,run["id"])
                    if saved["status"] not in {"running","queued"}: break
                    time.sleep(.03)
                self.assertEqual(saved["status"],"completed")
                self.assertEqual(saved["result"]["scope"]["new"],3)
                self.assertEqual(db.execute("SELECT count(*) FROM watchlist").fetchone()[0],0)
                db.execute("UPDATE opportunity_runs SET status='running' WHERE id=?",(run["id"],)); db.commit()
                recover_runs(db)
                self.assertEqual(read_run(db,run["id"])["status"],"interrupted")
            finally: db.close()

    def test_api_validation_and_missing_job(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.db"; init_db(path)
            def temp_db():
                db=connect(path)
                try: yield db
                finally: db.close()
            app.dependency_overrides[get_db]=temp_db
            try:
                client=TestClient(app)
                self.assertEqual(client.post("/stock-pools/1/opportunities",json={"source":"eastmoney"}).status_code,422)
                self.assertEqual(client.post("/stock-pools/1/opportunities",json={"outside_limit":1000}).status_code,422)
                self.assertEqual(client.get("/opportunities/missing").status_code,404)
                self.assertEqual(client.get("/stock-pools/1/opportunities").json(),[])
            finally: app.dependency_overrides.clear()
