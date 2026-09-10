#!/usr/bin/env bash
# Operator recipe: run Chain A inside a Humble image.
# Default image is built from docker/ros/ (Humble + Nav2; no RMW / domain ENV —
# same as DimOS docker/ros). Override with CHAIN_A_IMAGE=... if needed.
# Sources config/env/chain_a.sh at runtime. Does not change vendor / DimOS QoS.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

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
docker is not usable on this host (not on PATH, or daemon not running).
Install Docker Engine, then from the repository root:

  docker build -f docker/ros/Dockerfile -t ros2_hzj/ros:humble .

  docker run --rm --net=host \\
    -v "${ROS2_HZJ_ROOT}:/work" -w /work \\
    ros2_hzj/ros:humble \\
    bash -lc 'source /opt/ros/humble/setup.bash
              source /work/config/env/chain_a.sh
              export PYTHONPATH=/work/dimos_bridge:\${PYTHONPATH:-}
              # Official ROS pytest filter (needs a DimOS tree with rclpy extras):
              pytest /work/dimos_bridge/dimos/protocol/pubsub/benchmark/test_benchmark.py \\
                -o addopts= -m tool -k "ros or RawROS or DimosROS" -v || true
              python3 /work/scripts/bench/pingpong.py --chain A --topology same-process \\
                --out /work/docs/artifacts/bench/\$(date -u +%Y-%m-%d)/chain_a_same_process/raw.json'

Host path (no Docker): ./scripts/bench/run_chain_a.sh
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

IMAGE="${CHAIN_A_IMAGE:-ros2_hzj/ros:humble}"
if ! ${DOCKER_BIN} image inspect "${IMAGE}" >/dev/null 2>&1; then
  if [[ "${IMAGE}" == "ros2_hzj/ros:humble" ]]; then
    bench_log "building ${IMAGE} from docker/ros/Dockerfile (Humble + Nav2; no RMW/domain ENV)"
    ${DOCKER_BIN} build -f "${ROS2_HZJ_ROOT}/docker/ros/Dockerfile" -t "${IMAGE}" "${ROS2_HZJ_ROOT}"
  else
    bench_log "pulling ${IMAGE}"
    ${DOCKER_BIN} pull "${IMAGE}"
  fi
fi

DATE="${BENCH_DATE}"
# same-process always; same-host when pingpong.py implements two-process Chain A.
TOPOLOGIES="${CHAIN_A_TOPOLOGIES:-same-process same-host}"

run_in_image() {
  local topology="$1"
  bench_log "container Chain A topology=${topology} image=${IMAGE}"
  ${DOCKER_BIN} run --rm --net=host \
    --ipc=host \
    -v "${ROS2_HZJ_ROOT}:/work" \
    -e TOPSUN_DIMOS="${TOPSUN_DIMOS:-}" \
    -e BENCH_DATE="${DATE}" \
    -e TOPOLOGY="${topology}" \
    -e BENCH_SIZES="${BENCH_SIZES:-}" \
    -e BENCH_SAMPLES="${BENCH_SAMPLES:-}" \
    -w /work \
    "${IMAGE}" \
    bash -lc "
      set -euo pipefail
      source /opt/ros/humble/setup.bash
      source /work/config/env/chain_a.sh
      export PYTHONPATH=/work/dimos_bridge:\${PYTHONPATH:-}
      # pytest is not in the DimOS docker/ros package list; install only in this
      # ephemeral container so the official -m tool filter can run. No image ENV.
      python3 -m pip install --user -q pytest 2>/dev/null || \
        python3 -m pip install --user -q --break-system-packages pytest 2>/dev/null || true
      ./scripts/bench/run_chain_a.sh
    "
}

RC=0
for topology in ${TOPOLOGIES}; do
  if ! run_in_image "${topology}"; then
    bench_log "topology ${topology} exited non-zero (artifacts still written if runner reached disk)"
    RC=1
  fi
done

# Single-VM: always record cross-host-UDP as blocked (no second machine).
bench_log "recording chain_a_cross_host_UDP as blocked (single host)"
TOPOLOGY=cross-host-UDP BENCH_DATE="${DATE}" "${SCRIPT_DIR}/run_chain_a.sh" || true

exit "${RC}"
