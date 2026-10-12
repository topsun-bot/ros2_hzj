# Cloud VM smoke — **not** the 10× denominator

These files came from `python3 scripts/jazzy_baseline/run.py --smoke` on a
Cursor cloud agent VM (`host_class: cursor-cloud-vm`, Ubuntu 24.04 + native
Jazzy debs). Shared vCPU, no isolcpus, no robot NIC.

**Do not treat p50/p90/p99, msg/s, or RSS as the final baseline.**
Repeat on the target robot / HIL host with `--repeats 3` (or more) and the
full size × QoS matrix. Do not copy numbers into
[`docs/artifacts/bench/SCOREBOARD.md`](../bench/SCOREBOARD.md).

See [`scripts/jazzy_baseline/README.md`](../../../scripts/jazzy_baseline/README.md).
