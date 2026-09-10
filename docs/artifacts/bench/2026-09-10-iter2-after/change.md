# iter2 change — Fast-DDS default-participant UDP socket buffers (2 MiB)

**One change.** Config-only. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter2-large-baseline/`](../2026-09-10-iter2-large-baseline/README.md) existed on the branch.

## Hypothesis

The Step A large-packet baseline showed:

- 1 MiB **same-process** completes on Chain A (p50 a few ms).
- 1 MiB **same-host** BestEffort: **90/90 timeouts** (0 samples).
- 1 MiB **same-host** Reliable: 80/80 samples but p50 ≈ 47 ms (much larger than 256 KiB).

Humble Fast-DDS 2.6 default `sendSocketBufferSize` / `listenSocketBufferSize` are 0 (OS default). On this Linux that is typically ~212 KiB (`net.core.wmem_default` / `rmem_default`), **smaller than a 1 MiB sample**. Large RTPS samples are fragmented (~64 KiB UDP). A short burst of fragments can overflow the socket buffer: BestEffort drops (timeouts); Reliable retransmits (inflated RTT).

**Prediction:** setting the **default participant** (`is_default_profile="true"`) buffers to 2 MiB (2097152) — enough for one 1 MiB sample plus headers — reduces same-host 1 MiB BestEffort loss and/or Reliable RTT. Ping-pong participants load `FASTRTPS_DEFAULT_PROFILES_FILE`, so this knob can actually apply (unlike named foxglove / goal_pose profiles that ping-pong does not bind).

Send and listen are **one knob** (the same 2 MiB UDP socket buffer on the default participant). Ping-pong is bidirectional; setting only one side would be an incomplete application of that knob.

This does **not** prove a Feishu / real-robot / cross-host root cause. Same-host localhost is not that scene. Kernel `wmem_max` may still cap the request; if so, deltas stay honest.

## Exact diff (behavior)

In `config/fastdds.xml` only, inside the default participant `<rtps>`:

```xml
<sendSocketBufferSize>2097152</sendSocketBufferSize>
<listenSocketBufferSize>2097152</listenSocketBufferSize>
```

No other participant / writer / reader / QoS / domain / RMW change. `config/fastdds.zh.md` notes the knob. No `historyMemoryPolicy`, no UDP-only transport, no sysctl, no Chain B URI.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, domain 42)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`
- Chain B Cyclone URI / iceoryx
- Cross-host UDP (still blocked; single VM)
- 《3》90%/LLM scoring, 《4》Mac/preprod hero, 《5》Promptfoo, 《6》CVE audit

## Remeasure command (same as Step A, Chain A only)

The knob is Fast-DDS XML. Chain B is unchanged; it is **not** remasured (not a treatment).

```bash
BENCH_DATE=2026-09-10-iter2-after \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A \
  ./scripts/bench/run_large_packet.sh
```

Like-to-like vs `docs/artifacts/bench/2026-09-10-iter2-large-baseline/` Chain A only: sizes `102400,262144,1048576`, gap 100 ms, 80 samples, `uint8_multiarray`. Deltas in [`delta.md`](delta.md). Do not put Chain A and Chain B in one table.
