# Tongdaxin Stock

个人使用的 A 股持仓与目标股决策支持桌面软件。

本项目定位是个人股票分析与决策支持工作台：围绕关注股和持仓，展示行情、浮动盈亏、缠论结构和多证据情景分析。它不执行交易，不构成投资建议。

## 当前状态

- 已建立项目骨架。
- 已选择 `Tauri + React` 作为桌面端方向，MVP 先以本地 FastAPI 服务打通数据和规则闭环。
- 已建立 SQLite schema、持仓 CRUD、目标池 CRUD 和基础信号评估入口。
- 已支持持仓/目标池 CSV 导入导出、信号历史查询和工作台批量行动信号生成。
- 数据源已具备 provider 抽象：`source=tdx-official` 走通达信官方 Token 数据服务，`source=tongdaxin` / `source=eltdx` 走可选通达信协议 provider 和 `eltdx-mcp` 工具桥。
- `source=eastmoney` 保留为零依赖兜底和交叉验证源；`source=mock` 仅用于离线演示和测试。
- 工作台新增个人股票池：先选择股票池，再围绕该池内股票展示持仓、信号、复盘和池级分析。
- 持仓决策引擎固定使用日线和未来 20 个交易日的观察期，默认大盘基准为上海指数 `SH000300`，避免与深圳股票代码混淆。
- 上涨/震荡/下跌输出是规则式、未经历史校准的情景评分，不是已验证的预测概率。缺失、过期或不足的数据会明确标注并降低信心；行业和风格数据不可用时不伪造归因。
- 结果按股票提供可展开的证据、因子窗口、数据时间和价格来源。同池、同数据源、同周期、同模型的报告可比较；复盘读取保存的决策分析快照，不自动重新拉行情。

## 目录结构

```text
apps/desktop/              # Tauri + React 桌面端，占位说明
services/api/              # FastAPI 本地服务
services/analysis/         # 指标、信号、回测模块
services/mcp-adapters/     # 通达信/AkShare/Tushare MCP 适配
packages/shared/           # 跨端 schema 和类型约定
packages/strategy-core/    # 策略规则核心
data/cache/                # 本地缓存，不提交
docs/                      # 架构、数据源、信号引擎、路线图
scripts/                   # 本地维护脚本
```

## 本地后端

已配置好虚拟环境时，推荐使用：

```bash
.venv/bin/python scripts/run_api.py
```

未安装 FastAPI/uvicorn 时，下列命令会启动标准库 fallback API。它仅支持部分旧版接口，不支持当前决策引擎和缠论分析；完整工作台需要下方的 FastAPI 环境。

```bash
python3 scripts/run_api.py
```

启动后打开 `http://127.0.0.1:8765/`，可以添加关注股、编辑持仓数量和成本价、查看盈亏并执行股票分析。右上角可在中文和 English 之间切换。

完整 FastAPI 环境：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
pip install "eltdx[mcp]"
cp .env.example .env
python scripts/init_db.py
uvicorn services.api.app.main:app --reload --host 127.0.0.1 --port 8765
```

`eltdx` 需要 Python 3.10+。如果系统 `python3` 是 3.9，先安装/指定 Python 3.10 以上版本创建 `.venv`，否则通达信源会因为缺少 `eltdx` 而不可用。

通达信官方 Token 数据源：

```bash
# 本地 .env 或 shell 环境变量均可，真实 Key 不要提交到 git
TDX_API_KEY=your-tdx-api-key
TDX_API_DATA_ENDPOINT=http://tdxhub.icfqs.com:7615/TQLEX
```

配置后在 UI 右上角选择“通达信官方 Token”，或在 API 请求里传 `source=tdx-official`。该路线按官方 OpenClaw 插件兼容方式调用 `TdxShare.PBHQInfo`（实时行情）和 `TdxShare.PBFXT`（K 线），HTTP header 使用 `token`。

健康检查：

```bash
curl http://127.0.0.1:8765/health
```

## API 入口

- `GET /holdings`
- `POST /holdings`
- `GET /holdings/export.csv`
- `POST /holdings/import.csv`
- `POST /holdings/{holding_id}/signals`
- `GET /watchlist`
- `POST /watchlist`
- `GET /watchlist/export.csv`
- `POST /watchlist/import.csv`
- `GET /signals`
- `GET /reports`
- `GET /reports/stock/{symbol}`
- `GET /reports/trading-plan/{holding_id}`
- `GET /reports/daily-review`
- `GET /backtests`
- `POST /backtests/{symbol}`
- `GET /reviews/signals`
- `GET /market/quote/{symbol}`
- `GET /market/kline/{symbol}`
- `GET /market/indicators/{symbol}`
- `GET /market/snapshots`
- `GET /market/klines/{symbol}`
- `GET /market/fetch-logs`
- `GET /mcp/eltdx/tools`
- `GET /mcp/tongdaxin/tools`
- `POST /mcp/eltdx/tools/{tool_name}`
- `POST /mcp/tongdaxin/tools/{tool_name}`
- `POST /stock-pools/{pool_id}/mcp-analysis`
- `POST /stock-pools/{pool_id}/market-analysis`
- `POST /stock-pools/{pool_id}/chan-analysis`
- `POST /stock-pools/{pool_id}/decision-engine`
- `POST /workbench/actions`
- `POST /workbench/actions/from-market`

工作台行动信号示例：

```bash
curl -X POST http://127.0.0.1:8765/workbench/actions \
  -H "Content-Type: application/json" \
  -d '{"prices":{"600519":1500,"000001":12.2},"persist":true}'
```

安装通达信协议 provider：

```bash
pip install "eltdx[mcp]"
eltdx-mcp
```

本地 API 可以直接启动 `eltdx-mcp` stdio 进程并调用工具。默认命令是 `eltdx-mcp`，如需指定 venv 或 uvx 命令可设置：

```bash
export TDX_ELTDX_MCP_COMMAND='eltdx-mcp'
export TDX_MCP_TIMEOUT_SECONDS=15
```

列出通达信 MCP 工具并调用某个工具：

```bash
curl http://127.0.0.1:8765/mcp/tongdaxin/tools
curl -X POST http://127.0.0.1:8765/mcp/tongdaxin/tools/tdx_quotes \
  -H "Content-Type: application/json" \
  -d '{"arguments":{"symbol":"600519"}}'
```

基于当前个人股票池执行 MCP 池级分析：

```bash
curl -X POST http://127.0.0.1:8765/stock-pools/1/mcp-analysis \
  -H "Content-Type: application/json" \
  -d '{"persist":true,"max_symbols":30,"include_profile":true}'
```

如果 MCP 工具参数和默认推断不一致，可以指定工具名和参数模板：

```bash
curl -X POST http://127.0.0.1:8765/stock-pools/1/mcp-analysis \
  -H "Content-Type: application/json" \
  -d '{"quote_tool":"tdx_quotes","quote_arguments":{"code":"{tdx_code}"}}'
```

从通达信源自动拉 quote 并生成当前股票池行动信号：

```bash
curl -X POST http://127.0.0.1:8765/workbench/actions/from-market \
  -H "Content-Type: application/json" \
  -d '{"source":"tongdaxin","persist":true,"pool_id":1}'
```

拉取单股 quote / K 线：

```bash
curl "http://127.0.0.1:8765/market/quote/600519?source=tdx-official"
curl "http://127.0.0.1:8765/market/kline/600519?source=tdx-official&period=daily&limit=30"
```

生成报告和回测：

```bash
curl "http://127.0.0.1:8765/reports/stock/600519?source=tongdaxin"
curl -X POST http://127.0.0.1:8765/backtests/600519 \
  -H "Content-Type: application/json" \
  -d '{"source":"tongdaxin","limit":240,"persist":true}'
```

## 测试

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover services/api/tests
```

服务启动后可运行端到端 smoke test：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/smoke_api.py http://127.0.0.1:8765
```

## 核心原则

- 先结构化数据，再让 AI 解释。
- 先规则可回测，再谈智能信号。
- 先风险控制，再谈收益预测。
- 所有信号必须留痕。
- 不自动下单。
