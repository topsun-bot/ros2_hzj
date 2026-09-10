# DDS bench artifacts

UTC 日期子目录各放一次基线。链 A 与链 B **分目录**；`same-process` / `same-host` / `cross-host-UDP` **分目录**。

| UTC 日期 | 说明 |
|----------|------|
| [`2026-09-10/`](2026-09-10/README.md) | cursor-cloud-vm：链 B `same-process` + `same-host` 有真实 p50/p95/p99；链 A `same-process` + `same-host` 在 Humble `docker/ros` 内有真实 p50/p95/p99；两条链的 `cross-host-UDP` 均为 `STATUS: blocked`（单机） |
| [`2026-09-10-iter1/`](2026-09-10-iter1/README.md) | iter1：只改 `config/fastdds.xml`（Humble-valid `<historyQos>`）。重测链 A `same-process` + `same-host`；[`delta.md`](2026-09-10-iter1/delta.md) 只对照 2026-09-10 同链同拓扑。链 B 未重跑。 |

生成方式见 [`scripts/bench/README.md`](../../../scripts/bench/README.md) 与 [`docs/usage/benchmark-dds.md`](../../usage/benchmark-dds.md)。

本目录只收测量记录。没有数字时必须写 `STATUS: blocked` 和缺什么，禁止填假分位数。
