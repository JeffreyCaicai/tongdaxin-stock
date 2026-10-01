# Tongdaxin Stock

个人使用的 A 股持仓与目标股决策支持桌面软件。

本项目定位是个人股票分析与决策支持工作台：围绕关注股和持仓，展示行情、浮动盈亏、缠论结构和多证据情景分析。它不执行交易，不构成投资建议。

## 当前状态

- 工作台导航分为“市场机会 / 我的股票 / 分析记录”。添加关注默认折叠，左栏可搜索和选择股票；“我的股票”中保留决策、缠论、行情、持仓编辑和关注管理。
- 决策页优先展示股票结论及主要证据，可按上涨/震荡/下跌情景筛选并展开明细；模型信息折叠。切换视图不重新分析，本次会话内保留各视图结果；切换行情源会清空视图缓存。打开页面优先读取同池同源的已保存决策报告，不自动重新计算。
- 已新增“市场机会推荐”：通达信条件选股发现池外候选，合并个人关注与持仓，用资产独立评分生成最多10只研究名单。可查看支持/反对证据、确认参考、全部落选原因，手动加入关注；后台进度可取消，历史结果可重看。
- 市场机会新增独立的5/20/60/120交易日技术评价，原版20日名单保持不变。每个周期保留当时的依据、数据截止日期、确认与复核参考；长期栏因缺少经验证的财务/估值证据暂不作参与判断。
- 推荐记录支持按需更新后续表现：入选、未入选及数据排除组全部保留，按5/20/60/120交易日观察涨跌、相对沪深300超额和收盘回撤。旧记录不会补造分周期预测，未到期和数据缺失不进入有效样本分母。
- 首次实测完成40只池外候选与9只个人股票的分析。候选来自三组有限分页条件，页面显示覆盖范围；当前并非全市场穷举，也未接入财务/行业/事件判断。详见 [设计说明](docs/superpowers/specs/2026-10-01-market-opportunities-design.md)。
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

### 查看市场推荐

启动本地服务后，选择“通达信官方 Token”，进入“市场机会”，点击“更新分析”。完成后切换“推荐名单 / 全部评价”或按“新发现 / 已关注 / 已持仓”筛选。“分析记录 → 推荐记录 → 读取记录”可以重新打开之前保存的结果。

新接口：`POST /stock-pools/{id}/opportunities`、`GET /stock-pools/{id}/opportunities`、`GET /opportunities/{run_id}`、`DELETE /opportunities/{run_id}`。扫描参数默认 `source=tdx-official, outside_limit=40`。其他真实行情源暂不支持市场候选发现；`mock` 为测试演示。

任务运行于单进程本地服务；重启后未完成任务标记中断。请求使用现有本地凭证，不写入扫描记录。

### 推荐周期与表现跟踪

“市场机会”可切换“原版20日名单 / 短线5日 / 波段20日 / 中期60日 / 中期120日 / 长期”。新周期使用独立的均线、对齐日期的超额收益、成交量和风险检查分，而不是把原来的20日情景概率改个标签。原版与新周期分开保留版本；分数均未经收益概率校准。

在“分析记录”的已完成扫描中点击“查看后续表现”，再点击“更新表现”拉取后续行情。打开记录本身不产生行情请求。后台更新可取消；只写入 `opportunity_followups`，不修改推荐快照、关注股或持仓。

- `GET /opportunities/{run_id}/followup`：只读已保存的更新状态和结果。
- `POST /opportunities/{run_id}/followup`：启动一次后台更新；返回202。
- `DELETE /opportunities/{run_id}/followup`：请求取消更新。

计算起点为推荐时间转换为上海日期后的下一指数交易日开盘，终点为第N个交易日收盘。个股和指数必须使用完全相同的日期；起终价格来自本次同一批 `TQFlag=11` 日线，不与当时的实时价格混算。当天未收盘日线不参与。历史最多拉取1000根，无法覆盖推荐日的记录明确不可评估；股票缺日、零成交量或无效价格不填零、不向前凑窗口。交易日历依赖沪深300返回数据，接口缺漏仍是数据质量风险。

这是价格表现观察，不是交易回测：未模拟费用、滑点、涨跌停成交约束，也未单独核算现金分红。各组统计只纳入成熟有效样本；多次扫描和多周期可能重叠，不能把样本数量当成独立试验，更不能把正收益占比直接称为未来胜率。规则详见 [周期与跟踪口径](docs/opportunity-horizons-and-followup.md)。

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

缠论结构与行情概况的价格、时间、候选及数据质量口径见 [模块说明](docs/chan-and-market-overview.md)。

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
