# 《3》《4》 原生 DDS 实测与时延报告 — 2026-09-23

承接 `docs/testing/2026-09-mac-hil.md`（当时本机无 ROS runtime，建议在 Linux 上补两条真实 DDS 用例）。
本轮在 Colima VM 内用**原生 arm64** ROS 2 跑通真实 pub/sub 并测时延。

## 1. 环境与边界（先读，避免误读数字）

- 宿主：macOS（Apple Silicon，arm64）；Colima VM = **Ubuntu 24.04 (noble), aarch64 原生**（非 qemu）。
- ROS：**Jazzy**（`/opt/ros/jazzy`，204+ 包）。noble 对应 Jazzy；**Humble 官方只支持 22.04 jammy**，本机无法经 Docker Hub 取得 arm64 jammy 镜像（见 §5）。
- 因此本报告是**原生功能与时延代理**，**不是 Humble 认证**：Jazzy 用 FastDDS **2.14.6** / rmw 8.4.4，Humble 为 FastDDS 2.6.x，Cyclone 版本也不同。
- 路径为 **VM 内 loopback、单机**；跨物理机 / 真实网卡 p99 仍 **blocked**。未把冻结的 `config/fastdds.xml`（Humble schema）载入 Jazzy（版本不匹配，且属 Hold）。

## 2. 方法与复现

- 探针：`hil/lat_talker.py`（100Hz 发 `seq,monotonic_ns`，小 String）、`hil/lat_listener.py`（收满即算分位数）。两进程同核，CLOCK_MONOTONIC 一致，单向时延 = recv−send。QoS 默认（RELIABLE，depth 10）。
- 运行（在 VM 内）：
  ```bash
  colima start
  colima ssh -- bash /Users/zhang/colima-work/ros2_hzj/hil/run_latency.sh 1000 300 100
  ```
- 连通 sanity：原生 Jazzy `demo_nodes_cpp` talker/listener → listener 听到 11/12 条（PASS）。

## 3. 结果：三种配置全部真实 pub/sub，零丢失

| 配置（domain） | collected | loss | min | mean | p50 | p90 | p95 | p99 | max | jitter(p99−p50) | stdev |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| FastDDS 默认 (42) | 1000 | 0 | 187 | 476 | 420 | 696 | 817 | 1163 | 1897 | 743 | 175 |
| FastDDS UDP-only (42) | 1000 | 0 | 280 | 490 | 439 | 698 | 821 | 1055 | 1462 | 616 | 148 |
| Cyclone 默认 (0) | 1000 | 0 | 250 | 440 | 388 | 607 | 750 | 1166 | 2585 | 777 | 185 |

单位 µs；1000 个有效样本（另 300 warmup 丢弃）。

**读数（事实层）**
- 原生 DDS 数据面在两条链上均可靠交付（loss=0）。
- loopback 单向中位约 **0.39–0.44ms**，p99 约 **1.05–1.17ms**；尾延主要来自 VM 调度与 rclpy 回调，而非串行化（小消息）。
- FastDDS 强制 UDP-only 后 p99/max 略降、抖动收窄（SHM 在本 VM 无净收益）；Cyclone 中位略低但 max 更大。**仅为本 VM/Jazzy 观察，不外推到 Humble/真机。**

## 4. Bug 与分诊

### BUG-H1（High，针对「本机跑 Humble 镜像」路径）：qemu 模拟下 DDS 零交付
- **复现**：
  ```bash
  colima start
  docker run --rm --network rosnet -e ROS_DOMAIN_ID=42 osrf/ros:humble-desktop \
    bash -c 'ros2 run demo_nodes_cpp listener >/tmp/l.log 2>&1 & sleep10; \
      timeout15 ros2 run demo_nodes_cpp talker >/tmp/t.log 2>&1; sleep2; \
      echo heard=$(grep -c "I heard" /tmp/l.log)'
  ```
- **预期**：listener 逐条 `I heard`，heard>0。
- **实际**：heard=0；talker 正常 `Publishing`；单容器 loopback 同样为 0；强制 UDP-only（`hil/udp_only.xml`）仍为 0；**无任何报错**。
- **根因（环境，非 ROS 源码缺陷）**：本机仅有 `osrf/ros:humble-desktop` 的 **linux/amd64** 镜像，在 arm64 上经 **qemu-user** 模拟运行；模拟对 DDS 依赖的线程/锁/loopback 发现存在不兼容，数据面静默不通。
- **严重程度**：High（封死 Apple Silicon 上该 Humble 镜像路径）。
- **规避**：用原生 arm64 runtime（本报告 Jazzy）。原生 arm64 Humble 需 jammy arm64 镜像，当前网络取不到 → **blocked**。

### BUG-H2（Low，诊断工具）：qemu 下 ros2 CLI 列表为空
- **复现**：qemu 容器内 `ros2 node list` / `ros2 topic list`。
- **预期**：列出节点/话题（至少自身 `/parameter_events`）。
- **实际**：持续返回空（daemon 在内部超时内来不及应答），易误判为发现失败。原生环境正常。
- **严重程度**：Low（仅影响排障可读性）。

### 分诊总结
| # | 路径 | 结果 | 严重程度 |
|---|---|---|---|
| H1 | amd64 Humble 镜像 @ qemu | FAIL（零交付） | High（环境） |
| H2 | qemu 下 ros2 CLI 列表 | 空/误导 | Low |
| — | 原生 FastDDS（默认/UDP） | PASS，loss0 | — |
| — | 原生 Cyclone | PASS，loss0 | — |

非阻塞项继续推进，无阻塞性 bug 遗留于原生路径。

## 5. 非阻塞观察
1. VM 内残留指向主机代理的 `*_proxy=http://192.168.5.2:7897`（未运行），导致 apt 超时；已用 `Acquire::*::Proxy=false` 直连。
2. 打包脚坑：`--no-install-recommends` 且同批安装 `rmw-cyclonedds` 会满足 rmw 虚拟依赖，使 `rmw-fastrtps-cpp` 被跳过；需显式安装（本轮已补）。
3. 网络：`registry-1.docker.io` SSL 超时、`packages.ros.org` 证书名不匹配；TUNA/USTC 与 `ports.ubuntu.com` 直连可用。Docker bridge 的跨容器多播经 `hil/mc_rx.py`/`mc_tx.py` 实测可达。

## 6. 仍 blocked / 后续
- **原生 arm64 Humble（jammy）**：需可达的 Docker Hub 或 jammy arm64 镜像；取得后应重跑本套，方可对 Humble 下结论。
- **跨物理机 / 真实 NIC p99**：需第二台主机与被测链路（当前单机无法）。
- 本报告数字仅代表 Jazzy@Colima VM loopback；禁止写入冻结的 `SCOREBOARD.md`。
