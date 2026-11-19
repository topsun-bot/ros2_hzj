# ADR：Rust 自研 RMW 技术线（D 面，opt-in）

- 日期：2026-11-19
- 状态：**已批准进入 Phase 0（脚手架）。** 依据当日经用户批准的迁移计划 v1
  （[`docs/refactor/03-rust-dds-migration-plan.md`](../refactor/03-rust-dds-migration-plan.md)）。
  本 ADR 只登记决策与边界；**Phase 4 的 C-ABI shim 仍须在启动时另行满足
  `allow-hold-bypass` + 书面 ADR 条件，本文件不预先授予该豁免。**
- 关系：本 ADR 是对 [feishu-middleware-adr.md](feishu-middleware-adr.md) 中
  「自研 DDS 经 RMW 接入 = 未开始」一项的**增量推进**，不推翻其双链冻结结论。

## 1. 背景

- 本仓运行时 DDS 是上游只读 C/C++ 整树快照（`vendor/`）与 Humble apt 包，自有代码为
  Python 闸门 / bench / 文档与 `dimos_bridge` 只读拷贝；在本决策前**零 Rust 代码**，
  也没有"自研 DDS"可原地翻译。
- 2026-11 生态复核：无成熟、可直接替换 `rmw_fastrtps_cpp` 的纯 Rust RMW 现货；
  纯 Rust DDS 内核 RustDDS 0.15.1 仍 0.x，缺零拷贝发送、部分 QoS、DDS-Security
  跨厂商互通等；最接近的 HDDS 仅 0.1.0。规模上，上游 Fast-DDS/Cyclone 自有核心
  合计约 59 万行，完整等价物属多人多年工程。

## 2. 决策（用户 2026-11-19 拍板）

1. **终态路线定为 R2**：交付一个纯 Rust、可由 `RMW_IMPLEMENTATION=rmw_rustdds_hzj`
   显式加载的 RMW（cdylib），但**施工按分阶段证据门禁推进，不得跳步**：
   judge 先行 → RTPS 单消息互通 → QoS 对齐 → 最后才写 C-ABI shim。
2. **代码落在同仓新 D 面 `rust/`**（独立 Cargo workspace），与 A–C 面物理隔离，
   不修改任何现有文件即可 `cargo test`；成熟独立发版前不拆仓。
3. **默认双链永远不变**：链 A `rmw_fastrtps_cpp`/域 42/`config/fastdds.xml`、
   链 B Cyclone/域 0 的 RMW 名、域、环境变量、XML、QoS 契约零变化。Rust 线长期
   opt-in，与既有链共存，参照 `unitree_sdk2_hzj` + `UNITREE_DDS_PROVIDER=external`
   的合法换库模式，**绝不 in-place 覆盖**。
4. **验证环境**：Phase 2 起在本机经 colima + Docker 的 `osrf/ros:humble` 容器做
   跨实现互通与同机 pingpong；认证目标先钉 **Humble**，不得用 rolling 行为替代；
   跨机 UDP 在取得第二台物理机前持续 `STATUS: blocked`，禁止伪造分位。
5. **交付**：push 到 feature 分支并开 PR，merge 权始终在人类；本阶段不改
   `.github/workflows/`（gh token 缺 `workflow` scope，需用户另行授权刷新）。

## 3. 能力成熟度分级（M0–M5，达不到即 blocked，不写 PASS）

| 级 | 能力 | 阶段 |
|----|------|------|
| M0 | workspace + 纯逻辑单测 + fmt/clippy | Phase 0–1 |
| M1 | CDR/XCDR1 定长字节级编解码 + golden | Phase 1 |
| M2 | UDP loopback/同机 RTPS 发现 + BestEffort，与 Humble Fast-DDS/Cyclone 双向互通 | Phase 2 |
| M3 | Reliable + History + depth + domain 隔离 + 发现稳定性，双厂商对照 | Phase 3 |
| M4 | `rmw_rustdds_hzj` C-ABI shim，覆盖标准 pub/sub 所需 `rmw.h` 符号子集 | Phase 4（需 bypass） |
| M5 | 扩展 QoS、变长/分片、service/action/parameter、零拷贝发送、DDS-Security 跨厂商 | 后续，逐项 ADR，不承诺时间点 |

## 4. Hold 边界：解除范围与仍冻结面

**本次仅解除/新增（人类已批准）**：允许在 `rust/` 与 `docs/artifacts/rust/` 新增
Rust 技术线及其文档、夹具、测试；允许根 `.gitignore` 与 `AGENTS.md` 做对应登记。

**继续冻结，Rust 线同样不得触碰**：

- `vendor/**`、`config/fastdds.xml`、`docs/artifacts/bench/SCOREBOARD.md`；
- `dimos_bridge/dimos/**` 运行时；
- 不启用 Agnocast / zenoh / eCAL / DPDK / Cega，不 Rolling 覆盖 Humble；
- 现有 13 个 Python 闸门的命令名、exit code、marker 短语公共契约；
- structure/contracts/boundary 三个 required CI job 不改动、不编译 vendor。

**Phase 4 shim 的特别门槛**：实现/导出 `rmw.h` C 符号、改变可加载 RMW 集合，属于
对历史「No custom RMW」边界的突破，启动前必须同时满足：Phase 2/3 互通证据稳定、
gap 清单收敛、存在专门 ADR、由**人类**在 PR 贴 `allow-hold-bypass`（见
[ci-cd-gates.md](ci-cd-gates.md)）。Agent 不得自行贴标或提前实现 C 符号。

## 5. 工程纪律（对齐仓库长期约定）

- **确定性**：`rust/rust-toolchain.toml` 钉 1.99.0；外部 crate 精确钉版、
  `Cargo.lock` 入库；新增第三方依赖走 ADR；固定随机种子。
- **unsafe/FFI**：workspace 现 `forbid unsafe_code`；Phase 4 仅在 shim crate 局部、
  显式放开，每条 `unsafe` 注释对应编号不变量并论证并发/内存序安全，clippy + 评审双闸。
- **可移植性**：平台/网络/时钟差异收敛到 `dds_rs_port` 薄层；`dds_rs_core`
  零外部依赖、可在 vanilla macOS `cargo test`。
- **API 契约**：每个对外 API 写 REQUIRES 前置、空值语义、边界；assert 常驻；
  接口前后向兼容，字段只增不改语义，迁移期保留旧路径与显式开关。
- **评审规模**：单 PR ≤ 约 50 文件，不做无关重构，不覆盖用户改动；连续两轮验证
  失败、超范围或接口争议即停，转人工决策。

## 6. 验证命令

```bash
# Rust D 面（rust/ 目录）
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
# 既有 Python 闸门（仓库根目录，任何阶段必须保持 13/13 全绿）
python3 scripts/run_all_gates.py
```

Phase 0 验收：Rust 占位测试与 fmt/clippy 全绿；Python 闸门仍 13/13；默认 RMW、
域、环境变量、XML 零变化；本阶段不产生任何可加载 RMW 或网络行为。

## 7. 引用

- 迁移计划与规模/生态核实：[`../refactor/03-rust-dds-migration-plan.md`](../refactor/03-rust-dds-migration-plan.md)
- 双链与历史 RMW 决策：[feishu-middleware-adr.md](feishu-middleware-adr.md)、
  [ros2-dds-r0-interface-freeze.md](ros2-dds-r0-interface-freeze.md)
- Hold/bypass 机制：[ci-cd-gates.md](ci-cd-gates.md)
- 合法换库先例：[unitree-sdk2-dds-swap.md](unitree-sdk2-dds-swap.md)
- 供应商版本钉扎：[`../../vendor/VERSIONS.md`](../../vendor/VERSIONS.md)
