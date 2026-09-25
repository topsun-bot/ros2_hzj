# ros2_hzj

<div align="center">

# ros2_hzj

**桦之坚 ROS 2 / DDS 双链工作区**  
*Independent ROS 2 / DDS workspace for TOPSUN (hzj)*

[![Code](https://img.shields.io/badge/Code-topsun--bot%2Fros2__hzj-181717?logo=github&logoColor=white)](https://github.com/topsun-bot/ros2_hzj)
![Website](https://img.shields.io/badge/Website-TBD-lightgrey)
![Paper](https://img.shields.io/badge/Paper-TBD-lightgrey)
![Dataset](https://img.shields.io/badge/Dataset-TBD-lightgrey)
[![Docker](https://img.shields.io/badge/Docker-docs-2496ED?logo=docker&logoColor=white)](docker/ros/NOTES.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[新闻](#news) · [为何选择](#why-ros2_hzj) · [总体计划](#总体计划约一个月) · [Plugin](#量产可集成-plugin) · [交付物](#交付物) · [快速开始](#快速开始)

</div>

本仓库是 **TOPSUN / 桦之坚的 ROS 2 · DDS 工作线**，独立于 [`topsun_dimos`](https://github.com/topsun-bot/topsun_dimos)。目标是把公开 RMW / Fast-DDS / CycloneDDS 源码和 DimOS **双链相关**代码落到本仓自己的树里，并做 R1–R5 **行为不变**的结构抽出。`topsun_dimos` 只读：本工作流不在那边改代码、不开 PR。

默认 DimOS 传输仍是 **LCM**（Linux）/ **SHM**（Darwin）。**LCM 不在本仓 DDS 范围**。本仓**没有**自定义 RMW。

# News

- [2026.09.12] 飞书 wiki3 §13(4) Cega / Bridge **后置 Hold**：[feishu-cega-bridge-hold.md](docs/architecture/feishu-cega-bridge-hold.md) · `python3 scripts/check_cega_bridge_hold.py`。不接 Cega，不改 `dimos_bridge` 运行时。三条链 / DoD 仍 unmet / blocked。不改 XML / SCOREBOARD；不接 Agnocast / zenoh。
- [2026.09.12] 飞书 wiki3 §6.3 产品 DoD 仍 **unmet / STATUS: blocked**：[feishu-dod-evidence.md](docs/architecture/feishu-dod-evidence.md) · `python3 scripts/check_dod_evidence.py`。实编、modified `.so`、本机 baseline-vs-change、回滚、产品验收阈均未满足。`prove_rmw.py` 只是 env / 字符串身份闸。不改 XML / SCOREBOARD；不接 Agnocast / zenoh。
- [2026.09.12] 飞书 §13(3) 双链基线指针：[feishu-dual-chain-baseline.md](docs/architecture/feishu-dual-chain-baseline.md) · `python3 scripts/check_dual_chain_baseline.py`。SCOREBOARD current-best pointer only；same-topology XML tuning is paused；跨机 UDP `STATUS: blocked`；three-chain map≠reproduce；Unitree 0.10.2 vs vendor 11.0.1 drop-in FAIL。不改 XML / SCOREBOARD。
- [2026.09.12] 飞书《通信中间件》差异化下沉层：[feishu-sink-layers.md](docs/architecture/feishu-sink-layers.md) · `python3 scripts/check_sink_layers.py`。app / rcl / rmw / DDS / executor / memory 的 Hold vs allowed。派生自 ADR + 源码地图 + Executor 地图，不是 live Feishu excerpt。三条链 map ≠ reproduce；Unitree 0.10.2 vs vendor 11.0.1 drop-in FAIL。不改 XML / SCOREBOARD；不接 Agnocast / zenoh。
- [2026.09.12] 飞书 wiki3 §13(2) 三条链复现：**map ≠ reproduce**，本主机 `STATUS: blocked`：[feishu-three-chain-repro.md](docs/architecture/feishu-three-chain-repro.md) · `python3 scripts/check_three_chain_repro.py`。有地图（[源码地图](docs/architecture/ros2-source-map.md) · [WaitSet](docs/architecture/feishu-executor-waitset.md)），未执行 publish / History / wait→callback。不编造 PASS / 时延。不改 XML / SCOREBOARD。
- [2026.09.12] Unitree SDK2 自带 Cyclone 0.10.2 **不是**本仓 vendor 11.0.1 的 drop-in：[unitree-sdk2-dds-swap.md](docs/architecture/unitree-sdk2-dds-swap.md) · `python3 scripts/check_unitree_cyclone_swap.py`。drop-in FAIL / wire UNPROVEN。默认 bundled 0.10.2；合法换库走 [`unitree_sdk2_hzj`](https://github.com/topsun-bot/unitree_sdk2_hzj) + opt-in `UNITREE_DDS_PROVIDER=external`（不是 in-place overwrite）。不改 XML / SCOREBOARD；不接 Agnocast / zenoh。
- [2026.09.12] Underlay / overlay / vendor snapshot 分层闸：[feishu-runtime-provenance.md](docs/architecture/feishu-runtime-provenance.md) · `python3 scripts/check_runtime_provenance.py`。Humble `/opt/ros/humble` ≠ rolling `vendor/`。不改 XML / SCOREBOARD。
- [2026.09.12] Executor · WaitSet · callback 身份闸：[feishu-executor-waitset.md](docs/architecture/feishu-executor-waitset.md) · `python3 scripts/check_executor_map.py`。Humble `rclcpp`/`rclpy` 不在 vendor。不改 XML / SCOREBOARD。
- [2026.09.12] [PR #28](https://github.com/topsun-bot/ros2_hzj/pull/28) 时延归因闸门 + [PR #29](https://github.com/topsun-bot/ros2_hzj/pull/29) 飞书 wiki3 §9.4 风险矩阵：[latency-attribution.md](docs/architecture/latency-attribution.md) · [feishu-risk-matrix.md](docs/architecture/feishu-risk-matrix.md)。不改 `fastdds.xml` / SCOREBOARD；不接 Agnocast / zenoh / Cega。
- [2026.09.12] 飞书三份中间件计划对照本仓：[ADR](docs/architecture/feishu-middleware-adr.md) · [源码地图](docs/architecture/ros2-source-map.md)。不改 `fastdds.xml` / SCOREBOARD；不接 Agnocast / zenoh / Cega。
- [2026.09.12] 中日公开 ROS 2 / DDS 做法只进文档：[cn-jp-ros2-absorb.md](docs/architecture/cn-jp-ros2-absorb.md)。不改 `fastdds.xml` / SCOREBOARD。
- [2026.09.11] README 按 HoloMotion 结构重排：亮点、计划模板、Plugin 面与交付物清单（空项标 TBD，不编造链接）。
- [2026.09.10] `main` 合入 [PR #11](https://github.com/topsun-bot/ros2_hzj/pull/11)：iter6 IMU 尺度（64 B / 200 Hz）抖动基线；`port_queue_capacity` 探测未保留。
- [2026.09.10] [PR #6](https://github.com/topsun-bot/ros2_hzj/pull/6)–[#10](https://github.com/topsun-bot/ros2_hzj/pull/10)：链 A `fastdds.xml` 单旋钮迭代（Humble `historyQos`、UDP socket buffer、send-buffer 池、中包 SHM）并落盘重测。
- [2026.09.10] [PR #4](https://github.com/topsun-bot/ros2_hzj/pull/4)–[#5](https://github.com/topsun-bot/ros2_hzj/pull/5)：双链 bench 写入 p50 / p95 / p99 产物（链 A / 链 B 分表；跨机 UDP 标 blocked）。
- [2026.09.10] [PR #3](https://github.com/topsun-bot/ros2_hzj/pull/3)：vendor Cyclone + R1–R5 结构抽出（env / XML 种子 / Dockerfile 拆分 / topic 常量 / bench 说明）。
- [2026.09.10] [PR #2](https://github.com/topsun-bot/ros2_hzj/pull/2)：vendor Fast-DDS / RMW 整树 + DimOS 双链整文件拷贝。
- [2026.09.10] [PR #1](https://github.com/topsun-bot/ros2_hzj/pull/1)：R0 接口冻结与双链骨架。

# Why ros2_hzj

## 两条栈，不共享默认值

这是**两条栈**，不共享域、RMW 或 QoS，除非操作员显式对齐。混用默认值是**发现失败**，不是单栈时延 bug。公开实现都是本仓 `vendor/` **普通目录**（不是 submodule）。

| 链 | 角色 | 契约 | 本仓 vendor |
|----|------|------|-------------|
| **A — nav FastDDS** | 导航 / Foxglove / ROS 2 RMW | `rmw_fastrtps_cpp`，`ROS_DOMAIN_ID=42`，[`config/fastdds.xml`](config/fastdds.xml) | `vendor/rmw`、`vendor/rmw_implementation`、`vendor/rmw_fastrtps`、`vendor/Fast-DDS` |
| **B — DimOS Cyclone** | DimOS 原生 DDS / Unitree | Cyclone **域 0**；Unitree `ChannelFactoryInitialize(0)`；ROS 2 侧 `rmw_cyclonedds_cpp` | `vendor/rmw_cyclonedds`、`vendor/CycloneDDS` |

环境变量见 [`config/env/`](config/env/)：必须操作员显式 `source` / apply，**不会**在 import 时改运行时默认值。

`config/fastdds.xml` 是 R0 **契约种子**：`topsun_dimos` `main` **没有** `fastdds.xml` / `docker/navigation/`。不要当成从 DimOS 抽出的现网配置。说明见 [`config/fastdds.zh.md`](config/fastdds.zh.md)。

## 亮点与特色

这些能力来自本仓库已落地的目录与文档，**不是**未发表论文或已量产 SLA 的承诺。vendor 落盘或某条 RMW **不能**当成时延根因。

| 亮点 | 仓库中的落点 | 解决什么问题 |
|------|----------------|--------------|
| **双链隔离写进契约** | [R0 冻结](docs/architecture/ros2-dds-r0-interface-freeze.md)：域 42 vs 域 0 | 避免把「对不上 discovery」误诊成 Fast-DDS / Cyclone 时延 |
| **公开栈整树落盘** | [`vendor/`](vendor/) + [`vendor/VERSIONS.md`](vendor/VERSIONS.md) | 以本仓拷贝为准，禁止 submodule / 外部 gitlink 当源码真相 |
| **行为不变的结构抽出** | R1 env、R2 XML 种子、R3 Dockerfile 拆分、R4 topic 常量、R5 bench 说明 | 先抽出可对照的面，不改已拷 DimOS 模块行为 |
| **显式 env，不静默改默认** | [`config/env/`](config/env/)、[`dimos_bridge/dual_chain_env.py`](dimos_bridge/dual_chain_env.py) | Humble 未 source 时仍是发行版 RMW / 域 0 |
| **冻结 topic / QoS 常量** | [`config/topics.yaml`](config/topics.yaml)、[`dds_topics.py`](dimos_bridge/dimos/protocol/dds_topics.py) | 导航契约与 `DimosROS` 库默认（depth=5000）分开；publisher **尚未**改接 |
| **可复现 bench，禁止假分数** | [`scripts/bench/`](scripts/bench/README.md)、[`docs/artifacts/bench/`](docs/artifacts/bench/README.md) | 分链、分拓扑写 p50/p95/p99；缺环境就写 `STATUS: blocked` |
| **DimOS 双链子集整文件拷贝** | [`dimos_bridge/`](dimos_bridge/)（相对路径不变） | 对照 `ROSTransport` / `DDSTransport` / Go2 ROS 绑定，而不搬整个 monorepo |

完整冻结表、闸门与 live-tree drift：[docs/architecture/ros2-dds-r0-interface-freeze.md](docs/architecture/ros2-dds-r0-interface-freeze.md)。

## 论文点

### 已发表论文

暂无。本仓库没有 `CITATION.cff` / `CITATION.bib`，也没有已登记的 arXiv / 会议论文链接。

### 开放研究点

下列是可从现有代码与 bench 产物追问的**候选方向**，不是已发表贡献，也未绑定作者或实验结论。

- 双链隔离：域 42 Fast-DDS 与域 0 Cyclone 混用时，如何把 discovery 失败从单栈时延里拆开。
- 契约 QoS vs 库默认：冻结表导航 QoS 与 `DimosROS` / `RawROS`（`RELIABLE` / `KEEP_LAST` / `VOLATILE` / `depth=5000`）不一致时，评测到底测的是哪一层。
- Fast-DDS XML 单旋钮：socket buffer、send-buffer 池、中包 SHM 对 **同链同拓扑同尺寸** 分位数的影响（见 iter1–iter5 产物；**不要**合成 A/B 对照表）。
- IMU 尺度高频小包：64 B / 200 Hz 下以 **jitter**（RTT p95/p99 与到达间隔）为主指标，而不是 p50/均值（iter6）。
- vendor 整树 vs 发行版 RMW：对照编译、中间件行为补丁仍 Hold；本仓没有自定义 RMW。
- 缺件诚实记录：单机上 `cross-host-UDP` 必须标 blocked，而不是填假分位数。
- 公开 Isaac NITROS（Humble 类型适配/协商、同进程 GPU 零拷贝）能帮 CPU↔加速器，**不能**代替跨机 UDP、域 42/0 隔离或 Fast-DDS XML 旋钮；Vendor Isaac = Hold。对照：[NITROS vs 双链](docs/architecture/nitros-vs-dual-chain.md)。

# 总体计划（约一个月）

仓库内没有人员花名册或已签字的排期文档。下表是空模板，**请勿把空单元格当成已分配任务**。

> 人员与排期待填

## 人员分工

| Role | Owner | Feature | Scenario | Week |
|------|-------|---------|----------|------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |

## 功能与场景

| 功能 | 场景 | 要解决的问题 | Owner | 周次 |
|------|------|--------------|-------|------|
| | | | | |
| | | | | |
| | | | | |

## 里程碑

| 周次 | 目标 | 交付 | 状态 |
|------|------|------|------|
| W1 | | | 待填 |
| W2 | | | 待填 |
| W3 | | | 待填 |
| W4 | | | 待填 |

R0 文档已标 **仍 Hold**：对照编译 vendor、中间件行为补丁、评测数字当根因、安全。不要把空计划表填成这些 Hold 项已经排期。

# 量产可集成 Plugin

本仓**不是**带自己 `src/` overlay 的现成 colcon 工作区，也**没有**第一方 `.launch.py` / 自定义 `.msg` / `.srv` / `.action`。量产集成面是已经存在的 ROS 2 包、配置、拷贝模块与脚本。未单独评估过产线 SLA 的条目一律标 **状态待评估**。

`docker/navigation/`、`twist_relay.py`、`goal_autonomy_relay.py` 在 DimOS `main` **不存在**，本仓不伪造。Zenoh 在拷贝里只是空 stub，**不是**可用路径。

## ROS 2 包（vendor 上游拷贝）

| 包 / 树 | 链 | 作用 | 状态 |
|---------|----|------|------|
| `rmw_fastrtps_cpp`（[`vendor/rmw_fastrtps`](vendor/rmw_fastrtps/)） | A | 契约 RMW 名 | 状态待评估 |
| `rmw_fastrtps_shared_cpp` / `rmw_fastrtps_dynamic_cpp` | A | Fast-DDS RMW 共享 / 动态类型 | 状态待评估 |
| `fastdds`（[`vendor/Fast-DDS`](vendor/Fast-DDS/)） | A | Fast-DDS 实现 | 状态待评估 |
| `rmw` / `rmw_implementation` | A/B | ROS 2 RMW API 与装载 | 状态待评估 |
| `rmw_cyclonedds_cpp`（[`vendor/rmw_cyclonedds`](vendor/rmw_cyclonedds/)） | B | ROS 2 侧 Cyclone RMW | 状态待评估 |
| `cyclonedds`（[`vendor/CycloneDDS`](vendor/CycloneDDS/)） | B | Cyclone 实现（钉扎 tag `11.0.1`） | 状态待评估 |

CI **不**完整编译这些树。SHA 见 [`vendor/VERSIONS.md`](vendor/VERSIONS.md)。

## 配置与接口（本仓抽出，不是 launch）

| 集成面 | 路径 | 怎么挂 | 状态 |
|--------|------|--------|------|
| 链 A / 链 B env | [`config/env/`](config/env/) | `source chain_a.sh` / `chain_b.sh` 或 `load.py` 显式 apply | 状态待评估 |
| Fast-DDS 契约 XML | [`config/fastdds.xml`](config/fastdds.xml) | `FASTRTPS_DEFAULT_PROFILES_FILE` 指向它 | 状态待评估 |
| Topic / QoS 常量 | [`config/topics.yaml`](config/topics.yaml)、[`dds_topics.py`](dimos_bridge/dimos/protocol/dds_topics.py) | 只提供名字；**未**接到 publisher | 状态待评估 |
| Humble 运行时镜像配方 | [`docker/ros/`](docker/ros/NOTES.md) | `docker build -f docker/ros/Dockerfile .` | 状态待评估 |

冻结的导航接口（契约，不是本仓节点实现）：

| Surface | 类型 | QoS / 备注 |
|---------|------|------------|
| 发现域（链 A） | `ROS_DOMAIN_ID` | **42** |
| `/foxglove_teleop` → `/cmd_vel` | `Twist` → `TwistStamped` | `BEST_EFFORT`，`KEEP_LAST`，`depth=1` |
| `/goal_pose` | `PoseStamped` | `RELIABLE`，`VOLATILE`，`KEEP_LAST`，`depth=5` |
| `/way_point` | `PointStamped` | 同上 |
| `/joy` | `Joy` | 只冻结名字 |
| Go2 `lidar` / `global_map` / `odom` / `color_image` | `PointCloud2` / `PoseStamped` / `Image` | `unitree_go2_ros.py` 绑定；本仓无对应 launch |

## DimOS 拷贝模块（整文件，行为不变）

清单与 SHA：[dimos_bridge/SOURCE.md](dimos_bridge/SOURCE.md)。完整 DimOS 依赖仍在上游；本仓有 `__init__.py` / ImportError stub，**stub 不是运行时**。

| 模块 | 路径 | 形态 | 状态 |
|------|------|------|------|
| `ROSTransport` / `DimosROS` / `RawROS` | `dimos_bridge/dimos/core/transport.py`、`protocol/pubsub/impl/rospubsub.py` | 链 A 桥到当前 RMW | 状态待评估 |
| `DDSTransport` / `DDS` / `DDSService` | `transport.py`、`ddspubsub.py`、`ddsservice.py` | 链 B 原生 Cyclone，域默认 0 | 状态待评估 |
| Go2 ROS blueprint | `dimos_bridge/dimos/robot/unitree/go2/blueprints/smart/unitree_go2_ros.py` | 四条 `ROSTransport` 绑定 | 状态待评估 |
| G1 `dds_sdk.py` | `dimos_bridge/dimos/robot/unitree/g1/effectors/high_level/dds_sdk.py` | Unitree / Cyclone 高阶接口拷贝 | 状态待评估 |
| Foxglove 桥 | `dimos_bridge/dimos/robot/foxglove_bridge.py`、`utils/cli/foxglove_bridge/` | DimOS 拷贝；不是本仓独立节点包 | 状态待评估 |
| pubsub bench | `dimos_bridge/dimos/protocol/pubsub/benchmark/` | pytest `-m tool`；默认 `addopts` 会排除 | 状态待评估 |
| `run_greeter_dds_lite.py` | `dimos_bridge/scripts/run_greeter_dds_lite.py` | 上游脚本拷贝；依赖不在本仓补齐 | 状态待评估 |

Humble 镜像（[`docker/ros/install-runtime.sh`](docker/ros/install-runtime.sh)）安装发行版包：`desktop`、Nav2、`foxglove-bridge`、`joy` / `teleop-twist-joy`、`slam-toolbox` 等。镜像**不**设置 `RMW_IMPLEMENTATION` / `ROS_DOMAIN_ID` / `FASTRTPS_*`。这些是发行版包，不是本仓第一方 plugin。

# 交付物

只链接着陆在本仓库或已核对的公开地址。没有的条目保持 TBD，不编造 arXiv、数据集主页或 DockerHub 宣传 tag。

| 交付物 | 状态 | 链接 / 路径 |
|--------|------|-------------|
| 网站 | 无 | TBD |
| Code | 有 | [topsun-bot/ros2_hzj](https://github.com/topsun-bot/ros2_hzj) |
| 论文 | 无 | TBD（无 CITATION，无已发表论文条目） |
| 数据集 | 无公开发布集 | TBD。[`docs/artifacts/bench/`](docs/artifacts/bench/README.md) 是测量记录（分位数 / blocked），不是对外数据集主页 |
| Docker | 源码配方，无已核验的公开 tag | [`docker/ros/`](docker/ros/NOTES.md)；无 DockerHub / GHCR 宣传 tag |

### Docker 实际存在什么

| 路径 | 作用 |
|------|------|
| [`docker/ros/Dockerfile`](docker/ros/Dockerfile) | Humble `base` → `runtime` 组装 |
| [`install-base.sh`](docker/ros/install-base.sh) / [`install-runtime.sh`](docker/ros/install-runtime.sh) | 拆出的安装阶段（R3，安装语义不变） |

```bash
# 必须从仓库根做 context
docker build -f docker/ros/Dockerfile .
```

`dimos_bridge/docker/ros/Dockerfile` 历史包装**不在本树**。本拆分**没有**导航专用镜像，也没有写入域 42。不要把未核验的 DockerHub 宣传 tag 当成已发布制品。

# 快速开始

本仓第一方入口是**文档、配置、vendor 拷贝与 bench 脚本**。CI 检查路径与相对链接，**不**在 CI 里完整编译 Fast-DDS / CycloneDDS。根目录没有可 `colcon build` 的自有 overlay；镜像里装了 `python3-colcon-common-extensions`，那是 Humble 运行时依赖，不是本仓工作区配方。上游 vendor 各自 README 里的 colcon 步骤属于那些拷贝，**不是**本仓 Quick start。

## 克隆

```bash
git clone https://github.com/topsun-bot/ros2_hzj.git
cd ros2_hzj
```

禁止把外部 GitHub URL 当源码真相；**以本仓拷贝为准**。禁止 submodule / subtree 远端跟踪 / 指向外部仓的符号链接。

## 对齐一条链（显式）

```bash
# 链 A — Fast-DDS / 域 42 / 指向 config/fastdds.xml
source config/env/chain_a.sh
# 或
python3 config/env/load.py print-a
eval "$(python3 config/env/load.py export-a)"

# 链 B — 仅当同机 ROS 2 客户端要对齐 Cyclone 域 0
source config/env/chain_b.sh
```

`import` helper **不会**改 `os.environ`。未 source 时不要假设域 42 已生效。

## 构建 Humble 镜像

```bash
docker build -f docker/ros/Dockerfile .
```

说明：[docker/ros/NOTES.md](docker/ros/NOTES.md)。镜像不钉 RMW / 域；运行时再 `source config/env/chain_a.sh`。

## 跑双链 bench

前置与限制见 [docs/usage/benchmark-dds.md](docs/usage/benchmark-dds.md)。链 A 与链 B **不要**放进同一张对照表。

```bash
# 链 B：原生 Cyclone（不要 source chain_a.sh）
./scripts/bench/run_chain_b.sh

# 链 A：本机有 Humble 时
source /opt/ros/humble/setup.bash
source config/env/chain_a.sh
./scripts/bench/run_chain_a.sh

# 本机没有 Humble：用 docker/ros 或已有镜像，运行时再 source 链 A
./scripts/bench/docker_chain_a.sh
```

已落盘产物：[`docs/artifacts/bench/`](docs/artifacts/bench/README.md)（2026-09-10 基线与 iter1–iter6）。数字不是飞书现场 / 实机 / 跨机根因。`cross-host-UDP` 在单机上为 blocked。

完整 DimOS extra、消息类型、非 stub 模块仍在 [`topsun_dimos`](https://github.com/topsun-bot/topsun_dimos)。本仓缺依赖时命令会在 import 处失败——那是环境问题，不是「已经测过」。

## 目录地图

| 路径 | 内容 |
|------|------|
| [`vendor/`](vendor/) | 公开栈完整源码拷贝（链 A Fast-DDS + 链 B Cyclone） |
| [`dimos_bridge/`](dimos_bridge/) | DimOS 双链整文件拷贝（相对路径不变） |
| [`config/fastdds.xml`](config/fastdds.xml) | 链 A 域 42 契约种子（非 main 提取） |
| [`config/env/`](config/env/) | R1 双链环境变量（文档 + helper） |
| [`config/topics.yaml`](config/topics.yaml) | R4 冻结 topic/QoS 常量 |
| [`docker/ros/`](docker/ros/) | R3 Dockerfile 拆分 |
| [`docs/`](docs/) | R0 冻结、transports、[评测怎么跑](docs/usage/benchmark-dds.md) |
| [`scripts/bench/`](scripts/bench/README.md) | 双链 bench runner |

## 文档

- [R0 接口冻结](docs/architecture/ros2-dds-r0-interface-freeze.md) · [NITROS vs 双链](docs/architecture/nitros-vs-dual-chain.md) · [中日 ROS 2 吸收](docs/architecture/cn-jp-ros2-absorb.md) · [飞书中间件 ADR](docs/architecture/feishu-middleware-adr.md) · [源码地图](docs/architecture/ros2-source-map.md) · [Executor / WaitSet](docs/architecture/feishu-executor-waitset.md) · [三条链复现（blocked）](docs/architecture/feishu-three-chain-repro.md) · [运行时 provenance](docs/architecture/feishu-runtime-provenance.md) · [下沉层 Hold vs allowed](docs/architecture/feishu-sink-layers.md) · [Unitree SDK2 DDS swap（drop-in FAIL）](docs/architecture/unitree-sdk2-dds-swap.md) · [§13(3) 双链基线指针](docs/architecture/feishu-dual-chain-baseline.md) · [产品 DoD（unmet / blocked）](docs/architecture/feishu-dod-evidence.md) · [Cega / Bridge Hold（§13(4)）](docs/architecture/feishu-cega-bridge-hold.md) · [时延归因（不抄 SCOREBOARD 数字）](docs/architecture/latency-attribution.md) · [风险矩阵 §9.4（不打分）](docs/architecture/feishu-risk-matrix.md) · [Transports](docs/usage/transports/index.md) · [DDS 安装（链 B 参考）](docs/usage/transports/dds.md)
- [Bench 怎么跑](docs/usage/benchmark-dds.md) · [Bench 产物](docs/artifacts/bench/README.md)
- [env helper](config/env/README.md) · [fastdds.xml 说明](config/fastdds.zh.md) · [vendor SHA](vendor/VERSIONS.md)

## CI

Hold 阶段闸门（`structure` / `contracts` / `boundary`）见 [docs/architecture/ci-cd-gates.md](docs/architecture/ci-cd-gates.md)。工作流：[`.github/workflows/ci.yml`](.github/workflows/ci.yml)。源码地图机械核对：`python3 scripts/check_source_map.py`（无 ROS；见 [ros2-source-map.md](docs/architecture/ros2-source-map.md)）。WaitSet → callback：`python3 scripts/check_executor_map.py`（无 ROS；见 [feishu-executor-waitset.md](docs/architecture/feishu-executor-waitset.md)）。三条链复现（map ≠ reproduce / `STATUS: blocked`）：`python3 scripts/check_three_chain_repro.py`（无 ROS；见 [feishu-three-chain-repro.md](docs/architecture/feishu-three-chain-repro.md)）。underlay ≠ vendor snapshot：`python3 scripts/check_runtime_provenance.py`（无 ROS；见 [feishu-runtime-provenance.md](docs/architecture/feishu-runtime-provenance.md)）。下沉层 Hold vs allowed：`python3 scripts/check_sink_layers.py`（无 ROS；见 [feishu-sink-layers.md](docs/architecture/feishu-sink-layers.md)）。Unitree 0.10.2 vs vendor 11.0.1：`python3 scripts/check_unitree_cyclone_swap.py`（无 ROS；见 [unitree-sdk2-dds-swap.md](docs/architecture/unitree-sdk2-dds-swap.md)；drop-in FAIL / wire UNPROVEN）。§13(3) 双链基线指针：`python3 scripts/check_dual_chain_baseline.py`（无 ROS；见 [feishu-dual-chain-baseline.md](docs/architecture/feishu-dual-chain-baseline.md)；SCOREBOARD pointer only；no XML rewrite）。§6.3 产品 DoD（unmet / blocked）：`python3 scripts/check_dod_evidence.py`（无 ROS；见 [feishu-dod-evidence.md](docs/architecture/feishu-dod-evidence.md)）。§13(4) Cega / Bridge Hold：`python3 scripts/check_cega_bridge_hold.py`（无 ROS；见 [feishu-cega-bridge-hold.md](docs/architecture/feishu-cega-bridge-hold.md)）。bench 指针 / 跨机 STATUS：`python3 scripts/print_bench_gates.py`（无 ROS；见 [latency-attribution.md](docs/architecture/latency-attribution.md)）。§9.4 层序 / Hold 标记：`python3 scripts/check_risk_matrix.py`（无 ROS；见 [feishu-risk-matrix.md](docs/architecture/feishu-risk-matrix.md)）。

# Citation

暂无正式 citation。没有 `CITATION.cff` / `CITATION.bib`，也没有可引用的论文编号。需要引用本仓库时，请使用 Git URL 与 commit，待正式 bib 发布后再替换。

# Acknowledgements

本仓库 vendor 与 DimOS 拷贝致谢上游（本仓是 TOPSUN / 桦之坚工作线，不是这些项目的官方发行版）：

- [ros2/rmw](https://github.com/ros2/rmw)、[ros2/rmw_implementation](https://github.com/ros2/rmw_implementation)、[ros2/rmw_fastrtps](https://github.com/ros2/rmw_fastrtps)、[ros2/rmw_cyclonedds](https://github.com/ros2/rmw_cyclonedds) — ROS 2 RMW
- [eProsima/Fast-DDS](https://github.com/eProsima/Fast-DDS) — 链 A Fast-DDS
- [eclipse-cyclonedds/cyclonedds](https://github.com/eclipse-cyclonedds/cyclonedds) — 链 B CycloneDDS（本仓钉扎 `11.0.1`）
- [topsun-bot/topsun_dimos](https://github.com/topsun-bot/topsun_dimos)（上游 [dimensionalOS/dimos](https://github.com/dimensionalOS/dimos)）— 双链相关整文件拷贝，SHA 见 [dimos_bridge/SOURCE.md](dimos_bridge/SOURCE.md)

R0 文档源：`topsun_dimos` [PR #122](https://github.com/topsun-bot/topsun_dimos/pull/122)。冻结表本身未改；仅补充本仓路径。

根目录 [MIT](LICENSE)（Copyright 2026 topsun-bot / 桦之坚）。`vendor/` 与 `dimos_bridge/` 保留各自上游许可（多为 Apache-2.0 / EPL）。
