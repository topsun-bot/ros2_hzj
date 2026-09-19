# 《1》DDS 代码流走查（ros2_hzj 双链工作区）

Status: **走查笔记 — 不是复现报告、不是时延数字、不是飞书现场证明。**
范围：本仓 `/Users/zhang/colima-work/ros2_hzj`（TOPSUN / 桦之坚独立 ROS 2 / DDS 双链工作区，**不是** `topsun_dimos`）。
本机无 ROS runtime（`rclpy` 不可 import、无 `/opt/ros`）；本文所有 `scripts/check_*.py` 在本机均 exit 0，它们是**文件系统 / 环境字符串检查，不是端到端**。
边界遵守 [AGENTS.md](../../AGENTS.md)：不动 `config/fastdds.xml`、不动 `docs/artifacts/bench/SCOREBOARD.md` 数字、不启用 Agnocast/zenoh/Cega、不改 `dimos_bridge` 运行时 DDS 行为、不编译 vendor。

飞书 4 篇输入在本次走查时**全部返回 3380004 无权限**（无法读取正文），本文按仓库内已合入的派生文档与实际 grep 证据撰写，不编造飞书原文：
1. 《通信中间件》 <https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe> — **无法读取**
2. Cyclone 工业级 fork 研究 <https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e> — **无法读取**
3. 《ROS 2 源码闭环》 <https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf> — **无法读取**
4. ros2 问题清单（《2》输入） <https://topsunhzj.feishu.cn/docx/CsjGd7DqNoiU4mxT2KdcWBjFntg> — **无法读取**

---

## 0. 一句话全局图

```
应用 (app)  ──写 rclpy / ROSTransport / DDSTransport──▶  rcl (Humble, 不在本仓)
        │
        ▼
rmw  ──RMW_IMPLEMENTATION 装载──▶  链A rmw_fastrtps_cpp / 链B rmw_cyclonedds_cpp
        │
        ▼
DDS  ──链A Fast-DDS 域42 / 链B Cyclone 域0
        │
        ▼ (收包在 DDS 线程，早于用户 callback)
Reader History  ──rmw_wait / WaitSet──▶  rmw_take / dds_take ──▶ 用户 callback
```

关键诚实前提（来自 [ros2-source-map.md](../architecture/ros2-source-map.md)）：
**`publish()` / `rmw_publish()` 返回 `RMW_RET_OK` ≠ 对端已投递、已入 History、已 callback。** 那只是本进程把样本交给了 DataWriter / `dds_write_*`。入 History ≠ callback 已跑。端到端要另走 wait → take → executor。

---

## 1. 六层模块职责划分（app / rcl / rmw / DDS / executor / memory）

对照 [feishu-sink-layers.md](../architecture/feishu-sink-layers.md) §1 与 [ros2-source-map.md](../architecture/ros2-source-map.md)。本表只标**本树里核对过存在**的路径；链 A 用 Fast-DDS（域 **42**），链 B 用 Cyclone（域 **0**），两条独立栈，混用默认值是 discovery 失败，不是单栈时延 bug。

| 层 | 本仓职责与落点 | 本仓有 / 没有 | Hold vs allowed |
|----|----------------|---------------|-----------------|
| **app** | 应用继续写 `rclpy` / `ROSTransport` / `DDSTransport`。传输抽象 [`dimos_bridge/dimos/core/transport.py`](../../dimos_bridge/dimos/core/transport.py)；链 A 桥 [`.../impl/rospubsub.py`](../../dimos_bridge/dimos/protocol/pubsub/impl/rospubsub.py)；链 B 原生 [`.../impl/ddspubsub.py`](../../dimos_bridge/dimos/protocol/pubsub/impl/ddspubsub.py)。topic 常量 [`dimos_bridge/dimos/protocol/dds_topics.py`](../../dimos_bridge/dimos/protocol/dds_topics.py)、[`config/topics.yaml`](../../config/topics.yaml)；双链开关 [`config/env/load.py`](../../config/env/load.py)、[`config/env/chain_a.sh`](../../config/env/chain_a.sh)、[`config/env/chain_b.sh`](../../config/env/chain_b.sh) | 有（拷贝 + 契约） | Allowed：继续用现有应用 API + `config/env` 显式切链。**Hold：** 改 `dimos_bridge` DDS 行为、module 双堆 |
| **rcl** | `rcl_publish` / executor 封装 | **没有** vendor `rcl` / `rclcpp` / `rclpy`。在 Humble 发行版 `/opt/ros/humble`（[`docker/ros/`](../../docker/ros/) `ROS_DISTRO=humble`） | **Hold：** 不 vendor `rcl*`；rolling 覆盖 Humble = 严禁 |
| **rmw** | RMW 声明对照 [`vendor/rmw/rmw/include/rmw/rmw.h`](../../vendor/rmw/rmw/include/rmw/rmw.h)；装载 [`vendor/rmw_implementation/.../functions.cpp`](../../vendor/rmw_implementation/rmw_implementation/src/functions.cpp) `load_library()` 读 `RMW_IMPLEMENTATION`；链 A [`vendor/rmw_fastrtps/`](../../vendor/rmw_fastrtps/)（`rmw_fastrtps_cpp`）；链 B [`vendor/rmw_cyclonedds/`](../../vendor/rmw_cyclonedds/)（`rmw_cyclonedds_cpp`） | 有（只读快照） | Allowed：`RMW_IMPLEMENTATION` + `config/env` 切换已有实现；`prove_rmw.py` 证明加载了谁。**Hold：** 自研 RMW、`rmw_zenoh` |
| **DDS** | 链 A [`vendor/Fast-DDS/`](../../vendor/Fast-DDS/)（master 快照）+ 只读种子 [`config/fastdds.xml`](../../config/fastdds.xml)；链 B [`vendor/CycloneDDS/`](../../vendor/CycloneDDS/) tag **11.0.1** | 有（只读快照） | **Hold：** 不改 `fastdds.xml` / SCOREBOARD；Unitree 0.10.2 vs vendor 11.0.1 = drop-in FAIL |
| **executor** | Humble `rclcpp::Executor` / `rclpy.executors` | **不在 vendor。** 本仓只到 `rmw_wait` / `rmw_take`；身份地图见 [feishu-executor-waitset.md](../architecture/feishu-executor-waitset.md) | Allowed：身份地图 + `check_executor_map.py`。**Hold：** 不 fork Executor |
| **memory** | Loaned / Data Sharing / Iceoryx 对照 | 只对照；Cyclone 快照带 PSMX 适配源码（`vendor/CycloneDDS/src/psmx_iox/`）但本仓**没有** `vendor/iceoryx`，CI 不编 vendor | **Hold：** 零拷不落地；AUTO ≠ 已开零拷 |

### 1.1 三条链的实际代码流（publish / ingress→History / wait→callback）

来源 [ros2-source-map.md](../architecture/ros2-source-map.md)，本仓只画地图、**未复现**（见 §3 陷阱 3）。

- **publish 链**：`app.publish` → `rclpy/rcl`（发行版，不在本仓）→ `rmw_publish`（经 `rmw_implementation` 跳具体 `.so`）。
  - 链 A：[`vendor/rmw_fastrtps/.../rmw_publish.cpp`](../../vendor/rmw_fastrtps/rmw_fastrtps_cpp/src/rmw_publish.cpp) → shared `__rmw_publish` → Fast-DDS `DataWriterImpl.write_w_timestamp` → `DataWriterHistory.add_pub_change` / `WriterHistory.add_change`。
  - 链 B：[`vendor/rmw_cyclonedds/.../rmw_node.cpp`](../../vendor/rmw_cyclonedds/rmw_cyclonedds_cpp/src/rmw_node.cpp) `rmw_publish` → `dds_write_ts`（[`vendor/CycloneDDS/.../dds_write.c`](../../vendor/CycloneDDS/src/core/ddsc/src/dds_write.c)）→ `ddsi_whc_insert`（[`ddsi_whc.c`](../../vendor/CycloneDDS/src/core/ddsi/src/ddsi_whc.c)）。
- **ingress→History 链**：收包在 **DDS 线程**，早于 ROS callback。链 A `StatefulReader.change_received` → `ReaderHistory.received_change/add_change`；链 B `rhc_store` → `ddsi_rhc.c` / `dds_rhc.c`。入 History ≠ callback 已跑。
- **wait→callback 链**：Humble executor 循环 `rmw_wait`（链 A `WaitSet`/`GuardCondition`/`get_first_untaken_info`；链 B `dds_waitset_attach`）→ `rmw_take`（链 A `__rmw_take`；链 B `dds_take`/`dds_read.c`）→ 订阅回调。**DimOS 原生链 B 不走 ROS executor**：[`ddspubsub.py`](../../dimos_bridge/dimos/protocol/pubsub/impl/ddspubsub.py) 的 `_DDSMessageListener.on_data_available`（L73）里 `reader.take()`（L76）再分发用户 callback，这是 DDS listener，不是 `rclpy.executors`。

### 1.2 本仓"真正在跑的代码"其实分两类

1. **我们自己的脚本与契约（可维护、是本次重构对象）**：`scripts/*.py` 闸门、`config/env/load.py`、`config/env/chain_*.sh`、`dimos_bridge/dual_chain_env.py`、`docs/`。
2. **只读拷贝 / 快照（不可改）**：`dimos_bridge/dimos/**`（[整文件拷贝自 topsun_dimos main @ a5259958](../../dimos_bridge/SOURCE.md)）、`vendor/**`（rolling/master 快照）。

---

## 2. 数据在哪些地方做校验（prove_rmw.py 与 check_*.py 强制了什么假设）

本机无 ROS，下列闸门我已逐个跑过，**全部 exit 0**（基线）。它们强制的是**结构 / 字符串 / 路径存在**假设，不是行为假设。本地 runner [`scripts/run_all_gates.py`](../../scripts/run_all_gates.py) 现一把跑 **13 个 gate**（含轮次 4 新增的冻结路径防回潮闸，见 §2.4）；GitHub CI 的 `structure` job 目前仍只枚举前 **12** 个——第 13 个的 ci.yml 接线因推送账号缺 `workflow` scope 而离线待补（见 [ci-cd-gates.md](../architecture/ci-cd-gates.md) §6 与 [ITERATION_LOG.md](ITERATION_LOG.md) 轮次 4/9），这不影响本地红绿，只意味着该闸暂不在 required checks 里。

### 2.1 身份闸：`scripts/prove_rmw.py`

[`scripts/prove_rmw.py`](../../scripts/prove_rmw.py)（飞书 wiki3 §6.3）打印 `ROS_DISTRO` / `RMW_IMPLEMENTATION` / `ROS_DOMAIN_ID` / `FASTRTPS_DEFAULT_PROFILES_FILE` / `CYCLONEDDS_URI`，若 `rclpy` 可 import 再读 `get_rmw_implementation_identifier()`，并在搜索路径上找 `librmw_*.so` 跑 `ldd`。
- **它强制的假设**：`RMW_IMPLEMENTATION` 环境变量是"请求"；进程真正链接谁看 identifier。无 ROS 时打印 `ROS not loaded` 并 exit 0。
- **它证明不了**（[feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md) §3）：加载的是改过的 `.so` 还是发行版 underlay；这些 `.so` 来自本仓 overlay 还是补丁。**它是 env / 字符串身份闸，不是 modified `.so` 证明。**

### 2.2 结构闸：每个 `check_*.py` 打开一组文件并断言"标记仍在"

> 轮次 1/2/5 起，闸门**不再各自复制**路径常量、repo-root 查找、UTF-8 读取与 markdown 解析，
> 这些收敛进三个下划线前缀共享库（不进 CI 枚举、不被 runner 直接跑）：
> [`_freeze_paths.py`](../../scripts/_freeze_paths.py)（两条冻结路径与 existence hint 的单一真源）、
> [`_repo.py`](../../scripts/_repo.py)（`repo_root()` 多锚点查找 + lenient `read_utf8()`）、
> [`_md_paths.py`](../../scripts/_md_paths.py)（source/executor 两闸共用的 md 引用解析、符号查找、WARN-FAIL 渲染）。
> 每个闸的**业务断言 / 必需标记 / allowlist 仍归各自脚本**，helper 不承载业务断言。

| 闸门 | 强制的核心假设（断言什么字符串 / 路径） | 若红意味着 |
|------|------------------------------------------|------------|
| [`check_source_map.py`](../../scripts/check_source_map.py) | 只解析 [ros2-source-map.md](../architecture/ros2-source-map.md)：引用的本仓路径存在；允许清单符号仍在（`add_change`/`change_received`/`__rmw_publish`/`__rmw_wait`/`dds_waitset_attach`/`dds_take` 等，见脚本 L22–71）。行号过期只 WARN | 地图指向的 vendor 文件或符号被删 → 地图失真 |
| [`check_executor_map.py`](../../scripts/check_executor_map.py) | WaitSet→`rmw_wait`→take→callback 身份地图；`ddspubsub.py` 含 `on_data_available`、`rospubsub.py` 含 executor 符号；Humble `rcl*` 仍未 vendor | executor 地图失真 |
| [`check_sink_layers.py`](../../scripts/check_sink_layers.py) | 六层（app/rcl/rmw/DDS/executor/memory）Hold vs allowed 标记、`不改 config/fastdds.xml / SCOREBOARD`、不接 Agnocast/zenoh、`map ≠ reproduce`、`drop-in FAIL` | 层表 / 策略句被改 |
| [`check_dual_chain_baseline.py`](../../scripts/check_dual_chain_baseline.py) | `no XML rewrite`、SCOREBOARD `pointer only`、连续句 `same-topology XML tuning is paused`；[`chain_a.sh`](../../config/env/chain_a.sh) 锚定 `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`/`ROS_DOMAIN_ID=42`/`FASTRTPS_DEFAULT_PROFILES_FILE=…fastdds.xml`；[`chain_b.sh`](../../config/env/chain_b.sh) 锚定 `rmw_cyclonedds_cpp`/`ROS_DOMAIN_ID=0`/`unset CYCLONEDDS_URI`。轮次 3 起再用 importlib 加载 [`load.py`](../../config/env/load.py) 做 **env 单一真源交叉断言**：load.py `CHAIN_A/B` 为真值、与 chain_a/b.sh 字面 export 逐项相等、与 [`dual_chain_env.py`](../../dimos_bridge/dual_chain_env.py) 包装相等，且 import 前后 `os.environ` 不变（import 纯净） | 双链契约字符串被改、三处真源漂移、或 import 污染环境 |
| [`check_unitree_cyclone_swap.py`](../../scripts/check_unitree_cyclone_swap.py) | 连续裁决句 `drop-in FAIL / wire UNPROVEN`；[`vendor/VERSIONS.md`](../../vendor/VERSIONS.md) 同行有 `vendor/CycloneDDS/`+`11.0.1`+SHA `e54e991f…`；[`vendor/CycloneDDS/CMakeLists.txt`](../../vendor/CycloneDDS/CMakeLists.txt) `project(CycloneDDS … VERSION 11.0.1 …)` | 版本钉扎被改 |
| [`check_three_chain_repro.py`](../../scripts/check_three_chain_repro.py) | `map ≠ reproduce`、`STATUS: blocked`，不得写成 PASS/PROVEN | 把地图冒充成已复现 |
| [`check_dod_evidence.py`](../../scripts/check_dod_evidence.py) | 连续 `DoD: unmet`、`STATUS: blocked`、五项未满足、`prove_rmw`=env/字符串 | 把文档闸绿冒充成 §6.3 产品验收 |
| [`check_cega_bridge_hold.py`](../../scripts/check_cega_bridge_hold.py) | `STATUS: Hold`、`no Cega`、连续句 `no dimos_bridge runtime edits this cut`、`no XML/SCOREBOARD`；并**只检查存在**下表 8 个 `dimos_bridge` 运行时 `.py`（见脚本 L102–110） | Cega/Bridge 边界被破 |
| [`check_runtime_provenance.py`](../../scripts/check_runtime_provenance.py) | underlay(`/opt/ros/humble`) ≠ overlay ≠ vendor snapshot；Humble 钉扎、VERSIONS 六行 SHA 表还在 | 运行时分层被混淆 |
| [`check_risk_matrix.py`](../../scripts/check_risk_matrix.py) | §9.4 层序（env/XML→RMW→DDS knobs→Executor/memory→core fork）、Hold 标记；**不打风险分** | 层序被改 |
| [`print_bench_gates.py`](../../scripts/print_bench_gates.py) | SCOREBOARD / bench README 指针存在、含 `STATUS`；**不打印分位数** | bench 指针失效 |
| [`check_frozen_path_literals.py`](../../scripts/check_frozen_path_literals.py)（**第 13 闸，轮次 4**） | 静态扫 `scripts/` 顶层 `*.py`，禁止在真源 `_freeze_paths.py` 外用 `Path(...)` 二次硬编码两条冻结路径（防 Step 2 去重回潮）；豁免真源与自身，只拦"第二份路径构造"不拦 prose 提及 / `endswith` / 正则 | 有人重新引入独立的 `Path("config/fastdds.xml")` 拷贝 |

**`config/fastdds.xml` 与 `docs/artifacts/bench/SCOREBOARD.md` 在所有脚本里都是"只检查存在"**，内容冻结由 CI `boundary` job 管（[ci-cd-gates.md](../architecture/ci-cd-gates.md)）。改这两份内容 → PR 上 `boundary` 红（除非人类加 `allow-hold-bypass` 标签，Agent 不得自贴）。

### 2.3 契约闸：`config/env/load.py print-a / print-b`

[`config/env/load.py`](../../config/env/load.py) 是双链环境的**唯一真源**（[`dual_chain_env.py`](../../dimos_bridge/dual_chain_env.py) 只是它的 importlib 薄包装，L12–20 重新导出 `CHAIN_A/CHAIN_B`）。`print-a` → `rmw_fastrtps_cpp / 42 / FASTRTPS_DEFAULT_PROFILES_FILE=…/config/fastdds.xml`；`print-b` → `rmw_cyclonedds_cpp / 0`（且 `unset CYCLONEDDS_URI`）。
- **关键假设**：`import load.py` **不写** `os.environ`；操作员必须显式 `source chain_a.sh` 或 `eval "$(… export-a)"` / `apply-a`。未 source 就假设"域 42 已生效"是错的。

### 2.4 一致性与回归工具链（重构轮次 1–9 引入）

闸门之上叠了三层互补的本地回归，改任何 `scripts/*.py` 都应理解它们的分工（演进记录见 [ITERATION_LOG.md](ITERATION_LOG.md)，计划见 [02-modernization-plan.md](02-modernization-plan.md)）：

1. **红绿层** [`scripts/run_all_gates.py`](../../scripts/run_all_gates.py)：数据驱动跑 13 个 `(script, marker)`，只看退出码 + 一个健康 marker，结尾打印 `all gates green`。
2. **契约层** Promptfoo（[`evals/promptfooconfig.yaml`](../../evals/promptfooconfig.yaml) + custom provider [`localScriptProvider.mjs`](../../evals/localScriptProvider.mjs)，用法见 [`evals/README.md`](../../evals/README.md)）：跑 gate 脚本与 `load.py print-a/print-b`，对 stdout 做 `contains` **实质契约**断言——不只锁 marker，还锁裁决句 / blocked 诚实性 / Hold 短语 / 双链真值，防止"marker 还在但结论被翻转"。现 **17 个用例**，本地命令固定 `npx --yes promptfoo@0.123.1 eval -c evals/promptfooconfig.yaml`。
3. **指纹层（严格）** [`evals/fingerprint_check.py`](../../evals/fingerprint_check.py)（eval 用例 #17，**eval-only、不是第 14 个 gate**）：import `run_all_gates.GATES` 单一真源 + `load.py print-a/b` 共 15 个命令，完整 stdout 归一化后与 [`evals/fixtures/`](../../evals/fixtures/)（15 份基线）**逐字节**比对，漂移打 unified diff 并 exit 1。归一化只抹平仓库根绝对路径与 frozen gate 的动态扫描计数，其余计数（cited/symbol 数等）保持精确。**任何有意改动 gate stdout，都必须在同一 PR 跑 `python3 evals/fingerprint_check.py --update` 重生成并提交 fixtures**，否则 #17 红。

> **CI 现状（如实标注）**：required checks 为 `structure` / `contracts` / `boundary`。`structure` 目前只枚举跑前 12 个 gate（第 13 个 frozen gate 的 ci.yml 接线因推送 token 缺 `workflow` scope 离线待补）；Promptfoo 与指纹回归**只在本地 / 本循环运行，CI 不跑**。因此"本地 13 gate + 17 eval 全绿"不等于 PR 上跑了同样的集合——接线缺口与解除条件见 [ci-cd-gates.md](../architecture/ci-cd-gates.md) §6。

---

## 3. 改前最需要注意的主要陷阱

### 陷阱 1：Unitree Cyclone 0.10.2 ≠ vendor 11.0.1（drop-in FAIL / wire UNPROVEN）
[unitree-sdk2-dds-swap.md](../architecture/unitree-sdk2-dds-swap.md)：Unitree SDK2 自带 Cyclone **0.10.2**（`libddsc.so.0`，SOVERSION 0），本仓 vendor 是 **11.0.1**（CMake `SOVERSION` = major 11）。把 11.0.1 拷进 Unitree `thirdparty/lib/**` 去换 0.10.2 = **ABI 不兼容，FAIL**。线缆互通 = **UNPROVEN**。默认永远 bundled 0.10.2；合法换库走独立仓 `unitree_sdk2_hzj` + opt-in `UNITREE_DDS_PROVIDER=external`（且要整树重编，不是拷 `.so`）。DimOS Python 绑定是 `cyclonedds>=0.10.5`，属 0.10.x 家族，**不是** 11.0.1。

### 陷阱 2：Humble ≠ rolling（vendor 不是运行时）
[feishu-runtime-provenance.md](../architecture/feishu-runtime-provenance.md)：进程真正链接的是 underlay `/opt/ros/humble`（[`docker/ros/Dockerfile`](../../docker/ros/Dockerfile) `ENV ROS_DISTRO=humble`）。`vendor/**` 是 rolling / master **快照**（`rmw` 7.11.2、`rmw_fastrtps` 9.5.2、Fast-DDS master、Cyclone 11.0.1），**严禁**直接铺进 `/opt/ros/humble`。拿 vendor 路径当"正在跑的库"是错的；身份只认 `prove_rmw.py`。

### 陷阱 3：three-chain = map ≠ reproduce（本主机 blocked）
[feishu-three-chain-repro.md](../architecture/feishu-three-chain-repro.md)：本自动化主机**没有** `/opt/ros/humble`、没有已加载 `librmw_*.so`、没起节点。三条链只是**地图**，未复现。把 `check_source_map.py` / `check_executor_map.py` exit 0 写成"三条链已跑通"= 编造。`publish()` 返回 OK ≠ 端到端送达。

### 陷阱 4：DoD honesty（文档闸绿 ≠ 产品验收）
[feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md)：产品 DoD 五项（改过的库实编 / modified `.so` 已加载 / 本机 baseline-vs-change / 回滚证明 / 产品验收阈）**全部 `DoD: unmet` / `STATUS: blocked`**。`prove_rmw.py` 是 env/字符串闸，不是 modified `.so` 证明。禁止发明分位数 / 本机 delta / PASS / PROVEN；禁止声称本机存在过 Humble 运行时。

### 陷阱 5：本仓是"文档 + 闸门"工作区，不是可运行 ROS 工程
`dimos_bridge/dimos/core/stream.py`、`dimos/msgs/protocol.py` 等 25 个文件是 **ImportError stub**（`raise ImportError`），仅为包路径可导航。因此 [`transport.py`](../../dimos_bridge/dimos/core/transport.py) L24 `from dimos.core.stream import …` 在本仓**无法 import 成功**——这是预期，不是 bug。不要试图在本机 `import dimos.core.transport` 跑通它；完整运行时在只读上游 `topsun_dimos`。

---

## 4. 下一步该读的文件列表（按阅读顺序）

1. [AGENTS.md](../../AGENTS.md) — 本页纸：双链、Hold 边界、13 条命令。
2. [docs/architecture/feishu-middleware-adr.md](../architecture/feishu-middleware-adr.md) — 三份飞书计划 → 本仓已决（决策总览）。
3. [docs/architecture/ros2-source-map.md](../architecture/ros2-source-map.md) — publish / ingress→History / wait→callback 三条链**地图**。
4. [docs/architecture/feishu-executor-waitset.md](../architecture/feishu-executor-waitset.md) — wait→callback / WaitSet / executor 身份地图（链 B 原生走 listener）。
5. [docs/architecture/feishu-sink-layers.md](../architecture/feishu-sink-layers.md) — app/rcl/rmw/DDS/executor/memory 六层 Hold vs allowed。
6. [docs/architecture/feishu-runtime-provenance.md](../architecture/feishu-runtime-provenance.md) — underlay / overlay / vendor snapshot 三层。
7. [docs/architecture/feishu-dual-chain-baseline.md](../architecture/feishu-dual-chain-baseline.md) — 链 A / 链 B 契约、SCOREBOARD pointer only。
8. [docs/architecture/feishu-three-chain-repro.md](../architecture/feishu-three-chain-repro.md) · [feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md) — 为什么 map ≠ reproduce / DoD unmet。
9. [docs/architecture/unitree-sdk2-dds-swap.md](../architecture/unitree-sdk2-dds-swap.md) — 0.10.2 vs 11.0.1 drop-in FAIL。
10. [docs/architecture/feishu-cega-bridge-hold.md](../architecture/feishu-cega-bridge-hold.md) — §13(4) Cega/Bridge Hold；§3 列出**只读**的 dimos_bridge 运行时文件清单。
11. [vendor/MANIFEST.md](../../vendor/MANIFEST.md) · [vendor/VERSIONS.md](../../vendor/VERSIONS.md) — vendor 语义与六行 SHA。
12. [config/env/load.py](../../config/env/load.py) · [config/env/chain_a.sh](../../config/env/chain_a.sh) · [config/env/chain_b.sh](../../config/env/chain_b.sh) — 双链环境真源。
13. [scripts/prove_rmw.py](../../scripts/prove_rmw.py) · [scripts/check_source_map.py](../../scripts/check_source_map.py) · [scripts/check_executor_map.py](../../scripts/check_executor_map.py) — 看闸门到底断言什么。
14. [docs/architecture/ci-cd-gates.md](../architecture/ci-cd-gates.md) — `structure`/`contracts`/`boundary` 三个 required job 与 `allow-hold-bypass`。
15. 一致性/回归工具链：[`scripts/run_all_gates.py`](../../scripts/run_all_gates.py)（13 gate runner）· [`scripts/_freeze_paths.py`](../../scripts/_freeze_paths.py) / [`_md_paths.py`](../../scripts/_md_paths.py) / [`_repo.py`](../../scripts/_repo.py)（共享 helper）· [`evals/README.md`](../../evals/README.md) 与 [`evals/fingerprint_check.py`](../../evals/fingerprint_check.py)（契约 + 指纹回归）；演进与每轮实测见 [ITERATION_LOG.md](ITERATION_LOG.md)。

---

## 5. 明确回答四问

### 问 1：业务逻辑模块 vs 传输层 vs UI 层，各在哪？
- **业务逻辑模块**：不在本仓。本仓只有应用层传输绑定与契约，没有机器人业务决策逻辑。最接近的是 [`dimos_bridge/dimos/robot/unitree/...`](../../dimos_bridge/dimos/robot/unitree/)（如 G1 高阶 [`dds_sdk.py`](../../dimos_bridge/dimos/robot/unitree/g1/effectors/high_level/dds_sdk.py)，526 行，链 B 域 0），且是只读拷贝。
- **传输层**：[`dimos_bridge/dimos/core/transport.py`](../../dimos_bridge/dimos/core/transport.py)（`PubSubTransport`/`ROSTransport`/`DDSTransport`/`ZenohTransport` 空 stub）→ [`.../impl/rospubsub.py`](../../dimos_bridge/dimos/protocol/pubsub/impl/rospubsub.py)（链 A，`SingleThreadedExecutor`）→ [`.../impl/ddspubsub.py`](../../dimos_bridge/dimos/protocol/pubsub/impl/ddspubsub.py)（链 B 原生，Cyclone listener）→ [`.../service/ddsservice.py`](../../dimos_bridge/dimos/protocol/service/ddsservice.py)（共享 `DomainParticipant` 池）。再往下才是 rmw / DDS（vendor 快照）。
- **UI 层**：本仓**没有** UI 层（无 Foxglove viewer —— 已在 [SOURCE.md](../../dimos_bridge/SOURCE.md) §"已删"里列为死代码删除）。配置/可见性只有 `config/topics.yaml` 与 `docs/`。

### 问 2：校验在哪？强制了什么假设？
校验**不在运行时代码里**，而在仓外的闸门脚本（§2）：`prove_rmw.py` 强制"加载身份以进程 identifier 为准、env 只是请求"；各 `check_*.py` 强制"地图/分层/契约/版本钉扎/Hold 标记的字符串与路径仍在"；`load.py print-a/b` 强制双链 RMW/域/XML 字符串。它们**共同强制的假设**是：(a) 链 A=`rmw_fastrtps_cpp`/域42、链 B=`rmw_cyclonedds_cpp`/域0；(b) vendor 是对照快照不是运行时；(c) 三条链与 DoD 未复现/未验收；(d) XML/SCOREBOARD 冻结。**没有任何一个脚本做端到端时延或投递校验**。

### 问 3：改动后易被忽略的关联文件 / 后台任务？
- **改了引用路径或符号名** → [`check_source_map.py`](../../scripts/check_source_map.py) / [`check_executor_map.py`](../../scripts/check_executor_map.py) 会因"文件或允许清单符号消失"而 **exit 1**（不是 WARN）；行号过期只 WARN。
- **改了双链契约字符串**（`rmw_fastrtps_cpp`/`42`/`fastdds.xml`/`rmw_cyclonedds_cpp`/`0`/`unset CYCLONEDDS_URI`）→ [`check_dual_chain_baseline.py`](../../scripts/check_dual_chain_baseline.py) 红。注意同一事实在**三处**各写一遍：[`config/env/load.py`](../../config/env/load.py)（L20–31）、[`chain_a.sh`](../../config/env/chain_a.sh)（L9–11）/[`chain_b.sh`](../../config/env/chain_b.sh)（L9–13）、[`dds_topics.py`](../../dimos_bridge/dimos/protocol/dds_topics.py)（L16–17）——改一处漏两处是最容易犯的错。
- **改了 `dimos_bridge` 运行时 `.py`** → [`check_cega_bridge_hold.py`](../../scripts/check_cega_bridge_hold.py) 只查存在、不逐字节审，但政策是**禁止**（PR 上 `boundary` job 看 diff，碰到冻结/Agno cast·zenoh 路径会红）。
- **改了 `config/fastdds.xml` / `SCOREBOARD.md` 内容** → 各脚本只查存在，真正拦截在 CI `boundary`（PR 红，除非 `allow-hold-bypass`）。
- **后台任务**：无常驻守护进程；CI 三个 job（`structure`/`contracts`/`boundary`）是"后台任务"，本地不会自动跑，改完必须手动按 §4 跑一遍。

### 问 4：改动后该跑哪些 check 命令？
从仓库根，按依赖顺序（本机无 ROS，预期全 exit 0）：

```bash
python3 scripts/prove_rmw.py                 # 身份闸（无 ROS 应打印 ROS not loaded）
python3 scripts/check_source_map.py          # 地图路径/符号
python3 scripts/check_executor_map.py        # WaitSet→callback 地图
python3 scripts/check_sink_layers.py         # 六层 Hold vs allowed
python3 scripts/check_dual_chain_baseline.py # 双链契约 + no XML rewrite
python3 scripts/check_three_chain_repro.py   # map≠reproduce / blocked
python3 scripts/check_unitree_cyclone_swap.py# 0.10.2 vs 11.0.1
python3 scripts/check_runtime_provenance.py   # underlay≠vendor
python3 scripts/check_risk_matrix.py         # §9.4 层序（不打分）
python3 scripts/check_dod_evidence.py        # DoD unmet / blocked
python3 scripts/check_cega_bridge_hold.py    # §13(4) Hold / 不改 bridge 运行时
python3 scripts/print_bench_gates.py         # bench 指针（不打数字）
python3 scripts/check_frozen_path_literals.py # 第13闸：冻结路径防回潮（本地，CI 接线待补）
python3 config/env/load.py print-a
python3 config/env/load.py print-b
```

三层本地回归（§2.4）：
```bash
python3 scripts/run_all_gates.py                                  # 红绿层：一把跑 13 个 gate
python3 evals/fingerprint_check.py                                # 指纹层：15 命令 stdout 逐字节等于 fixtures
npx --yes promptfoo@0.123.1 eval -c evals/promptfooconfig.yaml    # 契约层：17 个 DDS 行为断言
```
（`run_all_gates.py` 一把跑 13 gate 但不替 CI `boundary`，PR 上仍会被 `boundary` 单独审 diff；fingerprint 与 Promptfoo 目前是本地验收层，CI 不跑。有意改了 gate stdout 记得 `fingerprint_check.py --update` 重生成 fixtures。）
**不要为了本地绿去编译 vendor、启 Humble、改 XML/SCOREBOARD、或把 DoD 改成已满足。**

---

## 6. 引用

飞书（本次走查 2026-09-19，4 篇均 3380004 无权限，**未读取正文**；本仓按已合入 ADR / 源码地图 / 各 feishu 页落地）：
1. 《通信中间件》：<https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>
2. Cyclone 工业级 fork 研究：<https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>
3. 《ROS 2 源码闭环》：<https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf>
4. ros2 问题清单：<https://topsunhzj.feishu.cn/docx/CsjGd7DqNoiU4mxT2KdcWBjFntg>

本仓：
5. [AGENTS.md](../../AGENTS.md)
6. [docs/architecture/feishu-middleware-adr.md](../architecture/feishu-middleware-adr.md)
7. [docs/architecture/ros2-source-map.md](../architecture/ros2-source-map.md) — 三条链地图（map≠reproduce）
8. [docs/architecture/feishu-sink-layers.md](../architecture/feishu-sink-layers.md) — 六层 Hold vs allowed
9. [docs/architecture/feishu-executor-waitset.md](../architecture/feishu-executor-waitset.md)
10. [docs/architecture/feishu-runtime-provenance.md](../architecture/feishu-runtime-provenance.md)
11. [docs/architecture/feishu-dual-chain-baseline.md](../architecture/feishu-dual-chain-baseline.md)
12. [docs/architecture/feishu-three-chain-repro.md](../architecture/feishu-three-chain-repro.md)
13. [docs/architecture/feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md)
14. [docs/architecture/unitree-sdk2-dds-swap.md](../architecture/unitree-sdk2-dds-swap.md)
15. [docs/architecture/feishu-cega-bridge-hold.md](../architecture/feishu-cega-bridge-hold.md)
16. [docs/architecture/ci-cd-gates.md](../architecture/ci-cd-gates.md)
17. [vendor/MANIFEST.md](../../vendor/MANIFEST.md) · [vendor/VERSIONS.md](../../vendor/VERSIONS.md)
18. [scripts/prove_rmw.py](../../scripts/prove_rmw.py) · [scripts/check_source_map.py](../../scripts/check_source_map.py) · 其余 `scripts/check_*.py`
