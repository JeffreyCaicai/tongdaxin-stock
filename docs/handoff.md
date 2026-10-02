# Handoff

The original handoff for this project is kept at:

```text
tongdaxin_stock_handoff.md (repository root)
```

Use it for the original product and data-source context. The current notes below and later user decisions
supersede its early MVP defaults; do not restore removed trading panels or demo-data behavior.

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

## Chan Research Foundation and Reports (2026-10-02)

- The previous research foundation is on `main` through `b4baf36`. The frozen model remains `daily_pen_overlap_v2`; fingerprint checks reject changes to its analysis, price handling or identity dependency.
- `scripts/validate_chan.py` supports explicit bounded `capture` and offline `replay`, `frame`, `report`. Minute data is for timestamp/cache validation only, not multi-period candidate confirmation.
- `report --language zh|en` exports self-contained HTML from a fixed dataset and explicit cutoff. It includes per-security coverage, actual historical closes, latest baseline structure, immutable first candidates, state events and 5/20/60-session price observations. Raw evidence retains its original language. No new server, UI route, live request, credential access or personal database write is involved in report/replay/frame.
- Daily quality diagnostics filter future data before validation. Calendar-verified gaps join the replay timeline, including trailing missing sessions; absent prices cannot invalidate a candidate using the previous close. Unknown calendars do not imply guessed weekday sessions. Flagged endpoint prices are excluded from valid-date summaries.
- Calendar/basis verification gates remain unchanged. The existing real 600519 / SH000300 snapshot has 240 daily bars each, ending 2026-09-30, with zero candidates and unverified calendar/basis. Do not relabel this as current prices, validated returns or improved accuracy.
- Outputs are atomic and exclusive, including rejection of dangling symlinks. Real inputs/HTML reports belong in ignored `data/cache/chan_validation/`; browser QA belongs outside version control.
- See [offline validation guide](chan-validation.md) for commands and evidence boundaries. New structural engines, rolling out-of-sample evaluation and execution-cost models remain future work, not implemented claims.

## Follow-up Integrity and Refresh State (2026-10-02)

- An immature opportunity follow-up checks already observed stock sessions before returning `pending`. Missing sessions, invalid prices, duplicate dates and zero/missing volume yield `unavailable` with null metrics. No post-signal completed sessions, or a complete but immature prefix, may remain pending.
- This new pending check ignores dated stock defects on or before the Shanghai recommendation date; undated defects still block evaluation. Existing matured-window and benchmark batch validation remains conservative and unchanged. No changes to recommendation snapshots, model versions, schema, or the frozen Chan dependencies.
- The bilingual UI explicitly labels retained results while a refresh is queued/running, failed, cancelled or interrupted, and shows the saved evidence dates. Same-run horizon selection survives polling, reconnect, manual refresh and language changes; another run defaults to 20. Reconnection performs a read, not a refresh.
- Validation: all 278 tests passed on Python 3.12 / Node 24, including actual JavaScript execution. Bundled Playwright checked an isolated synthetic FastAPI app in Chinese/English at 1440x1000 and 390x844 (Browser plugin skill unavailable): read-only history navigation, retained dates, refresh/cancel, horizon selection, screenshots, no page overflow, no console errors and no external requests. Independent read-only review found and verified fixes for reconnect/prefix edge cases, with no remaining actionable findings. The personal service was not restarted; QA used a temporary database.
