# Project Instructions

Read `docs/handoff.md` before changing this project. It describes the current
implementation and supersedes early MVP defaults in `tongdaxin_stock_handoff.md`.
For Codex Cloud setup, also read `docs/codex-cloud.md`.

## Product And Evidence Boundaries

- This is a personal stock research and portfolio valuation workbench, not an
  order execution system. Do not restore removed trading panels or auto-trading.
- Preserve Chinese/English UI support and the existing Python/FastAPI architecture.
- Never silently replace failed real market requests with mock data. Mock data is
  for explicitly selected tests and demonstrations only.
- Rule-based scenario scores are uncalibrated. Do not describe them as validated
  probabilities, buy/sell certainty, or proven improvements in returns.
- Keep the frozen Chan research model and dataset/evaluation contracts intact;
  a new model requires explicit versioning and separate validation.

## Development

- Supported development baseline: Python 3.12 and Node.js 24. Node is needed for
  the JavaScript regression tests; do not accept a run that silently skips them.
- Install: `python3.12 -m venv .venv`, then
  `.venv/bin/python -m pip install -r requirements-dev.txt`.
- Test from the repository root:
  `.venv/bin/python -B -m unittest discover services/api/tests`.
- For a clean development database, launch with:
  `TDX_STOCK_DB_PATH=data/cloud-dev.db .venv/bin/python scripts/run_api.py`.
- Full functionality requires FastAPI and uvicorn. The standard-library fallback
  supports older routes only; a working fallback is not a successful full setup.
- Background jobs are single-process. Do not start multiple API workers without
  redesigning job coordination and validating SQLite behavior.

## Data And Secrets

- Do not read, print, commit, upload or copy `.env`, `.env.save`, personal database
  files, real market snapshots, or cached reports as part of code synchronization.
- Use temporary databases in tests. `scripts/smoke_api.py` mutates data and must
  not target a personal database or an existing user service.
- Do not request or copy production credentials to make offline tests pass.
  Configure real-data access separately with the user's authorization.
- Preserve the source, timestamps, missing-data diagnostics and freshness of
  market evidence. Never fill unknown prices with zero or fabricate validation.
- Cloud work does not automatically synchronize back to the local checkout.
  Commit reviewed changes to GitHub and use normal pull requests or fast-forward
  pulls. Do not force-push or discard another session's work.

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call. Name a file or symbol in the query to read its current line-numbered source. If it is listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely. Indexing is the user's decision.
<!-- CODEGRAPH_END -->
