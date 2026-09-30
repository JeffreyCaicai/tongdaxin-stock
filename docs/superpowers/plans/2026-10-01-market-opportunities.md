# Market Opportunities Implementation Plan

## Scope

Implement [the design](../specs/2026-10-01-market-opportunities-design.md) in this session under the user's explicit end-to-end authorization.

## Tasks

- [x] Add strict screener parser, bounded diversified discovery and read-only capability tests in opportunity_discovery.py.
- [x] Add asset-only decision mode and recommendation gates/ranking in opportunities.py; test invariance, quality gates and selection.
- [x] Add persistent cancellable scan jobs and API routes; test API validation, progress, cancellation and saved results.
- [x] Add bilingual recommendation view with progress, reasons, full details and explicit add-to-watchlist; verify UI races and layouts.
- [x] Run full regression and live Token scan; document limitations and update handoff.

## Verification

157 tests passed. Independent review findings fixed and regression tested: exchange aliases, Beijing identity, personal ETF exclusion, late cancellation, polling recovery, history language state, and historical watchlist deduplication. Live Token scan: 96 unique upstream candidates, 40 outside plus9 personal analyzed, 10 shortlisted and1 data exclusion. Actual application scan saved without changing personal watchlist or holdings.

Browser plugin absent; used installed Playwright/Chromium. Desktop1440 and mobile390 verified with no page errors or page-level horizontal overflow; temporary-db add-to-watchlist and real-db read-only history/details verified.

## Review Focus

Returned upstream candidates are not assumed to satisfy every natural-language filter. Missing fields never become zero-valued evidence. Pool growth must not silently omit members. Failed scans preserve earlier saved results. Local credentials never appear in result payloads or errors.
