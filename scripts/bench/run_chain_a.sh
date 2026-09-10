#!/usr/bin/env bash
# Chain A runner: ROS 2 Fast-DDS / domain 42.
# Operator should already have sourced /opt/ros/<distro>/setup.bash and
# config/env/chain_a.sh. This script sources chain_a.sh itself if RMW is unset.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

TOPOLOGY="${TOPOLOGY:-same-process}"
OUT_DIR="${BENCH_ARTIFACT_ROOT}/chain_a_${TOPOLOGY//-/_}"
bench_mkdir "${OUT_DIR}"

write_cross_host_blocked() {
  local reason="cross-host-UDP needs a second machine; this runner is single-host"
  python3 "${SCRIPT_DIR}/pingpong.py" \
    --chain A \
    --topology cross-host-UDP \
    --out "${OUT_DIR}/raw.json" >/dev/null || true
  python3 "${SCRIPT_DIR}/collect_env.py" \
    --out "${OUT_DIR}/environment.md" \
    --repo-root "${ROS2_HZJ_ROOT}" \
    --chain A \
    --topology cross-host-UDP \
    --status blocked \
    --rmw "${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}" \
    --ros-domain-id "${ROS_DOMAIN_ID:-42}" \
    --ros-distro "${ROS_DISTRO:-}" \
    --dimos-source "not used (single-host VM)" \
    --blocked-reason "${reason}" \
    --notes "Single cloud VM. Cross-host UDP left blocked. No fake percentiles. Do not compare with Chain B."
  python3 "${SCRIPT_DIR}/write_summary.py" \
    --raw "${OUT_DIR}/raw.json" \
    --out "${OUT_DIR}/summary.md" \
    --title "Chain A cross-host-UDP" \
    --pytest-note "Not run: needs a second host."
  printf '%s\n' "STATUS: blocked — ${reason}" >"${OUT_DIR}/BLOCKED.txt"
  bench_log "wrote blocked ${OUT_DIR}"
}

if [[ "${TOPOLOGY}" == "cross-host-UDP" ]]; then
  write_cross_host_blocked
  exit 0
fi

# Apply Chain A contract if the caller did not already.
if [[ -z "${RMW_IMPLEMENTATION:-}" || -z "${ROS_DOMAIN_ID:-}" ]]; then
  # shellcheck source=../../config/env/chain_a.sh
  source "${ROS2_HZJ_ROOT}/config/env/chain_a.sh"
fi

ROS_SETUP=""
for cand in /opt/ros/humble/setup.bash /opt/ros/jazzy/setup.bash /opt/ros/${ROS_DISTRO:-humble}/setup.bash; do
  if [[ -f "${cand}" ]]; then
    ROS_SETUP="${cand}"
    # Humble setup.bash reads AMENT_TRACE_SETUP_FILES unset; nounset must be off.
    set +u
    # shellcheck disable=SC1090
    source "${cand}"
    set -u
    break
  fi
done

MISSING=()
python3 -c "import rclpy" 2>/dev/null || MISSING+=("python3-rclpy / ROS 2 rclpy")
command -v ros2 >/dev/null 2>&1 || MISSING+=("ros2 CLI")
[[ -n "${ROS_SETUP}" ]] || MISSING+=(" /opt/ros/humble/setup.bash (host is not Humble; see docker/ros/)")

if [[ "${#MISSING[@]}" -gt 0 ]]; then
  bench_log "Chain A blocked: ${MISSING[*]}"
  REASON="missing: $(IFS=', '; echo "${MISSING[*]}")"
  NOTES=$(cat <<EOF
STATUS: blocked on this VM.

Exact missing deps:
$(printf ' - %s\n' "${MISSING[@]}")

Host OS: $(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-unknown}")
ROS Humble apt packages target Ubuntu 22.04; this host may be newer.

Operator recipe (do not invent numbers here):
  ./scripts/bench/docker_chain_a.sh

That builds \`docker/ros/\` (Humble; no RMW/domain ENV in the image — same as DimOS)
then sources \`config/env/chain_a.sh\` (RMW=rmw_fastrtps_cpp, ROS_DOMAIN_ID=42)
and runs the ROS pytest filter + pingpong.

In-tree pytest command that would run if rclpy existed:

  source /opt/ros/humble/setup.bash
  source config/env/chain_a.sh
  export PYTHONPATH="\${PWD}/dimos_bridge:\${PYTHONPATH:-}"
  pytest dimos_bridge/dimos/protocol/pubsub/benchmark/test_benchmark.py -m tool -k 'ros or RawROS or DimosROS' -v

Do not compare any future Chain A table with Chain B.
EOF
)
  python3 "${SCRIPT_DIR}/collect_env.py" \
    --out "${OUT_DIR}/environment.md" \
    --repo-root "${ROS2_HZJ_ROOT}" \
    --chain A \
    --topology "${TOPOLOGY}" \
    --status blocked \
    --rmw "${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}" \
    --ros-domain-id "${ROS_DOMAIN_ID:-42}" \
    --ros-distro "${ROS_DISTRO:-}" \
    --dimos-source "not used (ROS missing)" \
    --blocked-reason "${REASON}" \
    --notes "${NOTES}"
  python3 - <<PY
import json
from pathlib import Path
Path("${OUT_DIR}/raw.json").write_text(json.dumps({
    "status": "blocked",
    "chain": "A",
    "topology": "${TOPOLOGY}",
    "domain_id": 42,
    "rmw": "${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}",
    "ros_domain_id": "${ROS_DOMAIN_ID:-42}",
    "metric": "round-trip time",
    "units": "microseconds",
    "error": "${REASON}",
    "cases": [],
    "errors": ["${REASON}"],
}, indent=2) + "\n", encoding="utf-8")
PY
  python3 "${SCRIPT_DIR}/write_summary.py" \
    --raw "${OUT_DIR}/raw.json" \
    --out "${OUT_DIR}/summary.md" \
    --title "Chain A ${TOPOLOGY}" \
    --pytest-note "Not run: ROS 2 Humble / rclpy / rmw_fastrtps_cpp missing on host. See docker_chain_a.sh."
  printf '%s\n' "${NOTES}" >"${OUT_DIR}/BLOCKED.txt"
  exit 0
fi

# ROS is present — try dimos_bridge first, then checkout for DimosROS Image types.
DIMOS_ROOT=""
DIMOS_SRC="not used (large-packet ping-pong / pytest skipped or ROS-only)"
DIMOS_SHA=""
if [[ "${BENCH_SKIP_PYTEST:-}" == "1" ]]; then
  PYTEST_RC=0
  printf '%s\n' "BENCH_SKIP_PYTEST=1 — official ROS pytest not run (large-packet ping-pong only)." \
    >"${OUT_DIR}/pytest_ros_stdout.txt"
else
  RESOLVE_JSON="${OUT_DIR}/dimos_resolve.json"
  python3 "${SCRIPT_DIR}/resolve_dimos.py" --json >"${RESOLVE_JSON}" || true
  DIMOS_ROOT="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("root",""))' "${RESOLVE_JSON}")"
  DIMOS_SRC="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("source","unknown"))' "${RESOLVE_JSON}")"
  DIMOS_SHA="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("git_sha") or "")' "${RESOLVE_JSON}")"

  BENCH_ROOT="${DIMOS_ROOT:-${ROS2_HZJ_ROOT}/dimos_bridge}"
  BENCH_FILE="dimos/protocol/pubsub/benchmark/test_benchmark.py"
  if [[ "${BENCH_ROOT}" == "${ROS2_HZJ_ROOT}/dimos_bridge" ]]; then
    BENCH_FILE="dimos_bridge/dimos/protocol/pubsub/benchmark/test_benchmark.py"
    BENCH_ROOT="${ROS2_HZJ_ROOT}"
  fi

  PYTEST_LOG="${OUT_DIR}/pytest_ros_stdout.txt"
  set +e
  (
    cd "${BENCH_ROOT}"
    export PYTHONPATH="${DIMOS_ROOT:-${ROS2_HZJ_ROOT}/dimos_bridge}${PYTHONPATH:+:$PYTHONPATH}"
    python3 -m pytest \
      "${BENCH_FILE}" \
      -o addopts= \
      -m tool -k 'ros or RawROS or DimosROS' -v \
      --tb=short \
      --junitxml="${OUT_DIR}/pytest_ros_junit.xml"
  ) >"${PYTEST_LOG}" 2>&1
  PYTEST_RC=$?
  set -e
fi

set +e
python3 "${SCRIPT_DIR}/pingpong.py" \
  --chain A \
  --topology "${TOPOLOGY}" \
  --out "${OUT_DIR}/raw.json" \
  ${BENCH_SIZES:+--sizes "${BENCH_SIZES}"} \
  ${BENCH_SAMPLES:+--samples "${BENCH_SAMPLES}"} \
  ${BENCH_WARMUP:+--warmup "${BENCH_WARMUP}"} \
  ${BENCH_TIMEOUT:+--timeout "${BENCH_TIMEOUT}"} \
  ${BENCH_INTERVAL_MS:+--interval-ms "${BENCH_INTERVAL_MS}"} \
  ${BENCH_ROS_MSG:+--ros-msg "${BENCH_ROS_MSG}"} \
  >"${OUT_DIR}/pingpong_stdout.txt" 2>"${OUT_DIR}/pingpong_stderr.txt"
PING_RC=$?
set -e

STATUS=ok
if [[ "${PING_RC}" -ne 0 ]]; then
  STATUS=blocked
elif [[ "${PYTEST_RC}" -ne 0 ]]; then
  STATUS=partial
fi

python3 "${SCRIPT_DIR}/collect_env.py" \
  --out "${OUT_DIR}/environment.md" \
  --repo-root "${ROS2_HZJ_ROOT}" \
  --chain A \
  --topology "${TOPOLOGY}" \
  --status "${STATUS}" \
  --dimos-source "${DIMOS_SRC}" \
  --dimos-root "${DIMOS_ROOT}" \
  --dimos-sha "${DIMOS_SHA}" \
  --rmw "${RMW_IMPLEMENTATION}" \
  --ros-domain-id "${ROS_DOMAIN_ID}" \
  --ros-distro "${ROS_DISTRO:-}" \
  --notes "Sourced chain_a.sh (RMW=rmw_fastrtps_cpp, ROS_DOMAIN_ID=42). ROS setup=${ROS_SETUP}. pytest exit=${PYTEST_RC}. pingpong exit=${PING_RC}. Topology=${TOPOLOGY}. BENCH_SIZES=${BENCH_SIZES:-default}. BENCH_INTERVAL_MS=${BENCH_INTERVAL_MS:-0}. BENCH_ROS_MSG=${BENCH_ROS_MSG:-byte_multiarray}. Fast-DDS transports are whatever the Humble rmw_fastrtps_cpp default plus config/fastdds.xml use — fastdds.xml does not force UDP-only or SHM-only; do not invent SHM. Do not compare with Chain B. Not real-robot / Feishu-field / cross-host proof."

python3 "${SCRIPT_DIR}/write_summary.py" \
  --raw "${OUT_DIR}/raw.json" \
  --out "${OUT_DIR}/summary.md" \
  --title "Chain A ${TOPOLOGY}" \
  --pytest-note "pytest -m tool -k 'ros or RawROS or DimosROS' exit ${PYTEST_RC}; see pytest_ros_stdout.txt"

exit "${PING_RC}"
