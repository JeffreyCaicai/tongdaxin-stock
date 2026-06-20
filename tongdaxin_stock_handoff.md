# Handoff: Tongdaxin Stock Personal Decision App

生成日期：2026-06-20  
目标项目名：`tongdaxin stock`  
用途：个人使用的 A 股持仓与目标股决策支持桌面软件  
重要边界：仅用于个人投研和风险管理，不作为收费产品，不自动下单，不构成投资建议。

## 1. 项目愿景

构建一个桌面级股票决策软件，把通达信相关 MCP / Skills / 数据接口接入本地系统，用于管理个人持仓和目标股票池。

软件的核心目标不是“预测未来”，而是：

- 把持仓和目标股的关键数据自动拉取并结构化。
- 根据可审计、可回测的规则生成买入、卖出、止损、止盈、观察信号。
- 用 LLM 做解释、复盘、冲突检查和报告生成。
- 让用户每天/盘中看到“哪些股票需要行动，为什么，需要等什么确认”。

产品定位应是“股票驾驶舱 / 决策支持系统”，不是全自动交易系统。

## 2. 已调研结论

通达信生态中已经出现与 AI / MCP / Skills 相关的官方与社区线索：

- 通达信官网公开入口包括：问小达AI、智能体广场、通达信MCP、TdxClaw、Skills广场。
- TDX SkillHub 是通达信公开的股票分析与研究技能中心。
- SkillHub 当前公开技能元数据约 46 个，其中大量为 TdxClaw 内置技能；公开可安装技能包括 `tdx-quant-python`、`tdx-quant-local`。
- 社区已有多个可用于本项目的 MCP / 数据封装项目。

关键参考：

- 通达信官网：https://www.tdx.com.cn/
- TdxClaw：https://www.tdx.com.cn/tdxclaw/
- TDX SkillHub：https://www.tdx.com.cn/skillhub/
- TdxQuant 帮助：https://help.tdx.com.cn/quant/
- MCP 简介：https://modelcontextprotocol.io/docs/getting-started/intro
- MCP Tools 规范：https://modelcontextprotocol.io/specification/2025-06-18/server/tools

## 3. 候选数据/MCP路线

### 3.1 官方 Token / OpenClaw 插件路线

代表项目：

- https://github.com/adambbhe/TDX-finance-mcp-plugin-v3

特点：

- 声明包含 6 个核心工具 + 45 个投资分析 Skills。
- 工具包括：
  - `tdx_api_data`
  - `tdx_quotes`
  - `tdx_kline`
  - `tdx_lookup_stock`
  - `tdx_screener`
  - `tdx_indicator_select`
- 覆盖 A 股实时行情、K 线、F10 基本面、智能选股、指标筛选、代码检索。
- 需要 Node.js >= 22.16.0、OpenClaw、TDX API Token。
- 部分 F10 子模块依赖更高权限 Token。

适合：后续若能获得通达信数据服务 Token，可以作为核心数据能力。

### 3.2 Python 通达信协议 MCP 路线

代表项目：

- https://github.com/electkismet/eltdx

特点：

- Python 包，支持通达信 7709 行情与 7615 F10。
- 提供 MCP stdio 服务。
- 工具包括行情快照、K 线、股票概况、题材、F10 公司概况、热点题材、09:25 集合竞价快照等。
- 安装示例：

```bash
pip install "eltdx[mcp]"
eltdx-mcp
```

适合：MVP 阶段优先验证，门槛较低。

### 3.3 本地 TdxQuant 封装路线

代表项目：

- https://github.com/lingfan/tdxquant-mcp

特点：

- 基于本地 `tqcenter.py` / TdxQuant / 通达信策略接口。
- 支持行情、财务、板块、公式、交易日历、交易接口等。
- 需要本地通达信/TdxQuant 环境、`TQ_PATH`、相关 DLL/客户端配置。
- 有交易接口，但必须保持 dry-run 和人工确认。

适合：如果本地已跑通 TdxQuant，则长期潜力最大。

### 3.4 通达信行情工具箱路线

代表项目：

- https://github.com/845340126/tdx_mcp

特点：

- 基于通达信公开行情服务器。
- 支持 A 股、扩展行情、K线、分时、排行榜、异动监控、F10、技术指标。
- 偏行情和指标工具箱。

适合：补充行情和技术指标能力。

### 3.5 浏览器表格查询路线

代表项目：

- https://github.com/wukan1986/mcp_query_table

特点：

- 基于 Playwright，可查同花顺问财、通达信问小达、东方财富条件选股。
- 更像“所见即所得”的网页表格抓取。
- 速度较慢，依赖浏览器状态和网站页面结构。

适合：自然语言选股/板块筛选的备用方案。

### 3.6 非通达信备选数据源

可作为备援或交叉验证：

- AkShare MCP:
  - https://github.com/zwldarren/akshare-one-mcp
  - https://github.com/aahl/mcp-aktools
  - https://github.com/ccq1/cn-financial-mcp
- Tushare MCP:
  - https://github.com/guangxiangdebizi/FinanceMCP

建议：不要只依赖单一数据源。至少保留 AkShare / Tushare / 东方财富类数据作为校验和兜底。

## 4. MVP 范围建议

第一阶段只做“个人持仓 + 目标池 + 每日信号”，不要一开始做自动交易或复杂多 Agent。

### 4.1 持仓管理

字段：

- 股票代码
- 股票名称
- 市场：SH/SZ/BJ/HK/US，MVP 优先 A 股
- 持仓数量
- 成本价
- 当前价
- 初始买入理由
- 计划止损价
- 计划止盈价
- 最大可承受亏损
- 当前策略：短线/波段/中线/长线
- 备注

### 4.2 目标股池

字段：

- 股票代码
- 股票名称
- 关注理由
- 计划买入区间
- 触发条件
- 失效条件
- 优先级
- 观察状态：等待、接近买点、触发买点、放弃

### 4.3 数据更新

每日/盘中拉取：

- 实时行情
- K线
- 成交量/成交额
- 涨跌幅/换手率
- 板块/题材
- F10 基本面
- 财务摘要
- 股东/机构/北向/资金，如权限允许
- 公告/事件，如可用

### 4.4 信号输出

对每只持仓股输出：

- 当前状态：持有、减仓、止盈、止损、观察
- 风险等级：低、中、高
- 关键价位：止损位、压力位、目标位、趋势失效位
- 原因说明：数据驱动，不允许只给结论
- 下一步动作：等待什么确认，触发什么提醒

对每只目标股输出：

- 是否接近买点
- 建议买入区间
- 突破买入条件
- 回踩买入条件
- 放弃条件
- 风险收益比

## 5. 推荐系统架构

建议使用桌面应用 + 本地服务 + 本地数据库。

### 5.1 桌面端

候选：

- Tauri + React：体积小、桌面体验好。
- Electron + React：生态成熟，但体积更大。

建议优先 Tauri，除非需要大量 Node 桌面生态能力。

### 5.2 本地服务

建议：

- Python FastAPI 作为本地分析服务。
- MCP Server 作为数据接入适配层。
- 前端通过 HTTP 调用本地 API。

### 5.3 数据库

建议：

- SQLite：持仓、配置、信号、日志、用户计划。
- DuckDB：后续用于行情历史、回测、批量分析。

### 5.4 分析层

建议 Python：

- `pandas` 或 `polars`
- 技术指标计算模块
- 规则引擎
- 回测模块
- 信号评分模块

### 5.5 AI 层

LLM 只做：

- 总结
- 解释
- 生成交易计划文本
- 检查信号冲突
- 做每日复盘
- 根据 Skills 风格生成结构化研究报告

LLM 不直接做：

- 自动下单
- 无规则约束的买卖决定
- 无数据引用的目标价判断

## 6. 信号引擎设计原则

信号必须可解释、可回测、可审计。

### 6.1 买入信号

至少组合以下条件：

- 价格进入计划区间，或突破关键位。
- 大盘环境不明显恶化。
- 所属板块强度不弱。
- K线趋势未破坏。
- 成交量结构支持。
- 风险收益比合格，例如潜在亏损 1，对应潜在收益至少 2。
- 基本面/公告/题材没有明显负面变化。

买入信号类型：

- 回踩买入
- 突破买入
- 低吸观察
- 趋势确认
- 禁止买入

### 6.2 卖出信号

分类：

- 硬止损：跌破计划止损价或趋势失效位。
- 趋势止盈：上涨后跌破移动止盈线。
- 目标止盈：触达目标价/估值区间。
- 风险卖出：公告、业绩、资金、龙虎榜、题材恶化。
- 仓位调整：单票过重、组合相关性过高。

### 6.3 信号评分

建议每只股票给出多维评分：

- 趋势分
- 量价分
- 板块/题材分
- 基本面分
- 资金分
- 风险分
- 综合行动等级

行动等级示例：

- A：可执行
- B：接近触发，继续观察
- C：无优势，等待
- D：风险升高
- E：退出/放弃

## 7. UI 初步设想

首屏不做营销页，直接是工作台。

### 7.1 工作台

- 今日需要关注的股票
- 持仓风险排行
- 触发买点的目标股
- 触发卖点/减仓点的持仓股
- 大盘/板块状态摘要

### 7.2 持仓页

表格列：

- 股票
- 成本
- 当前价
- 盈亏
- 当前信号
- 止损位
- 目标位
- 风险等级
- 下一触发条件

### 7.3 个股详情页

模块：

- 价格/K线图
- 当前交易计划
- 数据摘要
- 信号解释
- 风险清单
- 历史信号记录
- AI 研究报告

### 7.4 目标池页

模块：

- 待买股票列表
- 买点接近程度
- 买入区间
- 触发条件
- 失效条件

### 7.5 复盘页

模块：

- 今日信号变化
- 昨日计划是否兑现
- 错误信号归因
- 下一交易日观察重点

## 8. 安全与合规边界

用户已明确仅个人使用、风险自担。但工程上仍建议：

- 不做自动下单。
- 不接券商交易接口，至少 MVP 不接。
- 所有“买入/卖出”都表述为“信号/计划/条件”，并保留用户确认。
- 真实 Token 不进入 Git。
- Token 只保存在本地加密配置或系统钥匙串。
- 对 MCP 工具调用做白名单。
- 对工具输出做结构化校验和异常处理。
- 保留每次数据拉取、信号生成、AI 分析的日志。

MCP 规范本身也建议敏感操作保持 human-in-the-loop，并要求工具输入校验、访问控制、限流、输出净化、超时和审计日志。

## 9. 建议的项目目录

```text
tongdaxin stock/
├── apps/
│   └── desktop/              # Tauri/Electron + React
├── services/
│   ├── api/                  # FastAPI 本地服务
│   ├── mcp-adapters/          # 通达信/akshare/tushare MCP 适配
│   └── analysis/              # 信号、指标、回测
├── packages/
│   ├── shared/                # 类型、schema、工具函数
│   └── strategy-core/         # 策略规则核心
├── data/
│   ├── local.db               # SQLite，本地生成，不提交
│   └── cache/                 # 数据缓存，不提交
├── docs/
│   ├── handoff.md
│   ├── architecture.md
│   ├── data_sources.md
│   ├── signal_engine.md
│   └── roadmap.md
├── scripts/
├── .env.example
├── README.md
└── .gitignore
```

## 10. 第一批开发任务

### Milestone 1: 项目骨架

- 初始化仓库。
- 建立 README、docs、.env.example。
- 选择 Tauri 或 Electron。
- 建立本地 FastAPI 服务。
- 建立 SQLite schema。

### Milestone 2: 持仓与目标池

- 实现持仓 CRUD。
- 实现目标股 CRUD。
- 导入/导出 CSV。
- 本地持久化。

### Milestone 3: 数据接入 PoC

- 优先接 `eltdx` 或一个 AkShare MCP。
- 能拉取单股行情和 K 线。
- 写入本地缓存。
- 记录数据源、更新时间、错误状态。

### Milestone 4: 第一版信号引擎

- 实现基础指标：
  - MA5/10/20/60
  - MACD
  - RSI
  - ATR
  - 成交量均线
- 实现简单买入/卖出规则：
  - 跌破止损位
  - 突破压力位
  - 回踩均线确认
  - 放量突破
  - 趋势破坏
- 输出结构化信号 JSON。

### Milestone 5: AI 解释层

- 输入结构化数据和信号。
- 输出个股诊断报告。
- 输出交易计划。
- 输出每日复盘。
- 要求报告必须引用数据，不允许空泛结论。

### Milestone 6: 回测与复盘

- 对信号规则做历史回测。
- 保存每次信号。
- 复盘信号是否有效。
- 统计胜率、盈亏比、最大回撤。

## 11. 推荐第一版数据结构

### holdings

```sql
CREATE TABLE holdings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  name TEXT,
  market TEXT,
  quantity REAL NOT NULL DEFAULT 0,
  cost_price REAL NOT NULL,
  strategy_horizon TEXT DEFAULT 'swing',
  initial_thesis TEXT,
  stop_loss REAL,
  take_profit REAL,
  max_loss_pct REAL,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

### watchlist

```sql
CREATE TABLE watchlist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  name TEXT,
  market TEXT,
  thesis TEXT,
  buy_zone_low REAL,
  buy_zone_high REAL,
  trigger_condition TEXT,
  invalidation_condition TEXT,
  priority INTEGER DEFAULT 3,
  status TEXT DEFAULT 'watching',
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

### signals

```sql
CREATE TABLE signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  action TEXT NOT NULL,
  strength REAL,
  price REAL,
  reason_json TEXT,
  source_snapshot_id INTEGER,
  created_at TEXT NOT NULL
);
```

### market_snapshots

```sql
CREATE TABLE market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  source TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  fetched_at TEXT NOT NULL
);
```

## 12. 给后续 Codex 的开发提示

后续在 `tongdaxin stock` 项目中继续开发时，建议先做一个极小可用闭环：

1. 手动录入 1-3 只持仓和 1-3 只目标股。
2. 用一个可用数据源拉取行情和 K 线。
3. 生成最简单的止损/止盈/趋势信号。
4. 在桌面 UI 上展示“今日要看什么”。
5. 再逐步加入通达信 F10、题材、资金、龙虎榜、公告、AI 报告。

最重要的工程原则：

- 先结构化数据，再让 AI 解释。
- 先规则可回测，再谈智能信号。
- 先风险控制，再谈收益预测。
- 所有信号必须留痕。
- 不自动下单。

