# iter5 change — additive mid-size SHM (maxMessageSize 280000)

**One change.** Config-only. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter4/`](../2026-09-10-iter4/README.md) existed on `main` (PR #9, SHA `38f9db4a3c26d5618a31a03c012a3c6605d50f57`).

## Hypothesis

iter4 kept `preallocated_number=32`, `dynamic=false`. That recovered about half of the booked same-host **Reliable** 100/256 KiB tax. 1 MiB same-host stayed at or better than iter3. The leftover primary is BestEffort mid-size:

| case (iter4 vs iter3 / vs iter2-after, same-host) | p50 |
|---------------------------------------------------|-----|
| BestEffort 256 KiB | 1592 → 1653 µs (**+3.8%** / still **+12.9%** vs iter2-after) — **not recovered** |
| BestEffort 100 KiB | 1258 → 1214 µs (−3.5% / still +6.0% vs iter2-after) |
| Reliable 100/256 KiB | −8–9% vs iter3 (keep) |
| BestEffort 1 MiB | 2935 → 3002 µs (+2.3%, noise of iter3; **−23%** vs iter2-after — keep) |
| Reliable 1 MiB | 3178 → 2917 µs (−8.2% — keep) |

Same-process is **out of scope**. Shrinking the 32-slab (16 / 0) stays discarded.

Humble Fast-DDS **2.6.12** builtin SHM `segment_size` is **512 KiB** and `maxMessageSize` is **65500**. Same-host 256 KiB BestEffort is ~4 fragments plus a reassembly copy on that ceiling.

**Not kept:** exclusive UDP+SHM with `segment_size=768 KiB`. BestEffort 256 KiB 1653 → 1309 µs, but BestEffort 1 MiB **80/80 → 1/80**. Fast-DDS prefers SHM for same-host and does not fall back to UDP when the segment is short. Discarded.

**Not kept:** UDP-only (`useBuiltinTransports=false`, no SHM). BestEffort 256 KiB stayed ~1645 µs (flat vs iter4). BestEffort 1 MiB **0/90**. Replacing builtin UDP dropped the iter2 socket-buffer path. Discarded. Prefer not regressing 1 MiB.

**Prediction:** keep builtin transports (iter2 2 MiB sockets still apply) and add **one** user SHM with `maxMessageSize=280000` (100/256 KiB as a single RTPS message) and `segment_size=2097152`. 1 MiB (1048576 > 280000) stays fragmented on the builtin path. This is not the discarded iter3 probe (`maxMessageSize` 2 MiB / `segment_size` 4 MiB), which sent 1 MiB unfragmented and lost ~36%. Ping-pong loads `FASTRTPS_DEFAULT_PROFILES_FILE`.

This is **one knob** (additive mid-size SHM). Not a socket-buffer change. Not a send-buffer-pool change.

This does **not** prove a Feishu / real-robot / cross-host root cause.

## Exact diff (behavior)

In `config/fastdds.xml` only: one additive SHM transport; `useBuiltinTransports` stays true.

```xml
<transport_descriptor>
    <transport_id>shm_midsize</transport_id>
    <type>SHM</type>
    <maxMessageSize>280000</maxMessageSize>
    <segment_size>2097152</segment_size>
</transport_descriptor>
```

`preallocated_number=32` / `dynamic=false` stay. `config/fastdds.zh.md` notes the knob.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, domain 42)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB (left as-is on the participant)
- iter3/4 `preallocated_number=32` / `dynamic=false` (left as-is)
- Builtin SHM `maxMessageSize` (stays 65500). The additive transport is 280000, not the iter3 2 MiB / 4 MiB probe.
- Chain B Cyclone URI / iceoryx
- Cross-host UDP (still blocked; single VM)
- 《3》90%/LLM scoring, 《4》Mac/preprod hero, 《5》Promptfoo, 《6》CVE audit

## Remeasure command (same as iter4, Chain A only)

```bash
BENCH_DATE=2026-09-10-iter5 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A \
  ./scripts/bench/run_large_packet.sh
```

Like-to-like vs `docs/artifacts/bench/2026-09-10-iter4/` (primary). Honesty vs `2026-09-10-iter2-after` for mid-size. 1 MiB must stay within noise of iter4 (or better). Primary table: **same-host**. Same-process is an honesty check only. Deltas in [`delta.md`](delta.md). Do not put Chain A and Chain B in one table.

## Keep

Kept. Same-host BestEffort 256 KiB p50 **−18.6%** vs iter4 (and **−8.0%** vs iter2-after). 1 MiB BestEffort/Reliable 80/80 and faster than iter4. Exclusive 768 KiB SHM and UDP-only stay discarded.
