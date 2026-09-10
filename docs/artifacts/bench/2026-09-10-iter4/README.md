# 2026-09-10-iter4 (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` (same image class as iter3).

**One change:** default-participant RTPS send-buffer `preallocated_number` 32 → 0 (`dynamic` stays true) in `config/fastdds.xml`. See [`change.md`](change.md). Like-to-like deltas vs [`../2026-09-10-iter3/`](../2026-09-10-iter3/README.md): [`delta.md`](delta.md) (written after remasure).

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/) | A | `same-process` | pending remasure — honesty check only; **do not tune** |
| [`chain_a_same_host/`](chain_a_same_host/) | A | `same-host` | pending remasure — mid-size 100/256 KiB primary; 1 MiB must stay near iter3 |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/) | A | `cross-host-UDP` | blocked — 单机 VM |

链 B **未重跑**（本 iter 旋钮只在 Chain A XML）。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-10-iter4 CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh
```
