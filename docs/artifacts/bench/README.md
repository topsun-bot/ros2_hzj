# DDS bench artifacts

UTC 日期子目录各放一次基线。链 A 与链 B **分目录**；`same-process` / `same-host` / `cross-host-UDP` **分目录**。

| UTC 日期 | 说明 |
|----------|------|
| [`2026-09-10/`](2026-09-10/README.md) | cursor-cloud-vm：链 B `same-process` + `same-host` 有真实 p50/p95/p99；链 A `same-process` + `same-host` 在 Humble `docker/ros` 内有真实 p50/p95/p99；两条链的 `cross-host-UDP` 均为 `STATUS: blocked`（单机） |
| [`2026-09-10-iter1/`](2026-09-10-iter1/README.md) | iter1：只改 `config/fastdds.xml`（Humble-valid `<historyQos>`）。重测链 A `same-process` + `same-host`；[`delta.md`](2026-09-10-iter1/delta.md) 只对照 2026-09-10 同链同拓扑。链 B 未重跑。 |
| [`2026-09-10-iter2-large-baseline/`](2026-09-10-iter2-large-baseline/README.md) | iter2 Step A：大包 100KiB / 256KiB / 1MiB，间隔 100 ms（目标 10 Hz）。链 A 与链 B **分表**。无 transport knob。**不是**飞书现场 / 实机 / 跨机证明。 |
| [`2026-09-10-iter2-after/`](2026-09-10-iter2-after/README.md) | iter2 Step B：只改默认 participant UDP socket buffer 2 MiB。重测链 A 大包同拓扑；[`delta.md`](2026-09-10-iter2-after/delta.md) 只对照 Step A 同链同尺寸。链 B 未重跑。 |
| [`2026-09-10-iter3/`](2026-09-10-iter3/README.md) | iter3：只改默认 participant send-buffer 池（32 / dynamic）。重测链 A 大包同拓扑；[`delta.md`](2026-09-10-iter3/delta.md) 只对照 iter2-after 同链同尺寸。same-host 1 MiB 为主；same-process 只作诚实对照。链 B 未重跑。 |
| [`2026-09-10-iter4/`](2026-09-10-iter4/README.md) | iter4：同一 send-buffer 池保持 32，`dynamic` 改为 false。重测链 A 大包同拓扑；[`delta.md`](2026-09-10-iter4/delta.md) 只对照 iter3 同链同尺寸（主表）；相对 iter2-after 的 mid-size 诚实对照写在 delta 里。same-host Reliable 100/256 KiB 为主；1 MiB 须留在 iter3 噪声内。链 B 未重跑。 |
| [`2026-09-10-iter5/`](2026-09-10-iter5/README.md) | iter5：additive 中包 SHM（`maxMessageSize` 280000 / `segment_size` 2 MiB），builtin UDP+SHM 保留。重测链 A 大包同拓扑；[`delta.md`](2026-09-10-iter5/delta.md) 主对照 iter4；mid-size 另对照 iter2-after。same-host BestEffort 256 KiB 为主；1 MiB 未回吐。链 B 未重跑。 |
| [`2026-09-10-iter6-imu-baseline/`](2026-09-10-iter6-imu-baseline/README.md) | iter6 Step A：先钉 IMU **64 B / 200 Hz**（5 ms）。主指标 **jitter**（RTT p95/p99 + 到达间隔），不是 p50。链 A `same-process` + `same-host` **分表**。无新 transport knob。**不是**飞书现场 / 实机 / 跨机证明。 |
| [`2026-09-10-iter6-after/`](2026-09-10-iter6-after/README.md) | iter6 Step B：探测 `shm_midsize` `port_queue_capacity` 64。重测链 A IMU 同拓扑；[`delta.md`](2026-09-10-iter6-after/delta.md) 只对照 Step A，**jitter 门**。same-host BestEffort p95/到达间隔 **变差，未保留**。1 MiB 赢面未擦。落地 XML 仍是 iter5 种子。链 B 未重跑。 |
| [`2026-09-11-iter7/`](2026-09-11-iter7/README.md) | iter7：只改 `shm_midsize` `healthy_check_timeout_ms` 10000。重测链 A IMU 同拓扑；[`delta.md`](2026-09-11-iter7/delta.md) 只对照 iter6-imu-baseline，**jitter 门**。same-host BestEffort p95/到达间隔 **收紧，保留**。1 MiB / 中包点检未回吐。链 B 未重跑。 |

生成方式见 [`scripts/bench/README.md`](../../../scripts/bench/README.md) 与 [`docs/usage/benchmark-dds.md`](../../usage/benchmark-dds.md)。

本目录只收测量记录。没有数字时必须写 `STATUS: blocked` 和缺什么，禁止填假分位数。
