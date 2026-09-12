# 链 B — Cyclone / 域 0。必须 source，不要直接执行。
# 原生 DimOS DDS 读的是 DDSConfig.domain_id（默认 0），不是这些 ROS 变量。
# 本脚本只为「要用 ROS 2 RMW 对齐链 B」的操作员准备。
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "source ${BASH_SOURCE[0]}  （不要直接执行）" >&2
  exit 1
fi

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
# 不设置 CYCLONEDDS_URI：本仓没有现网 Cyclone XML。
# Autoware 公开配方是标签示例（非默认、非 SCOREBOARD）：
#   scripts/bench/cyclonedds_autoware_like.xml
# 操作员若要试，须自己 export CYCLONEDDS_URI=file://<绝对路径>。
# 对照：docs/architecture/cn-jp-ros2-absorb.md
# CYCLONEDDS_HOME 若已由 Nix/apt 装好则保留，不覆盖。

echo "chain B: RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION} ROS_DOMAIN_ID=${ROS_DOMAIN_ID}" >&2
echo "chain B: DimOS 原生 DDS 仍用 DDSConfig.domain_id=0（模块默认未改）" >&2
