from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from services.api.app.mcp_tools import (
    McpServerConfig,
    McpStdioClient,
    McpToolError,
    call_eltdx_mcp_tool,
    list_eltdx_mcp_tools,
)


class McpStdioClientTests(unittest.TestCase):
    def test_lists_and_calls_tools_over_stdio(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = McpServerConfig(
                command=self._fake_server_command(tmpdir),
                timeout_seconds=3,
            )

            tools = list_eltdx_mcp_tools(config)
            result = call_eltdx_mcp_tool(
                "tdx_quotes",
                {"symbol": "600519"},
                config,
            )

        self.assertEqual(tools[0]["name"], "tdx_quotes")
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"][0]["text"], "called tdx_quotes")

    def test_context_manager_supports_reusing_one_server_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = McpServerConfig(
                command=self._fake_server_command(tmpdir),
                timeout_seconds=3,
            )
            with McpStdioClient(config) as client:
                initialized = client.initialize()
                tools = client.list_tools()
                result = client.call_tool("tdx_kline", {"symbol": "000001"})

        self.assertEqual(initialized["serverInfo"]["name"], "fake-eltdx-mcp")
        self.assertEqual([tool["name"] for tool in tools], ["tdx_quotes", "tdx_kline"])
        self.assertEqual(result["content"][0]["text"], "called tdx_kline")

    def test_missing_command_reports_install_hint(self) -> None:
        config = McpServerConfig(
            command=["/definitely/missing/eltdx-mcp"],
            timeout_seconds=1,
        )

        with self.assertRaisesRegex(McpToolError, "pip install"):
            list_eltdx_mcp_tools(config)

    def _fake_server_command(self, tmpdir: str) -> list[str]:
        server_path = Path(tmpdir) / "fake_mcp_server.py"
        server_path.write_text(
            textwrap.dedent(
                """
                import json
                import sys


                TOOLS = [
                    {
                        "name": "tdx_quotes",
                        "description": "Fetch quote",
                        "inputSchema": {"type": "object"},
                    },
                    {
                        "name": "tdx_kline",
                        "description": "Fetch K-line",
                        "inputSchema": {"type": "object"},
                    },
                ]


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
                            "serverInfo": {"name": "fake-eltdx-mcp", "version": "0.0"},
                        }
                        response = {"jsonrpc": "2.0", "id": request_id, "result": result}
                    elif method == "tools/list":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {"tools": TOOLS},
                        }
                    elif method == "tools/call":
                        name = message["params"]["name"]
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"called {name}"}],
                                "isError": False,
                            },
                        }
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
