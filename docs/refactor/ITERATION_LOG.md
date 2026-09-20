# 评估驱动改进循环 — 迭代日志

> 任务来源：用户《3》评估驱动改进循环 + 每小时定时任务「ros2_hzj DDS 重构优化循环（每小时）」。
> 规则：一次只做一项重点改进；每次有意义修改后重跑全部 gate 与 eval；记录分数与变更；
> 不达标不停手、不回退（除非新结果明显更差）；blocked 项如实标注，禁止伪造通过。
> Hold 边界见 `AGENTS.md`：不动 `config/fastdds.xml`、不动 `docs/artifacts/bench/SCOREBOARD.md` 数字、
> 不启用 zenoh/Agnocast、不改 `dimos_bridge` 运行时、不集成 Cega。

## 评分口径

| 指标 | 命令 | 含义 |
| --- | --- | --- |
| Gate 通过率 | `python3 scripts/run_all_gates.py` | 13 个 check/prove 脚本 exit 0 且打印 healthy 标记的比例 |
| Eval 通过率 | `npx --yes promptfoo@0.123.1 eval -c evals/promptfooconfig.yaml`（仓库根执行） | 27 个 DDS 行为断言用例（custom provider 跑 gate 脚本 / `load.py print-a|b` + stdout contains 断言；#17 为全量 stdout 指纹回归；#18 为 frozen-path guard 的负向自测；#19 为双链 env 交叉断言 guard 的负向自测；#20 为 Unitree Cyclone 交换裁决 guard 的负向自测；#21 为 ros2-source-map guard 的负向自测；#22 为 Executor/WaitSet map guard 独有分支的负向自测；#23 为产品 DoD 诚实性 guard 反伪造逻辑的负向自测；#24 为 Cega / Bridge Hold guard 独有 ADR 表格 cell 解析/内置行自检/中文“已接 Cega”伪造/首行 Status 的负向自测；#25 为 runtime-provenance guard 独有 Dockerfile Humble 钉版三分支/VERSIONS 树名与 40 位 SHA 同行约束的负向自测；#26 为 sink-layers guard 独有六层表格行首粗体标签锚定（防裸词 rcl 误匹配 app 行 rclpy、防满屏 DDS 散文救回缺失行）的负向自测；#27 为 three-chain 复现 guard 独有 `map = reproduce` 等号矛盾句 / `three-chain repro: PROVEN` 伪造正则（phrase/status 存在性检查抓不到的追加矛盾句，含同行禁止句豁免）的负向自测） |

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

---

## 轮次 4 — 2026-09-19 19:22（Asia/Shanghai）§5.3 规则 1：冻结路径字面量防回潮 gate

> 定时任务第 4 轮。分支 `refactor/frozen-path-literal-gate`，PR #52（ci.yml 接线待 workflow scope，另开独立 PR）。
> 本轮是**新增静态一致性 gate（防回潮 regression guard）+ 一处等价收敛**：
> gate 数 12→13、eval 13→14；除被收敛的 1 行与新增 gate 外，其余 gate stdout 逐字节不变。

### 背景 / 当前行为
- 现代化计划 §5.3 规则 1 要求：除真源 helper `scripts/_freeze_paths.py` 外，
  gate 脚本不得再用 `Path(...)` 各自硬编码 `config/fastdds.xml` /
  `docs/artifacts/bench/SCOREBOARD.md`。Step 2（轮次 1）已把既有拷贝收敛，
  但**没有机器拦截**——后续提交随时可能重新引入第二份 `Path("config/fastdds.xml")`，
  让去重回潮。
- grep 取证（本轮基线）：除 `_freeze_paths.py` 外，gate python 已无 `Path(...)`
  冻结路径构造；残留仅为输出文案/marker（check_sink_layers 中文 Hold 串、
  run_all_gates docstring）、`bench/*.sh` 与 `bench/README.md`（非 gate python）、
  以及轮次 3 新引入的一处 `endswith("config/fastdds.xml")`（逻辑非常量）。

### 本轮改动（一项重点改进）
- **新增 `scripts/check_frozen_path_literals.py`（第 13 个 gate，marker
  `Frozen-path literals healthy`）**：静态扫描 `scripts/` 顶层 `*.py`（glob 不递归
  `bench/`），用正则只检测 `Path(...)` 构造里嵌入的冻结路径（允许 r/b/u/f/rf 字符串
  前缀）；命中即打印 `rel:lineno` + 代码块并 exit 1。
  - 豁免：真源 `_freeze_paths.py`（定义处）与该 gate 自身。
  - **刻意收窄检测边界**：输出文案/中文 Hold 串、`endswith(...)`、正则模式串、
    从 helper 的 import 一律不判违规——只拦"第二份路径构造"，不拦"提及"。
  - 首次运行即全绿（属防回潮 guard，不是修现存违规）。
- **等价收敛 1 处**：`scripts/check_dual_chain_baseline.py` 轮次 3 引入的
  `endswith("config/fastdds.xml")` 改为 `endswith(XML_REL.as_posix())`
  （`XML_REL` 即该文件已 import 的 `FASTDDS_XML_REL` 别名）；FAIL 文案串保留原样。
- 接线（本地侧已完成）：`scripts/run_all_gates.py` GATES 末尾登记（其 docstring 原写
  "The 13 gates" 在 12 gate 时是陈旧笔误，加完正好 13，数字变正确）；
  `docs/architecture/ci-cd-gates.md` §6 本地核对清单收录（§1 的 CI 实跑清单暂不收录，原因见下）。
- **CI 接线阻塞（凭证 scope，未入库）**：给 `.github/workflows/ci.yml` structure job 加
  `test -f` 存在性 + 运行 step（跑脚本并 grep marker）的改动已写好并通过 YAML 解析，但推送被
  GitHub 拒绝：当前推送账号 `yixinzhangagent` 的 OAuth token 只有 `gist/read:org/repo`、
  **缺 `workflow` scope**（改 `.github/workflows/*` 必须该 scope）；另一台账号
  `zhangyinxina-ui` 虽有 `workflow` scope，但对 `topsun-bot/ros2_hzj` 无 push 权限（403）。
  按流程不硬闯、不绕过保护：ci.yml 改动**不进本 PR**，新版离线备份于
  `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`，待授予 `workflow` scope 后以
  **独立 PR** 补接线。合入前该 gate 在本地 `run_all_gates.py` 生效（本地 13/13），CI 仍跑
  原 12 个 gate（structure 为枚举式 `test -f`，不限制新增文件，故新文件不影响 CI 红绿）。
- eval：`evals/promptfooconfig.yaml` 新增第 14 个用例（跑新 gate + contains
  `Frozen-path literals healthy`）；`evals/README.md` 用例表 13→14。
- **未做（Hold）**：未碰 `config/fastdds.xml`、`SCOREBOARD.md`、shell 字面 export、
  `dimos_bridge` 运行时、vendor 树；未启用 zenoh/Agnocast；未做框架/依赖/API 变更。

### 负向测试（证明 gate 不是摆设，/tmp 夹具，未入仓）
- 构造 `bad_gate.py`：第 2 行 `Path("config/fastdds.xml")`、第 3 行
  `Path("docs/artifacts/bench/SCOREBOARD.md")` → 被精确报 `scripts/bad_gate.py:2`
  与 `:3`，exit 1；
- 构造 `ok_gate.py`：import helper 常量 + prose 提及 + `endswith(...)` + 正则模式串
  → 全部不被误报，exit 0；
- 真仓 14 个顶层 .py 正向扫描：全绿 exit 0。夹具测完即删。

### 分数前后对比
- Gate：**12 → 13，13/13 exit 0，marker 13/13，通过率 100%**（`run_all_gates.py` 实测）。
- Eval：**13 → 14 用例，14 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1）。
- 行为不变证据：
  - 11 个未改 gate 与轮次 3 stdout 基线 `/tmp/iter3_after` 逐字节 `cmp` 全 IDENTICAL；
  - `check_dual_chain_baseline.py` 仅 endswith 等价收敛，HEAD 版 vs 工作区版
    stdout `cmp` IDENTICAL（两版均 exit 0）；
  - `python3 -m compileall scripts` 通过；**待接线**的 ci.yml 新版（离线备份）经 ruby
    YAML 解析合法、无 tab、新增 test -f 与 grep step 均在，但该文件本轮**未入库**（见上
    凭证 scope 阻塞）；`load.py print-a/print-b` 契约不受影响。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、
   飞书 3380004、bench 依赖未锁）。
2. **[凭证·阻塞 CI 接线]** 推送账号 `yixinzhangagent` 缺 GitHub `workflow` scope，
   本轮 ci.yml 改动无法入库（已离线备份）；需用户在本机执行一次
   `gh auth refresh -h github.com -s workflow`（浏览器授权）或换用对本仓有写权限且带
   workflow scope 的凭证，之后补一个仅含 ci.yml 接线的独立 PR。
3. 新 gate 只覆盖 `scripts/` 顶层 python 的 `Path(...)` 构造；`bench/*.sh`、
   markdown、其他语言暂不扫（刻意收窄，避免文案误报）。若未来冻结路径真源扩展到
   shell 侧，需要另立规则。
4. 计划 §5.3 规则 2（新增无下划线前缀 `scripts/*.py` 必须登记 ci-cd-gates §1/§6，
   否则 structure 不认识）目前仍靠手工遵守（本轮新增 gate 已在本地 runner/§6 登记，
   CI §1 待接线 PR 一并补），尚未机器化。

### 下一步（轮次 5 候选）
1. **（阻塞解除后优先）** 授予 `workflow` scope，用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补一个仅含 ci.yml 接线的
   独立 PR（structure 的 test -f + 运行 step），并把 ci-cd-gates.md §1 表格补登、
   去掉 §6 的 pending 说明。
2. §5.3 规则 2 机器化：静态核对每个无下划线前缀的 `scripts/check_*.py` 都在
   ci.yml structure 与 ci-cd-gates.md §1/§6 登记（先评估与现有 structure `test -f`
   清单的重复度，避免造死代码）。
3. 或 stdout 指纹/负向漂移沉淀为仓内可复跑回归（同上，先评估与 run_all_gates 的
   重复度）。
4. 视批准情况推进 CVE 修复独立 PR（external Cyclone ≥0.10.5、requirements 补锁、
   rosdistro key 钉 SHA）。

---

## 轮次 5 — 2026-09-19 20:24（Asia/Shanghai）Step 3 延伸：抽 `_repo.py` 收敛 repo-root/读取样板

> 定时任务第 5 轮。分支 `refactor/repo-root-helper`，PR #53。
> **纯提取重构，行为不变**：不新增 gate、不碰 `.github/workflows/ci.yml`（`workflow` scope
> 仍未授予，见轮次 4 阻塞），故不加剧"本地 gate 数 vs CI 枚举"的背离。

### 背景 / 当前行为
- grep 取证：10 个脚本各自逐字复制了同构的私有 `_repo_root()`（cwd 锚点 → `scripts/`
  相对回退 → 找不到 `sys.exit`，错误串逐字相同）与 UTF-8 读取（`_read()` 或内联
  `read_text(encoding="utf-8", errors="replace")`）。`_md_paths.py` 虽已有
  `repo_root(map_rel)`/`read_utf8`，但仅 source_map/executor_map 两脚本使用；让其余
  非 md 解析脚本 import `_md_paths` 仅为这两个通用函数会造成命名误导，故新建名义通用的
  helper。

### 本轮改动（一项重点改进）
- **新增 `scripts/_repo.py`（下划线前缀共享库，不进 CI 命令清单）**：
  - `repo_root(*anchors)`：支持一或多个锚点文件（任一 `is_file()` 即认定 root），
    cwd 锚点 → `scripts/` 父目录回退 → 找不到时 `sys.exit`，错误串与原各脚本逐字一致
    （`cannot find repo root from cwd=... or ...`）；无锚点调用 `raise ValueError`（编程错误）。
  - `read_utf8(path)`：`read_text(encoding="utf-8", errors="replace")`，与各脚本 `_read` 逐字一致。
  - docstring 写明**不承载业务断言**（计划 §5.3 helper 边界 spec），锚点常量/必需标记/
    allowlist/渲染仍归各 gate。
- 9 个脚本删除私有 `_repo_root()`+`_read()` 整块、改 `from _repo import repo_root, read_utf8`，
  并把 `(root or _repo_root())` 替换为带各自锚点的显式调用：
  check_cega_bridge_hold（HOLD/ADR）、check_sink_layers（SINK/ADR）、
  check_three_chain_repro（REPRO/ADR）、check_dod_evidence（DOD/ADR）、
  check_unitree_cyclone_swap（SWAP/VERSIONS）、check_runtime_provenance（PROVENANCE/MANIFEST）、
  check_risk_matrix（MATRIX/ADR）、check_dual_chain_baseline（BASELINE/ADR）、
  print_bench_gates（SCOREBOARD/METHOD）。
- check_frozen_path_literals.py（轮次 4 新建、自身也复制了样板）：私有 `_repo_root()`
  改为 `repo_root(SCRIPTS_REL / HELPER_NAME)`，扫描循环内联 `read_text(...)` 改为 `read_utf8(path)`。
- 机械化替换带命中次数断言（helper 块恰好 1、root 调用恰好 1、`_read(` 调用数逐脚本核对），
  替换后断言 `_repo_root`/`_read` 标识符零残留；`import sys`（各脚本 main 仍用
  `sys.stdout.write`）与 `from pathlib import Path`（仍大量使用）经核对保留。
- **净 −135 行**（10 个被改脚本 33 增 / 168 删；另新增 `_repo.py`）。
- **未做（Hold / 边界）**：未改 `_md_paths.py` 及其两个消费方（已稳定，缩小爆炸半径）；
  未碰 ci.yml、fastdds.xml、SCOREBOARD.md、shell 字面 export、`dimos_bridge` 运行时、vendor；
  无框架/依赖/API 变更；无新增行为，故未新增 eval 用例。

### 验证（行为不变证据）
- 重构前基线 `/tmp/iter5_before/`（13 gate + print-a/print-b 共 15 份 stdout），重构后
  `/tmp/iter5_after/` 逐字节 `cmp`：**14/15 IDENTICAL**。
- 唯一差异：`check_frozen_path_literals.py` 的动态计数 `ok scanned: 14 → 15`
  （新增共享库 `_repo.py` 进入 `scripts/*.py` 扫描面；`_repo.py` 不含冻结路径构造，被正确
  判为干净，marker 与 exit 0 不变）。该数字是 `len(glob)` 动态值、非契约（CI 与 eval #14
  只断言 `Frozen-path literals healthy`），属新增文件的预期变化，非行为回归。
- `python3 -m compileall scripts` 通过；全仓 `grep` 确认无私有 `def _repo_root`/`def _read` 残留。
- `python3 scripts/run_all_gates.py`：**13/13 exit 0，marker 13/13，all gates green**。
- promptfoo 0.123.1：**14 passed (100%) / 0 failed / 0 errors，Duration 1s**
  （eval ID `eval-fag-2026-09-19T12:24:13`；frozen 用例在 scanned=15 下仍 PASS）。
- `load.py print-a/print-b` stdout 逐字节 IDENTICAL。

### 分数
- Gate：13/13（100%），与轮次 4 持平（纯提取，不新增 gate）。
- Eval：14/14（100%），与轮次 4 持平。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、
   飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** `workflow` scope 未授予：第 13 个 gate 的 ci.yml 接线仍离线备份于
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`，CI structure 仍只枚举原 12 个；
   本轮刻意不新增 gate，以免背离继续扩大。
3. `repo_root` 现为 10 个脚本共享的公共路径，后续修改其回退/退出语义须全量回归这些 gate
   （stdout 指纹目前仍靠手动 /tmp 基线，未沉淀为仓内回归）。

### 下一步（轮次 6 候选）
1. **（阻塞解除后最高优先）** 授予 `workflow` scope（`gh auth refresh -h github.com -s workflow`），
   用离线备份补仅含 ci.yml 接线的独立 PR，并回填 ci-cd-gates.md §1、删除 §6 pending 说明。
2. ci.yml 接线完成后再做 §5.3 规则 2 机器化（新无下划线 `scripts/*.py` 必须登记 CI 与
   ci-cd-gates §1/§6）——接线前做会与 frozen gate 的"故意未登记 CI"pending 状态自相矛盾。
3. stdout 指纹/负向漂移沉淀为仓内可复跑回归（先评估与 run_all_gates 的重复度）。
4. 视批准情况推进 CVE 修复独立 PR。

---

## 轮次 6 — 2026-09-19 21:21（Asia/Shanghai）《5》深化：eval 锁定双链真值 + blocked/Hold 实质契约断言

> 定时任务第 6 轮。分支 `feat/eval-chain-contract-assertions`，PR #54。
> `workflow` scope 仍未授予（ci.yml 接线继续阻塞），本轮**不新增 gate、不碰 ci.yml、不改任何
> gate/生产代码**，只深化《5》Promptfoo 套件对**真实双链/DDS 契约行为**的断言覆盖（任务明确的
> 深化方向："扩大 eval 对真实 DDS 行为断言的覆盖，而非放水"）。

### 背景 / 当前行为
- 轮次 0–5 后 14 个 eval 用例中，13 个 gate 用例大多只 `contains` 一个健康 marker；marker 只证明
  "脚本跑到了成功分支"，锁不住关键**裁决句 / blocked 诚实性 / Hold 短语**——若有人把 Unitree 裁决
  从 `drop-in FAIL` 翻成 PASS、把三链复现 / DoD 的 blocked 改成已通过、或偷接 Cega，只要 marker 仍在，
  eval 层不会红。
- eval 此前**完全没有**直接执行双链可执行真源 `config/env/load.py`（provider 只接受单脚本路径、
  不能带 `print-a` 参数），链 A=`rmw_fastrtps_cpp/42/fastdds.xml`、链 B=`rmw_cyclonedds_cpp/0`
  只被 gate 间接覆盖。

### 本轮改动（一项重点改进，仅 evals/ 三个文件）
- `evals/localScriptProvider.mjs`：`callApi` 把 prompt 按空白拆成 argv
  （`execFileSync('python3', argv, …)`），支持 `config/env/load.py print-a` 这类带参数命令；
  无空格的旧用例 argv 长度仍为 1，**向后完全兼容**（原 14 用例路径不变即全过）；同步更新注释。
- `evals/promptfooconfig.yaml`（14 → **16** 用例）：
  - **新增 #15/#16**：直接跑 `load.py print-a` / `print-b`，断言链 A
    `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`、`ROS_DOMAIN_ID=42`、profiles 含 `config/fastdds.xml`，
    链 B `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`、`ROS_DOMAIN_ID=0`（绝对路径只断言 `config/fastdds.xml`
    后缀，避免机器相关）。
  - 给 9 个既有 gate 用例补**实质契约短语**（断言串全部取自脚本真实 stdout 逐字，非计划快照）：
    executor `WaitSet -> callback: mapped`；provenance `underlay != vendor snapshot`；
    unitree `drop-in: FAIL / wire: UNPROVEN`；three-chain `map ≠ reproduce` + `STATUS: blocked`；
    sink `sink layers: mapped (Hold vs allowed)`；dual-baseline `pointer only (no XML rewrite)` +
    `same-topology XML tuning is paused`；env 交叉检查补 `ok env truth:` + `rmw_fastrtps_cpp/42` +
    `rmw_cyclonedds_cpp/0` + `CYCLONEDDS_URI in CHAIN_B_UNSET`；dod `DoD: unmet`；cega `no Cega`。
- `evals/README.md`：用例表 14→16 并逐行登记新增断言；provider 机制改为"argv 拆分、可带 CLI 参数"；
  运行命令由 `promptfoo@latest` 固定为 `promptfoo@0.123.1`（与本循环固定命令对齐，消除版本漂移）。

### 验证（行为不变 / 断言有效证据）
- promptfoo 0.123.1：**16 passed (100%) / 0 failed / 0 errors，Duration 1s**
  （eval ID `eval-Q6t-2026-09-19T13:19:38`）；#15/#16 经增强后的 provider 正确执行带参数命令并
  命中链真值；原 14 用例在 argv 增强后仍全过（向后兼容）。
- 所有新增断言串先从脚本真实 stdout grep 取证再写入，无凭空字符串。
- `python3 scripts/run_all_gates.py`：**13/13 exit 0，all gates green**（本轮未改任何 gate，
  回归确认无连带影响）。
- 本轮无生产代码改动，gate 数仍 13、无 stdout 指纹变化；不新增 gate，故不加剧"本地 gate vs
  CI 枚举"背离，也不需要 ci.yml 接线（不受 `workflow` scope 阻塞）。

### 分数
- Gate：13/13（100%），与轮次 5 持平。
- Eval：**14 → 16 用例，16/16（100%）**；9 个用例从单 marker 升级为 marker + 实质契约，
  新增 2 个双链真值用例——覆盖深度提升，而非数字放水。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、
   bench 依赖未锁）。
2. **[凭证·仍阻塞]** `workflow` scope 未授予：第 13 个 gate 的 ci.yml 接线仍离线备份
   （`~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`），CI 仍只枚举原 12 gate。
3. **Promptfoo 目前是本地验收层，CI 不运行它**（structure/contracts/boundary 无 eval step）；
   若未来要在 CI 跑 eval，需评估 runner 联网 npx / 缓存策略，属独立改动。
4. eval 仍是"跑静态 gate 脚本 + stdout 断言"，无法替代真·双链 pub/sub / p99（本机无 Humble，blocked）。

### 下一步（轮次 7 候选）
1. **（阻塞解除后最高优先）** 授予 `workflow` scope，补仅含 ci.yml 接线的独立 PR，回填
   ci-cd-gates.md §1、删除 §6 pending 说明。
2. ci.yml 接线后做 §5.3 规则 2 机器化（新无下划线 `scripts/*.py` 登记完整性静态核对）。
3. stdout 指纹 / 负向漂移沉淀为仓内可复跑回归（先评估与 run_all_gates 的重复度，避免死代码）。
4. 视批准情况推进 CVE 修复独立 PR。

---

## 轮次 7 — 2026-09-19 22:15（Asia/Shanghai）《5》收尾：剩余 3 个单-marker gate 用例补诚实性/Hold 契约断言

> 定时任务第 7 轮。分支 `test/eval-gate-honesty-phrases`，PR #55。
> `workflow` scope 仍未授予（不能新增需 CI 接线的 gate，否则重蹈 frozen gate 的本地/CI 背离），
> CVE 修复仍待用户批准。本轮延续轮次 6 同一主题做**收尾**：轮次 6 后仍有 3 个 gate 用例
> （source_map / print_bench / risk_matrix）只断言健康 marker，本轮把它们各自 stdout 中
> 已有的**诚实性 / Hold / 符号白名单**契约句也锁进 eval。**仅改 evals/ 两个文件，用例数仍 16，
> 不新增 gate、不碰 ci.yml、不改任何 gate/生产代码。**

### 背景 / 当前行为
- 轮次 6 深化了 9 个用例 + 新增双链真值 2 例，但 #2 source_map、#3 print_bench、#4 risk_matrix
  仍只 `contains` marker。这三个 gate 的 stdout 本身印有强契约句，却没被 eval 锁定：
  - print_bench 明确声明跨机延迟 `cross-host: blocked`、`Do not sum segment P99s`（不得把分段
    P99 相加成链路 P99、不得重印 SCOREBOARD 数字）——是延迟诚实性的核心；
  - risk_matrix 印有 §9.4 层级锚点 `§9.4: env/XML first`、`Do not invent risk percentages`、
    `Cross-host stays blocked`——锁层级顺序与"不编风险百分比"；
  - source_map 印有 `allowlisted symbols ok:`——证明 rmw_publish/take、dds_take、WaitSet 等
    被追踪的真实 DDS/RMW 符号仍能在 vendor 源码解析到（vendor 重写/丢符号即应红）。

### 本轮改动（一项重点改进，仅 evals/ 两个文件）
- `evals/promptfooconfig.yaml`：给 3 个既有用例补 contains 断言（用例数不变，仍 16）：
  - #2 source_map：+ `allowlisted symbols ok:`（不锁 24/38 等动态计数，也不锁 `warnings: 0`，
    以免 vendor 升级导致行号 warn-only 漂移时误红；只锁"符号白名单检查通过"这一实质契约）；
  - #3 print_bench：+ `cross-host: blocked`、`Do not sum segment P99s`（均为 stdout 单行短语，
    避开跨行的 `not a latency measurement` 段）；
  - #4 risk_matrix：+ `§9.4: env/XML first`、`Do not invent risk percentages`、
    `Cross-host stays blocked`（均逐字单行）。
- `evals/README.md`：用例表 #2/#3/#4 逐行登记新断言；seed 用例说明中"额外断言实质契约短语"
  的用例数 9 → 12，并把短语类别写为 DDS/Hold/**诚实性**。
- 所有断言串先跑脚本取真实 stdout、确认逐字且在同一行（无 markdown 换行截断）后才写入。

### 验证
- promptfoo 0.123.1：**16 passed (100%) / 0 failed / 0 errors，Duration 2s**（用例数 16 不变，
  断言条数增加；3 个被加深用例与其余 13 例全过）。
- `python3 scripts/run_all_gates.py`：**13/13 exit 0，all gates green**（本轮未改任何 gate）。
- 本轮无生产代码改动，gate 数仍 13、无 stdout 指纹变化；不新增 gate，不加剧本地/CI 背离，
  不需要 ci.yml 接线（不受 `workflow` scope 阻塞）。

### 分数
- Gate：13/13（100%），与轮次 6 持平。
- Eval：**16/16（100%）**，用例数不变；至此 14 个 gate 脚本用例中 12 个为"marker + 实质契约"，
  仅 prove_rmw（`ROS not loaded` 本身即诚实句）与 frozen（marker 即防回潮契约）保持单断言——
  单-marker 薄弱面已清零，覆盖深度继续提升而非放水。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、
   bench 依赖未锁）。
2. **[凭证·仍阻塞]** `workflow` scope 未授予：第 13 个 gate 的 ci.yml 接线仍离线备份
   （`~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`），CI 仍只枚举原 12 gate；
   Promptfoo 仍是本地验收层，CI 不运行。
3. eval 断言的是静态 gate stdout，仍无法替代真·双链 pub/sub / p99 / 跨机 UDP（本机无 Humble，blocked）。
4. source_map 刻意未锁 `warnings: 0` 与具体计数：vendor 升级带来的行号 warn-only 漂移不会让
   eval 误红，但也意味着"出现 stale 行号警告"不会被 eval 抓住（gate 本身 warn-only 不 fail）；
   这是有意的灵敏度取舍，后续若要零 stale 需另立更严断言。

### 下一步（轮次 8 候选）
1. **（阻塞解除后最高优先）** 授予 `workflow` scope，补仅含 ci.yml 接线的独立 PR，回填
   ci-cd-gates.md §1、删除 §6 pending 说明；接线后再做 §5.3 规则 2 机器化。
2. stdout 指纹 / 负向漂移沉淀为仓内可复跑回归：评估作为 eval 用例（经 provider 跑一个比对脚本，
   避免新增需 CI 接线的 gate）的可行性，先确认与 run_all_gates 不重复、且能处理绝对路径/动态计数归一化。
3. 视批准情况推进 CVE 修复独立 PR（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）。
4. eval 深化已基本覆盖静态契约面；后续增量价值转向 CI 接线或真·Humble 主机实测，避免为凑改动制造低价值断言。

---

## 轮次 8 — 2026-09-19 23:10（Asia/Shanghai）《5》沉淀：全量 stdout 指纹回归做成 eval 用例 #17

> 定时任务第 8 轮。分支 `test/eval-stdout-fingerprint`，PR #57（#56 是他人的 ci advisory DRAFT，非本循环产物，未触碰）。
> `workflow` scope 仍未授予、CVE 修复仍待批准，本轮按轮次 7 候选 2 行动：把轮次 1/2/5 一直靠
> 手动 `/tmp` 基线做的"重构前后 stdout 逐字节 cmp"**沉淀为仓内可复跑回归**，并作为 Promptfoo
> 用例接入。关键决策：脚本放 `evals/` 而非 `scripts/`，**不是第 14 个 gate**，因此不进
> `run_all_gates.GATES`、不被 CI structure 枚举、不需要 ci.yml 接线（不受 `workflow` scope 阻塞）。

### 背景 / 与现有层的重复度评估（先证不重复再造）
- `run_all_gates` 只看每个 gate 的退出码 + 一个健康 marker；promptfoo `contains` 只保证关键串
  存在（宽松）。两者都看不到 marker 之外的**意外全文漂移**：多/少一行 ok、计数变化、裁决句被改写
  但仍 exit 0 且 marker 还在，都会绿。轮次 5 抽 `_repo.py` 时正是靠手动 cmp 才发现 frozen gate
  `ok scanned 14→15` 这一预期变化——说明这层有真实价值，但此前不可复跑。
- 三层定位互补、不重复：run_all_gates=红绿（exit+marker）、contains=关键契约不得丢/翻转（宽松）、
  指纹=全文必须等于已评审基线（严格）。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/fingerprint_check.py`（eval-only，标准库零依赖）**：
  - gate 命令清单直接 `sys.path` 引入 `scripts/run_all_gates.GATES`（**单一真源**，不复制 13 个脚本名），
    另加 `config/env/load.py print-a` / `print-b`，共 **15 个命令**；逐个 subprocess 跑、取 stdout。
  - 与 `evals/fixtures/<name>.txt` 归一化后逐字节比对；漂移打印 unified diff（每命令限 60 行）+
    `stdout fingerprint: DRIFT (n/15 stable)` + exit 1；全过打印 `- **commands:** 15` 与
    `- **stdout fingerprint: stable** (...)` + exit 0。
  - `--update` 重生成 fixtures（命令非 0 则拒绝写盘）；默认只读，绝不改仓内文件。
- **新增 `evals/fixtures/*.txt`（15 份基线，共 430 行）**：由 `--update` 从当前 main 真实 stdout 生成。
- **归一化（只抹平环境/噪声，绝不改契约文本）**，grep 取证后只发现两类跨环境不稳定项：
  1. 仓库根绝对路径 → `<REPO_ROOT>`（实测仅 print-a 的 profiles 行命中；13 gate stdout 均不含绝对路径），
     保证换 clone 路径 / CI 也能过；
  2. frozen gate 动态 `**ok scanned:** N` → `<N>`（N=顶层 `scripts/*.py` 文件数，新增 helper/gate 就变，
     属文件数噪声且已由 GATES 登记覆盖）。
  - 其余计数（source-map `cited paths 38 / paths on disk 38 / allowlisted symbols ok 24` 等）**保持精确**：
    它们反映被评审的 map/vendor 内容而非环境，漂移就应在评审中显形。
- `evals/promptfooconfig.yaml`：新增用例 **#17**（跑 `evals/fingerprint_check.py`，断言
  `stdout fingerprint: stable` + `**commands:** 15`，后者锁命令数、防悄悄删覆盖）；用例 16→17。
- `evals/README.md`：文件表加脚本与 fixtures、用例表加 #17、新增"stdout 指纹回归（#17）"小节
  （三层差异、为何不是 gate、归一化规则、`--update` 重生成流程）；顶部评分口径见迭代日志。

### 负向测试（证明严格层不是摆设）
- 向 `evals/fixtures/check_dod_evidence.txt` 追加一行 `EXTRA DRIFT LINE` → 脚本精确报
  `FAIL stdout drift: check_dod_evidence` + diff、`DRIFT (14/15 stable)`、**exit 1**（经 provider 即 eval 失败）；
  `--update` 重生成后恢复 `stable`、exit 0。
- 归一化核验：`load_print_a.txt` profiles 行为 `<REPO_ROOT>/config/fastdds.xml`；frozen fixture 为
  `**ok scanned:** <N>`；`grep -rF /Users/zhang evals/fixtures` 无任何本机路径泄漏；
  `grep token/secret/...` 仅命中 gate 业务短语 "no invented booked percentile tokens"（非密钥）。

### 分数前后对比
- Gate：**13/13（100%）**，与轮次 7 持平（未新增 gate、未改任何 gate，run_all_gates 不受影响）。
- Eval：**16 → 17 用例，17/17 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1）。
- `python3 -m py_compile evals/fingerprint_check.py` 通过；`--update` 与默认比对两轮实测一致。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** `workflow` scope 未授予：第 13 个 gate 的 ci.yml 接线仍离线备份；
   且 **Promptfoo（含新 #17）仍是本地验收层，CI 不运行**——指纹回归目前只在本地/本循环把关，
   未进入 GitHub required checks。
3. 指纹是严格层：**任何有意的 gate stdout 改动都必须在同一 PR 跑 `--update` 并提交 fixtures**，
   否则 #17 红；这是预期的"让输出变化在评审中显形"，但需让后续贡献者知道该流程（已写入 README）。
4. fixtures 只覆盖静态 gate/load.py stdout，仍无法替代真·双链 pub/sub / p99 / 跨机 UDP（本机无 Humble，blocked）。
5. source-map 计数保持精确：vendor 升级导致 cited/symbol 数变化时 #17 会红（需评审 + --update），
   与轮次 7 对 `warnings: 0` 的宽松取舍相反——这是有意的（计数变化比 warn-only 行号漂移更值得评审）。

### 下一步（轮次 9 候选）
1. **（阻塞解除后最高优先）** 授予 `workflow` scope，补仅含 ci.yml 接线的独立 PR（frozen gate
   test-f + 运行 step），回填 ci-cd-gates.md §1、删 §6 pending；接线后可评估把 promptfoo（或至少
   纯 python 的 fingerprint_check.py，无需 npx 联网）纳入 CI——fingerprint 是纯标准库脚本，
   比整套 promptfoo 更适合先接 CI。
2. ci.yml 接线后做 §5.3 规则 2 机器化（新无下划线 `scripts/*.py` 登记完整性静态核对）。
3. 视批准情况推进 CVE 修复独立 PR（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）。
4. eval 静态契约 + 全文指纹两层已较完备；后续增量价值主要在 CI 接线或真·Humble 主机实测，
   继续避免低价值断言堆砌。

---

## 轮次 9 — 2026-09-20 00:12（Asia/Shanghai）Step 3 收尾：`_md_paths.py` 复用 `_repo.read_utf8`

> 定时任务第 9 轮。分支 `refactor/md-paths-reuse-repo-read`，PR #58。
> `workflow` scope 仍未授予、CVE 修复仍待批准，ci.yml 接线与规则 2 机器化继续阻塞。本轮做
> **纯提取重构、行为不变**，且正好用上轮次 8 落地的 stdout 指纹回归作为行为不变的自动证据
> （不再需要手动 /tmp cmp）。这是轮次 5 刻意留下的尾巴：当时为缩小爆炸半径没让 `_md_paths.py`
> 复用 `_repo.py`，现有指纹安全网后补齐。

### 背景 / 当前行为
- 轮次 5 把 10 个脚本的 `_repo_root()`/`_read()` 收敛进 `scripts/_repo.py`，其 docstring 宣称是
  repo-root 查找与 lenient UTF-8 读取的"single home"；但 `scripts/_md_paths.py`（轮次 2 抽出）里
  仍保留一份与 `_repo.read_utf8` **逐字相同**的 `read_utf8(path) = read_text(encoding="utf-8",
  errors="replace")`，是 helper 体系里最后一份该函数的重复拷贝。
- grep 取证：`_md_paths.read_utf8` 被模块内 `check_cited_paths`（读 cited 源文件做符号查找）与
  `check_executor_map.py`（`from _md_paths import ..., read_utf8`，读 map）使用。
- `_md_paths.repo_root(map_rel)` 虽与 `_repo.repo_root` 同构，但**签名（单锚点）与失败串
  （`cannot find {map_rel} ...` vs `cannot find repo root ...`）有意不同**，属不同错误上下文，
  本轮**刻意保留不统一**（与轮次 1 不硬造 `check_existence` 同样的克制：不强行合并语义不同的东西）。

### 本轮改动（一项重点改进，仅 `scripts/_md_paths.py`，净 −3 行）
- 删除本地 `def read_utf8`（3 行），顶部标准库 import 后新增 `from _repo import read_utf8`（1 行）。
- 消费方零改动：`check_executor_map.py` 的 `from _md_paths import ..., read_utf8` 透明拿到
  `_repo.read_utf8`（Python 模块属性转发）；`check_source_map.py` 未直接 import 该名，不受影响。
- `parse_map` 内第 134 行的**严格** `map_path.read_text(encoding="utf-8")`（无 errors="replace"）
  保持原样——它读的是仓内受信任 map、要求严格解码，与 lenient 的 `read_utf8` 语义不同，不合并。
- 不新增/删除文件（frozen gate 的 `scripts/*.py` 计数不变，仍 15）、不新增 gate、不碰 ci.yml。

### 验证（行为不变证据）
- `python3 -m compileall scripts` 通过；`_md_paths.read_utf8 is _repo.read_utf8` 运行时为 **True**（同一函数对象）。
- **stdout 指纹回归（轮次 8 新安全网）**：`python3 evals/fingerprint_check.py` →
  `commands: 15`、`stdout fingerprint: stable`、exit 0——source_map / executor_map 两个消费该 helper 的
  gate 全文逐字节不变，这是本轮行为不变的直接自动证据（替代了轮次 1/2/5 的手动 cmp）。
- `python3 scripts/run_all_gates.py`：**13/13 exit 0，all gates green**。
- promptfoo 0.123.1：**17/17 passed (100%) / 0 failed / 0 errors**（含 #17 指纹用例）。
- import 链无环：`_repo` 仅 import sys/pathlib，不反向依赖 `_md_paths`。

### 分数
- Gate：13/13（100%），与轮次 8 持平（纯提取，不应改变分数）。
- Eval：17/17（100%），与轮次 8 持平。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** `workflow` scope 未授予：frozen gate 的 ci.yml 接线仍离线备份；promptfoo/指纹
   仍是本地验收层，CI 不运行。
3. `_md_paths.repo_root` 与 `_repo.repo_root` 仍各有一份（失败串有意不同）；这是**有意保留的差异**，
   不是遗漏——后续若要统一，必须先确认两个失败串没有被任何文档/断言引用，并作为单独行为变更评审。
4. 指纹/eval 仍只覆盖静态 gate 输出，真·双链 pub/sub / p99 / 跨机 UDP 本机 blocked。

### 下一步（轮次 10 候选）
1. **（阻塞解除后最高优先）** 授予 `workflow` scope，补仅含 ci.yml 接线的独立 PR；接线后优先把纯
   python 的 `evals/fingerprint_check.py`（无需 npx 联网）纳入 CI contracts/structure，再做 §5.3 规则 2 机器化。
2. 视批准情况推进 CVE 修复独立 PR（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）。
3. 若仍无授权：审视《1》走查文档 `docs/refactor/01-dds-request-flow.md` 是否需随轮次 1–9 的 helper
   体系（_freeze_paths/_md_paths/_repo/frozen gate/fingerprint）同步补一段"一致性/回归工具链"，
   或核对 evals/results 旧 BASELINE（仍停留在早期用例数）是否应加"当前基线见 ITERATION_LOG"指引。
4. 继续避免低价值断言堆砌；静态契约 + 全文指纹两层已较完备，增量价值在 CI 接线或 Humble 实测。

---

## 轮次 10 — 2026-09-20 01:05（Asia/Shanghai）《1》同步：走查文档补齐一致性/回归工具链

> 定时任务第 10 轮。分支 `docs/walkthrough-consistency-toolchain`，PR #59。
> `workflow` scope 仍未授予（active 账号 `yixinzhangagent` 仅 gist/read:org/repo；`zhangyinxina-ui`
> 有 workflow 但对本仓 403）、CVE 修复仍待批准，ci.yml 接线 / 规则 2 机器化继续阻塞。本轮按轮次 9
> 候选 3 行动，做**纯文档同步、行为不变**：《1》走查文档停留在轮次 0 的"12 个脚本、各自打开文件"
> 状态，未反映轮次 1–9 引入的共享 helper、第 13 闸、env 交叉断言、stdout 指纹与 Promptfoo 深化——
> 这是《1》"后续随代码重构保持同步"的明确欠账。本轮只改 `docs/refactor/01-dds-request-flow.md`。

### 背景 / 文档漂移取证
- §2 引言写"下列 12 个脚本"，但本地 runner 已是 13 gate（轮次 4 frozen gate）；且未说明 CI structure
  仍只枚举 12（workflow scope pending）这一"本地 13 vs CI 12"背离。
- §2.2 标题"每个 check_*.py **各自**打开一组文件"已不成立：轮次 1/2/5 抽出 `_freeze_paths` /
  `_md_paths` / `_repo` 三个共享 helper，路径常量、repo-root/读取、md 解析已单点维护。
- §2.2 闸门表缺第 13 行 frozen gate；`check_dual_chain_baseline` 行只写 shell 单侧锚定，未写轮次 3
  新增的 load.py↔shell↔wrapper env 单一真源交叉断言与 import 纯净检查。
- §问4 命令清单只有 12 gate + print-a/b，缺 frozen gate、指纹回归、Promptfoo；全文没有一处指引
  贡献者"改 gate stdout 要 --update fixtures"。

### 本轮改动（一项重点改进，仅 1 个文档，+30/−4）
- §2 引言：12 → 本地 runner 13 gate，并显式标注 CI structure 仍枚举 12、第 13 闸接线待 workflow scope（指向 ci-cd-gates §6 与本日志）。
- §2.2：标题去掉"各自"，新增一段三个下划线 helper 的职责与边界（helper 不承载业务断言，业务断言仍归各 gate）。
- §2.2 闸门表：补 `check_frozen_path_literals.py`（第 13 闸，防回潮）行；扩写 dual_chain 行的 env 交叉断言 / import 纯净。
- **新增 §2.4「一致性与回归工具链（轮次 1–9 引入）」**：讲清三层互补——run_all_gates 红绿层、Promptfoo 17 用例契约层（含固定 0.123.1 命令）、fingerprint_check 严格指纹层（eval-only 非第 14 gate、15 命令逐字节、`--update` 流程）；并用 blockquote 如实标注 CI 现状（structure 只跑 12、Promptfoo/指纹 CI 不跑）。
- §问4：命令块补 frozen gate；新增三层本地回归命令块与"改 stdout 记得 --update fixtures"提示。
- §4 阅读清单：新增第 15 条工具链入口（runner + 三 helper + evals README/fingerprint + 本日志）。

### 验证
- **相对链接全量自检**：用与 CI contracts「In-repo markdown relative links」同构的正则提取本文件全部
  **131 个相对链接，missing 0**（新增的 helper / evals / fixtures / 同目录日志计划链接均真实存在）。
  另核对 ci.yml：contracts 的 md-link 检查是**显式文件枚举**，files 列表不含 `docs/refactor/**`，
  故本文件本就不在该 CI 检查面——本地自检是更强保证。
- `python3 scripts/run_all_gates.py`：**13/13 all gates green**（docs-only，不碰任何脚本）。
- `python3 evals/fingerprint_check.py`：**15/15 stable**（无 gate stdout 变化，fixtures 不动）。
- promptfoo 0.123.1：**17/17 passed (100%) / 0 failed / 0 errors**。

### 分数
- Gate：13/13（100%），与轮次 9 持平（纯文档，不应改分）。
- Eval：17/17（100%），与轮次 9 持平。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint 进 CI、规则 2 机器化均无法落地；走查文档已如实写明该背离，避免读者误以为 PR 跑了 13 gate + eval。
3. 仍存文档债务：`evals/results/BASELINE.md` 还是早期 12 用例 / `promptfoo@latest` 的初始基线快照，与当前 17 用例 / 0.123.1 不符，本轮未动（留下一轮，倾向加"初始基线存档、当前基线见 ITERATION_LOG"指针而非改历史数字）。
4. docs/refactor 不在 CI md-link 枚举面，后续该目录链接正确性仍靠本地自检 / 本循环把关。

### 下一步（轮次 11 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，补仅含 ci.yml 接线的独立 PR（frozen gate + 评估把纯 python 的 fingerprint_check.py 先纳入 CI），再做 §5.3 规则 2 机器化。
2. 给 `evals/results/BASELINE.md` 加"初始基线存档"状态指针（不改历史数字），消除 12 vs 17 的误导。
3. 视批准情况推进 CVE 修复独立 PR。
4. 无授权且文档债务清完后，不制造低价值改动，做一次完整 gate+eval 回归并在日志标注「等待新指令」。

---

## 轮次 11 — 2026-09-20 02:10（Asia/Shanghai）《5》文档债务：旧 BASELINE 标注为初始基线存档

> 定时任务第 11 轮。分支 `docs/baseline-archive-status-pointer`，PR #60。
> 开工核对：本循环无在途 PR（#59 已 squash-merge，main HEAD `070032a`）；`gh auth status` 复核
> active 账号 `yixinzhangagent` 仍只有 gist/read:org/repo、**无 workflow**，`zhangyinxina-ui` 有
> workflow 但对本仓 403——ci.yml 接线 / fingerprint 进 CI / 规则 2 机器化继续阻塞；CVE 修复仍待批准。
> 本轮按轮次 10 候选 2 行动，做**纯文档、行为不变**的小步：消除旧基线文件"12 用例 / @latest"与
> 当前"17 用例 / 固定 0.123.1"并存却无说明的误导。只改 `evals/results/BASELINE.md`。

### 背景 / 文档债务取证
- `evals/results/BASELINE.md` 是 2026-09-19 套件刚落地时的**首次**运行存档：12 个 seed 用例、
  命令写 `promptfoo@latest`（实际缓存 0.123.1）。迭代 3/4/6/7/8 后套件已扩到 17 用例、命令固定
  `promptfoo@0.123.1`，但该文件没有任何"这是旧快照"的提示，新读者可能误以为 12/12 与 @latest 是现状。
- 处理原则（轮次 10 日志已定）：**加状态指针，不回改历史数字**——存档的价值就在于保留首次基线原貌。

### 本轮改动（一项重点改进，仅 1 个文档，+9/−0）
- 在 `evals/results/BASELINE.md` 标题下新增 blockquote「状态：初始基线存档（historical snapshot，
  勿当当前基线）」：说明本文件是首次运行存档（12 用例、命令写 @latest、实际 0.123.1），历史数字原样
  保留不回改；套件已扩到 17 用例（env 交叉断言 / frozen gate / 双链真值 print-a·print-b / 全量 stdout
  指纹 #17）、命令固定 0.123.1；当前权威口径与最新分数指向 `../../docs/refactor/ITERATION_LOG.md`
  顶部「评分口径」与各轮记录，用例清单指向 `../README.md`、配置指向 `../promptfooconfig.yaml`。
- 结果区 12/12、eval ID、`baseline_raw.txt` 引用等历史内容**一字未改**。

### 验证
- 新增 3 个相对链接目标（ITERATION_LOG.md / evals README.md / promptfooconfig.yaml）连同既有
  baseline_raw.txt 共 4 个逐一 `test -e` 均存在。核对 ci.yml：contracts 的 md-link 检查是显式文件
  枚举（275–306 行），**不含 `evals/results/**`**，故本文件不在该 CI 检查面，链接正确性靠本地自检。
- `python3 scripts/run_all_gates.py`：**13/13 all gates green**（docs-only，不碰脚本/evals 执行面）。
- `python3 evals/fingerprint_check.py`：**15/15 stable**（BASELINE.md 不是任何 gate/load.py 的 stdout，
  fixtures 不动）。
- promptfoo 0.123.1：**17/17 passed (100%) / 0 failed / 0 errors**（provider 跑脚本、yaml 不引用 results/）。

### 分数
- Gate：13/13（100%），与轮次 10 持平（纯文档，不应改分）。
- Eval：17/17（100%），与轮次 10 持平。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint 进 CI、§5.3 规则 2
   机器化均无法落地；这是当前最高价值但被外部授权卡住的一项，需用户本机
   `gh auth refresh -h github.com -s workflow`。
3. `evals/results/` 与 `docs/refactor/` 均不在 CI md-link 枚举面，这两个目录的链接正确性仍靠本地自检 / 本循环把关。
4. 静态契约 + 全文指纹两层已较完备，剩余增量价值主要在 CI 接线或真·Humble Linux 主机实测；不依赖授权的
   纯文档/低风险清理项正在减少，后续不应为凑改动制造低价值断言。

### 下一步（轮次 12 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，用离线备份 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`
   补仅含 ci.yml 接线的独立 PR（frozen gate test-f + 运行 step；评估把纯 python 的 fingerprint_check.py
   先于整套 promptfoo 纳入 CI），回填 ci-cd-gates.md §1、删 §6 pending；接线后再做 §5.3 规则 2 机器化。
2. 视批准情况推进 CVE 修复独立 PR（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）。
3. 4 份飞书文档授权后补读对齐《2》。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+eval 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 12 — 2026-09-20 03:12（Asia/Shanghai）《5》深化：frozen-path guard 负向自测沉淀为 eval 用例 #18

> 定时任务第 12 轮。分支 `test/frozen-guard-negative-selftest`，PR #62。
> 开工核对：本循环无在途 PR（#60 已 squash-merge，main HEAD `7f26d13`）；`gh auth status` 复核
> active 账号 `yixinzhangagent` 仍只有 gist/read:org/repo、**无 workflow**，`zhangyinxina-ui` 有
> workflow 但对本仓 403——ci.yml 接线 / fingerprint 进 CI / §5.3 规则 2 机器化继续阻塞；CVE 修复仍待批准。
> 完整重读 `02-modernization-plan.md` 确认：Step 1–4 与 §5.3 规则 1/3 已完成，规则 2 与 ci.yml 接线依赖
> workflow 授权，M1–M6 全是 B 面 Hold/需 Humble/需批准。在宣布「等待新指令」前，发现一个**不依赖授权、
> 不越界、且日志多次自认的真实缺口**：frozen gate 的负向能力（"该 fail 时真的会 fail"）轮次 4 只用一次性
> /tmp 夹具验证、未沉淀。本轮把它做成仓内可复跑回归。

### 背景 / 覆盖缺口取证
- #14（frozen gate 正向）只证明**当前树干净**，证明不了检测器**仍会触发**。若有人把
  `check_frozen_path_literals.py` 的正则改宽（或弄坏豁免/渲染逻辑）使它永不报错，所有正向运行（gate、
  #14、#17 指纹）都会继续全绿，而防回潮保护已悄悄失效——这是"guard 失效但全绿"的盲区，#17 全文指纹也
  锁不住（指纹比对的是正常仓 stdout，不含违规样本）。
- 轮次 3/4/8 日志均把"负向夹具是一次性 /tmp、未沉淀为仓内回归"列为薄弱项。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/frozen_guard_selftest.py`（eval-only，纯标准库，tempdir-only，不是 gate）**：
  与 fingerprint_check 同定位——不进 `run_all_gates.GATES`、不被 CI structure 枚举、无需 ci.yml 接线
  （不受 workflow scope 阻塞）。复用 guard 自身纯函数 `_hits_in` 与可注入的 `render(root=...)`，断言三类：
  1. **6 个必报片段**（违禁 `Path(...)`：双/单引号、`docs/artifacts/bench/SCOREBOARD.md`、`r"..."`/`f"..."`
     前缀、短形式 `artifacts/bench/SCOREBOARD.md`、并校验命中行号）；
  2. **7 个不得误报片段**（`from _freeze_paths import ...`、`Path(FASTDDS_XML_REL)`、
     `endswith("config/fastdds.xml")`、输出文案、检测器自身正则串、无关 `Path("scripts")`）；
  3. **2 个 render 端到端**：临时树放违禁 `bad_gate.py`（第 2 行）时必须 exit 1、不打印健康 marker、
     点名 `bad_gate.py:2`，且豁免真源 `_freeze_paths.py`（它本身合法硬编码路径）不被报；删坏文件后 exit 0、
     打印 marker。全过打印 `frozen guard selftest: PASS (6 must-flag, 7 non-flag, 2 render cases)`，exit 0。
- `evals/promptfooconfig.yaml`：新增用例 **#18**（跑该自测，断言 `frozen guard selftest: PASS` +
  计数短语 `6 must-flag, 7 non-flag, 2 render cases`，后者锁住夹具数、防悄悄删负向样本）；用例 17→18。
- `evals/README.md`：文件表加自测脚本、用例数 17→18、用例表加 #18 行、新增「frozen-path guard 负向自测
  （#18）」小节（为何正向证明不了 guard 会触发、6/7/2 夹具清单、变异验证、eval-only 定位）。
- **未做（Hold/边界）**：未改 `check_frozen_path_literals.py` 或任何 gate（其正常仓 stdout 零变化）；
  未碰 ci.yml、fastdds.xml、SCOREBOARD.md、shell、`dimos_bridge`、vendor；未启用 zenoh/Agnocast/Cega；
  无框架/依赖/API 变更；不新增 gate（不加剧"本地 13 vs CI 12"背离）。

### 负向有效性验证（证明自测不是摆设）
- 直接运行：`python3 evals/frozen_guard_selftest.py` → `6/6 must-flag、7/7 non-flag、2/2 render`，PASS、exit 0。
- **变异测试（内存，不落盘）**：把 `fg._FROZEN_PATH_RE` monkeypatch 为永不匹配的 `re.compile(r'(?!)')`
  后跑自测 → 精确报 `must-flag 'short scoreboard form': detector found NO hit` 与
  `render with bad_gate: expected exit 1, got 0`，**exit 1**。证明检测器一旦失效，#18 会红。

### 分数前后对比
- Gate：**13/13（100%）**，与轮次 11 持平（未改任何 gate，run_all_gates 不受影响）。
- 指纹：**15/15 stable**（新自测不在 fingerprint 的 15 命令内，gate/load.py stdout 零变化，fixtures 不动、无需 --update）。
- Eval：**17 → 18 用例，18/18 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#18 PASS）。
- `py_compile evals/frozen_guard_selftest.py` 通过。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint/#18 进 CI、§5.3 规则 2
   机器化仍无法落地；#18 与 #17 一样目前只在本地/本循环把关，未进 GitHub required checks。
3. #18 只覆盖 frozen-path 这一个 guard 的负向行为；轮次 3 新增的 env 交叉断言（4 类）负向夹具仍是一次性
   /tmp（A 域 42→43、wrapper 伪造、import 写 environ），未来可评估是否同样沉淀（先评估与 #11 正向契约的重复度）。
4. eval/指纹/负向自测都只覆盖静态 gate 层，真·双链 pub/sub / p99 / 跨机 UDP 本机仍 blocked。

### 下一步（轮次 13 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，用离线备份补仅含 ci.yml 接线的独立 PR（frozen gate
   test-f + 运行 step；纯标准库、无需 npx 联网的 fingerprint_check.py 与 frozen_guard_selftest.py 比整套
   promptfoo 更适合先纳入 CI），回填 ci-cd-gates.md §1、删 §6 pending；接线后再做 §5.3 规则 2 机器化。
2. 评估把轮次 3 env 交叉断言的负向夹具也沉淀为 eval-only 自测（若与 #11 不重复）。
3. 视批准推进 CVE 修复独立 PR；4 份飞书文档授权后补读。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+eval 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 13 — 2026-09-20 04:15（Asia/Shanghai）《5》深化：双链 env 交叉断言负向自测沉淀为 eval 用例 #19

> 定时任务第 13 轮。分支 `test/dual-chain-env-guard-selftest`，PR #63（已 squash-merge，main HEAD `141963f`）。
> 开工核对：本循环无在途 PR（#62 已 squash-merge，main HEAD `5547cb3`）；`gh auth status` 复核
> active 账号 `yixinzhangagent` 仍只有 gist/read:org/repo、**无 workflow**，`zhangyinxina-ui` 有
> workflow 但对本仓 403——ci.yml 接线 / fingerprint·#18·#19 进 CI / §5.3 规则 2 机器化继续阻塞；
> CVE 修复仍待批准。本轮执行轮次 12「下一步候选 2」：把轮次 3 新增、此后一直只靠一次性 /tmp 夹具
> 验证的 env 交叉断言**负向能力**沉淀为仓内可复跑回归（与 #18 同构、不依赖授权、不越界）。

### 背景 / 覆盖缺口取证（先证与 #11 不重复）
- #11 是**正向**用例：跑真实仓的 `check_dual_chain_baseline.py`，只证明当前 env 健康（4 行 `ok env ...`）。
  它证明不了四类交叉检查（env truth / cross-check A / cross-check B / wrapper，外加 chain_b 不得
  export、必须 unset `CYCLONEDDS_URI`）在出现漂移时**仍然会 fail**。若有人把某个等值比较改宽、弄坏
  分支使漂移漏报，gate、#11、#17 指纹（正常仓 stdout）都会继续全绿，而"load.py 单一真源"保证已悄悄
  失效——与轮次 12 frozen guard 同类的"guard 失效但全绿"盲区。
- 轮次 3 日志明确记载这些负向场景（A 域 42→43、wrapper 伪造、import 写 environ）只用 /tmp 夹具验证、
  未沉淀；轮次 12 剩余风险 3 再次列出。本轮补齐。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/dual_chain_env_guard_selftest.py`（eval-only，纯标准库，tempdir-only，不是 gate）**：
  与 fingerprint_check / frozen_guard_selftest 同定位——不进 `run_all_gates.GATES`、不被 CI structure
  枚举、无需 ci.yml 接线（不受 workflow scope 阻塞）。复用 gate 可注入的 `render(root=...)`，在
  `tempfile` 里造一棵**最小 env 树**（`config/env/load.py` + `chain_a.sh` + `chain_b.sh` +
  `dimos_bridge/dual_chain_env.py` + 仅占位的 `config/fastdds.xml`）；doc/marker 文件在临时树有意缺失
  （render 仍会因缺 doc exit 1），断言只看五行 `FAIL env truth|env cross-check|env wrapper|chain A|
  chain B` 家族（用精确行前缀匹配，避免把路径里含 "env" 的缺文件 FAIL 误计），忽略无关缺-doc FAIL：
  1. **6 个负向场景**：①A 域 42→43 而 chain_a.sh 仍 42（env truth + cross-check A 双报，且不得误触
     B/wrapper）；②B 域 0→1 而 chain_b.sh 仍 0（env truth + cross-check B）；③wrapper 硬编码伪造重
     导出（**仅** env wrapper 报，不得误触 truth/cross-check，证明该检查独立）；④import load.py 写
     `os.environ`（env truth 报 mutated）；⑤chain_b.sh 额外 `export CYCLONEDDS_URI=`（即使同时 unset
     也必报 must-not-export）；⑥chain_b.sh 漏 `unset CYCLONEDDS_URI`（报 need-anchored-unset）；
  2. **2 个健康对照**：完全正确的最小临时树必须**零** env/chain FAIL（零误报）；真实仓 `render()`
     必须 exit 0 且打印全部 4 行 `ok env ...`；
  3. **1 个变异**：内存里把 gate 的 `_EXPORT_CYCLONE_URI_RE` monkeypatch 为永不匹配 `(?!)`，场景⑤
     必须**漏报**（证明正常断言确实依赖该检测器），恢复后必须重新抓到。
  - 写 `os.environ` 的夹具（场景④）每次 render 前后做快照/恢复，不污染测试进程；健康 wrapper 夹具用
    与真实 `dual_chain_env.py` 同款的 importlib 跟随 load.py，伪造 wrapper 才硬编码漂移值（正是 gate
    要防的"复制常量且漂移"）。
- `evals/promptfooconfig.yaml`：新增用例 **#19**（断言 `dual-chain env guard selftest: PASS` +
  计数短语 `6 negative, 2 healthy, 1 mutation`，锁夹具数、防悄悄删负向样本）；用例 18→19。
- `evals/README.md`：文件表加自测脚本、用例数 18→19、用例表加 #19 行、新增「双链 env 交叉断言负向
  自测（#19）」小节（为何 #11 正向证明不了检查会触发、6/2/1 夹具清单、变异验证、environ 卫生、eval-only 定位）。
- **未做（Hold/边界）**：未改 `check_dual_chain_baseline.py` 或任何 gate（正常仓 stdout 零变化）；
  未碰 ci.yml、fastdds.xml、SCOREBOARD.md、shell、`dimos_bridge`、vendor；未启用 zenoh/Agnocast/Cega；
  无框架/依赖/API 变更；不新增 gate（不加剧"本地 13 vs CI 12"背离）。

### 负向有效性验证（证明自测不是摆设）
- 先用一次性 /tmp 探针（未入仓）逐场景打印 gate 真实 FAIL 行，确认 6 个场景的必报/不误报片段逐字后再
  写正式脚本（避免凭记忆造断言串）。
- 直接运行：`python3 evals/dual_chain_env_guard_selftest.py` →
  `negative 6/6、healthy 2/2、mutation 1/1`，PASS、exit 0。
- 脚本内置变异：`_EXPORT_CYCLONE_URI_RE` 改为永不匹配后场景⑤漏报（自测会红），恢复后重新抓到——
  证明 export-URI 检测一旦失效，#19 会红。

### 分数前后对比
- Gate：**13/13（100%）**，与轮次 12 持平（未改任何 gate，run_all_gates 不受影响）。
- 指纹：**15/15 stable**（新自测不在 fingerprint 的 15 命令内，gate/load.py stdout 零变化，fixtures 不动、无需 --update）。
- #18 frozen 负向自测：仍 PASS（6 must-flag / 7 non-flag / 2 render）。
- Eval：**18 → 19 用例，19/19 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#19 PASS，eval ID `eval-1m3-2026-09-19T20:20:41`）。
- `py_compile evals/dual_chain_env_guard_selftest.py` 通过。
- **合并后回归（main HEAD `141963f`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，pending 可忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18 与 #19 负向自测均 PASS、promptfoo **19/19 (100%) / 0 failed / 0 errors**。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint/#18/#19 进 CI、§5.3
   规则 2 机器化仍无法落地；三个 eval-only 严格/负向层（#17/#18/#19）目前都只在本地/本循环把关，未进
   GitHub required checks。
3. #19 覆盖 env 交叉断言的负向行为，但第四处真源 B 面 `dds_topics.py`（域 42/0）与 load.py 之间仍无
   直接交叉断言（由 contracts job 分别断言两侧常量，B 面 Hold），其负向行为不在本自测范围。
4. eval/指纹/两个负向自测都只覆盖静态 gate 层，真·双链 pub/sub / p99 / 跨机 UDP 本机仍 blocked。

### 下一步（轮次 14 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，用离线备份补仅含 ci.yml 接线的独立 PR（frozen gate
   test-f + 运行 step；纯标准库、无需 npx 联网的 fingerprint_check.py、frozen_guard_selftest.py、
   dual_chain_env_guard_selftest.py 比整套 promptfoo 更适合先纳入 CI），回填 ci-cd-gates.md §1、删 §6
   pending；接线后再做 §5.3 规则 2 机器化。
2. 不依赖授权的负向沉淀已覆盖 frozen 与 env 两个核心 guard；下一个候选可评估 source-map allowlisted
   符号检查（#2）或 unitree 裁决（#7）是否存在同类"正向全绿但 guard 可被改宽"盲区，先证不重复再做，
   避免低价值断言堆砌。
3. 视批准推进 CVE 修复独立 PR；4 份飞书文档授权后补读。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+#18+#19+eval 回归并在日志标注「等待新指令」，
   不制造无意义提交。

---

## 轮次 14 — 2026-09-20 05:12（Asia/Shanghai）《5》深化：Unitree 交换裁决 guard 负向自测沉淀为 eval 用例 #20

> 定时任务第 14 轮。分支 `test/unitree-swap-guard-selftest`，PR #66（已 squash-merge，main HEAD `f960fd8`）。
> 开工核对：本循环无在途 PR（#63/#64 已 squash-merge，main HEAD `a0cedea`；`gh pr list` 中 #65/#61/#56/#46
> 等均为他人 claude/cursor/codex 自动审查类 PR，未触碰）；`gh auth status` 复核 active 账号
> `yixinzhangagent` 仍只有 gist/read:org/repo、**无 workflow**，`zhangyinxina-ui` 有 workflow 但对本仓
> 403——ci.yml 接线 / fingerprint·#18·#19·#20 进 CI / §5.3 规则 2 机器化继续阻塞；CVE 修复仍待批准。
> 本轮执行轮次 13「下一步候选 2」的另一半：轮次 13 沉淀了 env guard（#19），本轮评估并沉淀 **#7 Unitree
> 交换裁决 guard** 的负向能力（与 #18/#19 同构、不依赖授权、不越界，且守护的是《6》CVE 结论的关键裁决）。

### 背景 / 覆盖缺口取证（先证与 #7 不重复）
- #7 是**正向**用例：跑真实仓 `check_unitree_cyclone_swap.py`，断言健康 marker 与 `drop-in: FAIL / wire:
  UNPROVEN`。它只证明**当前记录**打印该串，证明不了 guard 的各项检查在记录被篡改时**仍会 fail**。该裁决
  守护与《6》直接相关的诚实性：Unitree bundled Cyclone 0.10.2 对 vendor 11.0.1 不是 drop-in、默认保持
  bundled、唯一合法替换路径是 `unitree_sdk2_hzj + UNITREE_DDS_PROVIDER=external`、wire 互通保持 UNPROVEN。
- 若有人把交换文档裁决翻成 `drop-in PASS / wire PROVEN`、删掉引文 `DDS_VERSION "0.10.2"`、改松 vendor
  Cyclone SHA / CMake `project() VERSION` 钉版或删除交换文档，而 guard 被相应改宽，所有正向运行（gate、
  #7、#17 指纹，它们比对的都是健康树输出）都会继续全绿，安全裁决却已悄悄反转——与 #18/#19 同类的
  "guard 失效但全绿"盲区。
- 与 frozen/env 自测的差异：交换文档带 18 个连续 marker，手写最小健康文档易腐且会偏离真实记录，故本轮
  采用**复制 guard 读取的 5 个真实文件进 tempdir、再每次只变异一个**的夹具策略，健康复制树同时充当
  "夹具与真实树等价"的自证。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/unitree_swap_guard_selftest.py`（eval-only，纯标准库，tempdir-only，不是 gate）**：不进
  `run_all_gates.GATES`、不被 CI structure 枚举、无需 ci.yml 接线（不受 workflow scope 阻塞）。复制
  guard 读取的 5 个文件（交换文档、`vendor/VERSIONS.md`、`vendor/CycloneDDS/CMakeLists.txt`，以及在该
  脚本里只验存在的 `config/fastdds.xml`、`SCOREBOARD.md`）进临时树，驱动可注入的 `render(root=...)`：
  1. **5 个负向场景**：N1 连续裁决句 `drop-in FAIL / wire UNPROVEN`→`drop-in PASS / wire PROVEN`（报
     `FAIL verdict`，且未改动的 VERSIONS/CMake 仍报 ok，证明各检查独立、不连带）；N2 引文
     `DDS_VERSION "0.10.2"`→`"9.9.9"`（裸 0.10.2 在文档别处保留，专门引文检查仍报 `FAIL quote`）；
     N3 vendor CycloneDDS SHA 行被改（报 `FAIL VERSIONS row`，交换文档未动故裁决句仍 ok）；N4 CMake
     `project() VERSION 11.0.1`→9.9.9（报 `FAIL CMake project()`）；N5 删除交换文档（报 `FAIL missing`、
     不打印 marker，VERSIONS/CMake 仍 ok）；
  2. **2 个健康对照**：真实仓 `render()` 与一份完整复制的临时树都必须 exit 0 且打印 marker（证明复制夹具
     本身有效、与真实树等价，否则负向场景可能因错误原因失败）；
  3. **1 个变异**：把 `_CMAKE_PROJECT_RE` 改宽为只匹配 `project(CycloneDDS` 而不再钉 `VERSION 11.0.1`，
     N4 必须**漏报**（被篡改树打印 `ok CMake project()`），恢复正则后必须重新抓到——证明 N4 确实依赖检测
     器里的版本钉（"检查被改宽即漏报"），而非偶然通过。
  - 所有变异锚点串（裁决句、引文、SHA、CMake project 行、5 个文件路径）均先 grep 真实文件逐字取证；
    每次变异在全新 tempdir 进行，只读真实仓、绝不写仓。
- `evals/promptfooconfig.yaml`：新增用例 **#20**（断言 `unitree swap guard selftest: PASS` + 计数短语
  `5 negative, 2 healthy, 1 mutation`，锁夹具数、防悄悄删负向样本）；用例 19→20。
- `evals/README.md`：文件表加自测脚本、用例数 19→20、用例表加 #20 行、新增「Unitree Cyclone 交换裁决
  负向自测（#20）」小节（为何 #7 正向证明不了检查会触发、复制真实文件夹具策略、5/2/1 清单、变异验证、
  eval-only 定位）。
- **未做（Hold/边界）**：未改 `check_unitree_cyclone_swap.py` 或任何 gate（正常仓 stdout 零变化）；未碰
  ci.yml、fastdds.xml、SCOREBOARD.md、vendor、`dimos_bridge`；未启用 zenoh/Agnocast/Cega；无框架/依赖/
  API 变更；不新增 gate（不加剧"本地 13 vs CI 12"背离）。

### 负向有效性验证（证明自测不是摆设）
- `python3 evals/unitree_swap_guard_selftest.py` → negative 5/5、healthy 2/2、mutation 1/1，PASS、exit 0。
- 变异方向刻意选"改宽"（与威胁模型"等值/正则比较被改宽"一致）：去掉 CMake 版本钉后被篡改树打印
  `ok CMake project()`（漏报），恢复后重新 `FAIL CMake project()`——证明该负向场景确实依赖版本钉。

### 分数前后对比
- Gate：**13/13（100%）**，与轮次 13 持平（未改任何 gate，run_all_gates 不受影响）。
- 指纹：**15/15 stable**（新自测不在 fingerprint 的 15 命令内，gate/load.py stdout 零变化，fixtures 不动、无需 --update）。
- #18 frozen、#19 env 负向自测：均仍 PASS。
- Eval：**19 → 20 用例，20/20 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#20 PASS，Duration 2s）。
- `py_compile evals/unitree_swap_guard_selftest.py` 通过。
- **合并后回归（main HEAD `f960fd8`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，pending 可忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18/#19/#20 三个负向自测均 PASS、promptfoo **20/20 (100%) / 0 failed / 0 errors**。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint/#18/#19/#20 进 CI、§5.3
   规则 2 机器化仍无法落地；四个 eval-only 严格/负向层（#17/#18/#19/#20）目前都只在本地/本循环把关，未进
   GitHub required checks。
3. #20 复制的是真实文件，若交换文档/VERSIONS/CMake 的**合法演进**改变了变异锚点串（如未来 vendor 升级
   Cyclone 版本），自测会因锚点 `old not found` 显式 RuntimeError 失败——这是有意的 fail-loud，提示同步
   夹具；但意味着 vendor 升级 PR 需要同步更新本自测锚点。
4. #2 source-map allowlisted 符号检查是否存在同类"可被改宽但正向全绿"盲区尚未评估（其符号解析在
   `_md_paths.check_cited_paths`，构造负向夹具更复杂，留下一轮）；真·双链 pub/sub / p99 / 跨机 UDP 本机仍 blocked。

### 下一步（轮次 15 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，用离线备份补仅含 ci.yml 接线的独立 PR（frozen gate
   test-f + 运行 step；纯标准库、无需 npx 联网的 fingerprint_check.py、frozen_guard_selftest.py、
   dual_chain_env_guard_selftest.py、unitree_swap_guard_selftest.py 比整套 promptfoo 更适合先纳入 CI），
   回填 ci-cd-gates.md §1、删 §6 pending；接线后再做 §5.3 规则 2 机器化。
2. 评估 #2 source-map allowlisted 符号检查（`_md_paths.check_cited_paths`）的负向沉淀可行性：先证与 #2
   正向、#17 指纹不重复，且能在 tempdir 构造"vendor 丢符号/引用路径缺失被改宽漏报"夹具；若复杂度过高或
   与现有层重复则不做，避免低价值断言堆砌。
3. 视批准推进 CVE 修复独立 PR；4 份飞书文档授权后补读。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+#18+#19+#20+eval 回归并在日志标注「等待新指令」，
   不制造无意义提交。

---

## 轮次 15 — 2026-09-20 06:17（Asia/Shanghai）《5》深化：ros2-source-map guard 负向自测沉淀为 eval 用例 #21

> 定时任务第 15 轮。分支 `test/source-map-guard-selftest`，PR #68（已 squash-merge，main HEAD `f235532`）。
> 开工核对：本循环无在途 PR（#66/#67 已 squash-merge，main HEAD `ced21c2`；`gh pr list` 中 #65/#61/#56/#46
> 等均为他人 claude/cursor/codex 自动审查类 PR，未触碰）；`gh auth status` 复核 active 账号
> `yixinzhangagent` 仍只有 gist/read:org/repo、**无 workflow**，`zhangyinxina-ui` 有 workflow 但对本仓
> 403——ci.yml 接线 / fingerprint·#18·#19·#20 进 CI / §5.3 规则 2 机器化继续阻塞；CVE 修复仍待批准。
> 本轮执行轮次 14「下一步候选 2」：评估并沉淀 **#2 ros2-source-map guard** 的负向能力（轮次 14 剩余风险 4
> 明确点名的最后一个未评估核心 guard；与 #18/#19/#20 同构、不依赖授权、不越界）。

### 背景 / 覆盖缺口取证（先证与 #2/#17 不重复）
- #2 是**正向**用例：跑真实仓 `check_source_map.py`，断言 `Source map healthy` + `allowlisted symbols ok:`；
  #17 指纹比对的也是健康树全文。两者都证明不了 guard 的四类 FAIL 检查在被篡改时**仍会触发**。该 guard
  （wiki3 §13.2）保证 `docs/architecture/ros2-source-map.md` 仍指向真实在树文件、且被追踪的 vendor 符号
  （Fast-DDS `WriterHistory.cpp` 的 `add_change`、rmw 的 `rmw_publish/rmw_take/rmw_wait`、Cyclone 的
  `dds_take/ddsi_whc_insert` 等）未被重写/删除。
- 若有人删掉 map、清空全部引用、指向已删文件、或从 vendor 文件删掉钉版符号，而检测器被相应改宽，所有正向
  运行（gate、#2、#17）都会继续全绿，source map 却已悄悄不再描述 vendor 代码——与 #18/#19/#20 同类的
  "guard 失效但全绿"盲区。
- 可行性探针（一次性 /tmp，先逐字取真实 FAIL 行再写脚本）：最小夹具只需一个 map + 一个 vendor 文件
  （source map 不像 Unitree 交换文档带 18 个连续 marker，故采用**手写最小树**而非复制真实文件），
  `render(root=...)` 可注入，四类 FAIL 与一个 warn-only 契约全部如预期触发。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/source_map_guard_selftest.py`（eval-only，纯标准库，tempdir-only，不是 gate）**：不进
  `run_all_gates.GATES`、不被 CI structure 枚举、无需 ci.yml 接线（不受 workflow scope 阻塞）。在
  `tempfile` 里手写最小树（`docs/architecture/ros2-source-map.md` + 一个 allowlisted key
  `vendor/Fast-DDS/src/cpp/rtps/history/WriterHistory.cpp`），驱动可注入的 `render(root=...)`：
  1. **4 个负向场景**：N1 删除 map（`FAIL: map missing`）；N2 map 只剩散文、提不出任何在树路径
     （`FAIL: no in-repo paths extracted`）；N3 map 引用不存在的 `vendor/not/there.cpp`（`FAIL missing`）；
     N4 被引用文件删掉 allowlisted 符号 `add_change`（`FAIL symbol`）；
  2. **1 个 warn-only 契约**：map 引用 `...WriterHistory.cpp:999`、行号故意陈旧而符号仍在 L1 时，必须打印
     `WARN stale line` 但 **exit 0**——锁定文档承诺的"陈旧行号只告警、不 FAIL"，防止它被悄悄收紧成 FAIL
     （这是 #18/#19/#20 没有的双向契约：既防改宽漏报，也防改严误报）；
  3. **2 个健康对照**：真实仓 `render()` 与最小健康临时树都必须 exit 0 且打印 `Source map healthy`
     （证明手写夹具有效，负向场景不会因错误原因失败）；
  4. **1 个变异**：monkeypatch `_md_paths.symbol_lines` 为"恒返回命中 [1]"后，N4 必须**漏报**（被篡改树
     打印 `ok symbol`、exit 0），恢复后必须重新报 `FAIL symbol`——证明 N4 确实依赖检测器里的符号查找。
- `evals/promptfooconfig.yaml`：新增用例 **#21**（断言 `source map guard selftest: PASS` + 计数短语
  `4 negative, 1 warn-only, 2 healthy, 1 mutation`，锁夹具数、防悄悄删负向样本）；用例 20→21。
- `evals/README.md`：文件表加自测脚本、用例数 20→21、seed 用例说明加 #21、用例表加 #21 行、新增
  「ros2-source-map 负向自测（#21）」小节（为何 #2 正向证明不了检查会触发、手写最小树策略、4/1/2/1 清单、
  warn-only 双向契约、变异验证、eval-only 定位）。
- **未做（Hold/边界）**：未改 `check_source_map.py`、`_md_paths.py` 或任何 gate（正常仓 stdout 零变化）；
  未碰 ci.yml、fastdds.xml、SCOREBOARD.md、vendor、`dimos_bridge`；未启用 zenoh/Agnocast/Cega；无框架/
  依赖/API 变更；不新增 gate（不加剧"本地 13 vs CI 12"背离）。

### 负向有效性验证（证明自测不是摆设）
- 一次性 /tmp 探针逐场景打印真实输出：4 个负向场景 exit 1 且 FAIL 家族正确；stale 行号场景 exit 0 且
  含 `WARN stale line`；monkeypatch 恒命中后 N4 漏报（exit 0、`ok symbol`），恢复后 exit 1、`FAIL symbol`。
- 正式脚本：`python3 evals/source_map_guard_selftest.py` → negative 4/4、warn-only 1/1、healthy 2/2、
  mutation 1/1，PASS、exit 0。

### 分数前后对比
- Gate：**13/13（100%）**，与轮次 14 持平（未改任何 gate，run_all_gates 不受影响）。
- 指纹：**15/15 stable**（新自测不在 fingerprint 的 15 命令内，gate/load.py stdout 零变化，fixtures 不动、无需 --update）。
- #18 frozen、#19 env、#20 unitree 负向自测：均仍 PASS。
- Eval：**20 → 21 用例，21/21 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#21 PASS，Duration 2s）。
- `py_compile evals/source_map_guard_selftest.py` 通过。
- **合并后回归（main HEAD `f235532`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，pending 可忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18/#19/#20/#21 四个负向自测均 PASS、promptfoo **21/21 (100%) / 0 failed / 0 errors**。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint/#18/#19/#20/#21 进 CI、§5.3
   规则 2 机器化仍无法落地；五个 eval-only 严格/负向层（#17/#18/#19/#20/#21）目前都只在本地/本循环把关，未进
   GitHub required checks。
3. #21 手写最小树只覆盖 allowlist 的一个 key（WriterHistory.cpp/add_change）；其余 15 个 allowlisted 符号的
   消失由**同一** `check_cited_paths` 符号循环统一处理，N4 变异已证明该循环失效即漏报，故不逐符号堆夹具
   （有意的克制，避免低价值断言堆砌）；executor map（`check_executor_map.py`）是 `check_cited_paths` 的另一个
   消费方但带 `reject_bare_words`/`absent_keys` 两个独有分支，其独有分支的负向行为尚未覆盖。
4. 真·双链 pub/sub / p99 / 跨机 UDP / 三链复现本机仍 blocked（无 Humble runtime）。

### 下一步（轮次 16 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，用离线备份补仅含 ci.yml 接线的独立 PR（frozen gate
   test-f + 运行 step；纯标准库、无需 npx 联网的 fingerprint_check.py 与四个 guard selftest 比整套 promptfoo
   更适合先纳入 CI），回填 ci-cd-gates.md §1、删 §6 pending；接线后再做 §5.3 规则 2 机器化。
2. 评估 executor map 两个独有分支（`reject_bare_words` 裸词拒绝、`absent_keys` 缺席引用不要求存在）的负向
   沉淀：先证与 #5 正向、#17 指纹、#21（共享符号循环部分）不重复，只覆盖独有分支；重复则不做。
3. 视批准推进 CVE 修复独立 PR；4 份飞书文档授权后补读。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+#18+#19+#20+#21+eval 回归并在日志标注「等待新指令」，
   不制造无意义提交。

---

## 轮次 16 — 2026-09-20 07:16（Asia/Shanghai）《5》深化：Executor/WaitSet map guard 独有分支负向自测沉淀为 eval 用例 #22

> 定时任务第 16 轮。分支 `test/executor-map-guard-selftest`，PR #70（已 squash-merge，main HEAD `8772794`）。
> 开工核对：本循环无在途 PR（#68/#69 已 squash-merge，main HEAD `89b8a47`；`gh pr list` 中 #65/#61/#56/#46/#45/#44
> 等均为他人 claude/cursor/codex 自动审查类 PR，未触碰）；`gh auth status` 复核 active 账号 `yixinzhangagent` 仍只有
> gist/read:org/repo、**无 workflow**，`zhangyinxina-ui` 有 workflow 但对本仓 403——ci.yml 接线 / fingerprint·#18–#22
> 进 CI / §5.3 规则 2 机器化继续阻塞；CVE 修复仍待批准。本轮执行轮次 15「下一步候选 2」：评估并沉淀 **#5 Executor/
> WaitSet map guard 独有分支**的负向能力（轮次 15 剩余风险 3 明确点名的最后一个未覆盖 `check_cited_paths` 消费方；
> 与 #18–#21 同构、不依赖授权、不越界）。

### 背景 / 覆盖缺口取证（先证与 #5/#17/#21 不重复）
- #5 是**正向**用例：跑真实仓 `check_executor_map.py`，断言 `Executor map healthy` + `WaitSet -> callback: mapped`；
  #17 指纹比对的也是健康树全文。两者都证明不了 guard 的 executor 独有 FAIL 检查在被篡改时**仍会触发**。该 guard
  （wiki3 §13 wait→callback 身份图）守护：Humble `rcl/rclcpp/rclpy` 不得出现在 `vendor/`、16 条身份 marker 与 3 个
  飞书 URL 不得丢失、11 个 allowlisted WaitSet/wait/take 符号文件必须被 map 引用、7 个必需文档必须在树。
- **刻意不重复 #21**：executor 与 source_map 两个 guard 共享 `_md_paths.check_cited_paths`（引用路径存在性 +
  allowlisted 符号 + 陈旧行号 WARN），那部分负向行为已由 #21 的 4 negative + 1 warn-only + 符号查找变异完整覆盖；
  本轮只沉淀 executor **独有**分支：①`ABSENT_VENDOR_TREES`（vendor/rcl{,cpp,py} 出现即 FAIL vendored，守护
  "Humble rcl* 不进 vendor" Hold）；②`DOC_MARKERS` 16 条身份串缺失 FAIL markers；③`FEISHU_URLS` 3 个缺失 FAIL
  Feishu URL；④allowlist key 未被 map 引用 FAIL uncited；⑤`REQUIRED_DOCS` 缺失 FAIL missing；以及两个 executor
  独有的 `parse_map` 参数：`absent_keys`（vendor/rcl 引用作为"应当缺席"不要求存在）与 `reject_bare_words`
  （裸散文词 `` `dimos_bridge` `` 不解析为路径）。
- 可行性探针（一次性 `/tmp/probe_executor_map.py`，先逐字取真实 FAIL 行再写脚本）：5 个负向场景全部 exit 1 且 FAIL
  家族精确；PG1 不传 absent_keys 时 `vendor/rcl` 进 cited、传时不进；PG2 不传 reject 时裸词解析为
  `docs/architecture/dimos_bridge`、传时不解析；真实 map 第 14/90/91 行确有 vendor/rcl* 引用、第 17/80 行确有裸词
  `dimos_bridge`（健康树本身就在走这两个分支，故最小健康 map 含这两类引用时 exit 0 即同时证明两参数在防误报）。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/executor_map_guard_selftest.py`（eval-only，纯标准库，tempdir-only，不是 gate）**：不进
  `run_all_gates.GATES`、不被 CI structure 枚举、无需 ci.yml 接线（不受 workflow scope 阻塞）。夹具策略同 #20：
  复制 **11 个真实 allowlisted 符号文件**进 tempdir（符号查找跑在真实内容上）+ 6 个 required 占位文件（map 除外）+
  手写一张含 16 marker / 3 URL / 11 key 反引号引用 / vendor-rcl* absent 引用 / 裸词的最小 map，驱动可注入的
  `render(root=...)`：
  1. **5 个负向场景**：N1 `vendor/rcl{,cpp,py}` 三目录出现（`FAIL vendored`，三条）；N2 身份 marker 缺失
     （删 `§9.4`，`FAIL markers`）；N3 飞书 URL 缺失（删第 3 个 URL，`FAIL Feishu URL`）；N4 allowlisted 文件
     在盘但 map 不再引用（`vendor/CycloneDDS/.../dds_read.c`，`FAIL uncited`）；N5 必需文档缺失
     （`scripts/prove_rmw.py`，`FAIL missing`）；
  2. **2 个解析机制断言（parse-guard，executor 独有）**：PG1 `absent_keys` 把 `vendor/rcl` 引用挡在 cited 集合外
     （不传则进入集合、会被要求存在）；PG2 `reject_bare_words=True` 让裸词 `` `dimos_bridge` `` 不被误解析成
     `docs/architecture/dimos_bridge`（不传则误解析）；
  3. **2 个健康对照**：真实仓 `render()` 与最小健康临时树都必须 exit 0 且打印 `Executor map healthy`（最小 map 本身
     含 absent 引用与裸词，绿色即证明两个 parse 参数在防误报，否则同树会因"路径不存在"而 FAIL）；
  4. **1 个变异**：monkeypatch `g.ABSENT_VENDOR_TREES = ()`（try/finally 恢复）且三棵 rcl* 目录都存在时，N1 必须
     **漏报**（exit 0、无 FAIL vendored），恢复后必须重新抓到三条 FAIL vendored——证明 N1 确实依赖 vendored-tree
     检测器（探针中先验证过：只清空常量但不建目录时另两个缺失目录仍致 exit 1，变异不干净；故正式变异三目录都 mkdir）。
- `evals/promptfooconfig.yaml`：新增用例 **#22**（断言 `executor map guard selftest: PASS` + 计数短语
  `5 negative, 2 parse-guard, 2 healthy, 1 mutation`，锁夹具数、防悄悄删负向样本）；用例 21→22。
- `evals/README.md`：文件表加自测脚本、用例数 21→22、seed 用例说明加 #22、用例表加 #22 行、新增
  「Executor/WaitSet map 负向自测（#22）」小节（为何 #5 正向证明不了检查会触发、刻意不重复 #21 的共享循环、
  复制真实符号文件夹具策略、5/2/2/1 清单、两个 parse-guard 双向防误报、变异验证、eval-only 定位）。
- **未做（Hold/边界）**：未改 `check_executor_map.py`、`_md_paths.py` 或任何 gate（正常仓 stdout 零变化）；未碰
  ci.yml、fastdds.xml、SCOREBOARD.md、vendor、`dimos_bridge`；未启用 zenoh/Agnocast/Cega；无框架/依赖/API 变更；
  不新增 gate（不加剧"本地 13 vs CI 12"背离）。

### 负向有效性验证（证明自测不是摆设）
- 一次性 /tmp 探针逐场景打印真实输出：5 个负向场景 exit 1 且 FAIL 家族/点名串精确；PG1/PG2 两参数的传/不传差异
  逐字验证；清空 `ABSENT_VENDOR_TREES` + 三目录存在时 exit 0 无 FAIL vendored（漏报），恢复后 exit 1 三条 FAIL
  vendored（重新抓到）。
- 正式脚本：`python3 evals/executor_map_guard_selftest.py` → negative 5/5、parse guards 2/2、healthy 2/2、
  mutation 1/1，PASS、exit 0；`py_compile` 通过。

### 分数前后对比
- Gate：**13/13（100%）**，与轮次 15 持平（未改任何 gate，run_all_gates 不受影响）。
- 指纹：**15/15 stable**（新自测不在 fingerprint 的 15 命令内，gate/load.py stdout 零变化，fixtures 不动、无需 --update）。
- #18 frozen、#19 env、#20 unitree、#21 source-map 负向自测：均仍 PASS。
- Eval：**21 → 22 用例，22/22 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#22 PASS，Duration 2s）。
- **合并后回归（main HEAD `8772794`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，pending 可忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18/#19/#20/#21/#22 五个负向自测均 PASS、promptfoo **22/22 (100%) / 0 failed / 0 errors**。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint/#18–#22 进 CI、§5.3 规则 2 机器化
   仍无法落地；六个 eval-only 严格/负向层（#17/#18/#19/#20/#21/#22）目前都只在本地/本循环把关，未进 GitHub
   required checks。
3. #22 复制 11 个真实 allowlisted 符号文件；若 allowlist 或这些文件合法演进（增删 key、路径迁移），夹具会因
   复制失败/计数不符 fail-loud，需在同一 PR 同步本自测——这是有意的 fail-loud（同 #20 策略）。共享的
   `check_cited_paths` 路径/符号/陈旧行号分支刻意不重复测（#21 已覆盖），其余 executor 直白 substring 检查
   （markers/URL/required-docs）已在 N2/N3/N5 各取代表样本，不逐串堆夹具（有意的克制）。
4. 真·双链 pub/sub / p99 / 跨机 UDP / 三链复现本机仍 blocked（无 Humble runtime）。

### 下一步（轮次 17 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，用离线备份补仅含 ci.yml 接线的独立 PR（frozen gate test-f +
   运行 step；纯标准库、无需 npx 联网的 fingerprint_check.py 与五个 guard selftest 比整套 promptfoo 更适合先纳入
   CI），回填 ci-cd-gates.md §1、删 §6 pending；接线后再做 §5.3 规则 2 机器化。
2. 不依赖授权的 guard 负向沉淀已覆盖 frozen/env/unitree/source-map/executor 五个 guard；剩余 guard
   （risk_matrix/print_bench/runtime_provenance/three_chain/sink_layers/dod/cega）多为直白 substring/存在性检查，
   须先证与正向用例/#17 指纹/已有 selftest 不重复、夹具可在 tempdir 构造且有真实"可被改宽"盲区才做；复杂度过高或
   重复则不做，避免低价值断言堆砌。
3. 视批准推进 CVE 修复独立 PR；4 份飞书文档授权后补读。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+#18–#22+eval 回归并在日志标注「等待新指令」，
   不制造无意义提交。

---

## 轮次 17 — 2026-09-20 08:10（Asia/Shanghai）《5》深化：产品 DoD 诚实性 guard 反伪造负向自测沉淀为 eval 用例 #23

> 定时任务第 17 轮。分支 `test/dod-evidence-guard-selftest`，PR #72（已 squash-merge，main HEAD `2c71b38`）。
> 开工核对：轮次 16 功能 PR #70 与回填 PR #71 均已 squash-merge，main HEAD `25c24dc`；`gh pr list` 中在途 PR
> （#65/#61/#56/#46/#45/#44/#43/#42/#41/#32/#31/#30）全是他人 claude/cursor/codex 机器人 PR，未触碰；本循环
> 无在途 PR。`workflow` scope 仍未授予、CVE 修复仍待批准。本轮执行轮次 16「下一步候选 2」：在剩余七个未做负向
> 沉淀的 guard 中，先证不重复、再挑出**解析逻辑最复杂、有真实"可被改宽"盲区**的一个——`check_dod_evidence.py`
> 的反伪造检测器（与 #18–#22 同构、不依赖授权、不越界）。

### 背景 / 覆盖缺口取证（先证与 #12/#17 不重复）
- #12 是**正向**用例：跑真实仓 `check_dod_evidence.py`，断言 `Product DoD evidence healthy` + `DoD: unmet`；
  #17 指纹比对的也是健康树全文。两者都证明不了该 guard **独有**的反伪造正则在证据文档被偷偷翻绿时**仍会触发**。
  该 guard（wiki3 §6.3 产品 DoD 诚实性）守护：证据文档必须保持 `DoD: unmet` / `STATUS: blocked`、点名五项未达成
  产品项，且不得伪造正向 `STATUS: PASS` / `DoD: met` / this-host measured-delta / “Humble 在此跑过”，也不得虚构
  booked 分位 token（p50/p99）。
- 与已沉淀五个 guard 相比，dod guard 的检测器最富语义、最易在"重构简化"中被悄悄改宽：
  ①`_STATUS_FABRICATE_RE` / `_DOD_FABRICATE_RE` / `_FABRICATE_RES` 四组伪造正则；
  ②`_PROHIBITION_RE` **同行禁止词豁免**（"do not write STATUS: PASS" 必须放行；且不得把 unmet/blocked 本身当
  禁止词，否则 `DoD: unmet — STATUS: PASS` 会漏网，脚本注释明确点名这个陷阱）；
  ③`_PERCENTILE_RE` 用边界 lookaround 抓 booked pNN，但必须放行政策词“分位数”。
  若有人把某个伪造正则改宽、或把豁免改得过宽，一份伪造 PASS 的文档会让 gate、#12、#17 全部继续全绿，诚实裁决
  却已悄悄反转——与 #18–#22 同类的"guard 失效但全绿"盲区。
- **刻意只覆盖独有反伪造逻辑**：直白的 marker 缺失 / 文件缺失检查与 #20 N5 / #22 N2·N5 同形，不重复堆夹具。
- 可行性探针（一次性 `/tmp/probe_dod_evidence.py`，先逐字取真实 FAIL 行再写脚本）：健康复制树 exit 0；5 个篡改行
  全部 exit 1 且 FAIL 家族精确（4 个 `FAIL fabricate` + 1 个 `FAIL percentiles`）；禁止行与政策词均 exit 0；
  neuter `_STATUS_FABRICATE_RE` 后 `STATUS: PASS` 漏报（exit 0）、恢复后重新抓到——变异干净（该篡改行只被这一个
  正则命中）。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/dod_evidence_guard_selftest.py`（eval-only，纯标准库，tempdir-only，不是 gate）**：不进
  `run_all_gates.GATES`、不被 CI structure 枚举、无需 ci.yml 接线（不受 workflow scope 阻塞）。夹具策略同 #20/#22：
  把 guard 读取的 **7 个真实内容文件**（DoD 证据、ADR、provenance、source-map、latency-method、unitree-swap、
  prove_rmw.py）复制进 `tempfile`（fastdds.xml / SCOREBOARD 在该脚本里只验存在，用空占位），再每次只向 DoD 文档
  追加一行篡改，驱动可注入的 `render(root=...)`：
  1. **5 个负向场景**：N1 独立行 `STATUS: PASS`、N2 `DoD: met`、N3 `this-host measured-delta: PASS`、
     N4 `Humble runtime existed here`（分别覆盖 STATUS / DoD / measured-delta / Humble 四组伪造正则，均报
     `FAIL fabricate`）、N5 虚构 booked token `p99 = 12 ms`（报 `FAIL percentiles`）；
  2. **2 个防误报（non-flag，双向契约）**：P1 同行含禁止词的 `do not write STATUS: PASS` 必须被豁免、仍 exit 0；
     P2 政策词“分位数”不得触发分位正则、仍 exit 0（既防改宽漏报，也防改严误报，与 #21 warn-only 同类的双向性）；
  3. **2 个健康对照**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印成功 marker（证明复制夹具与真实树等价，
     负向场景不会因错误原因失败）；
  4. **1 个变异**：monkeypatch `_STATUS_FABRICATE_RE` 为永不匹配 `(?!)`（try/finally 恢复）后 N1 必须**漏报**
     （exit 0、无 FAIL fabricate），恢复后必须重新抓到——证明 N1 确实依赖该伪造检测器。
- `evals/promptfooconfig.yaml`：新增用例 **#23**（断言 `dod evidence guard selftest: PASS` + 计数短语
  `5 negative, 2 non-flag, 2 healthy, 1 mutation`，锁夹具数、防悄悄删负向样本）；用例 22→23。
- `evals/README.md`：文件表加自测脚本、用例数 22→23、seed 段加 #23、用例表加 #23 行、新增「产品 DoD 诚实性
  guard 反伪造负向自测（#23）」小节（为何 #12 正向证明不了检测器会触发、刻意不重复直白存在性检查、复制真实文件
  夹具策略、5/2/2/1 清单、禁止词豁免与政策词的双向防误报、变异验证、eval-only 定位）。
- **未做（Hold/边界）**：未改 `check_dod_evidence.py` 或任何 gate（正常仓 stdout 零变化）；未碰 ci.yml、
  fastdds.xml、SCOREBOARD.md、vendor、`dimos_bridge`；未启用 zenoh/Agnocast/Cega；无框架/依赖/API 变更；不新增
  gate（不加剧"本地 13 vs CI 12"背离）。

### 负向有效性验证（证明自测不是摆设）
- 一次性 /tmp 探针逐场景打印真实输出：5 个负向场景 exit 1 且 FAIL 家族精确；禁止行 / 政策词 exit 0；neuter 伪造
  正则后 N1 漏报、恢复后重新抓到。
- 正式脚本：`python3 evals/dod_evidence_guard_selftest.py` → negative 5/5、non-flag 2/2、healthy 2/2、
  mutation 1/1，PASS、exit 0；`py_compile` 通过。

### 分数前后对比
- Gate：**13/13（100%）**，与轮次 16 持平（未改任何 gate，run_all_gates 不受影响）。
- 指纹：**15/15 stable**（新自测不在 fingerprint 的 15 命令内，gate/load.py stdout 零变化，fixtures 不动、无需 --update）。
- #18 frozen、#19 env、#20 unitree、#21 source-map、#22 executor-map 负向自测：均仍 PASS。
- Eval：**22 → 23 用例，23/23 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#23 PASS）。
- **合并后回归（main HEAD `2c71b38`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，pending 可忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18/#19/#20/#21/#22/#23 六个负向自测均 PASS、promptfoo **23/23 (100%) / 0 failed / 0 errors**。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint/#18–#23 进 CI、§5.3 规则 2 机器化
   仍无法落地；七个 eval-only 严格/负向层（#17/#18/#19/#20/#21/#22/#23）目前都只在本地/本循环把关，未进 GitHub
   required checks。
3. #23 复制 7 个真实内容文件；若这些文件的**合法演进**改变了健康基线（marker 增删、五项措辞调整），健康复制树会
   fail-loud，需在同一 PR 同步本自测——有意的 fail-loud（同 #20/#22 策略）。其余直白 substring 检查（五项 items、
   status-line header、ADR/provenance 等指针 marker）与已覆盖的存在性检查同形，刻意不逐串堆夹具（有意的克制）。
4. 剩余未做负向沉淀的 guard（risk_matrix/print_bench/runtime_provenance/three_chain/sink_layers/cega）多为直白
   substring/存在性检查，缺独立正则检测器，负向自测价值边际递减；下一轮须先证明确有"可被改宽且正向全绿"盲区才做。
5. 真·双链 pub/sub / p99 / 跨机 UDP / 三链复现本机仍 blocked（无 Humble runtime）。

### 下一步（轮次 18 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，用离线备份补仅含 ci.yml 接线的独立 PR（frozen gate test-f +
   运行 step；纯标准库、无需 npx 联网的 fingerprint_check.py 与六个 guard selftest 比整套 promptfoo 更适合先纳入
   CI），回填 ci-cd-gates.md §1、删 §6 pending；接线后再做 §5.3 规则 2 机器化。
2. 评估剩余六个 guard（risk_matrix/print_bench/runtime_provenance/three_chain/sink_layers/cega）是否存在独有、
   可被改宽的检测器：多数是直白 substring/存在性，须先证与正向用例/#17 指纹/#18–#23 不重复、夹具可在 tempdir 构造、
   且有真实盲区才沉淀；重复或低价值则不做，避免断言堆砌。
3. 视批准推进 CVE 修复独立 PR；4 份飞书文档授权后补读。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+#18–#23+eval 回归并在日志标注「等待新指令」，
   不制造无意义提交。

---

## 轮次 18 — 2026-09-20 09:15（Asia/Shanghai）《5》深化：Cega / Bridge Hold guard 独有解析负向自测沉淀为 eval 用例 #24

> 定时任务第 18 轮。分支 `test/cega-hold-guard-selftest`，PR #74（已 squash-merge，main HEAD `0e6e065`）。
> 开工核对：轮次 17 功能 PR #72 与回填 PR #73 均已 squash-merge，main HEAD `a4e96fb`；`gh pr list` 中在途 PR
> （#65/#61/#56/#46/#45/#44/#43/#42/#41/#32/#31/#30）全是他人 claude/cursor/codex 机器人 PR，未触碰；本循环
> 无在途 PR。`workflow` scope 仍未授予、CVE 修复仍待批准。本轮执行轮次 17「下一步候选 2」：逐一评估剩余六个
> 未做负向沉淀的 guard，先证不重复、再挑出**独有解析最复杂、守护最高优先级 Hold** 的一个——
> `check_cega_bridge_hold.py`（wiki3 §13(4) 不集成 Cega / 不重写 Bridge runtime）。

### 背景 / 覆盖缺口取证（先证与 #9/#17/#23 不重复）
- 逐一读完剩余六个 guard 评估独有盲区：`check_risk_matrix.py`（146 行）纯 marker substring/存在性 + 一个
  `all(token in text)` 层级顺序，**无独立正则检测器，确认低价值不做**；`print_bench_gates.py`（137 行）纯 marker
  存在性 + cross-host blocked 扫描，直白；`check_runtime_provenance.py`（210 行）有 Dockerfile 多行 ENV 解析与
  VERSIONS SHA 行检查，是次优候选；`check_three_chain_repro.py`（231 行）的 fabricate 检测器与 #23 高度同构、
  独有仅 `map = reproduce`/`reproduce: PASS` 三正则，机制重复度高；`check_sink_layers.py`（248 行）的 ABSENT
  vendor-tree 机制已被 #22 覆盖，独有仅 `_LAYER_ROW_RE` 表格行锚定与 iceoryx。
- **选定 cega（363 行，六个里解析最复杂、守护最高优先级 Hold）**，其独有检测器：
  ①`_ADR_ROW_RE` / `_adr_row_ok` / `_CELL_POSITIVE_RE` 解析 ADR 表格里**单个 §13(4) cell**——cell 必须以
  `**Hold**` 开头、且 cell 内任何位置都不得有 PASS/PROVEN/Active/OK/SUCCESS/已接 Cega/integrate Cega（注意 cell
  检测**不做**禁止词豁免，只有全文 `_fabricate_hits` 才豁免）；
  ②guard **内置** `_row_self_check(adr_text)`：运行时对真实 ADR 做两个内存变异（Hold→PASS、Hold cell 后追加
  PASS/已接 Cega），断言 `_adr_row_ok` 都返回 False，健康 ADR 上返回 `[]`（检测器被改宽时 guard 自己会红的纵深
  防御，#18–#23 均无此内置自检）；
  ③`_CEGA_FABRICATE_RES` 三条独有伪造正则（Cega/Bridge:PASS、中文 `已接 Cega`、integrat(e|ed|ion) Cega）+
  `_STATUS_FABRICATE_RE`（含 Active）+ 比 dod 更宽的 `_PROHIBITION_RE`；
  ④`_first_status_line` 只取**第一个** `Status:` 行，要求 `Status: **Hold**` 且该行无伪造。
- **刻意不重复 #23**：通用 `STATUS: PASS` + 同行禁止句豁免机制两个 guard 各有一份、同构，不重复堆夹具；#24 只
  覆盖上面四组独有解析。可行性探针（一次性 `/tmp/probe_cega_hold.py`，先逐字取真实 FAIL 行再写脚本）11 个场景
  全部符合预期（详见下）。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/cega_bridge_hold_guard_selftest.py`（eval-only，纯标准库，tempdir-only，不是 gate）**：不进
  `run_all_gates.GATES`、不被 CI structure 枚举、无需 ci.yml 接线（不受 workflow scope 阻塞）。夹具策略同 #20/#22/#23：
  把 guard 解析的 **2 个真实内容文件**（Hold 文档、ADR）复制进 `tempfile`（fastdds.xml / SCOREBOARD / 9 个只读
  `dimos_bridge` runtime 路径在该脚本里只验存在，用空占位），再每次只变异一个文档，驱动可注入的 `render(root=...)`：
  1. **5 个负向场景**：N1 ADR §13(4) cell `**Hold**`→`**PASS**`（报 `FAIL ADR row`）；N2 cell 保留 Hold 前缀但
     末尾夹带一个**不带 Cega 字样**的裸 ` ... PASS`（报 `FAIL ADR row` 且**不报** `FAIL fabricate`，探针逐字证明
     是 cell 级检测器而非全文伪造扫描独立抓到）；N3 Hold 文档首个 `Status:` 行翻成 `**PASS**`（报 `FAIL status:
     first Status: must be Status: **Hold**`）；N4 Hold 文档追加独立行 `已接 Cega`（报 `FAIL fabricate hold:
     \`已接 Cega\``）；N5 删除 ADR §13(4) 整行（报 `FAIL ADR row`）；
  2. **2 个防误报（non-flag，双向契约）**：P1 Hold 文档、P2 ADR 中 §13(4) cell **之外**正文各追加一行同行禁止句
     `we do not integrate Cega ...`，必须被禁止词豁免、仍 exit 0 且 cell 行不动仍判 Hold；
  3. **1 个内置自检断言（builtin self-check，本 guard 独有）**：真实 ADR 上 `_row_self_check` 返回空，且它构造的
     两种伪装（Hold→PASS、Hold…PASS/已接 Cega）都被 `_adr_row_ok` 拒绝——把 guard 自带的内存变异纵深防御显式锁定；
  4. **2 个健康对照**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印 `§13(4) Cega / Bridge: Hold`；
  5. **1 个变异**：把 `_CEGA_FABRICATE_RES` tuple 中 `已接 Cega` 那条正则替换为永不匹配 `(?!)`（try/finally
     恢复）后 N4 必须**漏报**（exit 0、无 FAIL fabricate hold），恢复后必须重新抓到。变异刻意选独立行 `已接 Cega`
     而非 cell 正则：neuter `_CELL_POSITIVE_RE` 后 N2 会被 guard 内置 `_row_self_check` 兜住仍 exit 1（内置自检
     引用同一全局正则），漏报不成立；而独立行 `已接 Cega` 只被 tuple 第二条命中，变异干净（探针已验证）。
- `evals/promptfooconfig.yaml`：新增用例 **#24**（断言 `cega bridge hold guard selftest: PASS` + 计数短语
  `5 negative, 2 non-flag, 1 builtin self-check, 2 healthy, 1 mutation`，锁夹具数、防悄悄删负向样本）；用例 23→24。
- `evals/README.md`：文件表加自测脚本、用例数 23→24、seed 段加 #24、用例表加 #24 行、新增「Cega / Bridge Hold
  负向自测（#24）」小节（为何 #9 正向/#17 指纹证明不了 cell/伪造检测器会触发、刻意不重复 #23 的通用 STATUS 机制、
  cell 检测不豁免禁止词而全文 fabricate 豁免的差异、复制 2 真实文件 + 11 existence 占位策略、内置行自检、5/2/1/2/1
  清单、变异验证、eval-only 定位）。
- **未做（Hold/边界）**：未改 `check_cega_bridge_hold.py` 或任何 gate（正常仓 stdout 零变化）；未碰 ci.yml、
  fastdds.xml、SCOREBOARD.md、vendor、`dimos_bridge`；未启用 zenoh/Agnocast、未集成 Cega；无框架/依赖/API 变更；
  不新增 gate（不加剧"本地 13 vs CI 12"背离）。

### 负向有效性验证（证明自测不是摆设）
- 一次性 /tmp 探针逐场景打印真实输出（exit code + FAIL 行）：REAL 与完整复制树 exit 0 + marker；`_row_self_check(real ADR)==[]`；
  N1/N2/N5 仅 `FAIL ADR row`（N2 无 FAIL fabricate，证明 cell 检测器独立）；N3 `FAIL status`；N4 `FAIL fabricate hold:
  \`已接 Cega\``；P1/P2 exit 0（禁止词豁免、cell 未动）；neuter tuple 第二条后 N4 exit 0 无 FAIL fabricate hold（干净
  漏报），恢复后 exit 1 重新抓到。
- 正式脚本：`python3 evals/cega_bridge_hold_guard_selftest.py` → negative 5/5、non-flag 2/2、builtin self-check
  1/1、healthy 2/2、mutation 1/1，PASS、exit 0；`py_compile` 通过。

### 分数前后对比
- Gate：**13/13（100%）**，与轮次 17 持平（未改任何 gate，run_all_gates 不受影响）。
- 指纹：**15/15 stable**（新自测不在 fingerprint 的 15 命令内，gate/load.py stdout 零变化，fixtures 不动、无需 --update）。
- #18 frozen、#19 env、#20 unitree、#21 source-map、#22 executor-map、#23 dod 负向自测：均仍 PASS。
- Eval：**23 → 24 用例，24/24 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#24 PASS，Duration 2s）。
- **合并后回归（main HEAD `0e6e065`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，pending 可忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18/#19/#20/#21/#22/#23/#24 七个负向自测均 PASS、promptfoo **24/24 (100%) / 0 failed / 0 errors**（eval ID `eval-iTz-2026-09-20T01:21:13`）。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint/#18–#24 进 CI、§5.3 规则 2 机器化
   仍无法落地；八个 eval-only 严格/负向层（#17/#18/#19/#20/#21/#22/#23/#24）目前都只在本地/本循环把关，未进 GitHub
   required checks。
3. #24 复制 2 个真实内容文件；若 Hold 文档/ADR 的**合法演进**改变了健康基线（§13(4) 行措辞、Status 头调整），夹具会
   因锚点 `fixture anchor ... not found` 显式 RuntimeError fail-loud，需在同一 PR 同步本自测——有意的 fail-loud（同
   #20/#22/#23 策略）。cell 检测不豁免禁止词是刻意的严格语义（cell 是裁决格、不是叙述），未来若有人在 §13(4) cell 内
   写 "do not integrate Cega" 会被判 FAIL ADR row——这是设计而非误报，禁止语境只能放在 cell 之外（P2 已锁定该边界）。
4. 剩余未做负向沉淀的 guard（risk_matrix/print_bench/runtime_provenance/three_chain/sink_layers）本轮已逐一评估：
   risk_matrix/print_bench 确认直白低价值；runtime_provenance（Dockerfile ENV 解析、VERSIONS SHA 行）、sink_layers
   （`_LAYER_ROW_RE` 表格行、iceoryx absent）、three_chain（map=reproduce 伪造）尚有少量独有逻辑，但边际价值继续递减，
   下一轮须先证明确有"可被改宽且正向全绿"盲区且与 #17/#18–#24 不重复才做。
5. 真·双链 pub/sub / p99 / 跨机 UDP / 三链复现本机仍 blocked（无 Humble runtime）。

### 下一步（轮次 19 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope，用离线备份补仅含 ci.yml 接线的独立 PR（frozen gate test-f +
   运行 step；纯标准库、无需 npx 联网的 fingerprint_check.py 与七个 guard selftest 比整套 promptfoo 更适合先纳入
   CI），回填 ci-cd-gates.md §1、删 §6 pending；接线后再做 §5.3 规则 2 机器化。
2. 评估剩余五个 guard（risk_matrix/print_bench/runtime_provenance/three_chain/sink_layers）是否仍有独有、可被改宽的
   检测器：risk_matrix/print_bench 已确认低价值；runtime_provenance / sink_layers / three_chain 须先证与正向用例/
   #17 指纹/#18–#24 不重复、夹具可在 tempdir 构造、且有真实盲区才沉淀；重复或低价值则不做，避免断言堆砌。
3. 视批准推进 CVE 修复独立 PR；4 份飞书文档授权后补读。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+#18–#24+eval 回归并在日志标注「等待新指令」，
   不制造无意义提交。

---

## 轮次 19 — 2026-09-20 10:31（Asia/Shanghai）《5》深化：runtime-provenance guard 独有解析器负向自测沉淀为 eval 用例 #25

> 定时任务第 19 轮。分支 `test/runtime-provenance-guard-selftest`，PR #76（已 squash-merge，main HEAD `ba33146`）。
> 开工核对：main HEAD `3897cc8`（轮次 18 回填 PR #75 squash），工作区干净（仅受保护旧草稿 `docs/01-dds-request-flow.md`
> untracked，未触碰）；`gh pr list` 中在途 PR（#65/#61/#56/#46/#45/#44/#43/#42/#41/#32/#31/#30）全是他人
> claude/cursor/codex 机器人 PR，未触碰，本循环无在途 PR。`gh auth status` 复核：active 账号仍为 `yixinzhangagent`
> （scopes gist/read:org/repo，**无 workflow**，Git over ssh）；`zhangyinxina-ui` 含 workflow 但 Active=false 且对本仓
> 历史 403——不换凭证、不硬闯，ci.yml 接线 / fingerprint·#18–#25 进 CI / §5.3 规则 2 机器化继续阻塞；CVE 修复仍待批准。
> 本轮执行轮次 18「下一步候选 2」：逐一读完剩余五个未沉淀 guard 中的三个（risk_matrix/print_bench 前轮已确认直白低价值），
> 先证不重复、再挑出**独有解析器无同构覆盖**的一个——`check_runtime_provenance.py`（wiki3 §13 underlay vs overlay vs
> vendor snapshot）。

### 背景 / 三候选横向取舍（先证与 #6/#17/#18–#24 不重复）
- 逐一读完三个仍有少量独有逻辑的候选 guard：
  - `check_three_chain_repro.py`（231 行）：`_STATUS_FABRICATE_RE` + `_PROHIBITION_RE` 同行豁免与 #23/#24 高度同构；
    独有仅 `_FABRICATE_RES` 三正则（three-chain repro:PASS / reproduce:PASS / `map = reproduce` 等号伪造）与
    `_has_three_chains` 的 OR 组合（publish+History+(wait→callback 或 WaitSet+callback)），机制重复度高，**未选**。
  - `check_sink_layers.py`（248 行）：独有 `_LAYER_ROW_RE`（`^\|\s*\*\*(app|rcl|rmw|DDS|executor|memory)\*\*\|`
    表格行行首锚定，注释明示裸 substring "rcl" 会误匹配 app 行里的 rclpy）；ABSENT_VENDOR_TREES 比 executor 多 iceoryx
    但 absent 机制已被 #22 覆盖；policy clauses 是直白 substring，价值中等，**未选**。
  - **`check_runtime_provenance.py`（210 行）= 选定**：两个独有解析器在 #18–#24 中**无同构覆盖**（#20 测的是 unitree
    guard 自己的 VERSIONS 检查，不是本脚本的 `_versions_rows`），守护 underlay/overlay/vendor-snapshot 诚实性与
    "Humble underlay 钉版"。
- 选定 guard 的两个独有解析器：
  ①`_dockerfile_pins_humble(text)->(bool,str)` 用 `_ENV_DISTRO_RE` 多行解析 `ENV ROS_DISTRO`，有三个不同失败分支——
    指令完全缺失（missing）、指令在但 `findall` 为空即值无法解析（is not humble）、钉了非 humble 发行版（pins {bad}）；
  ②`_versions_rows(text)->list[str]` 逐行判定，要求 vendor 树名与 40 位 SHA（`_SHA_RE=\b[0-9a-f]{40}\b`）在**同一行**
    （`row in line and _SHA_RE.search(line)`），SHA 漂到别的行不能让该行通过——不是"全文某处有 SHA 就行"。
  若有人把 ENV 值判断或 SHA 正则改宽，一份钉成 rolling 的 Dockerfile、或 SHA 从表格行脱落的 VERSIONS 表会让 gate、#6、
  #17 指纹（比对的都是健康树输出）继续全绿，underlay/vendor 溯源裁决却已悄悄失真。
- 可行性探针（一次性 `/tmp/probe_runtime_provenance.py`，未入仓，先逐字取真实 FAIL 行再写脚本）：复制全部 5 个真实文件
  （MANIFEST/VERSIONS/Dockerfile/provenance 文档/prove_rmw.py）进 tempdir 再变异，REAL/COPY/N1–N5/四分支直调/mutation
  全部符合预期（详见下）。

### 本轮改动（一项重点改进，仅 evals/；不改任何 gate/生产代码、不碰 ci.yml）
- **新增 `evals/runtime_provenance_guard_selftest.py`（eval-only，纯标准库，tempdir-only，不是 gate）**：不进
  `run_all_gates.GATES`、不被 CI structure 枚举、无需 ci.yml 接线（不受 workflow scope 阻塞）。夹具策略同 #20/#22/#23/#24：
  把 guard 读取的 **5 个真实文件**（MANIFEST、VERSIONS、Dockerfile、provenance 文档、prove_rmw.py，均带连续 marker，
  手写最小健康树易腐）复制进 `tempfile`，再每次只变异一个文件，驱动可注入的 `render(root=...)`：
  1. **5 个负向场景**：N1 Dockerfile `ENV ROS_DISTRO=humble`→`rolling`（报 `FAIL Dockerfile`，pins rolling）；N2 删除
     ENV ROS_DISTRO 行（报 `FAIL Dockerfile`，missing ENV ROS_DISTRO=humble）；N3 保留 `ENV ROS_DISTRO` 但不给可解析值
     （报 `FAIL Dockerfile`，is not humble，覆盖 present-but-unparsed 分支）；N4 把 `vendor/rmw/` 行的 40 位 SHA 替换为
     NO_SHA、保留该行（报 `FAIL VERSIONS rows`，点名 vendor/rmw/）；N5 把该 SHA 挪到文件首行 `moved sha …`、原行留 NO_SHA
     （报 `FAIL VERSIONS rows`，证明是**同行约束**而非全文 SHA 扫描）；
  2. **2 个健康对照**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印 `underlay != vendor snapshot`（证明复制夹具
     与真实树等价，负向场景不会因错误原因失败）；
  3. **1 个变异**：把 `_SHA_RE` 从 40 位 hex 边界匹配改宽为任意单词 `\b\w+\b`（try/finally 恢复）后 N4 必须**漏报**
     （被篡改行仍含 `vendor/rmw/`、`rolling`、`7.11.2` 等单词，exit 0、无 FAIL VERSIONS rows），恢复后同一树必须重新抓到
     exit 1 + FAIL VERSIONS rows——证明 N4 确实依赖严格 SHA 检测器。
  - 探针中还直接调用 `_dockerfile_pins_humble` 逐字确认四分支返回串：rolling→`(False, 'Dockerfile ENV ROS_DISTRO pins
    rolling (need humble)')`、无 ENV→`(False, 'Dockerfile missing ENV ROS_DISTRO=humble')`、无值→`(False, 'Dockerfile
    ENV ROS_DISTRO is not humble')`、健康→`(True, 'ENV ROS_DISTRO=humble')`。
- `evals/promptfooconfig.yaml`：新增用例 **#25**（断言 `runtime provenance guard selftest: PASS` + 计数短语
  `5 negative, 2 healthy, 1 mutation`，锁夹具数、防悄悄删负向样本）；用例 24→25。
- `evals/README.md`：文件表加自测脚本、用例数 24→25、seed 段加 #25、用例表加 #25 行、新增「runtime-provenance Humble
  钉版 / VERSIONS 同行 SHA 负向自测（#25）」小节（为何 #6 正向/#17 指纹证明不了两个解析器会触发、刻意不重复直白 marker
  substring 检查、复制 5 真实文件夹具策略、5/2/1 清单、三分支与同行约束、SHA 正则变异验证、eval-only 定位）。
- **未做（Hold/边界）**：未改 `check_runtime_provenance.py` 或任何 gate（正常仓 stdout 零变化）；未碰 ci.yml、fastdds.xml、
  SCOREBOARD.md、vendor、`dimos_bridge`；未启用 zenoh/Agnocast、未集成 Cega；无框架/依赖/API 变更；不新增 gate（不加剧
  "本地 13 vs CI 12"背离）。

### 负向有效性验证（证明自测不是摆设）
- 一次性 /tmp 探针逐场景打印真实输出：REAL/COPY exit 0 + marker；N1/N2/N3 exit 1 且 FAIL Dockerfile 分支串逐字正确；
  N4/N5 exit 1 且 FAIL VERSIONS rows + vendor/rmw/；宽化 `_SHA_RE=\b\w+\b` 后 N4 干净漏报（exit 0、无 FAIL VERSIONS rows），
  恢复后同一树 exit 1 重新抓到。
- 正式脚本：`python3 evals/runtime_provenance_guard_selftest.py` → negative 5/5、healthy 2/2、mutation 1/1，
  打印 `runtime provenance guard selftest: PASS (5 negative, 2 healthy, 1 mutation)`、exit 0；`py_compile` 通过。

### 分数前后对比
- Gate：**13/13（100%）all gates green**，与轮次 18 持平（未改任何 gate，run_all_gates 不受影响）。
- 指纹：**15/15 stable**（新自测不在 fingerprint 的 15 命令内，gate/load.py stdout 零变化，fixtures 不动、无需 --update）。
- #18 frozen、#19 env、#20 unitree、#21 source-map、#22 executor-map、#23 dod、#24 cega 负向自测：均仍 PASS（八个自测全绿）。
- Eval：**24 → 25 用例，25/25 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#25 PASS，Duration 15s，
  eval ID `eval-ElJ-2026-09-20T02:29:10`）。
- **合并后回归（main HEAD `ba33146`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18/#19/#20/#21/#22/#23/#24/#25 八个负向自测均 exit 0、promptfoo **25/25 (100%) / 0 failed / 0 errors**（eval ID `eval-QoZ-2026-09-20T02:46:49`，Duration 3s）。

### 剩余风险 / 薄弱环节
1. 轮次 0 风险 1–4 不变（Unitree Cyclone CVE 待批准修复、无 Humble runtime、飞书 3380004、bench 依赖未锁）。
2. **[凭证·仍阻塞]** workflow scope 未授予：frozen gate ci.yml 接线、fingerprint/#18–#25 进 CI、§5.3 规则 2 机器化仍无法
   落地；九个 eval-only 严格/负向层（#17/#18/#19/#20/#21/#22/#23/#24/#25）目前都只在本地/本循环把关，未进 GitHub required checks。
3. #25 复制 5 个真实文件；若 Dockerfile 钉版行或 VERSIONS 六行 SHA 的**合法演进**改变了变异锚点（如未来升级 underlay 发行版、
   vendor 树 SHA 例行更新），夹具会因锚点 `fixture anchor ... not found` 显式 RuntimeError fail-loud，需在同一 PR 同步本自测
   ——有意的 fail-loud（同 #20/#22/#23/#24 策略）。MANIFEST/provenance 文档的直白 marker substring 检查刻意不逐串堆夹具
   （与正向用例同形、无解析器）。
4. 剩余未做负向沉淀的 guard：risk_matrix/print_bench 已确认直白低价值；sink_layers 仅剩 `_LAYER_ROW_RE` 表格行锚定（可造"缺
   rcl 行但 app 行含 rclpy"夹具）、three_chain 仅剩 `map = reproduce` 等号伪造与 `_has_three_chains` OR 组合尚有少量独有逻辑，
   但边际价值继续递减，下一轮须先证明确有"可被改宽且正向全绿"盲区且与 #17/#18–#25 不重复才做。
5. 真·双链 pub/sub / p99 / 跨机 UDP / 三链复现本机仍 blocked（无 Humble runtime）。

### 下一步（轮次 20 候选）
1. **（阻塞解除后最高优先）** 授予 workflow scope（本机 `gh auth refresh -h github.com -s workflow`，active 账号
   `yixinzhangagent`；不要擅自切到 `zhangyinxina-ui`，它对本仓 403），用离线备份 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`
   补仅含 ci.yml 接线的独立 PR——优先把纯 python、无需 npx 联网的 fingerprint_check.py 与八个 guard selftest 先于整套 promptfoo
   纳入 CI，回填 ci-cd-gates.md §1、删 §6 pending；接线后再做 §5.3 规则 2 机器化。
2. 评估 sink_layers `_LAYER_ROW_RE` 表格行锚定、three_chain `map = reproduce` 等号伪造/`_has_three_chains` OR 组合是否仍有独有、
   可被改宽的检测器：须先证与正向用例/#17 指纹/#18–#25 不重复、夹具可在 tempdir 构造、且有真实盲区才沉淀；重复或低价值则不做，
   避免断言堆砌。
3. 视批准推进 CVE 修复独立 PR（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）；4 份飞书文档授权后补读。
4. 若仍无授权且无新的不越界高价值项：做一次完整 gate+指纹+#18–#25+eval 回归并在日志标注「等待新指令」，不制造无意义提交。
## 轮次 20 — 2026-09-20 11:30（Asia/Shanghai）《5》深化：sink-layers guard 六层表格行首标签锚定负向自测沉淀为 eval 用例 #26

> 定时任务第 20 轮。分支 `test/sink-layers-guard-selftest`，功能 PR #78（已 squash-merge，main HEAD `a6e29d3`）。
> 主题：把 `scripts/check_sink_layers.py` 唯一的结构化解析器 `_LAYER_ROW_RE`（六层 sink 表格**行首粗体标签锚定**）
> 的负向能力从一次性 /tmp 探针沉淀为 eval-only、纯标准库、tempdir-only 的仓内回归，即 Promptfoo 用例 **#26**。
> 一次只做一个 guard，不与 three_chain 候选堆叠。

### 为什么是这一项（候选取舍，先取证再动手）

- re-ground：本地在 main、与 origin/main 同步于 `9c5b796`（轮次 19 回填 #77），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；`gh pr list` 确认本循环无在途 PR（开放的 #65/#61/#56/#46/#45/#44/
  #43/#42/#41/#32/#31/#30 全是他人 claude/cursor/codex 机器人 PR，未触碰）。
- 最高优先的 ci.yml 接线仍被 GitHub `workflow` scope 阻塞（active `yixinzhangagent` 仅 gist/read:org/repo），本轮不能自行
  授权；CVE 修复三项待用户明确批准；4 份飞书文档仍 3380004 无权限；真·双链 pub/sub/p99/跨机 UDP/三链复现本机恒
  `STATUS: blocked`。故本轮仍在"不依赖授权的 eval 负向沉淀"通道推进。
- 轮次 18/19 两次书面提示 sink_layers / three_chain 边际价值递减、须先证明确有独立盲区。本轮**先 Read 两个 guard 取证**：
  - `check_sink_layers.py`（248 行）唯一较有价值的独有解析器是
    `_LAYER_ROW_RE = re.compile(r"(?m)^\|\s*\*\*(app|rcl|rmw|DDS|executor|memory)\*\*\s*\|")`，脚本 L49 注释明示
    "Substring `rcl` would also match `rclpy` in the app row"。grep 取证：真实 sink 文档 L34 app 行正文本就含
    `` `rclpy` ``、L38 executor 行含 `rclcpp`/`rclpy`、L28 散文与 L43/44 mermaid 含裸 `rcl`，`DDS` 一词满屏；六个
    粗体行标签 `| **app/rcl/rmw/DDS/executor/memory** |` 各唯一出现一次（L34–L39）。
  - 这构成一个真实、注释背书、可被"重构简化"引入、且 #17/#18–#25 均未覆盖的盲区：若把行检查退化为裸词扫描，删掉
    `| **rcl** |` 行标签、只留周围正文，gate / 正向 #9 / #17 指纹（都比对健康树输出）会继续全绿，六层 sink 表却已丢行。
  - 不重复边界：`_SINK_MARKERS`/`_POLICY_CLAUSES`/Hold-vs-allowed/three-chain/Unitree pointer 都是直白 `token in text`
    （正向用例同形，不堆夹具）；`ABSENT_VENDOR_TREES`（含 iceoryx）缺席机制已由 #22 executor-map 自测覆盖。
  - `check_three_chain_repro.py` 的 fabricate 机制与 #23/#24 高度同构，本轮**不做**（一次一个 guard，留待后续若证出
    `_has_three_chains` OR 组合确有独立盲区再说）。

### 改了什么（行为不变，eval-only，新增负向覆盖）

- 新增 `evals/sink_layers_guard_selftest.py`（纯标准库、tempdir-only、非 gate）：把 guard 读取的 **7 个真实文件**
  （sink/ADR/source-map/executor/Unitree-swap 五个内容文档 + 仅验存在的 fastdds.xml/SCOREBOARD）复制进临时树，再每次只把
  sink 文档的一个表格行标签置空（`| **rcl** |`→`|  |`，**整行正文一字不动**，故 Humble/Rolling/eCAL/DPDK/Isaac/
  0.10.2/11.0.1 等行内 marker 全部保留），驱动可注入的 `render(root=...)`：
  - **2 个负向场景**：N1 置空 rcl 行标签（裸词扫描会被 app 行 `rclpy`、executor 行 `rclcpp` 救回）；N2 置空 DDS 行
    标签（裸词扫描会被满屏散文 `DDS` 救回）。两者都必须 exit 1、打印 `FAIL layers` 并点名对应 `| **<层>** |`，且
    **不得连带** `FAIL markers`/`FAIL policy`（证明只触发行锚定检查、行正文 marker 未丢）。
  - **2 个健康对照（双向契约）**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印
    `sink layers: mapped (Hold vs allowed)`——同时证明 app/executor 行里丰富的 `rclpy`/`rclcpp`/`DDS` 散文不会被
    误判成缺行（防改严误报方向）。
  - **1 个变异**：把 `_LAYER_ROW_RE` 改宽为去掉行首锚定与粗体要求的裸词
    `re.compile(r"(?m)(app|rcl|rmw|DDS|executor|memory)")`（try/finally 恢复）后，N1 篡改树必须**漏报**（exit 0、
    无 FAIL layers），恢复行锚定正则后必须重新抓到——精确复现脚本注释警告的 substring 陷阱。
  - 成功 marker：`sink layers guard selftest: PASS`，计数串 `2 negative, 2 healthy, 1 mutation`。
- 动手前先写 `/tmp/probe_sink_layers.py` 逐字取真实 FAIL 行：REAL/COPY exit 0；N1 exit 1 且 FAIL layers 精确点名 rcl、
  不连带 markers/policy；N2 点名 DDS；宽化后 N1 exit 0 干净漏报、恢复后 exit 1 重新抓到。探针全过才写正式脚本。
- `evals/promptfooconfig.yaml`：新增用例 **#26**（断言 `sink layers guard selftest: PASS` + 计数短语
  `2 negative, 2 healthy, 1 mutation`，弱化/删负向用例即红）。
- `evals/README.md`：文件表 yaml 用例数 25→26、新增 sink_layers selftest 文件行、seed 段计数与列举加 #26、用例表加
  #26 行、新增「sink-layers 六层表格行首标签锚定负向自测（#26）」专节。
- `docs/refactor/ITERATION_LOG.md`：评分口径行 25→26 并加 #26 描述 + 本小节。

### 分数前后对比 / 产物检查（本机 vanilla box，无 ROS）

- Gate：**13/13 all gates green**（未改任何 gate/helper，行为不变）。
- stdout 指纹：**15/15 stable**（gate/load.py stdout 零变化，未动 fixtures、无需 `--update`）。
- guard 负向自测：**#18–#26 九个全部 exit 0**（本轮新增 sink_layers: PASS，2 negative/2 healthy/1 mutation）。
- Eval：**25 → 26 用例，26/26 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#26 PASS，Duration 5s，
  eval ID `eval-DVz-2026-09-20T03:29:39`，UTC；约合 CST 11:29）。
- **合并后回归（main HEAD `a6e29d3`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#26 九个负向自测均 exit 0、promptfoo **26/26 (100%) / 0 failed / 0 errors**（eval ID `eval-25t-2026-09-20T03:36:54`，Duration 3s）。
- `python3 -m py_compile evals/sink_layers_guard_selftest.py` 通过。
- 可视化/产物检查：selftest stdout 实跑核对计数串与 marker；yaml/README 改动经 grep 复核四处登记一致。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字（selftest 仅把两者**只读复制**进 tempdir）。
- 未启用 Agnocast/zenoh（无 vendor 树/kmod/rmw_zenoh）；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、
  未重写 Bridge runtime。双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整（eval-only 测试 + 文档）；promptfoo 仅 npx 缓存运行、未写入运行时依赖。
- 《6》CVE 审计保持只读；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 测试/文档 only，不改生产或 gate 代码，风险低。selftest 复制真实文件、锚点 fail-loud：若 sink 文档六个粗体层标签或
  七个被复制文件的路径**合法演进**，该 PR 须同步更新锚点（与 #20/#22/#23/#24/#25 同一 fail-loud 契约）。
- 真·双链 pub/sub、p99、跨机 UDP、三链复现仍 `STATUS: blocked`（本机无 Humble runtime），本轮不伪造任何通过。
- 本机到 GitHub 443 在轮次 19 曾多次 SSL_ERROR_SYSCALL/EOF；本轮 push/PR 若再遇中断，沿用探测退避（每 20s 探
  http_code 直到 200 再续推），不硬闯、不换凭证。

### 下一步（轮次 21 候选）

1. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`：之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，优先把纯 python、无需 npx 联网的
   `fingerprint_check.py` 与 #18–#26 各 selftest **先于整套 promptfoo** 纳入 CI required checks，再做 §5.3 规则 2 机器化。
2. **[不依赖授权·边际继续递减]** `check_three_chain_repro.py`：须先 Read 全文证实 `_has_three_chains` 的 OR 组合
   （publish+History+(wait→callback 或 WaitSet+callback)）或 `map = reproduce` 等号伪造确有"可被改宽且正向全绿"、
   且与 #23/#24 fabricate 不重复的独立盲区，能 tempdir 构造，才做 #27；否则停止堆 guard selftest。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做一次完整 gate+指纹+#18–#26+promptfoo 回归并在日志标注「等待新指令」，
   不制造无意义提交。
## 轮次 21 — 2026-09-20 12:15（Asia/Shanghai）《5》深化：three-chain 复现 guard 独有伪造正则负向自测沉淀为 eval 用例 #27

> 定时任务第 21 轮。分支 `test/three-chain-repro-guard-selftest`，功能 PR #80（已 squash-merge，main HEAD `490b6a5`）。
> 主题：把 `scripts/check_three_chain_repro.py`（wiki3 §13(2)，map≠reproduce / STATUS: blocked 诚实性）独有的两条
> `_FABRICATE_RES` 伪造正则的负向能力，从一次性 /tmp 探针沉淀为 eval-only、纯标准库、tempdir-only 的仓内回归，即
> Promptfoo 用例 **#27**。一次只做一个 guard。

### 为什么是这一项（先 Read 全文取证，再决定做不做）

- re-ground：main 与 origin/main 同步于 `4bcaaba`（轮次 20 回填 #79），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；`gh pr list` 确认本循环无在途 PR（开放的 #65/#61/#56/#46/#45/#44/
  #43/#42/#41/#32/#31/#30 全是他人 claude/codex/cursor 机器人 PR，未触碰）。
- 轮次 20 日志「下一步」对 three_chain 候选设了硬门槛：**须先 Read 全文证实确有独立、可 tempdir 构造、与 #23/#24
  不重复的盲区，否则停止堆 guard selftest**。本轮先完整 Read `check_three_chain_repro.py`（232 行）再判定：
  - **`_has_three_chains` 的 OR/AND 共现不立项**：`publish AND History AND (wait→callback OR (WaitSet AND callback))`
    是直白 token 共现，guard 在收尾段自述边界就是 “Filesystem + honesty markers only”，从不声称做语义成链验证；
    “WaitSet/callback 在无关位置共现也判第三链存在”是 marker-only 的**设计边界而非 bug**，当前 guard 对这种文本本就
    exit 0，构造不出「当前会 FAIL」的负向；要收紧它属于行为增强（《2》重构，需独立论证），不是 eval-only 负向沉淀。
  - **`_FABRICATE_RES` 第三条 `\bmap\s*=\s*reproduce\b` 与第一条 `(three-chain repro|三条链复现):(PASS|PROVEN|OK)`
    确有独立增量**：健康文档必须连续含 `map ≠ reproduce`（≠，U+2260）与 `STATUS: blocked`，phrase/status 是
    **存在性**检查。若有人在文档末尾**额外追加**一句 ASCII `map = reproduce`（矛盾等号）或 `three-chain repro: PROVEN`
    而保留所有健康 marker，phrase/status/chains/markers 检查全部通过，**只有这两条 fabricate 正则能抓到**。被守护文档、
    正则、伪造串都与 #23（DoD）、#24（Cega）不同——机制同族（fabricate 正则 + 同行禁止句豁免），但守护对象独立，
    符合 #20/#22/#25/#26 一贯的「同构机制、不同 guard/不同正则分别立项」标准。
  - 不重复边界：六个 required 文件的 marker substring 检查（正向同形）、`_has_three_chains`（marker-only 边界）、
    `_STATUS_FABRICATE_RE` 的 STATUS: PASS 同族正则（#23/#24 已钉）均不重复堆夹具。

### 改了什么（行为不变，eval-only，新增负向覆盖）

- 新增 `evals/three_chain_repro_guard_selftest.py`（纯标准库、tempdir-only、非 gate）：把 guard 读取的 **6 个真实文件**
  （repro/source-map/executor/ADR 四个内容文档 + 仅验存在的 fastdds.xml/SCOREBOARD）复制进临时树，每次只向 repro 文档
  **末尾追加一句**（不删任何 marker），驱动可注入的 `render(root=...)`：
  - **2 个负向场景**：N1 追加裸 `map = reproduce`（ASCII `=`；`map ≠ reproduce` 仍在故 phrase 检查通过，只有正则
    `\bmap\s*=\s*reproduce\b` 抓到矛盾）；N2 追加 `three-chain repro: PROVEN`（命中第一条；相邻 `reproduce:` 正则刻意
    不匹配短词 `repro`）。两者都必须 exit 1、打印 `FAIL fabricate` 并点名伪造串，且**不得连带** FAIL missing/markers/
    phrase/status/chains（证明健康 marker 全存活、只触发诚实性检查）。
  - **1 个 non-flag（豁免契约）**：同行禁止句「不要把 map = reproduce 写进结论」必须被 `_PROHIBITION_RE`+`_line_at`
    豁免、整树 exit 0 且无 FAIL fabricate（防未来把豁免改严、误杀合法「不要写」指令；钉本 guard 自己的中英禁止词表）。
  - **2 个健康对照**：真实仓 `render()` 与完整复制临时树都必须 exit 0 且打印 `three-chain repro: blocked (map only)`。
  - **1 个变异**：把 `\bmap\s*=\s*reproduce\b` 替换为永不匹配的 `(?!)`（try/finally 恢复整个 `_FABRICATE_RES` 元组）
    后 N1 必须**漏报**（exit 0、无 FAIL fabricate），恢复后必须重新抓到。
  - 成功 marker：`three-chain repro guard selftest: PASS`，计数串 `2 negative, 1 non-flag, 2 healthy, 1 mutation`。
- 动手前先写 `/tmp/probe_three_chain.py` 逐字取真实行为：REAL/COPY exit 0；N1/N2 exit 1 且 FAIL fabricate 点名、
  五类 FAIL 均不连带；禁止句 exit 0 豁免；neuter 第三条正则后 N1 exit 0 干净漏报、恢复后 exit 1 重抓。探针全过才写
  正式脚本。正式脚本模块 docstring 含正则反斜杠，已用 raw docstring（`r"""`）消除 `SyntaxWarning`，
  `python3 -W error::SyntaxWarning -m py_compile` 干净。
- `evals/promptfooconfig.yaml`：新增用例 **#27**（断言 `three-chain repro guard selftest: PASS` + 计数短语
  `2 negative, 1 non-flag, 2 healthy, 1 mutation`，弱化/删负向用例即红）。
- `evals/README.md`：文件表 yaml 用例数 26→27、新增 three_chain selftest 文件行、seed 段计数与列举加 #27、用例表加
  #27 行、新增「three-chain 复现 guard 独有伪造正则负向自测（#27）」专节（含为何 `_has_three_chains` 不立项的说明）。
- `docs/refactor/ITERATION_LOG.md`：评分口径行 26→27 并加 #27 描述 + 本小节。

### 分数前后对比 / 产物检查（本机 vanilla box，无 ROS）

- Gate：**13/13 all gates green**（未改任何 gate/helper，行为不变）。
- stdout 指纹：**15/15 stable**（gate/load.py stdout 零变化，未动 fixtures、无需 `--update`）。
- guard 负向自测：**#18–#27 十个全部 exit 0**（本轮新增 three_chain: PASS，2 negative/1 non-flag/2 healthy/1 mutation）。
- Eval：**26 → 27 用例，27/27 passed (100%) / 0 failed / 0 errors**（promptfoo 0.123.1，#27 PASS，Duration 2s，
  eval ID `eval-XS7-2026-09-20T04:15:04`，UTC；约合 CST 12:15）。
- **合并后回归（main HEAD `490b6a5`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#27 十个负向自测均 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（eval ID `eval-e1Z-2026-09-20T04:21:10`，Duration 3s）。
- `python3 -W error::SyntaxWarning -m py_compile evals/three_chain_repro_guard_selftest.py` 干净通过。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字（selftest 仅把两者**只读复制**进 tempdir）。
- 未启用 Agnocast/zenoh（无 vendor 树/kmod/rmw_zenoh）；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、
  未重写 Bridge runtime。双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整（eval-only 测试 + 文档）；promptfoo 仅 npx 缓存运行、未写入运行时依赖。
- 《6》CVE 审计保持只读；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 测试/文档 only，不改生产或 gate 代码，风险低。selftest 复制真实文件、锚点 fail-loud：若 repro 等六个被复制文件的
  路径或健康 marker 文本**合法演进**，该 PR 须同步更新锚点（与 #20/#22–#26 同一 fail-loud 契约）。
- guard 负向 selftest 序列（#18–#27）已覆盖全部 13 个 gate 中带独有解析器的 guard；剩余 gate 的检查多为直白 marker
  substring（正向同形），继续堆同形负向夹具边际价值已很低，下一轮起原则上**停止新增 guard selftest**，除非又证出
  某个未覆盖的独有解析器。
- 真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`（本机无 Humble runtime；本轮只钉诚实性文档，
  不代表复现已运行），不伪造任何通过。

### 下一步（轮次 22 候选）

1. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`：之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，优先把纯 python、无需 npx 联网的
   `fingerprint_check.py` 与 #18–#27 各 selftest **先于整套 promptfoo** 纳入 CI required checks，再做 §5.3 规则 2 机器化。
2. **[guard selftest 收尾]** #18–#27 已覆盖各独有解析器；除非再证出未覆盖的独有解析器，否则不再新增同形负向夹具，
   转向《2》计划里不依赖授权的小步重构（简化控制流/抽辅助函数/替换陈旧模式，行为不变、stdout 指纹护航）。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做一次完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，
   不制造无意义提交。
## 轮次 22 — 2026-09-20 13:18（Asia/Shanghai）《2》小步重构：收敛 dual-chain guard 内 shell↔load.py 键值比对的重复列表推导

> 定时任务第 22 轮。分支 `refactor/dual-chain-shell-crosscheck-helper`，功能 PR #82（已 squash-merge，main HEAD `a06f5df`）。
> 轮次 21 已宣告 guard 负向自测（#18–#27）收尾，本轮按既定方向回到《2》现代化重构计划，做一项**行为不变、纯提取**的
> 「抽辅助函数」小步（plan §3 Step 3 精神），由 #17 stdout 指纹逐字节护航。一次只改一个脚本。

### 选题前的盘点（确认 Step 1–4 已落地，避免为改而改）

- re-ground：main 与 origin/main 同步于 `1ea19e5`（轮次 21 回填 #81），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；本循环无在途 PR（开放 PR 全是他人 claude/codex/cursor 机器人项，未触碰）。
- 逐项核对 plan §3：Step 1 死代码（迭代 1 删 `legacy_compare`）、Step 2 冻结路径样板（`_freeze_paths.py` + 9 个脚本 import +
  第 13 闸 `check_frozen_path_literals`，残留命中均为消息文本/`_SINK_MARKERS` 标记串/guard 自身，非 `Path(...)` 定义，不可动）、
  Step 3 `_md_paths.py` 收敛（`check_source_map`/`check_executor_map` 由 320/407 行降到 143/225 行）、Step 4 双链真源
  （`load.py` 唯一可执行真源 + `dual_chain_env.py` docstring 已写明真源指针 + 迭代 3 的四类 env 交叉检查）均已落地。
- 全脚本扫描确认：无直接 `open()`/`read_text()` 残留（统一走 `_repo.read_utf8`）；importlib 模块加载样板仅
  `check_dual_chain_baseline.py` 一处（`dimos_bridge/dual_chain_env.py` 那份在 B 面薄包装里，跨面不引 scripts helper），
  单一使用点抽 helper 属过度抽象，**不做**。
- 真实剩余重复：最大的 A 面脚本 `check_dual_chain_baseline.py`（470 行，迭代 3 扩充）里，chain_a / chain_b 两段
  「shell `export` 字面量 vs `load.py` chain dict」交叉检查各有一段**同构的 4 行列表推导**，f-string 完全相同、仅
  `sh_a/chain_a` 与 `sh_b/chain_b` 变量不同。这是本轮收敛对象。

### 改了什么（纯提取，+21/−10，只动 `scripts/check_dual_chain_baseline.py`）

- 新增模块级常量 `_SHELL_CROSS_KEYS = ("RMW_IMPLEMENTATION", "ROS_DOMAIN_ID")` 与辅助函数
  `_shell_key_drifts(shell_exports, chain, keys=_SHELL_CROSS_KEYS)`：逐键比较字面 shell 值与 `load.py` chain dict，
  返回与原内联推导**逐字相同**的漂移描述串 `f"{key}: shell={...!r} load.py={...!r}"`。
- chain_a / chain_b 两段各把 4 行内联列表推导替换为一次 `_shell_key_drifts(...)` 调用；两条 FAIL/ok 渲染分支、
  failures 收集、exit code 全部不动。
- **刻意保留**：chain_a 独有的 `FASTRTPS_DEFAULT_PROFILES_FILE` 路径解析比较（含 `${_ROS2_HZJ_ROOT}` 替换）留在原处，
  不进共享 helper（它是路径语义、chain_b 没有）；`_EXPECTED_CHAIN_A/B` 仍在 guard 内**独立硬编码**期望值
  （guard 不能 import `load.py` 的值来检查 `load.py`，否则变成自证）；不碰任何 Hold 面文件。

### 行为不变验证（本机 vanilla box，无 ROS）

- **stdout 逐字节**：重构前后各跑一次 `check_dual_chain_baseline.py`（均 exit 0、38 行），`diff` 为空
  （STDOUT BYTE-IDENTICAL）。
- **helper 等价性探针**（临时脚本，不入仓）：健康（shell==chain）返回 `[]`；单键漂移返回串与原内联推导逐字一致；
  shell 缺键（`None` vs 值）同样判漂移；默认键恰为两个契约键。
- **端到端负向回归**：#19 `evals/dual_chain_env_guard_selftest.py` 全过（**6 negative / 2 healthy / 1 mutation**），
  其中 shell/load.py cross-check drift 负向场景仍被抓到——证明提取没有把交叉检查改宽。
- Gate：**13/13 all gates green**；stdout 指纹：**15/15 stable**（被重构脚本在 15 条命令内，逐字节无漂移、未动 fixtures）；
  #18–#27 十个负向自测全 exit 0；promptfoo **27/27 passed (100%) / 0 failed / 0 errors**
  （eval ID `eval-1qp-2026-09-20T05:17:54`，UTC；约合 CST 13:17，Duration 5s）。本轮不新增 eval 用例（纯内部重构、
  无新行为；负向能力已由 #19 覆盖）。
- **合并后回归（main HEAD `a06f5df`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#27 十个负向自测均 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（eval ID `eval-2xn-2026-09-20T05:23:05`，Duration 4s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字。
- 未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码（含 `dual_chain_env.py` 薄包装，本轮只动 scripts/）；
  未集成 Cega、未重写 Bridge runtime。双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整（命令名、argv、exit code、关键打印短语全部不变；公共契约稳定）。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 极低。纯脚本内提取，stdout/exit code 逐字节不变，且有 #19 负向自测与 #17 指纹双保险。helper 仅本脚本使用，
  未跨文件导出（不下沉到 `_repo.py`，因为目前只有一个消费方；未来第二个 gate 需要同类 shell 比对时再下沉，避免过早抽象）。
- A 面 Step 1–4 的低垂重构果已基本摘完；后续同类脚本内小重复应继续「先证重复、再提取、指纹护航」，不为凑改动制造提交。
- 真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`（本机无 Humble runtime），不伪造任何通过。

### 下一步（轮次 23 候选）

1. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`：之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，优先把纯 python、无需 npx 联网的
   `fingerprint_check.py` 与 #18–#27 各 selftest **先于整套 promptfoo** 纳入 CI required checks，再做 §5.3 规则 2 机器化。
2. **[《2》续做]** 继续在 A 面脚本里找「有证据的」控制流简化/陈旧模式替换（候选：`check_cega_bridge_hold.py` 363 行、
   `check_dod_evidence.py` 300 行内的局部重复），严守一次一项、行为不变、stdout 逐字节 diff 为空；无真实增量则不提交。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做一次完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，
   不制造无意义提交。
## 轮次 23 — 2026-09-20 14:10（Asia/Shanghai）《2》小步重构：dod guard 的 existence-only 循环反转为单一 ok 出口

> 定时任务第 23 轮。分支 `refactor/dod-existence-only-single-exit`，功能 PR #84（已 squash-merge，main HEAD `97bac5f`）。
> 延续轮次 22 回到《2》计划的节奏，本轮做一项**行为不变、纯控制流简化**（plan §3「简化控制流」），
> 仍由 #17 stdout 指纹逐字节护航、#23 负向自测端到端兜底。一次只改一个脚本。

### 选题取证（先证重复，再动手；不为改而改）

- re-ground：main 与 origin/main 同步于 `4b59ee2`（轮次 22 回填 #83），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；本循环无在途 PR（开放 PR 全是他人机器人项，未触碰）。
- 先查轮次 22「下一步」点名的两个较大 A 面脚本：
  - `check_cega_bridge_hold.py`（363 行）hold 段有 5 个「短语存在性」检查块，但每块的 ok/FAIL label、failure 措辞、
    单短语 / 双短语 AND / 四元组 joined 形态各不相同；抽 helper 需要 5–6 个参数，会把直白代码绕复杂，
    且措辞被 #24 自测锚定。**判定收益边际、可读性下降，本轮不抽**（保留直白）。
  - `check_dod_evidence.py`（300 行）的 required 循环里，existence-only 分支与普通分支各自重复了一遍
    `extra = ...` + `lines.append(ok file)`（两处逐字相同）。grep 取证发现 **`check_dual_chain_baseline.py`
    L216–236 有一段逐字同构的 existence_only 循环**（连 f-string 都一样）。
- 按「一次一项、一个脚本」，本轮只简化 `check_dod_evidence.py` 这一处；`check_dual_chain_baseline.py` 的同构循环
  用同一手法留给轮次 24（避免单 PR 跨两脚本、也与轮次 22 刚改的脚本错开）。

### 改了什么（纯控制流简化，+12/−12，只动 `scripts/check_dod_evidence.py`）

- 原结构：文件存在后先 `if rel in existence_only: 渲染 ok; continue`，否则 read + marker 检查，末尾再渲染一遍 ok
  （ok 渲染重复两处）。
- 新结构：反转为 `if rel not in existence_only:` 才 `read_utf8` + 收集进 `texts` + marker 检查（缺则 FAIL + continue），
  之后**统一落到单一 ok-file 渲染出口**；并补 3 行注释说明 XML/SCOREBOARD 在本脚本里 existence-only、内容从不被读取
  （content freeze 归 boundary job）。
- FAIL missing / FAIL markers / ok file 三类输出行、failure 文案、`texts` 收集集合、exit code 全部不变。

### 行为不变验证（本机 vanilla box，无 ROS）

- **stdout 逐字节**：重构前后各跑一次 `check_dod_evidence.py`（均 exit 0、30 行），`diff` 为空（STDOUT BYTE-IDENTICAL）。
- **existence-only 边界动态证明**：monkeypatch `read_utf8` 计数后调 `render()`，健康路径恰好 **7 次内容读取**
  （9 个 required − 2 个 existence-only），读取集合为 7 个普通 md/脚本，**不含 `fastdds.xml` / `SCOREBOARD.md`**——
  反转控制流没有让 frozen 文件被读取，「existence only; numbers not read」的自我声明边界保持。
- **端到端负向回归**：#23 `evals/dod_evidence_guard_selftest.py` 全过（**5 negative / 2 non-flag / 2 healthy / 1 mutation**），
  伪造 STATUS: PASS / DoD: met / measured-delta / Humble-here 与虚构 booked p99 仍被抓到、同行禁止句与「分位数」政策词保持 green。
- Gate：**13/13 all gates green**；stdout 指纹：**15/15 stable**（被重构脚本在 15 条命令内，逐字节无漂移、未动 fixtures）；
  #18–#27 十个负向自测全 exit 0；promptfoo **27/27 passed (100%) / 0 failed / 0 errors**
  （eval ID `eval-Wqs-2026-09-20T06:10:50`，UTC；约合 CST 14:10，Duration 3s）。本轮不新增 eval 用例（纯内部控制流简化、
  无新行为；负向能力已由 #23 覆盖）。
- **合并后回归（main HEAD `97bac5f`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#27 十个负向自测均 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（eval ID `eval-HLJ-2026-09-20T06:16:21`，Duration 2s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字，且本脚本对这两个文件仍**只验存在、不读内容**。
- 未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime。
  双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整（命令名、argv、exit code、关键打印短语全部不变；公共契约即 stdout，指纹逐字节证明）。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 极低。单脚本控制流反转，stdout/exit code 逐字节不变；read_utf8 计数探针证明 frozen 文件读取边界未变，
  #23 负向自测与 #17 指纹双保险。
- `check_dual_chain_baseline.py` 仍有一处逐字同构的 existence_only 循环（轮次 24 用同一手法收敛）；两处收敛后该模式即清零。
- cega hold 段短语块维持直白（不强行参数化）。真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`
  （本机无 Humble runtime），不伪造任何通过。

### 下一步（轮次 24 候选）

1. **[《2》续做·最直接]** 用本轮同一手法把 `check_dual_chain_baseline.py` L216–236 的逐字同构 existence_only 循环
   反转为单一 ok 出口（同样要求 stdout 逐字节 diff 空、read_utf8 计数证明 XML/SCOREBOARD 不被读取、#19 负向自测全过）。
2. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`，之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，先把纯 python 的 fingerprint + #18–#27
   selftest 纳入 CI required checks，再做 §5.3 规则 2 机器化。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。
## 轮次 24 — 2026-09-20 15:18（Asia/Shanghai）《2》小步重构：dual-chain guard 的 existence-only 循环反转为单一 ok 出口（该模式两处清零）

> 定时任务第 24 轮。分支 `refactor/dual-chain-existence-only-single-exit`，功能 PR #86（已 squash-merge，main HEAD `b6a8fc9`）。
> 本轮直接执行轮次 23 日志「下一步」点名的最直接项：用**完全相同的手法**收敛 `check_dual_chain_baseline.py`
> 里那段与 dod 逐字同构的 existence_only 循环。行为不变、纯控制流简化（plan §3「简化控制流」），
> #17 stdout 指纹逐字节护航、#19 负向自测端到端兜底。一次只改一个脚本。

### 选题与范围

- re-ground：main 与 origin/main 同步于 `c8da188`（轮次 23 回填 #85），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；本循环无在途 PR（开放 PR 全是他人机器人项，未触碰）。
- 轮次 23 已在 `check_dod_evidence.py` 把「existence-only 分支 + 普通分支各渲染一遍 ok file」反转为单一 ok 出口，
  并 grep 取证 `check_dual_chain_baseline.py` L216–236 有逐字同构副本。本轮即收敛该副本，两处同构模式由此清零。
- 与 dod 的一处差异（已核对、保持行为）：dual-chain 的 required 里 `CHAIN_A_REL` / `CHAIN_B_REL` 两个 shell 文件
  markers 也是空元组，但它们**不是** existence-only——后续 shell↔load.py 交叉检查依赖 `texts[rel]`，必须读取。
  反转后它们走 `if rel not in existence_only:` 的 True 分支，照常 `read_utf8` + 进 `texts`，marker 列表为空时落到统一 ok 出口，
  与原逻辑一致。

### 改了什么（纯控制流简化，+12/−12，只动 `scripts/check_dual_chain_baseline.py`）

- 原结构：文件存在后先 `if rel in existence_only: 渲染 ok; continue`，否则 read + marker 检查，末尾再渲染一遍 ok（重复两处）。
- 新结构：反转为 `if rel not in existence_only:` 才 `read_utf8` + 收集进 `texts` + marker 检查（缺则 FAIL + continue），
  之后统一落到**单一 ok-file 渲染出口**；补 3 行注释说明 XML/SCOREBOARD 在本脚本 existence-only、内容从不被读取
  （content freeze 归 boundary job）。
- FAIL missing / FAIL markers / ok file 输出行、failure 文案、`texts` 收集集合（含 chain_a.sh / chain_b.sh）、
  后续 shell 交叉检查与 exit code 全部不变。

### 行为不变验证（本机 vanilla box，无 ROS）

- **stdout 逐字节**：重构前后各跑一次 `check_dual_chain_baseline.py`（均 exit 0、38 行），`diff` 为空（STDOUT BYTE-IDENTICAL）。
- **existence-only 边界动态证明**：monkeypatch `read_utf8` 记录路径后调 `render()`，健康路径恰好 **7 次内容读取**
  （9 个 required − 2 个 existence-only），读取集合为 baseline/ADR/**chain_a.sh/chain_b.sh**/R0/source-map/unitree-swap，
  **不含 `fastdds.xml` / `SCOREBOARD.md`**，且两个 shell 文件确实仍被读取（shell 交叉检查不断粮）。
- **端到端负向回归**：#19 `evals/dual_chain_env_guard_selftest.py` 全过（**6 negative / 2 healthy / 1 mutation**），
  含双链 domain drift、shell/load.py cross-check drift、wrapper re-export drift、import 期 os.environ 污染、
  chain_b.sh CYCLONEDDS_URI 等负向场景。
- Gate：**13/13 all gates green**；stdout 指纹：**15/15 stable**（被重构脚本在 15 条命令内，逐字节无漂移、未动 fixtures）；
  #18–#27 十个负向自测全 exit 0；promptfoo **27/27 passed (100%) / 0 failed / 0 errors**
  （eval ID `eval-Qy9-2026-09-20T07:17:53`，UTC；约合 CST 15:17，Duration 3s）。本轮不新增 eval 用例（纯内部控制流简化、
  无新行为；负向能力已由 #19 覆盖）。
- **合并后回归（main HEAD `b6a8fc9`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#27 十个负向自测均 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（eval ID `eval-w7P-2026-09-20T07:23:43`，Duration 2s）。

### 模式清零说明

- 「existence-only 不读取 + ok-file 渲染重复两处」这一模式在 `check_dod_evidence.py`（轮次 23）与
  `check_dual_chain_baseline.py`（本轮）两处已全部收敛为单一 ok 出口。
- `check_cega_bridge_hold.py` 的 required 循环形态不同：它对 XML/SCOREBOARD 也调用 `read_utf8`（markers 为空、不输出内容）。
  把它统一成「不读取」会**改变**该脚本是否读 frozen 文件这一既有行为，超出「行为不变」范围，本轮不动、也不建议在无明确
  收益时改动（cega hold 段 5 个短语检查块维持直白，不强行参数化，理由同轮次 23）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字，且本脚本对这两个文件仍只验存在、不读内容。
- 未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime。
  双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整（命令名、argv、exit code、关键打印短语全部不变；公共契约即 stdout，指纹逐字节证明）。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 极低。单脚本控制流反转，stdout/exit code 逐字节不变；read_utf8 计数探针证明 frozen 文件不被读取、两个 shell 文件仍被读取，
  #19 负向自测与 #17 指纹双保险。
- A 面「重复 ok 渲染 / 同构列表推导」类低垂果实已连续摘完（轮次 22 helper、轮次 23–24 existence-only 循环）。
  后续应继续坚持「先 grep 取证重复、再小步提取、指纹 + 负向自测护航」，找不到真实增量就不提交。
- 真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`（本机无 Humble runtime），不伪造任何通过。

### 下一步（轮次 25 候选）

1. **[《2》续做]** 重新全仓 grep 取证下一类真实重复/陈旧模式（候选方向：各 guard 末尾 FAIL/ok 汇总渲染、`_line_at` 等小工具
   是否在多个脚本重复定义且值得下沉到 `_repo.py`——须有 ≥2 个消费方才下沉，避免过早抽象）；一次一项、行为不变、stdout 逐字节 diff 空。
2. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`，之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，先把纯 python 的 fingerprint + #18–#27
   selftest 纳入 CI required checks，再做 §5.3 规则 2 机器化。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。
## 轮次 25 — 2026-09-20 16:32（Asia/Shanghai）《2》小步重构：三处逐字相同的 `_line_at` 下沉为共享 `_repo.line_at`

> 定时任务第 25 轮。分支 `refactor/line-at-shared-helper`，功能 PR #89（已 squash-merge，main HEAD `1ed6d78`；PR 号 #88 被他人/机器人占用，本循环功能 PR 实际为 #89）。
> 本轮按轮次 24「下一步」做全仓重复取证，落到一个有 **3 个消费方、逐字相同**的纯工具下沉，
> 属 plan §5.3 helper-boundary（迭代 5 建 `_repo.py`、迭代 9 `_md_paths` 复用 `read_utf8` 的延续）。
> 行为不变：新旧实现对拍逐字等价、三个 guard 的 stdout 逐字节不变，#23/#24/#27 负向自测端到端兜底。

### 取证与选题

- re-ground：main 与 origin/main 同步于 `a4a106e`（轮次 24 回填 #87），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；本循环无在途 PR。
- 列出 `scripts/` 全部顶层函数后，跨脚本同名工具盘点结果：
  - **`_line_at(text, index)`**：在 `check_cega_bridge_hold.py`、`check_dod_evidence.py`、
    `check_three_chain_repro.py` 三处**逐字相同**（同样 6 行函数体：`rfind` 定位行首、`find` 定位行尾、
    末尾无换行则取 `len(text)`）。它是「同行禁止句」判定的纯工具——给定字符 index 返回所在整行，
    供 `_PROHIBITION_RE.search(line_at(...))` 判断被标记 token 是否与豁免句同行。3 个消费方、零业务断言，
    符合下沉 `_repo.py` 的标准（≥2 消费方才下沉，避免过早抽象）。
  - `_fabricate_hits(text)` 虽也在这三个脚本同名出现，但各自的正则集合**独有且不同**
    （dod 的 STATUS/DoD/p99、cega 的 PASS/已接 Cega、three_chain 的 map=reproduce/PROVEN），且分别被
    #23/#24/#27 负向自测的 mutation 用例锚定——**不收敛**，强行合并会制造参数负担、削弱检测器，明确保留。
- selftest 代码本身不 import/调用 `_line_at`（仅 `evals/README.md` 与 #27 selftest 的 docstring 在文字里提到该工具名）。

### 改了什么（净 −8 行，+27/−35，6 个文件）

- `scripts/_repo.py`：新增公共函数 `line_at(text, index)`（实现逐字采用三份副本，补 docstring），
  并在模块 docstring 的 helper 清单加入第三项；该模块仍只承载无业务断言的通用工具。
- 三个 guard：`from _repo import repo_root, read_utf8` → 增加 `line_at`（字母序），删除各自本地
  `def _line_at`（6 行 + 分隔空行），5 处调用点 `_line_at(` → `line_at(`（cega 2、dod 1、three_chain 2）。
- 文档工具名同步（各 1 处、纯文字）：`evals/README.md` 的 #27 non-flag 豁免说明、
  `evals/three_chain_repro_guard_selftest.py` 的 docstring，`_line_at` → `line_at`。
- 全仓 `git grep _line_at`（scripts/ + evals/）已无残留；无 bare `line_at` 命名冲突。

### 行为不变验证（本机 vanilla box，无 ROS）

- **新旧实现对拍**：从 `git show HEAD:scripts/check_dod_evidence.py` 取出重构前原始 `_line_at`，与新
  `_repo.line_at` 在 6 组样本（含无换行、首尾换行、空行、中文多行）的**每个字符 index** 上对拍，结果逐字一致
  （IDENTICAL across all indices）。
- **stdout 逐字节**：cega / dod / three_chain 三个 guard 重构前后各跑一次（均 exit 0，35 / 30 / 23 行），
  三份 `diff` 全空。
- **端到端负向回归**：#23 `dod_evidence_guard_selftest`、#24 `cega_bridge_hold_guard_selftest`、
  #27 `three_chain_repro_guard_selftest` 全 PASS——「被标记 token 与豁免句同行则不报」的豁免逻辑、
  以及「正则被改宽即漏报、自测变红」的 mutation 用例在函数搬家后照常工作。
- `python3 -m compileall -q scripts config/env dimos_bridge/dual_chain_env.py` 通过；
  gate **13/13 all gates green**；stdout 指纹 **15/15 stable**（三个被改 guard 均在 15 条命令内，逐字节无漂移、
  未动 fixtures）；#18–#27 十个负向自测全 exit 0；promptfoo **27/27 passed (100%) / 0 failed / 0 errors**
  （eval ID `eval-rOi-2026-09-20T08:32:05`，UTC；约合 CST 16:32，Duration 2s）。本轮不新增 eval 用例
  （纯工具搬家、无新行为；同行豁免负向能力已由 #23/#24/#27 覆盖）。
- **合并后回归（main HEAD `1ed6d78`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#27 十个负向自测均 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（eval ID `eval-R2n-2026-09-20T08:38:47`，Duration 2s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；三个 guard 对 frozen 文件的
  existence-only / 不读取边界不变（本轮只动同行定位工具，未触碰 required 循环与读取集合）。
- 未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime。
  双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整：guard 的命令名、argv、exit code、关键打印短语全部不变
  （公共契约即 stdout，指纹逐字节证明）；`line_at` 是下划线 helper 模块内的新公共函数，不进 CI 命令枚举。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 极低。纯函数从三个 guard 搬到共享 helper：新旧体现在全 index 对拍等价、三个 guard stdout 逐字节不变，
  且依赖该工具的三个负向自测（含 mutation）全过。改动反而消除了三份未来可能漂移的副本（单一真源）。
- A 面低垂果实继续收敛中（轮次 22 helper、23–24 existence-only 循环、本轮 line_at）。仍坚持
  「先 grep 取证重复 / ≥2 消费方才下沉 / 指纹 + 负向自测护航」，不为凑改动抽象独有逻辑（如 `_fabricate_hits`）。
- 真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`（本机无 Humble runtime），不伪造任何通过。

### 下一步（轮次 26 候选）

1. **[《2》续做]** 继续全仓取证下一类真实重复：候选方向是各 guard 末尾「FAIL 汇总 + ok/SUCCESS 收尾」渲染块、
   以及 `_has_*` / 行解析小工具是否在 ≥2 个脚本逐字同构（须先 grep + 逐字比对确认，独有正则/独有措辞一律不合并）；
   一次一项、行为不变、stdout 逐字节 diff 空、helper 单一真源。
2. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`，之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，先把纯 python 的 fingerprint + #18–#27
   selftest 纳入 CI required checks，再做 §5.3 规则 2 机器化。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。
## 轮次 26 — 2026-09-20 17:16（Asia/Shanghai）《2》小步重构：12 个脚本逐字相同的 `main()` 入口样板下沉为 `_repo.emit_render`

> 定时任务第 26 轮。分支 `refactor/shared-emit-render-main`，功能 PR #91（已 squash-merge，main HEAD `2ad01f8`）。
> 延续轮次 25 的全仓重复盘点，本轮用 AST + 逐字节哈希比对锁定一个有 **12 个消费方、逐字节相同**的入口样板，
> 属 plan §5.3 helper-boundary。行为不变：12 个脚本 stdout 逐字节 diff 空、exit code（含非零）透传有探针证明。

### 取证与选题

- re-ground：main 与 origin/main 同步于 `1703398`（轮次 25 回填 #90），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；开放 PR 全是他人/机器人（claude/codex/cursor；#88 为 claude DRAFT，
  解释了轮次 25 号段跳号），本循环无在途 PR。
- 用 `ast` 抽取 `scripts/*.py` 全部 `main()` 并归一化分组，再对源码段与 `if __name__` 尾块分别算 SHA-256：
  - **12 个脚本的 `main()` 与 `__main__` 尾块各自落在同一个哈希组（逐字节相同）**：
    11 个 `check_*`（cega/dod/dual_chain/executor/frozen/risk/runtime/sink/source/three_chain/unitree）+
    `print_bench_gates.py`。它们的入口都是
    `text, code = render(); sys.stdout.write(text); return code`，尾块都是
    `if __name__ == "__main__": raise SystemExit(main())`。
  - `prove_rmw.py` 形态不同（`render()` 返回 str、恒 `return 0`），`run_all_gates.py` 是 runner（自带表格汇总），
    二者**不纳入**，不强行统一。
- 逐脚本确认 `sys` 在这 12 个文件里只出现两次：`import sys` 与 main 内唯一的 `sys.stdout.write(text)`；
  10 个已 `from _repo import ...`，`check_executor_map.py` / `check_source_map.py` 只经 `_md_paths` 间接使用、
  本文件无 `_repo` import。消费方 12 个、纯机械样板、零业务断言，远超「≥2 消费方才下沉」的门槛。

### 改了什么（净 −22 行，+36/−58，13 个文件）

- `scripts/_repo.py`：新增公共 `emit_render(result: tuple[str, int]) -> int`——写出 render 结果的 text、原样返回
  exit code（docstring 给出一行用法 `return emit_render(render())`）；模块 docstring helper 清单加第四项。
  该模块本就 `import sys`，未新增依赖。
- 12 个脚本统一：
  - `main()` 四行体 → 一行 `return emit_render(render())`（def 行与 `__main__` 尾块保持不动）；
  - 删除因此变为未使用的 `import sys`（每个文件 sys 仅剩入口用途，已逐一核验）；
  - import 接入：已有 `_repo` import 的 10 个在名单按字母序加 `emit_render`（置首）；
    executor/source 两个在 `from _md_paths import ...` 之后新增 `from _repo import emit_render`
    （本地 helper 组按 `_md_paths` < `_repo` 排序）。
- 改动后每个文件恰好 1 处 `emit_render(render())`、无 `import sys`、无残留 `sys.stdout.write(text)`。
- `prove_rmw.py`、`run_all_gates.py`、三个下划线 helper（`_repo/_md_paths/_freeze_paths`）不动。

### 行为不变验证（本机 vanilla box，无 ROS）

- **stdout 逐字节**：12 个脚本重构前后各跑一次（均 exit 0；行数 13/16/20/21/23/28/30/31/35/38/73/77），
  12 份 `diff` 全空（all_identical=1）。
- **exit code 透传探针**：直接断言 `emit_render(("MARKER\\n", 7))` 返回 7 且 stdout 恰为 `MARKER\\n`；
  monkeypatch 一个 guard 的 `render` 返回 `("boom\\n", 3)`，调 `main()` 得返回码 3、stdout 恰为 `boom\\n`
  （证明 FAIL 路径的非零码不会被入口吞掉）；健康 guard `main()` 返回 0。
- `python3 -m compileall -q scripts config/env dimos_bridge/dual_chain_env.py` 通过；
  gate **13/13 all gates green**（frozen gate 仍报 scanned 15，未新增第二个 `Path(...)` 源）；
  stdout 指纹 **15/15 stable**（12 个被改脚本都在 15 条命令内，逐字节无漂移、未动 fixtures）；
  #18–#27 十个负向自测全 exit 0；promptfoo **27/27 passed (100%) / 0 failed / 0 errors**
  （eval ID `eval-Y2d-2026-09-20T09:15:54`，UTC；约合 CST 17:15，Duration 2s）。
  本轮不新增 eval 用例（纯入口样板收敛、无新行为；各 guard 的负向能力仍由 #18–#27 覆盖）。
- **合并后回归（main HEAD `2ad01f8`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#27 十个负向自测均 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（eval ID `eval-UOR-2026-09-20T09:22:04`，Duration 2s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未触碰任何 required 循环、
  marker 集合、anchor 常量与 frozen 路径真源（本轮只收敛入口写法）。
- 未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime。
  双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整：脚本命令名、argv、render() 签名、exit code、关键打印短语全部不变
  （stdout 即公共契约，指纹逐字节证明）；`emit_render` 在下划线 helper 模块内，不进 CI 命令枚举。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 极低。入口样板从 12 份收敛为 1 个 helper：stdout 12 份逐字节不变，非零 exit code 透传有探针证明，
  依赖各脚本 render() 的 gate/selftest/promptfoo 全绿。改动消除了 12 份未来可能漂移的入口副本（单一真源），
  且让每个 guard 的 main 成为一眼可读的一行。
- 与轮次 25 一样坚持「先 AST/哈希取证逐字重复、≥2 消费方才下沉、独有逻辑不合并」：本轮明确不动
  形态不同的 `prove_rmw.main` / `run_all_gates.main`，也不碰各 guard 独有、措辞互异的 FAIL 汇总渲染块。
- 真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`（本机无 Humble runtime），不伪造任何通过。

### 下一步（轮次 27 候选）

1. **[《2》续做]** 继续全仓取证下一类真实重复：候选是各 guard 末尾「FAIL 汇总 + ok/SUCCESS 收尾」渲染块、
   以及 `_has_*` / 行解析小工具是否在 ≥2 个脚本**逐字**同构（须先 AST/哈希 + 逐字比对；轮次 23 已判 cega 的
   phrase 检查块形态各异、`_fabricate_hits` 三处正则独有，均不合并——除非出现新的逐字证据）；
   一次一项、行为不变、stdout 逐字节 diff 空、helper 单一真源。
2. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`，之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，先把纯 python 的 fingerprint + #18–#27
   selftest 纳入 CI required checks，再做 §5.3 规则 2 机器化。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。
## 轮次 27 — 2026-09-20 19:12（Asia/Shanghai）《2》小步重构：14 处逐字同构的 failure/warning bullet 渲染循环下沉为 `_repo.append_bullets`

> 定时任务第 27 轮。分支 `refactor/shared-append-bullets`，功能 PR #93（已 squash-merge，main HEAD `30c2652`）。
> 延续轮次 25/26 的全仓重复盘点（先 AST/哈希取证逐字重复、≥2 消费方才下沉、独有逻辑不合并），
> 本轮把 render() 内部一个跨 12 个脚本、出现 14 次、循环体仅一行的纯渲染循环收敛为共享 helper。
> 属 plan §5.3 helper-boundary。行为不变：12 个脚本健康 stdout 逐字节 diff 空、非空列表 bullet 渲染有等价探针 + 十个负向自测覆盖。

### 取证与选题

- re-ground：main 与 origin/main 同步于 `39f3295`（轮次 26 回填 #92），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；`gh pr list` 无本循环在途 PR（开放 PR 全是他人/机器人）。
- 先用 AST 对所有非下划线脚本的**函数体**（去掉 def 签名行后）算 SHA-256：除轮次 26 已下沉、12 脚本共享的
  `main()` 外，**没有任何跨脚本逐字相同的函数体**；同名函数 `_fabricate_hits`（3 个不同 body，正则独有）、
  `render`（13 个全不同，业务核心）维持轮次 23/25 的「不收敛」判定。函数级逐字重复已清零。
- 再逐字打印 12 个 guard 的 render() 收尾块：FAIL 汇总 + healthy 收尾**结构同构但措辞/marker 各异**
  （每个 guard 的 FAIL/healthy prose 独有；SUCCESS_MARKER 粗体行有的有、有的无，dual_chain 还多一个
  PAUSED_MARKER；executor/source/print_bench/risk 无粗体 marker 行），整块下沉需多参数且会抹平 guard 自述，
  判定**不合并**（与轮次 23 对 cega phrase 块的结论一致）。
- 在收尾块内锁定一个真正逐字、纯机械、零断言的片段——把失败/告警列表渲染成 Markdown bullet 的两行循环：
  ```python
          for item in failures:
              lines.append(f"- {item}")
  ```
  严格正则（锚定 8 空格缩进、循环体仅紧跟一行 append）全仓命中 **14 处、跨 12 个脚本、循环变量统一为 `item`**：
  **12 处 `for item in failures`**（11 个 check_* + print_bench_gates，每个 guard 一处）+
  **2 处 `for item in warnings`**（check_executor_map、check_source_map 的「stale 行号仅告警」段）。
  sink_layers 里 `", ".join(f"| **{name}** |" ...)` 等是表格行内 join、形态不同，不计入、不动。

### 改了什么（净 −2 行，+38/−40，13 个文件）

- `scripts/_repo.py`：新增公共 `append_bullets(lines: list[str], items: list[str]) -> None`——原地把每个
  failure/warning 字符串以 Markdown `- ` bullet 追加进渲染缓冲；docstring 明确「只渲染、不含断言，检测与排序仍归调用方」，
  模块顶部 helper 清单加第五项 bullet。无新依赖。
- 12 个脚本：
  - import 行统一为 `from _repo import append_bullets, emit_render[, line_at], repo_root, read_utf8`
    （`append_bullets` 字母序置首；轮次 26 后 12 个脚本都已有 `_repo` import）；
  - 14 处两行循环各自收敛为一行 `append_bullets(lines, failures)` / `append_bullets(lines, warnings)`
    （8 空格缩进不变；executor_map、source_map 各 2 处，其余各 1 处）。
- 替换后全仓 `for item in (failures|warnings)` 零残留；FAIL/healthy prose、SUCCESS/PAUSED marker、
  return code、required 循环、anchor/正则全部不动。

### 行为不变验证（本机 vanilla box，无 ROS）

- **健康 stdout 逐字节**：12 个脚本重构前后各跑一次（均 exit 0），12 份 `diff` 全空（all_identical=1）；
  健康路径 failures/warnings 为空，helper 对空列表是 no-op，输出自然不变。
- **非空列表等价探针**：对 `[]`/单条/多条样本，新 helper 输出与原内联循环逐元素相等；
  断言 in-place 修改且返回 None（`["header"] + ["x","y"] → ["header","- x","- y"]`）。
- **负向渲染由自测覆盖**：#18–#27 十个 guard 负向自测在 tempdir 构造非空 failures（executor/source 还构造
  warnings）并断言渲染出的 bullet 文本，本轮全部 exit 0，证明 FAIL/告警 bullet 行逐字不变。
- `python3 -m compileall -q scripts` 通过；gate **13/13 all gates green**（frozen gate 仍 scanned 15，
  append_bullets 不含 `Path(...)`、未新增路径字面量源）；stdout 指纹 **15/15 stable**（12 个被改脚本都在
  15 条命令内，逐字节无漂移、未动 fixtures）；promptfoo **27/27 passed (100%) / 0 failed / 0 errors**
  （eval ID `eval-vlS-2026-09-20T11:12:02`，UTC；约合 CST 19:12，Duration 2s）。
  本轮不新增 eval 用例（纯渲染循环收敛、无新行为；负向 bullet 渲染仍由 #18–#27 覆盖）。
- **合并后回归（main HEAD `30c2652`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#27 十个负向自测均 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（eval ID `eval-Jdu-2026-09-20T11:22:06`，Duration 2s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未触碰任何 required 循环、
  marker 集合、anchor 常量、FAIL/healthy 措辞与 frozen 路径真源（本轮只把 bullet 渲染循环换成等价 helper 调用）。
- 未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime。
  双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整：脚本命令名、argv、render() 签名、exit code、每一条打印文本全部不变
  （stdout 即公共契约，健康路径指纹逐字节 + 负向路径自测双重证明）；`append_bullets` 在下划线 helper 模块内，
  不进 CI 命令枚举。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 极低。14 份单行渲染循环收敛为 1 个 helper：健康 stdout 12 份逐字节不变，非空 failures/warnings 的 bullet
  输出有等价探针 + #18–#27 负向自测证明，gate/指纹/promptfoo 全绿。改动消除了 14 处未来可能漂移的 bullet
  格式副本（failure/warning 列表的 Markdown 渲染从此单一真源）。
- 继续坚持取证纪律：函数级逐字重复已清零，本轮只动**逐字相同且纯渲染**的循环；render 收尾块虽同构但
  prose/marker 互异，已明确不整块下沉；`_fabricate_hits` 三处正则独有、prove_rmw/run_all_gates.main 形态不同，均不合并。
- 真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`（本机无 Humble runtime），不伪造任何通过。

### 下一步（轮次 28 候选）

1. **[《2》续做]** 函数级与入口/渲染循环级逐字重复均已收敛，继续在 render() 内部找下一类**逐字**片段：候选是
   missing-file 的 `failures.append(...); continue` 守卫块、`lines.append("")` 空行 + `return "\n".join(lines), N`
   尾部（现 27 处 return，但前置 prose/marker/return 码各异，须先逐字取证，独有措辞不强行合并）；
   一次一项、行为不变、stdout 逐字节 diff 空、helper 单一真源。若证不出新的逐字重复，则《2》A 面小步重构
   可视为进入收尾，转为按需维护。
2. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`，之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，先把纯 python 的 fingerprint + #18–#27
   selftest 纳入 CI required checks，再做 §5.3 规则 2 机器化。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

## 轮次 28 — 2026-09-20 20:21（Asia/Shanghai）《2》小步重构：9 处逐字相同的 missing-file 报告守卫块下沉为 `_repo.report_missing_file`

> 定时任务第 28 轮。分支 `refactor/shared-missing-file-report`，功能 PR #95（已 squash-merge，main HEAD `c75cc10`）。
> 延续轮次 25–27「先 AST/正则取证逐字重复、≥2 消费方才下沉、独有措辞不合并」的纪律，本轮把 required 循环里
> 一个跨 9 个 guard、**逐字相同**的缺失文件报告块的两行报告语句收敛为共享 helper；检测（`is_file()`）与
> 控制流（`continue`）仍留在调用方。属 plan §5.3 helper-boundary。行为不变：9 个脚本健康 stdout 逐字节 diff 空、
> FAIL 路径有 monkeypatch 探针 + three_chain/unitree 删文件自测双重证明。

### 取证与选题

- re-ground：main 与 origin/main 同步于 `823a14d`（轮次 27 回填 #94），工作区仅 untracked 受保护旧草稿
  `docs/01-dds-request-flow.md`（未 add/未改）；`gh pr list` 无本循环在途 PR。
- 轮次 27 后函数级、入口（main）、bullet 渲染循环的逐字重复均已清零。本轮按日志候选检查 render() 内的
  missing-file 守卫与尾部 return：尾部 `lines.append("") + return join(lines), N` 前置 prose/marker/return 码互异
  （轮次 27 已判定不整块合并）；missing 守卫里则有一个**逐字相同的 4 行块**。
- 用捕获缩进的严格正则（锚定 `if not path.is_file():` + 两条固定 f-string + `continue`，变量名统一
  path/key/failures/lines）全仓命中 **9 处、缩进统一 8 空格（if）/12 空格（body）**：
  cega L199、dod L180、dual_chain L218、risk_matrix L72、runtime_provenance L119、sink_layers L132、
  three_chain L134、unitree L113、print_bench_gates L66。块体逐字为：
  ```python
          if not path.is_file():
              failures.append(f"missing file `{key}`")
              lines.append(f"- **FAIL missing:** `{key}`")
              continue
  ```
- **明确排除、保持原样**的近邻形态：①cega L301 的 read-only runtime 循环，文案是
  `missing read-only runtime` / `FAIL missing runtime`（独有措辞，不匹配、不下沉）；②print_bench_gates L42
  existence-only 的两行 `if not path.is_file(): continue`（无 failures/lines 报告）；③dual_chain L303/L316 的
  load.py/wrapper 交叉检查，key 是 `LOAD_PY_REL.as_posix()`/`WRAPPER_REL.as_posix()` 且后续不是同一报告块；
  ④executor_map L115 在 `if path.is_file():` **正向**分支内；executor_map/source_map/frozen 无此 4 行块，本轮不动。

### 改了什么（净 +6 行，+33/−27，10 个文件）

- `scripts/_repo.py`：新增公共 `report_missing_file(failures, lines, key) -> None`——原地追加一条
  `missing file `key`` failure 和一行 `- **FAIL missing:** `key`` bullet；docstring 明确「只共享逐字两行报告格式，
  存在性检测 `if not path.is_file()` 与 `continue` 仍归调用方，helper 自身不做任何检测」；模块顶部 helper 清单加第六项。
- 9 个脚本：import 行末尾追加 `report_missing_file`（保持既有名字顺序、最小 diff）；4 行守卫块收敛为 3 行——
  `if not path.is_file():` / `report_missing_file(failures, lines, key)` / `continue`。
- 替换后 gates 内不再有内联的 `failures.append(f"missing file `{key}`")` 逐字副本（残留 3 处均为上面排除的不同形态）；
  FAIL/healthy 其余 prose、SUCCESS/PAUSED marker、required 元组、anchor/正则、return 码全部不动。

### 行为不变验证（本机 vanilla box，无 ROS）

- **健康 stdout 逐字节**：9 个受影响脚本重构前后各跑一次（均 exit 0），9 份 `diff` 全空（all_identical=1）；
  健康路径 required 文件齐全、守卫不触发，输出自然不变。
- **helper 等价探针**：对多个 key，`report_missing_file` 产出的 failures/lines 与原内联两行逐元素相等；
  in-place 修改、返回 None（预置前缀列表验证追加位置正确）。
- **FAIL 路径端到端双重证明**：
  - three_chain 自测（断言 `FAIL missing`，L96）与 unitree 自测（N5 删除 swap doc 后断言 `("FAIL missing",)`，L172）
    直接走本轮改动的守卫块，#18–#27 十个负向自测全部 exit 0；
  - 对自身自测不删文件的 6 个改动 guard（risk_matrix/dod/sink_layers/runtime_provenance/cega/print_bench_gates），
    monkeypatch `pathlib.Path.is_file` 恒为 False 后调 `render(root)`，全部 **exit 1 且输出含逐字的
    `missing file ` 与 `- **FAIL missing:** ` 报告**（dual_chain 的同块为逐字机械替换、由 helper 等价探针 + #19 覆盖）。
- 排除项未误伤：cega runtime 变体文案仍在（grep count 1）、print_bench existence-only 纯 continue 仍在。
- `python3 -m compileall -q scripts` 通过；gate **13/13 all gates green**（frozen gate 仍 scanned 15，
  report_missing_file 不含 `Path(...)`、未新增路径字面量源）；stdout 指纹 **15/15 stable**（9 个被改脚本都在
  15 条命令内，健康输出逐字节无漂移、未动 fixtures）；promptfoo **27/27 passed (100%) / 0 failed / 0 errors**
  （eval ID `eval-b8R-2026-09-20T12:21:02`，UTC；约合 CST 20:21，Duration 2s）。
  本轮不新增 eval 用例（纯报告语句收敛、无新行为；缺失文件负向输出仍由 three_chain/unitree 自测与探针覆盖）。
- **合并后回归（main HEAD `c75cc10`）**：required checks structure / contracts / boundary 全 pass、CodeQL（python/actions/javascript-typescript + 汇总）全 pass、Cursor Approval APPROVED（Cursor Security 非 required，过滤忽略），squash-merge 后回 main 重跑——gate **13/13 all gates green**、指纹 **15/15 stable**、#18–#27 十个负向自测均 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（eval ID `eval-IXV-2026-09-20T12:32:19`，Duration 2s）。
  （合并时 `gh pr merge` 的 API 调用已成功、PR 状态 MERGED，但紧随其后的本地 `git pull` 一度撞 GitHub 443 中断；经网络重试后查询确认 mergeCommit `c75cc10`、再 ff-only 拉取，未重复合并。）

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未触碰 required 元组、marker 集合、
  anchor 常量、其余 FAIL/healthy 措辞与 frozen 路径真源（本轮只把逐字两行报告换成等价 helper 调用，检测与 continue 留在原处）。
- 未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime。
  双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整：脚本命令名、argv、render() 签名、exit code、每一条打印文本全部不变
  （健康路径指纹逐字节 + FAIL 路径探针/自测双重证明）；`report_missing_file` 在下划线 helper 模块内，不进 CI 命令枚举。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险

- 极低。9 份逐字两行缺失报告收敛为 1 个 helper（缺失文件的 failure 文案 + FAIL bullet 单一真源）：健康 stdout 9 份
  逐字节不变，FAIL 路径由删文件自测 + monkeypatch 探针证明 exit 1 且报告逐字正确，gate/指纹/十自测/promptfoo 全绿。
  检测与控制流刻意未下沉，guard 仍各自决定「什么算缺失、缺失后是否 continue」，helper 只统一报告格式。
- 至此《2》A 面（自有 scripts/config/docs）的**函数级、入口、bullet 渲染循环、缺失文件报告**逐字重复均已收敛；
  剩余同构片段都携带独有字面量（各 guard FAIL/healthy prose、`_fabricate_hits` 独有正则、cega runtime 变体、
  dual_chain load.py/wrapper 交叉检查、prove_rmw/run_all_gates.main 形态差异），按既定纪律不强行合并。
- 真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`（本机无 Humble runtime），不伪造任何通过。

### 下一步（轮次 29 候选）

1. **[《2》收尾确认]** 再做一次更宽的语句级（AST 连续语句片段、归一化空白但保留字面量）全仓重复扫描，确认除已下沉的
   line_at / emit_render / append_bullets / report_missing_file 外确实没有新的**逐字**重复；若证不出，则《2》A 面
   小步重构标记为「逐字重复已清零、进入按需维护」，不再为凑改动制造 PR，后续轮次以完整 gate+指纹+#18–#27+promptfoo
   回归为主并在日志标注状态。
2. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`，之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，先把纯 python 的 fingerprint + #18–#27
   selftest 纳入 CI required checks，再做 §5.3 规则 2 机器化。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

## 轮次 29 — 2026-09-20 21:16（Asia/Shanghai）《2》收尾确认扫描 + 12 处逐字 FAIL 汇总段下沉为 `_repo.append_failures_block`

> 定时任务第 29 轮。分支 `refactor/shared-failures-block`，功能 PR **#98**（squash-merge，main `49efee2`，分支功能 commit `53c9695`）；PR 号与合并后回归由 docs-only 回填 PR 补登。
> 本轮先执行轮次 28 计划的《2》收尾确认：对全部非下划线脚本做 AST 连续语句 n-gram（长度 2–3，含 if/for 块内一层）
> **严格逐字**重复扫描（`ast.unparse` 后仅折叠空白、**保留字符串字面量与变量名**，即只认逐字、不认形态同构），
> 再对命中片段按 `_repo` 的 rendering-only 边界逐项处置。最终只下沉一个纯渲染、12 处逐字的 FAIL 汇总段；
> 其余同构片段因含业务判定、属惯用法或与独有 prose 交织，按纪律保留。行为不变：12 个脚本健康 stdout 逐字节 diff 空。

### 收尾扫描结论（严格逐字档，跨 ≥2 文件且有信息量的片段）

- **本轮下沉（纯渲染、12 处逐字）**：每个 guard 收尾的 FAIL 汇总段
  ```python
      if failures:
          lines.append("FAIL:")
          append_bullets(lines, failures)
          lines.append("")
  ```
  在 11 个 check_* + print_bench_gates 共 **12 个文件、每文件恰好 1 处**逐字相同（4 空格 `if failures:`、8 空格 body，
  双引号 `"FAIL:"`/`""`）。块体三行只做渲染（标题 + 每条 failure 一个 bullet + 尾空行），无 guard 独有措辞、无判定。
- **判定保留、不下沉（记录理由，避免后续重复劳动）**：
  - **required-marker 断言块**（`missing_markers = [m for m in markers if m not in text]` + `FAIL markers` + `continue`，
    以及 `ok file` 渲染，6 文件逐字）：这是 guard 的**核心业务判定**（决定缺哪些 marker、是否 FAIL），不是纯渲染；
    且 dod/dual_chain 已在轮次 23/24 因 existence_only 反转而分化、executor/source 走 `_md_paths.check_cited_paths`
    不同路径，只有 6 个同形。把它下沉会让 `_repo` 承载 marker 断言、越过既定 rendering-only 边界；若未来要做，
    必须是带 docs/spec 与一致性检查的**独立机制 PR**，不属小步渲染收敛，本轮不动。
  - **`path = root / rel` / `key = rel.as_posix()`**（10 文件）、**`text = read_utf8(path)` / `texts[rel] = text`**
    （4 文件）：required 循环里的局部数据流与语言惯用法，各一行、无语义封装价值，下沉反而增加间接层，保留。
  - **尾部 `lines.append("") + return "\n".join(lines), 0/1`**：与各 guard 独有的 healthy prose / SUCCESS·PAUSED
    marker 交织，且 early `return ..., 1` 数量不一（executor/source 各 3 个 return），轮次 27 已判定不整块合并，维持。
  - **executor_map/source_map 的 warnings 段**（`Warnings (exit 0 unless a FAIL remains):` + bullets + 空行）：
    标题措辞为这两个 guard 独有，逐字仅 2 处且含专属说明，保留（本轮 grep 确认两处均未被误伤）。
  - **`_fabricate_hits` 里 cega/three_chain 的 prohibition-skip 两行**：走各自私有的 `_PROHIBITION_RE`/`_STATUS_FABRICATE_RE`，
    正则集合独有、被 #24/#27 mutation 锚定，前轮已判定不收敛。
- 结论：经本轮扫描，**rendering/机制级的跨文件逐字重复已基本清零**；剩余同构要么是业务判定（marker 块）、
  要么是惯用法/独有措辞，符合「逐字且纯机制才下沉、独有判定不合并」的既定纪律。

### 改了什么（净 −9 行，+39/−48，13 个文件）

- `scripts/_repo.py`：新增公共 `append_failures_block(lines, failures) -> None`——调用方保留 `if failures:` 守卫，
  非空时追加 `FAIL:` 标题、对每条 failure 调 `append_bullets`、再补一个尾空行；内部复用 `append_bullets`；
  docstring 明确「rendering only、假设 failures 非空（由调用方守卫）、不做判定」；helper 清单加第七项。
- 12 个脚本：import 在 `append_bullets` 后按字母序加 `append_failures_block`；4 行 FAIL 汇总段收敛为 2 行
  （`if failures:` / `append_failures_block(lines, failures)`）。替换后 gates 内不再有内联 `lines.append("FAIL:")`；
  各 guard 的 healthy prose、SUCCESS/PAUSED marker、required 循环、early return、warnings 段全部不动。

### 行为不变验证（本机 vanilla box，无 ROS）

- **健康 stdout 逐字节**：12 个脚本重构前后各跑一次（均 exit 0），12/12 `diff` 空（健康路径 failures 为空、
  `if failures:` 不进入，输出天然不变）。
- **helper 等价探针**：对 1 条/2 条/3 条 failures，`append_failures_block` 产出的行序列与原内联三行逐元素相等
  （`["FAIL:","- p","- q",""]` 精确断言），in-place、返回 None。
- **非空 failures 路径端到端**：#18–#27 十个负向自测全部 exit 0，其中 frozen Case A（bad file→exit 1、引用 bad_gate 行）、
  executor 五个负向场景（exit 1、断言 `FAIL vendored`）、source（exit 1、断言 `FAIL: map missing` 等）均走非空
  failures 的 FAIL 汇总段（即本轮 helper 渲染路径）。另用 monkeypatch 对走 required 循环的 risk_matrix 验证全缺失时
  exit 1 且末尾 `FAIL:\n- ` 汇总块由 helper 正确渲染。
  - 说明：初次用 `is_file` 恒 False 注入 frozen/executor 时探针未得到 exit 1——这是**探针注入方式不当**
    （frozen/executor 是扫描型 guard，文件全缺失并不触发它们的 failure 条件，属既有行为），非本轮改动缺陷；
    这两个 guard 的非空 failures 路径以上述 #18/#21/#22 自测为准（全过）。
- warnings 独有段经 grep 确认 executor/source 各保留 1 处、未被替换。
- `python3 -m compileall -q scripts` 通过；gate **13/13 all gates green**（frozen 仍 scanned 15，helper 无 `Path(...)`、
  未新增路径字面量源）；stdout 指纹 **15/15 stable**（12 个被改脚本都在 15 条命令内、健康输出逐字节无漂移、未动 fixtures）；
  promptfoo **27/27 passed (100%) / 0 failed / 0 errors**（eval ID `eval-Dh9-2026-09-20T13:16:22`，UTC；约合 CST 21:16，
  Duration 2s）。本轮不新增 eval 用例（纯渲染块收敛、无新行为；非空 FAIL 渲染由 #18–#27 覆盖）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未碰 required 元组、marker 集合、
  anchor 常量、SUCCESS/PAUSED marker、warnings 措辞与 frozen 路径真源（本轮只把逐字 FAIL 汇总三行换成等价 helper 调用，
  `if failures:` 条件留在原处）。
- 未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime。
  双链契约不动（A=rmw_fastrtps_cpp/42/config/fastdds.xml，B=Cyclone/0，无自定义 RMW）。
- 无框架迁移/依赖升级/API 变更/架构调整：命令名、argv、render() 签名、exit code、每一条打印文本全部不变
  （健康路径指纹逐字节 + 非空 failures 自测/探针证明）；helper 在下划线模块内，不进 CI 命令枚举。
  required-marker 断言块刻意**未**下沉（守 rendering-only 边界）。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 合并后回归（main `49efee2`，PR #98 squash-merge 后）

- required checks structure/contracts/boundary 全 pass，CodeQL（python/actions/javascript-typescript + aggregate）全 pass，Cursor Approval APPROVED、mergeStateStatus CLEAN；squash-merge 后远端分支已删。
- 回 main 重跑：gate **13/13 all gates green**、stdout 指纹 **15/15 stable**、#18–#27 十自测全 exit 0、promptfoo **27/27 (100%) / 0 failed / 0 errors**（合并后 eval ID `eval-wht-2026-09-20T13:37:58`，UTC，约合 CST 21:37，Duration 2s）。
- 网络备注：push 阶段 GitHub 曾连续 6 次探测返回 000、第 7 次恢复后 push 成功并经 ls-remote 确认；merge 与合并后 pull 一次成功，未重复合并。

### 剩余风险

- 极低。12 份逐字 FAIL 汇总三行收敛为 1 个纯渲染 helper（`FAIL:` 标题/bullet/尾空行单一真源）：健康 stdout 12 份
  逐字节不变，非空 failures 路径由 #18/#21/#22 等负向自测与探针证明 exit 1 且汇总块正确，gate/指纹/十自测/promptfoo 全绿。
  判定条件 `if failures:` 刻意留在各 guard，helper 不决定成败、只统一渲染。
- 《2》A 面（自有 scripts/config/docs）的函数级、入口、bullet 循环、缺失文件报告、FAIL 汇总段等**纯机制/纯渲染逐字重复
  均已收敛**；唯一较大的剩余同构是 required-marker 断言块，但属业务判定，按边界不在小步重构内合并。
- 真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`（本机无 Humble runtime），不伪造任何通过。

### 下一步（轮次 30 候选）

1. **[《2》A 面收尾]** 本轮严格逐字扫描已覆盖函数体与一层嵌套的连续语句；下一轮可补一次「跨函数单行 + 表达式级」扫描做
   最终确认，若 rendering/机制级逐字重复确认为 0，则在重构计划与日志中把《2》阶段 1（死代码/简化/抽 helper/替换陈旧模式
   的 A 面部分）标记为「逐字重复清零、进入按需维护」，此后不为凑改动制造 PR，每轮以完整 gate+指纹+#18–#27+promptfoo
   回归为主并在日志标注状态；required-marker 断言块若要收敛，单独立项（带 docs/spec、独立 PR），不混入小步循环。
2. **[凭证·仍阻塞·最高优先]** 需用户本机 `gh auth refresh -h github.com -s workflow`，之后用离线备份
   `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 补 ci.yml 独立 PR，先把纯 python 的 fingerprint + #18–#27
   selftest 纳入 CI required checks，再做 §5.3 规则 2 机器化。
3. **[需批准]** CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR。
4. **[需授权/环境]** 4 份飞书文档 3380004；提供 Humble Linux 主机解除端到端 pub/sub/p99/跨机 UDP/三链实际复现 blocked。
5. 若上述均不可推进且无新高价值项，下一轮做完整 gate+指纹+#18–#27+promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

## 轮次 30 — 2026-09-20 22:18（Asia/Shanghai）《2》A 面收尾：最终逐字重复扫描确认清零 + 计划状态标记「按需维护」（纯文档轮）

> 定时任务第 30 轮。分支 `docs/refactor-a-side-complete`，单个 docs-only PR（无代码功能 PR，故无回填 PR）。
> 本轮**不改任何代码**：执行轮次 29「下一步」第 1 条——补一次跨函数单行 + 表达式（调用头）级的最终确认扫描，
> 据此在重构计划中把《2》阶段 1 / Step 1–4 的 A 面部分正式标记为「逐字重复清零、进入按需维护」，并做一次完整回归。
> 目的是给《2》A 面一个有证据的收尾结论，而不是为消除重复制造新改动。

### 最终确认扫描（在轮次 29 的连续语句 n-gram 之外，补单行 / 调用头档）

- 方法：对全部非下划线脚本，AST 提取每个函数体（含 if/for/while 的 body/orelse/finalbody 一层嵌套）的
  **每一条语句**与其中的**调用头（callee）**，`ast.unparse` 后仅折叠空白、**保留字符串字面量与变量名**（严格逐字档），
  统计跨文件出现。
- 结论：跨 ≥3 文件的逐字单行语句 21 类、跨 ≥4 文件的逐字调用头 21 类，逐条判定后**没有新的可下沉机制**，全部落入四类：
  1. **已下沉 helper 的调用点**（逐字是预期结果，不是重复问题）：`append_failures_block(lines, failures)`（12 闸）、
     `return emit_render(render())`（12 脚本）、`if not path.is_file(): report_missing_file(...) continue`（9 闸）。
  2. **单行语言惯用法 / 局部数据流**：`lines.append("")`（13）、`failures: list[str] = []`（12）、
     `path = root / rel`（10）、`key = rel.as_posix()`（10）、`text = read_utf8(path)`（6）、`texts[rel] = text`（4）、
     `hits: list[str] = []`（4）等——封装成 helper 只会增加间接层，不下沉。
  3. **业务判定（守 rendering-only 边界，不收敛）**：required-marker 断言块
     （`missing_markers = [m for m in markers if m not in text]` + `FAIL markers` + `continue`，7 闸）与
     `ok file` 渲染（9 闸，含 hint）；dod/dual_chain 已因 existence_only 分化、executor/source 走 `_md_paths`。
     若未来要统一，必须是带 docs/spec 与一致性检查的**独立机制 PR**，不混入小步渲染收敛。
  4. **render 自然终点 / 独有措辞**：尾部 `return "\n".join(lines), 0/1`（12，与各闸独有 prose/SUCCESS·PAUSED marker 交织、
     early return 数量不一，executor/source 各 3 个 return）；executor/source 独有 warnings 标题；
     `_fabricate_hits` 的私有正则（被 #24/#27 mutation 自测锚定）。
- 与轮次 29 结论一致并补强：**函数级、入口、bullet 循环、缺失文件报告、FAIL 汇总段等纯机制/纯渲染的跨文件逐字重复，
  至此全部清零**；A 面无新的高置信度小步重构项。

### 文档改动（仅 2 个 md，0 代码）

- `docs/refactor/02-modernization-plan.md`：在 §3 Step 4 之后新增「Step 1–4 进展状态（A 面，持续更新）」小节，
  逐项登记 Step 1–4 的落地 PR（死代码 #49；冻结路径/第 13 闸 #52；`_md_paths` #50、env 交叉 #51、`_repo` #53 与
  轮次 22/25–29 的 #82/#89/#91/#93/#95/#98；existence_only 反转 #84/#86）、`_repo` 现有 7 个公共函数清单、
  逐字重复最终扫描的四类「不收敛」判定与理由，并明确 A 面 Step 1–4 **进入按需维护**、B/C 面维持 Hold、
  ci.yml 接线仍待 `workflow` scope。
- `docs/refactor/ITERATION_LOG.md`：本小节。
- 不改任何脚本/配置/eval/fixture；不新增 eval 用例（无行为变化）。

### 完整回归（main `784b15f`，纯文档改动前后代码树一致）

- gate **13/13 all gates green**；stdout 指纹 **15/15 stable**；#18–#27 十个负向自测全 exit 0；
  promptfoo **27/27 passed (100%) / 0 failed / 0 errors**（eval ID `eval-uTW-2026-09-20T14:17:26`，UTC，约合 CST 22:17，Duration 2s）。
- 分数无变化（维持 gate 13/13、指纹 15/15、eval 27/27 双百）——本轮是状态收尾而非功能/断言变更。

### Hold 合规

- 纯文档轮：未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字（计划 §1.3 行数表虽已过时，
  但非本轮主题，未顺手改动以免堆叠无关变更）；未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；
  未集成 Cega、未重写 Bridge runtime；双链契约不动；无框架/依赖/API/架构变更。
- 《6》CVE 审计保持只读；promptfoo 仅 npx 缓存运行；受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险与状态

- 《2》A 面（自有 scripts/config/docs）的机械性现代化已收尾，进入按需维护；继续强行抽 helper 的边际收益为负
  （会把业务判定或单行惯用法塞进共享模块、模糊 rendering-only 边界）。
- 仍 blocked / 待拍板（均不得自行突破）：① ci.yml 接线需本机 `gh auth refresh -h github.com -s workflow`
  （active `yixinzhangagent` 缺 workflow scope；优先把纯 python 的 fingerprint + #18–#27 selftest 纳入 CI，先于整套 promptfoo）；
  ② CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆独立 PR；
  ③ 4 份飞书文档 3380004 无权限；④ 无 Humble Linux 主机，真·双链 pub/sub、p99、跨机 UDP、三链实际复现恒 `STATUS: blocked`，不伪造。

### 下一步（轮次 31 候选）

1. 若 `workflow` scope 已授权：用 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 开**独立 PR** 把第 13 闸与
   eval-only 自测接进 CI（先纯 python 项），随后做计划 §5.3 规则 2 的机器化一致性检查。
2. 若用户批准 CVE 修复三项：按 external Cyclone / requirements 锁 / rosdistro key 钉 SHA 拆 3 个独立 PR（不与重构混合）。
3. 若评估侧出现新的真实 DDS 行为薄弱断言：按《5》纪律在 `evals/` 增补对应负向用例（eval-only、纯标准库、tempdir-only）。
4. 若以上均不可推进且无新高价值项：每轮做一次完整 gate+指纹+#18–#27+promptfoo 回归，在日志标注「等待新指令」，
   **不再为凑改动制造提交**。

---

## 轮次 31 — 2026-09-20 23:18（Asia/Shanghai）— eval #28：补 `print_bench_gates` 跨机目录存在性 / STATUS-blocked 正则负向自测（功能 PR #101，squash main `a3f3a30`）

### 背景与取证（为什么不是「等待新指令」）

- re-ground：`git fetch` 一次成功，main 与 origin/main 一致于 `8aeb1db`（轮次 30 纯文档 PR #100 已 squash-merge），无在途 PR，
  工作区仅 untracked 受保护旧草稿 `docs/01-dds-request-flow.md`。合并后完整回归先跑一遍全绿（见下「合并前回归」）。
- 轮次 30 已判定《2》A 面纯机制/纯渲染逐字重复清零、Step 1–4 进入按需维护；本轮在决定「等待」前，对 13 个 gate 中
  **尚无专属负向自测的 3 个**（`prove_rmw`、`print_bench_gates`、`check_risk_matrix`）逐个取证，发现轮次 21「#18–#27 已覆盖
  全部带独有解析器的 guard、原则上停止新增 selftest」的总结有**一个真实遗漏**：
  - `scripts/print_bench_gates.py` 带两项 #18–#27 未覆盖的**独有**检查：① 跨机占位目录
    `docs/artifacts/bench/2026-09-11-cross-host/` 的**存在性分支**（缺失即 `FAIL missing`）；② `_cross_host_hits()` 用独有正则
    `_STATUS_BLOCKED_RE = STATUS:\s*\*?\s*blocked`（IGNORECASE）扫描 5 个候选文件、要求至少一处诚实 `STATUS: blocked`
    （全空即 `FAIL cross-host`）。正向用例 #3 与 #17 指纹只能证明当前健康树为绿，证明不了这两项被放宽后仍会触发。
  - `scripts/prove_rmw.py` 设计上**恒 exit 0**（环境/文件系统事实报告，无 FAIL 分支），不适合「该 fail 时会 fail」型负向自测，
    其诚实性已由 Mac HIL（`docs/testing/2026-09-mac-hil.md`）手动覆盖；
  - `scripts/check_risk_matrix.py` 是直白 marker substring，其 §9.4「order」块复查的 5 个 token 已全部包含在 `_MATRIX_MARKERS`
    元组内、与 marker 断言重叠，并非真正的顺序校验——二者均不另设负向脚本。
- 该遗漏符合《5》既定深化方向（双百之后扩大对**真实 guard 负向能力**的断言覆盖，而非放水），且 eval-only、纯标准库、
  tempdir-only、不依赖任何外部授权，故本轮补为 **#28**（评估深化，不改任何生产脚本）。

### 改动（eval-only，3 个 evals 文件 + 本日志，0 生产代码）

- 新增 `evals/bench_gates_guard_selftest.py`：把 guard 读取的 **4 个真实文件**（SCOREBOARD、bench README、scripts-bench README、
  latency-attribution 方法文档）与**整个真实跨机占位目录**复制进 `tempfile`（SCOREBOARD 只复制、绝不在原地改），驱动可注入的
  `render(root=...)`。断言 **2 negative / 1 non-flag / 2 healthy / 1 mutation**：
  - **N1** 删除跨机占位目录、4 个 required 文件保留 → exit 1、含 `FAIL missing`，且**不连带** `FAIL cross-host` / `FAIL markers`
    （隔离目录存在性分支）；
  - **N2** 把 5 个候选里每一处 `STATUS: blocked` 改写成非 blocked 的 `STATUS: **ready**`（保留 required 所需 `STATUS` 子串），
    `_cross_host_hits` 返回空 → exit 1、含 `FAIL cross-host`，且**不连带** `FAIL markers`（隔离 blocked 正则扫描）；
  - **non-flag** 只保留 `BLOCKED.txt` 一处 blocked、其余 4 个候选改写 → 仍 exit 0 且 hits 恰为 `[BLOCKED.txt]`，钉死
    「任意一个候选命中即可（any-hit）」语义，防止未来被误改成要求每个文件都写 blocked；
  - **healthy** 真实仓 `render()` 与完整复制临时树均 exit 0、含 `Bench gates healthy`（复制树还须含 `cross-host: blocked` 行）；
  - **mutation** 把 `_STATUS_BLOCKED_RE` 放宽为裸 `STATUS`（try/finally 恢复）后 N2 必须**漏报**（exit 0、无 `FAIL cross-host`），
    恢复原正则后重新抓到。
  - 落盘前先在 /tmp 用探针逐字取真实 FAIL 行与各场景 exit code（H2/S1=0、N1=1 only-missing、N2=1 only-cross、mutation 0→1），
    再固化为脚本；直白 required-file/marker substring 循环与 #23 等同形，按惯例不重复堆夹具。
- `evals/promptfooconfig.yaml`：末尾追加 #28 用例（含计数串断言 `2 negative, 1 non-flag, 2 healthy, 1 mutation`），seed 用例 27→28。
- `evals/README.md`：五处登记——配置表 seed 总数 27→28、seed 用例计数叙述补 #28、selftest 文件表加行、用例明细表加 `| 28 |`、
  新增「bench-gates 跨机目录存在性 / STATUS-blocked 正则负向自测（#28）」专节（说明为何这是轮次 21 的遗漏，以及 prove_rmw /
  risk_matrix 为何不补）。`evals/results/BASELINE.md` 是首次 12 用例运行的历史快照，按惯例不改。

### 合并前回归（分支工作区，main `8aeb1db` + 本轮 eval 改动）

- `python3 -m compileall -q evals scripts` 通过；gate **13/13 all gates green**（新脚本不进 `run_all_gates.GATES`、不被 CI
  structure 枚举、无需 ci.yml 接线）；stdout 指纹 **15/15 stable**（新脚本不在 15 个被比对命令内，健康 stdout 零变化）；
  #18–#28 **11 个**负向自测全 exit 0；promptfoo **28/28 passed (100%) / 0 failed / 0 errors**
  （eval ID `eval-fmE-2026-09-20T15:17:51`，UTC，约合 CST 23:17，Duration 3s）。
- 分数变化：gate 13/13 与指纹 15/15 **不变**；promptfoo 27/27 → **28/28**（净增 1 条对真实 guard 负向能力的断言，非放水）；
  guard 负向自测由 10 个增至 **11 个**。

### 合并后回归（main `a3f3a30`，PR #101 squash-merge、远端分支已删）

- 回 main `git pull --ff-only` 至 `a3f3a30` 后重跑：gate **13/13 all gates green**；stdout 指纹 **15/15 stable**；#18–#28 **11 个**负向自测全 exit 0；promptfoo **28/28 passed (100%) / 0 failed / 0 errors**（合并后 eval ID `eval-4eJ-2026-09-20T15:24:28`，UTC，约合 CST 23:24，Duration 3s）。
- 功能 PR **#101**（分支 `test/bench-gates-guard-selftest`，分支 commit `3c6b867`，squash main `a3f3a30`）required checks structure/contracts/boundary 全 pass、CodeQL 三项全 pass、Cursor Approval APPROVED 后合并；非 required 的 Cursor Security Reviewer 为非阻塞项。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 的任何数字或内容（仅在 tempdir **副本**上变异）；
  未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；双链契约不动；
  无框架/依赖/API/架构变更（纯 eval-only 测试新增，公共 API 与生产脚本零改动）。
- 《6》CVE 审计保持只读；promptfoo 仅以 `npx --yes promptfoo@0.123.1` 缓存运行、未写入运行时依赖；
  受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删（commit 前以 `git diff --cached --name-only` 核验）。

### 剩余风险与状态

- 至此 13 个 gate 中，带独有解析器/独有判定分支的 guard 已全部具备负向自测（#18–#28 共 11 个）；仅剩 `prove_rmw`（恒 exit 0，
  不适合）与 `check_risk_matrix`（直白 marker + 与 marker 重叠的 order 块）无脚本，属轮次 21 原则内的合理空缺。后续 eval 深化
  只在出现**新的真实 DDS 行为薄弱断言**时按《5》增补，不为凑数新增。
- 仍 blocked / 待拍板（均不得自行突破）：① ci.yml 接线需本机 `gh auth refresh -h github.com -s workflow`
  （active `yixinzhangagent` 缺 workflow scope；离线备份 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`；授权后优先把纯
  python 的 fingerprint + #18–#28 selftest 纳入 CI，先于整套 promptfoo），再做计划 §5.3 规则 2 机器化；
  ② CVE 修复三项（external Cyclone ≥0.10.5、requirements 补锁、rosdistro key 钉 SHA）待用户明确批准、拆 3 个独立 PR；
  ③ 4 份飞书文档 3380004 无权限；④ 无 Humble Linux 主机，真·双链 pub/sub、p99、跨机 UDP、三链实际复现恒 `STATUS: blocked`，不伪造。

### 下一步（轮次 32 候选）

1. ~~功能 PR 合并后回 main 回归并开 docs-only 回填 PR~~（已完成：功能 PR **#101** / main `a3f3a30` / 合并后 eval `eval-4eJ-2026-09-20T15:24:28`，由本回填 PR 登记）。
2. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #28）接进 CI（先纯 python 项）。
3. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
4. 若以上均不可推进且无新高价值项：每轮做一次完整 gate + 指纹 + #18–#28 + promptfoo 回归，在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 32 — 2026-09-21 00:19（Asia/Shanghai）— eval #29：gate-runner 注册表双向一致性自测（功能 PR TBD）

### 背景与取证（runner 注册面，而非 guard 解析器面）

- re-ground：本地 main=`84cd55c`（轮次 31 回填 PR #102），`gh pr list` 无本循环在途 PR；git smart-http 端点本轮有网络抖动
  （前两次 curl 000 / fetch 超时，第 3 次探测 http=200 后 `git fetch` 成功），确认 origin/main 仍为 `84cd55c`、本地与之一致。
- 凭证复查：active 账号仍为 `yixinzhangagent`（scopes gist/read:org/repo，**仍无 workflow**）；`zhangyinxina-ui` 有 workflow 但非 active、
  不擅自切换——故最高优先的 ci.yml 接线**继续阻塞**，本轮不动 `.github/workflows/`。
- 延续轮次 31「判定等待前先再取证」的纪律，本轮把取证面从「guard 独有解析器」扩到 **runner 注册面**，发现一个新类别缺口
  （与 #18–#28 的 guard 负向自测不同类）：`scripts/run_all_gates.py` 跑绿只证明 **GATES 里已注册的 13 个脚本**存在、exit 0、打印 marker，
  它发现不了**反向漂移——孤儿 gate**：磁盘新增一个 `scripts/check_*.py`（或两个固定名 gate 之一）却忘记加进 `GATES`，头条分数会永远停在
  「13/13」，新 gate 从此不进《3》循环。这与第 13 闸 `check_frozen_path_literals.py` 落地后 CI `structure` 仍只枚举前 12 个 gate 是同一类漏注册。
- 探针（不改动仓库）实测：以唯一发现规则（`scripts/check_*.py` 共 **11** 个 + 固定名 `prove_rmw.py`/`print_bench_gates.py`，
  排除下划线 helper `_repo.py`/`_md_paths.py`/`_freeze_paths.py` 与 runner 自身 `run_all_gates.py`）扫描，磁盘集合与 `run_all_gates.GATES`
  注册集合**双向相等、各 13 个**，missing/orphan 均为空——当前树健康，但没有任何自动化断言钉住它。
- 去重取证：#19 `dual_chain_env_guard_selftest.py` 已用假夹具覆盖「guard 能否检测 load.py import 时写 os.environ」，真实 load.py 的
  import 纯净性由 gate #10 跑绿隐含保证，不重复；现有 28 个 promptfoo 用例无任何 runner 注册/孤儿一致性检查（grep 命中的 run_all_gates
  均为 README 说明文字）。

### 改动（eval-only，3 个 evals 文件 + 本日志，0 生产代码）

- 新增 `evals/gate_registry_selftest.py`（对象是 **runner**、不是某个 guard，故不叫 guard selftest）：内置唯一发现规则
  `discover_gate_scripts()` 与双向比对 `registry_problems(disk, registered) -> (missing, orphan)`，注册集合直接 `import run_all_gates.GATES`
  取 basename（单一真源）。断言 **2 negative / 1 non-flag / 2 healthy / 1 mutation**：
  - **N1 orphan**：tempdir 的 `scripts/` 放 13 个注册 gate + 额外 `check_orphan_gate.py` → 必报 orphan 且不报 missing；
  - **N2 missing**：tempdir 缺 `check_frozen_path_literals.py`（GATES 仍含）→ 必报 missing 且不报 orphan；
  - **non-flag**：磁盘同时放 13 gate + 3 个下划线 helper + `run_all_gates.py` → 发现器必须只返回 13 个 gate、零问题（钉排除规则，防把 helper/runner 误判为孤儿）；
  - **healthy**：真实仓发现集合 == 注册集合、gate 总数钉为 **13**、每个 marker 非空、两个固定名都已注册；tempdir 干净 13 gate 树零问题；
  - **mutation**：把发现器换成「只返回注册表、不扫磁盘」的桩（try/finally 恢复）后 N1 孤儿必须**漏报**，恢复真实发现器后同一孤儿重新被抓到。
- `evals/promptfooconfig.yaml`：末尾追加 #29 用例（含计数串断言），seed 用例 28→**29**。
- `evals/README.md`：配置表 28→29、seed 计数叙述与枚举句补 #29、selftest 文件表加行、明细表加 `| 29 |`、新增「gate-runner 注册表双向
  一致性自测（#29）」专节（倒序置于 #28 专节之前），并写明范围边界：CI structure 仍只枚举 12 个 gate 属 ci.yml 接线、待 workflow scope，本脚本不读 CI yaml、不替它断言。

### 合并前回归（分支工作区，main `84cd55c` + 本轮 eval 改动）

- `python3 -m compileall -q evals scripts` 通过；gate **13/13 all gates green**（新脚本不进 GATES、不被 CI structure 枚举、无需 ci.yml 接线）；
  stdout 指纹 **15/15 stable**（新脚本不在 15 个被比对命令内，健康 stdout 零变化）；#18–#29 **12 个** eval-only 自测全 exit 0；
  promptfoo **29/29 passed (100%) / 0 failed / 0 errors**（合并前 eval ID `eval-ykG-2026-09-20T16:18:30`，UTC，约合 CST 次日 00:18，Duration 4s）。
- 分数变化：gate 13/13 与指纹 15/15 **不变**；promptfoo 28/28 → **29/29**（净增 1 条对 runner 注册完整性的真实断言，非放水）；
  eval-only 自测脚本由 11 个增至 **12 个**（11 个 guard 负向自测 + 1 个 runner 注册一致性自测）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md`；未碰 `.github/workflows/ci.yml`（workflow scope 仍缺，接线保持阻塞）；
  未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；双链契约不动；
  无框架/依赖/API/架构变更（纯 eval-only 测试新增，生产脚本与 `run_all_gates.py` 零改动，仅只读 import 其 GATES）。
- 《6》CVE 审计保持只读；promptfoo 仅以 `npx --yes promptfoo@0.123.1` 缓存运行、未写入运行时依赖；
  受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险与状态

- guard 负向覆盖（#18–#28，11 个带独有解析器/判定分支的 guard）+ runner 注册一致性（#29）均已闭环；`prove_rmw`（恒 exit 0）、
  `check_risk_matrix`（直白 marker、order 块与 marker 元组重叠）维持无脚本的合理空缺。后续 eval 深化只在出现**新的真实行为/注册薄弱断言**时按《5》增补。
- 仍 blocked / 待拍板（均不得自行突破）：① ci.yml 接线需本机 `gh auth refresh -h github.com -s workflow`（active `yixinzhangagent` 缺 scope；
  离线备份 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`；授权后优先把纯 python 的 fingerprint + #18–#29 自测纳入 CI，先于整套 promptfoo，
  并顺手把第 13 闸接进 structure 枚举），再做计划 §5.3 规则 2 机器化；② CVE 修复三项待用户明确批准、拆 3 个独立 PR；
  ③ 4 份飞书文档 3380004 无权限；④ 无 Humble Linux 主机，真·双链 pub/sub、p99、跨机 UDP、三链实际复现恒 `STATUS: blocked`，不伪造。

### 下一步（轮次 33 候选）

1. 本功能 PR 合并后：回 main 跑合并后全套回归，开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。
2. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #29）接进 CI（先纯 python 项）。
3. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
4. 若以上均不可推进且无新高价值项：每轮做一次完整 gate + 指纹 + #18–#29 + promptfoo 回归，在日志标注「等待新指令」，不制造无意义提交。
