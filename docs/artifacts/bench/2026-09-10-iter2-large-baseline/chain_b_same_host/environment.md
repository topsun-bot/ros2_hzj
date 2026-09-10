# Environment — B / `same-host`

- **STATUS:** `ok`
- **UTC:** `2026-09-10T18:42:21Z`
- **Topology (required label):** `same-host`
- **Chain:** `B`
- **hostname:** `cursor`
- **hostname class:** `cursor-cloud-vm`
- **OS:** `Linux-6.12.94+-x86_64-with-glibc2.39` / `Ubuntu 24.04.4 LTS`
- **CPU:** `Intel(R) Xeon(R) Processor` × 4 logical
- **Python:** `3.12.3` (`/usr/bin/python3`)
- **ROS_DISTRO:** `(unset)`
- **RMW_IMPLEMENTATION:** `(unset)`
- **ROS_DOMAIN_ID:** `0`
- **FASTRTPS_DEFAULT_PROFILES_FILE:** `(unset)`
- **CYCLONEDDS_HOME:** `/opt/cyclonedds`
- **CYCLONEDDS_URI:** `(unset)`
- **cyclonedds C:** `idlc (Eclipse Cyclone DDS) 0.10.4`
- **cyclonedds Python:** `11.0.1`
- **pytest:** `9.1.1`
- **numpy:** `2.4.4`
- **pydantic:** `2.13.5`
- **rclpy:** `not-installed`
- **git SHA ros2_hzj:** `280c98d08948e5d519aa42d945e16b80172da620`
- **DimOS deps source:** `temporary topsun_dimos checkout`
- **DimOS tree:** `/tmp/topsun_dimos`
- **DimOS git SHA:** `a5259958db23c8ea6648544ed138eab19726ce93`
- **which docker:** `/usr/bin/docker`
- **which ros2:** `(not on PATH)`

## Notes

Chain B native Cyclone DDS (ddspubsub.DDS), DDSConfig.domain_id default 0.
Did not source config/env/chain_a.sh.
in-tree dimos_bridge pytest exit=0; checkout pytest exit=0.
Pytest harness = throughput + drain-after-publish, NOT per-message percentiles.
Percentiles come only from scripts/bench/pingpong.py.
BENCH_SIZES=102400,262144,1048576. BENCH_INTERVAL_MS=100.
same-host without RouDi is localhost UDP, not SHM.
DimOS source: temporary topsun_dimos checkout @ a5259958db23c8ea6648544ed138eab19726ce93
Pinned copy SHA in dimos_bridge/SOURCE.md: a5259958db23c8ea6648544ed138eab19726ce93
Not real-robot / Feishu-field / cross-host proof.

These facts describe the measurement environment. They are **not** a
root-cause analysis. Do not mix Chain A and Chain B in one table.
