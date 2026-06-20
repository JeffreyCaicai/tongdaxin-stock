# Data Sources

## Preferred MVP Path

Start with one low-friction provider, then add cross-checks.

Priority:

1. `eltdx` for Tongdaxin protocol PoC.
2. AkShare as backup and cross-validation source.
3. Official Tongdaxin Token/OpenClaw route when credentials are available.
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

The primary route is Tongdaxin protocol/MCP:

- `source=tongdaxin` / `source=eltdx` uses the optional `eltdx` provider.
- Install with `pip install "eltdx[mcp]"`.
- Run `eltdx-mcp` when an MCP stdio server is needed for Agent tools.
- In-process API calls use `eltdx.TdxClient` so the local workbench can still normalize quote/K-line data into project-owned schemas.

The API also includes a zero-dependency `eastmoney` provider for fallback quote checks and cross-validation, plus a `mock` provider for deterministic offline tests.

Implemented endpoints:

- `GET /market/quote/{symbol}` fetches one quote, stores it in `market_snapshots`, and records a fetch log.
- `GET /market/kline/{symbol}` fetches daily bars, upserts them into `market_klines`, and records a fetch log.
- `GET /market/snapshots` lists cached quote snapshots.
- `GET /market/klines/{symbol}` lists cached K-line bars.
- `GET /market/fetch-logs` lists success/error records for provider calls.
- `POST /workbench/actions/from-market` fetches quotes for all holdings and generates action signals from cached snapshot IDs.

Additional providers:

- `source=tongdaxin` / `source=eltdx` uses Tongdaxin protocol through eltdx.
- `source=eastmoney` uses Eastmoney public quote/K-line endpoints as fallback and requires no extra Python package.
- `source=akshare` uses AkShare when the package is installed locally. If it is not installed, the API returns a clear provider error and the app can continue using `source=mock`.
- `source=mock` uses synthetic demo data and should not be treated as market truth.

Next provider target: official Tongdaxin Token/OpenClaw once credentials are available, then local TdxQuant when the user has a configured terminal.
