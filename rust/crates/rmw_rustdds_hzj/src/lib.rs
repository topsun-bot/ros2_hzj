//! `rmw_rustdds_hzj`：面向 ROS 2 的 RMW C-ABI 适配层（R2 终态主体，Phase 4）。
//!
//! 终态以 `extern "C"` 实现 `vendor/rmw/rmw/include/rmw/rmw.h` 所需符号子集，
//! 编译为 cdylib（`librmw_rustdds_hzj.so/.dylib`），由用户通过
//! `RMW_IMPLEMENTATION=rmw_rustdds_hzj` **显式**加载；链 A/链 B 默认完全不变。
//!
//! 该 crate 在 Phase 4 启动前不提供任何 C 符号，也不开启 `unsafe`；启动 shim
//! 的前置是 Phase 2/3 互通证据稳定、书面 ADR 与人类 `allow-hold-bypass`。

/// 未来注册到 ROS 2 的 RMW 实现标识名。
///
/// 该字符串必须与最终导出的 `rmw_implementation` 标识一致，先固化以免命名漂移。
pub const RMW_IMPLEMENTATION_NAME: &str = "rmw_rustdds_hzj";

#[cfg(test)]
mod tests {
    use super::RMW_IMPLEMENTATION_NAME;

    #[test]
    fn implementation_name_is_stable() {
        // 命名属公共契约，改动会破坏 RMW_IMPLEMENTATION 选择，故锁定字面量。
        assert_eq!(RMW_IMPLEMENTATION_NAME, "rmw_rustdds_hzj");
    }
}
