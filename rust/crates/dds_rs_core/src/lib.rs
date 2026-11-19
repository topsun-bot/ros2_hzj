//! `dds_rs_core`：与平台和网络无关的纯逻辑内核。
//!
//! 职责（终态）：CDR/XCDR 序列化与反序列化、QoS/topic/domain 的纯数据模型、
//! 不依赖 I/O 的编解码与校验规则。该 crate 不允许出现网络、线程或 FFI 调用，
//! 以便在 vanilla macOS 上确定性单测，对应架构里的"核心可移植、平台进 port 薄层"。
//!
//! Phase 0 仅建立边界与一个真实语义占位；CDR golden 夹具在 Phase 1 引入。

/// RTPS 序列化载荷前的 CDR encapsulation 头长度（字节）。
///
/// 该头标识字节序与 CDR 版本（如 `0x0001` 小端 CDR1、`0x0010` 大端等）。
/// 先以常量固化这一协议事实，Phase 1 的编解码器与 golden 样本将围绕它展开。
pub const CDR_ENCAPSULATION_HEADER_BYTES: usize = 4;

#[cfg(test)]
mod tests {
    use super::CDR_ENCAPSULATION_HEADER_BYTES;

    #[test]
    fn cdr_encapsulation_header_is_four_bytes() {
        // 占位但真实的协议不变量：封装头固定 4 字节，作为后续编解码的锚点。
        assert_eq!(CDR_ENCAPSULATION_HEADER_BYTES, 4);
    }
}
