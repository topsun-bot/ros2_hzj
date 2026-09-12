# Cega / Bridge（飞书 wiki3 §13(4)：后置 Hold）

Status: **Hold** — `STATUS: Hold`。不接 Cega，不改 `dimos_bridge` 运行时。不是飞书现场、不是跨机根因。  
查阅日期：2026-09-12。对照飞书《ROS 2 源码闭环》<https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf> §13 第 (4) 步（Cega / Bridge **后置**）。另两份飞书计划（已在 ADR）：《通信中间件》<https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>、Cyclone 工业级 fork 研究 <https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>。

本环境打不开飞书 wiki 正文（登录墙 / 抓取失败）。本页章节对照**派生自**已合入 ADR [feishu-middleware-adr.md](feishu-middleware-adr.md) §2 第 (4) 行、§3 Cega 行、§4 硬闸门；**不是** Feishu field / 跨机证明，不阻塞等 wiki。双链契约：[ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md)。三条链地图：[ros2-source-map.md](ros2-source-map.md)。复现状态（**map ≠ reproduce**，`STATUS: blocked`）：[feishu-three-chain-repro.md](feishu-three-chain-repro.md)。DoD 形状：[latency-attribution.md](latency-attribution.md)。CI 闸门：[ci-cd-gates.md](ci-cd-gates.md)。

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

本切只落地文档 + 证明脚本。**no Cega.** **no dimos_bridge runtime edits this cut.** **no XML/SCOREBOARD.**

---

## 0. 硬规则

1. **`STATUS: Hold`。** 飞书 §13(4) 把 Cega / Bridge 放在 FastDDS + Cyclone 基线**之后**。本仓这一刀只登记 Hold，不接、不集成、不 vendor Cega。
2. **不接 Cega。** 不发明自定义 RMW，不抽《通信中间件》次优「上层 module 双堆」，不把 Cega 当第三条链。`no Cega` 是闸门原文，不是「以后再静默合进去」。
3. **不改 `dimos_bridge` 运行时 Python 模块。** `no dimos_bridge runtime edits this cut`。对照阅读可以，改 `ROSTransport` / `DDSTransport` / `DDSService` / Unitree DDS 绑定不行。
4. **不改** [`config/fastdds.xml`](../../config/fastdds.xml)、[`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md)。`no XML/SCOREBOARD`：本切 diff 不得含这两份内容变更。内容冻结由 CI **`boundary`** 管。
5. **不**启用 Agnocast / zenoh / eCAL / DPDK / Isaac。不 vendor `rmw_zenoh`，不装 kmod。`ZenohTransport` 仍是空 stub，不是 Cega 落点。
6. **《3》–《6》仍 Hold。** 《3》90%/LLM、《4》Mac/preprod、《5》Promptfoo、《6》CVE 仍出范围。跨机 UDP 仍 **blocked**。
7. **Unitree swap 仍 FAIL。** 自带 Cyclone 0.10.2 **不是** vendor 11.0.1 的 drop-in（`drop-in FAIL / wire UNPROVEN`）。见 [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md)。本切不借 Cega / Bridge 去「换库」。
8. **三条链复现与 wiki3 DoD 仍 unmet / blocked。** §13(2) 只画地图，不是已复现；§12 DoD 是产品定义，不是现场验收。Cega / Bridge 后置，所以这两项**不会**因本切变成 PASS。

核对本页 + ADR §13(4) 仍写 Hold：[`scripts/check_cega_bridge_hold.py`](../../scripts/check_cega_bridge_hold.py)。

---

## 1. Cega / Bridge 若落地会是什么（本仓对照，不是接入）

飞书把第 (4) 步写成 **Cega / Bridge 后置**。本环境未取到 wiki 正文，下面只复述 ADR 已决含义，不发明 Cega 厂商 API。

| 词 | 飞书 / ADR 在说什么 | 本仓若做（**本切不做**）会碰到谁 |
|----|---------------------|----------------------------------|
| **Cega** | §13 执行顺序里，排在双链基线之后的接入 / 自研桥。ADR：**不接 Cega**，不进 `vendor/`，不自定义 RMW | 新 transport、新 RMW、或改 DimOS 桥去对接 Cega。本仓没有 Cega 树 |
| **Bridge** | DimOS 双链桥：应用仍写 `ROSTransport` / `DDSTransport`，底下换 `.so` | [`dimos_bridge/`](../../dimos_bridge/) 运行时 Python。改这些才叫「动 Bridge」 |
| **后置** | 先冻 distro、画三条链、落 FastDDS + Cyclone 基线，**再**谈 Cega / 改桥 | 三条链仍是地图、DoD 未现场验收 → 本步保持 Hold |

保持 ROS 2 应用 API。操作员用已有 `config/env` 切链 A / 链 B，**不必**为了 Cega 再抽一层 module 双堆。

`ZenohTransport`（[`transport.py`](../../dimos_bridge/dimos/core/transport.py) 空 stub）**不是** Cega，也不是可用路径。LCM / SHM 默认传输不在本仓 DDS 范围。

---

## 2. 为何 deferred / 为何 Hold

ADR §13 顺序对本仓这一刀：

| §13 | 飞书要求 | 本仓现状 | 对 (4) 的含义 |
|-----|----------|----------|---------------|
| (1) | 冻 `ROS_DISTRO` + manifest | [feishu-runtime-provenance.md](feishu-runtime-provenance.md)：Humble underlay ≠ rolling vendor | 运行时身份已钉；不是接 Cega 的许可 |
| (2) | 复现 publish / ingress→History / wait→callback **三条链** | **map ≠ reproduce**：[ros2-source-map.md](ros2-source-map.md)、[feishu-executor-waitset.md](feishu-executor-waitset.md)、[feishu-three-chain-repro.md](feishu-three-chain-repro.md)（`STATUS: blocked`） | 三条链 unmet。后置的 (4) 不能抢跑 |
| (3) | FastDDS + Cyclone 基线 | 双链契约已在；bench 另册；**不**重写 XML、**不**改 SCOREBOARD | 基线数字冻结。Cega 不是调 XML 的借口 |
| **(4)** | Cega / Bridge 后置 | **Hold**（本文） | 不接 Cega，不改 `dimos_bridge` 运行时 |
| (5) | 一次一层 | 本切 = 文档 + 证明脚本 + CI 登记 | 下一层另开 PR |
| (6) | CI + 灰度 | 本工作流三个 job；**不**编译 vendor | 本切把 Hold 收进 `structure` |

wiki3 §12 DoD（[latency-attribution.md](latency-attribution.md) §2）是**产品定义**（一次 run 三件套、日期目录、SCOREBOARD 只认指针、跨机写 `STATUS: blocked`），**不是**现场验收。跨机 UDP 仍 blocked；无假分位数。三条链 / DoD 因此仍 **unmet / blocked**。在那之前接 Cega 或改 Bridge，会把未复现链路与冻结 XML 搅在一起。

---

## 3. 本切只读的 `dimos_bridge` 运行时路径

来源钉扎：[dimos_bridge/SOURCE.md](../../dimos_bridge/SOURCE.md)（上游 `topsun_dimos` `main` @ `a5259958`）。整文件拷贝，**行为不变**。本切 **只读** 下列运行时 Python；`__init__.py` / ImportError stub **不是**运行时，也不要当 Cega 落点。

| 路径 | 角色 | 本切 |
|------|------|------|
| [`dimos/core/transport.py`](../../dimos_bridge/dimos/core/transport.py) | `ROSTransport` / `DDSTransport`；`ZenohTransport` 空 stub | **只读** |
| [`dimos/protocol/pubsub/impl/rospubsub.py`](../../dimos_bridge/dimos/protocol/pubsub/impl/rospubsub.py) | 链 A：发行版 `SingleThreadedExecutor` | **只读** |
| [`dimos/protocol/pubsub/impl/ddspubsub.py`](../../dimos_bridge/dimos/protocol/pubsub/impl/ddspubsub.py) | 链 B：Cyclone `on_data_available` → `reader.take()` | **只读** |
| [`dimos/protocol/pubsub/impl/rospubsub_conversion.py`](../../dimos_bridge/dimos/protocol/pubsub/impl/rospubsub_conversion.py) | ROS ↔ DimOS 字段拷贝 | **只读** |
| [`dimos/protocol/service/ddsservice.py`](../../dimos_bridge/dimos/protocol/service/ddsservice.py) | Cyclone service | **只读** |
| [`dimos/protocol/dds_topics.py`](../../dimos_bridge/dimos/protocol/dds_topics.py) | 冻结 topic / 域常量（publisher **尚未**改接） | **只读** |
| [`dimos/robot/unitree/go2/blueprints/smart/unitree_go2_ros.py`](../../dimos_bridge/dimos/robot/unitree/go2/blueprints/smart/unitree_go2_ros.py) | Go2 `ROSTransport` 绑定 | **只读** |
| [`dimos/robot/unitree/g1/effectors/high_level/dds_sdk.py`](../../dimos_bridge/dimos/robot/unitree/g1/effectors/high_level/dds_sdk.py) | Unitree / Cyclone 高阶；域 0 | **只读** |

[`dual_chain_env.py`](../../dimos_bridge/dual_chain_env.py) 是本仓 R1 薄包装（import **不**写 `os.environ`），不是 Cega，也不是改 DDS 行为的口子。LCM / SHM 实现文件在树里，但 **LCM 不在本仓 DDS 范围**。

`boundary` **不**逐字节审 `dimos_bridge`；政策仍是 **不要改** 运行时模块。本切 CI 只确认这些路径还在、Hold 标记还在。

---

## 4. 三条链 / DoD 仍 unmet / blocked

| 项 | 指针 | 本切状态 |
|----|------|----------|
| 三条链（publish / ingress→History / wait→callback） | [ros2-source-map.md](ros2-source-map.md)、[feishu-executor-waitset.md](feishu-executor-waitset.md)、[feishu-three-chain-repro.md](feishu-three-chain-repro.md) | **unmet / blocked** — **map ≠ reproduce**。不编造已复现 |
| wiki3 §12 DoD | [latency-attribution.md](latency-attribution.md) §2 | **blocked / unmet** — 仓内可核对项（三件套、SCOREBOARD 指针）≠ 现场验收 |
| 跨机 UDP | [`2026-09-11-cross-host/`](../artifacts/bench/2026-09-11-cross-host/README.md) | **blocked** |
| Unitree 0.10.2 vs vendor 11.0.1 | [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) | **drop-in FAIL / wire UNPROVEN** |
| Agnocast / zenoh | [cn-jp-ros2-absorb.md](cn-jp-ros2-absorb.md)、ADR §3 | **Hold** |
| 《3》–《6》 | [ci-cd-gates.md](ci-cd-gates.md) | **Hold** |

不要把本页 Hold 登记写成「三条链已复现」或「DoD 已过」。

---

## 5. 闸门怎么跑

```bash
python3 scripts/check_cega_bridge_hold.py
```

无 ROS 时应 exit 0，并打印 `§13(4) Cega / Bridge: Hold`。脚本打开这些文件：

| 打开 | 断言 |
|------|------|
| 本文 [`feishu-cega-bridge-hold.md`](feishu-cega-bridge-hold.md) | `STATUS: Hold`、`no Cega`、`不接 Cega`、`no dimos_bridge runtime edits this cut`、`no XML/SCOREBOARD`、`《3》`–`《6》`、Agnocast / zenoh、三条链 / DoD / blocked、Unitree `drop-in FAIL` |
| [`feishu-middleware-adr.md`](feishu-middleware-adr.md) | §13 第 (4) 行仍写 Cega / Bridge **Hold** |
| 上表 `dimos_bridge` 运行时 `.py` | **只检查存在**。不审行为、不算 hash |
| [`config/fastdds.xml`](../../config/fastdds.xml) | **只检查存在**。内容冻结由 **`boundary`** 管 |
| [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) | **只检查存在**。不读数字；内容冻结由 **`boundary`** 管 |

CI 登记见 [ci-cd-gates.md](ci-cd-gates.md)。**不要**为了本地绿去编译 vendor、接 Cega、或改 XML / SCOREBOARD / `dimos_bridge` 运行时。

---

## 6. 引用

飞书（查阅 2026-09-12；本环境未取到 wiki 正文，本仓按已合入 ADR 落地）：

1. 《ROS 2 源码闭环》§13 (4) Cega / Bridge 后置：<https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf>
2. 《通信中间件》：<https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>
3. Cyclone 工业级 fork 研究：<https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>

本仓：

4. [feishu-middleware-adr.md](feishu-middleware-adr.md) — §13(4) / §3 Cega / §4 硬闸门（派生源）
5. [ros2-source-map.md](ros2-source-map.md) · [feishu-executor-waitset.md](feishu-executor-waitset.md) · [feishu-three-chain-repro.md](feishu-three-chain-repro.md) — 三条链地图 / `STATUS: blocked`（unmet）
6. [latency-attribution.md](latency-attribution.md) — §12 DoD（不是现场验收）
7. [unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md) — drop-in FAIL / wire UNPROVEN
8. [feishu-runtime-provenance.md](feishu-runtime-provenance.md) · [feishu-risk-matrix.md](feishu-risk-matrix.md) · [ci-cd-gates.md](ci-cd-gates.md)
9. [dimos_bridge/SOURCE.md](../../dimos_bridge/SOURCE.md)
10. [scripts/check_cega_bridge_hold.py](../../scripts/check_cega_bridge_hold.py)
