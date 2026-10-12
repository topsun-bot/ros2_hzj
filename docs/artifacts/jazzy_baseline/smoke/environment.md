# Environment — Jazzy ROS 2 baseline

- **STATUS:** `ok`
- **not_final_baseline:** `True`
- **UTC:** `2026-10-11T08:53:02Z`
- **hostname / class:** `cursor` / `cursor-cloud-vm`
- **OS:** `Ubuntu 24.04.4 LTS` (`Linux-6.12.94+-x86_64-with-glibc2.39`)
- **kernel:** `6.12.94+`
- **CPU:** `Intel(R) Xeon(R) Processor` × 4 logical
- **MemTotal:** `16398384 kB`
- **Python:** `3.12.3`
- **ROS_DISTRO:** `jazzy`
- **which ros2:** `(not on PATH)`
- **RMW_IMPLEMENTATION (env):** `(unset)`
- **ROS_DOMAIN_ID:** `(unset)`
- **FASTRTPS_DEFAULT_PROFILES_FILE:** `(unset — stock Jazzy)`
- **CYCLONEDDS_URI:** `(unset — stock Jazzy)`
- **ROS_LOCALHOST_ONLY:** `(unset)`
- **ROS_AUTOMATIC_DISCOVERY_RANGE:** `SUBNET`
- **dpkg rmw_fastrtps_cpp:** `8.4.4-1noble.20260911.100940`
- **dpkg rmw_cyclonedds_cpp:** `2.2.4-1noble.20260911.095700`
- **dpkg rclpy:** `7.1.12-1noble.20260912.162354`
- **dpkg fastdds:** `not-installed`
- **dpkg cyclonedds:** `0.10.5-1noble.20260225.142613`
- **git SHA ros2_hzj:** `ca08e716f56a574767b94e010cc16a638658071e`

## Notes

Cloud / lab measurement only. Not the final 10× denominator until repeated on the target robot or HIL host.

Stock Jazzy RMW defaults. This harness does **not** `source`
`config/env/chain_a.sh` and does **not** point at `config/fastdds.xml`.
Those are the Humble dual-chain contract, not the 10× denominator.

Do not paste these numbers into `docs/artifacts/bench/SCOREBOARD.md`.
