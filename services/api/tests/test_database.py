from __future__ import annotations

import tempfile
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from services.api.app.database import connect, init_db


class DatabaseTests(unittest.TestCase):
    def test_initialization_explicitly_closes_its_connection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connections = []
            def tracked_connect(path):
                db = connect(path)
                connections.append(db)
                return db
            with mock.patch("services.api.app.database.connect", side_effect=tracked_connect):
                init_db(Path(directory) / "lifecycle.db")
            try:
                with self.assertRaises(sqlite3.ProgrammingError):
                    connections[0].execute("SELECT 1")
            finally:
                connections[0].close()

    def test_request_connection_can_cross_worker_threads_sequentially(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workers.db"
            init_db(path)
            db = connect(path)
            try:
                with ThreadPoolExecutor(max_workers=1) as worker:
                    row = worker.submit(lambda: db.execute("SELECT COUNT(*) FROM stock_pools").fetchone()).result()
                    self.assertGreater(row[0], 0)
                    self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
                    worker.submit(db.close).result()
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
