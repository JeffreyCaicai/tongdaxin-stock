from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from services.api.app.chan_dataset import load_dataset, save_dataset, validate_dataset
from services.api.tests.chan_validation_cases import daily_bar, make_dataset, rehash


class ChanDatasetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dataset = make_dataset(series={"600519": {"daily": [daily_bar("2026-09-30")]}},
                                    sessions=["2026-09-30"], as_of="2026-10-01T12:00:00+08:00")

    def test_dataset_is_immutable_and_verified(self):
        path = save_dataset(self.dataset, self.root)
        self.assertEqual(load_dataset(path), self.dataset)
        before = path.stat().st_mtime_ns
        self.assertEqual(save_dataset(self.dataset, self.root), path)
        self.assertEqual(path.stat().st_mtime_ns, before)
        changed = copy.deepcopy(self.dataset)
        changed["created_at"] = "2026-10-02T00:00:00+08:00"
        with self.assertRaisesRegex(ValueError, "dataset_hash_mismatch"):
            validate_dataset(changed)

    def test_rejects_unknown_fields_nonfinite_and_false_verification(self):
        for change in [lambda d: d.update(token="secret"),
                       lambda d: d["price_basis"]["verification"].update(reference=None),
                       lambda d: d["series"]["600519"]["daily"]["bars"][0].update(raw="secret"),
                       lambda d: d.update(as_of="2026-10-01T12:00:00")]:
            data = copy.deepcopy(self.dataset)
            change(data)
            with self.assertRaises(ValueError):
                validate_dataset(rehash(data))
        data = copy.deepcopy(self.dataset)
        data["series"]["600519"]["daily"]["bars"][0]["close"] = float("nan")
        with self.assertRaises(ValueError):
            validate_dataset(data)

    def test_corrupt_or_oversized_input_fails_without_overwrite(self):
        path = save_dataset(self.dataset, self.root)
        for body in [b'{"bad":', b'{"value":NaN}', b'{"dataset_id":"x","dataset_id":"y"}']:
            path.write_bytes(body)
            with self.assertRaises(ValueError):
                load_dataset(path)
            with self.assertRaises(ValueError):
                save_dataset(self.dataset, self.root)
            self.assertEqual(path.read_bytes(), body)
        with path.open("wb") as stream:
            stream.truncate(50 * 1024 * 1024 + 1)
        with self.assertRaisesRegex(ValueError, "too_large"):
            load_dataset(path)


if __name__ == "__main__":
    unittest.main()
