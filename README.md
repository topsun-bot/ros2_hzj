# ros2_hzj

Independent ROS 2 / DDS workstream for topsun-bot (桦之坚).

**Delivery target:** this repository, [`topsun-bot/ros2_hzj`](https://github.com/topsun-bot/ros2_hzj).

**Not** [`topsun_dimos`](https://github.com/topsun-bot/topsun_dimos). Do not land ROS 2 / DDS work there unless a later request says otherwise.

Behavior is **unchanged** unless a later request explicitly asks for a runtime, env, topic, QoS, or middleware change. This R0 seed is documentation and skeleton only.

## Dual-chain contract

These are **two stacks**. They do not share a domain, RMW, or QoS profile unless an operator explicitly aligns them.

| Chain | Role | Contract |
|-------|------|----------|
| **A — nav FastDDS** | Navigation / Foxglove / ROS 2 RMW | RMW `rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`, `fastdds.xml` |
| **B — DimOS Cyclone** | DimOS native DDS / Unitree | Cyclone domain **0**; Unitree Cyclone path as documented in the freeze |

DimOS default transport is **LCM** (Linux) / **SHM** (Darwin). **LCM is out of DDS scope for this repo.**

## R0 documents

| Doc | Path |
|-----|------|
| Interface freeze (dual-chain map, frozen topics/QoS, gates) | [`docs/architecture/ros2-dds-r0-interface-freeze.md`](docs/architecture/ros2-dds-r0-interface-freeze.md) |
| Chain B Cyclone install notes (DimOS `dds` extra; reference only) | [`docs/usage/transports/dds.md`](docs/usage/transports/dds.md) |
| Transports overview + discoverability pointer | [`docs/usage/transports/index.md`](docs/usage/transports/index.md) |

Source of those three files: `topsun_dimos` PR [#122](https://github.com/topsun-bot/topsun_dimos/pull/122) (`cursor/ros2-dds-r0-interface-freeze-667f`). Content is faithful; light edits only retarget repo names and drop DimOS-only CI/path assumptions.

## Out of scope (R0)

- No public ROS 2 / rmw / Fast-DDS **subtree or submodule** in this repo.
- No **custom RMW** in R0. Use distro `rmw_fastrtps_cpp` (Chain A) and documented Cyclone (Chain B).
- No ROS 2 build, `apt install ros-*`, or vendor tree.
- **R1 and later workstreams are Hold** (env extract, externalize `fastdds.xml`, Dockerfile split, topic constants, middleware patches, eval / latency / security).

## License

[MIT](LICENSE). The R0 freeze does not mandate a license; MIT is the default for this independent repo.

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) only checks that the R0 markdown paths exist and that in-repo relative links among those docs resolve. It does **not** build ROS 2.
