# MCP Adapters

Adapters normalize provider-specific data into project-owned schemas before the signal engine reads it.

The MVP primary route is Tongdaxin protocol via `eltdx`:

```bash
pip install "eltdx[mcp]"
eltdx-mcp
```

The local API also exposes `source=tongdaxin` / `source=eltdx`, which uses `eltdx.TdxClient` in process when the package is installed. The MCP server remains the preferred Agent tool surface for richer workflows such as F10, topics, and future Skill-style reports.

Planned providers:

- `eltdx` / `eltdx-mcp` as the first Tongdaxin MVP route
- official Tongdaxin Token/OpenClaw plugin when credentials are available
- local TdxQuant when the terminal environment is configured
- Eastmoney and AkShare as fallback/cross-validation providers
- Tushare backup
