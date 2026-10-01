# Chan Validation Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复已支持分钟周期的数据时间链路，并为冻结的日线缠论模型建立可复现、无未来 K 线泄漏的逐根回放与价格观察工具。

**Architecture:** 数据提供器负责联网及认证；独立模块标准化时间、保存固定输入，研究模块仅离线读取快照。现有分析器保持为冻结基线，回放逐个历史时点调用它，事件与后续价格观察分开保存。第一阶段以本地 CLI 和 JSON 交付，不替换当前界面或模型，不增加后台任务。

**Tech Stack:** 现有 Python 3.12 / FastAPI / Pydantic / SQLite，标准库 `datetime`、`zoneinfo`、`json`、`hashlib`、`argparse`，现有 `unittest` 与 Node 前端运行时测试；本阶段不安装新产品依赖。

**Spec:** [已确认设计](../specs/2026-10-01-chan-validation-foundation-design.md)

状态：用户于 2026-10-01 确认 Native 顺序实现。Task 1–6 已完成；独立审查的两项重要问题已用失败回归复现并修复，252项完整测试通过。真实分钟链路及240根日线回放已验收，模型、界面和用户服务保持原样。分支等待用户选择合并或推送。

## Global Constraints

- 稳定基线为 `67a0b99d100de924a9e41a2ef9ee195a6afadcd4`，开发分支为 `codex/chan-validation-foundation`。
- “第一阶段仅回放冻结的日线 `daily_pen_overlap_v2`；分钟线先完成数据验收，不提前混入现有模型。”
- “现有日线 `trade_date=YYYY-MM-DD` 保持兼容，不批量重写日线历史。”
- 新研究入口只接受 `daily`、`5min`、`60min` 及已核查别名；分钟时间统一为带 `+08:00` 的完整时间戳。
- “验证输入使用独立本地 JSON 数据集及清单，存放于 Git 已忽略的 `data/cache/chan_validation/`，不提交到 GitHub。”
- “回放过程中禁止联网、刷新缓存或读取后来改变的市场状态。”
- “本阶段不引入新买卖规则，不调参追求历史胜率，不恢复原来的交易栏或 MA 回测栏目。”
- “未到期为 `pending`，质量失败为 `unavailable`”，缺失值不转为零；20 日为主要周期，5/60 日仅作辅助价格观察。
- 不自动交易，不修改关注、持仓、推荐快照或旧报告，不重启正在使用的服务替换模型。
- 所有研究输出均不含 Token、请求头、Cookie、账户数据；认证只在现有提供器中进行。
- 不运行 `scripts/smoke_api.py` 对接用户服务，该脚本会新增持仓和信号。集成测试使用临时数据库。

## Review Focus

1. 时间戳混合时区、无时区或跨午休：不能把未完成 K 线当完成数据，测试归 Task 1。
2. 重复批次包含冲突价格、旧分钟记录占满查询上限：必须完整检查后再写入，旧格式不挤掉有效结果，测试归 Task 2。
3. 分页重复返回第一页、输入被篡改、输出已存在：有界停止且不覆盖研究证据，测试归 Task 3/6。
4. 未来追加数据改变数据集总哈希、缺数后候选恢复、中枢延伸：不改写旧事件或虚增独立机会，测试归 Task 4。
5. 假期日历范围不足、基准漏日、多个信号重叠：不能凑窗口、伪造零收益或宣称独立胜率，测试归 Task 5。

## 文件与共享契约

| 文件 | 职责 |
| --- | --- |
| 新 `services/api/app/market_time.py` | 周期规范化、官方日期与时间解码、已完成 K 线检查 |
| 改 `market_data.py` / `repository.py` / `schemas.py` / `main.py` | 提供器及分钟缓存、字段输出的最小接线，保留日线兼容 |
| 新 `services/api/app/chan_dataset.py` | 严格数据集格式、质量记录、哈希和不覆盖保存 |
| 新 `services/api/app/chan_capture.py` | 有界历史采集与分页检查，唯一可联网的研究模块 |
| 新 `services/api/app/chan_baseline.py` | 基线指纹检查和历史时点调用适配，不复制重写缠论算法 |
| 新 `services/api/app/chan_replay.py` | 逐根回放、候选去重、追加状态事件 |
| 新 `services/api/app/chan_outcomes.py` | 5/20/60 日价格观察和质量门槛 |
| 新 `scripts/validate_chan.py` | 显式命令入口：`capture`、`replay`、`frame` |
| 新 `services/api/tests/chan_validation_cases.py` | 共享的合成数据集和价格路径；不含真实个人数据 |
| 新 `docs/chan-validation.md`；改 `README.md` | 命令、输出解释及能力边界 |

后文简称 app 文件时，均位于 `services/api/app/`；测试位于 `services/api/tests/`。不改 `static_ui.py`、`backtest.py` 或推荐跟踪模块。

**数据集 `chan_dataset_v1`：** 根字段固定为 `schema_version, dataset_id, created_at, selection, source, as_of, price_basis, calendar, series, issues, collection`。`selection` 含明确证券列表、选择时间及 `selected_sample` 范围；`series[symbol][period]` 含 `bars` 与质量问题。`SH000300` 单独作为基准，不混入选股名单。

**来源门槛：** `price_basis` 保存参数及 `verification={status, reference, evidence_sha256}`，真实采集默认 `unverified`，不能因 `TQFlag=11` 自动变为已验证。`calendar` 保存排序去重的交易日期、完整覆盖起止、来源、版本及相同验证记录。缺少证据元数据的 `verified` 声明拒绝；离线研究并不替用户证明外部证据真实。

**哈希：** 对规范 JSON 使用 `sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False`。数据集总哈希覆盖除 `dataset_id` 外的全部内容。事件的 `data_hash` 只覆盖该事件当时可见的个股前缀与配置，总数据集 ID 放在报告清单中，追加未来数据不得改变旧事件标识。

**质量问题：** 使用结构化 `{code, symbol, period, bar_key, scope}`，`scope` 为 `bar` 或 `series`。能定位时间的问题只在到达该时间后参与历史质量判断；无法定位的损坏阻断该序列，不凭空补时间。剔除未来行必须先于当期价格质量判断。

**结果 `chan_replay_v1`：** 保存 `dataset_id, model_version, baseline_fingerprint, as_of, frames, observations, events, issues`。frames 只存时点、输入前缀哈希、信号、质量和中枢摘要，不重复保存每一帧完整 K 线图；`frame` 命令按快照重新生成指定时点的完整分析及图形数据。

---

### Task 1: 官方分钟时间解析与完成性检查

**Files:** Create `market_time.py`, `test_market_time.py`; modify `market_data.py`, `test_market_data.py`。

**Interfaces:**
- `normalize_period(period: str) -> str`：统一日/周/月及已存在的分钟别名，未知值抛 `ValueError`；研究入口再限制到三种目标周期。
- `decode_tdx_bar_time(row: dict, *, period: str) -> dict`：返回 `trade_date, session_date, bar_end_at, time_semantics`；纯函数，不加载配置或联网。
- `completed_bars(bars: list[dict], *, period: str, as_of: str) -> tuple[list[dict], list[dict]]`：返回按时间排序的已完成规范行及结构化质量问题；不改输入。

- [x] **Step 1: 写失败测试。** 在 `test_market_time.py` 建立以下断言，均使用 `unittest.TestCase`：

```python
def test_seconds_field_preserves_intraday_time(self):
    row = decode_tdx_bar_time({"Item": ["20260930", "54000"]}, period="60min")
    self.assertEqual(row["trade_date"], "2026-09-30T15:00:00+08:00")
    self.assertEqual(row["session_date"], "2026-09-30")
    self.assertEqual(row["bar_end_at"], row["trade_date"])

def test_daily_key_stays_date_only(self):
    row = decode_tdx_bar_time({"Item": ["20260930", "0"]}, period="daily")
    self.assertEqual(row["trade_date"], "2026-09-30")
```

另测 `41400/50400`、`53400/53700`，named `Date/Time` 与数组冲突，缺时刻、布尔值、负秒数、86400、无效日期；60 分钟终点仅接受 10:30/11:30/14:00/15:00，5 分钟为 09:35..11:30、13:05..15:00 的 5 分钟端点。午休、盘前盘后拒绝。`as_of=2026-09-30T06:59:59Z` 排除 15:00 行，07:00:00Z 可纳入；无时区拒绝；未来行即使含 NaN 也不能污染过去的质量状态。冲突重复行不给可用价格。

- [x] **Step 2: 验证红灯。** Run `.venv/bin/python -B -m unittest services.api.tests.test_market_time -v`；新增模块不存在或缺少分钟时间导致失败，不能是 fixture 语法错误。
- [x] **Step 3: 实现以上接口并接入官方提供器。** 同时使用 `Item[0]` 与 `Item[1]`，日期可接受明确的紧凑/ISO 日期；不能从缺失字段猜时分。只给已核查的日线、5/60 分钟输出已验证格式元数据，其他现有周期保持行为且不进入新研究。元数据合并到现有 `payload`，不保存请求头。纯解析错误转换成不含原响应的 `MarketDataError`；数据质量数值检查拒绝 bool/NaN/inf/非正 OHLC，重复一致去重、冲突标错。缺失 volume 保留 None，价格观察阶段再判定可评估性。
- [x] **Step 4: 验证绿灯与兼容。** Run `.venv/bin/python -B -m unittest services.api.tests.test_market_time services.api.tests.test_market_data -v`；全部通过。真实时间语义仍需 Task 6 有界探查，不能仅凭合成测试标为实测。
- [x] **Step 5: 提交。** 只暂存本任务文件，commit message `Fix official intraday bar timestamps and completion checks`。

### Task 2: 分钟缓存与 API 往返不丢时间

**Files:** Modify `repository.py:485`, `main.py:324`, `schemas.py:178`, `test_repository.py`, `test_analysis_integrity.py`; create `test_intraday_kline_api.py`。

**Interfaces:** 消费 Task 1 的规范周期和时间键；保留 `upsert_market_klines(...)`、`list_market_klines(...)` 及原 API 签名。`MarketKlineBarOut` 新增可空 `session_date, bar_end_at, time_semantics`，从缓存 payload 读取；日线原字段不变。

- [x] **Step 1: 写失败测试。** 在临时 SQLite 数据库中写入同日 14:50/14:55/15:00 三根 5 分钟线，断言返回及数据库均为 3 根、重复写仍为 3 根；一次批次内部同时间不同 OHLC 必须抛安全错误且整批不落库。单独的新批次修订既有行可更新缓存，但原研究快照不得改变。直接用 SQL 放入旧的日期级分钟行，`list_market_klines(limit=3)` 仍得到 3 根有效分钟行，旧行保留。

```python
def test_three_intraday_rows_survive_roundtrip(self):
    stamps = [f"2026-09-30T{clock}:00+08:00" for clock in ("14:50", "14:55", "15:00")]
    bars = [dict(trade_date=s, open=10, high=11, low=9, close=10) for s in stamps]
    rows = upsert_market_klines(self.connection, symbol="600519", source="tdx-official", period="5min", bars=bars)
    self.assertEqual({row["trade_date"] for row in rows}, set(stamps))
```

`test_intraday_kline_api.py` 用临时依赖及 mock provider 经 TestClient 请求 `/market/kline/600519?source=tdx-official&period=60m`；断言规范输出 `60min`，时区和附加字段保留，`count` 与有效返回数量一致。再测旧 `/market/klines/...` 路由、日线原结果、同批返回范围与较新缓存隔离。预先保存关注/持仓/报告，断言内容未变化。

- [x] **Step 2: 验证红灯。** Run `.venv/bin/python -B -m unittest services.api.tests.test_intraday_kline_api services.api.tests.test_repository services.api.tests.test_analysis_integrity -v`；新时间及完整性断言失败，既有测试仍正常。
- [x] **Step 3: 接线。** 请求、读缓存、写缓存统一周期；先验证整个传入批次再写数据库，错误不留下部分数据。分钟查询在 LIMIT 前排除旧日期级键；返回仍仅为本次响应集合。`_fetch_kline_and_cache` 只做调用与输出转换，不新增分析规则，不清理旧数据、不重建表。
- [x] **Step 4: 验证绿灯。** 重跑 Step 2 全部命令及 `test_stock_pool_market_api`，确保空响应仍失败、日线响应保持一致。
- [x] **Step 5: 提交。** commit message `Preserve intraday identity through cache and API`。

### Task 3: 有界采集与不可覆盖的数据集

**Files:** Create `chan_dataset.py`, `chan_capture.py`, `test_chan_dataset.py`, `test_chan_capture.py`, `chan_validation_cases.py`; modify `market_data.py`, `test_market_data.py`。

**Interfaces:**
- 官方提供器增加 `fetch_kline_page(symbol: str, *, period: str, limit: int, start: int) -> list[dict]`；原 `fetch_kline` 用 start=0，空页仍按既有调用契约报错。研究分页在响应成功且 ListItem 为合法空数组时可返回 `[]`，服务错误不能伪装为历史结束。
- `capture_dataset(*, symbols: list[str], periods: list[str], as_of: str, page_size: int = 1000, max_pages: int = 1, calendar: dict | None = None) -> dict`：返回固定格式，数据提供器只在调用内部延迟导入。
- `validate_dataset(dataset: dict) -> None`, `save_dataset(dataset: dict, root: Path) -> Path`, `load_dataset(path: Path) -> dict`：校验、排他保存、验证总哈希；模块本身不导入 config/main/market_data。
- 共享 fixture `make_dataset(*, series: dict, sessions: list[str], as_of: str, calendar_verified: bool = True, basis_verified: bool = True) -> dict`，只生成标明 `synthetic` 的可验证测试数据，真实采集不能调用它提升权限或可信状态。

- [x] **Step 1: 写失败测试。** 断言规范快照保存后可精确读回；改动 close 而不改 ID 导致 `ValueError("dataset_hash_mismatch")`；拒绝 NaN、未知根字段、伪造 verified 缺证据元数据；相同内容重复保存返回同一路径、不覆盖；不同内容同 ID 拒绝。只允许列白名单，provider 额外返回 `token`/`headers`/`raw` 不进入文件或错误。

测试 setUp 用 `make_dataset` 构造 `self.dataset`，使用 TemporaryDirectory 的 `self.root`：

```python
def test_dataset_is_immutable_and_verified(self):
    path = save_dataset(self.dataset, self.root)
    self.assertEqual(load_dataset(path), self.dataset)
    self.assertEqual(save_dataset(self.dataset, self.root), path)
    changed = copy.deepcopy(self.dataset)
    changed["created_at"] = "2026-10-02T00:00:00+08:00"
    with self.assertRaisesRegex(ValueError, "dataset_hash_mismatch"):
        validate_dataset(changed)
```

采集 mock 三页，断言 offsets 为 0/N/2N、价格和顺序准确；重复第一页触发 `pagination_not_advancing` 并停止；跨页相同边界可去重、冲突价格记录问题。页数上限输出 `truncated`，部分失败保留已取得范围及失败原因，不返回 success-complete。无 calendar 时记录 unverified 而非从指数猜完整日历；`TQFlag=11` 仍为 unverified price_basis。测试股票别名去重，`000300` 不自动当沪深300，基准始终 `SH000300`。

- [x] **Step 2: 验证红灯。** Run `.venv/bin/python -B -m unittest services.api.tests.test_chan_dataset services.api.tests.test_chan_capture -v`。
- [x] **Step 3: 实现。** 第一阶段默认只采一页，最多 10 只明确指定股票，加一个基准；每页 1..1000 根、每序列最多 5 页，串行、页间至少 0.5 秒，保持现有 15 秒网络超时，不无限重试。进入下一页必须确认返回区间向过去推进，并按完成性规则检查跨页缺口。请求参数、偏移、时间、实际范围和限制入清单；不能用 HTTP 成功推断 history_complete。selection 的选择时间记录实际采集时间，不把用户传入的历史 as_of 当作当年已经选定该股票的证明。

保存路径为 `root/<dataset_id>/dataset.json`，使用排他创建及临时文件完成后落盘，目录只使用计算出的十六进制 ID；不依赖输入提供的相对路径。输入文件上限 50 MiB，读入前检查，JSON 非有限数拒绝；截断文件安全失败。旧文件保持不变。快照白名单丢弃非数据字段，错误只输出有界分类。created_at/as_of 必须带时区；是否 point-in-time 已核实与抓取时间分开记录。

- [x] **Step 4: 验证绿灯。** 重跑 Step 2、Task 1/2 回归，额外确认 `.gitignore` 会忽略 `data/cache/chan_validation/` 下文件。真实分页能力尚需 Task 6 探查，无法通过时保留单页模式并报告缺口。
- [x] **Step 5: 提交。** commit message `Add bounded capture and immutable Chan research datasets`。

### Task 4: 冻结模型与逐根事件回放

**Files:** Create `chan_baseline.py`, `chan_replay.py`, `test_chan_replay.py`, `test_chan_baseline.py`; extend `chan_validation_cases.py`。不修改 `chan_analysis.py`、`opportunity_prices.py`。

**Interfaces:**
- `baseline_fingerprint() -> str`：验证模型版本及固定源指纹，不符抛 `baseline_mismatch`。
- `analyze_frame(*, symbol: str, bars: list[dict], as_of: str) -> dict`：只把截止时刻以前的日线前缀交给冻结的 `analyze_chan_structure`，返回原分析含图形数据。
- `replay_symbol(*, symbol: str, bars: list[dict], as_of: str, quality_issues: list[dict], analyzer: Callable[..., dict] | None = None) -> dict`：返回 frames/observations/events/issues；测试可注入受控 analyzer，生产使用冻结适配器。窗口最少 35 根，日期须严格递增；不足时返回 insufficient_bars 而非虚假候选。

- [x] **Step 1: 写失败测试。** 实际 `zigzag_bars()` 每个前缀回放与 `analyze_chan_structure(..., as_of=该日15:00+08:00)` 的结构和信号一致；该 fixture 只测算法，不当交易日历。追加已知未来极端上涨/下跌及远端无效 OHLC，不改变追加日前的 frames 和已发出 events。传入无时区 as_of 拒绝。修改基线指纹会停止回放，不能默默继续。

```python
def test_frame_matches_original_model_at_same_cutoff(self):
    bars, cutoff = zigzag_bars(), "2026-02-10T15:00:00+08:00"
    actual = analyze_frame(symbol="600519", bars=bars, as_of=cutoff)
    expected = analyze_chan_structure(symbol="600519", bars=bars, as_of=cutoff)
    self.assertEqual(actual, expected)
```

用共享 fixture 的可控 frames 测状态：同候选连续 3 天只创建 1 个 observation；中枢 end_date 延长、upper 改变仍保留首次冻结边界；buy 首次 upper=12，后续 close=12 产生 invalidated，high/low 触及但 close=12.5 仅 risk flag；sell 的 lower 对称。数据缺失产生 data_unavailable，恢复原候选不新增；有效数据下候选消失产生 withdrawn，不等同失效。候选之后再次出现须经过有效非候选帧才允许新 episode，标明与旧窗口重叠。旧候选规则不能生成 rule_confirmed。

防未来泄漏测试必须有非空 candidate 事件断言，不能靠两组空列表相等通过；用至少一组真实分析器可产生候选的合成路径，另以受控 analyzer 精确覆盖状态转换。

- [x] **Step 2: 验证红灯。** Run `.venv/bin/python -B -m unittest services.api.tests.test_chan_baseline services.api.tests.test_chan_replay -v`。
- [x] **Step 3: 实现冻结适配与回放。** 固定以下当前源 SHA256，另固定 `repository.normalize_symbol` 的函数源码指纹，避免 Task 2 修改 repository 的其他函数使基线失效：
  - `chan_analysis.py`: `88723b84f88667db5d3a8b903c612fa6fec211f1b15c814e6f2e7e2a9984e332`
  - `opportunity_prices.py`: `23c896ab207fa31bf3b68d5b9db1637da13175b3b25a77b090fff82f5fbcf2a5`

`as_of` 始终显式传入，不依赖 utc_now。逐个完成日仅传入当前前缀；问题按 bar_key 限定其首次可见位置。未知时间的损坏阻断序列，不能用未来有利数据修复过去。序列在 35 根以后每根生成一个摘要 frame，未形成结构正常输出 observation 状态。

候选 anchor 取中枢最初三条稳定笔的方向和端点日期，不包含后来变动的边界或 end_date；模型、证券、方向、anchor、episode 首次时间共同生成 observation_id。事件 ID 再加入事件时刻和类型；event.data_hash 使用该时点规范前缀。只在状态变化时追加事件，首次 candidate 的快照永不修改。已失效 episode 终止；withdrawn 后保留原失效边界跟踪，重新出现的 episode 单独标识；缺数不构成重新武装条件。每个 observation 单独保存 evidence、first_seen_at、pivot_at、confirmed_at=null、frozen_boundary 与 invalidation_mode=close。

- [x] **Step 4: 验证绿灯。** 重跑 Step 2 与现有 `test_chan_analysis`、`test_chan_market_integrity`；两次同快照运行 events 内容完全一致。总数据集 hash 改变不导致历史事件 ID 改变，旧快照文件 hash 保持不变。
- [x] **Step 5: 提交。** commit message `Add causal Chan baseline replay and append-only observations`。

### Task 5: 独立日期对齐的价格观察

**Files:** Create `chan_outcomes.py`, `test_chan_outcomes.py`; extend `chan_validation_cases.py`。

**Interfaces:** `evaluate_observations(*, observations: list[dict], dataset: dict, as_of: str) -> dict`，固定 horizons=(5,20,60)，primary_horizon=20。输出 `items`（每项含 observation_id、symbol、direction、按字符串周期索引的 outcomes）、`summary`（周期及方向分组）、`method`、`issues`；只读输入，不调用提供器、旧推荐跟踪或数据库。

- [x] **Step 1: 写失败测试。** 已核实的合成日历中，candidate 当日收盘10，下一交易日 open=12，第5交易日 close=15，价格收益应为25%，不是50%；同期指数100到110，超额为15个百分点。跌向候选也返回真实价格涨跌，不反号作做空利润。五日路径中价格峰值15跌至12，收盘路径回撤为-20%。

测试 setUp 用 `make_dataset` 固定上述价格路径、日历及 `first_seen_at`，提供 `self.observations, self.dataset, self.as_of`：

```python
def test_returns_start_after_signal_was_observable(self):
    result = evaluate_observations(observations=self.observations, dataset=self.dataset, as_of=self.as_of)
    outcome = result["items"][0]["outcomes"]["5"]
    self.assertEqual(outcome["status"], "matured")
    self.assertAlmostEqual(outcome["return_pct"], 25.0)
    self.assertAlmostEqual(outcome["excess_pp"], 15.0)
```

少于5日且截至 as_of 的应有数据完整为 pending；已经过去但缺任何一日个股或基准为 unavailable，不顺延日期。calendar 未验证、范围不足或 basis 未验证分别返回明确 issue 和 None 数值。匹配日零/负/缺成交量不得成熟；基准在日历之外有成交也报告冲突。追加未来行不改变较早 as_of 的观察结果。成熟结果按观察方向分组；重复 observation_id 拒绝或去重为1，重叠日期标记关联，不产生 win_rate/probability 字段。

- [x] **Step 2: 验证红灯。** Run `.venv/bin/python -B -m unittest services.api.tests.test_chan_outcomes -v`。
- [x] **Step 3: 实现。** 先验证日历证据及覆盖，再验证指数每个期待日期，然后个股；用 `first_seen_at` 对应上海日期之后的日历日切精确窗口，所有端点不得晚于 as_of。计算 `(end_close / next_session_open - 1)*100`、同窗口基准差及 `[entry_open, daily_closes...]` 的逐步峰值回撤。

结果逐个 observation 保存每周期的 status、issue、起终日期、基准日期、价格、收益、超额和回撤；汇总分别计 total/matured/pending/unavailable，均值只纳入 matured，无成熟样本均值为 None。输出 `selected_sample, overlapping_samples_not_independent, execution_costs_included=false, tradeability_checked=false, dividends_included=false`；不能因为输出了费用免责声明就把未核实复权放行。失效/withdrawn 事件不删除候选原来的固定期观察，避免幸存者筛选。
- [x] **Step 4: 验证绿灯。** 重跑 Step 2、`test_opportunity_tracking`，确认原推荐观察不受影响。
- [x] **Step 5: 提交。** commit message `Evaluate Chan observations on fixed aligned trading windows`。

### Task 6: 研究命令、完整回归与真实有界验收

**Files:** Create `scripts/validate_chan.py`, `test_chan_validation_cli.py`, `docs/chan-validation.md`; modify `README.md`。

**Interfaces:** `main(argv: list[str] | None = None) -> int`；commands 为 `capture --symbols ... --periods ... --as-of ... --root ... [--calendar ... --max-pages N]`、`replay --dataset ... --as-of ... --output ...`、`frame --dataset ... --symbol ... --as-of ... --output ...`。capture 默认 root 为已忽略目录，其他命令必须显式给 output；输出存在拒绝，不提供静默覆盖开关。正常产物返回0（允许 pending/unavailable），参数或数据契约错误返回2，采集或文件 IO 失败返回1；采集部分失败可保留质量标记的快照，但返回1并显示未完成范围，不冒充完整成功。

- [x] **Step 1: 写失败测试。** TemporaryDirectory 内以 `main(argv)` 做依赖 mock 集成，网络和 `sqlite3.connect` 被拦截时 replay/frame 仍成功，capture 的 fake provider 参数和输出正确；再以 subprocess 验证实际命令入口及退出码，父进程 mock 不得当作已拦截子进程。缺参数、非法周期、文件篡改、输出已存在、输入输出同路径、非有限JSON、超过50MiB 输入安全失败；stderr 不含 fake credential。提供无候选快照成功返回空事件而非抛异常；不足35根明确返回问题，无伪造信号。

测试先保存合成的 `self.dataset_path`，`self.output` 指向临时目录中不存在的新文件：

```python
def test_replay_does_not_connect_to_network_or_database(self):
    with mock.patch("socket.socket.connect", side_effect=AssertionError("network")), \
         mock.patch("sqlite3.connect", side_effect=AssertionError("database")):
        self.assertEqual(main(["replay", "--dataset", str(self.dataset_path),
                               "--as-of", self.as_of, "--output", str(self.output)]), 0)
    self.assertTrue(self.output.is_file())
```

读取临时 personal.db 的字节哈希前后相同；patch 配置加载为失败确保 replay/frame 不读 `.env`；CLI 顶层不得导入 main、config 或 capture。replay 按明确 selection 逐股调用 Task 4/5，frame 返回指定证券时点的原分析图形数据，证券不在快照中拒绝。产物总清单链接 dataset_id，模型及配置指纹一致。

- [x] **Step 2: 验证红灯。** Run `.venv/bin/python -B -m unittest services.api.tests.test_chan_validation_cli -v`。
- [x] **Step 3: 实现 CLI 与文档。** 只在 capture 子命令内部导入认证链路；新报告排他写入并使用规范 JSON，无模糊的成功提示。文档给出一页有界采集、离线 replay、指定 frame 的可直接执行命令，区分已实测、未验证、模拟数据、第一阶段不提升模型本身；说明缺日历/复权证据时可以回放结构但不能宣称有效价格统计。校验所有路径，不安装新的框架。
- [x] **Step 4: 完整回归。** Run `.venv/bin/python -B -m unittest discover services/api/tests` 和 `git diff --check`；必须全部通过，不能只引用基线曾经通过的200项。检查 diff 仅含本计划列明的实现、测试和文档，`git status` 无密钥/数据库/真实行情产物；运行 `git check-ignore data/cache/chan_validation/probe/dataset.json` 应确认被忽略。
- [x] **Step 5: 真实只读验收。** 明确指定单只600519和SH000300，每次最多两页、每页12根，核查5/60分钟时间端点、跨页前进、同日多行及日期对齐；用临时数据库做 API 往返，不调用用户8766上的写接口。没有受信时间口径资料时保留 time_semantics 的未核实标记，不启用确认。随后单只采集一页240根日线为真实研究快照，用固定截止日离线回放，保存观察/质量报告，原持仓和报告不变。

网络、权限或上游失败时记录分类和已验证范围，不循环重试、不换源、不把合成通过当成真实验收。日历或复权未核实导致 unavailable 是预期安全结果；不得为了产出统计绕过门槛。分钟不足35根不拿来做缠论分析，分钟数据本阶段只验时间链路。阶段报告明确本次实际测试数、实际拉取数量、模型未更换、独立 review 是否完成。

- [x] **Step 6: 提交交付。** commit message `Expose offline Chan validation commands and document research limits`。在合并、推送新产品代码或更新用户服务前呈现分支差异与验证结果；保留原基线。按选定执行方式安排独立代码审查，修复后重新跑相关及全量测试。

## 自查与执行交接

设计第4节对应 Task 1/2/3，第5节对应 Task 3，第6节对应 Task 4，第7节对应 Task 5/6；全部九项验收映射到上述明确测试及真实探查。第二、三阶段完整引擎、过滤调参、成本与可成交模拟、样本外比较不在本实现计划内。

本轮按用户批准的 Native 方式顺序完成：每步红灯、绿灯和提交，最终独立审查整个分支，并完成一次回归修复。真实验收和研究限制见 [离线验证工具](../../chan-validation.md)。继续第二、三阶段或发布本轮实现须另行确认。
