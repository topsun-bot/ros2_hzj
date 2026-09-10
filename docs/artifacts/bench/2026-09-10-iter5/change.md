# iter5 change — UDP-only default participant (no builtin SHM)

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

Same-process is **out of scope**. Shrinking the 32-slab (16 / 0) stays discarded. iter3 SHM with `maxMessageSize` 2 MiB / `segment_size` 4 MiB stays discarded.

Humble Fast-DDS **2.6.12** builtin transports are UDPv4 + SHM. Implicit SHM `segment_size` is **512 KiB**. Same-host mid-size can take SHM (fragmented ~64 KiB RTPS messages). 256 KiB BestEffort is ~4 fragments plus a reassembly copy — that pair sits on the 512 KiB ceiling. 1 MiB (~16 fragments) does not fit; with builtin transports it already uses the tuned UDP path.

**Not kept:** recreate builtin UDP+SHM with `segment_size=768 KiB` (maxMessageSize still 65500). Same-host BestEffort 256 KiB moved 1653 → 1309 µs, but BestEffort 1 MiB went **80/80 → 1/80** and Reliable 1 MiB p50 2917 → 24190 µs. Fast-DDS prefers SHM for same-host and does **not** fall back to UDP when the segment is short. Prefer not regressing 1 MiB. Discarded. Not a second knob.

**Prediction:** set `useBuiltinTransports=false` and attach only a UDPv4 user transport with the iter2 2 MiB socket buffers. Mid-size same-host BestEffort leaves the 512 KiB SHM ceiling and rides the already-tuned localhost UDP path. 1 MiB was already on that path and should stay within noise of iter4. Ping-pong loads `FASTRTPS_DEFAULT_PROFILES_FILE`.

This is **one knob** (UDP-only / no SHM). Not a socket-buffer change (2 MiB stay on the descriptor). Not a send-buffer-pool change. Not the discarded 768 KiB or unfragmented-SHM probes.

This does **not** prove a Feishu / real-robot / cross-host root cause.

## Exact diff (behavior)

In `config/fastdds.xml` only: one UDPv4 user transport (iter2 2 MiB buffers) and `useBuiltinTransports=false` on the default participant.

```xml
<transport_descriptor>
    <transport_id>udp_v4_2m</transport_id>
    <type>UDPv4</type>
    <sendBufferSize>2097152</sendBufferSize>
    <receiveBufferSize>2097152</receiveBufferSize>
</transport_descriptor>
```

`preallocated_number=32` / `dynamic=false` stay. `config/fastdds.zh.md` notes the knob.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, domain 42)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB (left as-is; also set on the UDP descriptor)
- iter3/4 `preallocated_number=32` / `dynamic=false` (left as-is)
- SHM `maxMessageSize` (stays 65500; not the iter3 2 MiB probe)
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
