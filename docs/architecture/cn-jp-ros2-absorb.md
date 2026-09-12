# 中日公开 ROS 2 / DDS 优化吸收（对照本仓双链）

Status: **文档吸收 + 可选加法配方 — 不改现网契约。**  
查阅日期：2026-09-12。只写能核对到公开 URL 的内容；核不到的标 **未核实**，不编造数字。

本文把**日本 / 中国大陆**已公开、可引用的 ROS 2 / DDS 做法对照到本仓双链。落地范围：

| 允许 | 禁止（本 PR） |
|------|----------------|
| 本文 | 改 [`config/fastdds.xml`](../../config/fastdds.xml)（iter7 种子不动） |
| 可选 [`scripts/bench/cyclonedds_autoware_like.xml`](../../scripts/bench/cyclonedds_autoware_like.xml)（**标签示例**，非默认） | 改 SCOREBOARD 已记账表 / current best |
| SCOREBOARD **指针段** | vendor Autoware / Agnocast / Isaac / zenoh / iceoryx 树 |
| README 一条指针 | 新增 RMW、rebase 发行版 |
| CI 路径存在检查 | 启动 Promptfoo / Mac 占位测 / CVE（《3》–《6》仍 **Hold**） |

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

本仓契约仍是两条独立栈：[R0 接口冻结](ros2-dds-r0-interface-freeze.md)。链 A Fast-DDS 域 **42**，链 B Cyclone 域 **0**。DimOS 默认传输仍是 **LCM**（Linux）。NITROS 仍是同进程 GPU：[nitros-vs-dual-chain.md](nitros-vs-dual-chain.md)。跨机 UDP 仍 **blocked**（单机 yixin Docker DOWN）。

---

## 1. 对照到本仓双链（先看这张表）

| 公开项 | 本仓落点 | 本 PR 动作 |
|--------|----------|------------|
| TIER IV / Autoware Agnocast（未定长消息真零拷；kmod + `LD_PRELOAD` heaphook；`ENABLE_AGNOCAST`） | **不是** 第三条链，也不是 RMW。跨机 / rviz / rosbag 仍走现有 RMW/DDS | **Hold**：不 vendor、不装 kmod |
| Autoware CycloneDDS 配方（`SocketReceiveBufferSize` min 10MB、`MaxMessageSize` 65500B、`ParticipantIndex` none、`CYCLONEDDS_URI`） | 链 B 可选 URI；默认 **不** 设 `CYCLONEDDS_URI` | 加法示例 XML；`chain_b.sh` 仍不导出 URI |
| Autoware 经典 ComponentContainer 同进程（避免序列化/拷贝） | 与 NITROS / same-process bench 同类：**故障隔离 vs 零拷** | 只对照，不改节点图 |
| 奥比中光相机 Fast DDS（`rmw_fastrtps_cpp`、`FASTRTPS_*`、UDP 1MiB、`useBuiltinTransports` false） | 链 A 已用 **2MiB** socket buffer，且 **builtin 开** | **不回退** XML；不关 builtin |
| Fast DDS Data Sharing + Loaned Messages（Humble+ `rmw_fastrtps_cpp`，同机 POD） | 链 A XML **没有** `data_sharing`；SCOREBOARD 已写明要 `RMW_FASTRTPS_USE_QOS_FROM_XML` | **不** 翻转现网 `data_sharing` |
| openEuler 24.03：Jazzy 打包 + `rmw_zenoh` 预览；Embedded Humble / SDK | 本仓 Humble + 双链 RMW；`ZenohTransport` 仍是空 stub | **Hold** 新 RMW（zenoh）与发行版 rebase |

```mermaid
flowchart TB
  subgraph jp["日本公开项"]
    AG["Agnocast kmod + heaphook"]
    CY["Autoware Cyclone XML"]
    CC["ComponentContainer 同进程"]
  end
  subgraph cn["中国大陆公开项"]
    OB["Orbbec Fast DDS 1MiB / builtin off"]
    DS["Data Sharing + Loaned msg"]
    OE["openEuler Jazzy / zenoh / Embedded"]
  end
  subgraph chainA["链 A — 本仓"]
    A1["rmw_fastrtps_cpp"] --> A2["Fast-DDS 域 42"]
    A2 --> A3["config/fastdds.xml iter7"]
  end
  subgraph chainB["链 B — 本仓"]
    B1["Cyclone / rmw_cyclonedds_cpp"] --> B2["域 0"]
    B2 --> B3["默认不设 CYCLONEDDS_URI"]
  end
  AG -.->|"Hold"| chainA
  AG -.->|"Hold"| chainB
  CY -->|"标签示例"| B3
  CC -.->|"对照"| chainA
  OB -.->|"勿回退 2MiB"| A3
  DS -.->|"勿改 XML"| A3
  OE -.->|"Hold zenoh / rebase"| chainA
```

---

## 2. 日本

### 2.1 Agnocast（TIER IV / Autoware）— Hold

公开博客：[Agnocast: A True Zero-Copy Publish/Subscribe IPC](https://autoware.org/agnocast-a-true-zero-copy-publish-subscribe-ipc/)（2025-09-24）。仓库：[tier4/agnocast](https://github.com/tier4/agnocast)（README 现指向 [autowarefoundation/agnocast](https://github.com/autowarefoundation/agnocast) 与 [Getting Started](https://autowarefoundation.github.io/agnocast_doc/environment-setup/)）。

已核实要点：

- Autoware 作为 ROS 2 应用，跨进程 pub/sub 会做多次拷贝（含序列化 / 反序列化）。他们曾用 **ComponentContainer 把节点放进同一进程** 来避开这份开销。从故障隔离看，更希望每节点独立进程，因此需要「对任意 ROS 2 消息（含 `std::vector` 等未定长类型）的真零拷 IPC」。
- Iceoryx / Iceoryx2 等生产级中间件支持真零拷，但**只覆盖静态尺寸消息**，Autoware 大量未定长类型用不了。TZC / LOT 也不是任意 ROS 2 消息。
- Agnocast：内核模块（`agnocast-kmod`，`sudo modprobe agnocast`）+ `LD_PRELOAD` heaphook（`agnocast-heaphook`）把堆分配拦到可跨进程映射的共享虚址；智能指针元数据在 kmod 里。博客写明与 ROS 2 栈**共存**，且「不受 RMW 实现变更影响」——它**不是**一个新 RMW。
- 源码侧还要改智能指针 / pub/sub 命名空间（`rclcpp` → `agnocast`）以及 launch（`LD_PRELOAD`、ComposableNode 用 Agnocast executor）。
- Autoware 集成用构建期环境变量 **`ENABLE_AGNOCAST`** 开关（博客指向 `autoware_agnocast_wrapper`）。wrapper 说明：未设或 `0` = 普通 ROS 2；`1` = Agnocast 构建。[review guide](https://github.com/autowarefoundation/autoware_core/blob/a50ac9281442b83ec240aedcb4fe78598e07c8e3/common/autoware_agnocast_wrapper/docs/review_guide.md)
- TIER IV 在 Open Robotics Discourse 写明：即使 Agnocast 构建，**跨主机通信以及依赖 RMW 的 rviz / rosbag 仍走现有 RMW 栈**；与非 Agnocast 节点靠 Bridge。[Discourse #52678](https://discourse.openrobotics.org/t/agnocast-callback-isolated-executor-true-zero-copy-ipc-and-middleware-transparent-scheduling-for-ros-2/52678)

**本仓 verdict: Hold。** 不 vendor Agnocast 树，不装 / 不加载 kmod，不加第三条链。跨机 UDP、域 42/0、Fast-DDS XML 旋钮都不在 Agnocast 覆盖范围。

### 2.2 Autoware 推荐 CycloneDDS 配方 — 链 B 标签示例

来源：[DDS settings for ROS 2 and Autoware](https://autowarefoundation.github.io/autoware-documentation/main/installation/additional-settings-for-developers/network-configuration/dds-settings/)（与 [源码页](https://raw.githubusercontent.com/autowarefoundation/autoware-documentation/main/docs/installation/additional-settings-for-developers/network-configuration/dds-settings.md) 核对；站点 HTML 本次抓取曾 409，内容以该 markdown 为准）。

已核实：

- **CycloneDDS 是 Autoware 推荐且测得最多的 DDS。**
- XML（`~/cyclonedds.xml`）文档值：`MaxMessageSize` **65500B**；`Discovery/ParticipantIndex` **none**（Jazzy 上默认 participant index 大约 32，多节点会 `Failed to find a free participant index for domain 0`）；`Internal/SocketReceiveBufferSize` **min="10MB"**；另有文档里的 `WhcHigh` 500kB、以及把 `NetworkInterface` 钉到 **`lo`** 的本机示例。
- 环境：`RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`，`CYCLONEDDS_URI=file:///absolute/path/to/cyclonedds.xml`。
- 系统侧另有 `net.core.rmem_max` / IP 分片调参（ROS 2 DDS tuning 同源）。**本仓不把这些 sysctl 写成已测根因，也不改现网。**

本仓映射：链 B 是 Cyclone / 域 **0**。[`config/env/chain_b.sh`](../../config/env/chain_b.sh) **默认不设** `CYCLONEDDS_URI`。加法文件 [`scripts/bench/cyclonedds_autoware_like.xml`](../../scripts/bench/cyclonedds_autoware_like.xml) 是**标签示例**（复述上述文档旋钮），**不是**默认，**不是** SCOREBOARD。操作员若要试，须自己 `export CYCLONEDDS_URI=file://…`。不要和链 A ping-pong 混表。

### 2.3 ComponentContainer 同进程 — 对照，不落地

同一篇 Agnocast 博客：Autoware 经典做法是 **ComponentContainer 同进程**，避免跨进程序列化/拷贝；Agnocast 存在，是因为他们要 **进程隔离 + 真零拷**。

这与本仓 [NITROS 对照](nitros-vs-dual-chain.md) 同一类权衡：同进程才能吃到「少拷」，但不是跨机、不是跨域 42/0。same-process bench 只作诚实对照，**不要为它调参**。

---

## 3. 中国大陆

### 3.1 奥比中光相机 Fast DDS — 对照链 A，勿回退 XML

来源：[针对 Orbbec 相机与 ROS2 的 Fast DDS 优化](https://orbbec.github.io/OrbbecSDK_ROS2/zh/source/camera_devices/5_advanced_guide/performance/fastdds_tuning.html)。

已核实环境变量：

```text
RMW_IMPLEMENTATION=rmw_fastrtps_cpp
FASTRTPS_DEFAULT_PROFILES_FILE=$HOME/shm_fastdds.xml
RMW_FASTRTPS_USE_QOS_FROM_XML=1
```

已核实 XML 要点（他们的 `shm_fastdds.xml` 示例）：

- UDP `sendBufferSize` / `receiveBufferSize` 以及 participant `sendSocketBufferSize` / `listenSocketBufferSize` = **1048576（1MiB）**
- `<useBuiltinTransports>false</useBuiltinTransports>`，只用自定义 `UDPv4`
- `maxMessageSize` 65000；`initialPeersList` 指向 `127.0.0.1`
- 示例里的 data_reader 带 `<data_sharing><kind>AUTOMATIC</kind></data_sharing>`（以及 writer `ASYNCHRONOUS` / `latencyBudget` 等）

本仓链 A **已经**在 iter2 把默认 participant UDP socket 提到 **2097152（2MiB）**，且 **builtin UDP+SHM 开着**，另有加法 `shm_midsize`。**不要把 socket 回退到 1MiB，也不要为对齐 Orbbec 示例关掉 builtin。** 他们设 `RMW_FASTRTPS_USE_QOS_FROM_XML=1` 才会吃 writer/reader QoS；本仓 iter7 种子**没有**默认 writer/reader profile，SCOREBOARD 已写明 ping-pong 走 `testdata.py` QoS 名。

系统 `rmem_*` / `wmem_*` / IP 分片：Orbbec 页有示例数字。本仓不把这些写成已测根因，也不在本 PR 改 sysctl。

### 3.2 Fast DDS Data Sharing + Loaned Messages — 文档，不改现网 XML

来源：

- eProsima：[ROS 2 using Fast DDS middleware](https://fast-dds.docs.eprosima.com/en/latest/fastdds/ros2/ros2.html)（`rmw_fastrtps_cpp` 为除 EOL Galactic 外的默认 RMW）
- eProsima：[Data-sharing delivery](https://fast-dds.docs.eprosima.com/en/latest/fastdds/transport/datasharing.html)（**同机**共享 DataWriter history；跨机仍走传输层）
- ROS 2 设计：[Zero Copy via Loaned Messages](https://design.ros2.org/articles/zero_copy.html)
- `rmw_fastrtps` README（本仓拷贝 [`vendor/rmw_fastrtps/README.md`](../../vendor/rmw_fastrtps/README.md) 与 [上游](https://github.com/ros2/rmw_fastrtps) 一致）：Humble 上 Loaned Messages 需要 **POD + 打开 Data Sharing**；Iron+ 只需 POD。打开 Data Sharing 要 XML `<data_sharing><kind>AUTOMATIC</kind></data_sharing>` 且 `RMW_FASTRTPS_USE_QOS_FROM_XML=1`。默认 `rmw_fastrtps_cpp` 用 **SHM 做同机、UDPv4 做跨机**。

已核实约束（Data-sharing 页）：两端能碰同一块共享内存；类型 **bounded**；非 keyed；writer 预分配内存策略；不用 security。跨主机没有这块共享内存，仍要序列化走 UDP。

**本 PR 不**在 [`config/fastdds.xml`](../../config/fastdds.xml) 加 `data_sharing`，也不设 `RMW_FASTRTPS_USE_QOS_FROM_XML`。SCOREBOARD 已把该家族标成「不是一个 XML 旋钮」。

### 3.3 openEuler 24.03 / Embedded — Hold 新 RMW 与 rebase

来源：

- [openEuler 社区 2025 年 3 月运作报告](https://www.openeuler.org/zh/news/openEuler/20250407-yb/20250407-yb.html)：openEuler **24.03 LTS** 引入 **ROS 2 Jazzy**（Turtlesim / rqt / 全套 CLI；移植工具 ROT）。文内写 Jazzy「首次引入 **rmw_zenoh 中间件预览版**」。
- [openEuler Embedded 24.03 — 嵌入式 ROS 运行时支持](https://embedded.pages.openeuler.org/openEuler-24.03-LTS/features/ros.html)：ROS2 镜像 / **快速开发 SDK**（`populate_sdk` + colcon 交叉编译）。同页写明「当前 src-openeuler 已集成 **ROS humble** 的所有软件源码」。

**本仓 verdict: Hold。** 不引入 `rmw_zenoh`（DimOS `ZenohTransport` 仍是空 stub）。不把发行版从 Humble rebase 到 Jazzy。Embedded SDK 只作公开存在证明，不 vendor、不改 Docker 配方。

---

## 4. 对本仓契约的明确「不是」

| 项 | 状态 |
|----|------|
| 链 A：`rmw_fastrtps_cpp` / 域 42 / `config/fastdds.xml` iter7 种子 | **不变** |
| 链 B：Cyclone / 域 0；默认不设 `CYCLONEDDS_URI` | **不变**；Autoware XML 只是标签示例 |
| DimOS 默认 LCM | **不变**，仍在 DDS 范围外 |
| NITROS | 仍同进程 GPU only，见 [nitros-vs-dual-chain.md](nitros-vs-dual-chain.md) |
| 跨机 UDP | 仍 **STATUS: blocked**（单 VM）；无假分位数 |
| 《3》90%/LLM、《4》Mac/preprod、《5》Promptfoo、《6》CVE | 仍 **Hold** |
| 飞书现场 / 实机根因 | **不是。** Not Feishu field proof. |

---

## 5. 公开引用

只列本文用过的链接（2026-09-12 核对）：

1. Autoware — *Agnocast: A True Zero-Copy Publish/Subscribe IPC*：<https://autoware.org/agnocast-a-true-zero-copy-publish-subscribe-ipc/>
2. GitHub `tier4/agnocast`：<https://github.com/tier4/agnocast>（README 现指向 AWF 树 / 文档站）
3. AWF Agnocast Getting Started：<https://autowarefoundation.github.io/agnocast_doc/environment-setup/>
4. Open Robotics Discourse #52678（跨机 / rviz / rosbag 仍走 RMW）：<https://discourse.openrobotics.org/t/agnocast-callback-isolated-executor-true-zero-copy-ipc-and-middleware-transparent-scheduling-for-ros-2/52678>
5. `autoware_agnocast_wrapper` review guide（`ENABLE_AGNOCAST`）：<https://github.com/autowarefoundation/autoware_core/blob/a50ac9281442b83ec240aedcb4fe78598e07c8e3/common/autoware_agnocast_wrapper/docs/review_guide.md>
6. Autoware Documentation — *DDS settings*：<https://autowarefoundation.github.io/autoware-documentation/main/installation/additional-settings-for-developers/network-configuration/dds-settings/>
7. OrbbecSDK ROS2 — Fast DDS 优化：<https://orbbec.github.io/OrbbecSDK_ROS2/zh/source/camera_devices/5_advanced_guide/performance/fastdds_tuning.html>
8. eProsima Fast DDS — ROS 2：<https://fast-dds.docs.eprosima.com/en/latest/fastdds/ros2/ros2.html>
9. eProsima Fast DDS — Data-sharing delivery：<https://fast-dds.docs.eprosima.com/en/latest/fastdds/transport/datasharing.html>
10. ROS 2 design — *Zero Copy via Loaned Messages*：<https://design.ros2.org/articles/zero_copy.html>
11. `ros2/rmw_fastrtps` README：<https://github.com/ros2/rmw_fastrtps>
12. openEuler 2025-03 月报（Jazzy + `rmw_zenoh` 预览）：<https://www.openeuler.org/zh/news/openEuler/20250407-yb/20250407-yb.html>
13. openEuler Embedded 24.03 — 嵌入式 ROS（Humble 源码 + SDK）：<https://embedded.pages.openeuler.org/openEuler-24.03-LTS/features/ros.html>
14. 本仓双链：[ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md) · [nitros-vs-dual-chain.md](nitros-vs-dual-chain.md)
