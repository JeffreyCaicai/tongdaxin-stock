from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from services.api.app.database import connect, init_db
from services.api.app.decision_engine import generate_stock_pool_decision_engine
from services.api.app.main import api_analyze_stock_pool_with_decision_engine
from services.api.app.repository import (
    create_holding,
    create_watchlist_item,
    get_default_stock_pool,
)
from services.api.app.schemas import StockPoolDecisionEngineRequest


def trend_bars(start_price: float = 80.0, days: int = 90, step: float = 0.45) -> list[dict]:
    start = date(2026, 4, 30) - timedelta(days=days - 1)
    bars: list[dict] = []
    for index in range(days):
        close = start_price + index * step
        bars.append(
            {
                "trade_date": (start + timedelta(days=index)).isoformat(),
                "open": close - 0.2,
                "high": close + 0.8,
                "low": close - 0.8,
                "close": close,
                "volume": 1000 + index * 10,
            }
        )
    return bars


def mixed_bars(
    start_price: float = 80.0,
    days: int = 90,
    step: float = 0.45,
    *,
    final_price: float | None = None,
    volume: float = 1000,
) -> list[dict]:
    bars = trend_bars(start_price=start_price, days=days, step=step)
    for index, bar in enumerate(bars):
        bar["volume"] = volume + index * 4
    if final_price is not None:
        bars[-1] = {
            **bars[-1],
            "open": final_price - 0.1,
            "high": final_price + 0.5,
            "low": final_price - 0.5,
            "close": final_price,
            "volume": volume * 0.62,
        }
    return bars


def factor_return_bars(
    *,
    latest_price: float = 100.0,
    return20_pct: float = 0.0,
    return60_pct: float = 0.0,
    days: int = 90,
) -> list[dict]:
    start = date(2026, 4, 30) - timedelta(days=days - 1)
    price_20 = latest_price / (1 + return20_pct / 100)
    price_60 = latest_price / (1 + return60_pct / 100)
    bars: list[dict] = []
    for index in range(days):
        if index <= days - 61:
            close = price_60
        elif index <= days - 21:
            progress = (index - (days - 61)) / 40
            close = price_60 + (price_20 - price_60) * progress
        else:
            progress = (index - (days - 21)) / 20
            close = price_20 + (latest_price - price_20) * progress
        bars.append(
            {
                "trade_date": (start + timedelta(days=index)).isoformat(),
                "open": close - 0.2,
                "high": close + 0.6,
                "low": close - 0.6,
                "close": close,
                "volume": 1200 + index * 5,
            }
        )
    return bars


class DecisionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        clock = mock.patch(
            "services.api.app.decision_engine.utc_now", return_value="2026-05-01T00:00:00+00:00"
        )
        clock.start()
        self.addCleanup(clock.stop)

    def report(self, *, bars=None, index=None, quotes=None, **kwargs) -> dict:
        return generate_stock_pool_decision_engine(
            pool={"id": 1, "name": "test"},
            watchlist=[{"symbol": "600519"}],
            holdings=[],
            quotes=quotes or {},
            kline_by_symbol=bars or {},
            index_bars=index or [],
            source="fixture",
            **kwargs,
        )

    def test_sparse_identical_prices_have_zero_shared_window_excess(self) -> None:
        index = trend_bars(days=121)
        stock = index[::2]
        item = self.report(bars={"600519": stock}, index=index)["items"][0]
        profile = item["factor_profile"]
        for sessions in (20, 60):
            self.assertEqual(profile["relative_strength"][f"vs_index_{sessions}_pct"], 0.0)
            self.assertEqual(profile["attribution"][f"excess_market_{sessions}_pct"], 0.0)
            window = profile["windows"][str(sessions)]
            self.assertEqual(window["start"], index[-sessions - 1]["trade_date"])
            self.assertEqual(window["end"], "2026-04-30")
            self.assertEqual(window["sessions"], sessions)
            self.assertEqual(window["calendar_source"], "index")
            self.assertEqual(window["stock"]["start_date"], window["start"])
            self.assertEqual(window["stock"]["end_date"], window["end"])
        self.assertEqual(profile["as_of"], "2026-04-30")

    def test_pool_calendar_does_not_expand_sparse_stock_window(self) -> None:
        calendar = trend_bars(days=121)
        profile = self.report(bars={"600519": calendar[::2], "688630": calendar})["items"][0]["factor_profile"]
        self.assertEqual(profile["windows"]["20"]["calendar_source"], "pool")
        self.assertEqual(profile["windows"]["20"]["start"], "2026-04-10")
        self.assertEqual(profile["relative_strength"]["vs_pool_20_pct"], 0.0)
        self.assertIsNone(profile["relative_strength"]["vs_index_20_pct"])

    def test_returns_use_at_or_before_endpoints_and_expose_lags(self) -> None:
        index = trend_bars(days=121)
        stock = [bar for bar in index if bar["trade_date"] not in {"2026-04-10", "2026-04-30"}]
        profile = self.report(bars={"600519": stock}, index=index)["items"][0]["factor_profile"]
        endpoint = profile["windows"]["20"]["stock"]
        self.assertEqual(endpoint["start_date"], "2026-04-09")
        self.assertEqual(endpoint["end_date"], "2026-04-29")
        self.assertEqual(endpoint["start_lag_sessions"], 1)
        self.assertEqual(endpoint["end_lag_sessions"], 1)
        expected = (stock[-1]["close"] / index[99]["close"] - 1) * 100
        self.assertAlmostEqual(profile["momentum"]["return20_pct"], expected, places=3)

    def test_short_calendar_cannot_label_shorter_return_as_20_sessions(self) -> None:
        item = self.report(bars={"600519": trend_bars(days=20)})["items"][0]
        self.assertIsNone(item["factor_profile"]["momentum"]["return20_pct"])
        self.assertEqual(item["factor_profile"]["windows"]["20"]["stock"]["status"], "insufficient")

    def test_missing_start_cannot_create_relative_or_attribution_evidence(self) -> None:
        index = trend_bars(days=121)
        item = self.report(bars={"600519": index[-10:]}, index=index)["items"][0]
        self.assertIsNone(item["factor_profile"]["attribution"]["stock_return20_pct"])
        self.assertIsNone(item["factor_profile"]["relative_strength"]["vs_index_20_pct"])
        self.assertEqual(item["factor_profile"]["windows"]["20"]["stock"]["status"], "missing")

    def test_stale_endpoints_are_excluded_from_pool_baseline(self) -> None:
        index = trend_bars(days=121)
        old = [{**bar, **{key: bar[key] * 3 for key in ("open", "high", "low", "close")}} for bar in index[:-10]]
        report = self.report(bars={"600519": old, "688630": index}, index=index)
        item = report["items"][0]
        self.assertIsNone(item["factor_profile"]["relative_strength"]["vs_index_20_pct"])
        self.assertEqual(item["factor_profile"]["windows"]["20"]["stock"]["status"], "stale")
        self.assertAlmostEqual(item["factor_profile"]["attribution"]["pool_average_return20_pct"], 7.2, places=2)
        self.assertEqual(item["decision"]["confidence"], "low")
        self.assertEqual(item["data_quality"]["status"], "stale")

    def test_no_kline_cannot_have_high_confidence_from_other_evidence(self) -> None:
        item = self.report(
            quotes={
                "600519": {"price": 100, "pct_change": 10, "fetched_at": "2026-05-01T00:00:00+00:00"},
                "688630": {"price": 100, "pct_change": 0},
            },
            market_regime={"regime": "uptrend", "strategy_bias": {"weights": {"trend": 10}}},
        )["items"][0]
        self.assertGreater(item["probabilities"]["up"], 0.58)
        self.assertEqual(item["decision"]["confidence"], "low")
        self.assertEqual(item["data_quality"]["status"], "insufficient")
        self.assertIn("missing_kline", item["data_quality"]["issues"])
        self.assertEqual(item["data_quality"]["bar_count"], 0)
        self.assertIsNone(item["data_quality"]["kline_as_of"])
        self.assertEqual(item["price_origin"], "quote")

    def test_insufficient_kline_confidence_is_low(self) -> None:
        bars = trend_bars(days=59, step=3)
        item = self.report(bars={"600519": bars}, index=trend_bars(days=121))["items"][0]
        self.assertEqual(item["data_quality"]["status"], "insufficient")
        self.assertIn("insufficient_kline", item["data_quality"]["issues"])
        self.assertEqual(item["decision"]["confidence"], "low")

    def test_wall_clock_stale_series_is_low_even_without_newer_benchmark(self) -> None:
        bars = trend_bars()
        with mock.patch("services.api.app.decision_engine.utc_now", return_value="2026-05-20T00:00:00+00:00"):
            item = self.report(bars={"600519": bars}, index=bars)["items"][0]
        self.assertEqual(item["data_quality"]["status"], "stale")
        self.assertIn("stale_kline", item["data_quality"]["issues"])
        self.assertEqual(item["decision"]["confidence"], "low")
        self.assertIsNone(item["factor_profile"]["relative_strength"]["vs_index_20_pct"])

    def test_complete_quality_includes_timestamps_and_counts(self) -> None:
        bars = trend_bars()
        item = self.report(
            bars={"600519": bars}, index=bars,
            quotes={"600519": {"price": 120, "fetched_at": "2026-05-01T00:00:00+00:00"}},
        )["items"][0]
        self.assertEqual(item["data_quality"]["status"], "complete")
        self.assertEqual(item["data_quality"]["issues"], [])
        self.assertEqual(item["data_quality"]["bar_count"], 90)
        self.assertEqual(item["data_quality"]["kline_as_of"], "2026-04-30")
        self.assertEqual(item["data_quality"]["quote_fetched_at"], "2026-05-01T00:00:00+00:00")

    def test_missing_quote_or_index_caps_confidence_at_medium(self) -> None:
        bars = trend_bars(step=2)
        for quotes, index, issue in (
            ({}, bars, "missing_quote"),
            ({"600519": {"price": bars[-1]["close"]}}, [], "missing_index"),
        ):
            with self.subTest(issue=issue):
                item = self.report(bars={"600519": bars}, index=index, quotes=quotes)["items"][0]
                self.assertEqual(item["data_quality"]["status"], "partial")
                self.assertIn(issue, item["data_quality"]["issues"])
                self.assertIn(item["decision"]["confidence"], {"low", "medium"})

    def test_no_evidence_is_explicit_and_uncalibrated(self) -> None:
        report = self.report()
        item = report["items"][0]
        self.assertEqual(item["evidence"], [])
        self.assertEqual(item["evidence_summary"], "证据不足")
        self.assertIsNone(item["current_price"])
        self.assertIsNone(item["price_origin"])
        self.assertEqual(item["decision"]["confidence"], "low")
        self.assertIn("no_evidence", item["data_quality"]["issues"])
        self.assertEqual(report["calibration"]["status"], "uncalibrated")
        self.assertEqual(report["calibration"]["score_type"], "rule_based_scenario_scores")
        self.assertFalse(report["calibration"]["is_calibrated_probability"])

    def test_invalid_quote_prices_fall_back_to_latest_close(self) -> None:
        bars = trend_bars()
        for price in (0, -1, True, float("nan"), float("inf"), -float("inf"), "bad", 10**400):
            with self.subTest(price=price):
                item = self.report(bars={"600519": bars}, index=bars, quotes={"600519": {"price": price}})["items"][0]
                self.assertEqual(item["current_price"], bars[-1]["close"])
                self.assertEqual(item["price_origin"], "latest_close")
                self.assertIn("invalid_quote_price", item["data_quality"]["issues"])
                self.assertIn(item["decision"]["confidence"], {"low", "medium"})
                json.dumps(item, allow_nan=False)

    def test_invalid_kline_prices_are_not_evidence_or_endpoint_returns(self) -> None:
        for price in (0, -1, float("nan"), float("inf")):
            with self.subTest(price=price):
                index = trend_bars()
                stock = [{**bar, "close": price} for bar in index]
                item = self.report(bars={"600519": stock}, index=index)["items"][0]
                self.assertIsNone(item["current_price"])
                self.assertEqual(item["data_quality"]["bar_count"], 0)
                self.assertEqual(item["decision"]["confidence"], "low")
                self.assertIsNone(item["factor_profile"]["momentum"]["return20_pct"])
                json.dumps(item, allow_nan=False)

    def test_invalid_endpoint_is_not_silently_replaced_with_valid_earlier_close(self) -> None:
        bars = trend_bars()
        invalid = [*bars[:-1], {**bars[-1], "close": 0}]
        item = self.report(bars={"600519": invalid}, index=bars)["items"][0]
        self.assertIsNone(item["factor_profile"]["relative_strength"]["vs_index_20_pct"])
        self.assertEqual(item["factor_profile"]["windows"]["20"]["stock"]["status"], "invalid")

    def test_report_records_fixed_horizon_and_reproducible_provenance(self) -> None:
        report = self.report(bars={"600519": trend_bars()})
        self.assertEqual(report["model_version"], "rule_based_scenario_v1")
        self.assertEqual(report["period"], "daily")
        self.assertEqual(report["generated_at"], "2026-05-01T00:00:00+00:00")
        self.assertEqual(report["scope"]["horizon_sessions"], 20)
        self.assertEqual(report["provenance"]["source"], "fixture")
        self.assertEqual(report["provenance"]["as_of"], "2026-04-30")
        self.assertEqual(report["provenance"]["calendar_source"], "pool")
        self.assertEqual(report["provenance"]["stale_after_calendar_days"], 7)
        self.assertEqual(report["provenance"]["max_endpoint_lag_sessions"], 3)

    def test_unsupported_horizons_are_rejected_not_clamped(self) -> None:
        for horizon in (5, 19, 21, 60, 120, 0, 20.5, "20", None, True):
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                self.report(horizon_days=horizon)

    def test_v1_rejects_non_daily_periods(self) -> None:
        for period in ("weekly", "monthly", "minute", "Daily", "", None):
            with self.subTest(period=period), self.assertRaisesRegex(ValueError, "daily"):
                self.report(period=period)

    def test_stale_start_before_left_calendar_edge_is_not_a_valid_return(self) -> None:
        index = trend_bars(days=61)
        stock = [
            {**index[0], "trade_date": "2025-01-01"},
            *index[1:],
        ]
        item = self.report(bars={"600519": stock}, index=index)["items"][0]
        self.assertIsNone(item["factor_profile"]["momentum"]["return60_pct"])
        self.assertEqual(item["factor_profile"]["windows"]["60"]["stock"]["status"], "stale")
        self.assertEqual(item["data_quality"]["status"], "stale")
        self.assertEqual(item["decision"]["confidence"], "low")

    def test_session_and_wall_clock_staleness_boundaries(self) -> None:
        index = trend_bars(days=121)
        for missing, status in ((3, "complete"), (4, "stale")):
            with self.subTest(missing=missing):
                item = self.report(bars={"600519": index[:-missing]}, index=index)["items"][0]
                self.assertEqual(item["factor_profile"]["windows"]["20"]["stock"]["status"], status)
        for generated, status in (("2026-05-07", "partial"), ("2026-05-08", "stale")):
            with self.subTest(generated=generated), mock.patch(
                "services.api.app.decision_engine.utc_now", return_value=generated + "T00:00:00+00:00"
            ):
                item = self.report(bars={"600519": index}, index=index)["items"][0]
                self.assertEqual(item["data_quality"]["status"], status)

    def test_nonfinite_quote_change_cannot_contaminate_scores(self) -> None:
        bars = trend_bars()
        report = self.report(
            bars={"600519": bars}, index=bars,
            quotes={"600519": {"price": 120, "pct_change": float("nan")}},
        )
        self.assertNotIn("相对强弱", {entry["source"] for entry in report["items"][0]["evidence"]})
        json.dumps(report, allow_nan=False)

    def test_stale_all_inputs_cannot_generate_regime_or_candidate(self) -> None:
        bars = trend_bars()
        with mock.patch("services.api.app.decision_engine.utc_now", return_value="2026-05-20T00:00:00+00:00"):
            report = self.report(
                bars={"600519": bars}, index=bars,
                quotes={"600519": {"price": 150, "pct_change": 10, "fetched_at": "2026-05-01T00:00:00+00:00"}},
                market_regime={"regime": "uptrend", "confidence": "high", "strategy_bias": {"weights": {"trend": 100}}},
            )
        item = report["items"][0]
        self.assertEqual(report["market_regime"]["regime"], "unknown")
        self.assertEqual(report["market_regime"]["confidence"], "low")
        self.assertEqual(report["market_regime"]["data_quality"]["status"], "stale")
        self.assertTrue(report["market_regime"]["data_quality"]["degraded"])
        self.assertEqual(item["evidence"], [])
        self.assertEqual(item["prior"]["components"], [])
        self.assertEqual(item["decision"]["key"], "wait_confirm")
        self.assertIsNone(item["current_price"])
        self.assertEqual(item["data_quality"]["bar_count"], 90)
        json.dumps(report, allow_nan=False)

    def test_stale_individual_trend_is_not_scored_with_fresh_quote_and_index(self) -> None:
        index = trend_bars(days=121)
        old = [
            {**bar, "trade_date": (date.fromisoformat(bar["trade_date"]) - timedelta(days=30)).isoformat()}
            for bar in trend_bars(step=2)
        ]
        item = self.report(
            bars={"600519": old}, index=index,
            quotes={"600519": {"price": old[-1]["close"], "pct_change": 10, "fetched_at": "2026-05-01T00:00:00+00:00"}},
        )["items"][0]
        self.assertEqual(item["decision"]["key"], "wait_confirm")
        self.assertIsNone(item["indicator"]["trend"])
        self.assertIsNone(item["chan"]["signal_type"])
        self.assertNotIn("MA趋势", {entry["source"] for entry in item["evidence"]})
        self.assertNotIn("波动率区间", {entry["source"] for entry in item["prior"]["components"]})
        self.assertEqual(item["data_quality"]["status"], "stale")

    def test_stale_peers_do_not_change_fresh_item_scores(self) -> None:
        bars = trend_bars()
        quotes = {"600519": {"price": bars[-1]["close"], "pct_change": 0, "fetched_at": "2026-05-01T00:00:00+00:00"}}
        baseline = self.report(bars={"600519": bars}, index=bars, quotes=quotes)
        old = [
            {**bar, "trade_date": (date.fromisoformat(bar["trade_date"]) - timedelta(days=30)).isoformat()}
            for bar in trend_bars(step=-0.4)
        ]
        result = self.report(
            bars={"600519": bars, "688630": old}, index=bars,
            quotes={**quotes, "688630": {"price": 100, "pct_change": -20, "fetched_at": "2026-04-01T00:00:00+00:00"}},
        )
        item = result["items"][0]
        self.assertEqual(item["probabilities"], baseline["items"][0]["probabilities"])
        self.assertEqual(item["prior"]["scores"], baseline["items"][0]["prior"]["scores"])
        self.assertEqual(item["z_scores"], baseline["items"][0]["z_scores"])
        quality = result["market_regime"]["data_quality"]
        self.assertTrue(quality["degraded"])
        self.assertEqual(quality["excluded_quote_symbols"], ["688630"])
        self.assertEqual(quality["excluded_kline_symbols"], ["688630"])
        self.assertEqual(item["data_quality"]["status"], "complete")

    def test_stale_index_uses_fresh_pool_calendar_and_not_old_regime(self) -> None:
        bars = trend_bars()
        old = [
            {**bar, "trade_date": (date.fromisoformat(bar["trade_date"]) - timedelta(days=30)).isoformat()}
            for bar in trend_bars(step=-0.4)
        ]
        baseline = self.report(bars={"600519": bars})
        result = self.report(bars={"600519": bars}, index=old)
        self.assertEqual(result["items"][0]["probabilities"], baseline["items"][0]["probabilities"])
        self.assertEqual(result["provenance"]["calendar_source"], "pool")
        self.assertEqual(result["provenance"]["as_of"], "2026-04-30")
        self.assertEqual(result["market_regime"]["index"]["bar_count"], 0)
        self.assertTrue(result["market_regime"]["data_quality"]["degraded"])
        self.assertIn("stale_index", result["market_regime"]["data_quality"]["issues"])
        self.assertIn(result["market_regime"]["confidence"], {"low", "medium"})

    def test_stale_quote_is_not_current_price_or_daily_breadth_evidence(self) -> None:
        bars = trend_bars()
        baseline = self.report(bars={"600519": bars}, index=bars)
        result = self.report(
            bars={"600519": bars}, index=bars,
            quotes={"600519": {"price": 999, "pct_change": 80, "fetched_at": "2026-04-01T00:00:00+00:00"}},
        )
        item = result["items"][0]
        self.assertEqual(item["current_price"], bars[-1]["close"])
        self.assertEqual(item["price_origin"], "latest_close")
        self.assertEqual(item["probabilities"], baseline["items"][0]["probabilities"])
        self.assertNotIn("相对强弱", {entry["source"] for entry in item["evidence"]})
        self.assertIn("stale_quote", item["data_quality"]["issues"])
        self.assertEqual(item["decision"]["confidence"], "low")

    def test_stale_quote_blocks_candidate_even_with_fresh_uptrend(self) -> None:
        bars = trend_bars()
        item = self.report(
            bars={"600519": bars}, index=bars,
            quotes={"600519": {"price": 999, "pct_change": 80, "fetched_at": "2026-04-01T00:00:00+00:00"}},
        )["items"][0]
        self.assertEqual(item["indicator"]["trend"], "bullish")
        self.assertGreater(item["probabilities"]["up"], 0.55)
        self.assertEqual(item["data_quality"]["status"], "stale")
        self.assertEqual(item["decision"]["key"], "wait_confirm")
        self.assertEqual(item["decision"]["confidence"], "low")
        self.assertIn("补齐新鲜行情", item["decision"]["next_check"])

    def test_invalid_volume_suppresses_volume_and_volume_conditioned_reversion(self) -> None:
        bars = mixed_bars()
        for offset in (1, 10, 20):
            for volume in (None, "bad", -1, True, float("nan"), float("inf")):
                with self.subTest(offset=offset, volume=volume):
                    stock = [dict(bar) for bar in bars]
                    stock[-offset]["volume"] = volume
                    result = self.report(bars={"600519": stock}, index=bars)
                    item = result["items"][0]
                    self.assertIsNone(item["indicator"]["volume_ratio"])
                    self.assertIsNone(item["factor_profile"]["mean_reversion"]["volume_ratio"])
                    self.assertIn("invalid_volume", item["data_quality"]["issues"])
                    self.assertEqual(item["data_quality"]["status"], "partial")
                    sources = {entry["source"] for entry in item["evidence"]}
                    self.assertNotIn("成交量", sources)
                    self.assertNotIn("均值回归位置", sources)
                    self.assertIn("MA趋势", sources)
                    self.assertIn(item["decision"]["confidence"], {"low", "medium"})
                    json.dumps(result, allow_nan=False)

    def test_valid_zero_volume_remains_zero_not_missing(self) -> None:
        bars = trend_bars()
        stock = [*bars[:-1], {**bars[-1], "volume": 0}]
        item = self.report(bars={"600519": stock}, index=bars)["items"][0]
        self.assertEqual(item["indicator"]["volume_ratio"], 0)
        self.assertNotIn("invalid_volume", item["data_quality"]["issues"])
        self.assertIn("成交量", {entry["source"] for entry in item["evidence"]})

    def test_invalid_volume_outside_ratio_window_does_not_erase_fresh_volume(self) -> None:
        bars = trend_bars()
        stock = [dict(bar) for bar in bars]
        stock[-21]["volume"] = None
        item = self.report(bars={"600519": stock}, index=bars)["items"][0]
        self.assertEqual(item["indicator"]["volume_ratio"], 1.0529)
        self.assertIn("invalid_volume", item["data_quality"]["issues"])

    def test_impossible_ohlc_is_not_indicator_chan_or_return_evidence(self) -> None:
        bars = trend_bars(start_price=100, step=0)
        for updates in (
            {"high": 90, "low": 110}, {"open": 110}, {"close": 110},
        ):
            with self.subTest(updates=updates):
                stock = [{**bar, **updates} for bar in bars]
                result = self.report(bars={"600519": stock}, index=bars)
                item = result["items"][0]
                self.assertEqual(item["data_quality"]["bar_count"], 0)
                self.assertIn("invalid_kline_bars", item["data_quality"]["issues"])
                self.assertIsNone(item["indicator"]["atr14"])
                self.assertIsNone(item["chan"]["signal_type"])
                self.assertIsNone(item["factor_profile"]["momentum"]["return20_pct"])
                self.assertEqual(item["decision"]["confidence"], "low")
                self.assertEqual(item["decision"]["key"], "wait_confirm")
                json.dumps(result, allow_nan=False)

    def test_invalid_ohlc_peer_is_excluded_from_shared_regime_and_returns(self) -> None:
        bars = trend_bars()
        baseline = self.report(bars={"600519": bars}, index=bars)
        invalid = [{**bar, "high": 1, "low": 500} for bar in trend_bars(step=-0.4)]
        result = self.report(bars={"600519": bars, "688630": invalid}, index=bars)
        self.assertEqual(result["items"][0]["probabilities"], baseline["items"][0]["probabilities"])
        self.assertEqual(result["market_regime"]["pool_trend"]["sample_size"], 1)
        self.assertTrue(result["market_regime"]["data_quality"]["degraded"])

    def test_invalid_index_endpoint_does_not_silently_shorten_calendar(self) -> None:
        bars = trend_bars()
        index = [*bars[:-1], {**bars[-1], "close": 0}]
        result = self.report(bars={"600519": bars}, index=index)
        profile = result["items"][0]["factor_profile"]
        self.assertEqual(profile["windows"]["20"]["end"], "2026-04-30")
        self.assertIsNone(profile["relative_strength"]["vs_index_20_pct"])
        self.assertEqual(profile["windows"]["20"]["index"]["status"], "invalid")
        quality = result["market_regime"]["data_quality"]
        self.assertEqual(quality["index_as_of"], "2026-04-30")
        self.assertEqual(quality["eligible_index_as_of"], "2026-04-29")
        self.assertTrue(quality["degraded"])

    def test_supplied_stale_regime_cannot_contaminate_fresh_inputs(self) -> None:
        bars = trend_bars()
        baseline = self.report(bars={"600519": bars}, index=bars)
        result = self.report(
            bars={"600519": bars}, index=bars,
            market_regime={
                "regime": "downtrend", "confidence": "high",
                "strategy_bias": {"weights": {"risk": 100}},
                "data_quality": {"status": "stale"},
            },
        )
        self.assertEqual(result["items"][0]["probabilities"], baseline["items"][0]["probabilities"])
        self.assertEqual(result["market_regime"]["regime"], baseline["market_regime"]["regime"])
        self.assertIn("excluded_supplied_regime", result["market_regime"]["data_quality"]["issues"])
        self.assertTrue(result["market_regime"]["data_quality"]["degraded"])

    def test_decision_engine_returns_probabilities_and_evidence(self) -> None:
        bars = trend_bars()
        report = generate_stock_pool_decision_engine(
            pool={"id": 1, "name": "默认股票池"},
            watchlist=[{"id": 1, "symbol": "688630", "name": "芯碁微装", "priority": 1}],
            holdings=[{"id": 1, "symbol": "688630", "quantity": 100, "cost_price": 95}],
            quotes={
                "688630": {
                    "symbol": "688630",
                    "name": "芯碁微装",
                    "price": bars[-1]["close"],
                    "pct_change": 2.1,
                }
            },
            kline_by_symbol={"688630": bars},
            source="tdx-official",
            horizon_days=20,
            index_bars=trend_bars(start_price=3000, days=120, step=5),
        )

        item = report["items"][0]
        probabilities = item["probabilities"]
        self.assertEqual(report["report_type"], "stock_pool_decision_engine")
        self.assertEqual(report["market_regime"]["regime"], "uptrend")
        self.assertIn("rule_state_machine", report["tool_plan"]["market_regime_model"])
        self.assertIn("市场状态", {component["source"] for component in item["prior"]["components"]})
        self.assertAlmostEqual(sum(probabilities.values()), 1, places=3)
        self.assertGreater(probabilities["up"], probabilities["down"])
        self.assertIn("MA趋势", {entry["source"] for entry in item["evidence"]})
        self.assertTrue(all("category" in entry for entry in item["evidence"]))
        self.assertTrue(any("regime_weight" in entry for entry in item["evidence"]))
        self.assertIn(item["decision"]["key"], {"hold_observe", "position_review", "wait_confirm"})
        self.assertTrue(item["evidence_summary"])

    def test_decision_engine_adds_factor_evidence_conditioned_by_regime(self) -> None:
        strong_bars = mixed_bars(start_price=50, days=100, step=0.65, final_price=112)
        peer_bars = mixed_bars(start_price=50, days=100, step=0.12, final_price=62)
        index_bars = mixed_bars(start_price=3000, days=120, step=0.8, final_price=3105)

        report = generate_stock_pool_decision_engine(
            pool={"id": 1, "name": "默认股票池"},
            watchlist=[
                {"id": 1, "symbol": "688630", "name": "芯碁微装", "priority": 1},
                {"id": 2, "symbol": "603337", "name": "杰克科技", "priority": 2},
            ],
            holdings=[],
            quotes={
                "688630": {"symbol": "688630", "name": "芯碁微装", "price": 112, "pct_change": 2.4},
                "603337": {"symbol": "603337", "name": "杰克科技", "price": 62, "pct_change": 0.2},
            },
            kline_by_symbol={"688630": strong_bars, "603337": peer_bars},
            source="tdx-official",
            horizon_days=20,
            index_bars=index_bars,
        )

        item = next(row for row in report["items"] if row["symbol"] == "688630")
        sources = {entry["source"] for entry in item["evidence"]}
        self.assertIn("中期动量", sources)
        self.assertIn("指数相对强弱", sources)
        self.assertIn("股票池相对强弱", sources)
        self.assertIn("均值回归位置", sources)
        self.assertIn("factor_profile", item)
        self.assertGreater(item["factor_profile"]["relative_strength"]["vs_index_20_pct"], 0)
        self.assertGreater(item["factor_profile"]["relative_strength"]["vs_pool_20_pct"], 0)
        self.assertTrue(
            any(entry["source"] == "中期动量" and entry["regime_weight"] > 1 for entry in item["evidence"])
        )

    def test_decision_engine_separates_common_factor_rise_from_specific_strength(self) -> None:
        weak_absolute_bars = factor_return_bars(
            latest_price=105,
            return20_pct=5,
            return60_pct=12,
        )
        peer_a_bars = factor_return_bars(latest_price=118, return20_pct=18, return60_pct=24)
        peer_b_bars = factor_return_bars(latest_price=120, return20_pct=20, return60_pct=26)
        index_bars = factor_return_bars(latest_price=3400, return20_pct=14, return60_pct=18, days=120)

        report = generate_stock_pool_decision_engine(
            pool={"id": 1, "name": "默认股票池"},
            watchlist=[
                {"id": 1, "symbol": "600519", "name": "贵州茅台", "priority": 1},
                {"id": 2, "symbol": "688630", "name": "芯碁微装", "priority": 2},
                {"id": 3, "symbol": "603337", "name": "杰克科技", "priority": 3},
            ],
            holdings=[],
            quotes={
                "600519": {"symbol": "600519", "name": "贵州茅台", "price": 105, "pct_change": 0.8},
                "688630": {"symbol": "688630", "name": "芯碁微装", "price": 118, "pct_change": 2.1},
                "603337": {"symbol": "603337", "name": "杰克科技", "price": 120, "pct_change": 2.4},
            },
            kline_by_symbol={
                "600519": weak_absolute_bars,
                "688630": peer_a_bars,
                "603337": peer_b_bars,
            },
            source="tdx-official",
            horizon_days=20,
            index_bars=index_bars,
        )

        item = next(row for row in report["items"] if row["symbol"] == "600519")
        attribution = item["factor_profile"]["attribution"]
        self.assertAlmostEqual(attribution["stock_return20_pct"], 5.0, places=2)
        self.assertAlmostEqual(attribution["market_return20_pct"], 14.0, places=2)
        self.assertAlmostEqual(attribution["pool_median_return20_pct"], 18.0, places=2)
        self.assertAlmostEqual(attribution["excess_market_20_pct"], -9.0, places=2)
        self.assertAlmostEqual(attribution["excess_pool_median_20_pct"], -13.0, places=2)
        evidence = next(entry for entry in item["evidence"] if entry["source"] == "因子归因")
        self.assertIn("共同因子", evidence["observation"])
        self.assertGreater(evidence["contribution"]["down"], evidence["contribution"]["up"])

    def test_decision_engine_api_uses_watchlist_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_db(db_path)
            connection = connect(db_path)
            try:
                pool = get_default_stock_pool(connection)
                create_watchlist_item(
                    connection,
                    {"pool_id": pool["id"], "symbol": "688630", "name": "芯碁微装", "priority": 1},
                )
                create_holding(
                    connection,
                    {"symbol": "688630", "name": "芯碁微装", "quantity": 100, "cost_price": 95},
                )
                calls: list[tuple[str, str]] = []
                bars = trend_bars()

                def fake_fetch_quote(_db, *, symbol: str, source: str) -> dict:
                    calls.append(("quote", symbol))
                    return {
                        "snapshot_id": 1,
                        "symbol": symbol,
                        "name": "芯碁微装",
                        "source": source,
                        "price": bars[-1]["close"],
                        "pct_change": 2.1,
                        "fetched_at": "now",
                    }

                def fake_fetch_kline(_db, *, symbol: str, source: str, period: str, limit: int) -> dict:
                    calls.append(("kline", symbol))
                    return {
                        "symbol": symbol,
                        "source": source,
                        "period": period,
                        "count": len(bars),
                        "bars": bars,
                    }

                with (
                    mock.patch("services.api.app.main._fetch_quote_and_cache", side_effect=fake_fetch_quote),
                    mock.patch("services.api.app.main._fetch_kline_and_cache", side_effect=fake_fetch_kline),
                ):
                    report = api_analyze_stock_pool_with_decision_engine(
                        int(pool["id"]),
                        StockPoolDecisionEngineRequest(
                            source="tdx-official",
                            persist=False,
                            max_symbols=1,
                            horizon_days=20,
                            market_index_symbol="SH000300",
                        ),
                        connection,
                    )

                payload = report["payload"]
                self.assertEqual(calls, [("kline", "SH000300"), ("quote", "688630"), ("kline", "688630")])
                self.assertEqual(payload["report_type"], "stock_pool_decision_engine")
                self.assertEqual(payload["scope"]["horizon_days"], 20)
                self.assertEqual(payload["scope"]["market_index_symbol"], "SH000300")
                self.assertIn("market_regime", payload)
                self.assertEqual(payload["data_quality"]["failed_quote_count"], 0)
                self.assertEqual(payload["items"][0]["symbol"], "688630")
                self.assertIn("probabilities", payload["items"][0])
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
