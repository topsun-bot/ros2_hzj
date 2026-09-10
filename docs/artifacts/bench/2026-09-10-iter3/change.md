# iter3 change — Fast-DDS default-participant send-buffer pool (32, dynamic)

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

iter2 working is evidence that 1 MiB same-host still traverses **fragmented localhost UDP** (~64 KiB RTPS/UDP messages). Humble Fast-DDS 2.6.12 `SendBuffersAllocationAttributes` defaults are:

- `preallocated_number` **0** → initial guess from the number of threads that might send
- `dynamic` **false** → if no send buffer is free, **wait** for one to return (latency vs alloc trade-off; see Fast-DDS 2.6 SendBuffersAllocationAttributes)

A 1 MiB sample is ~16 fragments; a 256 KiB sample is ~4. On this 4-logical-CPU VM the guessed pool can be smaller than a 1 MiB burst. Waiting for buffers inflates same-host 1 MiB RTT while 100/256 KiB (fewer fragments) stay cheap.

**Not kept:** a user SHM transport with `maxMessageSize` 2 MiB / `segment_size` 4 MiB (additive, then exclusive). Humble default `maxMessageSize` is 65500 and builtin SHM `segment_size` is 512 KiB, so that was the first candidate. Exclusive SHM **regressed** same-host 1 MiB p50 by ~36% (BestEffort 3906 → 5314 µs; Reliable 3305 → 4497 µs). XMLPARSER accepted it; the data-path hypothesis was wrong. Reverted. Not a second knob.

**Prediction:** on the default participant (`is_default_profile="true"`), set the send-buffer pool to **32** preallocated buffers and `dynamic` **true** so a 1 MiB fragment burst never blocks on the pool. Same-host 1 MiB BestEffort/Reliable RTT should drop if the leftover cost was send-buffer wait. Ping-pong loads `FASTRTPS_DEFAULT_PROFILES_FILE`, so this participant knob can apply (unlike named foxglove / goal_pose profiles).

`preallocated_number` and `dynamic` are **one knob** (the same send-buffer pool). Setting only `preallocated_number` could still wait if 32 is slightly short; `dynamic` true is the documented “do not block” half of that pool. Not a socket-buffer change (iter2 2 MiB stay). Not history / flow-controller / async-publish / SHM.

This does **not** prove a Feishu / real-robot / cross-host root cause. Same-host localhost is not that scene.

## Exact diff (behavior)

In `config/fastdds.xml` only, inside the default participant `<rtps>` (iter2 socket buffers unchanged):

```xml
<allocation>
    <send_buffers>
        <preallocated_number>32</preallocated_number>
        <dynamic>true</dynamic>
    </send_buffers>
</allocation>
```

No writer/reader QoS, domain, RMW, transport, history, or flow-controller change. `config/fastdds.zh.md` notes the knob.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, domain 42)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB (left as-is)
- No SHM / `userTransports` / `useBuiltinTransports` (probe reverted)
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
