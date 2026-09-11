#!/usr/bin/env bash
# High-frequency small-packet same-topology ping-pong (Feishu / IMU scale).
# Does not change middleware / vendor / DimOS defaults.
# Chain A and Chain B are separate commands — never one mixed table.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

# Exact payload length (bytes): 64 B compact 6-axis IMU sample.
#   8 B timestamp (uint64 ns)
#  24 B linear acceleration (3 × float64)
#  24 B angular velocity (3 × float64)
#   8 B sequence / pad
# This is the on-wire body without sensor_msgs/Imu covariance matrices
# (3 × 9 × float64 ≈ 216 B, usually static, not sent every sample in
# compact robot IMU streams). Full ROS Imu with covariances is ~300 B+
# and is outside the 32–128 B IMU-ish window. 64 B sits in that window
# and matches the existing default bench size so tables stay comparable.
export BENCH_SIZES="${BENCH_SIZES:-64}"
export BENCH_SAMPLES="${BENCH_SAMPLES:-400}"
export BENCH_WARMUP="${BENCH_WARMUP:-40}"
# 5 ms minimum inter-publish gap ≈ 200 Hz IMU-ish (robotics / Unitree-class).
# 100 Hz would be 10 ms; 200 Hz is the upper half of the 100–200+ Hz band.
# If RTT > 5 ms, effective rate is 1/RTT (closed-loop).
export BENCH_INTERVAL_MS="${BENCH_INTERVAL_MS:-5}"
export BENCH_TIMEOUT="${BENCH_TIMEOUT:-1}"
export BENCH_SKIP_PYTEST="${BENCH_SKIP_PYTEST:-1}"
# Contiguous uint8 — same payload path as the large-packet suite (not
# Humble ByteMultiArray's one-Python-bytes-per-octet overhead).
export BENCH_ROS_MSG="${BENCH_ROS_MSG:-uint8_multiarray}"
export BENCH_SCALE_LABEL="${BENCH_SCALE_LABEL:-IMU-ish}"

CHAINS="${IMU_HF_CHAINS:-A}"
# same-process + same-host only. cross-host-UDP is recorded blocked (single VM).
TOPOS="${IMU_HF_TOPOLOGIES:-same-process same-host}"

bench_log "imu-hf sizes=${BENCH_SIZES} samples=${BENCH_SAMPLES} warmup=${BENCH_WARMUP}"
bench_log "interval_ms=${BENCH_INTERVAL_MS} timeout=${BENCH_TIMEOUT} date=${BENCH_DATE}"
bench_log "chains=${CHAINS} topologies=${TOPOS} scale=${BENCH_SCALE_LABEL}"
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
