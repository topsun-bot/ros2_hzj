# iter4 change — send-buffer pool 32, dynamic=false

**One change.** Config-only. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter3/`](../2026-09-10-iter3/README.md) existed on `main` (PR #8, SHA `270d982dc20c49fd788eb80dff7da2e70a4d42c2`).

## Hypothesis

iter3 kept `preallocated_number=32`, `dynamic=true`. That recovered Chain A **same-host** 1 MiB BestEffort p50 by ~25% (3906 → 2935 µs). The booked cost is mid-size same-host, worse on Reliable:

| case (iter3 vs iter2-after, same-host) | p50 |
|----------------------------------------|-----|
| BestEffort 100 KiB | 1146 → 1258 µs (**+9.8%**) |
| BestEffort 256 KiB | 1463 → 1592 µs (**+8.8%**) |
| Reliable 100 KiB | 1130 → 1393 µs (**+23.3%**) |
| Reliable 256 KiB | 1363 → 1693 µs (**+24.3%**) |

Same-process mid-size is **out of scope**. SHM exclusive / `maxMessageSize` stays discarded.

Humble Fast-DDS **2.6.12** `SendBuffersManager::get_buffer` (not the newer vendor tree): when the pool is empty and `dynamic=true`, it `new`s an `RTPSMessageGroup_t` on the hot path (`add_one_buffer`, separate heap, not the init slab). When `dynamic=false`, it waits for a buffer to return. iter3’s own comment called this a latency-vs-alloc trade-off.

Reliable ping-pong uses more concurrent senders (DATA + HEARTBEAT / ACKNACK) than BestEffort, so it is more likely to empty a pool and hit that grow. That matches the booked +23–24% Reliable mid-size tax vs +9% BestEffort.

**Not kept:** shrinking `preallocated_number` (32 → 16, then 0) with `dynamic` still true. 16 did not recover same-host 100/256 KiB vs iter3 (BestEffort mid-size moved the wrong way; Reliable only nudged). 0 erased the 1 MiB win (BestEffort 2935 → 5075 µs; Reliable 3178 → 4025 µs) because a default-sized pool grows on every 1 MiB burst. Discarded. Not a second knob.

**Prediction:** keep `preallocated_number=32` (the 1 MiB slab) and set `dynamic=false`. Same-host 100/256 KiB — especially Reliable — should move toward iter2-after if the leftover cost was hot-path grow. Same-host 1 MiB should stay near iter3 if 32 is enough that a 1 MiB burst never waits. Ping-pong loads `FASTRTPS_DEFAULT_PROFILES_FILE`.

This is **one knob** (the same send-buffer pool). Not a socket-buffer change (iter2 2 MiB stay). Not SHM.

This does **not** prove a Feishu / real-robot / cross-host root cause.

## Exact diff (behavior)

In `config/fastdds.xml` only, inside the default participant `<allocation><send_buffers>`:

```xml
<dynamic>false</dynamic>
```

was `true`. `preallocated_number` stays `32`. `config/fastdds.zh.md` notes the knob.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, domain 42)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB (left as-is)
- iter3 `preallocated_number=32` (left as-is)
- No SHM / `userTransports` / `useBuiltinTransports`
- Chain B Cyclone URI / iceoryx
- Cross-host UDP (still blocked; single VM)
- 《3》90%/LLM scoring, 《4》Mac/preprod hero, 《5》Promptfoo, 《6》CVE audit

## Remeasure command (same as iter3, Chain A only)

```bash
BENCH_DATE=2026-09-10-iter4 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A \
  ./scripts/bench/run_large_packet.sh
```

Like-to-like vs `docs/artifacts/bench/2026-09-10-iter3/` (primary). Honesty vs `2026-09-10-iter2-after` for mid-size. Primary table: **same-host**. Same-process is an honesty check only. Deltas in [`delta.md`](delta.md). Do not put Chain A and Chain B in one table.
