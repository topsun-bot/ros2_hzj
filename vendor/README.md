# vendor/

公开 ROS 2 RMW / Fast-DDS / CycloneDDS **完整源码树**的本仓拷贝。索引页；钉扎表只在 [VERSIONS.md](VERSIONS.md)。

| 链 | 目录 |
|----|------|
| A — Fast-DDS | `rmw/`、`rmw_implementation/`、`rmw_fastrtps/`、`Fast-DDS/` |
| B — Cyclone | `rmw_cyclonedds/`、`CycloneDDS/` |

- 普通目录，禁止 submodule / subtree 远端跟踪。
- **不**在 CI 里完整编译 Fast-DDS 或 CycloneDDS。
- 不要把 vendor 落盘当成时延根因。
- DimOS 拷贝不在本目录，见 [`../dimos_bridge/SOURCE.md`](../dimos_bridge/SOURCE.md)。
