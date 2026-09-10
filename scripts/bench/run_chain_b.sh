#!/usr/bin/env bash
# Chain B runner: Cyclone DDS / domain 0.
# Does NOT source chain_a.sh. Does not change DimOS or vendor defaults.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

TOPOLOGY="${TOPOLOGY:-same-process}"
OUT_DIR="${BENCH_ARTIFACT_ROOT}/chain_b_${TOPOLOGY//-/_}"
if [[ "${ICEORYX:-default}" == "off" ]]; then
  OUT_DIR="${OUT_DIR}_udp"
fi
bench_mkdir "${OUT_DIR}"

bench_log "Chain B topology=${TOPOLOGY} artifacts=${OUT_DIR}"
bench_log "Do not source chain_a.sh for native Cyclone DDS"

# Official in-tree path first (expected to fail on dimos_bridge stubs).
BRIDGE_PYTEST_LOG="${OUT_DIR}/pytest_dimos_bridge_attempt.txt"
set +e
(
  cd "${ROS2_HZJ_ROOT}"
  export PYTHONPATH="${ROS2_HZJ_ROOT}/dimos_bridge${PYTHONPATH:+:$PYTHONPATH}"
  python3 -m pytest \
    dimos_bridge/dimos/protocol/pubsub/benchmark/test_benchmark.py \
    -o addopts= \
    -m tool -k dds -v \
    --tb=short \
    --junitxml="${OUT_DIR}/pytest_dimos_bridge_junit.xml"
) >"${BRIDGE_PYTEST_LOG}" 2>&1
BRIDGE_RC=$?
set -e
bench_log "in-tree dimos_bridge pytest -m tool -k dds exit=${BRIDGE_RC} (stubs often ImportError)"

RESOLVE_JSON="${OUT_DIR}/dimos_resolve.json"
python3 "${SCRIPT_DIR}/resolve_dimos.py" --json >"${RESOLVE_JSON}" || true
DIMOS_ROOT="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("root",""))' "${RESOLVE_JSON}")"
DIMOS_SRC="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("source","unknown"))' "${RESOLVE_JSON}")"
DIMOS_SHA="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("git_sha") or "")' "${RESOLVE_JSON}")"

if [[ -z "${DIMOS_ROOT}" ]]; then
  bench_log "no importable DimOS tree; ping-pong / checkout pytest skipped"
  python3 "${SCRIPT_DIR}/collect_env.py" \
    --out "${OUT_DIR}/environment.md" \
    --repo-root "${ROS2_HZJ_ROOT}" \
    --chain B \
    --topology "${TOPOLOGY}" \
    --status blocked \
    --dimos-source "${DIMOS_SRC}" \
    --blocked-reason "resolve_dimos.py failed; see dimos_resolve.json and pytest_dimos_bridge_attempt.txt" \
    --notes "Tried vendored dimos_bridge then temporary topsun_dimos checkout. No fake percentiles."
  printf '%s\n' '{"status":"blocked","chain":"B","topology":"'"${TOPOLOGY}"'","error":"no DimOS tree"}' >"${OUT_DIR}/raw.json"
  python3 "${SCRIPT_DIR}/write_summary.py" \
    --raw "${OUT_DIR}/raw.json" \
    --out "${OUT_DIR}/summary.md" \
    --title "Chain B ${TOPOLOGY}" \
    --pytest-note "dimos_bridge pytest exit ${BRIDGE_RC}; see pytest_dimos_bridge_attempt.txt"
  exit 1
fi

export PYTHONPATH="${SCRIPT_DIR}:${DIMOS_ROOT}${PYTHONPATH:+:$PYTHONPATH}"
export TOPSUN_DIMOS="${DIMOS_ROOT}"

# Official checkout pytest (throughput / drain-time; not p50).
# -p hzj_dds_compat: host Pydantic 2.13 + DDSConfig forward-ref; does not edit DimOS.
CHECKOUT_LOG="${OUT_DIR}/pytest_topsun_dimos_stdout.txt"
set +e
(
  cd "${DIMOS_ROOT}"
  python3 -m pytest \
    dimos/protocol/pubsub/benchmark/test_benchmark.py \
    -o addopts= \
    -p hzj_dds_compat \
    -m tool -k dds -v \
    --tb=short \
    --junitxml="${OUT_DIR}/pytest_topsun_dimos_junit.xml"
) >"${CHECKOUT_LOG}" 2>&1
CHECKOUT_RC=$?
set -e
bench_log "topsun_dimos pytest -m tool -k dds exit=${CHECKOUT_RC}"

PING_ARGS=(
  --chain B
  --topology "${TOPOLOGY}"
  --dimos-root "${DIMOS_ROOT}"
  --domain-id 0
  --out "${OUT_DIR}/raw.json"
)
if [[ "${ICEORYX:-default}" == "off" ]]; then
  PING_ARGS+=(--iceoryx off)
fi
if [[ -n "${BENCH_SIZES:-}" ]]; then
  PING_ARGS+=(--sizes "${BENCH_SIZES}")
fi
if [[ -n "${BENCH_SAMPLES:-}" ]]; then
  PING_ARGS+=(--samples "${BENCH_SAMPLES}")
fi

set +e
python3 "${SCRIPT_DIR}/pingpong.py" "${PING_ARGS[@]}" >"${OUT_DIR}/pingpong_stdout.txt" 2>"${OUT_DIR}/pingpong_stderr.txt"
PING_RC=$?
set -e
bench_log "pingpong.py exit=${PING_RC}"

STATUS=ok
if [[ "${PING_RC}" -ne 0 ]]; then
  STATUS=blocked
fi
if [[ "${PING_RC}" -eq 0 && "${CHECKOUT_RC}" -ne 0 ]]; then
  STATUS=partial
fi

NOTES=$(cat <<EOF
Chain B native Cyclone DDS (ddspubsub.DDS), DDSConfig.domain_id default 0.
Did not source config/env/chain_a.sh.
in-tree dimos_bridge pytest exit=${BRIDGE_RC}; checkout pytest exit=${CHECKOUT_RC}.
Pytest harness = throughput + drain-after-publish, NOT per-message percentiles.
Percentiles come only from scripts/bench/pingpong.py.
DimOS source: ${DIMOS_SRC} @ ${DIMOS_SHA}
Pinned copy SHA in dimos_bridge/SOURCE.md: a5259958db23c8ea6648544ed138eab19726ce93
EOF
)

python3 "${SCRIPT_DIR}/collect_env.py" \
  --out "${OUT_DIR}/environment.md" \
  --repo-root "${ROS2_HZJ_ROOT}" \
  --chain B \
  --topology "${TOPOLOGY}" \
  --status "${STATUS}" \
  --dimos-source "${DIMOS_SRC}" \
  --dimos-root "${DIMOS_ROOT}" \
  --dimos-sha "${DIMOS_SHA}" \
  --ros-domain-id 0 \
  --notes "${NOTES}"

PYTEST_NOTE=$(cat <<EOF
- \`dimos_bridge\` official command exit \`${BRIDGE_RC}\` — log: \`pytest_dimos_bridge_attempt.txt\`
- temporary \`topsun_dimos\` checkout official command exit \`${CHECKOUT_RC}\` — log: \`pytest_topsun_dimos_stdout.txt\`, junit: \`pytest_topsun_dimos_junit.xml\`
- 上游 harness 的 Latency 列是 **发完再等收齐** 的 drain time，不是 p50/p95/p99。
EOF
)

python3 "${SCRIPT_DIR}/write_summary.py" \
  --raw "${OUT_DIR}/raw.json" \
  --out "${OUT_DIR}/summary.md" \
  --title "Chain B ${TOPOLOGY}" \
  --pytest-note "${PYTEST_NOTE}"

bench_log "wrote ${OUT_DIR}/summary.md environment.md raw.json"
exit "${PING_RC}"
