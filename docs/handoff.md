# Handoff

The original handoff for this project is kept at:

```text
tongdaxin_stock_handoff.md (repository root)
```

Use it as the source of truth for product boundaries, data-source research, MVP scope, and roadmap decisions.

## Current Implementation Notes (2026-09-30)

- Product focus is personal stock analysis and editable portfolio valuation, not order execution.
- The default benchmark is `SH000300`. Exchange-qualified identities prevent confusing an index with a bare stock code.
- Decision v1 supports daily bars and a fixed 20-trading-session horizon. Its softmax scores are uncalibrated, not validated forecast probabilities.
- Relative-return windows use shared index dates, or pool dates when index data is absent. Endpoint dates and carry-forward lags are recorded; stale or missing evidence lowers confidence.
- A fresh K-line request returns its fetched batch, not unrelated newer cache rows. Empty pools do not include external holdings.
- Stale shared inputs are excluded before regime/prior scoring. Invalid OHLC and volume cannot fabricate indicator evidence; invalid MCP prices are rejected with JSON-safe diagnostics.
- SQLite connections are request-local, allow sequential FastAPI worker handoff, and are explicitly closed after initialization and request cleanup.
- Portfolio summaries distinguish missing prices from zero and show partial valuation coverage.
- Saved decision reviews retain original timestamps and scores. Changed pool membership is disclosed; comparisons require matching pool/source/period/horizon/benchmark/model.
- Current decision and Chan workflows require FastAPI/uvicorn. The standard-library fallback supports only older routes.
- Use `.venv/bin/python -B -m unittest discover services/api/tests` for backend and actual JavaScript regression tests. JavaScript tests require Node on PATH.
- Local launch: `.venv/bin/python scripts/run_api.py`, then open `http://127.0.0.1:8765/`.
- Keep `.env`, `.env.save`, credentials, local database files and QA screenshots out of commits.

See [the repair plan](superpowers/plans/2026-09-30-analysis-correctness.md) and repository tests for this iteration's verified scope.

## Market Opportunities (2026-10-01)

- New primary action discovers outside stocks using the real Token screener, then merges all personal watched/held stocks for asset-only ranking. Three bounded queries, two pages of20 each, round-robin deduplication, default40 outside candidates. This is a screened subset, not an exhaustive market scan.
- Screener permission and quote/K-line access were live verified. Explicit turnover/momentum ordering avoids upstream default code-order bias. Natural-language screening is candidate discovery only; local analysis enforces quality and eligibility.
- Asset-only mode excludes holding cost/P&L and selected-sample breadth/relative performance. Benchmark is SH000300, daily240 bars, fixed20-session horizon. Missing benchmark, stale/invalid input, inadequate history, inactive/illiquid stocks and non-stock instruments cannot enter the shortlist.
- SH/SZ aliases deduplicate; Beijing identities remain explicitly qualified. New candidates can be added to watchlist only by user action.
- `POST /stock-pools/{id}/opportunities` starts a background job; GET same path lists history; `GET /opportunities/{id}` reads status/result; DELETE requests cancellation. Runs persist in `opportunity_runs`. Single-process local service supports one scan at a time with three data workers. Restart marks interrupted jobs; there is no distributed job queue.
- Frontend has progress, cancel, origin filters, all assessments, reasons, conditions and details, plus saved history. Default source for new browser storage is now official Token; existing source choice is preserved.
- This is an uncalibrated technical research shortlist. No fundamentals, industry/style attribution, event research, automatic execution or validated win-rate claims. See [Ganlee retrospective check](research/2026-10-01-ganlee-case.md).
