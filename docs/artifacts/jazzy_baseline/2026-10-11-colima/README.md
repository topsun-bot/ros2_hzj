# Jazzy 本机验证记录 — 2026-10-11

**STATUS: partial task acceptance / not_final_baseline: true。** 本次完成运行器、测量和重复统计的实现验证，未完成任务①全部拓扑验收。没有运行机器人、Rust 中间件或 10× 对比。

对应 [Notion 任务①](https://app.notion.com/p/3f6567e95a6a8166bde4cd97a4950441)。独立分支基于 [PR #205](https://github.com/topsun-bot/ros2_hzj/pull/205) 的 `1a65153213e4c556b7326cf627f6a8bb59d018df`；原 PR 分支和主分支未修改。PR #206/#207 的架构草案不构成本次范围或授权。

## 实际运行与结果

测试环境为已存在的 Colima VM：Ubuntu 24.04.4 / Linux 6.8.0-117-generic / aarch64，4 个逻辑 CPU、8112464 kB 内存，Python 3.12.3，ROS 2 Jazzy。使用发行版 rclpy、默认 RMW 配置、本机回环发现、ROS domain 87，没有安装软件或修改 DDS XML。

Fast DDS 的 Debian 包名是 `ros-jazzy-fastrtps`，版本 `2.14.6-1noble.20260902.013353`；RMW 为 `8.4.4-1noble.20260902.140744`。Cyclone DDS 为 `0.10.5-1noble.20260305.204044`，RMW 为 `2.2.4-1noble.20260902.140937`。早期 smoke/matrix 环境中的 `fastdds: not-installed` 是旧采集代码查询了不存在的 `ros-jazzy-fastdds` 包名，不能解释为没有加载 Fast DDS；96 个矩阵 worker 均实际查询并核验了 RMW。后续采集已修正包名，见 [RTT 环境](rtt/environment.json)。旧证据未覆盖。

| 验证 | 实际结果 | 证据 |
|---|---|---|
| 早期 Jazzy smoke | 4/4 成功，每项收发 40 条，exit 0 | [运行日志](validation/jazzy-smoke.json)、[报告](smoke/summary.md) |
| Jazzy 单向矩阵 | 48/48 完成，16 参数组 × 3 次，exit 0 | [运行日志](validation/jazzy-matrix-recovered.json)、[逐次指标与波动](matrix/summary.md)、[CSV](matrix/results.csv) |
| 本机 RTT 功能验证 | 8/8 完成，exit 0；每组仅一次，未满足三次重复 | [运行日志](validation/jazzy-rtt.json)、[报告](rtt/summary.md) |
| Python 3.9 自检修复后 | 原有 8 项检查和 33 项回归测试通过，exit 0 | [最终自检](validation/host-selftest-final.json) |
| Jazzy Python 3.12 自检 | 同一组自检和 33 项回归测试通过，exit 0 | [Linux 自检](validation/jazzy-selftest.json) |
| 仓库原有检查 | 13/13 通过，exit 0 | [检查日志](validation/repository-gates-final.json) |
| NaN 参数 | 拒绝，exit 2 | [错误输出](validation/rejected-nan.json) |
| 未实现拓扑 | same-process / cross-host 均 blocked，exit 2 | [同进程](validation/same-process-blocked.json)、[跨机](validation/cross-host-blocked-final.json) |

矩阵提供 1 KiB、64 KiB、1 MiB、4 MiB 四种消息尺寸，两个 RMW、reliable / best_effort，各重复三次。每次预热 0.5 秒、测量 3 秒、10 Hz，drain 0.5 秒。总发送 1440 条、接收 1292 条；36 个用例全部接收 30 条。剩余 12 个用例都是 1 MiB / 4 MiB best_effort：Fast DDS 分别接收 `15/16/19` 与 `13/15/15`，Cyclone DDS 分别接收 `26/23/27` 与 `16/12/15`，最大接收损失 60%。`status=ok` 表示产生有效测量结果，不表示无损交付或性能达标。

每次延迟统计仅有 12–30 个样本；三次 p99 的 CV 范围约 0.0775–0.6221。这些短时观察不足以稳定估计尾延迟。重复汇总中的平均 p99 是三次 p99 的平均值，不是合并样本的总体 p99。吞吐是固定发送频率下的接收吞吐，不是饱和吞吐；CPU/RSS 包含 Python 进程开销。

## 复现

在已有 Jazzy、两个 RMW 和 rclpy 的 Linux 主机中，从仓库根目录执行；每次使用新的输出目录：

```bash
source /opt/ros/jazzy/setup.bash
python3 scripts/jazzy_baseline/run.py \
  --sizes 1024,65536,1048576,4194304 --qos reliable,best_effort \
  --repeats 3 --duration 3 --warmup 0.5 --margin 0.5 --hz 10 \
  --topic-prefix /jazzy_baseline_reproduction --out /tmp/jazzy-new-matrix
python3 scripts/jazzy_baseline/selftest.py
python3 scripts/run_all_gates.py
```

完整实际命令、UTC 起止时间、输出和退出码在 `validation/*.json`。每个 case 保留原始 worker JSON、延迟样本、进程命令、退出码与 stdout/stderr；环境记录仅保留所需配置，不保存凭据。[独立矩阵审计脚本](validation/audit_matrix.py)重算各项指标和波动并核对源码散列，[审计结果](validation/matrix-audit.json)保留完整输出；[严格 JSON 与 RTT 检查](validation/strict-json-rtt.json)核对全部 JSON、RTT 原始计数、进程退出码和当前源码散列。

矩阵采集时 HEAD 仍为 PR #205 的提交且工作树有修改。其 `source_sha256` 对应代码提交 `faadb365f2211ed9d007d803b72d6fa6e445cd22` 中的 Python 源文件；不能用旧 HEAD 单独复现。本次后续修改只修正 DDS 包名采集、跨机阻断说明及默认发现范围文案；RTT 的源文件散列记录了这些修改。早期 smoke 是更早的修复阶段，保留原始散列和证据，不替代矩阵。

## 中断、恢复与未完成项

初次 macOS Python 3.9 自检因 `platform.freedesktop_os_release` 不存在而退出 1，[原始失败日志](validation/host-selftest.json)保留；现已兼容。worker 失败结果中的 NaN/Infinity 现转换为 JSON `null`，原始结果也强制标准 JSON。

暂存产物的默认 `git diff --check` 将 CSV 的标准 CRLF 行尾和生成 Markdown 的末尾空行报告为格式问题（exit 2），不涉及测量数值。原始产物保持不改写；[源码默认检查](validation/diff-check-source.json)和[允许这两种产物格式的检查](validation/diff-check-artifacts.json)均 exit 0。独立审计的首次工作副本检查也曾因后续三个元数据／文案文件改动而 exit 1；[该输出](validation/matrix-audit-initial-worktree-check.json)保留。最终审计以测量时源码提交为准，明确列出后续差异。

初次 48 项矩阵请求期间终端报 `exec-server transport disconnected`，桌面工具报 `Transport closed`，没有取得最终回执。恢复后的首条真实命令 `date -u '+%Y-%m-%dT%H:%M:%SZ'` 返回 `2026-10-11T11:22:52Z`。随后只读检查 Mac 和 Colima，未发现遗留基准进程，也未发现旧 matrix 输出目录；旧尝试状态不可确认。确认这些条件后才启动本报告中的新矩阵，没有覆盖旧输出或并行运行另一套基准。

任务①仍缺同进程测量实现、跨机编排及两台主机真实验证，且尚未取得目标部署环境中的稳定长时间基线。这里的本机 VM、短时 Python 结果不能视为真机、纯 DDS 或 C++ 客户端性能，不能宣称 10×。任务①不可标记 Done。
