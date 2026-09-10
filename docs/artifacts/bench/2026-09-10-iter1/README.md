# 2026-09-10-iter1 (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`（KVM，`hostname=cursor`）。OS: Ubuntu 24.04.4 LTS host; Chain A benches inside Humble `docker/ros` (Ubuntu 22.04.5).

**One change:** Humble-valid History QoS in `config/fastdds.xml`. See [`change.md`](change.md). Like-to-like deltas vs [`../2026-09-10/`](../2026-09-10/README.md): [`delta.md`](delta.md).

**不要**把下面几个目录的数字合成一张「谁更快」表。不要和链 B 混表。不要用 64 B same-process 去讲飞书大包 / 实机根因。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — ping-pong p50/p95/p99；Humble XMLPARSER 不再报 `<history>` |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — 两进程；Fast-DDS **默认** transport，**不要**标 SHM |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM，无第二台机器 |

链 B **未重跑**（本 iter 只改 Chain A XML）。《3》《4》《5》《6》仍 Hold。

重跑：[`scripts/bench/README.md`](../../../../scripts/bench/README.md)

```bash
BENCH_DATE=2026-09-10-iter1 CHAIN_A_TOPOLOGIES='same-process same-host' \
  ./scripts/bench/docker_chain_a.sh
```
