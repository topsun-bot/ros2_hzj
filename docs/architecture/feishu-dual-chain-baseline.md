# 双链基线指针（飞书 wiki3 §13 (3)：FastDDS + Cyclone）

Status: **指针 — 不是重测、不是飞书现场、不是跨机根因。**  
对照飞书《ROS 2 源码闭环》<https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf> §13 第 (3) 步（FastDDS + Cyclone 基线）。另两份飞书计划（已在 ADR）：《通信中间件》<https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>、Cyclone 工业级 fork 研究 <https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>。

本环境打不开飞书 wiki 正文（登录墙 / 抓取失败）。本页章节对照**派生自**已合入 ADR [feishu-middleware-adr.md](feishu-middleware-adr.md) §13(3)、[SCOREBOARD.md](../artifacts/bench/SCOREBOARD.md) **页眉**（不抄表内分位数）、以及 [`config/env/chain_a.sh`](../../config/env/chain_a.sh) / [`config/env/chain_b.sh`](../../config/env/chain_b.sh)；**不是** Feishu field / 跨机证明，不阻塞等 wiki。双链契约：[ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md)。

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

---

## 0. 硬规则

1. **双链契约已在。** 两条**独立**栈，不共享域 / RMW / QoS，除非操作员显式对齐。混用默认值是 **discovery 失败**，不是单栈时延。
2. **本切不重写 XML。** [`config/fastdds.xml`](../../config/fastdds.xml) 是链 A **只读**契约种子（iter7）。**no XML rewrite** this cut.
3. **SCOREBOARD 只当 current-best pointer。** [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) 是 **pointer only**。本文与 CI **不**抄、不改、不重算那边的分位数。
4. **same-topology XML tuning is paused.** 同拓扑（`same-process` / `same-host`）再拧 XML 旋钮已暂停：SCOREBOARD 页眉写 leftover family **Forbidden to retry**；本切不发明新旋钮。
5. **跨机 UDP 仍 `STATUS: blocked`。** 单机 / 无第二台，禁止填假分位数。见 [`2026-09-11-cross-host/`](../artifacts/bench/2026-09-11-cross-host/README.md)。
6. **三条链仍是地图，不是复现。** wiki3 §13(2) publish / ingress→History / wait→callback = **three-chain map≠reproduce**。只认 [ros2-source-map.md](ros2-source-map.md) + ADR「只画地图」。
7. **Unitree 0.10.2 vs vendor 11.0.1 = drop-in FAIL。** 见 [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md)。线缆互通仍 UNPROVEN。
8. **《3》–《6》仍 Hold。** 《3》90%/LLM、《4》Mac/preprod、《5》Promptfoo、《6》CVE。Agnocast / zenoh / Cega / 自定义 RMW 仍 Hold。不改 `dimos_bridge` 运行时模块。

核对本页 + 双链契约脚本仍一致：[`scripts/check_dual_chain_baseline.py`](../../scripts/check_dual_chain_baseline.py)。  
核对「加载了哪个 RMW」：[`scripts/prove_rmw.py`](../../scripts/prove_rmw.py)。  
核对 bench 指针 / 跨机 STATUS：[`scripts/print_bench_gates.py`](../../scripts/print_bench_gates.py)。

---

## 1. 链 A — Fast-DDS / 域 42（只读契约）

运行时契约（必须操作员显式 `source` / apply；`import` **不**写 `os.environ`）：

| 项 | 契约 | 本仓落点 |
|----|------|----------|
| RMW | `rmw_fastrtps_cpp` | [`config/env/chain_a.sh`](../../config/env/chain_a.sh) |
| 域 | `ROS_DOMAIN_ID=42` | 同上；R0 冻结表导航域 |
| XML | [`config/fastdds.xml`](../../config/fastdds.xml) | `FASTRTPS_DEFAULT_PROFILES_FILE` 指向该文件。**只读**契约种子，不是 DimOS `main` 现网抽出 |

```mermaid
flowchart LR
  srcA["source chain_a.sh"] --> rmwA["rmw_fastrtps_cpp"]
  rmwA --> domA["ROS_DOMAIN_ID=42"]
  domA --> xmlA["fastdds.xml 只读"]
```

Humble 发行版 `.so` 才是默认加载对象。`vendor/rmw_fastrtps` / `vendor/Fast-DDS` 是对照阅读，不是链 A 已加载库。身份仍走 `prove_rmw.py`。

---

## 2. 链 B — Cyclone / 域 0（默认不设 URI）

运行时契约：

| 项 | 契约 | 本仓落点 |
|----|------|----------|
| RMW（ROS 侧名） | `rmw_cyclonedds_cpp` | [`config/env/chain_b.sh`](../../config/env/chain_b.sh) |
| 域 | Cyclone **域 0** / `ROS_DOMAIN_ID=0` | 与 DimOS `DDSConfig.domain_id` / Unitree `ChannelFactoryInitialize(0)` 对齐 |
| Cyclone XML | 默认 **不**设 `CYCLONEDDS_URI` | 本仓没有现网 Cyclone XML。高吞吐同机不要默认 Cyclone **网络**配置（ADR） |

原生 DimOS DDS 读的是 `DDSConfig.domain_id`（默认 0），不是这些 ROS 变量。`chain_b.sh` 只为「要用 ROS 2 RMW 对齐链 B」的操作员准备。

`vendor/rmw_cyclonedds` + `vendor/CycloneDDS`（发行标签 **11.0.1**）是对照阅读，不是链 B 已加载库。不要把链 A 与链 B 推进同一张对照表去比快慢。

---

## 3. SCOREBOARD = current-best pointer only

当前最佳配置 + 已记账 same-host 表只认 [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md)。

派生自该页**页眉**（查阅 2026-09-12；本文不打开表内数字）：

- Path B. Docs only. No new transport knob. `config/fastdds.xml` 仍是 **iter7 seed**。
- 该页是 current best config + best measured tables **指针**，**不**重测、**不**改中间件行为。
- leftover 旋钮家族（SIMPLE lease / WLP / `port_queue_capacity` / exclusive SHM 等）标 **Forbidden to retry**。
- 跨机 UDP 仍 `STATUS: blocked`（单机）。
- 《3》–《6》仍 **Hold**。

因此：**SCOREBOARD pointer only。** same-topology XML tuning is paused。本切 **no XML rewrite**，也 **不**改 SCOREBOARD 数字。

方法怎么分段（仍不抄数字）：[latency-attribution.md](latency-attribution.md)。历次日期索引：[`docs/artifacts/bench/README.md`](../artifacts/bench/README.md)。

---

## 4. 诚实标记（本切不假装已证明）

| 断言 | 状态 | 指针（不发明分位数） |
|------|------|----------------------|
| 双链契约 | **已在** | [R0](ros2-dds-r0-interface-freeze.md) · [`config/env/`](../../config/env/) |
| XML / SCOREBOARD 本切 | **不重写 / 不改数字** | [`config/fastdds.xml`](../../config/fastdds.xml) 只读；SCOREBOARD **pointer only** |
| same-topology XML 再拧 | **paused** | SCOREBOARD 页眉 leftover = Forbidden to retry |
| 跨机 UDP | **`STATUS: blocked`** | [`2026-09-11-cross-host/`](../artifacts/bench/2026-09-11-cross-host/README.md) |
| §13(2) 三条链 | **three-chain map≠reproduce** | [ros2-source-map.md](ros2-source-map.md)；ADR「只画地图」 |
| Unitree Cyclone 换库 | **0.10.2 vs vendor 11.0.1 drop-in FAIL** | [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) |
| 《3》《4》《5》《6》 | **Hold** | [ci-cd-gates.md](ci-cd-gates.md) |

**禁止：** 把 SCOREBOARD 分位数抄进本文当新基线。  
**禁止：** 把 `same-process` / `same-host` 当成跨机或现场证明。  
**禁止：** 把三条链地图写成已复现 PASS。  
**禁止：** 把 vendor 11.0.1 写成 Unitree 0.10.2 的 drop-in。

---

## 5. 闸门怎么跑

```bash
python3 scripts/check_dual_chain_baseline.py
python3 scripts/print_bench_gates.py
python3 scripts/prove_rmw.py
```

无 ROS 时三个脚本都应能 exit 0。成功时打印 `dual-chain baseline: pointer only (no XML rewrite)` 以及 `same-topology XML tuning is paused`。脚本打开这些文件（缺一个就红）：

| 打开 | 断言 |
|------|------|
| 本文 [`feishu-dual-chain-baseline.md`](feishu-dual-chain-baseline.md) | 双链契约句、**`no XML rewrite`**、SCOREBOARD **`pointer only`**、连续句 **`same-topology XML tuning is paused`**、跨机 `STATUS: blocked`、**three-chain map≠reproduce**、Unitree **drop-in FAIL**、《3》–《6》 Hold。不写 booked ping-pong quantile tokens |
| [feishu-middleware-adr.md](feishu-middleware-adr.md) | §13(3) 行仍写 FastDDS + Cyclone、**不重写 XML**、并指向本文 |
| [`config/env/chain_a.sh`](../../config/env/chain_a.sh) | 锚定 `export RMW_IMPLEMENTATION=rmw_fastrtps_cpp`、`export ROS_DOMAIN_ID=42`、`export FASTRTPS_DEFAULT_PROFILES_FILE=` |
| [`config/env/chain_b.sh`](../../config/env/chain_b.sh) | 锚定 `export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`、`export ROS_DOMAIN_ID=0`。**不** `export CYCLONEDDS_URI=`。本闸不看调用者继承的环境；inherited `CYCLONEDDS_URI` 不在本闸范围 |
| [ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md) | 双链 R0 冻结页还在（`Hold` 标记） |
| [ros2-source-map.md](ros2-source-map.md) | 三条链地图还在（map≠reproduce，不是复现报告） |
| [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) | 0.10.2 vs 11.0.1 **drop-in FAIL** 句还在 |
| [`config/fastdds.xml`](../../config/fastdds.xml) | **只检查存在**。内容冻结由 CI **`boundary`** 管 |
| [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) | **只检查存在**。不读数字；内容冻结由 **`boundary`** 管 |

CI 登记见 [ci-cd-gates.md](ci-cd-gates.md)。**不要**为了本地绿去编译 vendor，也**不要**发明 booked 分位词。

---

## 6. 引用

飞书（查阅 2026-09-12；本环境未取到 wiki 正文，本仓按已合入 ADR / SCOREBOARD 页眉 / env 脚本落地，**派生自**这些已入库源）：

1. 《ROS 2 源码闭环》§13 (3) FastDDS + Cyclone 基线：<https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf>
2. 《通信中间件》：<https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>
3. Cyclone 工业级 fork 研究：<https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>

本仓：

4. [feishu-middleware-adr.md](feishu-middleware-adr.md) — §13(3) 行
5. [ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md) · [config/env/README.md](../../config/env/README.md)
6. [docs/artifacts/bench/SCOREBOARD.md](../artifacts/bench/SCOREBOARD.md) — current-best **pointer only**
7. [ros2-source-map.md](ros2-source-map.md) — three-chain **map≠reproduce**
8. [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) — 0.10.2 vs 11.0.1 **drop-in FAIL**
9. [latency-attribution.md](latency-attribution.md) · [feishu-runtime-provenance.md](feishu-runtime-provenance.md)
10. [scripts/check_dual_chain_baseline.py](../../scripts/check_dual_chain_baseline.py) · [scripts/print_bench_gates.py](../../scripts/print_bench_gates.py) · [scripts/prove_rmw.py](../../scripts/prove_rmw.py)
