# Transports

This repo's transport contract is **ROS 2 / DDS** (two stacks). The DimOS LCM tutorial that used to live here — site-root `/docs` and `/dimos` links, `docs/assets/` figures, LCM / SHM / Redis examples — is not in this tree. LCM stays DimOS's default in `topsun_dimos` and is **out of DDS scope**.

Use these pages instead:

| Page | What it is |
|------|------------|
| [R0 interface freeze](../../architecture/ros2-dds-r0-interface-freeze.md) | Dual-chain map, frozen topics / QoS, LCM out of scope |
| [dds.md](dds.md) | Chain B Cyclone install notes |
| [benchmark-dds.md](../benchmark-dds.md) | How to run benches (no scores) |

Chain A Fast-DDS participant defaults (domain 42, `shm_midsize`, socket / send-buffer knobs) live in [`config/fastdds.xml`](../../../config/fastdds.xml). A dual-chain **subset** is under [`dimos_bridge/`](../../../dimos_bridge/).
