# Signal Engine

Signals must be explainable, auditable, and later backtestable.

## MVP Inputs

- Holding or watchlist plan.
- Latest price.
- Optional market snapshot.
- Optional indicator snapshot.

## MVP Holding Rules

- `hard_stop_loss`: latest price is at or below planned stop loss.
- `take_profit`: latest price is at or above planned take profit.
- `max_loss_warning`: unrealized loss exceeds configured max tolerated loss.
- `hold_observe`: no action trigger, keep watching.

## Output Contract

Each signal includes:

- symbol
- action
- signal type
- risk level
- strength
- price
- reasons
- next check

All signals should be stored in SQLite so later reports can explain what changed and when.

## Workbench Batch Evaluation

Until a live data source is connected, `POST /workbench/actions` accepts a symbol-to-price map and evaluates all holdings in one call. Missing prices are returned explicitly so the UI can show which positions still need data.

`POST /workbench/actions/from-market` now fetches quote and daily K-line data from the configured provider, computes MA/MACD/RSI/ATR/volume indicators, and stores the resulting action signals.

## Backtest And Review

`POST /backtests/{symbol}` runs the first MA/volume trend strategy over cached or freshly fetched K-line data. Results include win rate, average win/loss, risk/reward ratio, max drawdown, trades, and equity curve.

`GET /reviews/signals` compares saved signals with current provider quotes and labels outcomes as favorable, unfavorable, neutral, or unverified.
