# Chain A Fast-DDS scoreboard (iter10)

**Path B.** Docs only. No new transport knob. `config/fastdds.xml` is still the **iter7 seed**. Ask a human to merge; this run does not merge.

This page is the **current best config + best measured tables** after iters 1–9. It does **not** remasure. It does **not** change middleware behavior.

**不是** 飞书现场、实机、或跨机根因证明。Not Feishu field proof. Not a real-robot claim. Not a cross-host root cause.

《3》90%/LLM scoring, 《4》Mac/preprod hero, 《5》Promptfoo, 《6》CVE audit — still **Hold**.

Do **not** put these numbers in a table with Chain B. Do **not** mix `same-process` / `same-host` / `cross-host-UDP`. Cross-host UDP remains `STATUS: blocked` (single VM).

## Why no new knob (knife 10)

Path A wanted **one** knob from a **new family**, not discovery / liveliness / lease / WLP, aimed at Chain A same-host **64 B / 200 Hz** jitter (RTT p95/p99 + arrival `|I−5 ms|` p95), remasured vs iter7, kept only if the jitter gate passes, without spitting 1 MiB / mid-size gains.

No solid candidate:

| leftover family | why not probed |
|-----------------|----------------|
| SIMPLE discovery / `leaseAnnouncement` / `leaseDuration` | **Forbidden to retry.** iter8 discarded (arrival jitter worse). |
| Writer Liveliness Protocol | **Forbidden to retry.** iter9 discarded (arrival `|I−5 ms|` p95 375 → 543 µs). |
| `port_queue_capacity` | **Forbidden to retry.** iter6 discarded. Same SHM-queue family. |
| Exclusive / oversized SHM | **Forbidden to retry.** Erased 1 MiB BestEffort. |
| `historyMemoryPolicy` / `publishMode` / data-sharing | Would need `RMW_FASTRTPS_USE_QOS_FROM_XML` plus default writer/reader profiles. Ping-pong uses `testdata.py` QoS names, not the topic profiles in `fastdds.xml`. Iters 7–9 explicitly left this unset. Binding it is not “one XML knob.” |
| Thread / affinity / reception_threads | Speculative on a shared 4-vCPU `cursor-cloud-vm`. No isolcpus. Cannot separate scheduling noise from a keep signal. |

A weak knob would only add another discarded artifact. The honest land is this scoreboard.

## Current best config

Landed file: [`config/fastdds.xml`](../../../config/fastdds.xml). Chinese notes: [`config/fastdds.zh.md`](../../../config/fastdds.zh.md).

| item | value |
|------|--------|
| Tree that holds this XML | `main` @ [`a048b0cfe2b3eee17c35ef6896ebd1dc186046ea`](https://github.com/topsun-bot/ros2_hzj/commit/a048b0cfe2b3eee17c35ef6896ebd1dc186046ea) (PR #19 merge; XML equals iter7) |
| XML seed commit | [`5efbca352b9e442234412f982c7e6af59f85c0c8`](https://github.com/topsun-bot/ros2_hzj/commit/5efbca352b9e442234412f982c7e6af59f85c0c8) (`healthy_check_timeout_ms` 10000) |
| iter7 remasure land | [`5d1ed6037968f4a51afad12476a6b0bf727ac2d4`](https://github.com/topsun-bot/ros2_hzj/commit/5d1ed6037968f4a51afad12476a6b0bf727ac2d4) |
| iter7 merge | [`63574b8666490f5f88954eb80db21852b7f611e8`](https://github.com/topsun-bot/ros2_hzj/commit/63574b8666490f5f88954eb80db21852b7f611e8) (PR #12) |
| RMW / domain | `rmw_fastrtps_cpp` / `ROS_DOMAIN_ID=42` (operator must `source config/env/chain_a.sh`) |
| Builtin transports | **on** (UDP + implicit SHM) |
| Additive SHM | `shm_midsize`: `maxMessageSize=280000`, `segment_size=2097152` (2 MiB) |
| SHM health-check | `healthy_check_timeout_ms=10000` |
| UDP sockets | `sendSocketBufferSize` / `listenSocketBufferSize` = 2097152 (2 MiB) |
| RTPS send-buffer pool | `preallocated_number=32`, `dynamic=false` |
| 1 MiB path | sample 1048576 > 280000 → builtin fragment path (not unfragmented SHM) |

Humble Fast-DDS 2.6 History stays in `<topic><historyQos>` (iter1 schema). Topic writer/reader profiles are R0 contract seeds, **not** ping-pong bindings.

## Kept knobs

| iter | knob | family | remasure SHA | merge SHA / PR | artifacts |
|------|------|--------|--------------|----------------|-----------|
| 1 | Humble-valid `<historyQos>` | XML schema (not transport) | — | [`5aa5e90`](https://github.com/topsun-bot/ros2_hzj/commit/5aa5e90256ddb3377ca41f34bc76ae7749e221ce) / [#6](https://github.com/topsun-bot/ros2_hzj/pull/6) | [`2026-09-10-iter1/`](2026-09-10-iter1/README.md) |
| 2 | UDP send/listen socket 2 MiB | socket buffers | [`58584a5`](https://github.com/topsun-bot/ros2_hzj/commit/58584a5badeb3fce150795552d58c93a7bf4c01c) | [`6478da4`](https://github.com/topsun-bot/ros2_hzj/commit/6478da41ef849172f9647fb2e38f78d1a2201b71) / [#7](https://github.com/topsun-bot/ros2_hzj/pull/7) | [`2026-09-10-iter2-after/`](2026-09-10-iter2-after/README.md) |
| 3 | `send_buffers` `preallocated_number=32` | RTPS send-buffer pool | land [`1597017`](https://github.com/topsun-bot/ros2_hzj/commit/1597017b48db811ded639d381066d589dbd4e2ea) | [`270d982`](https://github.com/topsun-bot/ros2_hzj/commit/270d982dc20c49fd788eb80dff7da2e70a4d42c2) / [#8](https://github.com/topsun-bot/ros2_hzj/pull/8) | [`2026-09-10-iter3/`](2026-09-10-iter3/README.md) |
| 4 | same pool, `dynamic=false` | RTPS send-buffer pool | land [`1df9203`](https://github.com/topsun-bot/ros2_hzj/commit/1df92035a093d307ffe9ba6659286ab9255d1e2e) | [`38f9db4`](https://github.com/topsun-bot/ros2_hzj/commit/38f9db4a3c26d5618a31a03c012a3c6605d50f57) / [#9](https://github.com/topsun-bot/ros2_hzj/pull/9) | [`2026-09-10-iter4/`](2026-09-10-iter4/README.md) |
| 5 | additive `shm_midsize` 280000 / 2 MiB | mid-size SHM | [`364f7cc`](https://github.com/topsun-bot/ros2_hzj/commit/364f7ccda1e4a09b7d0e4b1abff1fffb51c8b037) | [`cde262e`](https://github.com/topsun-bot/ros2_hzj/commit/cde262e3c5d023c4665e2dbf279aaeb0a338cf09) / [#10](https://github.com/topsun-bot/ros2_hzj/pull/10) | [`2026-09-10-iter5/`](2026-09-10-iter5/README.md) |
| 7 | `healthy_check_timeout_ms` 10000 | SHM health-check | [`5efbca3`](https://github.com/topsun-bot/ros2_hzj/commit/5efbca352b9e442234412f982c7e6af59f85c0c8) | [`63574b8`](https://github.com/topsun-bot/ros2_hzj/commit/63574b8666490f5f88954eb80db21852b7f611e8) / [#12](https://github.com/topsun-bot/ros2_hzj/pull/12) | [`2026-09-11-iter7/`](2026-09-11-iter7/README.md) |

iter6 Step A (no new knob) nailed IMU **64 B / 200 Hz**. That baseline stays: [`2026-09-10-iter6-imu-baseline/`](2026-09-10-iter6-imu-baseline/README.md), merge [`0cee4ee`](https://github.com/topsun-bot/ros2_hzj/commit/0cee4ee96e07d405bcd423d2a256482c67a061a1) / [#11](https://github.com/topsun-bot/ros2_hzj/pull/11).

## Discarded knobs (do not retry)

| iter | probe | family | remasure SHA | why discarded | artifacts |
|------|-------|--------|--------------|---------------|-----------|
| 3 | unfragmented SHM `maxMessageSize` 2 MiB / segment 4 MiB | oversized SHM | [`3544eda`](https://github.com/topsun-bot/ros2_hzj/commit/3544eda86c63a2c4636c632c52ef67e859b3b915) | same-host 1 MiB regressed | [`2026-09-10-iter3/change.md`](2026-09-10-iter3/change.md) |
| 4 | `preallocated_number` 16; then 0 (`dynamic` still true) | send-buffer pool size | [`a802daa`](https://github.com/topsun-bot/ros2_hzj/commit/a802daa77c6592cbb80c595ab59c96d4746d3622), [`c1b4ae6`](https://github.com/topsun-bot/ros2_hzj/commit/c1b4ae650b2ba816541ad2b924ef1031b043ddb3) | mid-size not recovered; 0 erased 1 MiB win | [`2026-09-10-iter4/change.md`](2026-09-10-iter4/change.md) |
| 5 | exclusive SHM segment 768 KiB | exclusive SHM | [`adc96cb`](https://github.com/topsun-bot/ros2_hzj/commit/adc96cb19903f14fa961966a08ca85033730cc62) | BestEffort 1 MiB 80/80 → 1/80 | [`2026-09-10-iter5/change.md`](2026-09-10-iter5/change.md) |
| 5 | UDP-only / no SHM | exclusive UDP | [`ff1fbc5`](https://github.com/topsun-bot/ros2_hzj/commit/ff1fbc5ade1b1dc426f15701d548fde0fe2970ed) | BestEffort 1 MiB 0/90 | [`2026-09-10-iter5/change.md`](2026-09-10-iter5/change.md) |
| 6 | `shm_midsize` `port_queue_capacity` 64 | SHM port queue | [`2d904a5`](https://github.com/topsun-bot/ros2_hzj/commit/2d904a598c8a6f8a1a3fdbd19dc3d34bdf5fed41) | BestEffort RTT p95 1205 → 1234 µs; arrival \|I−5 ms\| p95 488 → 568 µs | [`2026-09-10-iter6-after/`](2026-09-10-iter6-after/README.md) |
| 8 | SIMPLE `leaseAnnouncement` 15 s | discovery / lease | [`be6016b`](https://github.com/topsun-bot/ros2_hzj/commit/be6016bc049aebc191784c1c0e376f2c19c8a361) | arrival \|I−5 ms\| p95 375 → 448 µs; repeat lost RTT p95 win | [`2026-09-11-iter8/`](2026-09-11-iter8/README.md) |
| 9 | `use_WriterLivelinessProtocol` false | liveliness / WLP | [`44ad5d2`](https://github.com/topsun-bot/ros2_hzj/commit/44ad5d25c7ac0bcb445d6ad80a45b2c78eb2256a) | arrival \|I−5 ms\| p95 375 → 543 µs (repeat 413, still wide) | [`2026-09-11-iter9/`](2026-09-11-iter9/README.md) |

Discard merges (XML reverted to the then-current seed): iter6 [`0cee4ee`](https://github.com/topsun-bot/ros2_hzj/commit/0cee4ee96e07d405bcd423d2a256482c67a061a1) / [#11](https://github.com/topsun-bot/ros2_hzj/pull/11); iter8 [`d611bfd`](https://github.com/topsun-bot/ros2_hzj/commit/d611bfdf7df2d95c9a362727380126bfc4321665) / [#17](https://github.com/topsun-bot/ros2_hzj/pull/17); iter9 [`a048b0c`](https://github.com/topsun-bot/ros2_hzj/commit/a048b0cfe2b3eee17c35ef6896ebd1dc186046ea) / [#19](https://github.com/topsun-bot/ros2_hzj/pull/19).

## Best measured table — large-packet same-host

**Booked table:** [`2026-09-10-iter5/chain_a_same_host/summary.md`](2026-09-10-iter5/chain_a_same_host/summary.md)  
**Delta:** [`2026-09-10-iter5/delta.md`](2026-09-10-iter5/delta.md)  
**Remasure SHA:** [`364f7ccda1e4a09b7d0e4b1abff1fffb51c8b037`](https://github.com/topsun-bot/ros2_hzj/commit/364f7ccda1e4a09b7d0e4b1abff1fffb51c8b037)  
**Command:** `BENCH_DATE=2026-09-10-iter5 CHAIN_A_IMAGE=osrf/ros:humble-desktop LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh`  
**Image:** `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e`  
**Payload / gap / samples:** 102400 / 262144 / 1048576 B; 100 ms (target 10 Hz); 80 samples.

数字是 **ping-pong RTT**（`scripts/bench/pingpong.py`）。**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

| case | payload (B) | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) |
|------|-------------|--------:|---------:|---------:|---------:|---------:|
| `ros_high_throughput` | 102400 | 80 | 0 | 1153.9 | 1355.7 | 1448.6 |
| `ros_high_throughput` | 262144 | 80 | 0 | 1345.9 | 1541.1 | 1583.1 |
| `ros_high_throughput` | 1048576 | 80 | 0 | 2312.2 | 2841.0 | 3138.2 |
| `ros_reliable` | 102400 | 80 | 0 | 1143.4 | 1290.4 | 1332.8 |
| `ros_reliable` | 262144 | 80 | 0 | 1353.4 | 1523.4 | 1571.3 |
| `ros_reliable` | 1048576 | 80 | 0 | 2368.5 | 2699.1 | 2843.0 |

Headline vs iter4 (same-host): BestEffort 256 KiB p50 **−18.56%** (1653 → 1346 µs); BestEffort 1 MiB p50 **−22.98%** (3002 → 2312 µs, 80/80); Reliable 1 MiB p50 **−18.80%** (2917 → 2368 µs, 80/80).

iter7 same-host **spot** (health-check 10 s on; do **not** replace the booked table): BestEffort 256 KiB 1346/1541 → 1305/1474 µs; BestEffort 1 MiB 2312/2841 → 2301/2733 µs; Reliable 1 MiB 2368/2699 → 2339/2597 µs; all 80/80. See [`2026-09-11-iter7/change.md`](2026-09-11-iter7/change.md). **1 MiB / mid-size gains were not spat.**

## Best measured table — IMU HF same-host

**Booked table:** [`2026-09-11-iter7/chain_a_same_host/summary.md`](2026-09-11-iter7/chain_a_same_host/summary.md)  
**Delta vs IMU baseline:** [`2026-09-11-iter7/delta.md`](2026-09-11-iter7/delta.md)  
**Baseline:** [`2026-09-10-iter6-imu-baseline/chain_a_same_host/summary.md`](2026-09-10-iter6-imu-baseline/chain_a_same_host/summary.md)  
**Remasure SHA:** [`5efbca352b9e442234412f982c7e6af59f85c0c8`](https://github.com/topsun-bot/ros2_hzj/commit/5efbca352b9e442234412f982c7e6af59f85c0c8)  
**Command:** `BENCH_DATE=2026-09-11-iter7 CHAIN_A_IMAGE=osrf/ros:humble-desktop IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh`  
**Image:** same Humble digest as the large-packet table.  
**Payload / gap / samples:** **64 B**; **5 ms** (target **200 Hz**); 400 samples.

Primary metric is **jitter** (RTT p95/p99 + arrival interval). Do **not** claim success from p50/mean. **不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

### RTT

| case | payload (B) | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) |
|------|-------------|--------:|---------:|---------:|---------:|---------:|
| `ros_high_throughput` | 64 | 400 | 0 | 988.38 | 1147.9 | 1237.6 |
| `ros_reliable` | 64 | 400 | 0 | 970.54 | 1173.4 | 1249.7 |

### Jitter (gate)

| case | RTT p95−p50 (µs) | arr I stdev (µs) | arr \|I−5 ms\| p95 (µs) | arr \|I−5 ms\| p99 (µs) |
|------|-----------------:|-----------------:|------------------------:|------------------------:|
| `ros_high_throughput` | 159.54 | 167.66 | 375.21 | 508.44 |
| `ros_reliable` | 202.90 | 289.35 | 569.21 | 705.98 |

vs iter6 IMU baseline (same-host BestEffort): RTT p95 1205 → 1148 µs (**−4.76%**); RTT p99 1336 → 1238 µs (**−7.34%**); arrival \|I−5 ms\| p95 488 → 375 µs. p50 rose 957 → 988 µs — **not** the gate.

same-process tables exist for honesty only. **Do not tune** for them.

## What this is not

- **Not Feishu field proof.** 不是飞书现场丢包、卡顿、或实机根因。
- Not a cross-host / two-machine measurement (`cross-host-UDP` is blocked on this VM).
- Not a Chain A vs Chain B comparison.
- Not a claim that vendor SHAs or RMW names cause latency.
- Not a keep of leaseAnnouncement, WLP off, `port_queue_capacity` 64, exclusive SHM, or oversized SHM.
- Not 《3》90%/LLM scoring, 《4》Mac/preprod, 《5》Promptfoo, or 《6》CVE.

## Cross-host UDP baseline status

**STATUS: blocked** on this SCOREBOARD host (single `cursor-cloud-vm`). No second machine, so **no p50 / p95 / p99**. Do not invent numbers.

Recipe + runner (two real hosts later): [`scripts/bench/run_cross_host_a.sh`](../../../scripts/bench/run_cross_host_a.sh). How-to: [`scripts/bench/README.md`](../../../scripts/bench/README.md). Placeholder artifacts: [`2026-09-11-cross-host/`](2026-09-11-cross-host/README.md).

This section is a **pointer only**. It does **not** change current best config, booked same-host tables, or the iter7 `fastdds.xml` seed.

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

## CN / JP public ROS 2 absorb (pointer only)

Documented, citable Japan / mainland-China ROS 2 · DDS practices mapped onto the dual-chain contract: [`docs/architecture/cn-jp-ros2-absorb.md`](../../architecture/cn-jp-ros2-absorb.md). Optional Chain B **labeled example** (not default, not this scoreboard): [`scripts/bench/cyclonedds_autoware_like.xml`](../../../scripts/bench/cyclonedds_autoware_like.xml).

Hold: Agnocast vendor / kmod, new RMW (`rmw_zenoh`), distro rebase, flipping `data_sharing` in the live XML, regressing iter2 2 MiB sockets. 《3》–《6》 still Hold.

This section is a **pointer only**. It does **not** change current best config, booked same-host tables, or the iter7 `fastdds.xml` seed.

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

Index of every dated run: [`README.md`](README.md). How to re-run: [`docs/usage/benchmark-dds.md`](../../usage/benchmark-dds.md), [`scripts/bench/README.md`](../../../scripts/bench/README.md).
