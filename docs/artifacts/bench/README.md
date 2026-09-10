# DDS bench artifacts

UTC 日期子目录各放一次基线。链 A 与链 B **分目录**；`same-process` / `same-host` / `cross-host-UDP` **分目录**。

| UTC 日期 | 说明 |
|----------|------|
| [`2026-09-10/`](2026-09-10/README.md) | cursor-cloud-vm：链 B `same-process` + `same-host` 有真实 p50/p95/p99；链 A 与 `cross-host-UDP` 为 `STATUS: blocked` |

生成方式见 [`scripts/bench/README.md`](../../../scripts/bench/README.md) 与 [`docs/usage/benchmark-dds.md`](../../usage/benchmark-dds.md)。

本目录只收测量记录。没有数字时必须写 `STATUS: blocked` 和缺什么，禁止填假分位数。
