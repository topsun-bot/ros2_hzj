# Environment — A / `same-process`

- **STATUS:** `blocked`
- **blocked reason:** missing: python3-rclpy / ROS 2 rclpy,ros2 CLI, /opt/ros/humble/setup.bash (host is not Humble; see docker/ros/)
- **UTC:** `2026-09-10T16:36:31Z`
- **Topology (required label):** `same-process`
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
- **CYCLONEDDS_HOME:** `/opt/cyclonedds`
- **CYCLONEDDS_URI:** `(unset)`
- **cyclonedds C:** `idlc (Eclipse Cyclone DDS) 0.10.4`
- **cyclonedds Python:** `11.0.1`
- **pytest:** `9.1.1`
- **numpy:** `2.4.4`
- **pydantic:** `2.13.5`
- **rclpy:** `not-installed`
- **git SHA ros2_hzj:** `3038db79ea40bd26637bb9656dd4bc0c14f1ba7c`
- **DimOS deps source:** `not used (ROS missing)`
- **DimOS tree:** `(none)`
- **DimOS git SHA:** `(n/a)`
- **which docker:** `(not on PATH)`
- **which ros2:** `(not on PATH)`

## Notes

STATUS: blocked on this VM.

Exact missing deps:
 - python3-rclpy / ROS 2 rclpy
 - ros2 CLI
 -  /opt/ros/humble/setup.bash (host is not Humble; see docker/ros/)

Host OS: Ubuntu 24.04.4 LTS
ROS Humble apt packages target Ubuntu 22.04; this host may be newer.

Operator recipe (do not invent numbers here):
  ./scripts/bench/docker_chain_a.sh

That builds `docker/ros/` (Humble; no RMW/domain ENV in the image — same as DimOS)
then sources `config/env/chain_a.sh` (RMW=rmw_fastrtps_cpp, ROS_DOMAIN_ID=42)
and runs the ROS pytest filter + pingpong.

In-tree pytest command that would run if rclpy existed:

  source /opt/ros/humble/setup.bash
  source config/env/chain_a.sh
  export PYTHONPATH="${PWD}/dimos_bridge:${PYTHONPATH:-}"
  pytest dimos_bridge/dimos/protocol/pubsub/benchmark/test_benchmark.py -m tool -k 'ros or RawROS or DimosROS' -v

Do not compare any future Chain A table with Chain B.

These facts describe the measurement environment. They are **not** a
root-cause analysis. Do not mix Chain A and Chain B in one table.
