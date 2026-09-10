# Large-packet baseline notes (iter2 Step A)

中文 / English. This directory is a **baseline**. No Fast-DDS / Cyclone / sysctl knob was applied.

## 这不是什么 / What this is not

- **不是** 飞书现场丢包或卡顿的根因证明。
- **不是** 实机雷达 / 机械臂 / 跨机 UDP 证据。cross-host 在本单机 VM 上仍是 `STATUS: blocked`。
- **不是** 链 A 与链 B 的对照表。两套栈分目录、分表，禁止合成「谁更快」。
- **不是** 64 B–64 KiB 默认 bench 的续跑；默认尺寸仍在 `docs/artifacts/bench/2026-09-10/`。

This does **not** prove a Feishu-field, real-robot, or cross-host root cause. Same-process / same-host localhost is not that scene.

## Why these sizes and this rate

- 100 KiB / 256 KiB / 1 MiB sit toward image / lidar / large-message scale (not 64 B).
- 100 ms gap ≈ 10 Hz lidar-ish. The harness is still closed-loop ping-pong: if RTT exceeds 100 ms, the next publish waits for the pong (effective Hz = 1/RTT).
- Memory on this VM is 15 GiB. 1 MiB did **not** OOM. The largest size that completed with samples is **1048576 B** (same-process both chains; same-host reliable both chains).

## 1 MiB best-effort same-host timeouts

Both chains recorded **90 timeouts / 0 samples** for 1 MiB `high_throughput` (BestEffort / KeepLast 1) on `same-host`. Reliable 1 MiB on the same topology recorded 80/80 samples (Chain A p50 ≈ 47 ms; Chain B p50 ≈ 271 ms). That is documented, not filled in. It is a same-host localhost observation, not a Feishu / robot claim.

## Image / stack

- Chain A: `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (Humble `rmw_fastrtps_cpp`, domain 42, `config/fastdds.xml` as after iter1 historyQos). Ping-pong only needs rclpy; this is not the 6.7 GB Nav2 `docker/ros` image from 2026-09-10 / iter1.
- Chain B: host Ubuntu 24.04 + apt Cyclone 0.10.4 + Python `cyclonedds` 11.0.1; DimOS `/tmp/topsun_dimos` @ `a5259958db23c8ea6648544ed138eab19726ce93`. `same-host` = two processes, no RouDi ⇒ **localhost UDP, not SHM**.
