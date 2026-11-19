//! `dds_rs_port`：平台相关的薄移植层（portability shim）。
//!
//! 所有 UDP socket、时钟、调度与（未来的）共享内存/零拷贝差异都收敛到这里，
//! 保持零业务语义、零外部重型依赖，使 `dds_rs_core`/`dds_rs_rtps` 可移植、可单测。
//!
//! Phase 0 只声明规划中的后端枚举，尚不开 socket。

/// 传输后端类型。
///
/// Phase 0 仅规划 UDP 单一路径（首版明确不做 SHM/zero-copy 发送）；未来新增
/// 后端必须在此枚举显式扩展，而不是在核心逻辑里散落平台条件编译。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PortBackend {
    /// 标准 UDP/IP（含 loopback 与同机/跨机），Phase 2 的唯一后端。
    Udp,
}

#[cfg(test)]
mod tests {
    use super::PortBackend;

    #[test]
    fn phase0_only_udp_backend_is_declared() {
        assert_eq!(PortBackend::Udp, PortBackend::Udp);
    }
}
