# 2026-09-10 UTC baseline (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`（KVM，`hostname=cursor`）。OS: Ubuntu 24.04.4 LTS。

**不要**把下面几个目录的数字合成一张「谁更快」表。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_b_same_process/`](chain_b_same_process/summary.md) | B | `same-process` | ok — ping-pong p50/p95/p99；checkout pytest 24 passed |
| [`chain_b_same_host/`](chain_b_same_host/summary.md) | B | `same-host` | ok — 两进程；无 RouDi ⇒ localhost UDP，非 SHM |
| [`chain_b_cross_host_UDP/`](chain_b_cross_host_UDP/summary.md) | B | `cross-host-UDP` | blocked — 单机 VM，无第二台机器 |
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | blocked — 无 Humble / rclpy / docker；见 `docker_chain_a.sh` |

DimOS 运行时来自临时 checkout `topsun_dimos` @ `a5259958db23c8ea6648544ed138eab19726ce93`（与 `dimos_bridge/SOURCE.md` 相同）。vendored `dimos_bridge` stub 无法 collection 官方 pytest。

重跑：[`scripts/bench/README.md`](../../../../scripts/bench/README.md)。
