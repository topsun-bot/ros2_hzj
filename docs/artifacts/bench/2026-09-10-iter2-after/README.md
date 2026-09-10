# 2026-09-10-iter2-after (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` (same image digest as Step A).

**One change:** default-participant UDP socket buffers 2 MiB in `config/fastdds.xml`. See [`change.md`](change.md). Like-to-like deltas vs [`../2026-09-10-iter2-large-baseline/`](../2026-09-10-iter2-large-baseline/README.md): [`delta.md`](delta.md).

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — p50 +4–8% vs baseline (noise) |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — 1 MiB BestEffort **80/80** (baseline 0/90); 1 MiB Reliable p50 **−93%** |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |

链 B **未重跑**（本 iter 旋钮只在 Chain A XML）。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-10-iter2-after CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh
```
