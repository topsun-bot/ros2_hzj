# CI / CD gates（Hold 阶段）

Status: **闸门先于自动化。** 本仓按 AI-native SDLC：先把结构 / 契约 / Hold 边界变成必绿检查，再谈更重的流水线。  
查阅日期：2026-09-12。决策背景：[feishu-middleware-adr.md](feishu-middleware-adr.md)（#25）、[cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md)（#23）。

工作流：[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)。三个 job **都必须绿**：`structure`、`contracts`、`boundary`。

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

---

## 1. 今天 CI 检查什么

触发：`push` 到 `main`，以及 `pull_request`（`opened` / `synchronize` / `reopened` / `labeled` / `unlabeled`）。  
权限：`contents: read` + `pull-requests: read`。同 PR / 同 ref 的进行中 run 会被取消。

| Job | 断言（与拆分前同一套，可再拆不可丢） |
|-----|--------------------------------------|
| **structure** | R0 文档路径存在（含 `feishu-middleware-adr.md`、`ros2-source-map.md`、`cn-jp-ros2-absorb.md`、本文、`latency-attribution.md`、`feishu-risk-matrix.md`、`feishu-executor-waitset.md`、`feishu-runtime-provenance.md`、`unitree-sdk2-dds-swap.md`、`feishu-three-chain-repro.md`、`feishu-sink-layers.md`、`feishu-dual-chain-baseline.md`、`feishu-dod-evidence.md`、`feishu-cega-bridge-hold.md`、`AGENTS.md`）；`scripts/prove_rmw.py`、`scripts/check_source_map.py`、`scripts/print_bench_gates.py`、`scripts/check_risk_matrix.py`、`scripts/check_executor_map.py`、`scripts/check_runtime_provenance.py`、`scripts/check_unitree_cyclone_swap.py`、`scripts/check_three_chain_repro.py`、`scripts/check_sink_layers.py`、`scripts/check_dual_chain_baseline.py`、`scripts/check_dod_evidence.py`、`scripts/check_cega_bridge_hold.py`、`vendor/MANIFEST.md`；vendor 六棵树是普通目录（不是 gitlink / 无 `.gitmodules`）；DimOS 双链拷贝路径；R1–R5 产物；bench README 列出的日期目录存在；`fastdds.xml` 仍写 `domainId>42`；`chain_a.sh` / `chain_b.sh` 契约字符串；`python3 scripts/check_source_map.py`（只读源码地图：引用路径存在，允许清单符号仍在；行号过期只警告）；`python3 scripts/print_bench_gates.py`（只读 bench 指针 / `STATUS: blocked`，**不**打印分位数）；`python3 scripts/check_risk_matrix.py`（只读 §9.4 层序 / Hold 标记，**不**打风险分）；`python3 scripts/check_executor_map.py`（只读 WaitSet / `rmw_wait` / take / callback 地图 + Humble `rcl*` 未 vendor；打印 `WaitSet -> callback: mapped`，**不**发明时延）；`python3 scripts/check_runtime_provenance.py`（只读 Humble underlay / overlay / vendor snapshot 钉扎；打印 `underlay != vendor snapshot`，**不**发明 SHA）；`python3 scripts/check_unitree_cyclone_swap.py`（只读 Unitree 0.10.2 vs vendor 11.0.1；打印 `drop-in: FAIL / wire: UNPROVEN`，**不**发明时延）；`python3 scripts/check_three_chain_repro.py`（只读 §13(2) 三条链复现状态：map ≠ reproduce + `STATUS: blocked`；打印 `three-chain repro: blocked (map only)`，**不**发明复现已跑）；`python3 scripts/check_sink_layers.py`（只读 app / rcl / rmw / DDS / executor / memory 的 Hold vs allowed；打印 `sink layers: mapped (Hold vs allowed)`，**不**改 XML）；`python3 scripts/check_dual_chain_baseline.py`（只读 §13(3) 双链契约 / 不重写 XML / SCOREBOARD pointer-only / 跨机 blocked / 《3》–《6》 Hold；打印 `dual-chain baseline: pointer only (no XML rewrite)`，**不**发明分位数）；`python3 scripts/check_dod_evidence.py`（只读 wiki3 §6.3 产品 DoD 诚实标记；打印 `dod evidence: unmet (blocked)`，**不**发明 PASS / PROVEN / 本机 measured-delta）；`python3 scripts/check_cega_bridge_hold.py`（只读 §13(4) Cega / Bridge Hold；打印 `§13(4) Cega / Bridge: Hold`，**不**接 Cega、**不**改 `dimos_bridge` 运行时） |
| **contracts** | `python3 config/env/load.py print-a\|print-b` 打印契约且 import **不**写 `os.environ`；`dds_topics.py` 常量；上表文档的相对链接可解析；`python3 scripts/prove_rmw.py` 在 **没有 ROS** 时仍 exit 0 并打印 `ROS not loaded` |
| **boundary** | 仅对 `pull_request` **失败**：diff 碰到冻结路径或明显引入 Agnocast / zenoh 的路径。`push` 到 `main` **只警告、不失败**（已合入历史不得被这道闸误杀） |

**本阶段不做**（仍 Hold，不要在本工作流加）：

- ROS / vendor Docker 编译（《太重；Hold》）
- 《3》bench 分数闭环 / 90%·LLM 打分
- 《4》Mac HIL / preprod
- 《5》Promptfoo
- 《6》安全审计 / CVE
- 改 [`config/fastdds.xml`](../../config/fastdds.xml) 或 [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) 的内容

跨机 UDP 仍 **blocked**（单机）。无假分位数。

### 1.1 Claude code review（advisory，不是闸门）

工作流：[`.github/workflows/claude-code-review.yml`](../../.github/workflows/claude-code-review.yml)。`anthropics/claude-code-action`（钉在 commit SHA，注释标 `v1.0.223`）在 `pull_request`（`opened` / `synchronize` / `reopened` / `ready_for_review`）上读 [AGENTS.md](../../AGENTS.md) + PR diff，把审查意见写进 action 自建的 **一条** tracking 评论（`track_progress: true` + `update_claude_comment` 工具）。审查重点：Hold 边界、诚实标记、脚本只读审阅、CI/文档一致性、一般代码质量。

- **只评论，不 approve / request changes / merge。** 人类批准 merge 不变（§5）。
- **不要**把 `claude-review` 设为 required status check。三个闸门仍是 `structure` / `contracts` / `boundary`。
- 跳过 draft PR 与 fork PR（fork 拿不到 secret）。
- 需要 secret `ANTHROPIC_API_KEY`。缺 secret 时该 job 红，但不影响三个闸门。
- 权限：`contents: read`、`pull-requests: write`、`id-token: write`。额外工具白名单**只有** `gh pr view` / `gh pr diff`（带显式 PR 号 + `--repo`；checkout 是 detached HEAD，不能靠当前分支推断 PR）。**不放** `gh pr comment`：它接受 `--body-file`，prompt injection 可让模型把本地任意文件贴出去；评论只走固定参数的 `update_claude_comment`。
- **不执行 PR 检出里的任何代码**（不跑 `python3 scripts/*`、不跑 `config/env/load.py`）：该 job 持有 API key / 写权限 token / OIDC token，而检出内容由 PR 控制。脚本正确性只靠读；真正执行留给无 secret 的 `structure` / `contracts` job。
- `actions/checkout` 用 `persist-credentials: false`，token 不落 `.git/config`。
- **信任边界**：`pull_request` 工作流的 YAML 取自 PR merge ref，同仓 PR 可以改这个文件本身。job 跑在 GitHub Environment **`claude-review`** 里：把 `ANTHROPIC_API_KEY` 放到该 environment（而不是仓库级）并按需加 protection rules（required reviewers / 限定分支），就得到比「有 push 权限」更强的审批边界。不加 rules 时 environment 是透明的，行为同仓库级 secret。
- 升级 action 时改 SHA 并更新注释里的版本号；不要回到可变 tag。

---

## 2. Hold 政策

《1》《2》已落地（文档 + 证明脚本 + vendor/结构）。《3》–《6》 **Hold**。

| 禁止（无 bypass） | 说明 |
|-------------------|------|
| 改 `config/fastdds.xml` | 链 A 契约种子（iter7）。内容冻结 |
| 改 `docs/artifacts/bench/SCOREBOARD.md` | 已记账 current best。内容冻结 |
| 路径名带 `agnocast` / `zenoh` | 包括 `vendor/agnocast`、`rmw_zenoh`、kmod / heaphook 树。文档**正文**提到这些词不算；只看 **路径** |
| 启用 Agnocast / zenoh | 不 vendor、不装 kmod、不把 `ZenohTransport` stub 当可用路径 |

现有文档可以继续写 Agnocast / zenoh 对照（[cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md)、ADR）。那不是「引入」。

`dimos_bridge` DDS 行为与 `vendor/` 源码本闸门不逐字节审；政策仍是 **不要改**。中间件行为补丁、对照编译 vendor，仍 Hold。

---

## 3. 边界守卫怎么跑

`boundary` 在 PR 上 `git fetch` base SHA（`actions/checkout@v4` + 足够看见 PR base 的 fetch），然后 `git diff --name-status` base…HEAD（含 rename 两侧）。

命中则失败，除非该 PR 带标签 **`allow-hold-bypass`**。加/摘标签会重跑工作流。

`push` 到 `main`：打印 warn-only，**exit 0**。

---

## 4. 罕见 bypass：`allow-hold-bypass`

只在人类明确批准「这一刀必须动冻结面」时使用。Agent **不得**自己贴这个标签当默认出路。

1. 人类在 PR 上加 `allow-hold-bypass`。
2. `boundary` 仍会列出本会失败的路径，但不因此红。
3. 其它 job（`structure` / `contracts`）照常必须绿。
4. 合入后应摘标签；下一次 PR 默认重新上闸。

没有该标签时，动 XML / SCOREBOARD / Agnocast·zenoh 路径 = CI 红。

---

## 5. Branch protection

期望：`main` **要求本工作流绿才能合**。在 GitHub 里把 `structure`、`contracts`、`boundary` 设为 required status checks（Ruleset「Require status checks」或经典 Branch protection）。

- 不要只保护其中一个 job。
- Agent 可以做到 **merge / production 闸门之前**（开 PR、推提交、等 CI、修红）。
- **人类批准 merge**。本仓不自动合入。

---

## 6. 本地核对

仓库根：

```bash
# structure（概念上等同 CI；按需抽查路径）
test -f docs/architecture/feishu-middleware-adr.md
test -f docs/architecture/ros2-source-map.md
test -f docs/architecture/ci-cd-gates.md
test -f docs/architecture/latency-attribution.md
test -f docs/architecture/feishu-risk-matrix.md
test -f docs/architecture/feishu-executor-waitset.md
test -f docs/architecture/feishu-runtime-provenance.md
test -f docs/architecture/unitree-sdk2-dds-swap.md
test -f docs/architecture/feishu-three-chain-repro.md
test -f docs/architecture/feishu-sink-layers.md
test -f docs/architecture/feishu-dual-chain-baseline.md
test -f docs/architecture/feishu-dod-evidence.md
test -f docs/architecture/feishu-cega-bridge-hold.md
test -f AGENTS.md
test -f scripts/prove_rmw.py
test -f scripts/check_source_map.py
test -f scripts/print_bench_gates.py
test -f scripts/check_risk_matrix.py
test -f scripts/check_executor_map.py
test -f scripts/check_runtime_provenance.py
test -f scripts/check_unitree_cyclone_swap.py
test -f scripts/check_three_chain_repro.py
test -f scripts/check_sink_layers.py
test -f scripts/check_dual_chain_baseline.py
test -f scripts/check_dod_evidence.py
test -f scripts/check_cega_bridge_hold.py
test -d vendor/Fast-DDS && test ! -e vendor/Fast-DDS/.git
python3 scripts/check_source_map.py
python3 scripts/print_bench_gates.py
python3 scripts/check_risk_matrix.py
python3 scripts/check_executor_map.py
python3 scripts/check_runtime_provenance.py
python3 scripts/check_unitree_cyclone_swap.py
python3 scripts/check_three_chain_repro.py
python3 scripts/check_sink_layers.py
python3 scripts/check_dual_chain_baseline.py
python3 scripts/check_dod_evidence.py
python3 scripts/check_cega_bridge_hold.py

# contracts
python3 scripts/prove_rmw.py
python3 config/env/load.py print-a
python3 config/env/load.py print-b
```

`import` `config/env/load.py` **不会**改 `os.environ`。未 `source` / apply 时不要假设域 42 已生效。

`prove_rmw.py` 在无 ROS 的机器上应 exit 0，并含 `ROS not loaded`。**不要**为了本地绿去编译 vendor。

---

## 7. 相关文档

- [feishu-middleware-adr.md](feishu-middleware-adr.md) — 飞书三份中间件计划 → 本仓已决
- [cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md) — 中日公开做法对照（权威吸收文，不落旋钮）
- [ros2-source-map.md](ros2-source-map.md) — publish / History / callback 地图
- [feishu-executor-waitset.md](feishu-executor-waitset.md) — wiki3 §13 WaitSet → callback 身份地图（Humble `rcl*` 不在 vendor）
- [feishu-runtime-provenance.md](feishu-runtime-provenance.md) — wiki3 §13 underlay vs overlay vs vendor snapshot（Humble ≠ rolling）
- [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) — Unitree bundled 0.10.2 vs vendor 11.0.1（drop-in FAIL / wire UNPROVEN；default bundled；合法路径 `unitree_sdk2_hzj` + `UNITREE_DDS_PROVIDER=external`）
- [feishu-three-chain-repro.md](feishu-three-chain-repro.md) — wiki3 §13(2) 三条链复现（map ≠ reproduce；本主机 `STATUS: blocked`）
- [feishu-sink-layers.md](feishu-sink-layers.md) — 《通信中间件》app / rcl / rmw / DDS / executor / memory（Hold vs allowed；不改 XML）
- [feishu-dual-chain-baseline.md](feishu-dual-chain-baseline.md) — wiki3 §13(3) FastDDS + Cyclone 基线指针（不重写 XML；SCOREBOARD pointer only；same-topology XML tuning is paused）
- [feishu-dod-evidence.md](feishu-dod-evidence.md) — wiki3 §6.3 产品 DoD（`DoD: unmet` / `STATUS: blocked`；`prove_rmw` = env / 字符串，不是 modified `.so`）
- [feishu-cega-bridge-hold.md](feishu-cega-bridge-hold.md) — wiki3 §13(4) Cega / Bridge 后置 Hold（不接 Cega，不改 `dimos_bridge` 运行时）
- [latency-attribution.md](latency-attribution.md) — wiki3 §12 分段公式 × 双链（不抄 SCOREBOARD 数字）
- [feishu-risk-matrix.md](feishu-risk-matrix.md) — wiki3 §9.4 层序 × Hold（不打风险分）
- [ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md) — 双链契约
- [AGENTS.md](../../AGENTS.md) — agent 一页纸
