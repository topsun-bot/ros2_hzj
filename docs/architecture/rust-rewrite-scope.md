# Rust 重写范围（任务 ③：哪几层可写、哪几层只研究）

Status: **scope decided — 10× unmet; user confirmation open.**  
查阅日期：2026-10-11。输入是任务 ② 调研手递（同日检索的五份公开实现：rclrs、r2r、RustDDS、dust_dds、rmw_zenoh）。本页是范围决定，不是重写实现，不是实测。

对照本仓已决：[feishu-middleware-adr.md](feishu-middleware-adr.md)（不自研 RMW）、[feishu-sink-layers.md](feishu-sink-layers.md)（Hold vs allowed）、[feishu-dual-chain-baseline.md](feishu-dual-chain-baseline.md)（不重写 XML）、[ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md)（双链）、[feishu-cega-bridge-hold.md](feishu-cega-bridge-hold.md)（不接 Cega）、[feishu-dod-evidence.md](feishu-dod-evidence.md)（`DoD: unmet`）、[feishu-executor-waitset.md](feishu-executor-waitset.md)（C WaitSet）。CI：[ci-cd-gates.md](ci-cd-gates.md)。操作员入口：[AGENTS.md](../../AGENTS.md)。

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

本切只落地文档 + 证明脚本。**no custom RMW.** **DDS interop is study-only.** **do not adopt rmw_zenoh.** **do not replace FastDDS 42 / Cyclone 0.** **no Cega.** **no dimos_bridge runtime edits this cut.** **no XML/SCOREBOARD.**

---

## 0. 硬规则

1. **`10×: unmet`。** 项目页的「相对 Jazzy 快 10 倍」仍是目标。五份必读实现都没有第一方对照表支撑它。本页不把目标写成已测量。
2. **`user confirmation open`。** 任务完成标准要求文档经用户确认。落地本页不等于确认。在确认前，§5 只是可起草的边界，不是定稿。
3. **客户端 / codegen 可以参考，不在本切 vendor。** `reference rclrs`。`reference rosidl_rust`。不把 `ros2_rust` 或 `rosidl_rust` 拷进本仓。
4. **`DDS interop is study-only`。** RustDDS / ros2-client 只用来读发现、CDR、GID 和已发表的互通报告。**do not replace FastDDS 42 / Cyclone 0.** 链 A 仍是 `rmw_fastrtps_cpp`、域 **42**、[`config/fastdds.xml`](../../config/fastdds.xml)。链 B 仍是 `rmw_cyclonedds_cpp`、域 **0**、[`config/env/chain_b.sh`](../../config/env/chain_b.sh)。
5. **`no custom RMW`。** **do not adopt rmw_zenoh.** 不 vendor `rmw_zenoh`，不装 kmod，不启用 ros2-client 的 `zenoh` feature。任务 ⑥ 不在本切。
6. **任务 ⑤ 不在本切。** 不写 RTPS/DDS 栈，不把 RustDDS 当改造基底，不把 dust_dds 或 ZeroDDS 当复用基础。
7. **不改** [`config/fastdds.xml`](../../config/fastdds.xml)、[`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md)。`no XML/SCOREBOARD`。
8. **不接 Cega，不改 `dimos_bridge` 运行时。** `no Cega`。`no dimos_bridge runtime edits this cut`。
9. **《3》–《6》仍 Hold。** 不在本切跑 bench 分数闭环、Mac HIL、Promptfoo 产品环或 CVE。

核对本页决定仍在：[`scripts/check_rust_rewrite_scope.py`](../../scripts/check_rust_rewrite_scope.py)。

---

## 1. 分层决定

| 层 | 决定 | 本切 |
|----|------|------|
| **client** | reference rclrs | 以后若设计 Rust 应用层，API 形状跟 rclrs（`Context` / `Node` / pub-sub / service / action / parameter）。r2r 只作 async、cargo 优先的备选。二者都仍调用 C `rcl`，不能单独交出中间件 10 倍。不 vendor。不替换本仓 `rclpy` / `ROSTransport` 应用。 |
| **codegen** | reference rosidl_rust | 若消息面保持 ROS IDL，参考 `rosidl_generator_rs` + `rosidl_runtime_rs`（Apache-2.0），对接 `rosidl_generate_interfaces`。r2r 的 C introspection 是不想走 colcon 时的后备。dust_dds_gen 只生成 DDS IDL，不是 ROS `.msg` 管线。本切不往工作区加消息包。 |
| **rcl** | keep C rcl | 不重写 `rcl`。Humble `rclcpp` / `rclpy` 仍不在 vendor。rclrs / r2r 继承进程里的 `RMW_IMPLEMENTATION`。 |
| **rmw** | no custom RMW | do not adopt rmw_zenoh。rmw_zenoh 是 C++ RMW，线上不是 RTPS，不能加入链 A / 链 B。读它只为看 `rmw.h` 怎么映到 session / graph / SHM。任务 ⑥（自研 Rust rmw，接到 rcl）**task ⑥ out of this change**。 |
| **DDS** | study-only | DDS interop is study-only。do not replace FastDDS 42 / Cyclone 0。RustDDS + ros2-client 是必读集合里唯一「纯 Rust 且对 Fast DDS / Cyclone 有公开互通报告」的路径，只研究。dust_dds 是最小 profile / `no_std` 风格参考，ROS 级互通未证明。任务 ⑤（DDS 1.4 / RTPS 有线协议实现）**task ⑤ out of this change**。 |
| **executor** | keep C wait set | 不新写 async 运行时。rclrs 若被参考，执行器仍是 C rcl 的 WaitSet。r2r 的 ECRTS 2025 结果是 `futures-rt` 与 `rclcpp-rt` 端到端 P99 相当，不是快 10 倍；默认 async 配置达不到 rclcpp 实时，需要线程优先级和回调线程映射。那是任务 ⑨ 的题目，不是本切。地图仍是 [feishu-executor-waitset.md](feishu-executor-waitset.md)。 |
| **memory** | no SHM rewrite | 不实现共享内存或零拷贝发送。rclrs 的 loaned message 是经 C rcl 的 RMW loaned-message API，不是 Rust DDS 栈。RustDDS 接收路径有零拷贝记录，发送路径和 SHM 未完成。本仓没有 `vendor/iceoryx`。不改 XML。任务 ⑨ 的零拷贝 / SHM / 异步调优不从本切开工。 |

一句话：用 **rclrs（客户端 API）+ rosidl_rust（codegen）** 作为以后应用层的参考；**DDS 互通只研究**（RustDDS / ros2-client）；车上中间件保持 FastDDS 42 与 Cyclone 0；**rmw_zenoh 不进入本仓**。

---

## 2. 明确不采纳的旧稿

任务页上更早的「全栈纯 Rust 快路径」稿（自研 `ros2_rtps_dds`、`rmw_hzj_rust`、原生 Rust 客户端 API，以及「DDS 层以 RustDDS 为改造基底、自研 Rust rmw、ZeroDDS 短期 PoC」）**not adopted**。

原因：那是任务 ⑤ 和任务 ⑥ 的实现，并且会变成第三条栈。本仓 Hold 禁止自定义 RMW，禁止换掉 FastDDS 42 / Cyclone 0，禁止把 zenoh 当链。调研也没有给出 10 倍的测量。ZeroDDS 不在五份必读链接里，不作为复用基础。

---

## 3. 线程、内存、与 ROS 2 生态怎么接

本切不写代码，只钉对接方式，避免后面的任务另起一套工具链。

| 面 | 决定 |
|----|------|
| 线程 / 异步 | 保持 C WaitSet。不引入新的 async runtime。若以后用 r2r 形状，必须单独做线程优先级，不能把「async Rust」当成 10 倍。 |
| 内存 / 零拷贝 | 不新写 SHM。大消息 10 倍若要成立，依赖 RustDDS 今天没有的发送零拷贝和共享内存；那是缺口说明，不是开工许可。 |
| colcon | 参考 ros2-rust 时走现有 `rosidl_generate_interfaces`。本切不加 colcon 包。 |
| rosidl | reference rosidl_rust。生成物有 ergonomic `std` 形态和 ABI 兼容的 `msg::rmw` 形态（调研所引 message-generation 说明）。不把生成器拷进本仓。 |
| launch | 仍用 ROS 2 launch。rclrs 节点仍然加载 `librcl` 和当前 `RMW_IMPLEMENTATION`，所以链 A / 链 B 的 `source` 方式不变。 |
| 双链切换 | 操作员显式 `source` [`config/env/chain_a.sh`](../../config/env/chain_a.sh) 或 [`config/env/chain_b.sh`](../../config/env/chain_b.sh)。`import` `load.py` 不写 `os.environ`。 |

---

## 4. 「10 倍」量什么（定义草案，未测量）

`10×: unmet`

下面是候选定义，抄自项目页（同一硬件、1 KB–4 MB）和任务页草案。它等用户确认。本切没有跑基线，也不改 SCOREBOARD。对照数字只能来自任务 ① 的实测，不能来自本页。

| 场景 | 对照 | 候选阈 | 本切 |
|------|------|--------|------|
| 同机进程间大消息，约 1 MB（点云 / 图像一类），落在 1 KB–4 MB 带内 | 原版 Jazzy + Fast DDS UDP，同一硬件 | P99 传输延迟至少降低 10 倍 | 未测 |
| 高频小消息，64 B–256 B | 同上 | 吞吐至少提高 10 倍，或 P99 延迟至少降低 5 倍，并且 CPU 至少降低 50% | 未测 |
| 项目页全带：延迟、吞吐、CPU、内存，1 KB–4 MB | Jazzy Fast DDS 与 Cyclone | 10 倍 | 未测。SCOREBOARD **pointer only** |

调研手递：没有任何必读仓库发表过「相对 Jazzy FastDDS/Cyclone 快 10 倍」的第一方表。第三方 zenoh 材料最好大约是部分场景 2 到 4 倍，而且 zenoh 路线不互通 RTPS，本仓不采纳。

`user confirmation open`：完成标准「文档经用户确认」仍开着。确认前不要把上表写成验收阈已通过。

---

## 5. ⑤–⑩ 可以据此起草的边界

`⑤–⑩ scope draftable`。下表让后续任务知道本页允许什么。用户确认前不是定稿。本切不实现这些任务。

| 任务 | 本页给它的边界 |
|------|----------------|
| ④ 许可审查 | 允许先做文档审查，再谈任何拷贝。rclrs / rosidl_rust / RustDDS / dust_dds / rmw_zenoh 是 Apache-2.0（rmw_zenoh 另有 BSD xxhash，且代码不得入库）。r2r 是 MIT 与 Apache-2.0 文件级声明并存。链 B 的 Cyclone 是 EPL-2.0/EDL-1.0，不因为「不替换」就可以把 Cyclone 源码译成 Rust。 |
| ⑤ DDS 1.4 / RTPS | **task ⑤ out of this change**。study-only。不替换 FastDDS 42 / Cyclone 0。不把 RustDDS 当基底改造成第三条栈。ZeroDDS 不是复用基础。 |
| ⑥ rmw 接到 rcl | **task ⑥ out of this change**。no custom RMW。do not adopt rmw_zenoh。 |
| ⑦ Rust 客户端 API 与 rosidl | 允许的参考是 rclrs + rosidl_rust。可以在以后的任务里做应用层，但本切不 vendor、不建 crate。它仍坐在 C rcl 和现有 RMW 上，不能被写成 10 倍中间件。 |
| ⑧ 与原版 ROS 2 节点互通 | 互通对象是链 A FastDDS 与链 B Cyclone，不是第三条栈，也不是 zenoh。RustDDS 已发表的 dds-rtps 报告只作阅读。本切不跑互通。 |
| ⑨ 零拷贝 / SHM / 异步 / 基准 | 依赖 ① 的基线和 ⑧ 的互通。指标用 §4 的候选定义，未达标必须写实测倍数，不能改口成已达 10 倍。不改 `fastdds.xml`。不把 rmw_zenoh 的 SHM 搬进来。 |
| ⑩ 机器人实测（Go2W 或双臂） | 依赖前面的基线与互通。不改 `dimos_bridge` DDS 行为。Unitree 自带 Cyclone 0.10.2 对 vendor 11.0.1 仍是 drop-in FAIL，本页不借机换库。 |

---

## 6. 风险（不打分）

不发明风险分数，不对齐 [feishu-risk-matrix.md](feishu-risk-matrix.md) 以外的新分数。

| 风险 | 为何写在这里 |
|------|----------------|
| 把 rclrs 当成中间件重写 | 它绑 C rcl，继承现有 RMW，交不出 DDS/RMW 的 10 倍 |
| 采纳 rmw_zenoh 或 ros2-client 的 zenoh feature | 与链 A / 链 B 不互通；路径名本身就会撞 Hold |
| 把 RustDDS vendor 成第三条栈 | 自定义栈，破坏双链契约 |
| 忽略 RustDDS 的 QoS / SHM 缺口 | 缺 Partition、TimeBasedFilter、Presentation、Deadline/LatencyBudget，发送零拷贝和 SHM 未完成；大消息性能主要靠这些 |
| 把 dust_dds 当成 ROS DDS | 最小 profile；ROS 级互通未证明 |
| 把 ZeroDDS 当成短期 PoC 并入库 | 不在五份必读链接里；本切不安排 PoC |
| 许可混用 | r2r 双许可；Cyclone 是 EPL/EDL；未做任务 ④ 就拷贝会违规 |
| 用默认 async runtime 声称实时 | ECRTS 2025 只显示与 rclcpp-rt 相当，且依赖线程映射 |
| 没有任务 ① 基线就声称 10 倍 | SCOREBOARD 冻结；本页 `10×: unmet` |
| 借重写去改 Bridge / XML / Cega | `no Cega`；`no dimos_bridge runtime edits this cut`；`no XML/SCOREBOARD` |

---

## 7. 闸门怎么跑

```bash
python3 scripts/check_rust_rewrite_scope.py
```

无 ROS 时应 exit 0，并打印 `rust rewrite scope: decided (10× unmet)`。脚本打开这些文件：

| 打开 | 断言 |
|------|------|
| 本文 | 首行 Status 含 `10× unmet` 与 `user confirmation open`；七层表的决定格分别是 reference rclrs、reference rosidl_rust、keep C rcl、no custom RMW、study-only、keep C wait set、no SHM rewrite；连续短语 `DDS interop is study-only`、`do not adopt rmw_zenoh`、`do not replace FastDDS 42 / Cyclone 0`、`10×: unmet`、`task ⑤ out of this change`、`task ⑥ out of this change`、`⑤–⑩ scope draftable`、`not adopted` |
| [`feishu-middleware-adr.md`](feishu-middleware-adr.md) | 仍写 `不自研 RMW`，并指向本文 |
| 仓库根 `Cargo.toml` | **必须不存在**（本切不建 Rust crate） |
| `vendor/rmw_zenoh`、`vendor/agnocast` | **必须不存在** |
| [`config/fastdds.xml`](../../config/fastdds.xml) | **只检查存在**。内容冻结由 **`boundary`** 管 |
| [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) | **只检查存在**。不读数字 |

CI 登记见 [ci-cd-gates.md](ci-cd-gates.md)。不要为了本地绿去编译 vendor、接 zenoh、换双链，或把 `10×: unmet` 改成已达成。

---

## 8. 引用

1. 任务 ② 调研手递（2026-10-11）：rclrs、r2r、RustDDS、dust_dds、rmw_zenoh 的分层、许可与「没有 10 倍第一方表」结论。手递不在本仓树内；本页只收决定，不重做检索。
2. [feishu-middleware-adr.md](feishu-middleware-adr.md) — 不自研 RMW；双链契约
3. [feishu-sink-layers.md](feishu-sink-layers.md) — app / rcl / rmw / DDS / executor / memory 的 Hold vs allowed
4. [feishu-dual-chain-baseline.md](feishu-dual-chain-baseline.md) — 不重写 XML；SCOREBOARD pointer only
5. [feishu-cega-bridge-hold.md](feishu-cega-bridge-hold.md) — 不接 Cega；不改 `dimos_bridge` 运行时
6. [feishu-dod-evidence.md](feishu-dod-evidence.md) — 产品 DoD 仍 unmet
7. [AGENTS.md](../../AGENTS.md) — 链 A `rmw_fastrtps_cpp` 域 42；链 B Cyclone 域 0
8. [scripts/check_rust_rewrite_scope.py](../../scripts/check_rust_rewrite_scope.py)
