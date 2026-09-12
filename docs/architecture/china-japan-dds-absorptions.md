# 中日 ROS 2 / DDS 调参吸收（文档对照）

Status: **文档吸收 — 不改 XML / SCOREBOARD / 运行时。**  
本文只收录三条可核验的公开实践（Orbbec Fast-DDS 大缓冲、Autoware/Tier4 Cyclone 接收窗、ROS 2 loaned + Fast-DDS data-sharing），标清**参考 vs 本仓已采用**。不把厂商示例写成现网旋钮，也不把同机零拷贝写成跨机 UDP 解法。

本仓契约仍是两条独立栈：[R0 接口冻结](ros2-dds-r0-interface-freeze.md)。链 A Fast-DDS 域 **42**，链 B Cyclone 域 **0**。

---

## Hard gates / 非目标（Non-goals）

会议室共识，本文**不得**越界：

| 闸门 | 状态 |
|------|------|
| 只改文档（+ 既有索引一条指针） | **强制** |
| 改 [`config/fastdds.xml`](../../config/fastdds.xml) | **禁止** |
| 改 [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) 或任何 bench 数字 | **禁止** |
| 声称本稿解锁跨机 UDP | **禁止**（`cross-host-UDP` 仍 blocked） |
| 启用 Agnocast / zenoh / Vendor Isaac | **Hold**，本文不打开 |
| 改 `vendor/`、`dimos_bridge/`、DimOS 行为或运行时默认值 | **禁止** |
| 在本仓发明一份 Cyclone XML | **禁止** |
| 把 Orbbec `1048576` 写成我们的 XML 旋钮 | **禁止**（厂商示例 / 参考） |

证据等级：

| 等级 | 含义 | 本稿用法 |
|------|------|----------|
| **已采用** | 本仓已落地、可指到文件 | 仅链 A iter2 默认 participant 的 **2 MiB** socket（`2097152`）。不是本文新旋钮。 |
| **参考 / 吸收** | 公开页可核验，**未**写成现网配置 | Orbbec `1048576`、Autoware 接收窗 + ROS 2 `MinimumSocketReceiveBufferSize` ~10MB、loaned + data-sharing |
| **Hold** | 明确不打开 | Agnocast、zenoh、Vendor Isaac / NITROS 落地 |

---

## 1. Orbbec Fast-DDS 大缓冲（链 A 参考）

来源（须原页）：[OrbbecSDK ROS2 — Fast DDS Optimization for Orbbec Camera](https://orbbec.github.io/OrbbecSDK_ROS2/en/source/camera_devices/5_advanced_guide/performance/fastdds_tuning.html)。

奥比中光在相机大图传输页给出一份 **厂商示例** `shm_fastdds.xml`。他们展示的 socket / transport 缓冲是 **1048576（1 MiB）**：

| 厂商示例字段 | 他们写出的值 | 本仓标签 |
|--------------|--------------|----------|
| `<sendBufferSize>` / `<receiveBufferSize>`（UDPv4 transport） | `1048576` | **参考，不是我们的 XML** |
| `<sendSocketBufferSize>` / `<listenSocketBufferSize>`（participant） | `1048576` | **参考，不是我们的 XML** |

同页还示范：关 builtin transports、只挂 UDP、`initialPeersList` 指 `127.0.0.1`、以及 `RMW_FASTRTPS_USE_QOS_FROM_XML=1`。那是 **Orbbec 相机镜像 tuning 示例**，不是本仓契约，也**不要**抄进 `config/fastdds.xml`。

**本仓已采用的是另一组数。** 链 A iter2 在默认 participant 上把 send/listen socket 调到 **2 MiB（`2097152`）**，假设与落地见 [`2026-09-10-iter2-after/change.md`](../artifacts/bench/2026-09-10-iter2-after/change.md) 与 [`config/fastdds.zh.md`](../../config/fastdds.zh.md)。落地 XML 仍是 iter7 种子（builtin 开、中包 SHM、`send_buffers` 32 / `dynamic=false`）。**Orbbec 页只做吸收对照，不覆盖 iter2。**

不要从本稿推断：把 1 MiB 厂商示例「对齐」成我们的旋钮，或把他们的 UDP-only / localhost peer 当成跨机配方。

---

## 2. Autoware / Cyclone 接收窗（链 B 意识）

来源（须原页）：

1. [Autoware / Tier4 — Additional settings for developers](https://tier4.github.io/autoware-documentation/latest/installation/additional-settings-for-developers/)（DDS settings）
2. ROS 2 DDS tuning（Autoware 页指向的官方调参；Cyclone 节写明最小 socket 接收缓冲 ~10MB）：[Humble *DDS tuning*](https://docs.ros.org/en/humble/How-To-Guides/DDS-tuning.html)（现行 Humble 标签是 `<SocketReceiveBufferSize min="10MB"/>`）；旧发行版同节用 [`<MinimumSocketReceiveBufferSize>10MB</MinimumSocketReceiveBufferSize>`](https://docs.ros.org/en/foxy/How-To-Guides/DDS-tuning.html)

Tier4 开发者设置写明：Autoware 默认 Cyclone；**receive buffer 是关键参数**，不够大会丢点云 / 图像。他们的做法是 `CYCLONEDDS_URI` 指向一份本机 `cyclonedds_config.xml`，并：

```bash
sudo sysctl -w net.core.rmem_max=2147483647
```

官方 ROS 2 Cyclone 节把「内核 `rmem_max` + Cyclone 最小 socket 接收窗」绑在一起，示例量级是 **~10MB**（为约 9MB 可靠大包）。较新 Humble 页把元素改名为 `SocketReceiveBufferSize min="10MB"`；旧页名是 `MinimumSocketReceiveBufferSize`。本稿只记这个**公开量级与元素名**，**不在本仓发明 / 落盘 Cyclone XML**。

Autoware 示例 XML 还带 Eclipse 运行时文档里的其它片段（公开页可见 `65500B`、`500kB` 等）。那些同样是 **Tier4 开发者本机参考**，不是链 B 契约，也不是 Unitree `ChannelFactoryInitialize(0)` 的现网文件。

**链 B 意识：** DimOS 原生 Cyclone 域 **0**。本仓没有 `CYCLONEDDS_URI` 种子，也没有把 10MB 接收窗写进任何 XML。看到 Autoware 配方时，把它标成 **Chain B awareness / 开发者设置参考**，不要当成「本仓已调 Cyclone」。

跨机段 Autoware 只转述 ROS 2 的 `ipfrag_time=3` / `ipfrag_high_thresh=128MB`。那是内核碎片窗，**不是**本仓跨机 UDP 已通的证据。

---

## 3. Loaned messages + Fast-DDS data-sharing（同进程 / 同机零拷贝）

来源（须原页）：

1. [ROS 2 Jazzy — Configure Zero Copy Loaned Messages](https://docs.ros.org/en/jazzy/How-To-Guides/Configure-ZeroCopy-loaned-messages.html)
2. [ros2/rmw_fastrtps — Enable Zero Copy Data Sharing](https://github.com/ros2/rmw_fastrtps#enable-zero-copy-data-sharing)

公开要点（不改成本仓默认）：

- Loaned messages：应用向 RMW **借**消息缓冲，少一次应用↔RMW 拷贝。Jazzy 表：`rmw_fastrtps` **支持**；`rmw_cyclonedds` **不支持**。
- Fast-DDS data-sharing + SHM transport：加速 **intra-host**。`rmw_fastrtps` README 写明：默认 intra-host 走 SHM，**inter-host 仍是 UDPv4**。
- 完整零拷贝管线要 **loaned API + data-sharing**。Humble 还要求 POD，并加载 data-sharing XML，且 `RMW_FASTRTPS_USE_QOS_FROM_XML=1`。Iron+ 对 POD 的 loan 要求更松。
- 这是 **同进程 / 同机** 路径。跨进程、跨容器、跨主机仍要序列化 + UDP（或其它网络传输）。

**不解跨机 UDP。** 本仓 `cross-host-UDP` 仍是单机 blocked 拓扑，见 [benchmark-dds.md](../usage/benchmark-dds.md)。SCOREBOARD iter10 已写明：打开 `historyMemoryPolicy` / `publishMode` / data-sharing 需要额外 `RMW_FASTRTPS_USE_QOS_FROM_XML` 与 writer/reader profile，**不是**「一个 XML 旋钮」；本文不推翻那条，也不改记分板。

### 与 NITROS 对照（不矛盾 Vendor Isaac = Hold）

[NITROS vs 双链](nitros-vs-dual-chain.md) 谈的是 **同进程 GPU handle**（Humble 类型适配/协商）。本稿这条是 **RMW / Fast-DDS 消息借出 + data-sharing**，停在 CPU 侧 intra-host。两套都是「同机少拷」，都**不能**代替：

- 跨机 UDP（仍 blocked）
- 域 42 / 域 0 隔离
- 链 A 已落地的 Fast-DDS XML 旋钮

Vendor Isaac / `isaac_ros_nitros` 仍是 **Hold**。不要把 loaned / data-sharing 写成「NITROS 本仓实现」，也不要为了零拷贝去 vendor Isaac 或改 XML。

---

## 4. 对照总表

| 实践 | 链 | 公开值 / 说法 | 本仓动作 |
|------|----|----------------|----------|
| Orbbec Fast-DDS 大缓冲 | A | 示例 `send/receiveBufferSize` 与 `send/listenSocketBufferSize` = **1048576** | **参考。** 已采用的是 iter2 **2097152**，不是 1 MiB 厂商示例。 |
| Autoware / ROS 2 Cyclone 接收窗 | B | `rmem_max` 拉满；`MinimumSocketReceiveBufferSize` / `SocketReceiveBufferSize min` ≈ **10MB** | **参考 / 意识。** 不发明 Cyclone XML。 |
| Loaned + Fast-DDS data-sharing | A（RMW） | 同进程 / 同机零拷贝；跨机仍 UDP | **参考。** 不启用、不改默认、不解跨机。 |
| Agnocast / zenoh / Vendor Isaac | — | 场外加速叙事 | **Hold** |

---

## 5. 公开引用

查阅按仓库工作日 **2026-09-12**。只列本文用过的链接：

1. OrbbecSDK V2 ROS2 Wrapper — *5.1.3 Fast DDS Optimization for Orbbec Camera with ROS2*：<https://orbbec.github.io/OrbbecSDK_ROS2/en/source/camera_devices/5_advanced_guide/performance/fastdds_tuning.html>
2. Autoware Documentation — *Additional settings for developers*（DDS settings）：<https://tier4.github.io/autoware-documentation/latest/installation/additional-settings-for-developers/>
3. ROS 2 Humble — *DDS tuning information*（Cyclone 最小接收窗；现行元素名 `SocketReceiveBufferSize`）：<https://docs.ros.org/en/humble/How-To-Guides/DDS-tuning.html>
4. ROS 2 Foxy — *DDS tuning information*（同节旧名 `MinimumSocketReceiveBufferSize` = 10MB）：<https://docs.ros.org/en/foxy/How-To-Guides/DDS-tuning.html>
5. ROS 2 Jazzy — *Configure Zero Copy Loaned Messages*：<https://docs.ros.org/en/jazzy/How-To-Guides/Configure-ZeroCopy-loaned-messages.html>
6. ros2/rmw_fastrtps README — *Enable Zero Copy Data Sharing*：<https://github.com/ros2/rmw_fastrtps#enable-zero-copy-data-sharing>
7. 本仓双链冻结：[ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md)
8. 本仓 NITROS 对照（Vendor Isaac = Hold）：[nitros-vs-dual-chain.md](nitros-vs-dual-chain.md)
