# Environment — A / `same-process`

- **STATUS:** `ok` (ping-pong percentiles; official ROS pytest collection failed on Image stub)
- **UTC:** `2026-09-10T17:54:16Z`
- **Topology (required label):** `same-process`
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
- **git SHA ros2_hzj:** `a9cc1fc1f4090c511751979153738e668d3e702c`
- **DimOS deps source:** `unknown`
- **DimOS tree:** `(none)`
- **DimOS git SHA:** `(n/a)`
- **which docker:** `(not on PATH inside the container)`
- **which ros2:** `/opt/ros/humble/bin/ros2`
- **image:** `ros2_hzj/ros:humble` (`6f08fd8ce67c`, ~6.68GB) built from `docker/ros/Dockerfile` (Humble + Nav2; **no** RMW/domain ENV baked in)

## Notes

Sourced `config/env/chain_a.sh` at runtime (RMW=`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`, `FASTRTPS_DEFAULT_PROFILES_FILE=/work/config/fastdds.xml`).
ROS setup=`/opt/ros/humble/setup.bash`. pytest exit=2 (dimos_bridge `Image` stub). pingpong exit=0.
iter1: Humble Fast-DDS XMLPARSER **accepted** `config/fastdds.xml` (no `Invalid element ... Name: history`, no `Error parsing` in ping-pong stdout). History lives under `<topic><historyQos>`. Domain 42 still comes from `ROS_DOMAIN_ID`. Do not invent SHM. Do not compare with Chain B.

These facts describe the measurement environment. They are **not** a
root-cause analysis. Do not mix Chain A and Chain B in one table.
