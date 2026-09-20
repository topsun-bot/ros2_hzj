# evals/ — 《5》Promptfoo 评估套件

本目录是 `ros2_hzj` 的《5》Promptfoo 评估脚手架。仓库是 ROS 2 / DDS 中间件，DDS 层没有 prompt 概念，
因此把"对 DDS 行为的断言"映射成 promptfoo 的 **custom provider**：用一个本地脚本 provider 去跑
`scripts/check_*.py` / `prove_rmw.py` / `print_bench_gates.py`（以及 `config/env/load.py print-a|print-b`
这类带参数的命令），把脚本 stdout 当作 provider 输出，再用 `contains` 断言命中脚本自带的 "healthy"
标记行或双链契约真值。

> Hold 边界：本套件只**运行**现有只读 gate 脚本，不编辑 `config/fastdds.xml`、
> `docs/artifacts/bench/SCOREBOARD.md`、任何 vendor 树或 `dimos_bridge` 运行时代码。

## 文件

| 文件 | 作用 |
|---|---|
| `promptfooconfig.yaml` | 评估配置：1 个 custom provider + 31 个 seed 用例 |
| `localScriptProvider.mjs` | custom provider（`local-script`）：`python3 <prompt>`（prompt 可带空格分隔的 CLI 参数），返回 stdout；非 0 退出即 `error` |
| `fingerprint_check.py` | stdout 指纹回归（eval-only，**不是** CI gate、不进 `run_all_gates`、无需 ci.yml 接线）：重跑 13 gate + `load.py print-a\|b`，把归一化后的完整 stdout 与 `fixtures/` 逐字节比对 |
| `frozen_guard_selftest.py` | frozen-path guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 里构造夹具，断言 guard 对每种违禁 `Path(...)` 形态必报、对允许提及不误报、豁免真源、`render()` 退出码正确 |
| `dual_chain_env_guard_selftest.py` | 双链 env 交叉断言 guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 里造最小 `load.py`/`chain_*.sh`/wrapper 树，断言四类交叉检查对域漂移/shell 漂移/wrapper 伪造/import 写环境/`CYCLONEDDS_URI` 违规必报、对健康树与真实仓不误报 |
| `unitree_swap_guard_selftest.py` | Unitree Cyclone 交换裁决 guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：把 guard 读取的 5 个真实文件复制进 `tempfile` 再逐个变异，断言裁决句翻转/引文篡改/vendor SHA 与 CMake `project()` 版本钉被改/文档删除必报、健康树不误报 |
| `source_map_guard_selftest.py` | ros2-source-map guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 里造最小 map/vendor 树，断言 map 缺失/空 map/引用路径缺失/allowlisted 符号消失必报、陈旧行号只 WARN 不 FAIL、健康树不误报 |
| `executor_map_guard_selftest.py` | Executor/WaitSet map guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：复制 11 个真实 allowlisted 符号文件 + 手写最小 map 进 `tempfile`，只覆盖 executor 独有分支——vendor 下出现 Humble rcl* 树/身份 marker 缺失/飞书 URL 缺失/allowlisted 文件未被引用/必需文档缺失必报，`absent_keys` 与 `reject_bare_words` 两个独有解析参数生效、健康树不误报（共享的路径/符号循环由 #21 覆盖，不重复） |
| `dod_evidence_guard_selftest.py` | 产品 DoD 诚实性 guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：把 guard 读取的 7 个真实内容文件复制进 `tempfile`（fastdds.xml/SCOREBOARD 仅占位），只覆盖其独有的反伪造逻辑——伪造的 `STATUS: PASS`/`DoD: met`/this-host measured-delta/“Humble 在此跑过”声明与虚构的 booked p99 分位必报；同行禁止句（do not write STATUS: PASS）与政策词“分位数”不得误报；STATUS 伪造正则被改宽即漏报 |
| `cega_bridge_hold_guard_selftest.py` | Cega / Bridge Hold guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：把 Hold 文档与 ADR 两个真实内容文件复制进 `tempfile`（fastdds.xml/SCOREBOARD/9 个只读 runtime 路径仅占位），只覆盖其独有解析——ADR §13(4) 表格 cell 必须以 `**Hold**` 开头且不含 PASS/已接 Cega/integrate Cega（cell 翻 PASS、Hold cell 夹带裸 PASS、删行必报）、guard 内置内存行自检生效、首行 `Status:` 翻转与独立“已接 Cega”声明必报；同行禁止句在两份文档中均不得误报；“已接 Cega”正则被改宽即漏报（通用 STATUS:-PASS+禁止句机制与 #23 同形，不重复） |
| `runtime_provenance_guard_selftest.py` | runtime-provenance guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：把 guard 读取的 5 个真实文件（MANIFEST/VERSIONS/Dockerfile/provenance 文档/prove_rmw.py）复制进 `tempfile` 再逐个变异，只覆盖其两个独有解析器——`_dockerfile_pins_humble` 对 rolling 钉版/缺失 ENV/有 ENV 无值三种分支必报，`_versions_rows` 要求 vendor 树名与 40 位 SHA 在**同一行**（删 SHA、SHA 挪到别的行必报）；健康树不误报；SHA 正则被改宽为任意单词即漏报（直白 marker substring 检查不重复） |
| `sink_layers_guard_selftest.py` | sink-layers guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：把 guard 读取的 7 个真实文件（sink/ADR/source-map/executor/swap 文档 + 仅验存在的 fastdds.xml/SCOREBOARD）复制进 `tempfile`，只覆盖其唯一独有解析器 `_LAYER_ROW_RE`——六层表格行首粗体标签锚定：把 `\| **rcl** \|`/`\| **DDS** \|` 行标签置空但保留整行正文（app 行本就含 `rclpy`、executor 行含 `rclcpp`、散文满是 DDS）必须报 FAIL layers 且不连带 FAIL markers/policy；健康六行树不误报；正则被改宽为裸词扫描即漏报（直白 marker substring 与 absent-vendor-tree 机制分别由正向用例/#22 覆盖，不重复） |
| `three_chain_repro_guard_selftest.py` | three-chain 复现 guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：把 guard 读取的 6 个真实文件（repro/source-map/executor/ADR 文档 + 仅验存在的 fastdds.xml/SCOREBOARD）复制进 `tempfile`，只覆盖其独有的两条 `_FABRICATE_RES` 伪造正则——在健康文档（仍含 `map ≠ reproduce`、`STATUS: blocked` 与全部链名 marker）末尾**追加**矛盾句 `map = reproduce`（ASCII `=`，phrase 存在性检查抓不到，只有正则 `\bmap\s*=\s*reproduce\b` 抓）与 `three-chain repro: PROVEN` 必须报 FAIL fabricate 且不连带 missing/markers/phrase/status/chains；同行禁止句「不要把 map = reproduce…」必须豁免；健康树不误报；把 map=reproduce 正则 neuter 为永不匹配即漏报（marker 共现链检查是 guard 自述 marker-only 边界、STATUS 伪造同族机制已由 #23/#24 覆盖，不重复） |
| `bench_gates_guard_selftest.py` | bench-gates guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：把 guard 读取的 4 个真实文件（SCOREBOARD / bench README / scripts-bench README / latency 方法文档）与真实跨机占位目录整个复制进 `tempfile`（SCOREBOARD 只复制不原地改），只覆盖其两项独有检查——跨机占位目录 `2026-09-11-cross-host/` 必须存在（删目录必报 FAIL missing 且不连带 cross/markers），`_cross_host_hits` 经独有 `_STATUS_BLOCKED_RE` 必须在 5 个候选中扫到至少一处诚实的 `STATUS: blocked`（全部改写为非 blocked 但保留 STATUS 子串必报 FAIL cross-host 且不连带 markers）；仅 BLOCKED.txt 一处命中即健康（钉 any-hit 语义）；正则放宽为裸 STATUS 即漏报（直白 required-file/marker substring 与 #23 同形；prove_rmw 无 FAIL 路径、risk_matrix 的 order 块与 marker 元组重叠，均不重复） |
| `gate_registry_selftest.py` | gate-runner **注册表一致性自测**（eval-only，不是 CI gate、无需 ci.yml 接线；对象是 runner 而非某个 guard）：以单一发现规则（`scripts/check_*.py` 加两个固定名 `prove_rmw.py`/`print_bench_gates.py`，排除下划线 helper 与 `run_all_gates.py` 自身）扫描磁盘，与 `run_all_gates.GATES` **双向比对**——磁盘多一个未注册 gate 必报 orphan、GATES 指向缺失脚本必报 missing、helper/runner 不得被误判为 gate、gate 总数钉为 13 且 marker 非空；发现器换成「只信注册表」的桩则孤儿必漏报（恢复后抓回）。补齐「跑绿只证明已注册脚本健康、发现不了新增 gate 忘注册」的盲区（CI structure 仍只枚举 12 个的 ci.yml 接线缺口不在本脚本范围，待 workflow scope） |
| `gate_execution_selftest.py` | gate-runner **执行判定语义负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线；对象是 runner 的 `run_one`/`main` 而非注册表）：在 `tempfile` 放假 gate 并把 `run_all_gates.REPO_ROOT`/`GATES` 指过去（`finally` 恢复），钉「exit 0 且在 stdout/stderr 合并输出里打印健康 marker 才算过」——exit 0 但不打印 marker 必计 `zero-but-missing-marker` 并 FAIL、非零退出（即便打印 marker）必 FAIL、GATES 指向缺失脚本必返回 `127`/`missing:` 并 FAIL；marker 只打到 stderr 且 exit 0 仍算过（钉 combined 语义、防误报）；把 `run_one` 换成「恒报 marker 存在」的桩则空壳 exit-0 gate 必漏报（恢复后抓回）。补齐 #29 只钉注册表、不执行 gate 的盲区 |
| `fingerprint_guard_selftest.py` | stdout 指纹严格层（#17 `fingerprint_check.py`）的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 把 `fingerprint_check` 的 ROOT/FIX_DIR/COMMANDS 指到假命令（`finally` 恢复），钉逐字节比对真会 fail——live 输出与 fixture 不符必 `FAIL stdout drift`+DRIFT、健康命令缺 fixture 必 `FAIL missing fixture`、命令非零退出必 `FAIL command exit N`、`--update` 遇失败命令必在 stderr 拒绝且不写 fixture；命令 stdout 内嵌绝对仓库路径时 `normalize` 必归一化为 `<REPO_ROOT>`（可移植、防假 DRIFT 误报）；把 `normalize` 换成恒返回 fixture 内容的桩则 drift 漏报为绿（恢复后抓回）。补齐 #17 只断言健康 stable 的盲区 |
| `fixtures/*.txt` | 15 份已评审的归一化 stdout 基线（13 gate + print-a/print-b）；有意改动输出后用 `--update` 重生成并随 PR 提交 |
| `results/baseline_raw.txt` | 基线运行的原始终端输出 |
| `results/BASELINE.md` | 基线数字摘要 |

## 最小评估计划

- **目标适配器**：custom provider `local-script`（`evals/localScriptProvider.mjs`）。
  promptfoo 把它 `new` 出来，调用 `callApi(prompt)`；`prompt` 被约定为一个相对仓库根的
  python 脚本路径，可再跟空格分隔的 CLI 参数（如 `config/env/load.py print-a`）。
  provider 把 prompt 按空白拆成 argv，用 `execFileSync('python3', argv, { cwd: repoRoot })`
  执行，返回 `{ output: stdout }`；若脚本非 0 退出，返回 `{ output: stdout+stderr, error: ... }`，
  promptfoo 即把该 case 判为失败。
- **seed 用例**（31 个）：13 个 gate 健康标记（其中 12 个额外断言实质 DDS/Hold/诚实性契约短语）、
  1 个 env 单一真源交叉检查（含双链真值 42/0 与 `CYCLONEDDS_URI` unset）、1 个冻结路径字面量
  防回潮、2 个直接跑 `load.py print-a/print-b` 锁定双链可执行真源的用例、1 个全量 stdout
  指纹回归用例（#17，见下节）、1 个 frozen-path guard 的负向自测用例（#18）、1 个双链 env
  交叉断言 guard 的负向自测用例（#19）、1 个 Unitree Cyclone 交换裁决 guard 的负向自测用例
  （#20）、1 个 ros2-source-map guard 的负向自测用例（#21）、1 个 Executor/WaitSet map
  guard 的负向自测用例（#22）、1 个产品 DoD 诚实性 guard 反伪造逻辑的负向自测用例（#23）、
  1 个 Cega / Bridge Hold guard 独有解析的负向自测用例（#24）、1 个 runtime-provenance
  guard 的 Humble 钉版与 VERSIONS 同行 SHA 解析器负向自测用例（#25），以及 1 个 sink-layers
  guard 的六层表格行首标签锚定解析器负向自测用例（#26），以及 1 个 three-chain 复现 guard 独有的 `map = reproduce` / `three-chain repro: PROVEN` 伪造正则负向自测用例（#27），以及 1 个 bench-gates guard 的跨机占位目录存在性与 `STATUS: blocked` 正则扫描负向自测用例（#28），以及 1 个 gate-runner 注册表（磁盘 gate ↔ run_all_gates.GATES）双向一致性自测用例（#29），以及 1 个 gate-runner 执行判定语义（exit 0 且打印 marker 才算过；exit0 缺 marker / 非零退出 / 脚本缺失 127 必 FAIL；stderr marker 合并判定）负向自测用例（#30，与 #29 同属 runner 而非 guard），以及 1 个 stdout 指纹严格层 #17 自身的负向自测（live≠fixture drift / 缺 fixture / 命令非零 / `--update` 拒绝失败命令必 FAIL、绝对路径归一化 `<REPO_ROOT>` 防误报、normalize 盲桩漏报 drift）用例（#31，对象是 fingerprint_check 工具而非 gate，均见下文专节）：

  | # | 脚本 | 断言 stdout 必含的关键串 |
  |---|---|---|
  | 1 | `scripts/prove_rmw.py` | `ROS not loaded` |
  | 2 | `scripts/check_source_map.py` | `Source map healthy`、`allowlisted symbols ok:`（vendor 中被追踪的 DDS/RMW 符号仍可解析，vendor 重写/丢符号即红） |
  | 3 | `scripts/print_bench_gates.py` | `Bench gates healthy`、`cross-host: blocked`、`Do not sum segment P99s`（跨机测量 blocked、不得把分段 P99 相加/伪造延迟数字） |
  | 4 | `scripts/check_risk_matrix.py` | `Risk matrix healthy`、`§9.4: env/XML first`、`Do not invent risk percentages`、`Cross-host stays blocked`（层级顺序 + 不编风险分 + 跨机 blocked） |
  | 5 | `scripts/check_executor_map.py` | `Executor map healthy`、`WaitSet -> callback: mapped` |
  | 6 | `scripts/check_runtime_provenance.py` | `Runtime provenance healthy`、`underlay != vendor snapshot` |
  | 7 | `scripts/check_unitree_cyclone_swap.py` | `Unitree Cyclone swap record healthy`、`drop-in: FAIL / wire: UNPROVEN`（裁决句不得被悄悄改成 PASS/PROVEN） |
  | 8 | `scripts/check_three_chain_repro.py` | `Three-chain reproduce record healthy`、`map ≠ reproduce`、`STATUS: blocked`（无 Humble 主机不得伪造 reproduce PASS） |
  | 9 | `scripts/check_sink_layers.py` | `Sink-layer record healthy`、`sink layers: mapped (Hold vs allowed)` |
  | 10 | `scripts/check_dual_chain_baseline.py` | `Dual-chain baseline healthy`、`dual-chain baseline: pointer only (no XML rewrite)`、`same-topology XML tuning is paused` |
  | 11 | `scripts/check_dual_chain_baseline.py` | `ok env truth:`（整行编码 A=`rmw_fastrtps_cpp/42`+fastdds.xml、B=`rmw_cyclonedds_cpp/0`、`CYCLONEDDS_URI in CHAIN_B_UNSET`）、`chain_a.sh exports match load.py CHAIN_A`、`chain_b.sh exports match load.py CHAIN_B`、`dual_chain_env.py re-exports match load.py`、`import leaves os.environ unchanged` |
  | 12 | `scripts/check_dod_evidence.py` | `Product DoD evidence healthy`、`DoD: unmet` |
  | 13 | `scripts/check_cega_bridge_hold.py` | `Cega / Bridge Hold healthy`、`no Cega` |
  | 14 | `scripts/check_frozen_path_literals.py` | `Frozen-path literals healthy`（冻结 Hold 路径不得在 helper 外被 `Path(...)` 二次硬编码） |
  | 15 | `config/env/load.py print-a` | `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`、`ROS_DOMAIN_ID=42`、`config/fastdds.xml`（Chain A 可执行真源） |
  | 16 | `config/env/load.py print-b` | `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`、`ROS_DOMAIN_ID=0`（Chain B 可执行真源） |
  | 17 | `evals/fingerprint_check.py` | `stdout fingerprint: stable`、`**commands:** 15`（13 gate + print-a/b 的完整 stdout 与 `fixtures/` 归一化基线逐字节一致） |
  | 18 | `evals/frozen_guard_selftest.py` | `frozen guard selftest: PASS`、`6 must-flag, 7 non-flag, 2 render cases`（guard 对违禁 `Path(...)` 必报、对允许提及不误报、豁免真源、render 退出码正确） |
| 19 | `evals/dual_chain_env_guard_selftest.py` | `dual-chain env guard selftest: PASS`、`6 negative, 2 healthy, 1 mutation`（env 四类交叉检查对漂移必报、对健康树与真实仓不误报、检测器被改宽即红） |
| 20 | `evals/unitree_swap_guard_selftest.py` | `unitree swap guard selftest: PASS`、`5 negative, 2 healthy, 1 mutation`（裁决句翻转/引文篡改/vendor SHA·CMake 版本钉被改/文档删除必报、健康树不误报、CMake 正则被改宽即漏报） |
| 21 | `evals/source_map_guard_selftest.py` | `source map guard selftest: PASS`、`4 negative, 1 warn-only, 2 healthy, 1 mutation`（map 缺失/空 map/引用路径缺失/allowlisted 符号消失必报、陈旧行号只 WARN、健康树不误报、符号查找被改宽即漏报） |
| 22 | `evals/executor_map_guard_selftest.py` | `executor map guard selftest: PASS`、`5 negative, 2 parse-guard, 2 healthy, 1 mutation`（vendor 下出现 Humble rcl* 树/身份 marker 缺失/飞书 URL 缺失/allowlisted 文件未引用/必需文档缺失必报；`absent_keys` 与 `reject_bare_words` 两个 executor 独有解析参数生效、健康树不误报；vendored 检查被改宽即漏报） |
| 23 | `evals/dod_evidence_guard_selftest.py` | `dod evidence guard selftest: PASS`、`5 negative, 2 non-flag, 2 healthy, 1 mutation`（伪造 STATUS: PASS/DoD: met/measured-delta/Humble-here 声明与虚构 booked p99 必报；同行禁止句与政策词“分位数”不误报；STATUS 伪造正则被改宽即漏报） |
| 24 | `evals/cega_bridge_hold_guard_selftest.py` | `cega bridge hold guard selftest: PASS`、`5 negative, 2 non-flag, 1 builtin self-check, 2 healthy, 1 mutation`（ADR §13(4) cell 翻 PASS/Hold cell 夹带裸 PASS/删行、首行 Status 翻转、独立“已接 Cega”必报；内置行自检生效；同行禁止句在两文档中不误报；“已接 Cega”正则被改宽即漏报） |
| 25 | `evals/runtime_provenance_guard_selftest.py` | `runtime provenance guard selftest: PASS`、`5 negative, 2 healthy, 1 mutation`（Dockerfile 钉 rolling/缺失 ENV/有 ENV 无值三分支必报；VERSIONS 行删 SHA、SHA 挪到别的行必报；健康树不误报；SHA 正则被改宽为任意单词即漏报） |
| 26 | `evals/sink_layers_guard_selftest.py` | `sink layers guard selftest: PASS`、`2 negative, 2 healthy, 1 mutation`（rcl/DDS 表格行首粗体标签被置空但保留行正文时必报 FAIL layers 且不连带 markers/policy；健康六行树不误报；行锚定正则被改宽为裸词扫描即被 rclpy/DDS 散文救回而漏报） |
| 27 | `evals/three_chain_repro_guard_selftest.py` | `three-chain repro guard selftest: PASS`、`2 negative, 1 non-flag, 2 healthy, 1 mutation`（健康 marker 全在时追加 `map = reproduce` / `three-chain repro: PROVEN` 矛盾句必报 FAIL fabricate 且不连带 phrase/status/chains；同行「不要把」禁止句豁免；健康树不误报；map=reproduce 正则被 neuter 为永不匹配即漏报） |
| 28 | `evals/bench_gates_guard_selftest.py` | `bench gates guard selftest: PASS`、`2 negative, 1 non-flag, 2 healthy, 1 mutation`（删跨机占位目录必报 FAIL missing、所有候选 STATUS:blocked 被改写为非 blocked 必报 FAIL cross-host 且不连带 markers；仅 BLOCKED.txt 命中仍健康；正则放宽为裸 STATUS 即漏报） |
| 29 | `evals/gate_registry_selftest.py` | `gate registry selftest: PASS`、`2 negative, 1 non-flag, 2 healthy, 1 mutation`（磁盘新增未注册 check_*.py 必报 orphan、GATES 指向缺失脚本必报 missing；下划线 helper 与 run_all_gates.py 不得被当 gate；gate 总数钉 13、marker 非空；发现器只信注册表不扫磁盘即漏报孤儿） |
| 30 | `evals/gate_execution_selftest.py` | `gate runner execution selftest: PASS`、`3 negative, 1 non-flag, 1 healthy, 1 mutation`（exit0 缺 marker 必 FAIL zero-but-missing-marker、非零退出必 FAIL、缺失脚本必 127/FAIL；marker 仅在 stderr 且 exit0 仍过；run_one 恒报 marker 存在即漏报空壳 exit-0 gate） |
| 31 | `evals/fingerprint_guard_selftest.py` | `fingerprint guard selftest: PASS`、`4 negative, 1 non-flag, 1 healthy, 1 mutation`（live≠fixture 必 DRIFT、缺 fixture 必 FAIL、命令非零必 FAIL、`--update` 遇失败命令必拒且不写 fixture；绝对路径归一化 `<REPO_ROOT>` 防误报；normalize 恒返回 baseline 即漏报 drift） |

### stdout 指纹严格层负向自测（#31，eval-only）

- #17（`fingerprint_check.py`）是三层里的**严格层**：逐字节比对 13 gate + `load.py print-a|b` 的归一化完整 stdout 与 `evals/fixtures/` 基线。但 Promptfoo #17 此前只断言健康路径打印 `stdout fingerprint: stable`，**没有任何断言证明它该 fail 时真会 fail**；若它被掏空（比较被旁路、失败命令被容忍、缺/漂移 fixture 仍报绿），gate stdout 的非 marker 漂移会在 `run_all_gates`（只看退出码+单 marker）与宽松 `contains` 双双报绿时静默通过。
- `fingerprint_guard_selftest.py`（对象是 **fingerprint_check 工具本身**，沿用 `*_guard_selftest` 族）在 `tempfile` 把 `ROOT`/`FIX_DIR`/`COMMANDS` 指到假命令（`finally` 恢复），纯标准库、**不碰真实 `evals/fixtures/`**：
  - **4 个负向**：N1 live stdout 与 fixture 不符 → `FAIL stdout drift` + `stdout fingerprint: DRIFT (…)`、rc 1；N2 健康命令但缺 fixture → `FAIL missing fixture`（并提示 `--update`）、rc 1；N3 命令非零退出（即便有 fixture）→ exit code 优先、`FAIL command exit 1`、rc 1；N4 `--update` 遇到失败命令 → stderr `refusing to update fixture … command exited 1`、rc 1 且**不写** fixture（不得为失败命令生成基线）；
  - **1 个 non-flag**：命令 stdout 内嵌绝对仓库路径（macOS tempdir 真实前缀 `/private/...`）→ `normalize` 必把它改写成 `<REPO_ROOT>`、原始路径不泄漏进 fixture，且 verify 仍 stable（钉可移植性、防假 DRIFT 误报）；
  - **1 个健康对照**：`--update` 写出归一化 fixture、干净 verify 打印 stable 横幅、rc 0；
  - **1 个变异**：把 `normalize` 换成「恒返回 fixture baseline」的桩（等价于比较被旁路/输出被抹平的退化）→ 漂移命令漏报为 rc 0 stable；恢复真实 `normalize` 后同一漂移重新 rc 1 + DRIFT。
- **范围边界**：只钉指纹工具自身的判定/写保护/归一化，不重新比对 15 份真实 fixture（那是 #17 的职责），也不替 CI structure 的枚举缺口断言。
- 与 #18–#30 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线。

### gate-runner 执行判定语义负向自测（#30，eval-only）

- #29 钉的是 runner 的**注册面**（磁盘 gate ↔ `run_all_gates.GATES` 双向相等），它从不真正执行 gate，因此保护不了 runner 的**执行面**——`run_one`/`main` 的裁决逻辑：一个 guard 若被掏空成 `sys.exit(0)` 却不再打印健康 marker，头条仍可能报绿。
- `gate_execution_selftest.py`（对象同为 **runner**，不是某个 guard）在 `tempfile` 写假 gate，把 `run_all_gates.REPO_ROOT`/`GATES` 临时指向夹具（`finally` 恢复），纯标准库、**不改仓库**，钉死契约「exit 0 **且** 在 stdout+stderr 合并输出里出现 marker 才算过」：
  - **3 个负向**：N1 exit 0 但不打印 marker → `run_one` 返回 `(0, False)`、`main` 必 return 1 并计 `zero-but-missing-marker: 1` + FAIL；N2 打印 marker 但 `sys.exit(1)` → 非零退出必 FAIL（exit code 优先于 marker）、计 `non-zero: 1`；N3 GATES 指向不存在脚本 → `run_one` 必返回 `127, False` 且输出含 `missing: <rel>`、`main` 必 FAIL；
  - **1 个 non-flag**：marker 只打到 **stderr**、exit 0 → 合并输出仍判 marker 存在、`main` 报绿（钉 stdout+stderr combined 语义、防误报；同时不放松 exit 0 要求）；
  - **1 个健康对照**：exit 0 + stdout 打印 marker → `run_one` 返回 `(0, True)`、`main` return 0 且计 `zero-but-missing-marker: 0` + 绿横幅；
  - **1 个变异**：把 `run_one` 换成「无论 marker 是否打印都恒报 marker 存在」的桩（等价于未来退化成只看退出码），N1 空壳 gate 必**漏报**（`main` return 0）；恢复真实 `run_one` 后同一 gate 重新 FAIL（证明缺-marker 检测非空转）。
- **范围边界**：只钉 runner 的执行/裁决逻辑，不替 CI `structure` 的 12/13 枚举缺口断言（仍待 workflow scope，见 #29），也不跑任何真实项目 gate。
- 与 #17–#29 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线。

### gate-runner 注册表双向一致性自测（#29，eval-only）

- 跑 `run_all_gates.py` 全绿只能证明 **GATES 里已注册的 13 个脚本**存在、exit 0 且打印 marker；它发现不了反向漂移：磁盘上新增一个 `scripts/check_*.py`（或两个固定名 gate `prove_rmw.py` / `print_bench_gates.py` 之一）却忘记加进 `GATES`——头条分数会一直停在 “13/13”，新 gate 永远不进《3》循环。这与第 13 闸 `check_frozen_path_literals.py` 落地后 CI `structure` 仍只枚举前 12 个 gate 是同一类漏注册。
- `gate_registry_selftest.py`（对象是 **runner**，不是某个 guard，因此不叫 guard selftest）用**唯一发现规则**扫描 `scripts/`：名字以 `check_` 开头的 `.py`，加两个固定名；下划线前缀 helper（`_repo.py`/`_md_paths.py`/`_freeze_paths.py`）与 runner 自身 `run_all_gates.py` 永不算 gate。断言发现集合与 `run_all_gates.GATES` **双向相等**，纯标准库、`tempfile` 夹具、**不改仓库**：
  - **2 个负向**：N1 磁盘多一个 `check_orphan_gate.py` 但未注册 → 必报 orphan 且不报 missing；N2 GATES 含 `check_frozen_path_literals.py` 但磁盘缺该文件 → 必报 missing 且不报 orphan；
  - **1 个 non-flag**：磁盘同时放 13 个 gate + 3 个下划线 helper + `run_all_gates.py`，发现器必须只返回 13 个 gate、零问题（钉排除规则，防把 helper/runner 误判为孤儿）；
  - **2 个健康对照**：真实仓发现集合 == 注册集合、gate 总数钉为 **13**、每个 marker 非空、两个固定名都已注册；tempdir 干净 13 gate 树零问题；
  - **1 个变异**：把发现器换成「只返回注册表、不扫磁盘」的桩，N1 孤儿必须**漏报**；恢复真实发现器后同一孤儿重新被抓到（证明孤儿检测非空转）。
- **范围边界**：本用例只钉 runner 注册表与 `scripts/` 的一致性；CI `structure` 仍只枚举 12 个 gate 的缺口属于 `.github/workflows/ci.yml` 接线，需要推送 token 的 `workflow` scope（独立、待用户授权的 PR），本脚本不读 CI yaml、不替它断言。
- 与 #17/#18–#28 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线。

### bench-gates 跨机目录存在性 / STATUS-blocked 正则负向自测（#28，eval-only）

- #3 正向与 #17 指纹只证明**当前健康树渲染为绿**，证明不了 `scripts/print_bench_gates.py`（wiki3 §12 / §13.3，bench 只做指针、跨机 UDP 诚实 blocked）
  独有的两项检查在被悄悄放宽后仍会触发：其一，跨机占位目录 `docs/artifacts/bench/2026-09-11-cross-host/` 在 UDP blocked 期间**必须存在**；
  其二，`_cross_host_hits` 用独有正则 `_STATUS_BLOCKED_RE`（`STATUS:\s*\*?\s*blocked`）扫描 5 个候选文件，必须扫到至少一处诚实的
  `STATUS: blocked`，裸 `STATUS` token 不算数。若删掉目录检查或把 blocked 正则放宽，gate、#3、#17 指纹会继续全绿，跨机 blocked 结论却悄悄失去证据。
- **为什么现在补**：#18–#27 已覆盖 10 个带独有解析器的 guard，`print_bench_gates.py` 是被遗漏的第 11 个（独有正则 + 独有目录存在性分支）。
  `prove_rmw.py` 设计上恒 exit 0、无 FAIL 路径（其诚实性由 Mac HIL 记录覆盖）；`check_risk_matrix.py` 是直白 marker substring，
  其 §9.4「order」块复查的 5 个 token 已全部在 marker 元组里、并非真正顺序校验——两者都不另设负向脚本。
- `bench_gates_guard_selftest.py` 把 guard 读取的 **4 个真实文件 + 整个真实跨机占位目录**复制进 `tempfile`，每次只变异一处，
  驱动可注入的 `render(root=...)`，**不改动仓库**、纯标准库：
  - **2 个负向场景**：N1 删除跨机占位目录、4 个 required 文件保留，必须 exit 1、打印 `FAIL missing` 且**不连带** FAIL cross-host/markers；
    N2 把 5 个候选里每一处 `STATUS: blocked` 改写成非 blocked 的 `STATUS: **ready**`（保留 required 所需的 `STATUS` 子串），
    `_cross_host_hits` 必须返回空、exit 1、打印 `FAIL cross-host` 且**不连带** FAIL markers；
  - **1 个 non-flag**：只保留 `BLOCKED.txt` 一处 blocked、其余 4 个候选改写，树仍必须 exit 0 且 hits 恰为 `[BLOCKED.txt]`
    （钉「任意一个候选命中即可」，防止未来被误改成要求每个文件都写 blocked）；
  - **2 个健康对照**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印 `Bench gates healthy`（复制树还须含 `cross-host: blocked` 行）；
  - **1 个变异**：把 `_STATUS_BLOCKED_RE` 放宽为裸 `STATUS`（try/finally 恢复）后 N2 必须**漏报**（exit 0、无 FAIL cross-host），恢复后重新抓到。
- 与 #17/#18–#27 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要
  ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### three-chain 复现 guard 独有伪造正则负向自测（#27，eval-only）

- #8 正向与 #17 指纹只证明**当前健康文档**渲染为绿，证明不了 `check_three_chain_repro.py`（wiki3 §13(2)，map≠reproduce、
  `STATUS: blocked` 诚实性）独有的两条 `_FABRICATE_RES` 伪造正则在被改宽后仍会触发。#23（DoD）/#24（Cega）已钉过
  「STATUS 伪造正则 + 同行禁止句豁免」这一**同族机制**，但被守护文档、正则、伪造串都不同；#27 只钉 three-chain 记录独有、
  且 phrase/status **存在性检查抓不到**的增量：在一份仍完整保留 `map ≠ reproduce`（≠，U+2260）、`STATUS: blocked` 与
  publish / History / wait→callback / WaitSet 全部链名 marker 的健康文档末尾，**额外追加一句矛盾/伪造**。
- **刻意只覆盖独有解析器**：六个 required 文件的 marker substring 检查与 `_has_three_chains`（publish AND History AND
  (wait→callback OR (WaitSet AND callback))）是直白 token 共现，guard 自述边界就是 “filesystem + honesty markers only”、
  不做语义成链验证；「WaitSet/callback 在无关位置共现也接受」是 marker-only 设计而非 bug（收紧它属行为变更，超出 eval-only），
  不堆夹具；`STATUS: PASS` 这一同族正则由 #23/#24 覆盖。
- `three_chain_repro_guard_selftest.py` 把 guard 读取的 **6 个真实文件**复制进 `tempfile`，每次只向 repro 文档末尾追加
  一句（不删任何 marker），驱动可注入的 `render(root=...)`，**不改动仓库**、纯标准库：
  - **2 个负向场景**：N1 追加裸 `map = reproduce`（ASCII `=`；`map ≠ reproduce` 仍在故 phrase 检查通过，只有正则
    `\bmap\s*=\s*reproduce\b` 能抓到矛盾）；N2 追加 `three-chain repro: PROVEN`（命中
    `(three-chain repro|三条链复现) : (PASS|PROVEN|OK)`；相邻的 `reproduce:` 正则刻意不匹配短词 `repro`）。两者都必须
    exit 1、打印 `FAIL fabricate` 并点名伪造串，且**不得连带** FAIL missing/markers/phrase/status/chains（证明健康 marker
    全存活、只触发诚实性检查）；
  - **1 个 non-flag（豁免契约）**：同行禁止句「不要把 map = reproduce 写进结论」必须被 `_PROHIBITION_RE` + `line_at`
    豁免、整树 exit 0 且无 FAIL fabricate（防止未来把豁免改严、误杀合法的「不要写」指令）；
  - **2 个健康对照**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印 `three-chain repro: blocked (map only)`；
  - **1 个变异**：把 `\bmap\s*=\s*reproduce\b` 替换为永不匹配的 `(?!)`（try/finally 恢复整个 `_FABRICATE_RES` 元组）
    后 N1 必须**漏报**（exit 0、无 FAIL fabricate），恢复后必须重新抓到。
- 与 #17/#18–#26 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要
  ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### sink-layers 六层表格行首标签锚定负向自测（#26，eval-only）

- #9 的正向运行与 #17 指纹只证明**当前健康文档渲染为绿**，证明不了 `check_sink_layers.py`（飞书《通信中间件》
  sink 分层 app / rcl / rmw / DDS / executor / memory）唯一的**结构化解析器** `_LAYER_ROW_RE` 仍然会触发。该
  正则以**行首 + 粗体标签**锚定六层表格行：`(?m)^\|\s*\*\*(app|rcl|rmw|DDS|executor|memory)\*\*\s*\|`。脚本
  自带注释明示：裸 substring `rcl` 会同时命中 **app** 行正文里的 `rclpy`。真实文档里 app 行本就写着 `rclpy`、
  executor 行写着 `rclcpp` / `rclpy`，散文里 `DDS` 更是满屏。若有人把行检查"简化"成裸词扫描，删掉
  `| **rcl** |`（或 `| **DDS** |`）表格行标签、只留周围正文，会让 gate、#9、#17 指纹（比对健康树输出）继续全绿，
  六层 sink 表却已悄悄丢了一行。
- **刻意只覆盖独有解析器**：`_SINK_MARKERS` / `_POLICY_CLAUSES` / Hold vs allowed / three-chain / Unitree
  pointer 都是直白 `token in text` 检查、与正向用例同形，不重复堆夹具；`ABSENT_VENDOR_TREES`（含 iceoryx）的
  vendored-tree 缺席机制已由 #22 executor-map 自测覆盖。#26 只测行首标签锚定这一件 #17/#18–#25 都没钉的事。
- 五个内容文档带大量连续 marker，手写最小健康文档易腐；故 `sink_layers_guard_selftest.py` 把 guard 读取的
  **7 个真实文件**（sink、ADR、source-map、executor、Unitree-swap 文档，加仅验存在的 fastdds.xml / SCOREBOARD）
  复制进 `tempfile`，再每次只把 sink 文档的一个行标签置空（`| **rcl** |`→`|  |`，**整行正文一字不动**，故
  Humble/Rolling/eCAL/0.10.2 等行内 marker 都保留），驱动可注入的 `render(root=...)`，**不改动仓库**、纯标准库：
  - **2 个负向场景**：N1 置空 `| **rcl** |` 标签（裸词扫描会被 app 行 `rclpy`、executor 行 `rclcpp` 救回）；
    N2 置空 `| **DDS** |` 标签（裸词扫描会被满屏散文 `DDS` 救回）；两者都必须 exit 1、打印
    `FAIL layers` 并点名对应 `| **<层>** |`，且**不得连带** FAIL markers / FAIL policy（证明只触发行检查）；
  - **2 个健康对照（双向契约）**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印
    `sink layers: mapped (Hold vs allowed)`——同时证明 app/executor 行里丰富的 `rclpy`/`rclcpp`/`DDS`
    散文不会被误判成缺行或多行（防改严误报方向）；
  - **1 个变异**：把 `_LAYER_ROW_RE` 改宽为去掉行首锚定与粗体要求的裸词 `(?m)(app|rcl|rmw|DDS|executor|memory)`
    （try/finally 恢复）后 N1 必须**漏报**（exit 0、无 FAIL layers），恢复后必须重新抓到——精确复现脚本注释
    警告的 substring 陷阱，证明 N1 确实依赖行首粗体锚定。
- 与 #17/#18–#25 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、
  不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### runtime-provenance Humble 钉版 / VERSIONS 同行 SHA 负向自测（#25，eval-only）

- #6 的正向运行与 #17 指纹只证明**当前健康树渲染为绿**，证明不了 `check_runtime_provenance.py`（wiki3 §13
  underlay vs overlay vs vendor snapshot）独有的**两个解析器**仍然会触发。该 guard 守护：Docker 镜像必须钉
  Humble underlay（`ENV ROS_DISTRO=humble`），`vendor/VERSIONS.md` 里六棵 vendor 树每一行都必须带 40 位 SHA。
  若有人把这两个解析器改宽，一份钉成 `rolling` 的 Dockerfile、或 SHA 从表格行上脱落的 VERSIONS 表会让 gate、
  #6、#17 指纹（比对的都是健康树输出）继续全绿，underlay/vendor 溯源裁决却已悄悄失真。
- **刻意只覆盖独有解析逻辑**：MANIFEST/provenance 文档的 marker 是直白 `token in text` substring 检查、无解析器，
  与正向用例同形，不重复堆夹具；#25 只测本 guard 独有的两部分——
  ① `_dockerfile_pins_humble` 用 `_ENV_DISTRO_RE` 多行解析 `ENV ROS_DISTRO`，有三个不同失败分支（指令完全缺失 /
  指令在但值无法解析 / 钉了非 humble 的发行版，含多行 ENV）；
  ② `_versions_rows` 要求 vendor 树名与 40 位 SHA 在**同一行**（`row in line and _SHA_RE.search(line)`），SHA 漂到
  别的行不能让该行通过——不是"全文某处有 SHA 就行"。
- 五个文件都带连续 marker，手写最小健康树易腐；故 `runtime_provenance_guard_selftest.py` 把 guard 读取的
  **5 个真实文件**（MANIFEST、VERSIONS、Dockerfile、provenance 文档、prove_rmw.py）复制进 `tempfile`，再每次只
  变异一个文件，驱动可注入的 `render(root=...)`，**不改动仓库**、纯标准库：
  - **5 个负向场景**：N1 Dockerfile `ENV ROS_DISTRO=humble`→`rolling`（报 FAIL Dockerfile pins …）；N2 删除
    ENV 行（报 FAIL Dockerfile missing …）；N3 保留 `ENV ROS_DISTRO` 但不给可解析值（报 FAIL Dockerfile
    is not humble，覆盖 present-but-unparsed 分支）；N4 把 `vendor/rmw/` 行的 40 位 SHA 替换为 NO_SHA、保留该行
    （报 FAIL VERSIONS rows）；N5 把该 SHA 挪到文件首行、原行留 NO_SHA（报 FAIL VERSIONS rows，证明是同行约束
    而非全文 SHA 扫描）；
  - **2 个健康对照**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印 `underlay != vendor snapshot`；
  - **1 个变异**：把 `_SHA_RE` 从 40 位 hex 边界匹配改宽为任意单词 `\b\w+\b`（try/finally 恢复）后 N4 必须**漏报**
    （被篡改行仍含 `vendor/rmw/`、`rolling` 等单词，exit 0、无 FAIL VERSIONS rows），恢复后必须重新抓到——证明
    N4 确实依赖严格的 SHA 检测器。
- 与 #17/#18–#24 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、
  不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### Cega / Bridge Hold 负向自测（#24，eval-only）

- #9 的正向运行与 #17 指纹只证明**当前健康文档渲染为绿**，证明不了 `check_cega_bridge_hold.py`（wiki3 §13(4)
  Cega / Bridge 后置 Hold）独有的**表格 cell 解析与反伪造检测器**仍然会触发。该 guard 守护：本 cut 不集成
  Cega、不重写 `dimos_bridge` 运行时，ADR §13(4) 行必须保持 `**Hold**`。若有人把 cell 解析或伪造正则改宽，
  一份偷偷接入 Cega 的文档会让 gate、#9、#17 指纹（比对的都是健康树输出）继续全绿，最高优先级 Hold 却已被突破。
- **刻意只覆盖独有解析**：通用的 `STATUS: PASS` + 同行禁止句豁免机制与 #23 同形（两个 guard 各有一份独立
  正则），不重复堆夹具；#24 只测本 guard 独有的部分——
  ① `_ADR_ROW_RE` / `_adr_row_ok` / `_CELL_POSITIVE_RE` 解析 ADR 表格里**单个 §13(4) cell**（cell 必须以
  `**Hold**` 开头、且 cell 内任何位置都不得有 PASS/PROVEN/Active/已接 Cega/integrate Cega）；
  ② guard 内置的 `_row_self_check`（在内存里把真实 ADR 的 Hold 改成 PASS、或在 Hold cell 后追加 PASS/已接
  Cega，必须不再判 ok）——这是检测器自带的纵深防御，#24 把它沉淀为显式回归；
  ③ 中文独有的伪造模式 `已接 Cega`（独立于 STATUS:/Cega-Bridge:PASS/integrate Cega）；
  ④ `_first_status_line` 只检查 Hold 文档的**第一个** `Status:` 行。
- Hold 文档与 ADR 带大量连续 marker，手写最小健康文档易腐；故 `cega_bridge_hold_guard_selftest.py` 把 guard
  解析的 **2 个真实内容文件**复制进 `tempfile`（fastdds.xml / SCOREBOARD / 9 个只读 runtime 路径在该脚本里
  只验存在，用空占位），再每次只变异一个文档，驱动可注入的 `render(root=...)`，**不改动仓库**、纯标准库：
  - **5 个负向场景**：N1 ADR §13(4) cell `**Hold**`→`**PASS**`（报 FAIL ADR row）；N2 cell 保留 Hold 前缀但
    末尾夹带一个不带 Cega 字样的裸 ` ... PASS`（报 FAIL ADR row 且**不报** FAIL fabricate，证明是 cell 级
    检测器而非全文伪造扫描独立抓到）；N3 Hold 文档首个 `Status:` 行翻成 `**PASS**`（报 FAIL status）；
    N4 Hold 文档追加独立行 `已接 Cega`（报 FAIL fabricate hold）；N5 删除 ADR §13(4) 整行（报 FAIL ADR row）；
  - **2 个防误报（双向契约）**：P1 Hold 文档、P2 ADR 中 §13(4) cell **之外**的正文各追加一行同行禁止句
    `we do not integrate Cega ...`，必须被禁止句豁免、仍 exit 0（cell 行不动，仍判 Hold）；
  - **1 个内置自检断言**：真实 ADR 上 `_row_self_check` 返回空，且它构造的两种伪装（Hold→PASS、Hold…PASS/
    已接 Cega）都被 `_adr_row_ok` 拒绝（证明 guard 自带的内存变异纵深防御持续有效）；
  - **2 个健康对照**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印 `§13(4) Cega / Bridge: Hold`；
  - **1 个变异**：把 `_CEGA_FABRICATE_RES` 中 `已接 Cega` 那条正则替换为“永不匹配”（try/finally 恢复）后
    N4 必须**漏报**（exit 0、无 FAIL fabricate hold），恢复后必须重新抓到——证明 N4 确实依赖该中文伪造检测器。
- 与 #17/#18–#23 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、
  不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### 产品 DoD 诚实性 guard 反伪造负向自测（#23，eval-only）

- #12 的正向运行与 #17 指纹只证明**当前健康文档渲染为绿**，证明不了 `check_dod_evidence.py`（wiki3 §6.3
  产品 DoD 诚实性）独有的**反伪造检测器**仍然会触发。该 guard 保证证据文档保持 `DoD: unmet` /
  `STATUS: blocked`、点名五项未达成产品项，且不得伪造正向的 `STATUS: PASS` / `DoD: met` /
  this-host measured-delta / “Humble 在此跑过”，也不得虚构 booked 分位 token（p50/p99）。若有人把某个
  伪造正则或“同行禁止句豁免”改宽，一份偷偷翻成 PASS 的文档会让 gate、#12、#17 指纹（比对的都是健康树
  输出）继续全绿，诚实裁决却已悄悄反转。
- **刻意只覆盖独有反伪造逻辑**：直白的 marker 缺失 / 文件缺失与 #20 N5 / #22 N2·N5 同形，不重复堆夹具。
- DoD 文档带约 28 个连续 marker，手写最小健康文档易腐；故 `dod_evidence_guard_selftest.py` 把 guard 读取的
  **7 个真实内容文件**复制进 `tempfile`（fastdds.xml / SCOREBOARD 在该脚本里只验存在，用空占位），再每次
  只向 DoD 文档追加一行篡改，驱动可注入的 `render(root=...)`，**不改动仓库**、纯标准库：
  - **5 个负向场景**：N1 独立行 `STATUS: PASS`、N2 `DoD: met`、N3 `this-host measured-delta: PASS`、
    N4 `Humble runtime existed here`（均报 FAIL fabricate，分别覆盖 STATUS / DoD / measured-delta /
    Humble 四个不同伪造正则）、N5 虚构 booked token `p99 = 12 ms`（报 FAIL percentiles）；
  - **2 个防误报（双向契约）**：P1 同行含禁止词的 `do not write STATUS: PASS` 必须被豁免、仍 exit 0；
    P2 政策词“分位数”不得触发分位正则、仍 exit 0（既防改宽漏报，也防改严误报）；
  - **2 个健康对照**：真实仓 `render()` 与一份完整复制的临时树都必须 exit 0 且打印成功 marker
    （证明复制夹具与真实树等价，负向场景不会因错误原因失败）；
  - **1 个变异**：把 `_STATUS_FABRICATE_RE` monkeypatch 为“永不匹配”后 N1 必须**漏报**（exit 0、无
    FAIL fabricate），恢复后必须重新抓到——证明 N1 确实依赖该伪造检测器。
- 与 #17/#18/#19/#20/#21/#22 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI
  structure 枚举、不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### Executor/WaitSet map 负向自测（#22，eval-only）

- #5 的正向运行与 #17 指纹只证明**当前健康树渲染为绿**，证明不了 `check_executor_map.py`（wiki3 §13
  wait→callback 身份图）的 executor **独有**检查仍然会触发。该 guard 守护：Humble `rcl/rclcpp/rclpy`
  不得出现在 `vendor/`、16 条身份 marker 与 3 个飞书 URL 不得丢失、11 个 allowlisted WaitSet/wait/take
  符号文件必须被 map 引用、7 个必需文档必须在树。
- **刻意不重复 #21**：两个 guard 共享 `_md_paths.check_cited_paths`（引用路径存在性 + allowlisted 符号
  + 陈旧行号 WARN），那部分负向行为已由 #21 覆盖；#22 只测 executor 独有分支。
- `executor_map_guard_selftest.py` 把 **11 个真实 allowlisted 符号文件**复制进 `tempfile`（符号查找跑在
  真实内容上，同 #20 策略），再手写一张含 16 marker + 3 URL 的最小 map，驱动可注入的 `render(root=...)`，
  **不改动仓库**、纯标准库：
  - **5 个负向场景**：N1 `vendor/rcl{,cpp,py}` 目录出现（报 FAIL vendored）；N2 身份 marker 缺失
    （报 FAIL markers）；N3 飞书 URL 缺失（报 FAIL Feishu URL）；N4 allowlisted 文件存在但 map 不再引用
    （报 FAIL uncited）；N5 必需文档缺失（报 FAIL missing）；
  - **2 个解析机制断言（parse-guard，executor 独有）**：PG1 `absent_keys` 把"应当缺席"的 `vendor/rcl`
    引用挡在 cited 集合外（不传该参数则进入集合、会被要求存在）；PG2 `reject_bare_words` 让散文裸词
    `` `dimos_bridge` `` 不被误解析成 `docs/architecture/dimos_bridge`（不传则误解析）；最小健康 map
    本身就含这两类引用，健康树 exit 0 同时证明两个参数在防误报；
  - **2 个健康对照**：真实仓 `render()` 与最小健康临时树都必须 exit 0 且打印 `Executor map healthy`；
  - **1 个变异**：把 `ABSENT_VENDOR_TREES` 清空（同时三棵 rcl* 目录都存在）后 N1 必须**漏报**（exit 0、
    无 FAIL vendored），恢复后必须重新抓到三条 FAIL vendored——证明 N1 确实依赖 vendored-tree 检测器。
- 与 #17/#18/#19/#20/#21 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI
  structure 枚举、不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### ros2-source-map 负向自测（#21，eval-only）

- #2 的正向运行与 #17 指纹只证明**当前健康树渲染为绿**，证明不了 `check_source_map.py`（wiki3 §13.2）
  的各项检查**仍然会触发**。该 guard 保证 `docs/architecture/ros2-source-map.md` 仍指向真实在树文件、
  且被追踪的 vendor 符号（如 Fast-DDS `WriterHistory.cpp` 的 `add_change`、rmw 的 `rmw_publish` 等）
  未被重写/删除。若有人删掉 map、清空引用、指向已删文件或删掉钉版符号，而检测器被相应改宽，所有正向
  运行（gate、#2、#17 指纹，比对的都是健康树输出）都会继续全绿，source map 却已悄悄不再描述 vendor 代码。
- source map 的最小夹具很小（一个 map + 一个 vendor 文件），故 `source_map_guard_selftest.py` 不像
  Unitree 自测那样复制真实文件，而是在 `tempfile` 里手写最小树，驱动可注入的 `render(root=...)`，
  **不改动仓库**、纯标准库：
  - **4 个负向场景**：N1 删除 map（报 FAIL map missing）；N2 map 只剩散文、提不出任何在树路径
    （报 FAIL no in-repo paths extracted）；N3 map 引用不存在的 `vendor/not/there.cpp`（报 FAIL missing）；
    N4 被引用的 vendor 文件删掉 allowlisted 符号 `add_change`（报 FAIL symbol）；
  - **1 个 warn-only 契约**：map 引用 `...WriterHistory.cpp:999` 而行号故意陈旧、符号仍在时，必须打印
    `WARN stale line` 但 **exit 0**（锁定文档承诺的"陈旧行号只告警"，防止它被悄悄收紧成 FAIL）；
  - **2 个健康对照**：真实仓 `render()` 与最小健康临时树都必须 exit 0 且打印 `Source map healthy`
    （证明手写夹具有效，负向场景不会因错误原因失败）；
  - **1 个变异**：把 `_md_paths.symbol_lines` monkeypatch 成"恒返回命中"后，N4 必须**漏报**（被篡改树
    打印 `ok symbol`、exit 0），恢复后必须重新报 FAIL symbol——证明 N4 确实依赖检测器里的符号查找。
- 与 #17/#18/#19/#20 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure
  枚举、不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### Unitree Cyclone 交换裁决负向自测（#20，eval-only）

- #7 的正向运行只证明**当前记录打印了健康 marker**（`drop-in: FAIL / wire: UNPROVEN`），证明不了
  guard 的各项检查**仍然会触发**。该裁决守护的是与《6》CVE 结论直接相关的诚实性：Unitree bundled
  Cyclone 0.10.2 对 vendor 11.0.1 不是 drop-in、默认保持 bundled、唯一合法替换路径是
  `unitree_sdk2_hzj + UNITREE_DDS_PROVIDER=external`、wire 互通保持 UNPROVEN。若有人把文档裁决翻成
  `drop-in PASS / wire PROVEN`、删掉引文 `DDS_VERSION "0.10.2"`、改松 vendor SHA / CMake
  `project() VERSION` 钉版或删除交换文档，而 guard 被相应改宽，所有正向运行（gate、#7、#17 指纹，
  它们比对的都是健康树输出）都会继续全绿，安全裁决却已悄悄反转。
- 与 frozen/env guard 手写最小夹具不同，交换文档本身带 18 个连续 marker，手写健康文档易腐且会偏离真实
  记录；因此 `unitree_swap_guard_selftest.py` 把 guard 读取的 **5 个真实文件**（交换文档、`VERSIONS.md`、
  `vendor/CycloneDDS/CMakeLists.txt`、`config/fastdds.xml`、`SCOREBOARD.md`，后两者在该脚本里只验存在）
  复制进 `tempfile`，再每次只变异一个，复用可注入的 `render(root=...)`，**不改动仓库**、纯标准库：
  - **5 个负向场景**：N1 连续裁决句翻转 FAIL/UNPROVEN→PASS/PROVEN（报 FAIL verdict，且未改动的
    VERSIONS/CMake 仍报 ok，证明各检查独立、不连带）；N2 引文 `DDS_VERSION "0.10.2"` 改成 9.9.9
    （裸 0.10.2 在文档别处保留，专门的引文检查仍报 FAIL quote）；N3 vendor CycloneDDS SHA 行被改
    （报 FAIL VERSIONS row，交换文档未动故裁决句仍 ok）；N4 CMake `project() VERSION 11.0.1`
    被改成 9.9.9（报 FAIL CMake project()）；N5 删除交换文档（报 FAIL missing、不打印 marker）；
  - **2 个健康对照**：真实仓 `render()` 与一份完整复制的临时树都必须 exit 0 且打印 marker（证明复制
    夹具本身有效、与真实树等价，否则负向场景可能因错误原因失败）；
  - **1 个变异**：把 `_CMAKE_PROJECT_RE` 改宽为只匹配 `project(CycloneDDS` 而不再钉 `VERSION 11.0.1`，
    N4 必须**漏报**（被篡改树打印 `ok CMake project()`），恢复正则后必须重新抓到——证明 N4 确实依赖
    检测器里的版本钉，而非偶然通过。
- 与 #17/#18/#19 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure
  枚举、不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### 双链 env 交叉断言负向自测（#19，eval-only）

- #11 的正向运行只证明**当前 env 是健康的**，证明不了四类交叉检查（env truth / cross-check A /
  cross-check B / wrapper，外加 chain_b 不得 export、必须 unset `CYCLONEDDS_URI`）**仍然会触发**。
  若有人把某个比较改宽或弄坏分支使漂移不再被报，所有正向运行（gate、#11、#17 指纹）都会继续全绿，
  而"load.py 单一真源"保证已悄悄失效。轮次 3 这些负向行为只用一次性 `/tmp` 夹具验证过，#19 把它们
  沉淀为仓内可复跑回归。
- `dual_chain_env_guard_selftest.py` 复用 guard 可注入的 `render(root=...)`，在 `tempfile` 里造一棵
  最小 env 树（`load.py` + `chain_a.sh` + `chain_b.sh` + wrapper + 仅占位的 `config/fastdds.xml`），
  **不改动仓库**、纯标准库；doc/marker 文件在临时树里有意缺失（render 仍会因缺 doc exit 1），断言只看
  五行 `FAIL env|chain A|chain B` 家族，忽略无关的缺 doc FAIL：
  - **6 个负向场景**：A 域 42→43（shell 仍 42，env truth + cross-check A 双报）；B 域 0→1（env truth +
    cross-check B）；wrapper 硬编码伪造重导出（仅 env wrapper 报，不得误触 truth/cross-check）；import
    `load.py` 写 `os.environ`（env truth 报）；`chain_b.sh` 额外 `export CYCLONEDDS_URI`（即使同时 unset
    也必报 must not export）；`chain_b.sh` 漏 `unset CYCLONEDDS_URI`（报 need anchored unset）；
  - **2 个健康对照**：完全正确的最小临时树必须**零** env/chain FAIL（零误报）；真实仓 `render()` 必须
    exit 0 且打印全部 4 行 `ok env ...`；
  - **1 个变异**：内存里把 `CYCLONEDDS_URI` export 检测器正则替换为"永不匹配"后，export 场景必须漏报
    （证明正常断言确实依赖该检测器），恢复后必须重新抓到。
- 写 `os.environ` 的夹具场景在每次 render 前后做快照/恢复，不污染测试进程。
- 与 #17/#18 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、
  不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### frozen-path guard 负向自测（#18，eval-only）

- #14 的正向运行只证明**当前树是干净的**，证明不了 guard 的检测器**仍然会触发**。若有人把
  `check_frozen_path_literals.py` 的正则改宽（或弄坏豁免/渲染逻辑）使它永不报错，所有正向运行都会
  继续全绿，而保护已悄悄失效。轮次 4 这一负向行为只用一次性 `/tmp` 夹具验证过，#18 把它沉淀为
  仓内可复跑回归。
- `frozen_guard_selftest.py` 复用 guard 自身的纯函数 `_hits_in` 与可注入的 `render(root=...)`，
  只在 `tempfile` 临时目录里造夹具、**不改动仓库**、纯标准库：
  - **6 个必报片段**：`Path("config/fastdds.xml")`、`Path("docs/artifacts/bench/SCOREBOARD.md")`、
    `r"..."`/`f"..."` 前缀、单引号且校验行号、短形式 `artifacts/bench/SCOREBOARD.md`；
  - **7 个不得误报片段**：`from _freeze_paths import ...`、`Path(FASTDDS_XML_REL)`、
    `endswith("config/fastdds.xml")`、输出文案、检测器自身的正则串、无关路径；
  - **2 个 render 端到端**：临时树里放违禁 `bad_gate.py`（第 2 行）时必须 exit 1、不打印健康 marker、
    点名 `bad_gate.py:2`，且豁免真源 `_freeze_paths.py`（它本身合法地硬编码路径）不被报；删掉坏文件后
    必须 exit 0 并打印 marker。
- 已做变异验证：在内存里把检测正则替换为"永不匹配"后，该自测 `exit 1`（证明它不是摆设）。
- 与 #17 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、
  不需要 ci.yml 接线（不受推送 token 缺 `workflow` scope 阻塞）。

### stdout 指纹回归（#17，eval-only）

- `run_all_gates` 只看每个 gate 的退出码 + 一个健康 marker；promptfoo 的 `contains` 只保证关键串
  存在（宽松）。两者都看不到 marker 之外的**意外输出漂移**（多/少一行 ok、计数变化、裁决句被改写但
  仍 exit 0 且 marker 还在）。`fingerprint_check.py` 把 13 gate + `load.py print-a|b` 的**完整 stdout**
  与已提交的 `evals/fixtures/*.txt` 逐字节比对，是严格层，与前两者互补而非重复。
- 它放在 `evals/` 下，**不是**第 14 个 gate：不进 `run_all_gates.GATES`、不被 CI structure 枚举、
  不扫 `scripts/`、不需要 `.github/workflows/ci.yml` 接线（因此不受推送 token 缺 `workflow` scope 阻塞）。
  gate 命令清单直接 `import` 自 `run_all_gates.GATES`（单一真源），另加 print-a/print-b。
- **归一化（只抹平环境/噪声，不改契约文本）**：仓库根绝对路径 → `<REPO_ROOT>`（如 print-a 的
  profiles 行，保证换 clone 路径/CI 也能过）；frozen gate 的动态 `**ok scanned:** N` → `<N>`
  （N 是 `scripts/*.py` 文件数，新增 helper/gate 就变，属文件数噪声，已由 GATES 登记覆盖）。
  其余计数（如 source-map 的 cited paths / allowlisted symbols）保持精确——它们反映被评审的
  map/vendor 内容，漂移就应在评审中显形。
- **有意改动某 gate 的 stdout 时**：在同一 PR 内重生成并提交 fixtures，再跑 eval：

  ```bash
  python3 evals/fingerprint_check.py --update
  ```

  默认（不带参数）只读比对，漂移即 exit 1 并打印 unified diff。

- **断言语义**：
  - 退出码 0 —— 由 provider 契约保证（非 0 即 `error`，case 直接失败），不需要额外断言。
  - stdout 关键串 —— 由每个 case 的 `assert: { type: contains, value: ... }` 保证。
  - 任一不满足 → 该 case 失败。
- **夹具**：不含机密 / PII。所有"输入"只是仓库内的脚本路径；所有"输出"只是这些脚本的 stdout
  （文件系统 + Hold 标记，不含密钥、token、个人信息）。

## 运行

从仓库根目录：

```bash
npx --yes promptfoo@0.123.1 eval -c evals/promptfooconfig.yaml
```

仓库根没有 `package.json`，故不新增 `npm run evals` 脚本；直接用上面这条命令即可。
首次运行 `npx` 会把 promptfoo 拉到 npx 缓存（一次性），之后运行很快。
`promptfoo view` 可在浏览器里看交互式结果（结果默认存在 `~/.promptfoo/`，不在仓库内）。

## 环境变量

本机无 ROS 2 环境（`rclpy` 不可导入，`/opt/ros` 不存在）。**这是预期基线**：
`prove_rmw.py` 等脚本本就是 env/string 事实脚本，在 `RMW_IMPLEMENTATION` / `ROS_DOMAIN_ID` /
`ROS_DISTRO` 等均未设置时仍 `exit 0` 并打印 `ROS not loaded`，这正是 seed case #1 断言的内容。
不要为了跑这套 eval 去 source ROS 或 export RMW 变量；那会改变被断言的基线语义。

## 基线

见 [`results/BASELINE.md`](results/BASELINE.md)。
