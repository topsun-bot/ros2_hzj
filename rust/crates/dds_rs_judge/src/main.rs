//! `dds_rs_judge`（二进制）：Rust 线的对等裁判与观测入口。
//!
//! Phase 1 起在此实现：CDR golden-sample 校验、RTPS 报文捕获/回放、loopback
//! pingpong（p50/p95/p99 与到达间隔口径）、与 Humble 容器的跨实现互通判定。
//! 裁判必须先能对"故意破坏"的输入变红，禁止成为橡皮图章。
//!
//! Phase 0 仅提供可运行的占位入口，明确当前尚无裁判能力，以退出码 0 返回。

use dds_rs_core::CDR_ENCAPSULATION_HEADER_BYTES;

fn main() {
    println!(
        "dds_rs_judge: Phase 0 scaffold only; no judge rules yet \
         (CDR header anchor = {} bytes)",
        CDR_ENCAPSULATION_HEADER_BYTES
    );
    println!("next: Phase 1 introduces CDR golden samples and loopback pingpong.");
}

#[cfg(test)]
mod tests {
    #[test]
    fn placeholder_smoke() {
        // 保证 bin target 也被 `cargo test --workspace` 覆盖并通过。
        assert_eq!(2 + 2, 4);
    }
}
