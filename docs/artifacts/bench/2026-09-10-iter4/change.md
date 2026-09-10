# iter4 change — restore default send-buffer prealloc, keep dynamic

**One change.** Config-only. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter3/`](../2026-09-10-iter3/README.md) existed on `main` (PR #8, SHA `270d982dc20c49fd788eb80dff7da2e70a4d42c2`).

## Hypothesis

iter3 kept the default-participant send-buffer pool at `preallocated_number=32`, `dynamic=true`. That recovered Chain A **same-host** 1 MiB BestEffort p50 by ~25% (3906 → 2935 µs) and nudges Reliable 1 MiB (−3.8%). The booked cost is mid-size same-host:

| case (iter3 vs iter2-after, same-host) | p50 |
|----------------------------------------|-----|
| BestEffort 100 KiB | 1146 → 1258 µs (**+9.8%**) |
| BestEffort 256 KiB | 1463 → 1592 µs (**+8.8%**) |
| Reliable 100 KiB | 1130 → 1393 µs (**+23.3%**) |
| Reliable 256 KiB | 1363 → 1693 µs (**+24.3%**) |

Same-process mid-size +25–32% is **out of scope** (honesty check only; do not tune for it). SHM exclusive / `maxMessageSize` stays discarded.

Humble Fast-DDS 2.6 `SendBuffersManager::init` allocates one contiguous slab for every preallocated `RTPSMessageGroup_t` (`common_buffer_`, ~2 × `maxMessageSize` ≈ 128 KiB each). Default `preallocated_number=0` guesses from send threads (`2 + receiver resources`, typically a handful). 32 buffers ≈ 4 MiB. Mid-size samples are ~2–4 × 64 KiB fragments and do not need a 1 MiB-sized slab.

`get_buffer` only consults `dynamic` when the pool is empty. Mid-size at 10 Hz should not empty a default-sized pool. The 1 MiB leftover win is the no-wait half (`dynamic=true`): a fragment burst may grow a buffer instead of blocking.

**Not kept:** `preallocated_number` 32 → 16 (same `dynamic=true`). Same-host BestEffort 100/256 KiB p50 moved the wrong way vs iter3 (~+7–8%); Reliable mid-size only nudged (−2–5%) and stayed far from iter2-after. 16 is still ~4× the default guess. Discarded. Not a second knob.

**Prediction:** on the default participant (`is_default_profile="true"`), set `preallocated_number` to **0** (documented default guess) and keep `dynamic` **true**. Same-host 100 KiB and/or 256 KiB p50 should move back toward iter2-after (same pool size as before the 32-slab). Same-host 1 MiB BestEffort/Reliable should stay near iter3 if the leftover cost was wait-on-empty rather than the 32-slab itself; warmup (10) absorbs first-growth allocs. Ping-pong loads `FASTRTPS_DEFAULT_PROFILES_FILE`, so this participant knob can apply.

This is **one knob** (the same send-buffer pool iter3 introduced): drop the oversized prealloc, keep the no-wait half. Not a socket-buffer change (iter2 2 MiB stay). Not history / flow-controller / async-publish / SHM.

This does **not** prove a Feishu / real-robot / cross-host root cause. Same-host localhost is not that scene.

## Exact diff (behavior)

In `config/fastdds.xml` only, inside the default participant `<allocation><send_buffers>` (iter2 socket buffers and iter3 `dynamic=true` unchanged):

```xml
<preallocated_number>0</preallocated_number>
```

was `32`. No writer/reader QoS, domain, RMW, transport, history, or flow-controller change. `config/fastdds.zh.md` notes the knob.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, domain 42)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB (left as-is)
- iter3 `dynamic=true` (left as-is)
- No SHM / `userTransports` / `useBuiltinTransports` (probe stays discarded)
- Chain B Cyclone URI / iceoryx
- Cross-host UDP (still blocked; single VM)
- 《3》90%/LLM scoring, 《4》Mac/preprod hero, 《5》Promptfoo, 《6》CVE audit

## Remeasure command (same as iter3, Chain A only)

The knob is Fast-DDS XML. Chain B is unchanged; it is **not** remasured (not a treatment).

```bash
BENCH_DATE=2026-09-10-iter4 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A \
  ./scripts/bench/run_large_packet.sh
```

Like-to-like vs `docs/artifacts/bench/2026-09-10-iter3/` Chain A only (primary): sizes `102400,262144,1048576`, gap 100 ms, 80 samples, `uint8_multiarray`. Honesty vs `2026-09-10-iter2-after` where useful (mid-size recovery target). Primary table: **same-host**. Same-process is an honesty check only — do not optimize for it. Deltas in [`delta.md`](delta.md). Do not put Chain A and Chain B in one table.
