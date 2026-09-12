# 内存下沉层（飞书《通信中间件》：与 Executor **并列** Hold）

Status: **Hold** — `STATUS: Hold`。不落地 Loaned / Fast-DDS Data Sharing / Iceoryx 运行时 / Agnocast kmod / heaphook。`no zero-copy land`。不是飞书现场、不是跨机根因。  
查阅日期：2026-09-12。对照飞书《通信中间件》<https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>（差异化下沉到 RMW / DDS / Executor / **内存**，内存与 Executor **并列**，不是 DDS 之后的下一跳）。另两份飞书计划（已在 ADR）：《ROS 2 源码闭环》<https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf> §9.4 / §13(5) 一次一层、《ROS 2 源码闭环》§13(4) Cega / Bridge 后置已登记 Hold（#40）。Cyclone 工业级 fork 研究 <https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>。

本环境打不开飞书 wiki 正文（登录墙 / 抓取失败）。本页章节对照**派生自**已合入 ADR [feishu-middleware-adr.md](feishu-middleware-adr.md)、下沉层表 [feishu-sink-layers.md](feishu-sink-layers.md)、中日对照 [cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md)；**不是** Feishu field / 跨机证明，不阻塞等 wiki。双链契约：[ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md)。CI 闸门：[ci-cd-gates.md](ci-cd-gates.md)。

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

本切只落地文档 + 证明脚本。**no zero-copy land.** **no XML/SCOREBOARD.**

---

## 0. 硬规则

1. **`STATUS: Hold`。** 飞书把 **memory** 与 Executor **并列**下沉。本仓这一刀只登记 Hold：不落地 Loaned messages、不翻转现网 Fast-DDS `data_sharing`、不打开 Iceoryx / Iceoryx2 运行时、不装 Agnocast kmod、不加 heaphook。`no zero-copy land`。
2. **AUTO CMake ≠ zero-copy proven。** Cyclone 快照里 `ENABLE_ICEORYX` / `ENABLE_ICEORYX2` 默认 **AUTO**（宿主机若已装 `iceoryx_*`，CMake 才可能编插件）。那是构建探测，**不是**本仓已开零拷、不是 Iceoryx 在跑。本仓 CI **不**编译 vendor。
3. **adapter source ≠ vendored Iceoryx。** [`vendor/CycloneDDS/src/psmx_iox/`](../../vendor/CycloneDDS/src/psmx_iox/) 是 PSMX **适配源码**对照。Iceoryx 库本身是可选外部依赖（[VERSIONS.md](../../vendor/VERSIONS.md)）。本仓 **没有 vendor/iceoryx** 树。适配源码 ≠ 已 vendor Iceoryx。
4. **不改** [`config/fastdds.xml`](../../config/fastdds.xml)、[`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md)。`no XML/SCOREBOARD`：本切 diff 不得含这两份内容变更。内容冻结由 CI **`boundary`** 管。
5. **不**启用 Agnocast / zenoh / eCAL / DPDK / Isaac。不 vendor `rmw_zenoh`，不装 kmod，不加 heaphook。零拷 **不**解锁跨机 UDP（跨机仍 **blocked**）。
6. **《3》–《6》仍 Hold。** 《3》90%/LLM、《4》Mac/preprod、《5》Promptfoo、《6》CVE 仍出范围。
7. **Unitree swap 仍 FAIL。** 自带 Cyclone 0.10.2 **不是** vendor 11.0.1 的 drop-in（`drop-in FAIL / wire UNPROVEN`）。见 [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md)。本切不借零拷去「换库」。
8. **三条链复现与 wiki3 DoD 仍 unmet / blocked。** §13(2) **map ≠ reproduce**（[feishu-three-chain-repro.md](feishu-three-chain-repro.md)，`STATUS: blocked`）；§6.3 / §12 DoD 仍 unmet（[feishu-dod-evidence.md](feishu-dod-evidence.md)）。**Cega / Bridge 仍 Hold（#40）**：[feishu-cega-bridge-hold.md](feishu-cega-bridge-hold.md)。本切**不会**把这些写成 PASS。

核对本页 + ADR / 下沉层 / 中日指针仍写 Hold：[`scripts/check_memory_hold.py`](../../scripts/check_memory_hold.py)。

---

## 1. 本仓已有对照（不是落地）

飞书要差异化下沉到内存，但 §9.4 把 Executor / memory 排在 env/XML、RMW、DDS knobs **之后**。本环境未取到 wiki 正文，下面只复述 ADR + 下沉层表 + 中日吸收已决含义，不发明飞书字段号。

| 词 | 已在树里的对照 | 本仓若做（**本切不做**） |
|----|----------------|--------------------------|
| **Loaned** messages | [cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md) §3.2：Loaned + Fast DDS Data Sharing 加速 **intra-host**；Humble 还要 POD + 打开 Data Sharing | 落地 Loaned API / 现网 XML `data_sharing`。**Hold** |
| Fast-DDS **Data Sharing** | 同上；`rmw_fastrtps` README 写明 intra-host Shared Memory、inter-host 仍 UDPv4。现网 [`fastdds.xml`](../../config/fastdds.xml) **不**翻转 `data_sharing` | 改 XML 旋钮。**Hold**（且 XML 冻结） |
| **Iceoryx** / **Iceoryx2** | Cyclone PSMX 适配源码 [`vendor/CycloneDDS/src/psmx_iox/`](../../vendor/CycloneDDS/src/psmx_iox/)；`ENABLE_ICEORYX` / `ENABLE_ICEORYX2` = **AUTO**。**没有 vendor/iceoryx** | 打开 Iceoryx 运行时、vendor Iceoryx 树、把 AUTO 当已证零拷。**Hold** |
| **Agnocast** / **heaphook** | [cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md) §2.1：kmod + `LD_PRELOAD` heaphook；**不是** RMW。**zenoh** 同页 Hold | 装 kmod / heaphook / `rmw_zenoh`。**Hold** |

层表权威页仍是 [feishu-sink-layers.md](feishu-sink-layers.md)（app / rcl / rmw / DDS / executor / memory；Hold vs allowed）。本页只把 **memory** 行收成独立 Hold 闸。Executor 身份地图另见 [feishu-executor-waitset.md](feishu-executor-waitset.md)（不 fork Executor）。

**AUTO ≠ 已开零拷。** `AUTO CMake ≠ zero-copy proven`。`adapter source ≠ vendored Iceoryx`。

---

## 2. 为何 Hold（§13(5) 一次一层）

ADR §13 对本仓这一刀：

| §13 | 飞书要求 | 本仓现状 | 对 memory 的含义 |
|-----|----------|----------|------------------|
| (1) | 冻 `ROS_DISTRO` + manifest | [feishu-runtime-provenance.md](feishu-runtime-provenance.md)：Humble underlay ≠ rolling vendor | 运行时身份已钉；不是开零拷的许可 |
| (2) | 复现三条链 | **map ≠ reproduce**，`STATUS: blocked` | 未复现链路不能靠 Loaned / Iceoryx 「加速」 |
| (3) | FastDDS + Cyclone 基线 | 不重写 XML、不改 SCOREBOARD | 翻转 `data_sharing` = 动冻结 XML |
| (4) | Cega / Bridge 后置 | **Hold**（#40） | 不接 Cega，不改 `dimos_bridge` 运行时 |
| **(5)** | 一次一层 | 本切 = memory **Hold** 文档 + 证明脚本 + CI 登记 | 只登记身份 / 文档闸；不落地零拷 |
| (6) | CI + 灰度 | 本工作流三个 job；**不**编译 vendor | 本切把 Hold 收进 `structure` |

wiki3 §9.4（[feishu-risk-matrix.md](feishu-risk-matrix.md)）层序：env/XML → RMW → DDS knobs → **Executor / memory** → core forks。跳过 XML 去开 Iceoryx / Loaned 是越层。跨机 UDP 仍 blocked；无假分位数。三条链 / DoD 因此仍 **unmet / blocked**。Cega / Bridge 仍 Hold。

---

## 3. 闸门怎么跑

```bash
python3 scripts/check_memory_hold.py
```

无 ROS 时应 exit 0，并打印 `memory layer: Hold (no zero-copy land)`。脚本打开这些文件：

| 打开 | 断言 |
|------|------|
| 本文 [`feishu-memory-hold.md`](feishu-memory-hold.md) | `STATUS: Hold`、`no zero-copy land`、`no XML/SCOREBOARD`、`AUTO ≠ 已开零拷`、`AUTO CMake ≠ zero-copy proven`、`adapter source ≠ vendored Iceoryx`、`没有 vendor/iceoryx`、`《3》`–`《6》`、Agnocast / zenoh / heaphook、Loaned / Data Sharing / Iceoryx、三条链 / DoD / blocked、Unitree `drop-in FAIL`、Cega Hold |
| [`feishu-middleware-adr.md`](feishu-middleware-adr.md) | 仍写 内存 + 本页 + `check_memory_hold.py` + `check_cega_bridge_hold.py`；不得把 memory 写成 PASS / PROVEN / Active |
| [`feishu-sink-layers.md`](feishu-sink-layers.md) | memory 行仍指向本页；`AUTO ≠ 已开零拷`；`没有 vendor/iceoryx`；`psmx_iox` |
| [`cn-jp-ros2-absorb.md`](cn-jp-ros2-absorb.md) | Loaned / Data Sharing / Agnocast / zenoh / heaphook 对照仍在；不翻转现网 `data_sharing` |
| [`vendor/CycloneDDS/src/psmx_iox/`](../../vendor/CycloneDDS/src/psmx_iox/) | **目录仍在**（适配源码对照）。`ENABLE_ICEORYX*` 在 Cyclone CMake 仍为 AUTO 字面量 |
| `vendor/iceoryx` | **不得存在**（顶层树） |
| [`config/fastdds.xml`](../../config/fastdds.xml) | **只检查存在**。内容冻结由 **`boundary`** 管 |
| [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) | **只检查存在**。不读数字；内容冻结由 **`boundary`** 管 |

CI 登记见 [ci-cd-gates.md](ci-cd-gates.md)。**不要**为了本地绿去编译 vendor、落地零拷、或改 XML / SCOREBOARD / `dimos_bridge` 运行时。本脚本**不**发明时延，**不**声称 Iceoryx 在跑。

---

## 4. 引用

飞书（查阅 2026-09-12；本环境未取到 wiki 正文，本仓按已合入 ADR / 下沉层 / 中日吸收落地）：

1. 《通信中间件》：<https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>
2. 《ROS 2 源码闭环》§9.4 / §13(5)：<https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf>
3. Cyclone 工业级 fork 研究：<https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>

本仓：

4. [feishu-middleware-adr.md](feishu-middleware-adr.md) — 差异化下沉 / §13(5) 一次一层（派生源）
5. [feishu-sink-layers.md](feishu-sink-layers.md) — app / rcl / rmw / DDS / executor / memory（Hold vs allowed）
6. [cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md) — Loaned / Data Sharing / Agnocast / zenoh（不落地）
7. [feishu-cega-bridge-hold.md](feishu-cega-bridge-hold.md) — wiki3 §13(4) Cega / Bridge 仍 Hold（#40）
8. [feishu-three-chain-repro.md](feishu-three-chain-repro.md) · [feishu-dod-evidence.md](feishu-dod-evidence.md) — 三条链 / DoD 仍 unmet / blocked
9. [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) — drop-in FAIL / wire UNPROVEN
10. [feishu-risk-matrix.md](feishu-risk-matrix.md) · [feishu-executor-waitset.md](feishu-executor-waitset.md) · [ci-cd-gates.md](ci-cd-gates.md)
11. [scripts/check_memory_hold.py](../../scripts/check_memory_hold.py)
