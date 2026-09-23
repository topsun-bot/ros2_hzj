#!/usr/bin/env bash
# Native (arm64) one-way latency probe, run INSIDE the Colima VM with ROS Jazzy.
# Jazzy is a native functional/latency proxy; the workspace targets Humble, so
# these numbers are not a Humble certification. Usage: run_latency.sh [need]
# [warmup] [rate_hz]
set +u
source /opt/ros/jazzy/setup.bash
HERE="$(cd "$(dirname "$0")" && pwd)"
NEED="${1:-1000}"
WARM="${2:-300}"
RATE="${3:-100}"
TOTAL=$((NEED + WARM))

run_cfg () {
  local name="$1"; shift
  echo "############################################################"
  echo "# CONFIG: $name  (need=$NEED warmup=$WARM rate=$RATE)"
  echo "############################################################"
  rm -f /tmp/lp.log
  ( env "$@" python3 "$HERE/lat_listener.py" "$NEED" "$WARM" 120 \
      > /tmp/lp.log 2>&1 ) &
  local lpid=$!
  sleep 8
  env "$@" python3 "$HERE/lat_talker.py" "$TOTAL" "$RATE" \
      > /tmp/tk.log 2>&1
  wait "$lpid"
  grep -v '^progress' /tmp/lp.log
  echo
}

run_cfg "Chain A FastDDS default domain42" \
  RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_DOMAIN_ID=42
run_cfg "Chain A FastDDS UDP-only domain42" \
  RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_DOMAIN_ID=42 \
  FASTRTPS_DEFAULT_PROFILES_FILE="$HERE/udp_only.xml"
run_cfg "Chain B Cyclone default domain0" \
  RMW_IMPLEMENTATION=rmw_cyclonedds_cpp ROS_DOMAIN_ID=0 CYCLONEDDS_URI=
echo ALL_DONE
