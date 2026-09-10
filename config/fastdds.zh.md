# `fastdds.xml` 是契约种子（R2）

本目录的 [`fastdds.xml`](fastdds.xml) **不是**从 `topsun_dimos` `main` 抽出来的现网配置。DimOS main（`a5259958db23c8ea6648544ed138eab19726ce93`）没有 `fastdds.xml`，也没有 `docker/navigation/`，也没有 `FASTRTPS_DEFAULT_PROFILES_FILE`。

它只做一件事：把 R0 冻结表里的**链 A**落成可引用路径，方便后续对照，而不是假装已经在跑导航镜像。

## 冻结表对齐

| 项 | 值 |
|----|----|
| 链 | A — nav FastDDS |
| RMW | `rmw_fastrtps_cpp` |
| 域 | `ROS_DOMAIN_ID=42`（XML 里 `<domainId>42</domainId>` 与之一致） |
| topic QoS 种子 | `/foxglove_teleop`→`/cmd_vel`：BEST_EFFORT / KEEP_LAST / depth=1；`/goal_pose`、`/way_point`：RELIABLE / VOLATILE / KEEP_LAST / depth=5 |
| `/joy` | 只冻结名字，XML 不编造 QoS |

完整表见 [`docs/architecture/ros2-dds-r0-interface-freeze.md`](../docs/architecture/ros2-dds-r0-interface-freeze.md)。常量模块：[`topics.yaml`](topics.yaml)、[`dimos_bridge/dimos/protocol/dds_topics.py`](../dimos_bridge/dimos/protocol/dds_topics.py)。

## 怎么指向它

不要改 DimOS 拷贝代码去硬编码路径。操作员显式：

```bash
source config/env/chain_a.sh
# 导出 FASTRTPS_DEFAULT_PROFILES_FILE=<repo>/config/fastdds.xml
```

未 source 时，Humble 仍用发行版默认 RMW / 域 0——这是现状，不是本文件的静默生效。

iter2 在默认 participant 上加了 **一对** UDP socket buffer（send/listen 各 2 MiB）。这是大包 RTT 的**一个**旋钮，假设写在 `docs/artifacts/bench/2026-09-10-iter2-after/change.md`。不是现网证明。

iter3 在同一默认 participant 上加了 **一个** RTPS send-buffer 池（`preallocated_number` 32，`dynamic` true）。Humble Fast-DDS 2.6 默认 `preallocated_number=0`（按发送线程猜）、`dynamic=false`（池空就等）。1 MiB 大约 16 个 ~64 KiB 分片。不是 SHM，也不是第二个 socket-buffer 旋钮。SHM `maxMessageSize` 探测让 same-host 1 MiB 变慢，未保留。假设写在 `docs/artifacts/bench/2026-09-10-iter3/change.md`。不是现网证明。

iter4 保留 iter3 的 32 块 slab（这是 1 MiB 的赢面），把 `dynamic` 改成 **false**。Humble Fast-DDS 2.6.12 在池空且 dynamic=true 时会在热路径 `new` 一块 buffer；中包 Reliable 账上 +23–24%。32 通常够用时，短等比现场分配便宜。16 / 0 且 dynamic=true 的探测没挽回 mid-size；0 还把 1 MiB 赢面吃掉了，未保留。不是 SHM，也不是第二个 socket-buffer 旋钮。假设写在 `docs/artifacts/bench/2026-09-10-iter4/change.md`。不是现网证明。

iter5 只改默认 participant 为 **UDP-only**（关掉 builtin SHM）。Humble 隐式 SHM 段是 512 KiB。768 KiB SHM 探测挽回了 same-host BestEffort 256 KiB（1653 → 1309 µs），但 1 MiB BestEffort 从 80/80 掉成 1/80——同机走 SHM，段不够时不会退回 UDP，未保留。UDP-only 让中包走已经调过的 localhost UDP（iter2 2 MiB socket），不再顶 512 KiB SHM。`send_buffers` 32 / `dynamic=false` 不动。不是 iter3 那次不分片 SHM 探测。假设写在 `docs/artifacts/bench/2026-09-10-iter5/change.md`。不是现网证明。

Humble Fast-DDS 2.6 的 XMLPARSER **不接受** `<qos><history>`（2026-09-10 基线：`Invalid element ... Name: history`，`loadXMLFile` 失败）。History 写在 `<topic><historyQos>`，kind/depth 仍对齐冻结表。这不是传输层根因，也不改 `ddspubsub` / `rospubsub`。

## 不是什么

- 不是自定义 RMW
- 不是链 B（Cyclone 域 0）的配置
- 不是已测时延根因
