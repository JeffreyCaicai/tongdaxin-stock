# Tongdaxin Stock

个人使用的 A 股持仓与目标股决策支持桌面软件。

本项目定位是“股票驾驶舱 / 决策支持系统”：结构化持仓、目标池和行情数据，通过可审计规则生成买入、卖出、止损、止盈和观察信号，再由 AI 做解释与复盘。它不自动下单，不构成投资建议。

## 当前状态

- 已建立项目骨架。
- 已选择 `Tauri + React` 作为桌面端方向，MVP 先以本地 FastAPI 服务打通数据和规则闭环。
- 已建立 SQLite schema、持仓 CRUD、目标池 CRUD 和基础信号评估入口。
- 已支持持仓/目标池 CSV 导入导出、信号历史查询和工作台批量行动信号生成。
- 数据源暂以本地/模拟输入为主，后续接入 `eltdx`、AkShare 或通达信 Token 路线。

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

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
cp .env.example .env
python scripts/init_db.py
uvicorn services.api.app.main:app --reload --host 127.0.0.1 --port 8765
```

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
- `POST /workbench/actions`

工作台行动信号示例：

```bash
curl -X POST http://127.0.0.1:8765/workbench/actions \
  -H "Content-Type: application/json" \
  -d '{"prices":{"600519":1500,"000001":12.2},"persist":true}'
```

## 测试

```bash
python -m unittest discover services/api/tests
```

## 核心原则

- 先结构化数据，再让 AI 解释。
- 先规则可回测，再谈智能信号。
- 先风险控制，再谈收益预测。
- 所有信号必须留痕。
- 不自动下单。
