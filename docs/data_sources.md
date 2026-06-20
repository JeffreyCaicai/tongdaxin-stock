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

## Current PoC

The API currently includes a `mock` provider that returns deterministic quote and daily K-line data. This provider exists so the cache, signal, and workbench paths can be developed without external network access or real credentials.

Implemented endpoints:

- `GET /market/quote/{symbol}` fetches one quote, stores it in `market_snapshots`, and records a fetch log.
- `GET /market/kline/{symbol}` fetches daily bars, upserts them into `market_klines`, and records a fetch log.
- `GET /market/snapshots` lists cached quote snapshots.
- `GET /market/klines/{symbol}` lists cached K-line bars.
- `GET /market/fetch-logs` lists success/error records for provider calls.
- `POST /workbench/actions/from-market` fetches quotes for all holdings and generates action signals from cached snapshot IDs.

Next provider target: `eltdx`, because it keeps the MVP close to the Tongdaxin ecosystem while avoiding official token dependencies.
