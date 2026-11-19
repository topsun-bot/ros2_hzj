# rust/ — 自研 Rust RMW 技术线（D 面）

> 状态：**Phase 0（脚手架）。** 本 workspace 当前只包含可独立编译测试的空骨架，
> **不产出任何 RMW、不接入网络运行时、不是默认 RMW，也不会改变链 A / 链 B 行为。**

## 这是什么 / 不是什么

- **终态目标（R2）**：以纯 Rust 实现一个可被 ROS 2 通过 `RMW_IMPLEMENTATION`
  显式加载的 `rmw_rustdds_hzj`，长期 **opt-in**，与既有 Fast-DDS（域 42）、
  Cyclone（域 0）双链并存，绝不 in-place 替换。
- **不是**：对 `vendor/` 内 C/C++ 代码的原地翻译或改写；`vendor/**`、
  `config/fastdds.xml`、`docs/artifacts/bench/SCOREBOARD.md`、
  `dimos_bridge/dimos/**` 始终只读冻结。
- 在取得 RTPS 跨实现互通证据之前，**不宣称具备替代能力**；不伪造 PASS 或延迟分位。

完整背景、规模实测、生态选型、风险与阶段门禁见：

- [`../docs/architecture/rust-rmw-adr.md`](../docs/architecture/rust-rmw-adr.md)
- [`../docs/refactor/03-rust-dds-migration-plan.md`](../docs/refactor/03-rust-dds-migration-plan.md)

## crate 布局

| crate | 职责 | Phase 0 状态 |
|-------|------|--------------|
| `dds_rs_core` | CDR 编解码、QoS/topic/domain 纯模型；零外部依赖、纯单测 | 占位 |
| `dds_rs_rtps` | RTPS 发现/收发/分片/重传（未来封装钉版 DDS 内核） | 占位 |
| `dds_rs_port` | UDP/时钟/平台差异薄层；核心逻辑不直接依赖它 | 占位 |
| `rmw_rustdds_hzj` | `extern "C"` 实现 `rmw.h` 符号子集的 cdylib（Phase 4） | 占位，暂为普通 lib |
| `dds_rs_judge` | CDR golden、报文回放、pingpong、互操作裁判（bin） | 占位 |

## 编码纪律（摘要）

- 平台/网络/FFI 差异收敛到 `dds_rs_port` 薄层；核心逻辑保持可在 vanilla macOS 单测。
- `unsafe` 在 workspace 级默认 `forbid`；未来 FFI shim 确需开启时，每条 `unsafe`
  必须注释对应编号不变量，论证并发与内存序为何安全，并经评审。
- 外部 crate 精确钉版、`Cargo.lock` 入库；新增第三方依赖走 ADR。
- 每个对外 API 写明 REQUIRES 前置条件、空值语义与边界；assert 常驻。

## 本地命令

```bash
# 在 rust/ 目录下
cargo test --workspace
cargo clippy --all-targets -- -D warnings
cargo fmt --all -- --check

# 仓库既有 Python 闸门（在仓库根目录，任何阶段都必须保持全绿）
python3 scripts/run_all_gates.py
```

Phase 0 预期：Rust 侧占位测试通过、clippy/fmt 零警告；Python 侧仍为 13/13 gate 绿，
默认 RMW 名、域、环境变量与 XML 零变化。
