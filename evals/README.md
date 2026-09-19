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
| `promptfooconfig.yaml` | 评估配置：1 个 custom provider + 22 个 seed 用例 |
| `localScriptProvider.mjs` | custom provider（`local-script`）：`python3 <prompt>`（prompt 可带空格分隔的 CLI 参数），返回 stdout；非 0 退出即 `error` |
| `fingerprint_check.py` | stdout 指纹回归（eval-only，**不是** CI gate、不进 `run_all_gates`、无需 ci.yml 接线）：重跑 13 gate + `load.py print-a\|b`，把归一化后的完整 stdout 与 `fixtures/` 逐字节比对 |
| `frozen_guard_selftest.py` | frozen-path guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 里构造夹具，断言 guard 对每种违禁 `Path(...)` 形态必报、对允许提及不误报、豁免真源、`render()` 退出码正确 |
| `dual_chain_env_guard_selftest.py` | 双链 env 交叉断言 guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 里造最小 `load.py`/`chain_*.sh`/wrapper 树，断言四类交叉检查对域漂移/shell 漂移/wrapper 伪造/import 写环境/`CYCLONEDDS_URI` 违规必报、对健康树与真实仓不误报 |
| `unitree_swap_guard_selftest.py` | Unitree Cyclone 交换裁决 guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：把 guard 读取的 5 个真实文件复制进 `tempfile` 再逐个变异，断言裁决句翻转/引文篡改/vendor SHA 与 CMake `project()` 版本钉被改/文档删除必报、健康树不误报 |
| `source_map_guard_selftest.py` | ros2-source-map guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 里造最小 map/vendor 树，断言 map 缺失/空 map/引用路径缺失/allowlisted 符号消失必报、陈旧行号只 WARN 不 FAIL、健康树不误报 |
| `executor_map_guard_selftest.py` | Executor/WaitSet map guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：复制 11 个真实 allowlisted 符号文件 + 手写最小 map 进 `tempfile`，只覆盖 executor 独有分支——vendor 下出现 Humble rcl* 树/身份 marker 缺失/飞书 URL 缺失/allowlisted 文件未被引用/必需文档缺失必报，`absent_keys` 与 `reject_bare_words` 两个独有解析参数生效、健康树不误报（共享的路径/符号循环由 #21 覆盖，不重复） |
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
- **seed 用例**（22 个）：13 个 gate 健康标记（其中 12 个额外断言实质 DDS/Hold/诚实性契约短语）、
  1 个 env 单一真源交叉检查（含双链真值 42/0 与 `CYCLONEDDS_URI` unset）、1 个冻结路径字面量
  防回潮、2 个直接跑 `load.py print-a/print-b` 锁定双链可执行真源的用例、1 个全量 stdout
  指纹回归用例（#17，见下节）、1 个 frozen-path guard 的负向自测用例（#18）、1 个双链 env
  交叉断言 guard 的负向自测用例（#19）、1 个 Unitree Cyclone 交换裁决 guard 的负向自测用例
  （#20）、1 个 ros2-source-map guard 的负向自测用例（#21），以及 1 个 Executor/WaitSet map
  guard 的负向自测用例（#22，均见下文专节）：

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
