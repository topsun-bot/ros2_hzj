# 评估驱动改进循环 — 迭代日志

> 任务来源：用户《3》评估驱动改进循环 + 每小时定时任务「ros2_hzj DDS 重构优化循环（每小时）」。
> 规则：一次只做一项重点改进；每次有意义修改后重跑全部 gate 与 eval；记录分数与变更；
> 不达标不停手、不回退（除非新结果明显更差）；blocked 项如实标注，禁止伪造通过。
> Hold 边界见 `AGENTS.md`：不动 `config/fastdds.xml`、不动 `docs/artifacts/bench/SCOREBOARD.md` 数字、
> 不启用 zenoh/Agnocast、不改 `dimos_bridge` 运行时、不集成 Cega。

## 评分口径

| 指标 | 命令 | 含义 |
| --- | --- | --- |
| Gate 通过率 | `python3 scripts/run_all_gates.py` | 12 个既有 check/prove 脚本 exit 0 且打印 healthy 标记的比例 |
| Eval 通过率 | `npx --yes promptfoo@0.123.1 eval -c evals/promptfooconfig.yaml`（仓库根执行） | 12 个 DDS 行为断言用例（custom provider 跑 gate 脚本 + stdout contains 断言） |

- Gate / Eval 衡量的是**仓库一致性与 Hold 合规性**，不是端到端 DDS 延迟（本机无 Humble runtime，
  端到端 pub/sub、p99、跨机 UDP 为 `STATUS: blocked`，见 `docs/testing/2026-09-mac-hil.md`）。
- bench 分数以 `docs/artifacts/bench/SCOREBOARD.md` 为只读权威，本循环不改其数字。

---

## 轮次 0 — 2026-09-19 16:40（Asia/Shanghai）基线固化轮（手动立即触发）

### 本轮改动
- **无生产代码改动**。本轮目标是把《1》《2》《4》《5》《6》+ 外部调研的首批产物固化并推送到 GitHub。
- 纳入本轮的既有提交（子代理产出，此前未 push）：
  - `e194f98` feat(eval): add run_all_gates runner and 2026-09 loop log
  - `ec8cfb2` docs(refactor): add DDS request-flow walkthrough and modernization plan
  - `b7ff4b1` test(eval): scaffold Promptfoo suite over local gate scripts
  - `121d1a5` docs(security): read-only vendor CVE audit (2026-09)
  - `85b00a9` docs(absorb): add 2026-09 CN/JP ROS 2 DDS survey (15 items)
  - `d88195b` docs(testing): Mac HIL triage report (2026-09)

### 分数（重跑实测，非引用子代理记录）
- Gate：**12/12 exit 0，marker 12/12，通过率 100%**（`run_all_gates.py` 实测）。
- Eval：**12 passed (100%) / 0 failed / 0 errors，Duration 1s**
  （promptfoo 0.123.1，eval ID `eval-MYO-2026-09-19T08:40:17`）。

### 产物检查
- `docs/refactor/01-dds-request-flow.md`：六层走查、gate 强制假设、4 个陷阱、有序阅读清单。
- `docs/refactor/02-modernization-plan.md`：grep 取证的死代码/桩/重复/过大模块/遗留模式清单，
  按「删死代码 → 简化控制流 → 抽辅助函数 → 替换陈旧模式」排序，含 Hold 越界项拆分与验证映射。
- `docs/security/2026-09-vendor-cve-audit.md`：只读审计，**已确认暴露 2 / 需验证 4 / 已排除 9**，
  每条带文件引用。
- `docs/testing/2026-09-mac-hil.md`：3 个本机可执行用例全 PASS，阻塞性问题 0；
  真·pub/sub 因无 Humble runtime blocked（与既有 `feishu-three-chain-repro.md` 一致）。
- `docs/architecture/cn-jp-ros2-absorb.md`：增补 15 条大陆/日本 DDS 优化可吸收项（6.1–6.15）。
- `evals/`：custom provider + 12 seed 用例 + 基线记录；未触碰生产代码。

### 剩余风险 / 薄弱环节
1. **[安全·高]** Unitree 机器人侧 bundled Cyclone 0.10.2：CVE-2024-10838（HIGH）、
   CVE-2025-67109（CRITICAL）已确认暴露；合法修复路径为 `unitree_sdk2_hzj` +
   `UNITREE_DDS_PROVIDER=external` 指向 ≥0.10.5（Hold：不在本仓直接改 bundled 二进制）。
2. **[验证缺口]** macOS 无 Humble runtime，端到端双链 pub/sub、延迟 p99、跨机 UDP 无法本机闭环；
   需一台 `/opt/ros/humble` Linux 主机（Mac HIL 报告已列两条追加用例）。
3. **[输入缺口]** 4 份飞书方案文档读取返回 3380004 无权限；《2》分析目前仅基于仓内源码，
   授权后需补读并对齐。
4. **[供应链·中]** `scripts/bench/requirements-chain-b.txt` 浮动依赖未上锁；
   `install-base.sh` rosdistro GPG key 拉取未钉 SHA（CVE 报告 §4.2 第 3、4 条）。
5. `docs/01-dds-request-flow.md`（仓库根，2026-09-15 用户旧草稿，37KB）与
   `docs/refactor/01-dds-request-flow.md`（本轮新版，24KB）同名不同内容；
   旧稿为用户未跟踪文件，**本轮保持原样不动**，待用户决定合并或删除。

### 下一步（轮次 1 候选，按优先级）
1. 按 `02-modernization-plan.md` 的第 1 阶段执行**第一项小步重构：删除已 grep 取证的死代码**
   （仅删计划中标注且有验证映射的条目；删后重跑 12 gate + 12 eval，必须保持 100%）。
2. 为 `requirements-chain-b.txt` 补锁（生成 lock 文件，不改 Hold 文件）。
3. 飞书文档权限恢复后补读，回填《2》对齐差异。

---

## 轮次 1 — 2026-09-19 17:18（Asia/Shanghai）Step 2：提取冻结路径公共辅助

### 本轮改动（一项重点改进，纯提取重构，行为不变）
- 新增 `scripts/_freeze_paths.py`（下划线前缀，不进 CI 命令清单）：冻结路径
  `FASTDDS_XML_REL`、`SCOREBOARD_REL` 与两条 existence-only hint 常量的**单一真源**。
- 8 个闸门脚本删除本地重复定义，改为 import：
  - 6 个三元组脚本（check_three_chain_repro / check_dod_evidence /
    check_unitree_cyclone_swap / check_cega_bridge_hold / check_sink_layers /
    check_dual_chain_baseline）：路径常量 + 两条 hint 字面量收敛；
  - check_risk_matrix：仅路径常量（它对两文件做内容断言，不用 existence hint）；
  - print_bench_gates：仅 SCOREBOARD 路径常量。
- 消除 §1.2 盘点的 7–8 份 `XML_REL/SCOREBOARD_REL` 拷贝与 6 份 hint 串拷贝。
- 与计划的偏差（有依据）：计划提到的 `check_existence(rel)` 辅助**未引入**——各脚本
  存在性失败渲染文案不同、无独立重复模式，强加会变成无调用者的死代码，与重构目标矛盾；
  本轮只收敛真正重复的常量与串。
- 机械化替换带命中次数断言（每处恰好 1 次命中，否则中止不写盘）。

### 验证（行为不变证据）
- **stdout 逐字节对比**：12 个 gate 脚本重构前后输出 `cmp` 全部 IDENTICAL，exit 全 0。
- `python3 -m compileall`：新模块 + 全部脚本编译通过。
- `python3 scripts/run_all_gates.py`：**12/12 exit 0，marker 12/12**。
- promptfoo 0.123.1：**12 passed (100%) / 0 failed / 0 errors，Duration 0s**。
- CI 兼容性已核对：structure job 为 `test -f` 存在性清单（不限制新增文件）；
  contracts/boundary job 以 `python3 scripts/<gate>.py` 从仓库根调用，
  `sys.path[0]=scripts/`，同目录 import 可用。
- 本轮无新增行为，未新增 eval 用例（被改的 8 个脚本本就被现有 12 用例覆盖）。

### 分数
- Gate：12/12（100%），与轮次 0 持平（本轮目标是去重，不应改变分数）。
- Eval：12/12（100%），与轮次 0 持平。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、
   飞书 3380004、bench 依赖未锁）。
2. 本轮只做 A 面（我们自己的脚本）；Step 3（抽 `_md_paths.py` 收敛
   check_source_map/check_executor_map 的 md 路径解析）为下一候选。
3. 冗余 PR #47 已关闭并删除分支（内容已由 #48 合并）。

### 下一步（轮次 2 候选）
1. Step 3：抽 `scripts/_md_paths.py`，收敛 check_source_map.py（320 行）与
   check_executor_map.py（407 行）同构的 md 路径解析/符号查找/WARN-FAIL 渲染；
   仍要求 stdout 逐字节不变。
2. 视批准情况推进 CVE 修复独立 PR（external Cyclone ≥0.10.5、requirements 补锁）。

---

## 轮次 2 — 2026-09-19 17:51（Asia/Shanghai）Step 3：抽 _md_paths.py 收敛 md 引用解析

> 用户手动「确认，立即执行」，未等 18:07 定时触发。分支 `refactor/md-paths-helper`，PR #50。

### 本轮改动（一项重点改进，纯提取重构，行为不变）
- 新增 `scripts/_md_paths.py`（256 行，下划线前缀辅助模块，不进 CI 命令清单）：
  - 共享：`REPO_PREFIXES`、`LINK_RE`/`FENCE_RE`/`TICK_PATH_RE`/`FILE_LINE_RE`、
    `repo_root(map_rel)`（锚点参数化）、`ident_re`/`symbol_lines`（标识符正则缓存）、
    `looks_like_repo_path`、`to_repo_rel`、`parse_map`、`read_utf8`、
    `check_cited_paths`（cited 路径存在性 + allowlist 符号检查 + stale WARN 渲染循环）。
  - 两个调用方的**行为差异显式参数化保留**，不做静默统一：
    - `reject_bare_words=True`（仅 executor）：裸 prose 词（无 `/` 无后缀，如
      `` `dimos_bridge` ``）不算路径引用；source_map 保持 False（原行为）。
    - `absent_keys=`（仅 executor）：作为"应当缺席"引用的 `vendor/rcl*` 不要求存在；
      source_map 传空（原行为）。
- check_source_map.py：320 → **143 行**（-177）；check_executor_map.py：407 →
  **225 行**（-182）；两脚本合计删 381 行重复、新增 helper 256 行，净 -125 行，
  md 引用解析/符号检查从此单点维护。
- render 主体（executor 的 REQUIRED_DOCS / DOC_MARKERS / FEISHU_URLS /
  ABSENT_VENDOR_TREES / uncited 检查、source_map 的 map-missing 早退）**不抽取**，
  保持各自语义边界清晰。
- 顺带消除 executor 原 `_parse_map` link 循环缺少 `line = None` 初始化、可能残留
  上一迭代行号的隐患，统一为带初始化版本；实测当前文档未触发该路径（stdout 不变）。

### 验证（行为不变证据）
- **stdout 逐字节对比**：12 个 gate 脚本重构前后输出 `cmp` 全部 IDENTICAL，exit 全 0
  （基线 /tmp/iter1_after，重构后 /tmp/iter2_after）。
- `python3 -m compileall`：新模块 + 两个改写脚本编译通过；无残留未用 import
  （`re` 已随辅助块移除，`Path`/`sys` 仍被常量与 main 使用）。
- `python3 scripts/run_all_gates.py`：**12/12 exit 0，marker 12/12**。
- promptfoo 0.123.1：**12 passed (100%) / 0 failed / 0 errors，Duration 1s**。
- CI 兼容性同轮次 1 结论（structure 为 `test -f` 清单；contracts/boundary 同目录 import 可用）。
- 本轮无新增行为，未新增 eval 用例（两个被改脚本本就被现有 12 用例覆盖）。

### 分数
- Gate：12/12（100%），与轮次 1 持平（纯去重不应改变分数）。
- Eval：12/12（100%），与轮次 1 持平。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、
   飞书 3380004、bench 依赖未锁）。
2. `check_cited_paths` 现在是两个闸门的公共渲染路径，后续修改必须同时回归两个脚本；
   stdout cmp 目前靠手动 /tmp 基线，尚未沉淀为仓内可复跑回归。
3. executor link 行号解析旧隐患虽消除，但当前 markdown 无覆盖该分支的真实样本；
   属于 eval 对真实 DDS 行为断言覆盖不足的一部分。

### 下一步（轮次 3 候选）
1. Step 4：双链域常量（domain 42 / 0、rmw 标识、XML 路径）单一真源——计划标注
   "需小心"：chain_a.sh/chain_b.sh 的字面 `export` 串被 check_dual_chain_baseline
   锚定，**不得**改成 `source config/env/load.py`；先做只影响 Python 侧的收敛。
2. 或把"重构前后 stdout 逐字节 cmp"沉淀为可复跑回归（先评估与现有 gate 是否重复，
   避免造死代码）。
3. 视批准情况推进 CVE 修复独立 PR（external Cyclone ≥0.10.5、requirements 补锁）。

---

## 轮次 3 — 2026-09-19 18:18（Asia/Shanghai）Step 4：env 单一真源交叉一致性检查

> 定时任务第 3 轮（18:07 档）。分支 `refactor/env-source-truth-crosscheck`，PR #51。
> 本轮是**行为增强**（新增一致性断言），不是纯提取：被增强 gate 的 stdout 有意新增 4 行；
> 其余 11 个 gate stdout 仍要求逐字节不变。

### 背景 / 当前行为
- 计划 §1 盘点：双链契约值（A=rmw_fastrtps_cpp/域 42/fastdds.xml、
  B=rmw_cyclonedds_cpp/域 0）在**三处**各写一遍——`config/env/load.py`、
  `chain_a.sh`/`chain_b.sh` 字面 export、`dimos_bridge/dual_chain_env.py` 薄包装
  （B 面 `dds_topics.py` 第四处由 contracts job 断言，本轮不动）。
- 旧 `check_dual_chain_baseline.py` 只对 shell 做**单侧字面锚定**，从不读 load.py：
  若 load.py 的 42 被改成 43 而 shell 不动，全部 gate 仍绿——真源漂移不可见。

### 本轮改动（一项重点改进）
- `scripts/check_dual_chain_baseline.py` 新增「env 单一真源」段（importlib 加载，
  零第三方依赖，vanilla 可跑），4 条新断言：
  1. **env truth**：load.py `CHAIN_A/CHAIN_B` 值等于契约（rmw 标识、域 42/0、
     profiles 解析到真实 `config/fastdds.xml`、`CYCLONEDDS_URI` 在 `CHAIN_B_UNSET`），
     且 import load.py + wrapper 前后 `os.environ` 四个相关键快照不变（import 纯净）；
  2. **env cross-check A**：解析 chain_a.sh 字面 export（去引号、`${_ROS2_HZJ_ROOT}`
     归一化）与 load.py `CHAIN_A` 逐项相等，含 profiles 绝对路径等价；
  3. **env cross-check B**：chain_b.sh 的 RMW/域与 `CHAIN_B` 相等；
  4. **env wrapper**：`dimos_bridge/dual_chain_env.py` 的 `CHAIN_A/CHAIN_B` 与
     `chain_a_env()/chain_b_env()` 与 load.py 等值。
  任一项失败 → FAIL 行 + exit 1；两个既有 success marker 仅在全绿时打印（语义不变）。
- `dimos_bridge/dual_chain_env.py`：按 Step 4 计划补 **docstring 注释**，明确
  load.py 是唯一可执行真源、薄包装不得复制常量（零代码行为变化；该文件无 gate
  对其内容做整串断言，已 grep 核实）。
- `evals/promptfooconfig.yaml`：新增第 13 个用例（同跑 check_dual_chain_baseline，
  4 条 contains 断言锁定新交叉检查的健康输出）；`evals/README.md` 用例表 12→13。
- **未做（Hold）**：chain_a.sh/chain_b.sh 一字未改（baseline 与 boundary job 锚定
  字面 export，禁止 `source load.py`）；未碰 load.py 契约值、fastdds.xml、dds_topics.py。

### 负向测试（证明新断言不是摆设，/tmp 夹具，未入仓）
- A. load.py 域 42→43、shell 保持 42：**抓到** `FAIL env truth` +
  `FAIL env cross-check chain_a.sh != load.py CHAIN_A`，exit 1；
- B. wrapper 重导出伪造值：**抓到** `FAIL env wrapper`，exit 1；
- C. load.py import 时写 `os.environ`：**抓到** `import mutated os.environ`，exit 1；
- D. 健康夹具：4 行 env ok 全亮。

### 分数前后对比
- Gate：**12/12（100%）**，脚本数不变（增强现有 gate，未新增脚本，CI 枚举无需改）。
- Eval：**12 → 13 用例，13/13 passed (100%)，0 failed / 0 errors，1s**。
- 其余 11 个未改 gate：stdout 逐字节 `cmp` 全部 IDENTICAL。
- `python3 -m compileall`（scripts + dual_chain_env.py + load.py）通过；
  `load.py print-a/print-b` 输出契约不变。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、
   飞书 3380004、bench 依赖未锁）。
2. 第四处真源 `dds_topics.py`（B 面）与 load.py 之间仍无直接交叉断言；目前由
   contracts job 分别断言两侧常量值（42/0），属于 B 面 Hold，不在本步合并。
3. 负向测试夹具是一次性 /tmp 脚本，未沉淀为仓内回归；stdout 指纹/负向漂移的
   可复跑化仍是后续候选。

### 下一步（轮次 4 候选）
1. 计划 §5.3 第 1 条静态一致性检查：`scripts/check_*.py` 不得再硬编码
   `config/fastdds.xml` / `docs/artifacts/bench/SCOREBOARD.md` 字面量（helper 除外），
   防止 Step 2 去重回潮——评估作为新 gate（gate 数 12→13，需同步 ci.yml/structure/
   run_all_gates/ci-cd-gates.md/eval）还是并入现有 gate。
2. 或 stdout 指纹/负向漂移可复跑回归（先评估与现有 gate 重复度，避免造死代码）。
3. 视批准情况推进 CVE 修复独立 PR。
