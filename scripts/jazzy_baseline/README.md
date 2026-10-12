# Jazzy ROS 2 性能基线（10× 分母）

测 **ROS 2 Jazzy** 发行版自带的 `rmw_fastrtps_cpp` 与 `rmw_cyclonedds_cpp`。
结果是后面「用 Rust 重写中间件、性能 10 倍」的分母。

这套工具**不是** Humble 双链 bench，也**不是** [`docs/artifacts/bench/SCOREBOARD.md`](../../docs/artifacts/bench/SCOREBOARD.md)。

- 不 `source config/env/chain_a.sh` / `chain_b.sh`
- 不加载 [`config/fastdds.xml`](../../config/fastdds.xml)（那是链 A Humble 契约种子）
- 不把数字写进 SCOREBOARD
- Fast DDS 与 Cyclone 在 Markdown 里**分表**，不当 bake-off

Humble 双链入口仍是 [`scripts/bench/README.md`](../bench/README.md)。

## 为什么不直接包 `ros2/performance_test`

[cn-jp-ros2-absorb.md §6.11](../../docs/architecture/cn-jp-ros2-absorb.md) 允许在 `scripts/` 里包一层 `performance_test` / iRobot `ros2-performance`。这次没有 vendoring 那套，理由：

1. 本仓禁止 submodule / gitlink；把 `performance_test` 整树拷进来会膨胀 vendor，且 CI Hold「不在流水线里编译 ROS / vendor」。
2. 现成 C++ 工具默认不报**发布端 / 订阅端进程**的 CPU% 与 RSS；还要再包一层 `/proc`。
3. 已有 [`scripts/bench/pingpong.py`](../bench/pingpong.py) 是 Humble 双链 RTT（p50/p95/p99），缺吞吐 MB/s、p90、4 MiB、分进程资源，不能当 Jazzy 10× 分母。
4. 本 harness 用 `RMW_IMPLEMENTATION` 切换实现，和将来的 Rust RMW **同一套 CLI / 同一套 CSV 列**。有现成 `performance_test` 二进制时，可以再加 `--worker`，不必重写报告。

## 测什么

| 维 | 默认 | 可配 |
|----|------|------|
| RMW | `rmw_fastrtps_cpp`, `rmw_cyclonedds_cpp` | `--rmw` |
| 拓扑 | **同机两进程** `same-host`（必测） | `cross-host` 可选；单机写 `STATUS: blocked` |
| 消息 | 1 KiB / 64 KiB / 1 MiB / 4 MiB | `--sizes` |
| QoS | `reliable` / `best_effort` | `--qos` |
| 模式 | 单向时延（同机 `CLOCK_MONOTONIC` 打戳） | `--mode rtt` 往返 |
| 频率 | 按尺寸：100 / 50 / 10 / 2 Hz | `--hz` |
| 时长 | 10 s + 预热 2 s | `--duration` `--warmup` |
| 重复 | 3 | `--repeats` |
| 资源 | 每个进程 CPU% + VmRSS 均值/峰值 | `/proc/<pid>` |

默认域 **87**，避免撞上链 A 域 42 / 链 B 域 0。同机默认 `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`（Jazzy 替代已弃用的 `ROS_LOCALHOST_ONLY`）。

## 构建

本工具是 **Python 3 + Jazzy `rclpy` / `std_msgs`**，没有 colcon overlay。

### 本机（Ubuntu 24.04 / Noble）

按 [Jazzy 安装说明](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) 装 `ros-jazzy-ros-base`，并保证：

```bash
sudo apt-get install -y \
  ros-jazzy-rclpy ros-jazzy-std-msgs \
  ros-jazzy-rmw-fastrtps-cpp ros-jazzy-rmw-cyclonedds-cpp
source /opt/ros/jazzy/setup.bash
```

### Docker

```bash
# 从仓库根。会 pull osrf/ros:jazzy-ros-base 并 apt 两个 RMW。
./scripts/jazzy_baseline/docker_run.sh
# 覆盖镜像：
JAZZY_BASELINE_IMAGE=osrf/ros:jazzy-desktop ./scripts/jazzy_baseline/docker_run.sh
```

不需要、也不应该 `source config/env/chain_a.sh`。

无 ROS 自检（CI / 本机都该绿）：

```bash
python3 scripts/jazzy_baseline/selftest.py
```

## 运行

仓库根：

```bash
source /opt/ros/jazzy/setup.bash   # Docker 脚本已 source

# 云端 / CI 冒烟：1KiB+64KiB，2s，reliable，两个 RMW，同机
python3 scripts/jazzy_baseline/run.py --smoke

# 完整默认矩阵（1k/64k/1M/4M × 两 QoS × 两 RMW × 3 次，约数十分钟）
python3 scripts/jazzy_baseline/run.py \
  --out docs/artifacts/jazzy_baseline/$(date -u +%Y-%m-%dT%H%MZ)

# 只跑 Fast-DDS、只 reliable、固定 10 Hz
python3 scripts/jazzy_baseline/run.py \
  --rmw rmw_fastrtps_cpp --qos reliable --hz 10 --repeats 3
```

跨机（可选；两台都要 Jazzy，同一 `--topic-prefix` / `--domain`）：

```bash
# 主机 B — 先开订阅
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_DOMAIN_ID=87
python3 scripts/jazzy_baseline/worker.py \
  --role sub --mode oneway --qos reliable --size 1024 --hz 50 \
  --duration 10 --warmup 2 --topic-prefix /jazzy_baseline/cross \
  --result-json /tmp/sub.json

# 主机 A — 发布
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_DOMAIN_ID=87
python3 scripts/jazzy_baseline/worker.py \
  --role pub --mode oneway --qos reliable --size 1024 --hz 50 \
  --duration 10 --warmup 2 --topic-prefix /jazzy_baseline/cross \
  --result-json /tmp/pub.json
```

单机跑 `--topology cross-host` 会诚实写 `STATUS: blocked`，不编分位。

## 产物

`--out` 目录：

| 文件 | 内容 |
|------|------|
| `results.csv` | 机器可读；列见 `defaults.CSV_COLUMNS` |
| `results.json` | 同上 + 环境 |
| `summary.md` | 按 RMW 分表：p50/p90/p99/max、msg/s、MB/s、CPU、RSS |
| `environment.md` / `.json` | CPU、内核、ROS 发行版、rmw dpkg 版本、git SHA |
| `cases/...` | 每个 case 的 pub/sub worker JSON |

每行都带 `not_final_baseline=true` 和 `host_class`（云端 VM 为 `cursor-cloud-vm`）。**云端冒烟数字不能当最终基线。**

## 方法注意

1. **预热**：`--warmup` 秒内的样本不进分位、不进吞吐。默认 2 s，冒烟 0.5 s。
2. **重复**：正式基线 `--repeats 3`（或更多），取各次 CSV 再自己算中位；不要只报一次 p50。
3. **CPU 隔离**：共享云 vCPU 噪声很大。目标机建议 `isolcpus` / `cset` / `taskset`，关 turbo，固定频率，停无关进程。本 harness 不自动绑核。
4. **时钟**：同机单向时延用 `CLOCK_MONOTONIC`（进程间可比）。跨机不要信单向戳，改 `--mode rtt`，或先 PTP。
5. **大包**：4 MiB 会走 DDS 分片。默认 2 Hz。Docker 请 `--shm-size=1g` 或更大。
6. **发现**：同机 `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`。跨机需要组播或自己的 peer 列表；本工具不改 XML。
7. **缺件**：没有对应 `librmw_*.so` 的 case 写 `STATUS: blocked` + 原因，不填假数。
8. **不要**把同机数字说成现场 / 实机 / 跨机根因。

## Rust 实现怎么接同一套测试

三种由浅到深的接法（推荐 1，需要自己进程模型时用 2）：

### 1. 只换 RMW（首选）

Rust RMW 只要能被 `RMW_IMPLEMENTATION` 加载（`rmw_*` 动态库在 `AMENT_PREFIX_PATH`）：

```bash
export RMW_IMPLEMENTATION=rmw_your_rust_cpp   # 名字以仓库实际为准
source /opt/ros/jazzy/setup.bash
python3 scripts/jazzy_baseline/run.py --rmw rmw_your_rust_cpp \
  --out docs/artifacts/jazzy_baseline/rust-$(date -u +%Y-%m-%d)
```

CSV 列不变，直接和 Jazzy Fast-DDS / Cyclone 行比吞吐与分位。

### 2. 换 worker 二进制（`--worker`）

实现与 [`worker.py`](worker.py) 相同的 CLI 和结果 JSON：

```text
--role pub|sub|echo|client
--mode oneway|rtt
--qos reliable|best_effort
--size N --hz F --duration S --warmup S
--topic-prefix PREFIX
--result-json PATH
--sync-dir DIR          # 写 <role>.ready；读 go JSON {"go_at_mono": float}
```

线格式（小端，总长 = `--size`）：

```text
magic u32 = 0x4A5A4253
seq   u32
t0_ns u64   同机 CLOCK_MONOTONIC
payload     零填充
```

topic：`{prefix}/data`（单向或 ping），`{prefix}/echo`（pong）。
消息类型：`std_msgs/UInt8MultiArray`（连续 `uint8`）。

结果 JSON 至少包含：`status`, `sent` 或 `received`, `p50_us`/`p90_us`/`p99_us`/`max_us`,
`throughput_msg_s`, `throughput_mbyte_s`, `cpu_percent`, `rss_kb_avg`, `rss_kb_peak`, `pid`。

```bash
python3 scripts/jazzy_baseline/run.py \
  --worker ./target/release/jazzy_baseline_worker \
  --rmw rmw_fastrtps_cpp
```

### 3. 只复用报告

自己跑完后按 `defaults.CSV_COLUMNS` 填 `cases`，调用同一套 `report.write_reports`。
不要另起一列名，否则 10× 对不上。

## Hold

- 不改 `config/fastdds.xml`、`docs/artifacts/bench/SCOREBOARD.md`
- 不启用 Agnocast / zenoh / `rmw_zenoh`
- 不改 `dimos_bridge` DDS 行为
- 《3》–《6》（分数闭环、Mac HIL、Promptfoo、CVE）仍 Hold
