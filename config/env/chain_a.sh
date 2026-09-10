# 链 A — nav FastDDS。必须 source，不要直接执行。
# 不改变 DimOS 拷贝模块的默认值；只导出当前 shell 的环境变量。
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "source ${BASH_SOURCE[0]}  （不要直接执行）" >&2
  exit 1
fi

_ROS2_HZJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=42
export FASTRTPS_DEFAULT_PROFILES_FILE="${_ROS2_HZJ_ROOT}/config/fastdds.xml"
unset _ROS2_HZJ_ROOT

echo "chain A: RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION} ROS_DOMAIN_ID=${ROS_DOMAIN_ID}" >&2
echo "chain A: FASTRTPS_DEFAULT_PROFILES_FILE=${FASTRTPS_DEFAULT_PROFILES_FILE}" >&2
