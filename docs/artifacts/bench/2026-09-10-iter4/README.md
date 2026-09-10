# 2026-09-10-iter4 (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` (same image digest as iter3).

**One change:** default-participant RTPS send-buffer pool stays 32; `dynamic` true → false in `config/fastdds.xml`. See [`change.md`](change.md). Like-to-like deltas vs [`../2026-09-10-iter3/`](../2026-09-10-iter3/README.md): [`delta.md`](delta.md). Mid-size honesty vs [`../2026-09-10-iter2-after/`](../2026-09-10-iter2-after/README.md) is in that same delta.

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — honesty check only; mid-size and 1 MiB faster vs iter3; **do not tune** |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — Reliable 100/256 KiB p50 **−8–9%** vs iter3; 1 MiB BestEffort within ~2% of iter3; BestEffort 256 KiB **not** recovered vs iter2-after |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |

链 B **未重跑**（本 iter 旋钮只在 Chain A XML）。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-10-iter4 CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh
```
