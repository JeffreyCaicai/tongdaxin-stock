# 缠论离线验证工具

这是第一阶段的数据与回放工具，不是新的推荐模型，也没有提高或验证胜率。
现有 `daily_pen_overlap_v2` 算法及其价格处理保持冻结；源码指纹不一致时拒绝回放。
分钟数据只验收时间与缓存，不参与候选确认。工具不会启动服务、改持仓、写旧报告或执行交易。

## 三个命令

从项目根目录执行。示例明确固定到 2026-09-30 收盘，不会自动选择今天或读取个人股票池。

```bash
.venv/bin/python -B scripts/validate_chan.py capture \
  --symbols 600519 --periods daily \
  --as-of 2026-09-30T15:00:00+08:00 --page-size 240 --max-pages 1
```

只有 `capture` 读取本地认证配置并联网。自动补充正确标识的沪深300基准 `SH000300`；
裸代码 `000300` 不等同于该指数。最多10只指定证券、每序列最多5页、每页最多1000根，
串行请求之间至少间隔0.5秒。默认一页；分页不前进、权限或网络异常立即标记失败，不换源。
输出打印本次实际 `dataset.json` 路径。真实行情保存在 Git 忽略的 `data/cache/chan_validation/`。
密钥、原始响应、请求头与个人账户字段均不写入快照。

以刚才输出的路径替换 `<dataset-id>`：

```bash
.venv/bin/python -B scripts/validate_chan.py replay \
  --dataset data/cache/chan_validation/<dataset-id>/dataset.json \
  --as-of 2026-09-30T15:00:00+08:00 \
  --output data/cache/chan_validation/replay-20260930.json

.venv/bin/python -B scripts/validate_chan.py frame \
  --dataset data/cache/chan_validation/<dataset-id>/dataset.json \
  --symbol 600519 --as-of 2026-09-15T15:00:00+08:00 \
  --output data/cache/chan_validation/frame-600519-20260915.json
```

`replay` 和 `frame` 完全离线，不加载 `.env` 或应用数据库。输出路径必须尚不存在，不能覆盖旧文件。
相同输入和截止时间产生相同内容。数据集哈希校验能发现意外改动，但不是第三方真实性认证。
退出码：0为产物写入成功（可包含未到期或不可评估）；1为采集部分失败或文件读写失败；2为参数、
数据契约、哈希或输出冲突。遇到1仍可能已保存部分快照，必须检查质量记录，不能当成全量成功。

## 怎么看结果

- `frames`：每个历史收盘时点的原模型结论、可见输入哈希、中枢摘要及数据质量。
- `observations`：候选第一次出现时冻结的依据、中枢边界、端点日期与首次观察时间。
- `events`：后续候选恢复、收盘失效、撤回、缺数、盘中触及边界等追加记录，不重写首次提示。
- `price_observations`：主周期20日、辅助5/60日的价格观察，按上涨/下跌候选分组。
- `frame` 的 `analysis.chart`：该截止时间的完整原始结构数据；`external_issues` 与
  `eligible_for_observation` 另外说明快照损坏是否限制该图形的解释。

原模型输出仍叫 `candidate`，不会产生 `rule_confirmed`。结构端点日期不等于首次可观察日期。
收盘回到首次冻结边界才记为失效；只有盘中触及单独记风险。质量中断不重新计数，
有效数据下候选撤回后再出现会形成新 episode，观察窗口重叠仍须视为关联样本。
采集截断仅说明历史深度有限，不把有效前缀全部判坏；不能据此宣称历史完整。

## 数值门槛

起点为候选可见后的下一交易日开盘；终点为第N个交易日收盘。个股与 `SH000300` 使用相同日期，
不移动窗口凑数。价格收益为 `终点收盘 / 起点开盘 - 1`，超额为个股与指数收益之差；
最大回撤沿起点开盘及此后每日收盘路径计算。下跌候选不反号为做空利润。

`pending` 是尚未到期，且截至当时应有数据完整；`unavailable` 是缺日、无有效成交量、
无效价格、日历范围不够或口径未核实，数值为 null；只有 `matured` 进入均值。
没有候选或没有成熟样本都是正常结果，均值不填0，不输出胜率、概率或显著性结论。

真实采集默认 **日历和复权未核实**：`TQFlag=11` 只是请求参数，不是证明。
因此能够回放结构，不等于能输出有效价格统计。可用 `--calendar <calendar.json>` 提供固定日历，
它必须包含 `sessions, coverage_start, coverage_end, source, version, verification`。
验证记录形如 `{"status":"verified","reference":"证据文件或来源","evidence_sha256":"证据的64位SHA256"}`。
仅填入这些字段不代表证据真实，必须先人工核对原始来源及覆盖范围。
复权核验同样需要独立证据；本工具没有自动提升为 verified 的开关，不应为得到数值而篡改标记。

选股时间是实际采集时间，不冒充历史选股记录。存在样本选择和幸存者偏差；结果不含手续费、滑点、
涨跌停可成交性和现金分红。历史重建也不能证明供应商在当时曾返回相同数据。

## 验收

测试使用显式标为 `synthetic` 的合成数据，覆盖非空候选的未来追加不变性、边界、缺数和重复计数。
真实探查与合成测试分开记录，分钟时间语义在取得可信接口资料交叉核对前继续标为
`bar_end_assumed_unverified`，不能用于多周期确认。

```bash
.venv/bin/python -B -m unittest discover services/api/tests
```

本阶段不修改线上界面，也不恢复旧 MA 回测。后续再对照完整结构引擎，并做滚动样本外验证、
成本和成交约束模拟，依据实际结果决定是否替换模型。
