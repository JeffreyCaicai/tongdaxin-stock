# Codex Cloud Development

This guide prepares the existing workbench for remote development. It does not
deploy a public website or migrate personal portfolios. Publishing a Codex Cloud
environment is separate from pushing this repository to GitHub.

## Environment Setup

1. Open Codex Cloud environments in your ChatGPT account and create an environment
   for `JeffreyCaicai/tongdaxin-stock`. Reuse a matching environment if one already
   exists. Keep access private to the owner.
2. Use `main` as the reviewed baseline. Check its commit against GitHub before
   starting work; local uncommitted files are not part of the cloud checkout.
3. Ask setup to use Python 3.12 and Node.js 24 and run the commands below from the
   repository root. `httpx` is required by FastAPI's test client even though the
   runtime service does not need it.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
node --version
.venv/bin/python -B -m unittest discover services/api/tests
```

The `node --version` check must succeed. Some JavaScript tests skip themselves
when Node is missing, so a green result with those tests skipped is insufficient.
The existing baseline at `885211b` has 269 passing tests; check the actual test
count and output for later revisions rather than assuming this count is fixed.

`eltdx[mcp]` is optional and is not required for offline tests or the official
Token provider. Do not install it as a workaround for missing official API access.

## Start And Check The Workbench

Use a separate database and the full FastAPI service. The launch script initializes
the database automatically. Keep these variables on the same launch command, since
exports in an installation shell may not persist into a later task.

```bash
TDX_STOCK_DB_PATH=data/cloud-dev.db \
TDX_STOCK_API_HOST=127.0.0.1 \
TDX_STOCK_API_PORT=8765 \
.venv/bin/python scripts/run_api.py
```

In another terminal in that same cloud task:

```bash
curl --fail http://127.0.0.1:8765/health
curl --fail http://127.0.0.1:8765/openapi.json
```

Check the startup log says FastAPI, not `fallback`, and that the OpenAPI document
includes the decision-engine, Chan-analysis and opportunity routes. Use the cloud
task's private preview if available. Its `127.0.0.1` address refers to the cloud
machine, not your laptop; do not expect a local browser address to reach it.
No public tunnel or unauthenticated public endpoint is part of this setup.

The fresh database has no personal holdings, watchlist entries or saved reports.
That is intentional. Test data must be explicitly synthetic and kept separate
from real-data analysis. Do not run `scripts/smoke_api.py` on a personal database.

## Credentials And Network

- Code synchronization must not include `.env`, `.env.save`, `data/*.db`,
  `data/cache/`, personal reports, or local virtual environments.
- Offline regression tests do not require a Token or market network access.
- Real-data development requires separate `TDX_API_KEY` configuration in the
  account's personal cloud environment settings. Do not put its value in source,
  setup scripts, task prompts, screenshots or logs.
- Start with only the package-network access needed for dependency installation.
  Review extra market-data destinations separately before enabling them.
- The current default endpoint uses HTTP on port 7615. A cloud network secret
  restricted to HTTPS/443 is not a drop-in substitute for this provider. Confirm
  an authorized, supported connection before making real-data requests; never
  disable transport checks or expose the key through a public proxy.
- Cloud-IP, network policy and Token permission failures must remain visible.
  Do not claim live data was verified based only on passing offline tests.

## Publish And Continue Development

After cloud setup actually passes the checks, review and publish the private
environment. Select **Work in > Cloud**, choose that environment, and start the
next development task. Do not claim the environment is ready before the UI
confirms publication and a cloud task passes the checks.

Use this initial task prompt:

```text
Read AGENTS.md, docs/handoff.md and docs/codex-cloud.md. Verify the checkout and
dependencies, then run the full offline test suite including Node-based tests.
Start the FastAPI workbench with a separate data/cloud-dev.db and check /health
and /openapi.json. Do not load personal data, configure credentials, make live
market calls, modify the analysis algorithms, or deploy a public site. Report
the commit, test results and any remaining setup limitation.
```

A cloud task can continue while the laptop sleeps; this local task cannot acquire
that behavior merely because its Git commits were pushed. Continue in the cloud
task on the web/mobile client. Commit cloud changes to a separate `codex/` branch
and review them before merging. Back on the laptop, finish or preserve local
changes, then use `git pull --ff-only` after the reviewed merge. Database contents
and unpublished changes do not synchronize automatically.

Official setup and lifecycle reference:
[Codex Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments).
