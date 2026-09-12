# DDS latency baseline runners

These scripts record **Chain A** (ROS 2 / Fast-DDS, domain 42) and **Chain B**
(Cyclone `DDS`, domain 0) measurements. They do **not** change DimOS copied
modules, vendor trees, QoS defaults, or domains.

Do **not** put Chain A and Chain B numbers in one comparison table.
Do **not** treat these numbers as a root-cause claim.

## Exact commands

### Chain B (Cyclone `DDS` / domain 0)

Do **not** `source config/env/chain_a.sh`. Native DimOS DDS does not read RMW.

```bash
# From repository root. Optional: source config/env/chain_b.sh
# (only affects same-host ROS 2 clients; native DDS still uses DDSConfig.domain_id=0)

# Official upstream pytest filter (see docs/usage/benchmark-dds.md):
#   pytest -m tool -k dds
./scripts/bench/run_chain_b.sh
```

That wrapper:

1. Tries in-tree `dimos_bridge` (often blocked by ImportError stubs).
2. Falls back to a **read-only** `topsun_dimos` checkout (`TOPSUN_DIMOS` or
   `/tmp/topsun_dimos`) at the SHA in `dimos_bridge/SOURCE.md`.
3. Runs `pytest -m tool -k dds` (overrides DimOS default `addopts` that exclude `tool`).
4. Runs `pingpong.py` for per-message RTT p50 / p95 / p99 (the pytest harness
   is a throughput / drain-time bench, not per-message percentiles).

Host pip extras for the checkout pytest path:
`python3 -m pip install --user -r scripts/bench/requirements-chain-b.txt`
(also installed automatically by `run_chain_b.sh` unless `BENCH_SKIP_PIP=1`).

### Chain A (ROS 2 Fast-DDS / domain 42)

```bash
source /opt/ros/humble/setup.bash   # if Humble is on the host
source config/env/chain_a.sh        # RMW=rmw_fastrtps_cpp, domain 42
./scripts/bench/run_chain_a.sh
```

If Humble / `rclpy` is missing, the script writes `STATUS: blocked` under
`docs/artifacts/bench/<UTC-date>/chain_a_*` and prints the Docker recipe:

```bash
# Builds docker/ros/ (Humble; no RMW/domain ENV in the image) unless
# CHAIN_A_IMAGE already exists. Sources config/env/chain_a.sh at runtime.
# Default topologies: same-process then same-host; cross-host-UDP is
# recorded as blocked on a single VM.
./scripts/bench/docker_chain_a.sh
# optional: CHAIN_A_TOPOLOGIES=same-process ./scripts/bench/docker_chain_a.sh
```

## Topology labels (required, pick exactly one per run)

| Label | Meaning |
|-------|---------|
| `same-process` | Publisher and subscriber in one process |
| `same-host` | Two processes on one machine. Label the transport you actually used (Chain B without RouDi = localhost UDP, **not** SHM; Chain A = Fast-DDS defaults — do not invent SHM) |
| `cross-host-UDP` | Two machines over UDP |

Keep SHM vs UDP vs same-process in **separate** files/tables.

## Artifacts

Each successful (or blocked) run writes:

- `summary.md` — p50 / p95 / p99 (or blocked reason)
- `raw.json` — machine-readable samples / pytest pointers
- `environment.md` — OS, CPU, hostname class, RMW, domain, versions, git SHA,
  whether DimOS came from vendored `dimos_bridge` or a temporary checkout

See [docs/usage/benchmark-dds.md](../../docs/usage/benchmark-dds.md).
Current best config + booked same-host tables (no new knob):
[docs/artifacts/bench/SCOREBOARD.md](../../docs/artifacts/bench/SCOREBOARD.md).
Those numbers are **not** Feishu field proof.

## Large-packet cases (iter2 / iter3 / iter4 / iter5)

Default sizes stay `64,1024,16384,65536`. Feishu / lidar-ish cases are **opt-in**:

```bash
# Exact payload lengths (bytes): 102400 (100 KiB), 262144 (256 KiB), 1048576 (1 MiB)
# Inter-message gap: 100 ms (target 10 Hz). If RTT > 100 ms, effective rate is 1/RTT.
# Chain A uses std_msgs/UInt8MultiArray (contiguous uint8). Humble ByteMultiArray
# (one Python bytes per octet) is not viable at ≥100KiB.
BENCH_DATE=2026-09-10-iter2-large-baseline \
  LARGE_PACKET_CHAINS='A B' \
  ./scripts/bench/run_large_packet.sh

# iter3 remasure (Chain A only; like-to-like vs iter2-after):
BENCH_DATE=2026-09-10-iter3 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A \
  ./scripts/bench/run_large_packet.sh

# iter4 remasure (Chain A only; like-to-like vs iter3, honesty vs iter2-after):
BENCH_DATE=2026-09-10-iter4 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A \
  ./scripts/bench/run_large_packet.sh

# iter5 remasure (Chain A only; like-to-like vs iter4, honesty vs iter2-after):
BENCH_DATE=2026-09-10-iter5 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  LARGE_PACKET_CHAINS=A \
  ./scripts/bench/run_large_packet.sh
```

That wrapper sets `BENCH_SIZES`, `BENCH_INTERVAL_MS=100`, `BENCH_SAMPLES=80`,
`BENCH_WARMUP=10`, `BENCH_TIMEOUT=8`, `BENCH_ROS_MSG=uint8_multiarray`,
`BENCH_SKIP_PYTEST=1`. Chain A runs in `osrf/ros:humble-desktop` unless
`CHAIN_A_IMAGE` is set. Chain B `same-host` is localhost UDP (no RouDi), **not** SHM.

## High-frequency IMU-scale cases (iter6)

Small-packet HF cases are **opt-in** and stay in their own date dirs (do **not**
mix with the 100 KiB–1 MiB lidar tables):

```bash
# Exact payload: 64 B compact 6-axis IMU (ts + accel xyz + gyro xyz + seq).
# Inter-message gap: 5 ms (target 200 Hz). If RTT > 5 ms, effective rate is 1/RTT.
# Chain A uses std_msgs/UInt8MultiArray (same contiguous path as large-packet).
BENCH_DATE=2026-09-10-iter6-imu-baseline \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh

# iter6 Step B remasure (Chain A only; like-to-like vs Step A):
BENCH_DATE=2026-09-10-iter6-after \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh

# iter7 remasure (Chain A only; like-to-like vs iter6-imu-baseline):
BENCH_DATE=2026-09-11-iter7 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh

# iter8 remasure (Chain A only; like-to-like vs iter7):
BENCH_DATE=2026-09-11-iter8 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh

# iter9 remasure (Chain A only; like-to-like vs iter7):
BENCH_DATE=2026-09-11-iter9 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh
```

That wrapper sets `BENCH_SIZES=64`, `BENCH_INTERVAL_MS=5`, `BENCH_SAMPLES=400`,
`BENCH_WARMUP=40`, `BENCH_TIMEOUT=1`, `BENCH_ROS_MSG=uint8_multiarray`,
`BENCH_SCALE_LABEL=IMU-ish`, `BENCH_SKIP_PYTEST=1`. Chain A
`same-process` + `same-host` at minimum. Chain B is optional (`IMU_HF_CHAINS='A B'`)
and must stay in **separate** tables.

Documented in each `raw.json` / `summary.md`: exact payload length, gap/Hz,
topology label, chain, timeouts/loss, **and jitter** (RTT p95/p99 +
inter-message interval variance / `|I − gap|`). Do **not** claim success from
p50/mean alone. **Never** one mixed A-vs-B table. Cross-host UDP stays blocked
on a single VM. These numbers are **not** real-robot or Feishu-field proof.

`pingpong.py` flags: `--sizes`, `--interval-ms`, `--timeout`, `--warmup`, `--samples`,
`--ros-msg uint8_multiarray`.

## Cross-host UDP (Chain A Fast-DDS / domain 42)

Two **real** machines. Same-host / two-container-on-one-VM is **not** this topology.
This cloud VM records **STATUS: blocked** — see
[docs/artifacts/bench/2026-09-11-cross-host/](../../docs/artifacts/bench/2026-09-11-cross-host/README.md).
**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

Do **not** change [`config/fastdds.xml`](../../config/fastdds.xml). Point
`FASTRTPS_DEFAULT_PROFILES_FILE` at the existing iter7 seed. One QoS per
invocation (the responder binds that QoS and a shared `--topic-prefix`).
Do **not** put these numbers in a table with Chain B or with `same-process` /
`same-host`.

### Network prerequisites

- Both hosts on the same L2, or L3 with **multicast** reachability. This recipe
  does **not** add `initialPeersList` (no new XML knobs). If multicast is
  blocked, discovery will fail with the current seed.
- Firewall: UDP both ways. Humble Fast-DDS SIMPLE discovery, `portBase=7400`,
  `domainIDGain=250`, domain **42**:
  - multicast metatraffic `7400 + 250*42 + 0` = **17900**
  - unicast metatraffic `7400 + 250*42 + 10` = **17910**
  - unicast user `7400 + 250*42 + 11` = **17911**
  Allow at least that set (often `7400–19000/udp`). Multicast group `239.255.0.1`.
- Same `ROS_DOMAIN_ID=42` on both. Domain 0 (Chain B) will not discover this run.
- Ping / ICMP is optional; DDS uses UDP.

### Env (both hosts)

```bash
source /opt/ros/humble/setup.bash
source config/env/chain_a.sh
# RMW_IMPLEMENTATION=rmw_fastrtps_cpp
# ROS_DOMAIN_ID=42
# FASTRTPS_DEFAULT_PROFILES_FILE=<repo>/config/fastdds.xml
```

R0 freeze: Chain A domain **42**. Bench QoS names match `testdata.py`
(`high_throughput` = BestEffort/KeepLast(1)/Volatile; `reliable` =
Reliable/KeepLast(5000)/Volatile). That is **not** nav-path freeze QoS.

### Exact commands

```bash
# Host B — responder / echo. Start first; leave running.
source /opt/ros/humble/setup.bash
source config/env/chain_a.sh
ROLE=responder QOS=high_throughput \
  BENCH_TOPIC_PREFIX=hzj_cross_host \
  ./scripts/bench/run_cross_host_a.sh

# Host A — client / pub. Writes p50/p95/p99 under
# docs/artifacts/bench/<UTC-date>-cross-host/
source /opt/ros/humble/setup.bash
source config/env/chain_a.sh
ROLE=client CROSS_HOST_PEER=<host-B-hostname-or-ip> \
  QOS=high_throughput BENCH_TOPIC_PREFIX=hzj_cross_host \
  BENCH_DATE=$(date -u +%Y-%m-%d)-cross-host \
  ./scripts/bench/run_cross_host_a.sh

# Repeat both sides with QOS=reliable (separate invocation; same artifact
# dir will overwrite — use a suffix in BENCH_DATE if you need both).

# Single VM / no peer: record blocked (no fake numbers)
./scripts/bench/run_cross_host_a.sh
```

Equivalent `pingpong.py` (same env as above):

```bash
# Host B
python3 scripts/bench/pingpong.py --chain A --topology cross-host-UDP \
  --role responder --qos high_throughput --topic-prefix hzj_cross_host

# Host A
python3 scripts/bench/pingpong.py --chain A --topology cross-host-UDP \
  --role client --remote-peer <host-B> --qos high_throughput \
  --topic-prefix hzj_cross_host --discover-s 5 \
  --out docs/artifacts/bench/<UTC-date>-cross-host/raw.json
```

Without `--remote-peer`, `pingpong.py --topology cross-host-UDP` still writes
**blocked** so `run_chain_a.sh` / `docker_chain_a.sh` do not invent numbers.

### Artifacts

Under `docs/artifacts/bench/<UTC-date>-cross-host/`:

- `summary.md` — p50 / p95 / p99 (or blocked)
- `raw.json` — samples
- `environment.md` — **both** hosts (client/pub + responder/echo)

### Chain B (documented only; not run in this gate)

Same `pingpong.py` roles with `--chain B` and `source config/env/chain_b.sh`
(Cyclone domain **0**, do **not** source `chain_a.sh`). No `run_cross_host_b.sh`
in this PR. If you ever measure B, keep it in a **separate** directory and
**never** one A-vs-B table. This gate is Chain A Fast-DDS preferred.
