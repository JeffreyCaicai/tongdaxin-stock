from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.validate_chan import main
from services.api.app.chan_dataset import save_dataset
from services.api.app.chan_quality import dataset_quality
from services.api.app.chan_report import _chart
from services.api.tests.chan_validation_cases import candidate_bars, controlled_bars, daily_bar, make_dataset, rehash


class ReportParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements, self.text = [], []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, text):
        self.text.append(text)


class ChanReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.as_of = "2026-02-15T15:00:00+08:00"
        bars = candidate_bars()
        self.data = make_dataset(series={"600519": {"daily": bars}, "SH000300": {"daily": bars},
                                         "688630": {"daily": controlled_bars(10)}},
                                 sessions=[b["trade_date"] for b in bars], as_of=self.as_of)

    def export(self, data=None, language="zh", output=None):
        path = save_dataset(rehash(data or self.data), self.root)
        output = output or self.root / f"report-{language}.html"
        args = ["report", "--dataset", str(path), "--as-of", self.as_of,
                "--output", str(output), "--language", language]
        with redirect_stderr(io.StringIO()) as errors, redirect_stdout(io.StringIO()):
            code = main(args)
        return code, output, errors.getvalue()

    def test_bilingual_report_contains_each_security_evidence_and_unavailable_values(self):
        for language, expected in (("zh", "缠论验证报告"), ("en", "Chan research report")):
            code, path, error = self.export(language=language)
            self.assertEqual(code, 0, error)
            page = ReportParser(path.read_text())
            text = " ".join(page.text)
            self.assertIn(expected, text)
            self.assertIn(self.as_of, text)
            self.assertIn(self.data["dataset_id"], text)
            sections = [attrs["id"] for tag, attrs in page.elements if tag == "section" and attrs.get("id")]
            self.assertIn("stock-600519", sections)
            self.assertIn("stock-688630", sections)
            self.assertIn("SH000300", text)
            self.assertIn("candidate", text)
            self.assertTrue(any(tag == "svg" for tag, _ in page.elements))
            self.assertTrue(any(tag == "details" for tag, _ in page.elements))
            self.assertNotIn("0.00%", text)
            self.assertIn("No valid candidate" if language == "en" else "未记录有效候选", text)
            self.assertIn("Insufficient data" if language == "en" else "数据不足", text)
            self.assertIn("Pending" if language == "en" else "尚未到期", text)

    def test_unverified_inputs_are_both_visible_and_never_reported_as_zero_return(self):
        self.data["calendar"]["verification"]["status"] = "unverified"
        self.data["price_basis"]["verification"]["status"] = "unverified"
        code, path, error = self.export(language="en")
        self.assertEqual(code, 0, error)
        text = " ".join(ReportParser(path.read_text()).text)
        self.assertIn("Calendar: Unverified", text)
        self.assertIn("Price basis: Unverified", text)
        self.assertIn("Unavailable", text)
        self.assertNotIn("0.00%", text)
        self.assertNotIn("win rate:", text.lower())

    def test_chart_has_breaks_at_missing_sessions_and_excludes_invalid_prices(self):
        bars = self.data["series"]["600519"]["daily"]["bars"]
        bars.pop(36)
        bars[37]["close"] = None
        code, path, error = self.export()
        self.assertEqual(code, 0, error)
        page = ReportParser(path.read_text())
        lines = [attrs for tag, attrs in page.elements if tag == "polyline" and attrs.get("data-symbol") == "600519"]
        self.assertEqual(len(lines), 3)
        self.assertIn("missing_session", " ".join(page.text))
        self.assertIn("invalid_ohlc", " ".join(page.text))
        self.assertNotIn("NaN", path.read_text())

    def test_provenance_is_escaped_and_report_is_self_contained(self):
        attack = '<script src="https://invalid.example/x"></script><img onerror="alert(1)">'
        self.data["calendar"]["verification"]["reference"] = attack
        code, path, error = self.export()
        self.assertEqual(code, 0, error)
        page = ReportParser(path.read_text())
        self.assertIn(json.dumps(attack)[1:-1], " ".join(page.text))
        self.assertFalse(any(tag in {"script", "iframe", "img", "link"} for tag, _ in page.elements))
        self.assertFalse(any(key.startswith("on") for _, attrs in page.elements for key in attrs))
        self.assertFalse(any(attrs.get("href", "").startswith("http") for _, attrs in page.elements))
        self.assertTrue(any(tag == "meta" and attrs.get("http-equiv") == "Content-Security-Policy"
                            for tag, attrs in page.elements))

    def test_repeat_output_is_deterministic_exclusive_and_symlink_safe(self):
        code, first, error = self.export()
        self.assertEqual(code, 0, error)
        original = first.read_bytes()
        self.assertEqual(self.export(output=first)[0], 2)
        self.assertEqual(first.read_bytes(), original)
        code, second, error = self.export(output=self.root / "second.html")
        self.assertEqual(code, 0, error)
        self.assertEqual(second.read_bytes(), original)
        link = self.root / "link.html"
        link.symlink_to(self.root / "absent.html")
        self.assertEqual(self.export(output=link)[0], 2)
        self.assertFalse((self.root / "absent.html").exists())
        self.assertEqual(self.export(output=save_dataset(self.data, self.root))[0], 2)

    def test_report_is_offline_and_has_no_environment_or_database_access(self):
        original = Path.open
        def guarded(path, *args, **kwargs):
            if path.name.startswith(".env"):
                raise AssertionError("env")
            return original(path, *args, **kwargs)
        with mock.patch("socket.socket.connect", side_effect=AssertionError("network")), \
             mock.patch("sqlite3.connect", side_effect=AssertionError("database")), \
             mock.patch.object(Path, "open", guarded):
            code, _, error = self.export()
        self.assertEqual(code, 0, error)

    def test_latest_structure_is_visible_even_without_a_candidate(self):
        bars = controlled_bars(40)
        self.as_of = bars[-1]["trade_date"] + "T15:00:00+08:00"
        data = make_dataset(series={"600519": {"daily": bars}},
                            sessions=[b["trade_date"] for b in bars], as_of=self.as_of)
        code, path, error = self.export(data, language="en")
        self.assertEqual(code, 0, error)
        page = ReportParser(path.read_text())
        text = " ".join(page.text)
        self.assertIn("Latest baseline structure", text)
        self.assertIn("Insufficient structure", text)
        self.assertIn("No valid candidate", text)

    def test_chart_coordinates_stay_finite_for_extreme_positive_prices(self):
        for price in (1.79e308, 5e-324):
            bars = [daily_bar("2026-01-01", price, high=price, low=price)]
            data = make_dataset(series={"600519": {"daily": bars}}, sessions=["2026-01-01"], as_of=self.as_of)
            quality = dataset_quality(data, self.as_of)["items"][0]
            html = _chart(data, quality, [], lambda zh, en: en)
            for tag, attrs in ReportParser(html).elements:
                for key in ("points", "cx", "cy", "x", "y", "y1", "y2"):
                    value = attrs.get(key, "").lower()
                    self.assertNotIn("nan", value)
                    self.assertNotIn("inf", value)
