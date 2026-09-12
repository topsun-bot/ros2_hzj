# Bugbot / auto-review — ros2_hzj

`ros2_hzj` is TOPSUN / 桦之坚's **dual-chain** ROS 2 / DDS workspace (not `topsun_dimos`).
链 A：`rmw_fastrtps_cpp`，domain **42**，`config/fastdds.xml`。链 B：Cyclone domain **0**。
No custom RMW. LCM is out of scope.

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof.

## Never approve / 永不批准

Do **not** approve a PR that edits:

- `config/fastdds.xml`
- `docs/artifacts/bench/SCOREBOARD.md`
- Agnocast / zenoh **paths**（vendor 树、kmod、`rmw_zenoh`、heaphook）。文档**正文**提到这些词可以；新增 / 改动 **路径** 不行。

Flag those path edits as blocking Hold violations. 命中上述路径必须标红，不得 Approve。

## Hold 《3》–《6》

《3》bench score loops / 90%·LLM，《4》Mac HIL / preprod，《5》Promptfoo，《6》CVE — still **Hold**. Do not approve enabling them, vendoring those stacks, or treating stubs as live.

## Cross-host

跨机 UDP 仍 **blocked**，除非本 PR 产物明确证明否则（真实第二台主机 + 非假分位数）。
Cross-host UDP stays **blocked** unless artifacts in this PR prove otherwise (second host; no invented percentiles). Same-VM Docker is not cross-host.

## Expected CI

`python3 scripts/prove_rmw.py`、`python3 scripts/check_source_map.py`、`python3 scripts/print_bench_gates.py` are expected CI (`structure` / `contracts`). Do not drop them. `print_bench_gates.py` must keep `cross-host: blocked` unless artifacts prove otherwise.

## Dual-chain

Do not mix Chain A / Chain B defaults, domains, or bench tables. Do not change `dimos_bridge` DDS behavior or vendor sources.
