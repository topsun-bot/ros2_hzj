# Environment — A / `same-host`

- **STATUS:** `ok` (ping-pong percentiles; official ROS pytest collection failed on Image stub)
- **UTC:** `2026-09-10T17:25:08Z`
- **Topology (required label):** `same-host`
- **Chain:** `A`
- **hostname:** `cursor`
- **hostname class:** `cursor-cloud-vm`
- **OS:** `Linux-6.12.94+-x86_64-with-glibc2.35` / `Ubuntu 22.04.5 LTS`
- **CPU:** `Intel(R) Xeon(R) Processor` × 4 logical
- **Python:** `3.10.12` (`/usr/bin/python3`)
- **ROS_DISTRO:** `humble`
- **RMW_IMPLEMENTATION:** `rmw_fastrtps_cpp`
- **ROS_DOMAIN_ID:** `42`
- **FASTRTPS_DEFAULT_PROFILES_FILE:** `/work/config/fastdds.xml`
- **CYCLONEDDS_HOME:** `(unset)`
- **CYCLONEDDS_URI:** `(unset)`
- **cyclonedds C:** `unknown`
- **cyclonedds Python:** `not-installed`
- **pytest:** `6.2.5`
- **numpy:** `1.21.5`
- **pydantic:** `not-installed`
- **rclpy:** `3.3.21`
- **git SHA ros2_hzj:** `0f73f9fa5b3af1c3c8ef57b6e73d436155f3cfc4` (bench scripts at measurement time; container `git rev-parse` was unknown because root vs host-owned `.git`)
- **DimOS deps source:** `not required for Chain A ping-pong (rclpy ByteMultiArray)`
- **DimOS tree:** `(none)`
- **DimOS git SHA:** `(n/a)`
- **which docker:** `(not on PATH inside the container)`
- **which ros2:** `/opt/ros/humble/bin/ros2`
- **image:** `ros2_hzj/ros:humble` (`52073a8a245f`, ~6.68GB) built from `docker/ros/Dockerfile` (Humble + Nav2; **no** RMW/domain ENV baked in)

## Notes

Two OS processes (`--role responder` + client) on one VM, `--net=host --ipc=host`.
Sourced `config/env/chain_a.sh` at runtime (RMW=`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`).
Fast-DDS default transports (XML does not force UDP-only or SHM-only). **Do not label this SHM.**
Humble Fast-DDS XMLPARSER rejects `<history>` in writer/reader QoS of the contract seed; file unchanged.
pytest exit=2 (dimos_bridge `Image` stub). pingpong exit=0. Do not compare with Chain B.

These facts describe the measurement environment. They are **not** a
root-cause analysis. Do not mix Chain A and Chain B in one table.
