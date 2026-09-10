# Shared helpers for scripts/bench/*.sh. Source only; do not execute.
# shellcheck shell=bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "source ${BASH_SOURCE[0]}  (do not execute)" >&2
  exit 1
fi

_bench_this="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROS2_HZJ_ROOT="$(cd "${_bench_this}/../.." && pwd)"
unset _bench_this

export PATH="${HOME}/.local/bin:${PATH}"

# UTC date directory (override with BENCH_DATE=YYYY-MM-DD)
BENCH_DATE="${BENCH_DATE:-$(date -u +%Y-%m-%d)}"
BENCH_ARTIFACT_ROOT="${ROS2_HZJ_ROOT}/docs/artifacts/bench/${BENCH_DATE}"

# Cyclone C library prefix used by the Python bindings on this host recipe.
# Does not change vendor trees or DimOS defaults.
if [[ -z "${CYCLONEDDS_HOME:-}" && -d /opt/cyclonedds ]]; then
  export CYCLONEDDS_HOME=/opt/cyclonedds
fi
if [[ -n "${CYCLONEDDS_HOME:-}" ]]; then
  export LD_LIBRARY_PATH="${CYCLONEDDS_HOME}/lib:${LD_LIBRARY_PATH:-}"
fi

bench_mkdir() {
  mkdir -p "$1"
}

bench_log() {
  printf '[bench] %s\n' "$*" >&2
}
