# 双链 pubsub benchmark 怎么跑（R5）

本文说明**命令、前置条件、以及本仓已落盘的基线产物路径**。vendor 落盘或某条 RMW **不能**当成根因。

冻结表把评测标成 hypothesis，直到记下 p50 / p95 / p99。链 A 与链 B **不是**同一次 ping-pong，数字不能直接对比；也不要把 `same-process` / `same-host` / `cross-host-UDP` 混在一张表里。

可复现入口（仓库根）：[`scripts/bench/`](../../scripts/bench/README.md)。

- 链 B：`./scripts/bench/run_chain_b.sh` → 文档里的 `pytest -m tool -k dds`，再加一层 **不改** `ddspubsub` 的 ping-pong 包分位
- 链 A：先 `source config/env/chain_a.sh`，再 `./scripts/bench/run_chain_a.sh`；本机没有 Humble 时看 `STATUS: blocked` 和 [`scripts/bench/docker_chain_a.sh`](../../scripts/bench/docker_chain_a.sh)

已记录的产物目录：[`docs/artifacts/bench/`](../../docs/artifacts/bench/README.md)（按 UTC 日期分子目录；链 A / 链 B 分文件）。

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

## 产物与怎么重跑

每个成功（或明确 blocked）的 run 应有：

| 文件 | 内容 |
|------|------|
| `summary.md` | p50 / p95 / p99（微秒，RTT）或 blocked 原因；case 名；消息大小 |
| `raw.json` | ping-pong 样本；以及 pytest junit/stdout（若跑过） |
| `environment.md` | OS、CPU、hostname class、`ROS_DISTRO`、RMW、`ROS_DOMAIN_ID`、cyclonedds 版本、包版本、`ros2_hzj` git SHA、DimOS 来自 vendored `dimos_bridge` 还是临时 `topsun_dimos` checkout |
| **Topology** | 每个 run **只标一个**：`same-process` / `same-host` / `cross-host-UDP` |

上游 `test_benchmark.py` 的 Latency 列是「发完再等收齐」的 drain time，**不是** per-message p50。分位数只来自 [`scripts/bench/pingpong.py`](../../scripts/bench/pingpong.py)。

`dimos_bridge` 里 LCM / `logging_config` / `Image` 等仍是 ImportError stub 时，runner 可以 **只读 clone** `topsun-bot/topsun_dimos`（不 submodule、不往那边 push）去跑 `dimos/protocol/pubsub/benchmark/`，再把**结果**拷回本仓 `docs/artifacts/bench/`。

重跑：

```bash
# 链 B（Cyclone / 域 0；不要 source chain_a.sh）
./scripts/bench/run_chain_b.sh
# 可选同机两进程（localhost UDP / SHM，仍标 same-host，单独目录）：
TOPOLOGY=same-host ./scripts/bench/run_chain_b.sh
ICEORYX=off TOPOLOGY=same-host ./scripts/bench/run_chain_b.sh

# 链 A（需要 Humble + rmw_fastrtps_cpp）
source /opt/ros/humble/setup.bash
source config/env/chain_a.sh
./scripts/bench/run_chain_a.sh
# 或操作员稍后：
./scripts/bench/docker_chain_a.sh
```

DimOS 默认 `addopts` 会排除 `tool`，checkout 上跑官方命令时 runner 会加 `-o addopts=` 再写 `-m tool`。

## 明确不写的东西

- 不把这些数字写成「谁更快」或根因
- vendor SHA 不能当性能证据
- 不要拿链 B 的 `-k dds` 去解释 Foxglove / `/cmd_vel` / `ROSTransport` 的时延
- 不要把链 A 和链 B 放进同一张对照表假装可比
