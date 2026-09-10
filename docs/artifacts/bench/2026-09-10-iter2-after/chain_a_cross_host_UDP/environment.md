# Environment — A / `cross-host-UDP`

- **STATUS:** `blocked`
- **blocked reason:** cross-host-UDP needs a second machine; this runner is single-host
- **UTC:** `2026-09-10T18:46:10Z`
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
- **FASTRTPS_DEFAULT_PROFILES_FILE:** `(unset)`
- **CYCLONEDDS_HOME:** `/opt/cyclonedds`
- **CYCLONEDDS_URI:** `(unset)`
- **cyclonedds C:** `idlc (Eclipse Cyclone DDS) 0.10.4`
- **cyclonedds Python:** `11.0.1`
- **pytest:** `9.1.1`
- **numpy:** `2.4.4`
- **pydantic:** `2.13.5`
- **rclpy:** `not-installed`
- **git SHA ros2_hzj:** `58584a5badeb3fce150795552d58c93a7bf4c01c`
- **DimOS deps source:** `not used (single-host VM)`
- **DimOS tree:** `(none)`
- **DimOS git SHA:** `(n/a)`
- **which docker:** `/usr/bin/docker`
- **which ros2:** `(not on PATH)`

## Notes

Single cloud VM. Cross-host UDP left blocked. No fake percentiles. Do not compare with Chain B.

These facts describe the measurement environment. They are **not** a
root-cause analysis. Do not mix Chain A and Chain B in one table.
