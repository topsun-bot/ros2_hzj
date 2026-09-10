# 2026-09-10-iter5 (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` (same image digest as iter4).

**One change:** additive user SHM `maxMessageSize=280000`, `segment_size=2 MiB`; builtin UDP+SHM kept. See [`change.md`](change.md). Like-to-like deltas vs [`../2026-09-10-iter4/`](../2026-09-10-iter4/README.md): [`delta.md`](delta.md). Mid-size honesty vs [`../2026-09-10-iter2-after/`](../2026-09-10-iter2-after/README.md) is in that same delta.

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — honesty check only; mid-size and 1 MiB faster vs iter4; **do not tune** |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — BestEffort 256 KiB p50 **−18.6%** vs iter4 (past iter2-after); 1 MiB BestEffort/Reliable **−19–23%**; 80/80 |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |

链 B **未重跑**（本 iter 旋钮只在 Chain A XML）。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-10-iter5 CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh
```
