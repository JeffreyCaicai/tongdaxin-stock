# Analysis Correctness and Result Detail Plan

**Goal:** Fix the confirmed review defects and make stock-level analysis readable and traceable.

**Architecture:** Keep the existing FastAPI, SQLite and static JavaScript UI. Repair provider identity and parsing, enforce analysis data contracts, and expose a compact summary with expandable evidence. No trading execution.

**Scope:** The ten findings in the approved project review; data timestamps/model identity and previous-report comparison. Forecasts remain a fixed 20-session rule score until empirical calibration exists.

## Constraints

- Preserve local holdings and environment files; never commit credentials.
- Use synthetic fixtures and temporary databases for tests, not live credentials.
- Keep industry/style attribution unavailable until actual supporting data exists.
- Show partial valuation and missing/stale analysis explicitly.

## Tasks

- [x] Provider routing and MCP text JSON parsing: add failing tests, repair exchange-qualified benchmark identity and parser behavior.
- [x] Decision engine: add failing tests for aligned date windows, missing/stale data confidence, fixed horizon, and trace fields; implement deterministic data-quality gates.
- [x] API/cache/pool/review: test fetched-batch provenance, empty pools, duplicate members, and reading current decision reports; repair the flows.
- [x] UI: test actual JavaScript valuation and request ordering; implement compact result overview, expandable per-stock evidence, provenance and partial valuation.
- [x] Verification: run the full suite, JavaScript checks, isolated API/browser workflows, desktop/mobile screenshots, and independent review.

## Review Focus

- A benchmark index and a stock can share a numeric symbol: market identity must survive requests and caching.
- Missing quotes are not zero prices; incomplete portfolios must not display complete totals.
- Suspended/missing-bar securities must not compare different date intervals.
- An empty pool must stay empty, including report generation and legacy API paths.
- Older asynchronous results must not overwrite the user's current choice.

## Verified Results

- Full offline suite: 145 tests passed with no skips, including actual Node execution and 128 deferred-request race combinations.
- Isolated FastAPI/browser QA: 20 concurrent mock quote requests returned HTTP 200; no unexpected 5xx or JavaScript page errors.
- Browser flows passed: decision details, quantity/cost editing and persistence, compatible-report comparison, saved review, missing quote with partial valuation, and language switching.
- Desktop 1440px and mobile 390px screenshots inspected. Page width stays within the viewport; wide holdings data scrolls only within its table container.
- Independent review additionally found and repaired stale shared inputs, invalid volume/OHLC, nonfinite MCP prices, and SQLite cross-worker/connection-cleanup issues, with regression tests.
- No live Token permission test or empirical probability calibration was performed. Real holdings and local credential files were not used for QA or staged.
