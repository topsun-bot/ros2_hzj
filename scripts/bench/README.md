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
