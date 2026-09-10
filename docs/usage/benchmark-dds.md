# 双链 pubsub benchmark 怎么跑（R5）

本文只说明**命令与前置条件**。这里**没有**时延分数，也不把 vendor 落盘或某条 RMW 写成根因。

冻结表把评测标成 hypothesis，直到记下 p50 / p95 / p99。链 A 与链 B **不是**同一次 ping-pong，数字不能直接对比。

源码在本仓：[`dimos_bridge/dimos/protocol/pubsub/benchmark/`](../../dimos_bridge/dimos/protocol/pubsub/benchmark/)。  
这是从 `topsun_dimos` 整目录拷来的；默认传输仍是 LCM（**不在**本仓 DDS 范围）。完整 DimOS 依赖（`uv` extra、消息类型、非 stub 模块）仍在上游仓。本仓缺那些依赖时，下列命令会在 import 处失败——那是环境问题，不是「已经测过」。

## 测什么

| 过滤 | 实现 | 链 | 域 |
|------|------|----|----|
| `-k dds` | `dds_high_throughput_pubsub_channel` / `dds_reliable_pubsub_channel`（Cyclone Python，`ddspubsub.DDS`） | **B** | `DDSConfig.domain_id` 默认 **0** |
| `-k ros` 或 `RawROS` / `DimosROS` | `rospubsub.py` → 当前 `RMW_IMPLEMENTATION` | 取决于你 export 的链 | 链 A 应为 **42**；未设则为 ROS 默认 **0** |

`testdata.py` 里 LCM / SHM / Redis 用例**不是**本仓 DDS 工作。Pytest 默认 `addopts` 会排除 `tool` marker，所以必须加 `-m tool`。

## 链 B（原生 Cyclone）

需要：已安装的 Cyclone C 库 + Python `cyclonedds`（系统 / Nix，见 [transports/dds.md](transports/dds.md)）。本仓 `vendor/CycloneDDS` 是源码拷贝，**CI 不编译它**；你要自己编或用发行版。

在**完整 DimOS 树**（推荐，依赖齐全）或本仓把 `dimos_bridge` 放进 `PYTHONPATH` 且 extra 已装时：

```bash
# 不要 source chain_a.sh。原生 DDS 不读 RMW；域在代码里默认 0。
# 可选：source config/env/chain_b.sh  （只影响同机 ROS 2 客户端）

cd <topsun_dimos> && uv sync --extra dds
uv run pytest dimos/protocol/pubsub/benchmark/test_benchmark.py -m tool -k dds -v
```

本仓等价路径（依赖自行补齐）：

```bash
export PYTHONPATH="${PWD}/dimos_bridge${PYTHONPATH:+:$PYTHONPATH}"
pytest dimos_bridge/dimos/protocol/pubsub/benchmark/test_benchmark.py -m tool -k dds -v
```

`-k dds` 选中的是 Cyclone 用例，不是 Fast-DDS。

## 链 A（ROS 2 / Fast-DDS）

需要：可用的 ROS 2（Humble 镜像见 [`docker/ros/`](../../docker/ros/NOTES.md)）以及 `rclpy`。这测的是 **RMW 当前实现**，不是 `DDS()`。

```bash
source /opt/ros/humble/setup.bash
source config/env/chain_a.sh   # RMW=rmw_fastrtps_cpp，域 42，指向 config/fastdds.xml

export PYTHONPATH="${PWD}/dimos_bridge${PYTHONPATH:+:$PYTHONPATH}"
pytest dimos_bridge/dimos/protocol/pubsub/benchmark/test_benchmark.py -m tool -k 'ros or RawROS or DimosROS' -v
```

库默认 QoS（`RELIABLE` / `KEEP_LAST` / `VOLATILE` / `depth=5000`）**不是**冻结表导航 QoS。本 bench 不能代替「同域 42 的应用层 ping-pong」。

若误用 `chain_b.sh`（`rmw_cyclonedds_cpp` + 域 0）再跑 ROS bench，那是链 B 的 ROS 侧，不是链 A。

## 明确不写的东西

- 无 p50 / p95 / p99，无「谁更快」
- vendor SHA 不能当性能证据
- 不要拿链 B 的 `-k dds` 去解释 Foxglove / `/cmd_vel` / `ROSTransport` 的时延
