# 2026-09-11-cross-host — Chain A Fast-DDS UDP baseline

**STATUS: blocked.** This cloud VM is a single `cursor` / `cursor-cloud-vm` host.
There is no second machine, no second ROS 2 endpoint, and no measured p50 / p95 / p99.

**不要填假分位数。Do not invent numbers.**

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof. Not a real-robot claim.
Even a future two-host run of this recipe is **still** not Feishu field proof.

《3》90%/LLM scoring, 《4》Mac/preprod, 《5》Promptfoo, 《6》CVE audit — still **Hold**.

## Why blocked

| check | result |
|-------|--------|
| Second physical / VM host | **missing** (`CROSS_HOST_PEER` unset, `ROLE` unset) |
| Hostname | `cursor` (one host) |
| ROS 2 Humble / `rclpy` on this host | not required for the blocked recording; live two-host needs it on **both** |
| `config/fastdds.xml` | **unchanged** (iter7 seed) |
| SCOREBOARD current best / iter7 claims | **unchanged** (pointer only) |

Two Docker containers on this same VM would still be **same-host** (or localhost UDP), not `cross-host-UDP`. This directory does not treat that as a two-machine baseline.

## Recipe (two real hosts)

Exact commands: [`scripts/bench/run_cross_host_a.sh`](../../../../scripts/bench/run_cross_host_a.sh) and [`scripts/bench/README.md`](../../../../scripts/bench/README.md).

- Host B (responder / echo) first, then host A (client / pub).
- Both: `source config/env/chain_a.sh` → `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`, `FASTRTPS_DEFAULT_PROFILES_FILE` → existing [`config/fastdds.xml`](../../../../config/fastdds.xml).
- One QoS per invocation. Do **not** mix Chain A and Chain B in one table.

## Files in this directory

| file | meaning |
|------|---------|
| [`summary.md`](summary.md) | p50 / p95 / p99 table empty; STATUS blocked |
| [`raw.json`](raw.json) | machine-readable blocked payload (no samples) |
| [`environment.md`](environment.md) | this host + missing peer |
| [`BLOCKED.txt`](BLOCKED.txt) | one-line blocked marker |

Recorded by:

```bash
BENCH_DATE=2026-09-11-cross-host ./scripts/bench/run_cross_host_a.sh
```

## What this is not

- Not Feishu field proof. 不是飞书现场丢包、卡顿、或实机根因。
- Not a booked SCOREBOARD table. Same-host best numbers stay on [`../SCOREBOARD.md`](../SCOREBOARD.md).
- Not a Chain A vs Chain B comparison.
- Not a `fastdds.xml` knob. No new transport / discovery / QoS XML.
