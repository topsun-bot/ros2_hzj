# iter6 Step A — IMU-scale HF baseline notes

**Step A only. No new transport / config knob.** IMU **64 B / 200 Hz** is fixed before any knob. Primary success metric is **jitter** (RTT p95/p99 + inter-message interval variance), not p50/mean. `config/fastdds.xml` is the iter5-accepted seed (mid-size SHM + prior socket / send_buffers). This directory records a **new suite**, not a treatment.

这些数字 **不是** 飞书现场、实机、或跨机根因证明。

## Why 64 B and 200 Hz

| Item | Value | Why |
|------|--------|-----|
| Payload | **64 B** | Compact 6-axis IMU sample: 8 B `uint64` timestamp + 24 B accel (`3 × float64`) + 24 B gyro (`3 × float64`) + 8 B seq/pad. Typical raw IMU is tens of bytes. Full `sensor_msgs/Imu` with three 9-element covariance matrices is ~216 B of covariances alone (often static) and sits **outside** the 32–128 B IMU-ish window. 64 B is inside that window and matches the existing default bench size. |
| Gap | **5 ms** | Target **200 Hz**. Consumer IMU is often 100 Hz (10 ms); robotics / Unitree-class streams are commonly 200–500 Hz. 200 Hz is the upper half of the requested 100–200+ Hz band. |
| Pacing | closed-loop + min gap | Next ping waits for pong **or** the 5 ms gap, whichever is later. If RTT > 5 ms, effective rate is **1/RTT**. |
| Samples | 400 + 40 warmup | Same order as the default ping-pong suite so p99 is not a 80-sample toy. Timeout 1 s (loss proxy; RTT should be ≪ 1 s). |
| Chain A msg | `std_msgs/UInt8MultiArray` | Same contiguous uint8 path as the large-packet suite. Humble `ByteMultiArray` (one Python `bytes` per octet) would dominate 64 B RTT. |

## SHM size thresholds vs payload sizes (accepted iter5)

Kept on `main` (PR #10): additive user SHM `maxMessageSize=280000`, `segment_size=2 MiB`; builtin UDP+SHM; iter2 2 MiB sockets; iter3/4 `send_buffers` 32 / `dynamic=false`. Exclusive / oversized SHM stays discarded.

| Payload | Bytes | vs user SHM `maxMessageSize` 280000 | vs builtin SHM `maxMessageSize` 65500 | vs user `segment_size` 2 MiB |
|---------|------:|--------------------------------------|----------------------------------------|------------------------------|
| IMU (this suite) | 64 | **≪ 280000** — one SHM message | **≪ 65500** — also one builtin message | fits easily |
| Mid-size 100 KiB | 102400 | **< 280000** — one mid-size SHM message | **> 65500** — fragmented on builtin | fits |
| Mid-size 256 KiB | 262144 | **< 280000** — one mid-size SHM message | **> 65500** — fragmented on builtin | fits |
| Large 1 MiB | 1048576 | **> 280000** — **not** one user-SHM message; stays on builtin fragment path | **> 65500** | fragments may still use the 2 MiB segment |

**Discarded (do not revive in this iter):**

- iter3 exclusive / unfragmented 1 MiB SHM (`maxMessageSize` 2 MiB / `segment_size` 4 MiB) — same-host 1 MiB p50 ~+36%
- iter5 exclusive UDP+SHM `segment_size=768 KiB` — BestEffort 1 MiB 80/80 → 1/80
- iter5 UDP-only / no SHM — BestEffort 1 MiB 0/90

This baseline does **not** change those knobs. Step B must be exactly one HF-focused change and must not erase 1 MiB / mid-size gains without documenting the tradeoff.

## What this is not

- Not Feishu-field / real-robot / cross-host proof
- Not a Chain A vs Chain B table (Chain B was not run)
- Not 《3》90%/LLM, 《4》Mac/preprod, 《5》Promptfoo, 《6》CVE
- same-process is labeled and recorded; **do not** treat it as the primary if same-host HF is the bottleneck
