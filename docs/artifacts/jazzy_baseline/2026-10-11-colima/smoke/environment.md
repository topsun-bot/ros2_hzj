# Environment — Jazzy ROS 2 baseline

- **STATUS:** `ok`
- **not_final_baseline:** `True`
- **UTC:** `2026-10-11T09:18:37Z`
- **hostname / class:** `colima` / `colima-local-vm`
- **OS:** `Ubuntu 24.04.4 LTS` (`Linux-6.8.0-117-generic-aarch64-with-glibc2.39`)
- **kernel:** `6.8.0-117-generic`
- **CPU:** `aarch64` × 4 logical
- **MemTotal:** `8112464 kB`
- **Python:** `3.12.3`
- **ROS_DISTRO:** `jazzy`
- **which ros2:** `/opt/ros/jazzy/bin/ros2`
- **RMW_IMPLEMENTATION (env):** `(unset)`
- **ROS_DOMAIN_ID:** `(unset)`
- **FASTRTPS_DEFAULT_PROFILES_FILE:** `(unset — stock Jazzy)`
- **CYCLONEDDS_URI:** `(unset — stock Jazzy)`
- **ROS_LOCALHOST_ONLY:** `(unset)`
- **ROS_AUTOMATIC_DISCOVERY_RANGE:** `SUBNET`
- **dpkg rmw_fastrtps_cpp:** `8.4.4-1noble.20260902.140744`
- **dpkg rmw_cyclonedds_cpp:** `2.2.4-1noble.20260902.140937`
- **dpkg rclpy:** `7.1.12-1noble.20260902.143245`
- **dpkg fastdds:** `not-installed`
- **dpkg cyclonedds:** `0.10.5-1noble.20260305.204044`
- **git SHA ros2_hzj:** `1a65153213e4c556b7326cf627f6a8bb59d018df`

## Notes

Cloud / lab measurement only. Not the final 10× denominator until repeated on the target robot or HIL host.

Stock Jazzy RMW defaults. This harness does **not** `source`
`config/env/chain_a.sh` and does **not** point at `config/fastdds.xml`.
Those are the Humble dual-chain contract, not the 10× denominator.

Do not paste these numbers into `docs/artifacts/bench/SCOREBOARD.md`.
