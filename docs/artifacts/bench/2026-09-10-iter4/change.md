# iter4 change — right-size Fast-DDS send-buffer pool (32 → 16)

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

Humble Fast-DDS 2.6 `SendBuffersManager::init` allocates one contiguous slab for every preallocated `RTPSMessageGroup_t` (`common_buffer_`, ~2 × `maxMessageSize` ≈ 128 KiB each). 32 buffers ≈ 4 MiB; 16 buffers ≈ 2 MiB. A 1 MiB sample is ~16 × 64 KiB UDP/RTPS fragments — that is the number iter3 itself named. 32 is 2× that burst. Mid-size samples are ~2–4 fragments and still pay for the oversized slab.

`get_buffer` is LIFO and does not consult `dynamic` unless the pool is empty, so `dynamic=true` is not the mid-size tax. The tax is `preallocated_number=32`.

**Prediction:** on the default participant (`is_default_profile="true"`), set `preallocated_number` to **16** and keep `dynamic` **true**. Same-host 100 KiB and/or 256 KiB p50 should move back toward iter2-after. Same-host 1 MiB BestEffort/Reliable should stay within noise of iter3 (16 still covers one 1 MiB fragment burst; `dynamic=true` still avoids a wait if the pool is briefly short). Ping-pong loads `FASTRTPS_DEFAULT_PROFILES_FILE`, so this participant knob can apply.

`preallocated_number` retune is **one knob** (the same send-buffer pool iter3 introduced). Not a socket-buffer change (iter2 2 MiB stay). Not history / flow-controller / async-publish / SHM.

This does **not** prove a Feishu / real-robot / cross-host root cause. Same-host localhost is not that scene.

## Exact diff (behavior)

In `config/fastdds.xml` only, inside the default participant `<allocation><send_buffers>` (iter2 socket buffers and iter3 `dynamic=true` unchanged):

```xml
<preallocated_number>16</preallocated_number>
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
