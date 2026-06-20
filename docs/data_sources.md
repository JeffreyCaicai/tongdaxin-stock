# Data Sources

## Preferred MVP Path

Start with one low-friction provider, then add cross-checks.

Priority:

1. Official Tongdaxin Token/OpenClaw-compatible route when credentials are available.
2. `eltdx` for Tongdaxin protocol PoC and MCP tool bridge.
3. Eastmoney as a no-token fallback and cross-validation source.
4. Local TdxQuant route if the local Tongdaxin environment is already configured.

## Adapter Contract

Each adapter should normalize output into project-owned structures:

- quote snapshot
- daily/intraday kline series
- basic company metadata
- sector/theme metadata
- data source name
- fetched timestamp
- raw payload hash or JSON

The rule engine should never depend directly on provider-specific payloads.

## Current Providers

The official Token route is available through `source=tdx-official`:

- Requires `TDX_API_KEY` in the shell or local `.env`; `TDX_API_TOKEN` is also accepted as a compatibility fallback.
- Uses `TDX_API_DATA_ENDPOINT`, defaulting to `http://tdxhub.icfqs.com:7615/TQLEX`.
- Quote calls use `Entry=TdxShare.PBHQInfo`.
- K-line calls use `Entry=TdxShare.PBFXT`.
- Requests send the token in the HTTP `token` header and never store it in the database payload.

The Tongdaxin protocol/MCP route remains available:

- `source=tongdaxin` / `source=eltdx` uses the optional `eltdx` provider.
- Install with `pip install "eltdx[mcp]"`.
- Run `eltdx-mcp` when an MCP stdio server is needed for Agent tools.
- In-process API calls use `eltdx.TdxClient` so the local workbench can still normalize quote/K-line data into project-owned schemas.
- MCP tool calls go through `GET /mcp/tongdaxin/tools` and `POST /mcp/tongdaxin/tools/{tool_name}`. This is the route for richer Tongdaxin tool capabilities such as F10, topics, code lookup, and future Skill-style workflows.

The API also includes a zero-dependency `eastmoney` provider for fallback quote checks and cross-validation, plus a `mock` provider for deterministic offline tests.

Implemented endpoints:

- `GET /market/quote/{symbol}` fetches one quote, stores it in `market_snapshots`, and records a fetch log.
- `GET /market/kline/{symbol}` fetches daily bars, upserts them into `market_klines`, and records a fetch log.
- `GET /market/snapshots` lists cached quote snapshots.
- `GET /market/klines/{symbol}` lists cached K-line bars.
- `GET /market/fetch-logs` lists success/error records for provider calls.
- `GET /mcp/tongdaxin/tools` lists the tools exposed by `eltdx-mcp`.
- `POST /mcp/tongdaxin/tools/{tool_name}` calls one MCP tool with an `arguments` object.
- `POST /stock-pools/{pool_id}/mcp-analysis` analyzes only the selected personal stock pool by listing MCP tools, selecting quote/profile-like tools, calling them per pool symbol, and saving a stock-pool report.
- `POST /workbench/actions/from-market` fetches quotes for all holdings and generates action signals from cached snapshot IDs.

Additional providers:

- `source=tdx-official` uses Tongdaxin official Token data-service endpoints.
- `source=tongdaxin` / `source=eltdx` uses Tongdaxin protocol through eltdx.
- `source=eastmoney` uses Eastmoney public quote/K-line endpoints as fallback and requires no extra Python package.
- `source=akshare` uses AkShare when the package is installed locally. If it is not installed, the API returns a clear provider error and the app can continue using `source=mock`.
- `source=mock` uses synthetic demo data and should not be treated as market truth.

Next provider target: local TdxQuant when the user has a configured terminal.
