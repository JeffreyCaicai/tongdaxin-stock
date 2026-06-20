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
