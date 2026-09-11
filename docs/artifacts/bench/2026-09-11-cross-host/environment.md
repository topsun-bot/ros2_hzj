# Environment — A / `cross-host-UDP`

- **STATUS:** `blocked`
- **blocked reason:** cross-host-UDP needs a second machine; this runner is single-host (ROLE unset, CROSS_HOST_PEER='')
- **UTC:** `2026-09-11T10:04:32Z`
- **Topology (required label):** `cross-host-UDP`
- **Chain:** `A`
- **hostname:** `cursor`
- **hostname class:** `cursor-cloud-vm`
- **OS:** `Linux-6.12.94+-x86_64-with-glibc2.39` / `Ubuntu 24.04.4 LTS`
- **CPU:** `Intel(R) Xeon(R) Processor` × 4 logical
- **Python:** `3.12.3` (`/usr/bin/python3`)
- **ROS_DISTRO:** `(unset)`
- **RMW_IMPLEMENTATION:** `rmw_fastrtps_cpp`
- **ROS_DOMAIN_ID:** `42`
- **FASTRTPS_DEFAULT_PROFILES_FILE:** `/workspace/config/fastdds.xml`
- **CYCLONEDDS_HOME:** `(unset)`
- **CYCLONEDDS_URI:** `(unset)`
- **cyclonedds C:** `unknown`
- **cyclonedds Python:** `not-installed`
- **pytest:** `not-installed`
- **numpy:** `2.4.4`
- **pydantic:** `not-installed`
- **rclpy:** `not-installed`
- **git SHA ros2_hzj:** `59a65a3b74db07ae1b0672753c93e74a1dae6d02`
- **DimOS deps source:** `not used (cross-host recipe; ping-pong only)`
- **DimOS tree:** `(none)`
- **DimOS git SHA:** `(n/a)`
- **which docker:** `(not on PATH)`
- **which ros2:** `(not on PATH)`

## Notes

Single-host (or incomplete two-host) environment. Cross-host UDP left **blocked**.
No fake p50/p95/p99. Do not compare with Chain B. Do not mix topologies.

Recipe: scripts/bench/run_cross_host_a.sh and scripts/bench/README.md.
XML: config/fastdds.xml is the iter7 seed — this runner does not edit it.

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.
《3》90%/LLM, 《4》Mac/preprod, 《5》Promptfoo, 《6》CVE — still Hold.

These facts describe the measurement environment. They are **not** a
root-cause analysis. Do not mix Chain A and Chain B in one table.

## Hosts (cross-host-UDP)

| role | identity | notes |
|------|----------|-------|
| client / pub (host A) | `cursor` | this process / single-host VM (client/pub role would live here) |
| responder / echo (host B) | `missing` | no second machine in this environment; CROSS_HOST_PEER unset or ROLE not client/responder |

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.
