# Environment — Jazzy ROS 2 baseline

- **STATUS:** `blocked`
- **blocked reason:** cross-host orchestration is not implemented: it requires remote startup, a coordinated measurement window and result collection. Independent worker starts do not constitute a cross-host baseline.
- **not_final_baseline:** `True`
- **UTC:** `2026-10-11T11:30:51Z`
- **hostname / class:** `updates-MacBook-Pro-7.local` / `unknown`
- **OS:** `Darwin` (`macOS-26.5.2-arm64-arm-64bit`)
- **kernel:** `25.5.0`
- **CPU:** `arm` × 16 logical
- **MemTotal:** `unknown`
- **Python:** `3.9.6`
- **ROS_DISTRO:** `(unset)`
- **which ros2:** `(not on PATH)`
- **RMW_IMPLEMENTATION (env):** `(unset)`
- **ROS_DOMAIN_ID:** `(unset)`
- **FASTRTPS_DEFAULT_PROFILES_FILE:** `(unset — stock Jazzy)`
- **CYCLONEDDS_URI:** `(unset — stock Jazzy)`
- **ROS_LOCALHOST_ONLY:** `(unset)`
- **ROS_AUTOMATIC_DISCOVERY_RANGE:** `(unset; default same-host workers use LOCALHOST)`
- **dpkg rmw_fastrtps_cpp:** `not-installed`
- **dpkg rmw_cyclonedds_cpp:** `not-installed`
- **dpkg rclpy:** `not-installed`
- **dpkg fastdds:** `not-installed`
- **dpkg cyclonedds:** `not-installed`
- **git SHA ros2_hzj:** `faadb365f2211ed9d007d803b72d6fa6e445cd22`

## Notes

Cloud / lab measurement only. Not the final 10× denominator until repeated on the target robot or HIL host.

Stock Jazzy RMW defaults. This harness does **not** `source`
`config/env/chain_a.sh` and does **not** point at `config/fastdds.xml`.
Those are the Humble dual-chain contract, not the 10× denominator.

Do not paste these numbers into `docs/artifacts/bench/SCOREBOARD.md`.
