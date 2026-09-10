# iter3 change — Fast-DDS default-participant large SHM transport

**One change.** Config-only. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter2-after/`](../2026-09-10-iter2-after/README.md) existed on `main` (PR #7, SHA `6478da41ef849172f9647fb2e38f78d1a2201b71`).

## Hypothesis

iter2 set default-participant UDP socket buffers to 2 MiB. That recovered Chain A **same-host** 1 MiB BestEffort (0/90 → 80/80) and cut same-host 1 MiB Reliable p50 by ~93%. The remaining same-host large-packet RTT is still high vs 100/256 KiB:

| case (iter2-after, same-host) | p50 |
|-------------------------------|-----|
| BestEffort 256 KiB | 1463 µs |
| BestEffort 1 MiB | 3906 µs |
| Reliable 256 KiB | 1363 µs |
| Reliable 1 MiB | 3305 µs |

Same-process +4–8% from iter2 is **out of scope** (honesty check only; do not tune for it).

iter2 working is evidence that 1 MiB same-host still traversed **fragmented localhost UDP**: Linux default socket buffers (~212 KiB) overflowed a ~16-fragment burst. Humble Fast-DDS 2.6 builtin transports also enable SHM, but the documented defaults cannot carry these payloads unfragmented:

- Transport `maxMessageSize` default **65500** (Fast-DDS 2.6 XML / TransportDescriptor). 100 KiB / 256 KiB / 1 MiB all exceed it.
- Builtin SHM `segment_size` default **512 KiB**. Docs warn that a segment close to or smaller than the sample risks overwrite/loss. 1 MiB > 512 KiB.

So same-host 100 KiB–1 MiB cannot stay on a single SHM message; they fragment (~64 KiB) and, as iter2 showed, the 1 MiB burst used UDP.

**Prediction:** add **one** user SHM transport on the default participant (`is_default_profile="true"`) with `maxMessageSize` 2 MiB (2097152) and `segment_size` 4 MiB (4194304) — enough for one 1 MiB sample plus headers, and room so a bidirectional ping-pong write does not overwrite the segment. Same-host 1 MiB (and 100/256 KiB) BestEffort/Reliable RTT should drop if the data path can stay on SHM instead of fragmented UDP. Ping-pong loads `FASTRTPS_DEFAULT_PROFILES_FILE`, so this participant knob can apply (unlike named foxglove / goal_pose profiles).

`maxMessageSize` and `segment_size` are **one knob** (the same oversized SHM transport). Setting only `maxMessageSize` would still leave the 512 KiB implicit segment too small for 1 MiB. Builtin UDP and the iter2 2 MiB socket buffers stay (`useBuiltinTransports` true). Not SHM-only. Not a second buffer / history / flow-controller change.

This does **not** prove a Feishu / real-robot / cross-host root cause. Same-host localhost is not that scene. Docker `--ipc=host` is already in `docker_chain_a.sh`; if SHM still fails over to UDP, deltas stay honest.

## Exact diff (behavior)

In `config/fastdds.xml` only:

1. A `transport_descriptors` entry `shm_large_same_host` (`type` SHM):

```xml
<maxMessageSize>2097152</maxMessageSize>
<segment_size>4194304</segment_size>
```

2. On the default participant `<rtps>`, reference it and keep builtin transports:

```xml
<userTransports>
    <transport_id>shm_large_same_host</transport_id>
</userTransports>
<useBuiltinTransports>true</useBuiltinTransports>
```

No writer/reader QoS, domain, RMW, socket-buffer, history, or flow-controller change. `config/fastdds.zh.md` notes the knob.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, domain 42)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`, no flow controller
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB (left as-is)
- Chain B Cyclone URI / iceoryx
- Cross-host UDP (still blocked; single VM)
- 《3》90%/LLM scoring, 《4》Mac/preprod hero, 《5》Promptfoo, 《6》CVE audit

## Remeasure command (same as iter2-after, Chain A only)

The knob is Fast-DDS XML. Chain B is unchanged; it is **not** remasured (not a treatment).

```bash
BENCH_DATE=2026-09-10-iter3 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A \
  ./scripts/bench/run_large_packet.sh
```

Like-to-like vs `docs/artifacts/bench/2026-09-10-iter2-after/` Chain A only: sizes `102400,262144,1048576`, gap 100 ms, 80 samples, `uint8_multiarray`. Primary table: **same-host**. Same-process is an honesty check only — do not optimize for it. Deltas in [`delta.md`](delta.md). Do not put Chain A and Chain B in one table.
