#!/usr/bin/env bash
# Large-packet same-topology ping-pong (Feishu / lidar scale).
# Does not change middleware / vendor / DimOS defaults.
# Chain A and Chain B are separate commands — never one mixed table.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

# Exact payload lengths (bytes). 100 KiB / 256 KiB / 1 MiB lidar-ish.
# Override if a size OOMs; document the largest stable size in the artifact README.
export BENCH_SIZES="${BENCH_SIZES:-102400,262144,1048576}"
export BENCH_SAMPLES="${BENCH_SAMPLES:-80}"
export BENCH_WARMUP="${BENCH_WARMUP:-10}"
# 100 ms minimum inter-publish gap ≈ 10 Hz lidar-ish. If RTT > gap, rate is 1/RTT.
export BENCH_INTERVAL_MS="${BENCH_INTERVAL_MS:-100}"
export BENCH_TIMEOUT="${BENCH_TIMEOUT:-8}"
export BENCH_SKIP_PYTEST="${BENCH_SKIP_PYTEST:-1}"
# Contiguous uint8 — Humble ByteMultiArray (1 Python bytes/octet) is not viable at ≥100KiB.
export BENCH_ROS_MSG="${BENCH_ROS_MSG:-uint8_multiarray}"
export BENCH_SCALE_LABEL="${BENCH_SCALE_LABEL:-lidar-ish}"

CHAINS="${LARGE_PACKET_CHAINS:-A B}"
# same-process + same-host only. cross-host-UDP is recorded blocked (single VM).
TOPOS="${LARGE_PACKET_TOPOLOGIES:-same-process same-host}"

bench_log "large-packet sizes=${BENCH_SIZES} samples=${BENCH_SAMPLES} warmup=${BENCH_WARMUP}"
bench_log "interval_ms=${BENCH_INTERVAL_MS} timeout=${BENCH_TIMEOUT} date=${BENCH_DATE}"
bench_log "chains=${CHAINS} topologies=${TOPOS}"
bench_log "NOT real-robot / Feishu-field / cross-host proof. Do not mix A and B in one table."

RC=0
for chain in ${CHAINS}; do
  if [[ "${chain}" == "A" ]]; then
    IMAGE="${CHAIN_A_IMAGE:-osrf/ros:humble-desktop}"
    export CHAIN_A_IMAGE="${IMAGE}"
    export CHAIN_A_TOPOLOGIES="${TOPOS}"
    if ! "${SCRIPT_DIR}/docker_chain_a.sh"; then
      bench_log "Chain A docker runner exited non-zero"
      RC=1
    fi
  elif [[ "${chain}" == "B" ]]; then
    for topo in ${TOPOS}; do
      if ! TOPOLOGY="${topo}" "${SCRIPT_DIR}/run_chain_b.sh"; then
        bench_log "Chain B topology=${topo} exited non-zero"
        RC=1
      fi
    done
    TOPOLOGY=cross-host-UDP "${SCRIPT_DIR}/run_chain_b.sh" || true
  else
    bench_log "unknown chain ${chain}"
    RC=1
  fi
done

exit "${RC}"
