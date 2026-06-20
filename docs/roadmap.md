# Roadmap

## Milestone 1: Skeleton

- Project docs and environment sample.
- FastAPI local service.
- SQLite schema.
- Basic tests.

## Milestone 2: Portfolio And Watchlist

- Holding CRUD.
- Watchlist CRUD.
- CSV import/export.
- Local persistence.

## Milestone 3: Data Source PoC

- Connect one provider such as `eltdx` or AkShare.
- Fetch quote and kline for a single stock.
- Cache raw snapshots with source and timestamp.

Current implementation uses the built-in `mock` provider to prove the adapter, cache, logging, and signal integration path before adding a live dependency.

## Milestone 4: First Signal Engine

- MA, MACD, RSI, ATR, volume moving average.
- Stop-loss, take-profit, trend break, pullback and breakout rules.
- Structured JSON signals.

Implemented with pure-Python indicators and enhanced technical signal rules.

## Milestone 5: AI Explanation Layer

- Stock diagnosis report.
- Daily review.
- Trading plan text with data references.

Implemented as a deterministic explanation layer that can later be replaced or augmented by an LLM. Reports include data references and can be persisted.

## Milestone 6: Backtest And Review

- Persist historical signals.
- Backtest rule outcomes.
- Report win rate, risk/reward and max drawdown.

Implemented with a first MA/volume trend backtest, persistent backtest results, and saved-signal review outcomes.
