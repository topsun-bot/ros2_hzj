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
| `promptfooconfig.yaml` | 评估配置：1 个 custom provider + 16 个 seed 用例 |
| `localScriptProvider.mjs` | custom provider（`local-script`）：`python3 <prompt>`（prompt 可带空格分隔的 CLI 参数），返回 stdout；非 0 退出即 `error` |
| `results/baseline_raw.txt` | 基线运行的原始终端输出 |
| `results/BASELINE.md` | 基线数字摘要 |

## 最小评估计划

- **目标适配器**：custom provider `local-script`（`evals/localScriptProvider.mjs`）。
  promptfoo 把它 `new` 出来，调用 `callApi(prompt)`；`prompt` 被约定为一个相对仓库根的
  python 脚本路径，可再跟空格分隔的 CLI 参数（如 `config/env/load.py print-a`）。
  provider 把 prompt 按空白拆成 argv，用 `execFileSync('python3', argv, { cwd: repoRoot })`
  执行，返回 `{ output: stdout }`；若脚本非 0 退出，返回 `{ output: stdout+stderr, error: ... }`，
  promptfoo 即把该 case 判为失败。
- **seed 用例**（16 个）：13 个 gate 健康标记（其中 12 个额外断言实质 DDS/Hold/诚实性契约短语）、
  1 个 env 单一真源交叉检查（含双链真值 42/0 与 `CYCLONEDDS_URI` unset）、1 个冻结路径字面量
  防回潮，以及 2 个直接跑 `load.py print-a/print-b` 锁定双链可执行真源的用例：

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
