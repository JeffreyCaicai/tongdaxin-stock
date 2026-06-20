from __future__ import annotations

import json
import os
import selectors
import shlex
import subprocess
import time
from dataclasses import dataclass
from typing import Any


class McpToolError(RuntimeError):
    pass


@dataclass(frozen=True)
class McpServerConfig:
    command: list[str]
    timeout_seconds: float = 15.0


class McpStdioClient:
    def __init__(self, config: McpServerConfig) -> None:
        self.config = config
        self._process: subprocess.Popen[str] | None = None
        self._next_id = 1

    def __enter__(self) -> McpStdioClient:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def start(self) -> None:
        if self._process is not None:
            return
        if not self.config.command:
            raise McpToolError("MCP server command is empty.")
        try:
            self._process = subprocess.Popen(
                self.config.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError as exc:
            command = self.config.command[0]
            raise McpToolError(
                f"MCP server command '{command}' was not found. "
                "Install Tongdaxin tooling with 'pip install \"eltdx[mcp]\"' "
                "and make sure 'eltdx-mcp' is on PATH, or set "
                "TDX_ELTDX_MCP_COMMAND."
            ) from exc
        except OSError as exc:
            raise McpToolError(f"Failed to start MCP server: {exc}") from exc

    def initialize(self) -> dict[str, Any]:
        result = self.request(
            "initialize",
            {
                "protocolVersion": os.environ.get(
                    "TDX_MCP_PROTOCOL_VERSION", "2025-06-18"
                ),
                "capabilities": {},
                "clientInfo": {
                    "name": "tongdaxin-stock",
                    "version": "0.1.0",
                },
            },
        )
        self.notify("notifications/initialized", {})
        return result

    def list_tools(self) -> list[dict[str, Any]]:
        result = self.request("tools/list", {})
        tools = result.get("tools", [])
        if not isinstance(tools, list):
            raise McpToolError("MCP tools/list returned an invalid tools payload.")
        return tools

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if not name:
            raise McpToolError("MCP tool name is required.")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise McpToolError("MCP tool arguments must be an object.")
        return self.request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {},
            }
        )
        return self._read_response(request_id)

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._send(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
            }
        )

    def close(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
        finally:
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe is not None and not pipe.closed:
                    pipe.close()

    def _send(self, message: dict[str, Any]) -> None:
        self.start()
        process = self._process
        if process is None or process.stdin is None:
            raise McpToolError("MCP server stdin is unavailable.")
        if process.poll() is not None:
            raise McpToolError(self._server_exit_message(process))
        try:
            process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            process.stdin.flush()
        except BrokenPipeError as exc:
            raise McpToolError(self._server_exit_message(process)) from exc

    def _read_response(self, expected_id: int) -> dict[str, Any]:
        process = self._process
        if process is None or process.stdout is None:
            raise McpToolError("MCP server stdout is unavailable.")

        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + self.config.timeout_seconds

        try:
            while True:
                if process.poll() is not None:
                    raise McpToolError(self._server_exit_message(process))
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise McpToolError(
                        f"MCP server timed out after {self.config.timeout_seconds:g}s."
                    )
                events = selector.select(timeout=remaining)
                if not events:
                    raise McpToolError(
                        f"MCP server timed out after {self.config.timeout_seconds:g}s."
                    )
                line = process.stdout.readline()
                if not line:
                    raise McpToolError(self._server_exit_message(process))
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if message.get("id") != expected_id:
                    continue
                if "error" in message:
                    error = message["error"]
                    if isinstance(error, dict):
                        detail = error.get("message") or json.dumps(
                            error, ensure_ascii=False
                        )
                    else:
                        detail = str(error)
                    raise McpToolError(f"MCP {detail}")
                result = message.get("result", {})
                if not isinstance(result, dict):
                    raise McpToolError("MCP response result must be an object.")
                return result
        finally:
            selector.close()

    def _server_exit_message(self, process: subprocess.Popen[str]) -> str:
        stderr = ""
        if process.stderr is not None and process.poll() is not None:
            stderr = process.stderr.read().strip()
        if stderr:
            return f"MCP server exited with code {process.returncode}: {stderr}"
        return f"MCP server exited with code {process.returncode}."


def eltdx_mcp_config() -> McpServerConfig:
    command_text = os.environ.get("TDX_ELTDX_MCP_COMMAND", "eltdx-mcp")
    timeout = float(os.environ.get("TDX_MCP_TIMEOUT_SECONDS", "15"))
    return McpServerConfig(command=shlex.split(command_text), timeout_seconds=timeout)


def list_eltdx_mcp_tools(config: McpServerConfig | None = None) -> list[dict[str, Any]]:
    with McpStdioClient(config or eltdx_mcp_config()) as client:
        client.initialize()
        return client.list_tools()


def call_eltdx_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    config: McpServerConfig | None = None,
) -> dict[str, Any]:
    with McpStdioClient(config or eltdx_mcp_config()) as client:
        client.initialize()
        return client.call_tool(tool_name, arguments)
