from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts.validate_chan import main
from services.api.app.chan_dataset import save_dataset
from services.api.tests.chan_validation_cases import candidate_bars, controlled_bars, make_dataset, daily_bar


class ChanValidationCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.as_of = "2026-02-15T15:00:00+08:00"
        self.bars = candidate_bars()
        self.dataset = make_dataset(series={"600519": {"daily": self.bars}},
                                    sessions=[b["trade_date"] for b in self.bars], as_of=self.as_of)
        self.dataset_path = save_dataset(self.dataset, self.root)
        self.output = self.root / "replay.json"
        self.args = ["replay", "--dataset", str(self.dataset_path), "--as-of", self.as_of, "--output", str(self.output)]
        self.stdout, self.stderr = io.StringIO(), io.StringIO()

    def invoke(self, args):
        with redirect_stdout(self.stdout), redirect_stderr(self.stderr):
            return main(args)

    def test_offline_replay_and_frame_never_open_network_database_or_env(self):
        personal = self.root / "personal.db"
        with sqlite3.connect(personal) as connection:
            connection.execute("CREATE TABLE positions (quantity INTEGER)")
            connection.execute("INSERT INTO positions VALUES (100)")
        before = hashlib.sha256(personal.read_bytes()).hexdigest()
        original_open = Path.open
        def guarded_open(path, *args, **kwargs):
            if path.name.startswith(".env"):
                raise AssertionError("env")
            return original_open(path, *args, **kwargs)
        with mock.patch("socket.socket.connect", side_effect=AssertionError("network")), \
             mock.patch("sqlite3.connect", side_effect=AssertionError("database")), \
             mock.patch.object(Path, "open", guarded_open), \
             mock.patch.dict(sys.modules, {"services.api.app.config": None, "services.api.app.market_data": None}):
            self.assertEqual(self.invoke(self.args), 0, self.stderr.getvalue())
            frame = self.root / "frame.json"
            self.assertEqual(self.invoke(["frame", "--dataset", str(self.dataset_path), "--symbol", "600519",
                                          "--as-of", self.as_of, "--output", str(frame)]), 0)
        result = json.loads(self.output.read_text())
        self.assertEqual(result["dataset_id"], self.dataset["dataset_id"])
        self.assertTrue(result["observations"])
        self.assertTrue(json.loads(frame.read_text())["analysis"]["chart"]["bars"])
        self.assertEqual(hashlib.sha256(personal.read_bytes()).hexdigest(), before)

    def test_repeat_is_deterministic_and_never_overwrites(self):
        self.assertEqual(self.invoke(self.args), 0)
        saved = self.output.read_bytes()
        self.assertEqual(self.invoke(self.args), 2)
        self.assertEqual(self.output.read_bytes(), saved)
        other = self.root / "second.json"
        self.assertEqual(self.invoke(self.args[:-1] + [str(other)]), 0)
        self.assertEqual(other.read_bytes(), saved)
        original = self.dataset_path.read_bytes()
        self.assertEqual(self.invoke(self.args[:-1] + [str(self.dataset_path)]), 2)
        self.assertEqual(self.dataset_path.read_bytes(), original)

    def test_bad_arguments_tampered_input_and_nonfinite_json_are_safe(self):
        self.assertEqual(self.invoke(["capture", "--symbols", "private-token"]), 2)
        self.assertEqual(self.invoke(["capture", "--symbols", "600519", "--periods", "bad", "--as-of", self.as_of]), 2)
        for raw in [b'{"private-token": NaN}', b'{"private-token":', self.dataset_path.read_bytes().replace(b'12.7', b'12.8')]:
            self.dataset_path.write_bytes(raw)
            self.assertEqual(self.invoke(self.args), 2)
        with self.dataset_path.open("wb") as stream:
            stream.truncate(50 * 1024 * 1024 + 1)
        self.assertEqual(self.invoke(self.args), 2)
        self.assertFalse(self.output.exists())
        self.assertNotIn("private-token", self.stderr.getvalue())

    def test_no_candidate_or_insufficient_history_still_writes_report(self):
        for count in [10, 40]:
            bars = controlled_bars(count)
            data = make_dataset(series={"600519": {"daily": bars}}, sessions=[b["trade_date"] for b in bars], as_of=self.as_of)
            path = save_dataset(data, self.root)
            output = self.root / f"empty-{count}.json"
            self.assertEqual(self.invoke(["replay", "--dataset", str(path), "--as-of", self.as_of, "--output", str(output)]), 0)
            report = json.loads(output.read_text())
            self.assertEqual(report["observations"], [])
            if count == 10:
                self.assertIn("insufficient_bars", str(report["issues"]))

    def test_capture_uses_bounded_provider_and_saves_only_research_input(self):
        provider = mock.Mock()
        provider.fetch_kline_page.return_value = [daily_bar("2026-02-15")]
        with mock.patch("services.api.app.market_data.get_market_data_provider", return_value=provider), \
             mock.patch("services.api.app.chan_capture.time.sleep"):
            code = self.invoke(["capture", "--symbols", "600519", "--periods", "daily",
                                "--as-of", self.as_of, "--root", str(self.root / "capture"), "--page-size", "12"])
        self.assertEqual(code, 0, self.stderr.getvalue())
        paths = list((self.root / "capture").glob("*/dataset.json"))
        self.assertEqual(len(paths), 1)
        captured = json.loads(paths[0].read_text())
        self.assertEqual(captured["collection"]["page_size"], 12)
        self.assertEqual(captured["price_basis"]["verification"]["status"], "unverified")

    def test_real_script_entry_and_offline_import_graph(self):
        root = Path(__file__).resolve().parents[3]
        process = subprocess.run([sys.executable, "-B", "scripts/validate_chan.py", *self.args],
                                 cwd=root, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        process = subprocess.run([sys.executable, "-B", "scripts/validate_chan.py", "replay"],
                                 cwd=root, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 2)
        check = "import sys; import scripts.validate_chan; assert not any(x in sys.modules for x in ['services.api.app.config','services.api.app.main','services.api.app.market_data','services.api.app.chan_capture'])"
        process = subprocess.run([sys.executable, "-B", "-c", check], cwd=root, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
