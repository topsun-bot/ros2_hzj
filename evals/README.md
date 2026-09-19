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
| `promptfooconfig.yaml` | 评估配置：1 个 custom provider + 19 个 seed 用例 |
| `localScriptProvider.mjs` | custom provider（`local-script`）：`python3 <prompt>`（prompt 可带空格分隔的 CLI 参数），返回 stdout；非 0 退出即 `error` |
| `fingerprint_check.py` | stdout 指纹回归（eval-only，**不是** CI gate、不进 `run_all_gates`、无需 ci.yml 接线）：重跑 13 gate + `load.py print-a\|b`，把归一化后的完整 stdout 与 `fixtures/` 逐字节比对 |
| `frozen_guard_selftest.py` | frozen-path guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 里构造夹具，断言 guard 对每种违禁 `Path(...)` 形态必报、对允许提及不误报、豁免真源、`render()` 退出码正确 |
| `dual_chain_env_guard_selftest.py` | 双链 env 交叉断言 guard 的**负向自测**（eval-only，不是 CI gate、无需 ci.yml 接线）：在 `tempfile` 里造最小 `load.py`/`chain_*.sh`/wrapper 树，断言四类交叉检查对域漂移/shell 漂移/wrapper 伪造/import 写环境/`CYCLONEDDS_URI` 违规必报、对健康树与真实仓不误报 |
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
- **seed 用例**（19 个）：13 个 gate 健康标记（其中 12 个额外断言实质 DDS/Hold/诚实性契约短语）、
  1 个 env 单一真源交叉检查（含双链真值 42/0 与 `CYCLONEDDS_URI` unset）、1 个冻结路径字面量
  防回潮、2 个直接跑 `load.py print-a/print-b` 锁定双链可执行真源的用例、1 个全量 stdout
  指纹回归用例（#17，见下节）、1 个 frozen-path guard 的负向自测用例（#18），以及 1 个双链 env
  交叉断言 guard 的负向自测用例（#19，均见下文专节）：

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
