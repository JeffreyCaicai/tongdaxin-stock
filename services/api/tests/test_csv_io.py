from __future__ import annotations

import unittest

from services.api.app.csv_io import csv_to_rows, rows_to_csv


class CsvIoTests(unittest.TestCase):
    def test_csv_to_rows_converts_numeric_values(self) -> None:
        rows = csv_to_rows(
            "symbol,cost_price,quantity,max_loss_pct\n600519,1500,100,8\n",
            required_fields={"symbol", "cost_price"},
        )

        self.assertEqual(rows[0]["symbol"], "600519")
        self.assertEqual(rows[0]["cost_price"], 1500.0)
        self.assertEqual(rows[0]["quantity"], 100.0)
        self.assertEqual(rows[0]["max_loss_pct"], 8.0)

    def test_csv_to_rows_requires_header_fields(self) -> None:
        with self.assertRaises(ValueError):
            csv_to_rows("symbol,name\n600519,Moutai\n", required_fields={"cost_price"})

    def test_rows_to_csv_writes_requested_fields(self) -> None:
        csv_text = rows_to_csv(
            [{"symbol": "000001", "name": "Ping An Bank", "ignored": "x"}],
            ["symbol", "name"],
        )

        self.assertIn("symbol,name", csv_text)
        self.assertIn("000001,Ping An Bank", csv_text)
        self.assertNotIn("ignored", csv_text)


if __name__ == "__main__":
    unittest.main()
