#!/usr/bin/env bash
# FastDDS-only native latency (Chain A), run inside the Colima VM with Jazzy.
set +u
source /opt/ros/jazzy/setup.bash
HERE="$(cd "$(dirname "$0")" && pwd)"
NEED="${1:-1000}"; WARM="${2:-300}"; RATE="${3:-100}"
TOTAL=$((NEED + WARM))

run_cfg () {
  local name="$1"; shift
  echo "############################################################"
  echo "# CONFIG: $name (need=$NEED warmup=$WARM rate=$RATE)"
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
echo FAST_DONE
