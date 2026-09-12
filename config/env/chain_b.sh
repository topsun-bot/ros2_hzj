# 链 B — Cyclone / 域 0。必须 source，不要直接执行。
# 原生 DimOS DDS 读的是 DDSConfig.domain_id（默认 0），不是这些 ROS 变量。
# 本脚本只为「要用 ROS 2 RMW 对齐链 B」的操作员准备。
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "source ${BASH_SOURCE[0]}  （不要直接执行）" >&2
  exit 1
fi

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0
# 对齐 load.py CHAIN_B_UNSET：默认清掉继承的 Cyclone 网络 XML。
# 本仓没有现网 Cyclone XML。CYCLONEDDS_HOME 若已由 Nix/apt 装好则保留，不覆盖。
unset CYCLONEDDS_URI

echo "chain B: RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION} ROS_DOMAIN_ID=${ROS_DOMAIN_ID}" >&2
echo "chain B: DimOS 原生 DDS 仍用 DDSConfig.domain_id=0（模块默认未改）" >&2
