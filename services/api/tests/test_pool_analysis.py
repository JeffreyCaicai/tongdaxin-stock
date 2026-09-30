from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from services.api.app.mcp_tools import McpServerConfig
from services.api.app.pool_analysis import (
    generate_stock_pool_market_analysis,
    generate_stock_pool_mcp_analysis,
)


class StockPoolMcpAnalysisTests(unittest.TestCase):
    def test_market_analysis_uses_quotes_without_mcp_tools(self) -> None:
        report = generate_stock_pool_market_analysis(
            pool={"id": 1, "name": "默认股票池", "description": None},
            holdings=[],
            watchlist=[
                {
                    "id": 20,
                    "symbol": "688630",
                    "name": "芯碁微装",
                    "priority": 1,
                    "status": "watching",
                },
                {
                    "id": 21,
                    "symbol": "603337",
                    "name": "杰克科技",
                    "priority": 2,
                    "status": "watching",
                },
            ],
            quotes={
                "688630": {
                    "snapshot_id": 1,
                    "symbol": "688630",
                    "name": "芯碁微装",
                    "source": "tdx-official",
                    "price": 502.0,
                    "fetched_at": "now",
                }
            },
            source="tdx-official",
            failed_symbols=["603337"],
            max_symbols=10,
        )

        self.assertEqual(report["report_type"], "stock_pool_market_analysis")
        self.assertIn("已用 tdx-official 分析股票池", report["summary"])
        self.assertEqual(report["tool_plan"]["data_source"], "tdx-official")
        self.assertEqual(report["data_quality"]["quote_count"], 1)
        self.assertEqual(report["data_quality"]["missing_quote_count"], 1)
        self.assertEqual(report["items"][0]["quote"]["fields"]["price"], 502.0)
        self.assertEqual(report["items"][0]["action_hint"], "watch_pool_candidate")
        self.assertEqual(report["items"][1]["action_hint"], "complete_market_data")

    def test_pool_analysis_calls_selected_mcp_tools_for_pool_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = generate_stock_pool_mcp_analysis(
                pool={"id": 1, "name": "Short Watch", "description": None},
                holdings=[
                    {
                        "id": 10,
                        "symbol": "600519",
                        "name": "Old Name",
                        "quantity": 100,
                        "cost_price": 90,
                        "stop_loss": 80,
                        "take_profit": 130,
                    }
                ],
                watchlist=[
                    {
                        "id": 20,
                        "symbol": "600519",
                        "name": "Moutai",
                        "priority": 1,
                        "status": "holding",
                    },
                    {
                        "id": 21,
                        "symbol": "688630",
                        "name": "",
                        "priority": 2,
                        "status": "watching",
                        "buy_zone_low": 20,
                        "buy_zone_high": 30,
                    },
                ],
                max_symbols=10,
                mcp_config=McpServerConfig(
                    command=self._fake_server_command(tmpdir),
                    timeout_seconds=3,
                ),
            )

        self.assertEqual(report["report_type"], "stock_pool_mcp_analysis")
        self.assertEqual(report["scope"]["symbol_count"], 2)
        self.assertEqual(report["tool_plan"]["quote_tool"], "tdx_quotes")
        self.assertEqual(report["tool_plan"]["profile_tool"], "tdx_lookup_stock")
        self.assertEqual(report["items"][0]["symbol"], "600519")
        self.assertEqual(report["items"][0]["name"], "Name 600519")
        self.assertEqual(report["items"][0]["action_hint"], "hold_and_monitor")
        self.assertEqual(report["items"][1]["action_hint"], "review_buy_zone")

    def test_pool_analysis_supports_argument_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = generate_stock_pool_mcp_analysis(
                pool={"id": 1, "name": "Template Test"},
                holdings=[],
                watchlist=[{"id": 1, "symbol": "600519", "priority": 1}],
                quote_arguments={"code": "{tdx_code}", "market": "{market}"},
                include_profile=False,
                mcp_config=McpServerConfig(
                    command=self._fake_server_command(tmpdir),
                    timeout_seconds=3,
                ),
            )

        arguments = report["items"][0]["mcp_calls"]["quote"]["arguments"]
        self.assertEqual(arguments["code"], "sh600519")
        self.assertEqual(arguments["market"], "SH")
        self.assertEqual(report["tool_plan"]["profile_tool"], None)

    def _report_for_quote_result(self, result: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            return generate_stock_pool_mcp_analysis(
                pool={"id": 1, "name": "Offline Quote"},
                holdings=[{"id": 1, "symbol": "600519", "quantity": 100,
                           "cost_price": 90, "stop_loss": 80, "take_profit": 130}],
                watchlist=[],
                include_profile=False,
                mcp_config=McpServerConfig(
                    command=self._fake_server_command(tmpdir, quote_result=result),
                    timeout_seconds=3,
                ),
            )

    def test_generator_decodes_json_text_before_extracting_nested_fields(self) -> None:
        result = {"content": [{"type": "text", "text": json.dumps({
            "data": [{"code": "sh600519", "price": 100, "name": "Correct Name"}]
        })}], "isError": False}
        report = self._report_for_quote_result(result)
        item = report["items"][0]
        self.assertEqual(item["mcp_calls"]["quote"]["fields"].get("price"), 100)
        self.assertEqual(item["name"], "Correct Name")
        self.assertEqual(item["position"]["pnl_pct"], 11.11)
        self.assertEqual(item["action_hint"], "hold_and_monitor")
        self.assertEqual(report["data_quality"]["missing_quote_count"], 0)

    def test_generator_tolerates_malformed_json_without_inventing_price(self) -> None:
        report = self._report_for_quote_result({
            "content": [{"type": "text", "text": '{"price": 100,'}]
        })
        item = report["items"][0]
        self.assertEqual(item["mcp_calls"]["quote"]["fields"], {})
        self.assertIsNone(item["position"]["pnl_pct"])
        self.assertEqual(item["action_hint"], "complete_market_data")

    def test_generator_prefers_structured_content_over_text_json(self) -> None:
        for text in ['{"symbol":"600519","price":10,"name":"Stale"}', "not JSON"]:
            with self.subTest(text=text):
                report = self._report_for_quote_result({
                    "content": [{"type": "text", "text": text}],
                    "structuredContent": {"symbol": "600519", "price": 100, "name": "Current"},
                })
                item = report["items"][0]
                self.assertEqual(item["mcp_calls"]["quote"]["fields"]["price"], 100)
                self.assertEqual(item["name"], "Current")
                self.assertEqual(item["action_hint"], "hold_and_monitor")

    def test_generator_rejects_wrong_symbol_in_text_and_structured_results(self) -> None:
        for identity in [{"symbol": "000001"}, {"code": "sz000001"},
                         {"secid": "0.000001"}, {"full_code": "sz600519"}]:
            for structured in [False, True]:
                with self.subTest(identity=identity, structured=structured):
                    payload = {"data": {**identity, "price": 10, "name": "Wrong Stock"}}
                    result = {"content": [{"type": "text", "text": json.dumps(payload)}]}
                    if structured:
                        result["structuredContent"] = payload
                    report = self._report_for_quote_result(result)
                    item = report["items"][0]
                    self.assertEqual(item["mcp_calls"]["quote"]["status"], "error")
                    self.assertNotIn("price", item["mcp_calls"]["quote"]["fields"])
                    self.assertIsNone(item["position"]["pnl_pct"])
                    self.assertIsNone(item["name"])
                    self.assertEqual(item["action_hint"], "complete_market_data")
                    self.assertEqual(report["data_quality"]["failed_symbols"], ["600519"])

    def test_generator_does_not_fallback_from_wrong_structured_symbol_to_text(self) -> None:
        report = self._report_for_quote_result({
            "structuredContent": {"symbol": "000001", "price": 10},
            "content": [{"type": "text", "text": '{"symbol":"600519","price":100}'}],
        })
        self.assertEqual(report["items"][0]["action_hint"], "complete_market_data")

    def test_generator_selects_matching_symbol_from_multiple_quotes(self) -> None:
        report = self._report_for_quote_result({"content": [{"type": "text", "text": json.dumps({
            "quotes": [{"symbol": "000001", "price": 10, "name": "Wrong"},
                       {"symbol": "600519", "price": 100, "name": "Correct"}]
        })}]})
        item = report["items"][0]
        self.assertEqual(item["mcp_calls"]["quote"]["fields"].get("price"), 100)
        self.assertEqual(item["name"], "Correct")
        self.assertEqual(item["action_hint"], "hold_and_monitor")

    def test_generator_does_not_use_error_payload_for_position_analysis(self) -> None:
        report = self._report_for_quote_result({
            "isError": True, "structuredContent": {"symbol": "600519", "price": 10}
        })
        self.assertEqual(report["items"][0]["action_hint"], "complete_market_data")
        self.assertIsNone(report["items"][0]["position"]["pnl_pct"])

    def test_generator_rejects_invalid_prices_in_text_and_structured_content(self) -> None:
        prices = [float("nan"), float("inf"), -float("inf"), "NaN", "inf", "-inf",
                  "1e309", 0, "0", -10, "-10", True, False, "", "invalid"]
        for structured in [False, True]:
            for price in prices:
                with self.subTest(structured=structured, price=price):
                    data = {"symbol": "600519", "price": price, "name": "Known Stock"}
                    result = {"structuredContent": data} if structured else {
                        "content": [{"type": "text", "text": json.dumps(data)}]
                    }
                    report = self._report_for_quote_result(result)
                    item = report["items"][0]
                    self.assertEqual(item["mcp_calls"]["quote"]["status"], "error")
                    self.assertNotIn("price", item["mcp_calls"]["quote"]["fields"])
                    self.assertIsNone(item["position"]["pnl_pct"])
                    self.assertEqual(item["action_hint"], "complete_market_data")
                    self.assertEqual(report["data_quality"]["failed_symbols"], ["600519"])
                    self.assertEqual(report["data_quality"]["missing_quote_count"], 1)
                    json.dumps(report, allow_nan=False)

    def test_generator_accepts_positive_prices_in_text_and_structured_content(self) -> None:
        cases = [(100, 100.0, 11.11, "hold_and_monitor"),
                 ("100.25", 100.25, 11.39, "hold_and_monitor"),
                 ("0.01", 0.01, -99.99, "review_stop_loss")]
        for structured in [False, True]:
            for price, expected, pnl, action in cases:
                with self.subTest(structured=structured, price=price):
                    data = {"symbol": "600519", "price": price}
                    result = {"structuredContent": data} if structured else {
                        "content": [{"type": "text", "text": json.dumps(data)}]
                    }
                    report = self._report_for_quote_result(result)
                    item = report["items"][0]
                    self.assertEqual(item["mcp_calls"]["quote"]["status"], "success")
                    self.assertEqual(item["mcp_calls"]["quote"]["fields"]["price"], expected)
                    self.assertEqual(item["position"]["pnl_pct"], pnl)
                    self.assertEqual(item["action_hint"], action)
                    self.assertEqual(report["data_quality"]["failed_symbol_count"], 0)
                    self.assertEqual(report["data_quality"]["missing_quote_count"], 0)
                    json.dumps(report, allow_nan=False)

    def test_generator_retains_json_safe_raw_payloads_on_success_and_error(self) -> None:
        for structured in [False, True]:
            for is_error in [False, True]:
                with self.subTest(structured=structured, is_error=is_error):
                    data = {"symbol": "600519", "price": 100}
                    result = {"structuredContent": data} if structured else {
                        "content": [{"type": "text", "text": json.dumps(data)}]
                    }
                    result.update({
                        "isError": is_error,
                        "diagnostics": {"volume": 0, "pct_change": -2, "note": "NaN",
                                        "flag": True, "values": [float("nan"), float("inf"),
                                        -float("inf"), 3, {"amount": float("nan")}]},
                    })
                    report = self._report_for_quote_result(result)
                    quote = report["items"][0]["mcp_calls"]["quote"]
                    self.assertEqual(quote["status"], "error" if is_error else "success")
                    self.assertEqual(quote["raw"]["diagnostics"], {
                        "volume": 0, "pct_change": -2, "note": "NaN", "flag": True,
                        "values": [None, None, None, 3, {"amount": None}],
                    })
                    self.assertEqual(quote["raw"]["structuredContent"] if structured else
                                     json.loads(quote["raw"]["content"][0]["text"]), data)
                    json.dumps(report, allow_nan=False)

    def _fake_server_command(self, tmpdir: str, quote_result: dict | None = None) -> list[str]:
        server_path = Path(tmpdir) / "fake_pool_mcp_server.py"
        server_path.write_text(
            textwrap.dedent(
                """
                import json
                import sys

                QUOTE_RESULT = __QUOTE_RESULT__

                TOOLS = [
                    {
                        "name": "tdx_quotes",
                        "description": "Fetch realtime quote",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"symbol": {"type": "string"}},
                            "required": ["symbol"],
                        },
                    },
                    {
                        "name": "tdx_lookup_stock",
                        "description": "Lookup company info",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"code": {"type": "string"}},
                            "required": ["code"],
                        },
                    },
                ]


                def symbol_from_args(args):
                    value = args.get("symbol") or args.get("code") or ""
                    return str(value)[-6:]


                for line in sys.stdin:
                    message = json.loads(line)
                    request_id = message.get("id")
                    if request_id is None:
                        continue
                    method = message.get("method")
                    if method == "initialize":
                        result = {
                            "protocolVersion": message["params"]["protocolVersion"],
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "fake-pool-mcp", "version": "0.0"},
                        }
                        response = {"jsonrpc": "2.0", "id": request_id, "result": result}
                    elif method == "tools/list":
                        response = {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
                    elif method == "tools/call":
                        name = message["params"]["name"]
                        args = message["params"].get("arguments", {})
                        symbol = symbol_from_args(args)
                        if name == "tdx_quotes":
                            price = 25.0 if symbol == "688630" else 100.0
                            result = {
                                "content": [{"type": "text", "text": f"{symbol} quote {price}"}],
                                "structuredContent": {"symbol": symbol, "price": price},
                                "isError": False,
                            }
                            if QUOTE_RESULT is not None:
                                result = QUOTE_RESULT
                        else:
                            result = {
                                "content": [{"type": "text", "text": f"Name {symbol}"}],
                                "structuredContent": {"symbol": symbol, "name": f"Name {symbol}"},
                                "isError": False,
                            }
                        response = {"jsonrpc": "2.0", "id": request_id, "result": result}
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32601, "message": "missing method"},
                        }
                    sys.stdout.write(json.dumps(response) + "\\n")
                    sys.stdout.flush()
                """
            ).replace("__QUOTE_RESULT__", f"json.loads({json.dumps(quote_result)!r})"),
            encoding="utf-8",
        )
        return [sys.executable, str(server_path)]


if __name__ == "__main__":
    unittest.main()
