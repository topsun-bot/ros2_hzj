# vendor/

公开 ROS 2 RMW / Fast-DDS / CycloneDDS **完整源码树**的本仓拷贝。

双链都在本目录，都是普通目录，不是 submodule / subtree：

| 链 | 目录 |
|----|------|
| A — Fast-DDS | `rmw/`、`rmw_implementation/`、`rmw_fastrtps/`、`Fast-DDS/` |
| B — Cyclone | `rmw_cyclonedds/`、`CycloneDDS/` |

- 禁止 submodule / subtree 远端跟踪。
- 精确 SHA 见 [VERSIONS.md](VERSIONS.md)。
- **不**在 CI 里完整编译 Fast-DDS 或 CycloneDDS。
- 不要把 vendor 落盘当成时延根因。
