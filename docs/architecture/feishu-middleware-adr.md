# ADR：飞书三份中间件计划对照本仓

Status: **已决 — 本切只落地文档 + 证明脚本，不改 XML / 不自研 RMW。**  
查阅日期：2026-09-12。三份飞书是决策来源；本仓动作以**已有双链契约**为准，不把飞书当现场根因。

| 飞书 | URL | 对本仓的可执行结论 |
|------|-----|-------------------|
| 《通信中间件》 | https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe | ROS 2 是生态底座。先评估 / 调优现有 RMW；只有收益可量化才自研。优选：业务仍走 ROS 2 API，DDS 用 RMW 接入，`RMW_IMPLEMENTATION` 切换，应用不感知。次优「上层再抽 module 双堆」**本仓不做**。 |
| Cyclone 工业级 fork 研究 | https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e | 高吞吐同机不要默认 Cyclone **网络**配置。Agnocast / eCAL / DPDK-XDP / `rmw_zenoh` / Unitree 控环剥离 DDS 是行业选型建议，**不是**本切交付。本仓映射见下表，**不 vendor**。 |
| 《ROS 2 源码闭环》 | https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf | 不重写整套中间件；差异化下沉到 RMW / DDS / Executor / 内存。执行顺序 §13、风险矩阵 §9.4、运行时证明 §6.3。**严禁** Rolling 源码直接覆盖 Humble。 |

本仓契约仍是两条独立栈：[R0 接口冻结](ros2-dds-r0-interface-freeze.md)。中日公开做法只对照、不落旋钮：[cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md)。NITROS 仍是同进程 GPU：[nitros-vs-dual-chain.md](nitros-vs-dual-chain.md)。vendor 语义冻结：[vendor/MANIFEST.md](../../vendor/MANIFEST.md)。运行时分层（underlay / overlay / vendor snapshot）：[feishu-runtime-provenance.md](feishu-runtime-provenance.md)。链路上的真实文件：[ros2-source-map.md](ros2-source-map.md)。三条链复现（**map ≠ reproduce**，`STATUS: blocked`）：[feishu-three-chain-repro.md](feishu-three-chain-repro.md)。Unitree 自带 Cyclone 0.10.2 **不是** vendor 11.0.1 的 drop-in：[unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md)。

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

---

## 1. 决策

**保持 ROS 2 应用 API。** 本切不发明自定义 RMW，不抽 module 双堆接口，不接 Cega，不 vendor Agnocast / zenoh / eCAL / DPDK / Isaac。

双链用**已有** `config/env` helper 切换（必须操作员显式 `source` / apply，import **不**改默认）：

| 链 | RMW / 实现 | 域 | 本仓开关 |
|----|------------|----|----------|
| **A** | `rmw_fastrtps_cpp` → Fast-DDS | **42** | [`config/env/chain_a.sh`](../../config/env/chain_a.sh)（`FASTRTPS_DEFAULT_PROFILES_FILE` → [`config/fastdds.xml`](../../config/fastdds.xml) 契约种子） |
| **B** | Cyclone（原生 DimOS DDS；ROS 侧名 `rmw_cyclonedds_cpp`） | **0** | [`config/env/chain_b.sh`](../../config/env/chain_b.sh)（默认 **不**设 `CYCLONEDDS_URI`） |

混用默认值是 **discovery 失败**，不是单栈时延 bug。应用代码继续写 `rclpy` / `ROSTransport` / `DDSTransport`，不感知底下换了哪份 `.so`。

《通信中间件》的「马后炮」在本仓的落点：对照编译 vendor、中间件行为补丁、把评测数字当根因，仍 **Hold**。先证明加载了哪个 RMW（§6.3 / [`scripts/prove_rmw.py`](../../scripts/prove_rmw.py)），再谈自研。

---

## 2. 飞书 §13 执行顺序 × 本切

《ROS 2 源码闭环》§13 的顺序，对到本仓**这一刀**做了什么、刻意没做什么：

| §13 | 飞书要求 | 本切 |
|-----|----------|------|
| (1) | 冻 `ROS_DISTRO` + exact manifest | [`vendor/MANIFEST.md`](../../vendor/MANIFEST.md)。运行时目标 = Humble（[`docker/ros/`](../../docker/ros/)）。vendor 树 = rolling / master 快照，SHA **只**在 [`vendor/VERSIONS.md`](../../vendor/VERSIONS.md)。分层记录：[feishu-runtime-provenance.md](feishu-runtime-provenance.md)。 |
| (2) | 复现 publish / ingress→History / wait→callback 三条链 | **map ≠ reproduce。** 地图：[ros2-source-map.md](ros2-source-map.md)。wait→callback 加深：[feishu-executor-waitset.md](feishu-executor-waitset.md)。复现状态：[feishu-three-chain-repro.md](feishu-three-chain-repro.md)（`STATUS: blocked`；本自动化主机无 Humble 运行时，未执行复现）。不编造 PASS / 时延。`publish()` 返回 **不是**端到端送达。 |
| (3) | FastDDS + Cyclone 基线 | 双链契约已在；bench 产物另册。本切 **不**重写 XML、**不**改 SCOREBOARD。 |
| (4) | Cega / Bridge 后置 | **Hold**。不接 Cega，不改 `dimos_bridge` 运行时模块。 |
| (5) | 一次一层 | 本切 = 文档 + 证明脚本 + CI 登记。下一层另开 PR。 |
| (6) | CI + 灰度 | 三个 required job 名不变：`structure` / `contracts` / `boundary`。路径 + 相对链接 + 现网检查器：`prove_rmw.py`、`check_source_map.py`、`print_bench_gates.py`、`check_risk_matrix.py`、`check_executor_map.py`、`check_runtime_provenance.py`、`check_unitree_cyclone_swap.py`、`check_three_chain_repro.py`。**不**编译 vendor。 |

§9.4 风险矩阵：DDS XML / 环境变量 **第一优先**（本切只读现网契约，不改 [`config/fastdds.xml`](../../config/fastdds.xml)）；Executor / WaitSet / callback **居中**（身份地图见 [feishu-executor-waitset.md](feishu-executor-waitset.md)，不是风险打分）；fork `rcl` / `rclcpp` / DDS core **最后**（本仓甚至没有 vendor `rcl` / `rclcpp`）。本仓清单：[feishu-risk-matrix.md](feishu-risk-matrix.md)。

---

## 3. 行业选型 → 本仓 Hold 映射

来自飞书 Cyclone fork 研究 + 室共识。**对照，不 vendor。** 奥比 / Autoware recv window / Loaned 数字表见 [cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md)，本文不重复。

| 选型 | 飞书 / 行业在说什么 | 本仓 |
|------|---------------------|------|
| 换 / 调优现有 RMW | 先量化，再谈自研 | 用 `RMW_IMPLEMENTATION` + `config/env`；无自定义 RMW |
| 自研 DDS 经 RMW 接入 | 应用不感知 | **未开始**；本切只冻契约与证明脚本 |
| 上层 module 双堆 | 《通信中间件》次优 | **不做** |
| Agnocast | 同机真零拷 IPC，不是 RMW | **Hold**（cn-jp 已写） |
| `rmw_zenoh` | 另一条 RMW | **Hold**；DimOS `ZenohTransport` 仍是空 stub |
| eCAL | 高吞吐同机替代网络 Cyclone | **Hold** |
| DPDK / XDP | 用户态包 I/O | **Hold** |
| Isaac / NITROS | 同进程 GPU | **Hold**（见 NITROS 对照） |
| Unitree 控环剥离 DDS | 控环不走导航 Fast-DDS | 已是链 B 原生 Cyclone 域 0，**不是**新 vendor。自带 0.10.2 **不能** drop-in 换成本仓 vendor 11.0.1：[unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) |
| Cyclone 默认网络 XML | 高吞吐同机不要当默认 | 链 B **不**设 `CYCLONEDDS_URI` |
| Cega | §13 后置 | **Hold** |

---

## 4. 硬闸门（本切与后续都适用）

| 闸门 | 状态 |
|------|------|
| 改 [`config/fastdds.xml`](../../config/fastdds.xml) / SCOREBOARD 已记账表 / current best | **禁止** |
| 跨机 UDP | 仍 **blocked**（单机 / yixin Docker DOWN）；无假分位数 |
| 《3》90%/LLM、《4》Mac/preprod、《5》Promptfoo、《6》CVE | 仍 **Hold** |
| Rolling / master vendor 文件直接覆盖 Humble 发行版树 | **严禁**（见 MANIFEST） |
| 自定义 RMW、Cega、Agnocast / zenoh / eCAL / DPDK / Isaac 进 `vendor/` | 本切 **不**做 |
| 改 `dimos_bridge` 运行时 Python 模块 | **禁止**（本切） |
| 飞书现场 / 实机根因 | **不是。** |
| 用 vendor Cyclone 11.0.1 drop-in / in-place overwrite Unitree SDK2 自带 0.10.2 `libddsc` / `libddscxx` | **FAIL**（主版本 / ABI）。默认保持 **bundled 0.10.2**。合法路径：[`unitree_sdk2_hzj`](https://github.com/topsun-bot/unitree_sdk2_hzj) + opt-in `UNITREE_DDS_PROVIDER=external`。线缆互通 **UNPROVEN**。见 [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) |

---

## 5. 引用

飞书（2026-09-12）：

1. 《通信中间件》：<https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>
2. Cyclone 工业级 fork 研究：<https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>
3. 《ROS 2 源码闭环》：<https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf>

本仓：

4. [ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md)
5. [cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md)
6. [nitros-vs-dual-chain.md](nitros-vs-dual-chain.md)
7. [ros2-source-map.md](ros2-source-map.md)
8. [feishu-risk-matrix.md](feishu-risk-matrix.md) — wiki3 §9.4 层序 × Hold（不打分）
9. [feishu-executor-waitset.md](feishu-executor-waitset.md) — wiki3 §13 wait→callback 身份地图
10. [feishu-runtime-provenance.md](feishu-runtime-provenance.md) — wiki3 §13 underlay vs overlay vs vendor snapshot
11. [feishu-three-chain-repro.md](feishu-three-chain-repro.md) — wiki3 §13(2) 三条链复现（map ≠ reproduce；`STATUS: blocked`）
12. [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) — Unitree 0.10.2 vs vendor 11.0.1（drop-in FAIL / wire UNPROVEN）
13. [vendor/MANIFEST.md](../../vendor/MANIFEST.md) · [vendor/VERSIONS.md](../../vendor/VERSIONS.md)
14. [config/env/README.md](../../config/env/README.md) · [scripts/prove_rmw.py](../../scripts/prove_rmw.py) · [scripts/check_source_map.py](../../scripts/check_source_map.py) · [scripts/print_bench_gates.py](../../scripts/print_bench_gates.py) · [scripts/check_risk_matrix.py](../../scripts/check_risk_matrix.py) · [scripts/check_executor_map.py](../../scripts/check_executor_map.py) · [scripts/check_runtime_provenance.py](../../scripts/check_runtime_provenance.py) · [scripts/check_unitree_cyclone_swap.py](../../scripts/check_unitree_cyclone_swap.py) · [scripts/check_three_chain_repro.py](../../scripts/check_three_chain_repro.py)
