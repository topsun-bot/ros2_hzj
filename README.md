# ros2_hzj

独立仓 [`topsun-bot/ros2_hzj`](https://github.com/topsun-bot/ros2_hzj)（桦之坚 ROS 2 / DDS 工作流）。

**本仓目标：** 把公开 RMW / Fast-DDS / CycloneDDS 源码和 DimOS 双链相关代码落到**本仓自己的树里**，并做 R1–R5 **行为不变**的结构抽出。  
**不进** [`topsun_dimos`](https://github.com/topsun-bot/topsun_dimos)。`topsun_dimos` 只读，本工作流不在那边改代码、不开 PR。

DimOS 已拷文件**保持原样**（不做功能重构）。默认 DimOS 传输仍是 **LCM**（Linux）/ **SHM**（Darwin）；**LCM 不在本仓 DDS 范围**。

## 双链契约

这是**两条栈**，不共享域、RMW 或 QoS，除非操作员显式对齐。混用默认值是发现失败，不是单栈时延 bug。

两条栈的公开实现都已经是**本仓 vendor 普通目录**（不是 submodule）：

| 链 | 角色 | 契约 | 本仓 vendor |
|----|------|------|-------------|
| **A — nav FastDDS** | 导航 / Foxglove / ROS 2 RMW | RMW `rmw_fastrtps_cpp`，`ROS_DOMAIN_ID=42`，[`config/fastdds.xml`](config/fastdds.xml) | `vendor/rmw`、`vendor/rmw_implementation`、`vendor/rmw_fastrtps`、`vendor/Fast-DDS` |
| **B — DimOS Cyclone** | DimOS 原生 DDS / Unitree | Cyclone **域 0**；Unitree `ChannelFactoryInitialize(0)`；ROS 2 侧实现名 `rmw_cyclonedds_cpp` | `vendor/rmw_cyclonedds`、`vendor/CycloneDDS` |

本仓**没有**自定义 RMW。环境变量见 [`config/env/`](config/env/)（需操作员显式 source / apply，**不会**在 import 时改运行时默认值）。

`config/fastdds.xml` 是 R0 契约种子：`topsun_dimos` `main` **没有** `fastdds.xml` / `docker/navigation/`。不要当成从 DimOS 抽出的现网配置。说明见 [`config/fastdds.zh.md`](config/fastdds.zh.md)。

## 目录地图

| 路径 | 内容 |
|------|------|
| [`vendor/`](vendor/) | 公开栈**完整源码拷贝**（链 A Fast-DDS + 链 B Cyclone）。不是 submodule。 |
| [`vendor/VERSIONS.md`](vendor/VERSIONS.md) | 上游 URL + 完整 SHA / 标签 |
| [`dimos_bridge/`](dimos_bridge/) | 从 `topsun_dimos` **整文件拷贝**的双链相关代码（相对路径不变） |
| [`config/fastdds.xml`](config/fastdds.xml) | 链 A 域 42 契约种子（非 main 提取） |
| [`config/env/`](config/env/) | R1 双链环境变量（文档 + helper，不静默改默认） |
| [`config/topics.yaml`](config/topics.yaml) | R4 冻结 topic/QoS 常量（镜像 Python 模块） |
| [`docker/ros/`](docker/ros/) | R3 Dockerfile 拆分（base / runtime）；原路径仍是兼容包装 |
| [`docs/`](docs/) | R0 冻结、transports、[评测怎么跑](docs/usage/benchmark-dds.md) |

`dimos_bridge/` 下真实拷贝包括：`docker/ros/`、`ddspubsub.py` / `rospubsub*.py`、`ddsservice.py`、pubsub `spec`/`patterns`/`encoders`、`benchmark/`、`transport.py`、Foxglove 桥、Go2 ROS blueprint、G1 `dds_sdk.py`、`scripts/run_greeter_dds_lite.py`。清单见 [`dimos_bridge/SOURCE.md`](dimos_bridge/SOURCE.md)。

## 分支约定

| 分支 | 用途 |
|------|------|
| `main` | 稳定（R0 文档 + R1 vendor 种子） |
| `feat/...` | 功能分支 |
| **本 PR 分支** | `feat/r1-cyclone-vendor-and-structure-r1-r5` |

禁止把外部 GitHub URL 当源码真相；**以本仓拷贝为准**。禁止 submodule / subtree 远端跟踪 / 指向外部仓的符号链接。

## Vendor 上游 SHA

链 A 拷贝日期 2026-09-10（浅克隆 default branch）。链 B 同日：`rmw_cyclonedds` 取 `rolling` HEAD；`CycloneDDS` 取稳定标签 `11.0.1`。

| 树 | SHA | 备注 |
|----|-----|------|
| `vendor/rmw` | `1e58706ed978ff8a9066f17dc11c61d3a644bf76` | `rolling` / tag `7.11.2` |
| `vendor/rmw_implementation` | `ff8818df2328396011543db07e8ddca99b54345a` | `rolling` |
| `vendor/rmw_fastrtps` | `83471d45c448dfc7f4d408bc36cff593df14eb90` | `rolling` |
| `vendor/Fast-DDS` | `343f155c36b561db3d9f047a65d866ce0f3da300` | `master`（近旁稳定 tag `v3.6.2`） |
| `vendor/rmw_cyclonedds` | `19478b0a9aa523af62023812d05bfcb4295e8efb` | `rolling` / tag `4.2.1` |
| `vendor/CycloneDDS` | `e54e991f75a3e67f8e628da3171122e36ea5b872` | 稳定 tag `11.0.1` |
| DimOS 拷贝源 | `a5259958db23c8ea6648544ed138eab19726ce93` | `topsun_dimos` `main` |

Fast-DDS 原 gitlink（`asio` / `fastcdr` / `tinyxml2` 等）已摊成普通目录，SHA 见 [vendor/VERSIONS.md](vendor/VERSIONS.md)。Cyclone 树无待摊 gitlink。

## R0 文档（保留）

| 文档 | 路径 |
|------|------|
| 接口冻结（双链、topic/QoS、闸门） | [`docs/architecture/ros2-dds-r0-interface-freeze.md`](docs/architecture/ros2-dds-r0-interface-freeze.md) |
| 链 B Cyclone 安装（系统侧参考；源码已 vendor） | [`docs/usage/transports/dds.md`](docs/usage/transports/dds.md) |
| Transports 总览 | [`docs/usage/transports/index.md`](docs/usage/transports/index.md) |
| 双链 bench 怎么跑（无伪造分数） | [`docs/usage/benchmark-dds.md`](docs/usage/benchmark-dds.md) |

R0 源：`topsun_dimos` PR [#122](https://github.com/topsun-bot/topsun_dimos/pull/122)。冻结表本身未改；仅补充本仓路径。

## R1–R5 结构抽出（行为不变）

| 项 | 落点 | 行为 |
|----|------|------|
| R1 env | [`config/env/`](config/env/) | 文档 + shell/Python helper；**不**在 import 时改 DimOS 默认 |
| R2 `fastdds.xml` | [`config/fastdds.xml`](config/fastdds.xml)、[`config/fastdds.zh.md`](config/fastdds.zh.md) | 契约种子对齐冻结表域 42；helper 指向它 |
| R3 Dockerfile | [`docker/ros/`](docker/ros/)、原路径包装 | 安装语义不变 |
| R4 topic 常量 | [`config/topics.yaml`](config/topics.yaml)、[`dimos_bridge/dimos/protocol/dds_topics.py`](dimos_bridge/dimos/protocol/dds_topics.py) | 只抽常量，不改 publisher |
| R5 bench 文档 | [`docs/usage/benchmark-dds.md`](docs/usage/benchmark-dds.md) | 怎么跑；**无**伪造时延分数 |

仍 Hold：对照编译 vendor、中间件行为补丁、评测数字、安全。

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) 检查 R0 文档路径、vendor 目录存在（含 Cyclone）、R1–R5 结构产物、以及文档相对链接。  
**不在 CI 里完整编译 Fast-DDS / CycloneDDS。**

## 许可

根目录 [MIT](LICENSE)。`vendor/` 与 `dimos_bridge/` 保留各自上游许可（多为 Apache-2.0）。
