# Vendor 清单（发行版 vs 快照）

本文件冻 **语义**：哪边是 Humble 运行时、哪边是对照用的 rolling / master 拷贝。  
**完整六行 SHA / 标签表只在 [VERSIONS.md](VERSIONS.md)，这里不抄。**

拷贝日期（与 VERSIONS 一致）：**2026-09-10**。  
查阅补记：2026-09-12（飞书《ROS 2 源码闭环》§13 第 1 步：冻 `ROS_DISTRO` + exact manifest）。

决策：[docs/architecture/feishu-middleware-adr.md](../docs/architecture/feishu-middleware-adr.md)。路径地图：[docs/architecture/ros2-source-map.md](../docs/architecture/ros2-source-map.md)。

---

## 目标运行时

| 面 | 钉扎 |
|----|------|
| 链 A Docker / 发行版 ROS | **Humble**（[`docker/ros/Dockerfile`](../docker/ros/Dockerfile) `ENV ROS_DISTRO=humble`，Ubuntu 22.04）。镜像**不**写 `RMW_IMPLEMENTATION` / `ROS_DOMAIN_ID` / `FASTRTPS_*`。 |
| 链 A 契约 RMW（运行时） | 发行版 `rmw_fastrtps_cpp`，域 **42**（操作员 `source` [`config/env/chain_a.sh`](../config/env/chain_a.sh)） |
| 链 B | 原生 Cyclone 域 **0**；ROS 侧名 `rmw_cyclonedds_cpp`。Cyclone **发行标签 11.0.1**（见 VERSIONS，不要用拷贝当日 `master` HEAD） |
| 本仓 `vendor/` 树 | **rolling**（`rmw` / `rmw_implementation` / `rmw_fastrtps` / `rmw_cyclonedds`）与 Fast-DDS **`master`** 快照，按 VERSIONS 浅克隆后去 `.git` |

未发明自定义 RMW。未使用 git LFS。CI **不**编译这些树。

---

## 严禁：Rolling 覆盖 Humble

vendor 里的 `package.xml` 版本（例如 `rmw` `7.11.2`、`rmw_fastrtps_cpp` `9.5.2`、Fast-DDS `master`）**大于** Humble 发行版对应包。这是**对照阅读快照**，不是 Humble overlay。

**不要**把 `vendor/rmw/**`、`vendor/rmw_fastrtps/**`、`vendor/Fast-DDS/**` 或其它 rolling / master 文件直接铺进 `/opt/ros/humble` 或 Humble 工作区，除非经过**语义 backport**（另开 PR，写明 ABI / 行为差）。混用会把「对照源码」伪装成「正在跑的发行版」。

运行时「到底加载了谁」以进程里的 `.so` / `rmw_get_implementation_identifier` 为准，不是以本目录文件为准。用 [`scripts/prove_rmw.py`](../scripts/prove_rmw.py)。

---

## 树索引（无 SHA）

| 链 | 目录 | 上游策略（细节在 VERSIONS） |
|----|------|------------------------------|
| A | `rmw/` `rmw_implementation/` `rmw_fastrtps/` `Fast-DDS/` | rolling / Fast-DDS `master` |
| B | `rmw_cyclonedds/` `CycloneDDS/` | rolling + Cyclone tag **11.0.1** |

DimOS 双链拷贝不在本目录：[dimos_bridge/SOURCE.md](../dimos_bridge/SOURCE.md)。
