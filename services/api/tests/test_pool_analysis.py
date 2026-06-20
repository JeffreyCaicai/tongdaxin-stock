from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from services.api.app.mcp_tools import McpServerConfig
from services.api.app.pool_analysis import generate_stock_pool_mcp_analysis


class StockPoolMcpAnalysisTests(unittest.TestCase):
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

    def _fake_server_command(self, tmpdir: str) -> list[str]:
        server_path = Path(tmpdir) / "fake_pool_mcp_server.py"
        server_path.write_text(
            textwrap.dedent(
                """
                import json
                import sys


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
            ),
            encoding="utf-8",
        )
        return [sys.executable, str(server_path)]


if __name__ == "__main__":
    unittest.main()
