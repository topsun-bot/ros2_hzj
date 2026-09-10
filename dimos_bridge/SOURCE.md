# dimos_bridge/ 来源说明

前缀：`dimos_bridge/`。其下**保持** `topsun_dimos` 相对路径（`dimos/...`、`docker/ros/`、`scripts/`）。

| 项 | 值 |
|----|----|
| 只读上游 | https://github.com/topsun-bot/topsun_dimos |
| 分支 | `main` |
| SHA | `a5259958db23c8ea6648544ed138eab19726ce93` |
| 行为 | **整文件拷贝，本 PR 不做功能重构** |
| 未改上游仓 | `topsun_dimos` 只读，未 push / 未开 PR |

## 整文件 / 整目录拷贝（真实 DimOS 源码）

- `docker/ros/`（`Dockerfile`、`install-nix.sh`）
- `dimos/protocol/pubsub/impl/ddspubsub.py`
- `dimos/protocol/pubsub/impl/rospubsub.py`
- `dimos/protocol/pubsub/impl/rospubsub_conversion.py`
- `dimos/protocol/pubsub/impl/test_rospubsub.py`
- `dimos/protocol/service/ddsservice.py`
- `dimos/protocol/service/spec.py`（`DDSService` 的直接依赖）
- `dimos/protocol/pubsub/benchmark/`（整目录）
- `dimos/protocol/pubsub/spec.py`
- `dimos/protocol/pubsub/patterns.py`
- `dimos/protocol/pubsub/encoders.py`
- `dimos/core/transport.py`
- `dimos/robot/foxglove_bridge.py`
- `dimos/utils/cli/foxglove_bridge/`
- `dimos/utils/test_foxglove_bridge.py`
- `dimos/robot/unitree/go2/blueprints/smart/unitree_go2_ros.py`
- `dimos/robot/unitree/g1/effectors/high_level/dds_sdk.py`
- `scripts/run_greeter_dds_lite.py`

## 未在 main 找到（因此未拷）

在 `topsun_dimos` @ 上述 SHA 上搜索 `fastdds.xml`、`ROS_DOMAIN_ID`、`rmw_fastrtps`、`FASTRTPS_DEFAULT_PROFILES_FILE`、`docker/navigation/`：

- **没有** `docker/navigation/`（Dockerfile / compose / foxglove relays）
- **没有** `fastdds.xml`
- **没有** 编码 `ROS_DOMAIN_ID=42` 或 `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` 的已提交文件

链 A 契约种子放在本仓 [`config/fastdds.xml`](../config/fastdds.xml)，**标明不是从 main 提取**。

`docker-build.yml` 仍提到 `docker/navigation/**`，但该目录在 main 上不存在。未伪造 navigation 镜像或 relay 模块。

## 可导航占位（`__init__.py` / stub）

为让包路径可浏览，补了 `__init__.py` 以及若干 **ImportError stub**（LCM/SHM、消息类型、module coordinator 等）。stub **不是** DimOS 实现，也不要当运行时。完整模块仍在 `topsun_dimos`。

未 vendor 整个 DimOS monorepo。默认 LCM 传输不在本仓 DDS 范围内。
