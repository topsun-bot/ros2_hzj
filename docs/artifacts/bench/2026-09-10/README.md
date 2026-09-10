# 2026-09-10 UTC baseline (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`（KVM，`hostname=cursor`）。OS: Ubuntu 24.04.4 LTS。

**不要**把下面几个目录的数字合成一张「谁更快」表。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_b_same_process/`](chain_b_same_process/summary.md) | B | `same-process` | ok — ping-pong p50/p95/p99；checkout pytest 24 passed |
| [`chain_b_same_host/`](chain_b_same_host/summary.md) | B | `same-host` | ok — 两进程；无 RouDi ⇒ localhost UDP，非 SHM |
| [`chain_b_cross_host_UDP/`](chain_b_cross_host_UDP/summary.md) | B | `cross-host-UDP` | blocked — 单机 VM，无第二台机器 |
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — Humble `docker/ros` 内 ping-pong p50/p95/p99；官方 ROS pytest 因 Image stub 未 collection |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — 两进程；Fast-DDS **默认** transport，**不要**标 SHM |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM，无第二台机器 |

链 A 在 `ros2_hzj/ros:humble`（`docker/ros/Dockerfile`，runtime source `config/env/chain_a.sh`：RMW=`rmw_fastrtps_cpp`，域 42）里测。链 B 运行时来自临时 checkout `topsun_dimos` @ `a5259958db23c8ea6648544ed138eab19726ce93`（与 `dimos_bridge/SOURCE.md` 相同）。

**不要**把链 A 和链 B 的数字合成一张「谁更快」表。

重跑：[`scripts/bench/README.md`](../../../../scripts/bench/README.md)（链 A：`./scripts/bench/docker_chain_a.sh`）。
