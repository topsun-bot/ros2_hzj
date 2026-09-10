# 2026-09-10-iter2-large-baseline (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`（KVM，`hostname=cursor`）。OS: Ubuntu 24.04.4 LTS host; Chain A benches inside `osrf/ros:humble-desktop` (Ubuntu 22.04.5 / Humble).

**Step A only.** Large-packet same-topology ping-pong. **No transport / config knob** in this directory. See [`NOTES.md`](NOTES.md).

**不要**把下面几个目录的数字合成一张「谁更快」表。不要和链 B 混表。
**不是** 飞书现场 / 实机 / 跨机根因证明。cross-host 仍 blocked。

## Exact sizes and rate

| Item | Value |
|------|--------|
| Payload lengths (bytes) | **102400** (100 KiB), **262144** (256 KiB), **1048576** (1 MiB) |
| Inter-message gap | **100 ms** (target **10 Hz**, lidar-ish) |
| Samples / warmup / timeout | 80 / 10 / 8 s |
| Pacing | minimum 100 ms between publishes; if RTT > 100 ms, effective rate is **1/RTT** (closed-loop) |
| Chain A message | `std_msgs/UInt8MultiArray` (contiguous uint8). Humble `ByteMultiArray` is not used at these sizes. |
| Chain B payload | `BenchProbe.payload` `sequence[uint8]` of the same lengths |

1 MiB was **stable** (no OOM, 80/80 samples) on both chains for `same-process` and for `same-host` **reliable**.  
1 MiB **best-effort** `same-host` timed out 90/90 on **both** chains (not OOM — likely localhost UDP fragment loss). Size kept; zeros documented. This is **not** a field root-cause claim.

## Topologies (separate tables)

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — all three sizes, both QoS |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — 100/256 KiB both QoS; 1 MiB reliable ok; 1 MiB best-effort **0/90** |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |
| [`chain_b_same_process/`](chain_b_same_process/summary.md) | B | `same-process` | ok — all three sizes, both QoS |
| [`chain_b_same_host/`](chain_b_same_host/summary.md) | B | `same-host` | ok — localhost UDP, **not** SHM (no RouDi); 1 MiB best-effort **0/90** |
| [`chain_b_cross_host_UDP/`](chain_b_cross_host_UDP/summary.md) | B | `cross-host-UDP` | blocked — 单机 VM |

Shared env facts: [`environment.md`](environment.md).

## Command

```bash
BENCH_DATE=2026-09-10-iter2-large-baseline \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS='A B' \
  ./scripts/bench/run_large_packet.sh
```

《3》《4》《5》《6》仍 Hold。
