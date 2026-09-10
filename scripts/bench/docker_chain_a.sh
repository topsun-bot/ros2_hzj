#!/usr/bin/env bash
# Operator recipe: run Chain A inside the in-repo Humble image (docker/ros/).
# Does not change image ENV (no RMW / domain baked in — same as DimOS docker/ros).
# Sources config/env/chain_a.sh at runtime.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

if ! command -v docker >/dev/null 2>&1; then
  cat >&2 <<EOF
docker is not on PATH. Install Docker Engine, then from the repository root:

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
  exit 2
fi

IMAGE="${CHAIN_A_IMAGE:-ros2_hzj/ros:humble}"
if [[ -z "$(docker images -q "${IMAGE}" 2>/dev/null)" ]]; then
  bench_log "building ${IMAGE} from docker/ros/Dockerfile (Humble + Nav2; no RMW/domain ENV)"
  docker build -f "${ROS2_HZJ_ROOT}/docker/ros/Dockerfile" -t "${IMAGE}" "${ROS2_HZJ_ROOT}"
fi

DATE="${BENCH_DATE}"
OUT_IN_CONTAINER="/work/docs/artifacts/bench/${DATE}/chain_a_same_process"
docker run --rm --net=host \
  -v "${ROS2_HZJ_ROOT}:/work" \
  -e TOPSUN_DIMOS="${TOPSUN_DIMOS:-}" \
  -w /work \
  "${IMAGE}" \
  bash -lc "
    set -euo pipefail
    source /opt/ros/humble/setup.bash
    source /work/config/env/chain_a.sh
    mkdir -p ${OUT_IN_CONTAINER}
    export PYTHONPATH=/work/dimos_bridge:\${PYTHONPATH:-}
    ./scripts/bench/run_chain_a.sh
  "
