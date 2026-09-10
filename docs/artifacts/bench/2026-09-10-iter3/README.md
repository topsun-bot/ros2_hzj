# 2026-09-10-iter3 (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` (same image digest as iter2-after).

**One change:** default-participant RTPS send-buffer pool 32 / dynamic in `config/fastdds.xml`. See [`change.md`](change.md). Like-to-like deltas vs [`../2026-09-10-iter2-after/`](../2026-09-10-iter2-after/README.md): [`delta.md`](delta.md).

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — honesty check only; 1 MiB faster, 100/256 KiB slower; **do not tune** |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — 1 MiB BestEffort p50 **−25%**; 1 MiB Reliable p50 **−3.8%** |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |

链 B **未重跑**（本 iter 旋钮只在 Chain A XML）。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-10-iter3 CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh
```
