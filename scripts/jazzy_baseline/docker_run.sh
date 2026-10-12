#!/usr/bin/env bash
# Run the Jazzy baseline harness inside osrf/ros:jazzy-ros-base.
# Does not source config/env/chain_a.sh and does not mount fastdds.xml as the
# Fast-DDS profile. Stock Jazzy RMW defaults are the 10× denominator.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROS2_HZJ_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

docker_ok() {
  docker info >/dev/null 2>&1
}

sudo_docker_ok() {
  sudo -n docker info >/dev/null 2>&1
}

pick_docker() {
  if docker_ok; then
    echo docker
    return 0
  fi
  if sudo_docker_ok; then
    echo "sudo -n docker"
    return 0
  fi
  return 1
}

print_no_docker() {
  cat >&2 <<EOF
docker is not usable on this host.
Install Docker Engine, then from the repository root:

  ./scripts/jazzy_baseline/docker_run.sh --smoke

Native Jazzy (Ubuntu 24.04):

  source /opt/ros/jazzy/setup.bash
  python3 scripts/jazzy_baseline/run.py --smoke
EOF
}

if ! command -v docker >/dev/null 2>&1 && ! sudo -n which docker >/dev/null 2>&1; then
  print_no_docker
  exit 2
fi

DOCKER_BIN="$(pick_docker)" || {
  print_no_docker
  exit 2
}

IMAGE="${JAZZY_BASELINE_IMAGE:-osrf/ros:jazzy-ros-base}"
if ! ${DOCKER_BIN} image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "[jazzy-baseline] pulling ${IMAGE}" >&2
  ${DOCKER_BIN} pull "${IMAGE}"
fi

OUT_REL="${JAZZY_BASELINE_OUT:-docs/artifacts/jazzy_baseline/smoke}"
mkdir -p "${ROS2_HZJ_ROOT}/${OUT_REL}"

# Extra RMW / rclpy packages: ros-base usually has rclpy + Fast-DDS; Cyclone
# is installed explicitly so both RMWs can run.
${DOCKER_BIN} run --rm --net=host --shm-size=1g \
  -v "${ROS2_HZJ_ROOT}:/work" -w /work \
  -e DEBIAN_FRONTEND=noninteractive \
  "${IMAGE}" \
  bash -lc "
    set -euo pipefail
    set +u
    source /opt/ros/jazzy/setup.bash
    set -u
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
      ros-jazzy-rclpy \
      ros-jazzy-std-msgs \
      ros-jazzy-rmw-fastrtps-cpp \
      ros-jazzy-rmw-cyclonedds-cpp >/dev/null
    set +u
    source /opt/ros/jazzy/setup.bash
    set -u
    python3 /work/scripts/jazzy_baseline/run.py --smoke --out /work/${OUT_REL} $*
  "
