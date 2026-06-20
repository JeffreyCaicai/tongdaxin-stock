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
