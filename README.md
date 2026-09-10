# ros2_hzj

独立仓 [`topsun-bot/ros2_hzj`](https://github.com/topsun-bot/ros2_hzj)（桦之坚 ROS 2 / DDS 工作流）。

**本仓目标：** 把公开 RMW / Fast-DDS 源码和 DimOS 双链相关代码落到**本仓自己的树里**，供后续 R1+ 抽出环境与对照。  
**不进** [`topsun_dimos`](https://github.com/topsun-bot/topsun_dimos)。`topsun_dimos` 只读，本工作流不在那边改代码、不开 PR。

DimOS 已拷文件**保持原样**（本 PR 不做功能重构）。默认 DimOS 传输仍是 **LCM**（Linux）/ **SHM**（Darwin）；**LCM 不在本仓 DDS 范围**。

## 双链契约

这是**两条栈**，不共享域、RMW 或 QoS，除非操作员显式对齐。混用默认值是发现失败，不是单栈时延 bug。

| 链 | 角色 | 契约 |
|----|------|------|
| **A — nav FastDDS** | 导航 / Foxglove / ROS 2 RMW | RMW `rmw_fastrtps_cpp`，`ROS_DOMAIN_ID=42`，[`config/fastdds.xml`](config/fastdds.xml) |
| **B — DimOS Cyclone** | DimOS 原生 DDS / Unitree | Cyclone **域 0**；Unitree `ChannelFactoryInitialize(0)` |

链 B 的 CycloneDDS / `rmw_cyclonedds_cpp` **本轮不 vendor**，按系统 / Unitree 侧依赖记录（安装说明见 [docs/usage/transports/dds.md](docs/usage/transports/dds.md)）。本仓**没有**自定义 RMW。

`config/fastdds.xml` 是 R0 契约种子：`topsun_dimos` `main` **没有** `fastdds.xml` / `docker/navigation/`。不要当成从 DimOS 抽出的现网配置。

## 目录地图

| 路径 | 内容 |
|------|------|
| [`vendor/`](vendor/) | 公开栈**完整源码拷贝**（`rmw`、`rmw_implementation`、`rmw_fastrtps`、`Fast-DDS`）。不是 submodule。 |
| [`vendor/VERSIONS.md`](vendor/VERSIONS.md) | 上游 URL + 完整 SHA / 标签 |
| [`dimos_bridge/`](dimos_bridge/) | 从 `topsun_dimos` **整文件拷贝**的双链相关代码（相对路径不变） |
| [`config/fastdds.xml`](config/fastdds.xml) | 链 A 域 42 契约种子（非 main 提取） |
| [`docs/`](docs/) | R0 冻结与 transports 文档（保留并按新路径作了延伸） |

`dimos_bridge/` 下真实拷贝包括：`docker/ros/`、`ddspubsub.py` / `rospubsub*.py`、`ddsservice.py`、pubsub `spec`/`patterns`/`encoders`、`benchmark/`、`transport.py`、Foxglove 桥、Go2 ROS blueprint、G1 `dds_sdk.py`、`scripts/run_greeter_dds_lite.py`。清单见 [`dimos_bridge/SOURCE.md`](dimos_bridge/SOURCE.md)。

## 分支约定

| 分支 | 用途 |
|------|------|
| `main` | 稳定（当前为 R0 文档 + 本 R1 落地后的 vendor 种子） |
| `feat/...` | 功能分支 |
| **本 PR 分支** | `feat/r1-vendor-dimos-dds-full` |

禁止把外部 GitHub URL 当源码真相；**以本仓拷贝为准**。禁止 submodule / subtree 远端跟踪 / 指向外部仓的符号链接。

## Vendor 上游 SHA（2026-09-10 浅克隆 default branch）

| 树 | SHA | 备注 |
|----|-----|------|
| `vendor/rmw` | `1e58706ed978ff8a9066f17dc11c61d3a644bf76` | `rolling` / tag `7.11.2` |
| `vendor/rmw_implementation` | `ff8818df2328396011543db07e8ddca99b54345a` | `rolling` |
| `vendor/rmw_fastrtps` | `83471d45c448dfc7f4d408bc36cff593df14eb90` | `rolling` |
| `vendor/Fast-DDS` | `343f155c36b561db3d9f047a65d866ce0f3da300` | `master`（近旁稳定 tag `v3.6.2`） |
| DimOS 拷贝源 | `a5259958db23c8ea6648544ed138eab19726ce93` | `topsun_dimos` `main` |

Fast-DDS 原 gitlink（`asio` / `fastcdr` / `tinyxml2` 等）已摊成普通目录，SHA 见 [vendor/VERSIONS.md](vendor/VERSIONS.md)。

## R0 文档（保留）

| 文档 | 路径 |
|------|------|
| 接口冻结（双链、topic/QoS、闸门） | [`docs/architecture/ros2-dds-r0-interface-freeze.md`](docs/architecture/ros2-dds-r0-interface-freeze.md) |
| 链 B Cyclone 安装（系统侧参考） | [`docs/usage/transports/dds.md`](docs/usage/transports/dds.md) |
| Transports 总览 | [`docs/usage/transports/index.md`](docs/usage/transports/index.md) |

R0 源：`topsun_dimos` PR [#122](https://github.com/topsun-bot/topsun_dimos/pull/122)。冻结表本身未改；仅补充本仓已出现的 `vendor/` / `dimos_bridge/` / `config/fastdds.xml` 路径。

## R1 TODO（本 PR 不实现）

- 抽出 env：`RMW_IMPLEMENTATION=rmw_fastrtps_cpp`、`ROS_DOMAIN_ID=42`、`FASTRTPS_DEFAULT_PROFILES_FILE` 指向 `config/fastdds.xml`
- 按需拆 Dockerfile / nav 镜像（`topsun_dimos` main **没有** `docker/navigation/`）
- 对照编译 vendor Fast-DDS / `rmw_fastrtps_cpp`（**不要**自定义 RMW）
- topic 常量、中间件行为补丁、评测 / 时延 / 安全：仍 Hold

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) 检查 R0 文档路径、vendor 目录存在、以及文档相对链接。  
**本 PR 不在 CI 里完整编译 Fast-DDS。**

## 许可

根目录 [MIT](LICENSE)。`vendor/` 与 `dimos_bridge/` 保留各自上游许可（多为 Apache-2.0）。
