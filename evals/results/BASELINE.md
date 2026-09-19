# 基线运行记录

> **状态：初始基线存档（historical snapshot，勿当当前基线）。**
> 本文件是 2026-09-19 套件刚落地时的**首次**运行存档：当时只有 **12 个 seed 用例**，命令写作
> `promptfoo@latest`（实际缓存解析到 0.123.1）。下方 12/12 等历史数字按存档原样保留、**不回改**。
> 套件此后经迭代 3/4/6/7/8 扩展到 **17 个用例**（新增 env 交叉断言、frozen gate、双链真值 print-a/print-b、
> 全量 stdout 指纹 #17），运行命令也**固定为 `promptfoo@0.123.1`**。
> 当前权威口径与最新分数见 [`../../docs/refactor/ITERATION_LOG.md`](../../docs/refactor/ITERATION_LOG.md)
> 顶部「评分口径」与各轮记录；用例清单与运行方式见 [`../README.md`](../README.md)、
> 配置见 [`../promptfooconfig.yaml`](../promptfooconfig.yaml)。

- 命令：`npx --yes promptfoo@latest eval -c evals/promptfooconfig.yaml`
- 运行目录：仓库根 `/Users/zhang/colima-work/ros2_hzj`
- 日期：2026-09-19（Asia/Shanghai）
- promptfoo 版本：0.123.1（npx 缓存）
- Node：v22.23.2

## 结果

```
Results:
  ✓ 12 passed (100%)
  0 failed (0%)
  0 errors (0%)
Duration: 1s (concurrency: 4)
```

- eval ID：`eval-3Om-2026-09-19T08:33:50`
- 通过 12 / 失败 0 / 错误 0。
- 12 个 seed case 全部命中各自的 stdout 关键串，且脚本退出码均为 0。

原始终端输出见 [`baseline_raw.txt`](baseline_raw.txt)。

## 备注

- 首次 `npx` 冷下载 promptfoo 会超过 120 秒；本基线已预热 npx 缓存后在 120 秒内跑完（实际 1 秒）。
- 本基线只反映"脚本在本机当前文件系统状态下退出 0 且打印预期 healthy 串"，
  不是端到端 DDS 延迟、不是 cross-host 实测、不是 Feishu 现场证明（与各 gate 脚本自身的 disclaimer 一致）。
