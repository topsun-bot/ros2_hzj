# 双链环境变量（R1 抽出）

这里只做**文档与显式 helper**。拷贝自 DimOS 的模块（`dimos_bridge/dimos/**`）**不会**在 import 时改环境变量，运行时默认值与 `topsun_dimos` 拷贝一致。

操作员要对齐某条链，必须自己 `source` 脚本，或调用 Python `apply_*`。

冻结表：[`docs/architecture/ros2-dds-r0-interface-freeze.md`](../../docs/architecture/ros2-dds-r0-interface-freeze.md)。  
不要把「设了这些变量」或「已 vendor」当成时延根因。混用链 A / 链 B 默认值是**发现失败**。

## 链 A — nav FastDDS

| 变量 | 契约值 | 说明 |
|------|--------|------|
| `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` | Humble 发行版默认也是它；这里显式钉扎 |
| `ROS_DOMAIN_ID` | `42` | 冻结表导航域。ROS 2 未设置时是 **0** |
| `FASTRTPS_DEFAULT_PROFILES_FILE` | 本仓 [`config/fastdds.xml`](../fastdds.xml) 的绝对路径 | 契约种子，不是 DimOS main 现网文件 |

```bash
# 在仓库根：
source config/env/chain_a.sh
# 或
python3 config/env/load.py print-a
python3 config/env/load.py apply-a   # 只对当前进程 os.environ；需 eval 才能进父 shell
eval "$(python3 config/env/load.py export-a)"
```

## 链 B — DimOS Cyclone / 域 0

DimOS 原生 DDS（`DDSTransport` → `ddspubsub` → `DDSService`）走 **cyclonedds Python**，`DDSConfig.domain_id` 默认 **0**。这**不是** RMW 环境变量；拷贝模块里已经写死默认 0，helper **不会**去改那个 dataclass。

若同一台机器上还要用 ROS 2 客户端对齐链 B（Unitree / `ChannelFactoryInitialize(0)`）：

| 变量 | 建议值 | 说明 |
|------|--------|------|
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp` | 仅当走 ROS 2 RMW；原生 DimOS DDS 不读这个 |
| `ROS_DOMAIN_ID` | `0` | 与 `DDSConfig.domain_id` / Unitree 域 0 对齐 |
| `CYCLONEDDS_URI` | （可选，默认不设） | 本仓不提供现网 Cyclone XML。Autoware 公开配方的**标签示例**在 [`scripts/bench/cyclonedds_autoware_like.xml`](../../scripts/bench/cyclonedds_autoware_like.xml)，须操作员自己 export；不是默认，不是 SCOREBOARD。对照 [cn-jp-ros2-absorb.md](../../docs/architecture/cn-jp-ros2-absorb.md) |
| `CYCLONEDDS_HOME` | 系统 / Nix 前缀 | 装 Python `cyclonedds` 时需要；见 [docs/usage/transports/dds.md](../../docs/usage/transports/dds.md) |

```bash
source config/env/chain_b.sh
eval "$(python3 config/env/load.py export-b)"
```

## 文件

| 文件 | 用途 |
|------|------|
| [`.env.example`](.env.example) | 可复制为 `.env`（已被 gitignore）；**不会**被代码自动加载 |
| [`chain_a.sh`](chain_a.sh) / [`chain_b.sh`](chain_b.sh) | `source` 用 |
| [`load.py`](load.py) | 打印 / export / 显式 apply |
| [`../../dimos_bridge/dual_chain_env.py`](../../dimos_bridge/dual_chain_env.py) | 给 Python 调用的薄包装，默认只读不 apply |
