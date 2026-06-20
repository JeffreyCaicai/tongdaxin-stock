# Architecture

## Product Shape

The app is a local-first decision cockpit for personal A-share portfolio management.

MVP architecture:

```text
Tauri + React desktop UI
        |
        | HTTP on localhost
        v
FastAPI local service
        |
        +-- SQLite for portfolio, watchlist, signals, snapshots
        +-- Data adapters for Tongdaxin / AkShare / Tushare
        +-- Rule-based signal engine
        +-- AI explanation layer
```

## Boundaries

- No automatic orders.
- No brokerage trading API in the MVP.
- Every signal is a rule output with an auditable reason.
- LLM output is explanation and review only; it does not create unconstrained buy/sell decisions.
- Secrets stay in local config or OS keychain, never in git.

## First Implementation Loop

1. Manual CRUD for holdings and watchlist.
2. Manual or mocked price input.
3. Basic stop-loss, take-profit, and risk rules.
4. Store generated signals.
5. Show the daily action list in the desktop UI.
