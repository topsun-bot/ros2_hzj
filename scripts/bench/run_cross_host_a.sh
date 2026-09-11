#!/usr/bin/env bash
# Chain A Fast-DDS two-machine cross-host UDP recipe.
#
# Thin wrapper around pingpong.py / collect_env.py / write_summary.py.
# Does NOT change config/fastdds.xml, RMW, domains, or vendor trees.
# Does NOT invent percentiles. Single-VM default is STATUS: blocked.
#
# Roles:
#   Host B (responder / echo)  — start first, leave running
#   Host A (client / pub)      — measures RTT p50/p95/p99, writes artifacts
#
# 不是飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default artifact dir: docs/artifacts/bench/<UTC-date>-cross-host/
if [[ -z "${BENCH_DATE:-}" ]]; then
  BENCH_DATE="$(date -u +%Y-%m-%d)-cross-host"
fi
export BENCH_DATE

# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

# Files live at the date-cross-host root (not a nested topology dir).
OUT_DIR="${BENCH_ARTIFACT_ROOT}"
bench_mkdir "${OUT_DIR}"

ROLE="${ROLE:-}"
CROSS_HOST_PEER="${CROSS_HOST_PEER:-}"
QOS="${QOS:-high_throughput}"
TOPIC_PREFIX="${BENCH_TOPIC_PREFIX:-hzj_cross_host}"
DISCOVER_S="${BENCH_DISCOVER_S:-5}"
LOCAL_HOST="$(hostname -s 2>/dev/null || hostname)"

usage() {
  cat <<'EOF'
Chain A cross-host UDP (Fast-DDS / domain 42 / iter7 config/fastdds.xml).

  # Host B — responder / echo (start first, leave running)
  source /opt/ros/humble/setup.bash
  source config/env/chain_a.sh
  ROLE=responder QOS=high_throughput \
    BENCH_TOPIC_PREFIX=hzj_cross_host \
    ./scripts/bench/run_cross_host_a.sh

  # Host A — client / pub (writes p50/p95/p99)
  source /opt/ros/humble/setup.bash
  source config/env/chain_a.sh
  ROLE=client CROSS_HOST_PEER=<host-B-hostname-or-ip> \
    QOS=high_throughput BENCH_TOPIC_PREFIX=hzj_cross_host \
    ./scripts/bench/run_cross_host_a.sh

  # This VM / no second host: record blocked (no fake numbers)
  ./scripts/bench/run_cross_host_a.sh

One QoS per invocation (responder binds that QoS). Repeat for `reliable`.
Do not mix Chain A and Chain B in one table. Chain B is documented only
in scripts/bench/README.md (same pingpong.py --chain B roles; domain 0).

Env (both hosts, from config/env/chain_a.sh):
  RMW_IMPLEMENTATION=rmw_fastrtps_cpp
  ROS_DOMAIN_ID=42
  FASTRTPS_DEFAULT_PROFILES_FILE=<repo>/config/fastdds.xml

Artifacts: docs/artifacts/bench/<UTC-date>-cross-host/{summary.md,raw.json,environment.md}

不是飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

source_chain_a_if_needed() {
  if [[ -z "${RMW_IMPLEMENTATION:-}" || -z "${ROS_DOMAIN_ID:-}" || -z "${FASTRTPS_DEFAULT_PROFILES_FILE:-}" ]]; then
    # shellcheck source=../../config/env/chain_a.sh
    source "${ROS2_HZJ_ROOT}/config/env/chain_a.sh"
  fi
}

source_ros_if_present() {
  local cand
  for cand in /opt/ros/humble/setup.bash /opt/ros/jazzy/setup.bash /opt/ros/${ROS_DISTRO:-humble}/setup.bash; do
    if [[ -f "${cand}" ]]; then
      set +u
      # shellcheck disable=SC1090
      source "${cand}"
      set -u
      return 0
    fi
  done
  return 1
}

write_blocked() {
  local reason="$1"
  local host_b_id="${CROSS_HOST_PEER:-missing}"
  local host_b_notes="no second machine in this environment; CROSS_HOST_PEER unset or ROLE not client/responder"
  if [[ -n "${CROSS_HOST_PEER}" ]]; then
    host_b_notes="peer identity was set but the run did not measure (see blocked reason)"
  fi
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
    --hostname-class "cursor-cloud-vm" \
    --dimos-source "not used (cross-host recipe; ping-pong only)" \
    --blocked-reason "${reason}" \
    --host-a "${LOCAL_HOST}" \
    --host-a-notes "this process / single-host VM (client/pub role would live here)" \
    --host-b "${host_b_id}" \
    --host-b-notes "${host_b_notes}" \
    --notes "$(cat <<EOF
Single-host (or incomplete two-host) environment. Cross-host UDP left **blocked**.
No fake p50/p95/p99. Do not compare with Chain B. Do not mix topologies.

Recipe: scripts/bench/run_cross_host_a.sh and scripts/bench/README.md.
XML: config/fastdds.xml is the iter7 seed — this runner does not edit it.

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.
《3》90%/LLM, 《4》Mac/preprod, 《5》Promptfoo, 《6》CVE — still Hold.
EOF
)"
  python3 "${SCRIPT_DIR}/write_summary.py" \
    --raw "${OUT_DIR}/raw.json" \
    --out "${OUT_DIR}/summary.md" \
    --title "Chain A cross-host-UDP" \
    --pytest-note "Not run: needs two real hosts. See README.md in this directory."
  {
    printf '%s\n' "STATUS: blocked — ${reason}"
    printf '%s\n' ""
    printf '%s\n' "不是飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof."
  } >"${OUT_DIR}/BLOCKED.txt"
  bench_log "wrote blocked ${OUT_DIR}"
}

write_ok_env() {
  local status="$1"
  python3 "${SCRIPT_DIR}/collect_env.py" \
    --out "${OUT_DIR}/environment.md" \
    --repo-root "${ROS2_HZJ_ROOT}" \
    --chain A \
    --topology cross-host-UDP \
    --status "${status}" \
    --rmw "${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}" \
    --ros-domain-id "${ROS_DOMAIN_ID:-42}" \
    --ros-distro "${ROS_DISTRO:-}" \
    --dimos-source "not used (cross-host recipe; ping-pong only)" \
    --host-a "${LOCAL_HOST}" \
    --host-a-notes "client / pub (this process wrote raw.json)" \
    --host-b "${CROSS_HOST_PEER}" \
    --host-b-notes "responder / echo (started first with the same TOPIC_PREFIX and QOS)" \
    --notes "$(cat <<EOF
Sourced chain_a.sh (RMW=rmw_fastrtps_cpp, ROS_DOMAIN_ID=42,
FASTRTPS_DEFAULT_PROFILES_FILE=${FASTRTPS_DEFAULT_PROFILES_FILE:-unset}).
QOS=${QOS} TOPIC_PREFIX=${TOPIC_PREFIX} DISCOVER_S=${DISCOVER_S}.
fastdds.xml is the iter7 seed — unchanged. Builtin UDP + implicit SHM in XML
does not make this SHM; cross-host is UDP. Do not invent SHM.
Do not compare with Chain B.

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.
EOF
)"
}

# ---------------------------------------------------------------------------
# Default: no ROLE / no peer → blocked (this cloud VM is single-host).
# Still source chain_a.sh so environment.md records the intended contract
# (RMW / domain 42 / iter7 fastdds.xml path) — not a measurement claim.
# ---------------------------------------------------------------------------
source_chain_a_if_needed
if [[ -z "${ROLE}" ]]; then
  write_blocked "cross-host-UDP needs a second machine; this runner is single-host (ROLE unset, CROSS_HOST_PEER='${CROSS_HOST_PEER}')"
  exit 0
fi

if [[ "${ROLE}" != "responder" && "${ROLE}" != "client" ]]; then
  echo "ROLE must be responder or client (or omit ROLE to record blocked)" >&2
  usage >&2
  exit 2
fi

source_chain_a_if_needed

if [[ "${ROLE}" == "client" && -z "${CROSS_HOST_PEER}" ]]; then
  write_blocked "ROLE=client but CROSS_HOST_PEER is empty — refusing to invent a peer or percentiles"
  exit 0
fi

if ! source_ros_if_present; then
  if [[ "${ROLE}" == "responder" ]]; then
    echo "ERROR: ROLE=responder needs ROS 2 Humble (rclpy) on this host. See docker/ros/." >&2
    exit 1
  fi
  write_blocked "ROLE=${ROLE} but ROS 2 Humble / rclpy is missing on this host (no second measured endpoint)"
  exit 0
fi

if ! python3 -c "import rclpy" 2>/dev/null; then
  if [[ "${ROLE}" == "responder" ]]; then
    echo "ERROR: python3-rclpy missing; cannot start responder." >&2
    exit 1
  fi
  write_blocked "ROLE=${ROLE} but python3-rclpy is missing on this host"
  exit 0
fi

# Humble Fast-DDS SIMPLE discovery (domain 42) uses UDP multicast 239.255.0.1
# plus unicast. Default portBase=7400, domainIDGain=250:
#   multicast metatraffic  7400 + 250*42 + 0  = 17900
#   unicast metatraffic    7400 + 250*42 + 10 = 17910
#   unicast user traffic   7400 + 250*42 + 11 = 17911
# Firewall must allow those UDP ports (and typically 7400–19000 UDP) both ways.
# Same L2 / multicast-reachable L3 is required: this recipe does NOT add
# initialPeersList to fastdds.xml (no new knobs).

if [[ "${ROLE}" == "responder" ]]; then
  bench_log "Chain A cross-host responder QOS=${QOS} prefix=${TOPIC_PREFIX} domain=${ROS_DOMAIN_ID}"
  bench_log "Start the client on the other host with the same QOS and TOPIC_PREFIX."
  bench_log "不是飞书现场 / 实机 / 跨机根因证明。"
  exec python3 "${SCRIPT_DIR}/pingpong.py" \
    --chain A \
    --topology cross-host-UDP \
    --role responder \
    --qos "${QOS}" \
    --topic-prefix "${TOPIC_PREFIX}" \
    ${BENCH_ROS_MSG:+--ros-msg "${BENCH_ROS_MSG}"}
fi

# ROLE=client
bench_log "Chain A cross-host client peer=${CROSS_HOST_PEER} QOS=${QOS} prefix=${TOPIC_PREFIX}"
set +e
python3 "${SCRIPT_DIR}/pingpong.py" \
  --chain A \
  --topology cross-host-UDP \
  --role client \
  --remote-peer "${CROSS_HOST_PEER}" \
  --qos "${QOS}" \
  --topic-prefix "${TOPIC_PREFIX}" \
  --discover-s "${DISCOVER_S}" \
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
fi

write_ok_env "${STATUS}"
python3 "${SCRIPT_DIR}/write_summary.py" \
  --raw "${OUT_DIR}/raw.json" \
  --out "${OUT_DIR}/summary.md" \
  --title "Chain A cross-host-UDP" \
  --pytest-note "Official ROS pytest not run (cross-host ping-pong only). Not Feishu field proof."

exit "${PING_RC}"
