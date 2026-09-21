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
| `promptfooconfig.yaml` | 评估配置：1 个 custom provider + 37 个 seed 用例 |
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
| `dual_chain_env_load_selftest.py` | 双链环境**真源** `config/env/load.py` 的契约/负向自测（eval-only，不是 CI gate、无需 ci.yml 接线；区别于 #19 测 guard 检测假夹具）：钉 `describe` 返回精确 Chain A/B 契约值（fastrtps/42/fastdds.xml 绝对路径、cyclone/0）、未知 chain 抛 `ValueError`、未知 CLI 子命令 argparse exit 2、Chain B `apply` 必 `unset CYCLONEDDS_URI`（预置外部 URI 必须被删除）、`export_shell` 单引号转义可被 POSIX shell 原样 round-trip、import 不改 `os.environ`（import 纯净）；`apply` 只 update 不 pop 的盲桩会让 CYCLONEDDS_URI 泄漏（恢复后抓回）。进程内 apply 快照/恢复、CLI 与 import 纯净走隔离子进程 |
| `repo_helper_selftest.py` | 共享 gate helper `scripts/_repo.py`（7 个函数）**自身契约**自测（eval-only，不是 CI gate、无需 ci.yml 接线）：11 个 guard 自测只钉消费 helper 的 gate、#29 仅把 `_repo.py` 列为非 gate 库，helper 自身分支此前零断言；本项 import 真实 `_repo`，钉 `repo_root` 无 anchor 抛 ValueError/两处无 anchor 非零退出/cwd 同名 anchor 优先于 scripts 回退、`read_utf8` 非法字节 lenient、`line_at` 首/中/末/换行边界、`emit_render` 退出码透传、缺失文件与 FAIL 块逐字渲染；tempdir+chdir（必恢复）、纯内存渲染 |
| `doc_link_selftest.py` | 本循环所写文档（`docs/refactor/**.md`、`evals/**.md`）的 **markdown 相对链接完整性**自测（eval-only，不是 CI gate、无需 ci.yml 接线）：CI contracts 只对固定白名单 `test -f`、不解析链接且不含这两个目录，source_map/executor_map 只解析两份架构图；本项剥离围栏/行内代码后，要求每个相对 `[text](target)` 链接不越出仓库根且目标在磁盘存在（文件或目录）；external/锚点/mailto 跳过；缺失同级文件、`../` 越界、缺失目录必报，真实目标被强制判失也必报（非恒真） |
| `eval_registry_selftest.py` | Promptfoo **eval 套件自身注册面**的一致性自测（eval-only，不是 CI gate、无需 ci.yml 接线）：与 #29（钉 gate runner 注册面 vs scripts/）对称，本项钉 promptfoo 注册面——磁盘 `evals/*_selftest.py` ↔ yaml `script:` 引用双向一致（无 orphan 自测、无引用已删脚本）、每个 yaml script 路径磁盘存在、每 case 恰一个 script、固定严格层 fingerprint_check.py 必须在册、每个 evals 自测（含 fingerprint_check）的 SUCCESS/STABLE marker 必须在 yaml 被 `value:` 断言（防登记脚本却不断言成功路径的放水）、README 两处标题用例数等于 yaml case 数；读真实仓库，负向用内存变异（新增 orphan/缺失路径/计数漂移/删 marker 断言），无 tempdir 文件 |
| `dual_chain_env_wrapper_selftest.py` | DimOS 薄包装 `dimos_bridge/dual_chain_env.py`（importlib 再导出 load.py）的契约/负向自测（eval-only，不是 CI gate、无需 ci.yml 接线）：#32 钉 load.py 本体、#19 钉读 shell 的 guard，本项钉中间薄包装层——CHAIN_A/CHAIN_B 必须是真源**同一对象**（重导出而非复制常量，防漂移）、chain_a_env/chain_b_env 委托 describe 且返回 fresh dict（调用方改不到常量）、`_ENV_PY` 解析到 config/env/load.py、`__all__` 恰 6 项；import 包装不得改 os.environ；apply_chain_b 必须转发 unset 删除预置 CYCLONEDDS_URI、apply_chain_a 设置 Chain A 三元组；真源 load.py 缺失时包装形态 import 必失败；盲委托（apply 不传 unset）泄漏 URI 而真实包装删除（mutation）。进程内 apply 用 env 快照恢复，纯净/缺源走隔离子进程，tempdir only |
| `local_script_provider_selftest.py` | promptfoo **local-script provider 自身**（`localScriptProvider.mjs`）的契约/负向自测（eval-only，不是 CI gate、无需 ci.yml 接线）：provider 是 #12–#32 全部用例的执行器，非零退出必须转成 promptfoo `error`（负向 eval「exit1→case fail」的根基）。python 主体在 tempdir 写 Node harness、经 file:// URL import 真实 .mjs provider 并跑临时 python 夹具：钉 id=`local-script`、空/纯空白 prompt→empty error、exit1→`exited with code 1` 且 output 含 stdout+stderr、缺失脚本（python3 exit2）→`exited with code 2`、成功 output 仅 stdout（stderr 不得污染 contains/指纹）、argv 空白拆分 + cwd=repoRoot；盲 provider（catch 不返回 error）吞掉非零退出会漏报、真实 provider 报 error（mutation 可区分）。不在树内建 fixture、不编辑仓库 |
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
- **seed 用例**（37 个）：13 个 gate 健康标记（其中 12 个额外断言实质 DDS/Hold/诚实性契约短语）、
  1 个 env 单一真源交叉检查（含双链真值 42/0 与 `CYCLONEDDS_URI` unset）、1 个冻结路径字面量
  防回潮、2 个直接跑 `load.py print-a/print-b` 锁定双链可执行真源的用例、1 个全量 stdout
  指纹回归用例（#17，见下节）、1 个 frozen-path guard 的负向自测用例（#18）、1 个双链 env
  交叉断言 guard 的负向自测用例（#19）、1 个 Unitree Cyclone 交换裁决 guard 的负向自测用例
  （#20）、1 个 ros2-source-map guard 的负向自测用例（#21）、1 个 Executor/WaitSet map
  guard 的负向自测用例（#22）、1 个产品 DoD 诚实性 guard 反伪造逻辑的负向自测用例（#23）、
  1 个 Cega / Bridge Hold guard 独有解析的负向自测用例（#24）、1 个 runtime-provenance
  guard 的 Humble 钉版与 VERSIONS 同行 SHA 解析器负向自测用例（#25），以及 1 个 sink-layers
  guard 的六层表格行首标签锚定解析器负向自测用例（#26），以及 1 个 three-chain 复现 guard 独有的 `map = reproduce` / `three-chain repro: PROVEN` 伪造正则负向自测用例（#27），以及 1 个 bench-gates guard 的跨机占位目录存在性与 `STATUS: blocked` 正则扫描负向自测用例（#28），以及 1 个 gate-runner 注册表（磁盘 gate ↔ run_all_gates.GATES）双向一致性自测用例（#29），以及 1 个 gate-runner 执行判定语义（exit 0 且打印 marker 才算过；exit0 缺 marker / 非零退出 / 脚本缺失 127 必 FAIL；stderr marker 合并判定）负向自测用例（#30，与 #29 同属 runner 而非 guard），以及 1 个 stdout 指纹严格层 #17 自身的负向自测（live≠fixture drift / 缺 fixture / 命令非零 / `--update` 拒绝失败命令必 FAIL、绝对路径归一化 `<REPO_ROOT>` 防误报、normalize 盲桩漏报 drift）用例（#31，对象是 fingerprint_check 工具而非 gate），以及 1 个双链环境真源 load.py 自身的契约/负向自测（describe 精确契约 / 未知 chain ValueError / 未知子命令 exit 2 / Chain B apply 必 unset CYCLONEDDS_URI / shell 转义 round-trip / import 纯净 / apply 不 pop 泄漏变异）用例（#32，对象是 env 真源而非 #19 的 guard），以及 1 个 local-script provider 自身的契约/负向自测（空/空白 prompt error、exit1 透传 error+stdout/stderr、缺失脚本 code2、成功 output 仅 stdout、argv 拆分/cwd、盲 provider 吞非零退出变异）用例（#33，对象是 promptfoo 执行器 .mjs 本身，python 经 tempdir Node harness 桥接），以及 1 个 DimOS 薄包装 dual_chain_env.py 再导出/委托的契约负向自测（同一对象重导出不复制、describe fresh dict、import 纯净、apply_chain_b 转发 unset 删 CYCLONEDDS_URI、缺源必失败、盲委托漏 unset 变异）用例（#34，对象是 load.py 真源与 DimOS 之间的薄包装），以及 1 个 Promptfoo eval 套件自身注册面一致性自测（磁盘 selftest↔yaml 双向无 orphan/missing、路径存在、一 case 一 script、fingerprint_check 在册、每个 PASS marker 被 yaml 断言、README 计数==yaml case 数；与 #29 gate 注册面对称）用例（#35，对象是 eval 套件注册面），以及 1 个文档相对链接完整性自测（docs/refactor 与 evals 文档的相对 markdown 链接必须在磁盘解析、不越界、代码块内伪链接不扫）用例（#36，对象是文档链接同构面），以及 1 个共享 gate helper 自身契约自测（`scripts/_repo.py` 的 root 解析/退出/回退优先级、lenient 读取、行索引、退出码透传与 FAIL 逐字渲染）用例（#37，对象是共享 helper 底座，均见下文专节）：

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
| 32 | `evals/dual_chain_env_load_selftest.py` | `dual-chain env load selftest: PASS`、`3 negative, 2 non-flag, 1 healthy, 1 mutation`（未知 chain 必 ValueError、未知子命令必 exit 2、Chain B apply 必删 CYCLONEDDS_URI；shell 转义 round-trip 与 import 纯净防误报；apply 不 pop 盲桩泄漏 URI、恢复抓回） |
| 33 | `evals/local_script_provider_selftest.py` | `local-script provider selftest: PASS`、`3 negative, 2 non-flag, 1 healthy, 1 mutation`（空 prompt 必 error、exit1 必透传 error 且含 stdout/stderr、缺失脚本必 code 2；纯空白不绕过、成功 output 不含 stderr 防误报；盲 provider 吞非零退出漏报、真实 provider 报 error） |
| 34 | `evals/dual_chain_env_wrapper_selftest.py` | `dual-chain env wrapper selftest: PASS`、`3 negative, 2 non-flag, 1 healthy, 1 mutation`（import 不改 env、apply_chain_b 必删预置 CYCLONEDDS_URI、缺 load.py 必 import 失败；apply_chain_a 置 Chain A、describe 返回 fresh dict 防污染；CHAIN_A/B 与真源同对象、`_ENV_PY`/`__all__` 契约；盲委托漏 unset 泄漏、真实包装删除） |
| 35 | `evals/eval_registry_selftest.py` | `eval registry selftest: PASS`、`3 negative, 2 non-flag, 1 healthy, 1 mutation`（磁盘 selftest 未登记 yaml=orphan、yaml 引用磁盘缺失=missing、README 计数漂移必报；fingerprint_check.py 固定在册、每个自测/fingerprint 的 PASS marker 必被 yaml 断言；删某 marker 断言的变异必被检出） |
| 36 | `evals/doc_link_selftest.py` | `doc link selftest: PASS`、`3 negative, 2 non-flag, 1 healthy, 1 mutation`（缺失同级文件、`../` 越出仓库根、缺失目录链接必报；http/#锚点/mailto 跳过、围栏与行内代码内伪链接不扫；真实目标被 exists 包装强制判失必报；健康基线 5 个 md、165 个相对链接零断链） |
| 37 | `evals/repo_helper_selftest.py` | `repo helper selftest: PASS`、`3 negative, 2 non-flag, 1 healthy, 1 mutation`（`repo_root` 无参 ValueError、两处无 anchor 非零退出且文案含 cannot find repo root、缺失文件+FAIL 块逐字渲染必含 FAIL；空 bullet 不改、emit_render 透传 code 0 且写文本；非法字节 lenient replace、line_at 首/中/末/换行/单行边界；tempdir 同名 anchor 必须压过 scripts 回退证明非恒真） |

### 共享 gate helper 自身契约自测（#37，eval-only）

- `scripts/_repo.py` 是 11 个 gate 在《2》§5.3 重构中下沉到的**共享底座**（`repo_root` / `read_utf8` / `line_at` / `emit_render` / `append_bullets` / `report_missing_file` / `append_failures_block`）。#18–#28 的 guard 自测只钉**消费**这些 helper 的 gate，#29 仅把 `_repo.py` 列为"非 gate 库"用于注册面排除——helper 模块自身的分支/渲染契约此前**零直接断言**；底座一旦回归（root 解析到错目录、`emit_render` 吞掉非零退出码、FAIL 块丢标题）会同时静默削弱所有 gate。
- `repo_helper_selftest.py`（对象是**共享 helper 底座**，中缀 `repo_helper`；import **真实** `scripts/_repo.py`，文件系统分支用 tempdir + `os.chdir` 且 try/finally 必恢复 cwd，渲染 helper 纯内存；不改仓库、不是 gate、不进 GATES、不被 CI 枚举）：
  - **1 个健康对照**：cwd=真实仓库根时 `repo_root(AGENTS.md)` 返回真实 root、`scripts/_repo.py` 在其下，`read_utf8` 读到 AGENTS 首行，`line_at` 对自身源码 index 0 取首行一致；
  - **3 个负向**：N1 `repo_root()` 无参必须抛 `ValueError`（不得静默返回错目录）；N2 cwd 为空 tempdir、anchor 在 cwd 与 scripts 父目录都不存在时必须 `SystemExit` 非零且文案含 `cannot find repo root`；N3 `report_missing_file` 必须同时追加 failure 条目与 `- **FAIL missing:**` bullet，`append_failures_block` 必须以 `FAIL:` 开头、每条 failure 一个 `- ` bullet、尾空行（失败必须可见、逐字）；
  - **2 个 non-flag**：空 items 调 `append_bullets` 不得改动列表，`emit_render(("...",0))` 必须返回 0 且把文本写到 stdout；`read_utf8` 遇非法 UTF-8 字节必须 lenient replace 不抛，`line_at` 在首行/中间行/末行/换行符 index/单行无换行五种边界正确；
  - **1 个变异**：在 tempdir 放一个与真实 root **同名**的 anchor（`AGENTS.md`）并 chdir 过去，`repo_root` 必须返回 tempdir（cwd 优先于 scripts 父回退），证明它不是恒返回 scripts 父目录。
- 与 #18–#36 一样放在 `evals/` 下，eval-only、纯标准库；不重复各 guard 的业务断言，只钉共享底座自身契约。

### 文档相对链接完整性自测（#36，eval-only）

- CI `contracts` job 只对固定白名单做 `test -f`（**不解析** markdown 链接，且白名单不含 `docs/refactor/**` 与 `evals/**`）；`scripts/_md_paths.py` 的 `parse_map` 虽解析引用，但只服务 `check_source_map.py` / `check_executor_map.py` 两份特定架构图，且把反引号 `` `path` `` 也当引用（配 allowlist），与「纯 markdown 链接存在性」是不同职责。
- 因此本循环每轮产出的文档——`docs/refactor/01-dds-request-flow.md`、`02-modernization-plan.md`、`ITERATION_LOG.md` 与 `evals/README.md`、`evals/results/BASELINE.md`——共约 165 个相对链接（`../../scripts/...`、`../architecture/...`、同目录 `ITERATION_LOG.md` 等），其目标是否仍存在**此前零机器检查**；重命名/移动文件不更新链接会静默腐烂。
- `doc_link_selftest.py`（对象是**文档链接同构面**，中缀 `doc_link`；纯标准库，读**真实仓库**做健康对照，负向用**内存注入链接**、不写 tempdir、不改仓库）：先剥围栏代码块（```` ``` ````）与行内代码（`` `...` ``），避免正则片段/命令样例里的 `](...)` 被误判；再对每个 inline/图片链接分类——external（http/https/mailto/`#锚点`/`<...>`/web 根绝对路径）跳过，相对路径相对当前 md 目录解析，越出仓库根报 `escapes repo root`、目标（文件或目录，允许末尾 `/`）不存在报 `missing target`。
  - **1 个健康对照**：真实仓库 5 个 md、≥100 个相对链接、零断链（设文件数/链接数下限，防 glob 失效导致空扫恒真）；
  - **3 个负向**：注入缺失同级文件链接必报 missing；注入 `../../../../` 越界链接必报 escape；注入缺失目录（末尾 `/`）链接必报 missing；
  - **2 个 non-flag**：external/锚点/mailto 链接一律不检查；围栏代码块与行内代码中的伪 `](x.md)` 链接不被扫描；
  - **1 个变异**：用 exists 包装把一个真实存在的目标强制判失，必被报 missing，证明检查非恒真。
- 与 #18–#35 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线；不重复 source_map/executor_map 的反引号引用 + 符号 allowlist 检查。

### Promptfoo eval 套件注册面一致性自测（#35，eval-only）

- #29（`gate_registry_selftest.py`）钉的是 **gate runner 注册面**：磁盘 gate 脚本 ↔ `run_all_gates.GATES` 双向一致，防 orphan gate / GATES 指向已删脚本在绿色头条下隐身；其 scope note 明确只对 `scripts/`，不覆盖 eval 侧。Promptfoo 套件存在**对称的注册面**，此前零机器断言：磁盘 `evals/*_selftest.py`、yaml `evals/promptfooconfig.yaml` 的 `script:` 引用、`evals/README.md` 的标题用例数三者可能漂移。
- 漂移是静默且真实的：新增自测忘登记 yaml → promptfoo 永不运行它（**假绿**）；yaml case 指向已删脚本只在运行时才炸；登记了脚本却不对其 PASS marker 做 contains 断言 → case 不证明脚本成功路径（断言放水）；README 计数与 yaml case 数不符无人拦。
- `eval_registry_selftest.py`（对象是 **eval 套件注册面**，中缀 `eval_registry`；纯标准库，读**真实仓库**做健康对照，负向用**内存变异**注入——不写 tempdir、不改仓库）：
  - **1 个健康对照**：真实仓库零注册问题（磁盘 selftest 集合 == yaml evals selftest 引用集合双向；每个 yaml script 路径磁盘存在；case 数 == script 行数；fingerprint_check.py 在册；每个 evals 自测 + fingerprint_check 的 SUCCESS/STABLE marker 都在 yaml 被 `value:` 断言；README 两处标题计数 == yaml case 数）；
  - **3 个负向**：N1 磁盘多一个 `zzz_orphan_selftest.py`（yaml 未引用）必报 orphan；N2 yaml 追加一个指向不存在脚本的 case 必报 missing on disk（同时带 description 保持一 case 一 script 中性）；N3 README 标题计数改成 99 必报 count drift；
  - **2 个 non-flag**：固定严格层 `evals/fingerprint_check.py` 必须始终在册（#17 不能掉）；磁盘每个自测（≥17）与 fingerprint_check 的成功 marker 必须在 yaml 有断言（NF 健康面）；
  - **1 个变异**：把 yaml 文本中 frozen 自测的 PASS marker 断言内存替换为错误串，必被检出「marker not asserted」，证明 marker 检查非恒真。
- **范围边界（刻意不钉）**：README 逐用例明细表早期行（#1–#16 的 gate/load 用例）列格式不统一、非单一机器稳定结构，故不绑定其编号连续性；总量由两处标题计数、每个 selftest 由磁盘↔yaml 集合双向覆盖，已足够防漏登/假绿。本项不重复 #29 对 `scripts/` gate 注册面、#30 对 runner 执行裁决的断言。
- 与 #18–#34 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线。

### 双链环境薄包装 dual_chain_env.py 契约/负向自测（#34，eval-only）

- `dimos_bridge/dual_chain_env.py` 是 DimOS 侧读取双链环境契约的**薄包装**：docstring 声明 `config/env/load.py` 是唯一可执行真源，本模块只用 importlib 重新导出、不得复制常量；模块级再导出 `CHAIN_A/CHAIN_B`，提供 `chain_a_env()/chain_b_env()`（委托 `describe`）与 `apply_chain_a()/apply_chain_b()`（委托 `apply`，其中 Chain B 必须传 `unset=CHAIN_B_UNSET`）。#32 钉了 load.py 本体、#19 钉了读 shell 脚本的 guard，但中间这层薄包装此前零断言：复制常量会与真源漂移、`apply_chain_b` 漏传 unset 会让外部 `CYCLONEDDS_URI` 污染 Chain B、import 包装可能误写 `os.environ`、真源缺失可能被静默吞掉。
- `dual_chain_env_wrapper_selftest.py`（对象是**薄包装层**，中缀 `dual_chain_env_wrapper` 区别于 #19 的 `dual_chain_env_guard` 与 #32 的 `dual_chain_env_load`；纯标准库，进程内 `apply_*` 用 env 快照始终恢复，import 纯净/缺源失败走隔离子进程，坏包装夹具写 tempdir、不在树内建文件）：
  - **1 个健康对照**：`CHAIN_A/CHAIN_B` 与包装内部已加载真源 `_env.CHAIN_A/B` 是**同一对象**（`is`，重导出而非复制）；`chain_a_env()/chain_b_env()` 等于真源常量（describe 委托）；`_ENV_PY` 解析到仓库 `config/env/load.py` 且存在；`__all__` 恰为 6 个导出名；
  - **3 个负向**：N1 隔离子进程 import 包装前后 `RMW_IMPLEMENTATION/ROS_DOMAIN_ID/FASTRTPS_DEFAULT_PROFILES_FILE/CYCLONEDDS_URI` 必须无变化（模块级纯净、不得 apply）；N2 预置 `CYCLONEDDS_URI` 后 `apply_chain_b()` 必删除它（unset 必须转发），且置 RMW=Cyclone、DOMAIN=0；N3 与包装同构但 `load.py` 指向不存在文件的 tempdir 模块，import 必须非零失败（`FileNotFoundError`/No such file），不得静默成功；
  - **2 个 non-flag**：`apply_chain_a()` 置 Chain A 三元组（rmw_fastrtps_cpp / 42 / fastdds.xml）；`chain_a_env()` 每次返回 fresh dict、既非常量本体也非同一对象（调用方 mutate 污染不到模块常量），但值等于常量；
  - **1 个变异**：盲委托 `load.apply(CHAIN_B)` 不传 unset 时预置 `CYCLONEDDS_URI` **泄漏**（sanity），而真实 `apply_chain_b()` 删除——证明本测试能抓住「薄包装漏传 unset」退化。
- **范围边界**：只钉薄包装的再导出同一性、委托接线与纯净/失败语义，不重复 #32 对 load.py 自身（describe/apply/export/CLI/import）的断言，也不重复 #19 对 shell 字面 export 的 guard；不修改包装行为（行为不变）。
- 与 #18–#33 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线。

### local-script provider 契约/负向自测（#33，eval-only）

- `evals/localScriptProvider.mjs` 是 promptfoo 的 custom provider（id `local-script`），也是 **#12–#32 全部用例的执行器**：把 prompt 按空白拆成 argv 用 `python3` 跑、cwd=repoRoot，exit 0 返回 stdout 作为 `output`，**exit 非 0 必须设置 `error`**，promptfoo 才会把该 case 判失败。#18–#32 的负向自测脚本内部 exit 1 能否真的在 promptfoo 里标红，完全依赖这条「非零→error」透传；但此前 provider 自身零断言。
- `local_script_provider_selftest.py`（对象是 **provider .mjs 执行器本身**；provider 硬编码 python3、无法被 python3 provider 直接执行，故 python 主体在 tempdir 写一个 Node harness，经 `file://` URL import 真实 provider、再跑 tempdir 内一次性 python 夹具，结果以 JSON 回传断言；不在树内建 fixture、不编辑仓库；需要 `node`——promptfoo 本身也依赖 node）：
  - **3 个负向**：N1 空 prompt 必返回 error（`empty prompt ...`）且 output 为空串；N2 夹具 exit 1 必返回 error 含 `exited with code 1`，且 output 同时含 stdout（`OUT-LEAD`）与 stderr（`ERR-DETAIL`）；N3 缺失脚本（python3 自身 exit 2）必返回 error 含 `exited with code 2`，不得静默成功；
  - **2 个 non-flag**：纯空白 prompt（`'   \t '`）经 trim/split/filter 后同样命中 empty error（不得靠空白绕过）；exit 0 但往 stderr 写内容的脚本必须**无 error** 且 output 只含 stdout（`CLEAN-OUT`）、**不含** stderr（`NOISE-STDERR`），防止 stderr 污染 contains 断言与 stdout 指纹；
  - **1 个健康对照**：`id()=='local-script'`，且 `config/env/load.py print-a`（带参数）exit 0、无 error、stdout 含 Chain A 契约（证明 argv 空白拆分传参与 cwd=repoRoot）；
  - **1 个变异**：内联定义一个 catch 里不返回 error 的「盲 provider」，其对 exit 1 夹具**漏报**（hasError=false，sanity 自检），而真实 provider 对同一夹具报 error——证明本测试能区分「吞掉非零退出」的退化。
- **范围边界**：只钉 provider 的 prompt→argv→exit 裁决与 output/error 通道，不重复各 selftest 对 guard/runner/工具自身判定逻辑的断言；不修改 provider 行为（行为不变）。
- 与 #18–#32 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线。

### 双链环境真源 load.py 契约/负向自测（#32，eval-only）

- `config/env/load.py` 是双链环境变量的**唯一真源**（Chain A = rmw_fastrtps_cpp / domain 42 / config/fastdds.xml；Chain B = rmw_cyclonedds_cpp / domain 0 且 `CYCLONEDDS_URI` 必须 unset）。#19（`dual_chain_env_guard_selftest.py`）只证明 guard `check_dual_chain_env.py` 能识别被篡改的 shell 夹具，**从不钉 load.py 这个真源自身**；Mac HIL 里 print/import 纯净是文档叙述、不是可执行回归。
- `dual_chain_env_load_selftest.py`（对象是 **env 真源工具本身**，区别于 #19 的 guard；纯标准库、不编辑仓库：进程内 `apply` 用快照在退出时恢复 `os.environ` 与函数本身，CLI/import 纯净走隔离子进程）：
  - **3 个负向**：N1 `describe("z")` 必抛 `ValueError: unknown chain: z`（未知链不得静默返回空/错配置）；N2 未知 CLI 子命令必 argparse **exit 2**（不得当成功）；N3 Chain B `apply` 必须 **pop 掉预置的 `CYCLONEDDS_URI`**（跳过 unset 会让外部 Cyclone URI 污染 Chain B），且 B 不得带 FastDDS profiles 文件；
  - **2 个 non-flag**：`export_shell` 对含单引号+空格的值 `a'b c` 必输出 `'a'"'"'b c'`，并用 `/bin/sh -c` eval 回读证明 POSIX shell 原样 round-trip（防错误/不可解析的 export）；全新解释器 `import load` 前后 `os.environ` 完全一致（import 纯净、不得隐式 apply）；
  - **1 个健康对照**：`describe('a'/'b')` 返回精确契约 dict（含 fastdds.xml 绝对路径且文件存在），六个子命令 print-a/print-b/export-a/export-b/apply-a/apply-b 均 exit 0 且输出关键契约串；
  - **1 个变异**：把 `apply` 换成「只 `os.environ.update`、不做 unset pop」的盲桩 → Chain B 下预置 `CYCLONEDDS_URI` 泄漏（断言能观察到泄漏以自检）；恢复真实 `apply` 后该 URI 被删除。
- **范围边界**：只钉 load.py 真源的 describe/apply/export/CLI/import 语义，不重复 #19 对 guard 解析 shell 夹具能力的断言，也不改 shell 包装 `chain_a.sh`/`chain_b.sh`（其字面 export 串由 #19 guard 锚定）。
- 与 #18–#31 一样放在 `evals/` 下，**不是** gate、不进 `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线。

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
