//! `dds_rs_rtps`：RTPS 线协议层（发现、DATA/DATAACK、分片、可靠重传）。
//!
//! 终态在此封装钉版 DDS/RTPS 内核并补齐其 QoS/分片/Security 缺口，向上提供
//! 受控的 Rust API，向下经 `dds_rs_port` 收发 UDP 报文。Phase 2 的跨实现互通、
//! Phase 3 的 Reliable/QoS 对照都以本 crate 为对象。
//!
//! Phase 0 不接网络、不引外部内核，仅固化一个 well-known 端口常量作为占位。

/// RTPS well-known UDP 端口基数（PB = 7400）。
///
/// 实际端口按 domain_id、participant index 与 D0/D1/D2/D3 偏移公式推导；
/// Phase 2 抓包对照时会在此基础上实现完整端口推导，先记录协议常量。
pub const RTPS_WELL_KNOWN_UDP_PORT_BASE: u16 = 7400;

#[cfg(test)]
mod tests {
    use super::RTPS_WELL_KNOWN_UDP_PORT_BASE;

    #[test]
    fn rtps_port_base_matches_spec() {
        assert_eq!(RTPS_WELL_KNOWN_UDP_PORT_BASE, 7400);
    }
}
