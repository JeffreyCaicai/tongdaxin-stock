# MCP Adapters

Adapters normalize provider-specific data into project-owned schemas before the signal engine reads it.

The MVP primary route is Tongdaxin protocol via `eltdx`:

```bash
pip install "eltdx[mcp]"
eltdx-mcp
```

The local API also exposes `source=tongdaxin` / `source=eltdx`, which uses `eltdx.TdxClient` in process when the package is installed. The MCP server remains the preferred Agent tool surface for richer workflows such as F10, topics, and future Skill-style reports.

## Local MCP tool bridge

The API can launch the `eltdx-mcp` stdio server per request and talk to it through MCP JSON-RPC:

- `GET /mcp/tongdaxin/tools`
- `GET /mcp/eltdx/tools`
- `POST /mcp/tongdaxin/tools/{tool_name}`
- `POST /mcp/eltdx/tools/{tool_name}`
- `POST /stock-pools/{pool_id}/mcp-analysis`

Tool arguments are passed in the request body:

```bash
curl -X POST http://127.0.0.1:8765/mcp/tongdaxin/tools/tdx_quotes \
  -H "Content-Type: application/json" \
  -d '{"arguments":{"symbol":"600519"}}'
```

The exact argument schema is whatever `eltdx-mcp` returns from `tools/list`.
If the binary is not on PATH, set `TDX_ELTDX_MCP_COMMAND`, for example:

```bash
export TDX_ELTDX_MCP_COMMAND='eltdx-mcp'
```

The stock-pool analysis endpoint uses the selected personal stock pool as the full analysis scope. It lists MCP tools, selects quote/profile-like tools by name and description, builds arguments from the tool schema, calls them once per pool symbol, then stores a `stock_pool_mcp_analysis` report.

Planned providers:

- `eltdx` / `eltdx-mcp` as the first Tongdaxin MVP route
- official Tongdaxin Token/OpenClaw plugin when credentials are available
- local TdxQuant when the terminal environment is configured
- Eastmoney and AkShare as fallback/cross-validation providers
- Tushare backup
