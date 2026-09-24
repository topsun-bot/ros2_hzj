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

## 轮次 32 — 2026-09-21 00:19（Asia/Shanghai）— eval #29：gate-runner 注册表双向一致性自测（功能 PR #103，squash main `1be8c35`）

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

### 合并后回归（main `1be8c35`，PR #103 squash-merge 后）

- 回 main `git pull --ff-only` 至 `1be8c35`（mergeCommit `1be8c35dafbdac760572f71515005ae95afb4fbf`，远端分支已删），工作区仅余受保护旧草稿 untracked。
- gate **13/13 all gates green**；stdout 指纹 **15/15 stable**；#18–#29 **12 个** eval-only 自测全 exit 0；
  promptfoo **29/29 passed (100%) / 0 failed / 0 errors**（合并后 eval ID `eval-5Tz-2026-09-20T16:24:49`，UTC，约合 CST 00:24，热缓存 Duration 3s）。
- required checks（structure/contracts/boundary）+ CodeQL（actions/javascript-typescript/python + 聚合）+ Cursor Approval 全 pass，reviewDecision APPROVED、MERGEABLE 后 squash-merge；
  Cursor Security Reviewer 仍 IN_PROGRESS（非 required，历轮一致），mergeStateStatus UNSTABLE 仅因此项。

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

1. ~~本功能 PR 合并后：回 main 跑合并后全套回归，开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ **已完成**：功能 PR #103 squash-merge main `1be8c35`，合并后回归见上（本 docs-only 回填 PR 即此步）。
2. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #29）接进 CI（先纯 python 项）。
3. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
4. 若以上均不可推进且无新高价值项：每轮做一次完整 gate + 指纹 + #18–#29 + promptfoo 回归，在日志标注「等待新指令」，不制造无意义提交。

## 轮次 33 — 2026-09-21 01:18（Asia/Shanghai）— eval #30：gate-runner 执行判定语义负向自测（功能 PR #105，squash-merge main `4a6b79f`）

### re-ground

- 本地 `main` HEAD 与 `origin/main` 引用均为 `d6fbe59`（轮次32 回填 #104 squash）；本轮触发时 GitHub 端点 8 次 `curl` 探测全 `000`、`git fetch` 未刷新（网络抖动），但 #103/#104 是本循环最后的写 main 动作且上轮已 pull 到 `d6fbe59`，push 前网络恢复后再 fetch 复核。
- `gh pr list` 过滤本循环分支（refactor/*、test/*、docs/log*、docs/refactor*、feat/*、fix/*）：**无在途 PR**（open 列表全是 claude/codex/cursor 他人/机器人分支，按惯例不碰）。
- `gh auth status`：active 账号仍为 `yixinzhangagent`（scopes gist/read:org/repo，**无 workflow**）；`zhangyinxina-ui` 含 workflow 但非 active、对本仓历史 403，不擅自切换。ci.yml 接线继续 blocked。
- 工作区仅余受保护旧草稿 `docs/01-dds-request-flow.md` untracked（不 add/不改/不删）。

### 取证：runner 的「执行面」此前零断言

- 延续轮次31/32「决定等待前先取证」纪律。#29（gate_registry）钉的是 runner 的**注册面**——磁盘 gate 集合 ↔ `run_all_gates.GATES` 双向相等；它**从不真正执行任何 gate**，因此保护不了 runner 的**执行面**，即 `scripts/run_all_gates.py` 的 `run_one`/`main` 裁决逻辑：
  - `run_one` 对「exit 0 但没打印健康 marker」返回 `(0, False, …)`，`main` 必须把它计入 `zero-but-missing-marker` 并 FAIL（防 guard 被掏空成 `sys.exit(0)` 空跑、头条仍绿）；
  - 非零退出（即便打印了 marker）必须 FAIL（exit code 优先于 marker）；
  - GATES 指向缺失脚本必须返回 `127, False` 且输出 `missing: <rel>`、`main` FAIL；
  - marker 在 **stderr**（exit 0）须按 stdout+stderr combined 判为存在（防误报，同时不放松 exit 0）。
- 若未来 `main` 退化成「只看退出码、忽略 marker」、`run_one` 恒报 marker 存在、或缺失文件被当通过，13-gate 循环会在 guard 被静默禁用时仍报绿，而 #29 注册一致性测不出来。属 runner 类别、与 #29 互补不重复，是真实负向缺口（非凑数）。
- /tmp 探针在 tempdir 逐字取到真实行为：健康 gate `main` rc=0 绿；exit0-缺-marker `run_one=(0,False)`、`main` rc=1 含 `zero-but-missing-marker: 1`+FAIL；exit1（带 marker）rc=1、`non-zero: 1`+FAIL；缺失文件 rc=127、`missing: scripts/does_not_exist.py`、`main` rc=1；marker 仅在 stderr 时 `(0,True)`、`main` rc=0 绿；把 `run_one` 换成「恒报 marker=True」的桩则 exit0-缺-marker 漏报为 rc=0，恢复真实 `run_one` 后重新 rc=1。

### 改动（纯 eval-only，0 生产代码）

- 新增 `evals/gate_execution_selftest.py`（#30，对象同为 **runner** 而非 guard，命名沿用 `gate_*` 族、无 `_guard` 中缀）：`tempfile` 写假 gate，monkeypatch `run_all_gates.REPO_ROOT`/`GATES`（`contextmanager` + `finally` 恢复），`contextlib.redirect_stdout` 捕获 `main()` 输出，纯标准库、不改仓库。
  - **3 negative**：N1 exit0 缺 marker → `run_one (0,False)`、`main` return 1 + `zero-but-missing-marker: 1` + FAIL；N2 打印 marker 但 `sys.exit(1)` → rc 非 0、`non-zero: 1` + FAIL；N3 GATES 指向不存在脚本 → `run_one` 返回 `127,False` 且含 `missing: <rel>`、`main` FAIL；
  - **1 non-flag**：marker 只打到 stderr、exit 0 → combined 判 `(0,True)`、`main` 绿（钉 stdout+stderr 合并语义）；
  - **1 healthy**：exit0 + stdout marker → `(0,True)`、`main` return 0、`zero-but-missing-marker: 0` + 绿横幅；
  - **1 mutation**：`run_one` 换成恒报 marker 存在的桩（等价于只看退出码的退化）→ N1 空壳 gate 漏报为 `main` return 0；恢复真实 `run_one` 后同场景 return 1（证明缺-marker 检测非空转）。
  - PASS 计数串：`3 negative, 1 non-flag, 1 healthy, 1 mutation`，PASS 短语 `gate runner execution selftest: PASS`。
- `evals/promptfooconfig.yaml`：29 → **30** 用例（末尾追加 #30 块，2 条 contains：PASS 短语 + 计数串）。
- `evals/README.md`：六处登记——配置表「30 个 seed 用例」、seed 叙述「（30 个）」、文件表新增 `gate_execution_selftest.py` 行、seed 枚举句追加 #30、明细表新增 `| 30 | … |`、新增 #30 专节（**倒序置于 #29 专节之前**，含范围边界：不替 CI structure 12/13 缺口断言、不跑真实 gate）。

### 合并前回归（分支工作区，main `d6fbe59` + 本轮 eval 改动）

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py` 通过；gate **13/13 all gates green**（新脚本不进 GATES、不被 CI structure 枚举、无需 ci.yml 接线）；
  stdout 指纹 **15/15 stable**（新脚本不在 15 个被比对命令内，健康 stdout 零变化）；eval-only 自测由 12 个增至 **13 个**（11 guard + gate_registry + gate_execution）全 exit 0；
  promptfoo **30/30 passed (100%) / 0 failed / 0 errors**（合并前 eval ID `eval-d7X-2026-09-20T17:18:09`，UTC，约合 CST 次日 01:18，Duration 4s）。
- 分数变化：gate 13/13 与指纹 15/15 **不变**；promptfoo 29/29 → **30/30**（净增 1 条对 runner 执行裁决语义的真实负向断言，非放水）；eval-only 自测脚本 12 → **13**。

### 合并后回归（main `4a6b79f`，#105 squash-merge 后，2026-09-21 01:40 CST）

- 功能 PR **#105**（分支 `test/gate-runner-execution-selftest`，分支 commit `96b32c6`，4 files +391/−3）required checks **structure / contracts / boundary 全 pass**、CodeQL（Analyze actions/javascript-typescript/python + 聚合）全 pass、Cursor Approval Agent pass、reviewDecision **APPROVED**、MERGEABLE（mergeStateStatus UNSTABLE 仅因非 required 的 Cursor Security Reviewer pending，历轮同），已 `gh pr merge --squash --delete-branch`，mergeCommit **`4a6b79fdf5a85f7aee0a3d8ce969cf95394d3a81`**，远端分支已删。
- 回 main `git pull --ff-only` 到 `4a6b79f`（合并后网络一度持续 000，按重试循环恢复后 ff，未重复 merge；合并事实以 `gh pr view 105 --json state,mergeCommit` = MERGED 为准）。
- main 上全套回归：compile ok；gate **13/13 all gates green**；stdout 指纹 **15/15 stable**；eval-only 自测 **13/13**（11 guard + gate_registry + gate_execution）全 exit 0；promptfoo **30/30 passed (100%) / 0 failed / 0 errors**，合并后 eval ID **`eval-vL5-2026-09-20T17:40:45`**（UTC，约 CST 01:40，Duration 3s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md`；未碰 `.github/workflows/ci.yml`（workflow scope 仍缺，接线保持 blocked）；
  未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；双链契约不动；
  无框架/依赖/API/架构变更（纯 eval-only 测试新增，生产脚本与 `run_all_gates.py` 零改动，仅只读 import 并在 tempdir monkeypatch 后恢复）。
- 《6》CVE 审计保持只读；promptfoo 仅以 `npx --yes promptfoo@0.123.1` 缓存运行、未写入运行时依赖；
  受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险与状态

- runner 双面现已闭环：**注册面**（#29，磁盘↔GATES 双向一致）+ **执行面**（#30，exit0+marker 才过、非零/缺脚本/缺 marker 必 FAIL、stderr combined、变异反证）。
  11 个带独有解析器的 guard 负向自测（#18–#28）此前已闭环；`prove_rmw`（恒 exit 0、无 FAIL 路径，Mac HIL 覆盖）、`check_risk_matrix`（直白 marker substring、§9.4 order 块 5 token 全在 marker 元组内）维持无脚本的合理空缺。
- 仍 blocked / 待拍板（均不得自行突破）：① ci.yml 接线需本机 `gh auth refresh -h github.com -s workflow`（active `yixinzhangagent` 缺 scope；离线备份 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`；授权后优先把纯 python 的 fingerprint + #18–#30 自测纳入 CI、先于整套 promptfoo，并把第 13 闸接进 structure 枚举），再做计划 §5.3 规则 2 机器化；② CVE 修复三项待用户明确批准、拆 3 个独立 PR；③ 4 份飞书文档 3380004 无权限；④ 无 Humble Linux 主机，真·双链 pub/sub、p99、跨机 UDP、三链实际复现恒 `STATUS: blocked`，不伪造。

### 下一步（轮次 34 候选）

1. 已完成：#105 squash-merge main `4a6b79f`，合并后回归 gate 13/13、指纹 15/15、13 selftest、promptfoo 30/30（eval `eval-vL5-2026-09-20T17:40:45`），功能 PR 号 / main HEAD / 合并后 eval ID 已由本 docs-only 回填 PR 补入。
2. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #30）接进 CI（先纯 python 项）。
3. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
4. 若以上均不可推进：再做一次取证扫描（runner/guard/config/docs 是否还有未被任何断言钉住的独有判定分支或注册/契约漂移面，例如 `fingerprint_check.py` 自身的 DRIFT 负向能力是否值得补），确无新高价值项才做完整 gate + 指纹 + #18–#30 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

## 轮次 34 — 2026-09-21 02:14（Asia/Shanghai）— eval #31：stdout 指纹严格层负向自测（功能 PR #108，squash-merge main `7964092`）

### re-ground

- 本地 `main` = `origin/main` = `f8f1d59`（轮次33 回填 #106 squash），`git pull --ff-only` Already up to date；本循环分支（refactor/*、test/*、docs/log*、docs/refactor*、feat/*、fix/*）**无在途 PR**。
- `gh auth status`：active 仍为 `yixinzhangagent`（gist/read:org/repo，**无 workflow**）；`zhangyinxina-ui` 含 workflow 但非 active、对本仓历史 403，不擅自切换。ci.yml 接线继续 blocked。
- 工作区仅余受保护旧草稿 `docs/01-dds-request-flow.md` untracked（不 add/不改/不删）。

### 取证：严格层 #17 此前只有健康断言

- 按轮次33「下一步」第 4 条点名的候选，对 `evals/fingerprint_check.py`（#17，逐字节 stdout 指纹严格层）取证。Promptfoo #17 只断言健康路径打印 `stdout fingerprint: stable`，**没有任何断言证明它该 fail 时真会 fail**。其多个独有判定分支零负向覆盖：
  - live stdout 与 fixture 不符 → `FAIL stdout drift` + `stdout fingerprint: DRIFT (n/N stable)`、rc 1（核心严格层）；
  - 命令 exit 0 但缺 fixture → `FAIL missing fixture`（并提示 `--update`）、rc 1；
  - 命令非零退出（即便有 fixture）→ exit code 优先、`FAIL command exit N`、rc 1；
  - `--update` 遇到失败命令 → stderr `refusing to update fixture for <name>: command exited N`、rc 1 且**不得写** fixture（写路径安全闸）；
  - `normalize` 把绝对仓库路径改写为 `<REPO_ROOT>`（可移植、防假 DRIFT 误报）。
- 若该工具被掏空（比较被旁路、失败命令被容忍、缺/漂移 fixture 仍报绿），gate stdout 里非 marker 的增删行、计数变化、裁决句改写会在 `run_all_gates`（只看退出码+单 marker）与宽松 `contains` 双双报绿时静默通过——三层防线的严格层随之失效。属真实负向缺口，非凑数。
- /tmp 探针（`/tmp/probe_fp.py`）在 tempdir monkeypatch `ROOT`/`FIX_DIR`/`COMMANDS` 逐字取到真实行为：drift rc1 含 `FAIL stdout drift` 与 `DRIFT (0/1 stable)`；缺 fixture rc1 含 `FAIL missing fixture`；非零 rc1 含 `FAIL command exit 1`；`--update` 对 exit1 命令 rc1 且 stderr `refusing to update fixture for bad_gate: command exited 1`、不写文件；路径归一化后 fixture 为 `cwd=/private<REPO_ROOT>`（macOS tempdir 真实前缀 `/private/...`，无原始路径泄漏）、verify rc0；把 `normalize` 换成「恒返回 fixture baseline」的桩则 drift 漏报为 rc0，恢复真实 `normalize` 后重新 rc1 + DRIFT。

### 改动（纯 eval-only，0 生产代码、0 fixture 改动）

- 新增 `evals/fingerprint_guard_selftest.py`（#31，对象是 fingerprint_check 工具本身，沿用 `*_guard_selftest` 族；`contextmanager` 保存/恢复 `ROOT`/`FIX_DIR`/`COMMANDS`，变异在 `try/finally` 内恢复 `normalize`），纯标准库、**不碰真实 `evals/fixtures/`**：
  - **4 negative**：N1 live≠fixture → `FAIL stdout drift`+DRIFT、rc1；N2 健康命令缺 fixture → `FAIL missing fixture`、rc1；N3 命令非零退出 → `FAIL command exit 1`、rc1；N4 `--update` 遇 exit1 命令 → stderr 拒绝、rc1 且不写 fixture；
  - **1 non-flag**：stdout 内嵌绝对仓库路径 → `normalize` 必改写为 `<REPO_ROOT>`、原始路径不泄漏、verify 仍 stable（防假 DRIFT）；
  - **1 healthy**：`--update` 写出归一化 fixture、干净 verify 打印 stable 横幅、rc0；
  - **1 mutation**：`normalize` 盲桩（恒返回 fixture baseline，等价比较被旁路）→ drift 漏报 rc0 stable；恢复后同漂移 rc1 + DRIFT。
  - PASS 计数串 `4 negative, 1 non-flag, 1 healthy, 1 mutation`，PASS 短语 `fingerprint guard selftest: PASS`。
- `evals/promptfooconfig.yaml`：30 → **31** 用例（末尾追加 #31 块，2 条 contains）。
- `evals/README.md`：六处登记——配置表「31 个 seed 用例」、seed 叙述「（31 个）」、文件表新增 `fingerprint_guard_selftest.py` 行、seed 枚举句追加 #31、明细表新增 `| 31 | … |`、新增 #31 专节（**倒序置于 #30 专节之前**，含范围边界：不重新比对 15 份真实 fixture、不替 CI structure 枚举缺口断言）。

### 合并前回归（分支工作区，main `f8f1d59` + 本轮 eval 改动）

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py` 通过；gate **13/13 all gates green**（新脚本不进 GATES、不被 CI structure 枚举、无需 ci.yml 接线）；
  stdout 指纹 **15/15 stable**（新脚本不跑任何被比对命令、不改 fixture，健康 stdout 零变化）；eval-only 自测由 13 个增至 **14 个**（11 guard + gate_registry + gate_execution + fingerprint_guard）全 exit 0；
  promptfoo **31/31 passed (100%) / 0 failed / 0 errors**（合并前 eval ID `eval-lUy-2026-09-20T18:14:09`，UTC，约合 CST 次日 02:14，Duration 4s）。
- 分数变化：gate 13/13 与指纹 15/15 **不变**；promptfoo 30/30 → **31/31**（净增 1 条对严格层工具自身负向能力的真实断言，非放水）；eval-only 自测脚本 13 → **14**。

### 合并后回归（main `7964092`，2026-09-21 02:27 CST）

- 功能 PR **#108**（分支 `test/fingerprint-guard-selftest`，分支 commit `687be7d`，4 files +306/−3）required checks（structure/contracts/boundary）+ CodeQL（actions/javascript-typescript/python + 聚合）全 pass、Cursor Approval **APPROVED**、MERGEABLE，squash-merge 到 main **`7964092`**（mergeCommit `7964092ff67df52de07807ccbfb99a3b51372ae2`，mergedAt 2026-09-20T18:19:23Z），远端分支已删。
- 回 main `git pull --ff-only` 到 `7964092` 后重跑：compile ok；gate **13/13 all gates green**；stdout 指纹 **15/15 stable**；eval-only 自测 **14/14**（#18–#31）exit 0；promptfoo **31/31 passed (100%) / 0 failed / 0 errors**（合并后 eval ID `eval-qZf-2026-09-20T18:27:03`，Duration 5s）。
- 合并前 eval `eval-lUy-2026-09-20T18:14:09`、合并后 eval `eval-qZf-2026-09-20T18:27:03` 均 31/31，结论一致。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md`；**未改任何 `evals/fixtures/*.txt`**（负向场景全在 tempdir 副本）；未碰 `.github/workflows/ci.yml`（workflow scope 仍缺）；
  未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；双链契约不动；
  无框架/依赖/API/架构变更（纯 eval-only 测试新增，生产脚本与 `fingerprint_check.py` 零改动，仅只读 import 并在 tempdir monkeypatch 后恢复）。
- 《6》CVE 审计保持只读；promptfoo 仅以 `npx --yes promptfoo@0.123.1` 缓存运行、未写入运行时依赖；
  受保护旧草稿 `docs/01-dds-request-flow.md` 全程 untracked、未 add/未改/未删。

### 剩余风险与状态

- 负向自测覆盖现状：11 个带独有解析器的 guard（#18–#28）+ runner 双面（注册 #29 / 执行 #30）+ 严格层指纹工具（#31）均已闭环「该 fail 时真会 fail」；`prove_rmw`（恒 exit 0、无 FAIL 路径，Mac HIL 覆盖）、`check_risk_matrix`（直白 marker substring、§9.4 order 块 token 全在 marker 元组内）维持无脚本的合理空缺。
- 仍 blocked / 待拍板（均不得自行突破）：① ci.yml 接线需本机 `gh auth refresh -h github.com -s workflow`（active `yixinzhangagent` 缺 scope；离线备份 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`；授权后优先把纯 python 的 fingerprint + #18–#31 自测纳入 CI、先于整套 promptfoo，并把第 13 闸接进 structure 枚举），再做计划 §5.3 规则 2 机器化；② CVE 修复三项待用户明确批准、拆 3 个独立 PR；③ 4 份飞书文档 3380004 无权限；④ 无 Humble Linux 主机，真·双链 pub/sub、p99、跨机 UDP、三链实际复现恒 `STATUS: blocked`，不伪造。

### 下一步（轮次 35 候选）

1. ~~本功能 PR 合并后：回 main 跑合并后全套回归，开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ 已完成：功能 PR #108 squash main `7964092`，合并后 31/31（eval `eval-qZf-2026-09-20T18:27:03`），由本回填 PR 收尾。
2. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #31）接进 CI（先纯 python 项）。
3. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
4. 若以上均不可推进：再做一次取证扫描（localScriptProvider.mjs provider 自身、config/env 薄包装、docs 契约链接同构检查等是否还有未被任何断言钉住的独有判定/漂移面），确无新高价值项才做完整 gate + 指纹 + #18–#31 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 35 — 2026-09-21 03:23（Asia/Shanghai）— eval #32：双链环境真源 load.py 契约/负向自测（功能 PR #111，squash-merge main `61bc10d`）

**re-ground**：main=`2d1d120`=origin/main（轮次34 回填 #109 已合），工作区仅受保护旧草稿 `docs/01-dds-request-flow.md` untracked；本循环无在途 PR；active gh 账号 `yixinzhangagent` 仍仅 gist/read:org/repo（无 workflow）。GitHub 网络间歇 curl 000/HTTP2 framing 抖动，本地 main 已与 origin 一致，不阻塞本地开发与热缓存回归。

**取证（先探针、后新增）**：按轮次34「下一步」第4条做取证扫描，读两个候选——
- 候选 A `evals/localScriptProvider.mjs`（备查，本轮未选）：node ESM，硬编码 `execFileSync('python3', argv)`，独有分支（空 prompt→error、非零退出→error 透传）零断言，但无法用 python3 provider 直接跑 .mjs 自测，需 python subprocess 包 node 或 promptfoo expected-error 机制，集成别扭，留待后续轮次。
- 候选 B `config/env/load.py`（**选定为 #32**）：双链 env 唯一真源。#19（`dual_chain_env_guard_selftest.py`）只钉 guard `check_dual_chain_env.py` 检测假 shell 夹具的能力，**从不钉 load.py 真源自身**；Mac HIL 里 print/import 纯净只是文档叙述、非可执行回归。`/tmp/probe_load.py` 逐字取全行为：`describe('a'/'b')` 返回精确契约 dict（A=rmw_fastrtps_cpp/42/fastdds.xml 绝对路径，B=rmw_cyclonedds_cpp/0）、未知 chain 抛 `ValueError: unknown chain: z`；`apply(CHAIN_B, unset=('CYCLONEDDS_URI',))` 写入 cyclone/0 并 **pop 掉预置 CYCLONEDDS_URI**、不带 FastDDS profiles；`export_shell` 单引号转义 `_sh_single("a'b")`=`'a'"'"'b'`；CLI print/export/apply 六子命令全 rc0、非法子命令 argparse **rc2**；全新解释器 import load 前后 `os.environ` 完全一致（PURE）。

**改动（纯 eval-only，0 生产代码 / 0 fixture / 0 ci.yml）**：新增 `evals/dual_chain_env_load_selftest.py`（**eval #32**，对象是 env 真源工具本身、区别于 #19 的 guard；纯标准库、不编辑仓库：进程内 `apply` 用 `_EnvSnapshot` 在退出时恢复 `os.environ` 与函数本身，CLI/import 纯净走隔离子进程），共 **3 negative / 2 non-flag / 1 healthy / 1 mutation**：
- N1 `describe('z')` 必抛 `ValueError: unknown chain: z`（未知链不得静默返回空/错配置）；N2 未知 CLI 子命令必 argparse **exit 2**；N3 Chain B `apply` 必须 **pop 预置的 CYCLONEDDS_URI**（跳过 unset 会让外部 Cyclone URI 污染 Chain B），且 B 不带 FastDDS profiles 文件；
- non-flag1 `export_shell` 对 `a'b c` 必输出 `'a'"'"'b c'` 且 `/bin/sh -c` eval 回读原样 round-trip（防错误/不可解析 export）；non-flag2 全新解释器 `import load` 前后 env 完全一致（import 纯净、不得隐式 apply）；
- healthy：`describe` 精确契约 dict（fastdds.xml 绝对路径且文件存在）+ 六子命令全 rc0 且含关键契约串；
- mutation：把 `apply` 换成「只 `os.environ.update`、不做 unset pop」盲桩 → Chain B 下 CYCLONEDDS_URI 泄漏（断言观察到泄漏以自检），恢复真实 `apply` 后删除。
- 登记：`promptfooconfig.yaml` 31→32（2 contains：PASS 短语 + 计数串）；`evals/README.md` 六处（配置表/seed 叙述/文件表/枚举句/明细表 `| 32 |`/倒序 #32 专节置于 #31 专节前），445→458 行。

**合并前回归（main 2d1d120，2026-09-21 03:23 CST）**：`compileall`（evals/scripts/config/env/薄包装）通过；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；eval-only 自测 **15 个全 PASS**（14 个 #18–#31 + 新 `dual_chain_env_load`，fail=0）；promptfoo **32/32 passed (100%)、0 failed、0 errors**（合并前 eval `eval-we2-2026-09-20T19:23:08`，Duration 6s）。

**合并后回归（main 61bc10d，2026-09-21 03:29 CST）**：功能 PR #111 squash-merge 后回 main 复跑——`compileall` 通过；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；eval-only 自测 **15 个全 PASS**（fail=0）；promptfoo **32/32 passed (100%)、0 failed、0 errors**（合并后 eval `eval-qfs-2026-09-20T19:29:05`）。

**Hold 合规**：未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未启用 Agnocast/zenoh（无 vendor 树/kmod/rmw_zenoh）；未改 `dimos_bridge` DDS 行为与 vendor 源码、未集成 Cega/重写 Bridge；未改 shell 包装 `chain_a.sh`/`chain_b.sh`（其字面 export 串仍由 #19 guard 锚定）；无框架迁移/依赖升级/API 变更/架构调整；CVE 审计保持只读；promptfoo 仅 npx 缓存运行、未写入运行时依赖；受保护旧草稿未跟踪未改。

### 剩余风险与状态

- 负向自测覆盖现状：11 个带独有解析器的 guard（#18–#28）+ runner 双面（#29/#30）+ 严格层指纹工具（#31）+ **双链 env 真源 load.py（#32）** 均已闭环「该 fail 时真会 fail / 该纯时不污染」；`prove_rmw`（恒 exit0）、`check_risk_matrix`（marker/order 重叠）维持无脚本的合理空缺。
- 仍 blocked / 待拍板（均不得自行突破）：① ci.yml 接线需本机 `gh auth refresh -h github.com -s workflow`（active `yixinzhangagent` 缺 scope；离线备份 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak`；授权后优先把纯 python 的 fingerprint + #18–#32 自测纳入 CI、先于整套 promptfoo，并把第 13 闸接进 structure 枚举）；② CVE 修复三项待用户明确批准、拆 3 个独立 PR；③ 4 份飞书文档 3380004 无权限；④ 无 Humble Linux 主机，真·双链 pub/sub、p99、跨机 UDP、三链实际复现恒 `STATUS: blocked`，不伪造。

### 下一步（轮次 36 候选）

1. ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 32/32），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ 已完成：功能 PR #111 squash main `61bc10d`，合并后 32/32（eval `eval-qfs-2026-09-20T19:29:05`），由本回填 PR 收尾。
2. 候选 A `localScriptProvider.mjs` provider 自身（空 prompt error、非零退出 error 透传——这是 #18–#32 全部负向 eval「exit1→case fail」的根基）：先探针取证并确认集成可行（python subprocess 调 `node -e`/临时 .mjs，或研究 promptfoo expected-error 用例写法），可行再做，不为凑数硬上。
3. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #32）接进 CI（先纯 python 项）。
4. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
5. 若以上均不可推进且确无新高价值项：做完整 gate + 指纹 + #18–#32 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 36 — 2026-09-21 04:22（Asia/Shanghai）— eval #33：local-script provider 自身契约/负向自测（功能 PR #114，squash-merge main `cb91e1e`）

### 背景与取证（先探针、后写脚本）

- re-ground：`main`=`c85c35f`=origin/main（轮次35 回填 #112 后），工作区干净，仅受保护旧草稿 `docs/01-dds-request-flow.md` untracked（未碰）；本循环无在途 PR；node **v22.23.2** 在 PATH（promptfoo 本身依赖 node）。
- 按轮次35「下一步」第 2 条取证 **`evals/localScriptProvider.mjs`（promptfoo custom provider 自身）**。它是 #12–#32 全部用例的执行器：把 prompt 按空白拆成 argv 用 `python3` 跑（cwd=repoRoot、timeout 30s），exit 0 返回 stdout 作为 `output`，**exit 非 0 才设置 `error`**——#18–#32 负向自测脚本内部 exit 1 能否在 promptfoo 里真标红，完全依赖这条「非零→error」透传；但此前 provider 自身零可执行回归。若它被掏空（空 prompt 静默成功 / 非零退出被吞 / 缺失脚本当成功 / 成功路径 stderr 混入 output 污染 contains 与指纹），整套负向 eval 可能在仍显绿时失去判别力。
- `/tmp/probe_provider.mjs`（node harness，经 `file://` import 真实 provider）逐字取全行为：①`id()='local-script'`；②空 prompt `''` → error `local-script: empty prompt (expected a script path, optionally with args)`、output 空串；③纯空白 `'   \t '`（trim→split→filter 后空）→ 同一 empty error；④`config/env/load.py print-a` exit 0 → 无 error、output 为 Chain A 三行 stdout（证明 argv 空白拆分传参与 cwd=repoRoot）；⑤临时 fail.py（stdout `OUT-LEAD`、stderr `ERR-DETAIL`、exit 1）→ error 含 `exited with code 1`、output=`OUT-LEAD`+空行+`ERR-DETAIL`（stdout 与 stderr 都透传）；⑥缺失脚本 → python3 自身 exit 2（`can't open file ... No such file`，非 node ENOENT）、error 含 `exited with code 2`；⑦exit 0 但写 stderr 的脚本 → 无 error、output **只含 stdout**（stderr 不入 output）；⑧内联「盲 provider」（catch 不返回 error）跑同一 fail.py → hasError=false（漏报），证明变异检查能区分「吞非零退出」。

### 改动（纯 eval-only，0 生产代码 / 0 fixture / 0 ci.yml）

- 新增 `evals/local_script_provider_selftest.py`（**eval #33**，对象是 **provider .mjs 执行器本身**；provider 硬编码 python3、无法被 python3 provider 直接执行，故 python 主体在 tempdir 写一个 Node harness，经 `file://` URL import 真实 provider、再跑 tempdir 内一次性 python 夹具，结果以 `__JSON_BEGIN__/END__` 哨兵包裹的 JSON 回传断言；不在树内建 fixture、不编辑仓库；纯标准库；需要 `node`，缺失即 FAIL——promptfoo 本身也依赖 node）。场景 **3 negative / 2 non-flag / 1 healthy / 1 mutation**：
  - N1 空 prompt 必 error（`empty prompt`）且 output 为空串；N2 exit 1 必 error 含 `exited with code 1` 且 output 同时含 stdout（`OUT-LEAD`）与 stderr（`ERR-DETAIL`）；N3 缺失脚本（python3 exit 2）必 error 含 `exited with code 2`，不得静默成功；
  - non-flag1 纯空白 prompt 同样命中 empty error（不得靠空白绕过）；non-flag2 exit 0 但写 stderr 必无 error、output 含 `CLEAN-OUT` 且**不含** `NOISE-STDERR`（成功路径 output 严格=stdout，防 stderr 污染 contains/指纹）；
  - healthy：`id()=='local-script'` 且 `load.py print-a` exit 0、无 error、stdout 含 `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` 与 `ROS_DOMAIN_ID=42`（argv 拆分 + cwd）；
  - mutation：盲 provider（catch 不返回 error）对 exit 1 夹具漏报（hasError=false，sanity），真实 provider 对同一夹具报 error——证明本测试能抓住「吞非零退出」退化。
- `evals/promptfooconfig.yaml`：32→**33**，末尾追加 #33 块（2 条 contains：`local-script provider selftest: PASS` + 计数串）。
- `evals/README.md`：六处登记（配置表/seed 叙述 33、文件表新增 provider 自测行、枚举句追加 #33、明细表 `| 33 |`、倒序新增 #33 专节置于 #32 专节之前），458→471 行。

### 合并前回归（分支，2026-09-21 04:21 CST）

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py`：通过；
- `python3 scripts/run_all_gates.py`：**13/13**，`run_all_gates: all gates green`；
- `python3 evals/fingerprint_check.py`：**15/15 stable**（未改任何被指纹命令的 stdout）；
- eval-only 自测：**16 个全 PASS**（fail=0，含新增 `local_script_provider_selftest.py`，本地见 7 个 `  ok ...` + PASS + 计数串）；
- promptfoo：**33/33 passed (100%)、0 failed、0 errors**（合并前 eval `eval-wzt-2026-09-20T20:21:55`，Duration 14s）。

**合并后回归（main cb91e1e，2026-09-21 04:32 CST）**：功能 PR #114 squash-merge 后回 main 复跑——`compileall` 通过；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；eval-only 自测 **16 个全 PASS**（fail=0）；promptfoo **33/33 passed (100%)、0 failed、0 errors**（合并后 eval `eval-cMD-2026-09-20T20:32:38`，Duration 13s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未启用 Agnocast/zenoh（无 vendor 树/kmod/rmw_zenoh）；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；未改 shell 包装 `chain_a.sh`/`chain_b.sh`；无框架迁移/依赖升级/API 变更/架构调整（仅新增一个 eval-only 自测 + 登记）。
- 负向自测一律 tempdir 一次性 Node harness / python 夹具，不在原地改任何文件；node harness 是临时文件、不进仓库、不新增 node 依赖（仓库只新增一个 .py）；promptfoo 仍仅 npx 缓存运行、未写入运行时依赖。
- 《6》CVE 审计保持只读，未安装/构建/执行被审计依赖。
- 受保护旧草稿 `docs/01-dds-request-flow.md`（untracked）未删除/覆盖/提交。

### 剩余风险与缺口

- 本机无 ROS Humble runtime：真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`，未伪造。
- 第 13 闸 `check_frozen_path_literals.py` 与全部 eval-only 自测（含 #33）仍未接 CI structure 枚举（active 账号缺 `workflow` scope，离线备份 `~/ros2_hzj_pending/ci.yml.iter4-with-frozen-gate.bak` 待用）。
- provider 的 30s timeout 分支未单独构造（需慢夹具，价值低、易拖慢 eval）；#33 已钉住空/空白/非零/缺失/成功 stdout-only/argv 拆分/盲变异等真实独有分支。
- 《6》CVE 修复三项仍待用户明确批准、拆独立 PR；4 份飞书文档仍 3380004 无权限。

### 下一步

1. ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 33/33），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ 已完成：功能 PR #114 squash main `cb91e1e`，合并后 33/33（eval `eval-cMD-2026-09-20T20:32:38`），由本回填 PR 收尾。
2. 取证薄包装 `dimos_bridge/dual_chain_env.py`（importlib 二次导出 load.py）与真源的一致性是否已有断言（#32 钉了 load.py 本体，薄包装的「声明唯一真源 + 再导出」面可能仍零断言）；先 /tmp 探针确认真实未覆盖的独有分支再决定是否新增，不为凑数。
3. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #33）接进 CI（先纯 python 项；#33 依赖 node，CI 已有 node 但应排在纯 python 项之后）。
4. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
5. 若以上均不可推进且确无新高价值项：做完整 gate + 指纹 + #18–#33 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 37 — 2026-09-21 05:16（Asia/Shanghai）— eval #34：双链环境薄包装 dual_chain_env.py 再导出/委托契约负向自测（功能 PR #116，squash-merge main `b18c789`）

### 背景与取证（先探针、后写脚本）

- re-ground：`main`=`4cd1781`=origin/main（轮次36 回填 #115 后），工作区干净，仅受保护旧草稿 `docs/01-dds-request-flow.md` untracked（未碰）；本循环无在途 PR。
- 按轮次36「下一步」第 2 条取证 **`dimos_bridge/dual_chain_env.py`（DimOS 侧薄包装，48 行）**。它 docstring 声明 `config/env/load.py` 是唯一可执行真源、只做 importlib 重新导出、不得复制常量；模块级再导出 `CHAIN_A/CHAIN_B`，`chain_a_env()/chain_b_env()` 委托 `describe`，`apply_chain_a()/apply_chain_b()` 委托 `apply`（Chain B 传 `unset=CHAIN_B_UNSET`）。#32 钉了 load.py 本体、#19 钉了读 shell 字面 export 的 guard，但**中间这层薄包装零断言**：复制常量会与真源漂移、`apply_chain_b` 漏传 unset 会让外部 `CYCLONEDDS_URI` 污染 Chain B、import 包装可能误写 `os.environ`、真源缺失可能被静默吞掉。
- `/tmp/probe_wrapper.py`、`/tmp/probe_wrapper2.py` 逐字取证（关键修正：外部用第二个 spec 另载 load 时 `w.CHAIN_A is load.CHAIN_A` 为 False 是两份模块实例所致，同一性必须比对包装内部 `w._env.CHAIN_A`）：①`w.CHAIN_A is w._env.CHAIN_A`、`w.CHAIN_B is w._env.CHAIN_B` 均 **True**（重导出同一对象、非复制）；②`chain_a_env()==_env.CHAIN_A` 为 True，但 `describe` 每次返回 **fresh dict**（既非常量本体、两次调用也不同对象）；③`__all__` 恰为 6 名；④`_ENV_PY` 解析到仓库 `config/env/load.py` 且存在；⑤预置 `CYCLONEDDS_URI` 后 `apply_chain_b()` 删除它并置 RMW=Cyclone/DOMAIN=0；盲委托 `load.apply(CHAIN_B)` 不传 unset 则 URI **泄漏**（mutation 成立）；⑥`apply_chain_a()` 置 fastrtps/42/fastdds.xml；⑦隔离子进程 import 包装不改四个 env 键（纯净）；⑧与包装同构但 load.py 指向不存在文件的 tempdir 模块 import rc1、抛 `FileNotFoundError`（spec 非 None，在 exec_module 阶段失败，非静默）。

### 改动（纯 eval-only，0 生产代码 / 0 fixture / 0 ci.yml）

- 新增 `evals/dual_chain_env_wrapper_selftest.py`（**eval #34**，对象是**薄包装层**，中缀 `dual_chain_env_wrapper` 区别于 #19 `dual_chain_env_guard` 与 #32 `dual_chain_env_load`；纯标准库；进程内 `apply_*` 用 `_EnvSnapshot` 始终恢复，import 纯净/缺源失败走隔离子进程，坏包装夹具写 tempdir、不在树内建文件）。场景 **3 negative / 2 non-flag / 1 healthy / 1 mutation**：
  - N1 隔离子进程 import 包装前后 `RMW_IMPLEMENTATION/ROS_DOMAIN_ID/FASTRTPS_DEFAULT_PROFILES_FILE/CYCLONEDDS_URI` 无变化（模块级纯净）；N2 预置 `CYCLONEDDS_URI` 后 `apply_chain_b()` 必删除（unset 必须转发）且置 Cyclone/0；N3 load.py 缺失的同构包装 import 必非零失败（FileNotFoundError），不得静默；
  - non-flag1 `apply_chain_a()` 置 Chain A 三元组；non-flag2 `chain_a_env()` 返回 fresh dict（非常量本体、两次不同对象）但值等于常量，调用方 mutate 污染不到源；
  - healthy：`CHAIN_A/B is _env.CHAIN_A/B`（同一对象、非复制）、`chain_*_env()` 委托值一致、`_ENV_PY` 指向仓库 load.py 且存在、`__all__` 恰 6 名；
  - mutation：盲委托 `apply(CHAIN_B)` 不传 unset 泄漏预置 URI（sanity），真实 `apply_chain_b()` 删除（对照）。
- `evals/promptfooconfig.yaml`：33→**34**，末尾追加 #34 块（2 条 contains：`dual-chain env wrapper selftest: PASS` + 计数串）。
- `evals/README.md`：六处登记（配置表/seed 叙述 34、文件表新增包装自测行、枚举句追加 #34、明细表 `| 34 |`、倒序新增 #34 专节置于 #33 专节之前），471→484 行。

### 合并前回归（分支，2026-09-21 05:15 CST）

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py`：通过；
- `python3 scripts/run_all_gates.py`：**13/13**，`run_all_gates: all gates green`；
- `python3 evals/fingerprint_check.py`：**15/15 stable**（未改任何被指纹命令的 stdout；未改包装/load.py 行为）；
- eval-only 自测：**17 个全 PASS**（fail=0，新增 `dual_chain_env_wrapper_selftest.py` 本地 7 个 `  ok ...` + PASS + 计数串）；
- promptfoo：**34/34 passed (100%)、0 failed、0 errors**（合并前 eval `eval-nA9-2026-09-20T21:15:32`，Duration 23s）。

### 合并后回归（main b18c789，2026-09-21 05:26 CST）

功能 PR #116 squash-merge 到 main `b18c789`（mergeCommit `b18c78907476b8a04584638d0fb5d431b13b9f80`，mergedAt 2026-09-20T21:21:40Z；merge 命令首次撞 `expected flush after ref listing` 网断，API 确认 MERGED 未重复 merge，本地随后 ff）。回 main 全量回归：

- `python3 scripts/run_all_gates.py`：**13/13**，`run_all_gates: all gates green`；
- `python3 evals/fingerprint_check.py`：**15/15 stdout fingerprint: stable**；
- eval-only 自测：**17 个全 PASS**（fail=0）；
- promptfoo：**34/34 passed (100%)、0 failed、0 errors**（合并后 eval `eval-M3V-2026-09-20T21:26:21`，Duration 26s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未启用 Agnocast/zenoh；未改 `dimos_bridge` 的 DDS 行为与 vendor 源码（本项**只读 import 薄包装做断言、未改其一行**）；未集成 Cega、未重写 Bridge runtime；未改 shell 包装 `chain_a.sh`/`chain_b.sh`；无框架迁移/依赖升级/API 变更/架构调整（仅新增一个 eval-only 自测 + 登记）。
- 负向自测一律 tempdir 同构坏包装 / 隔离子进程 / env 快照，不在原地改任何文件；不新增依赖。
- 《6》CVE 审计保持只读；受保护旧草稿 `docs/01-dds-request-flow.md`（untracked）未删除/覆盖/提交。

### 剩余风险与缺口

- 本机无 ROS Humble runtime：真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`，未伪造。
- 第 13 闸与全部 eval-only 自测（含 #34）仍未接 CI structure 枚举（active 账号缺 `workflow` scope）。
- 薄包装 `spec is None → ImportError` 分支在正常文件系统下不可达（spec_from_file_location 对存在/不存在路径都返回非 None），#34 以「缺源 exec 必失败（FileNotFoundError）」钉住可观测防线，未强行构造 None。
- 《6》CVE 修复三项仍待用户明确批准、拆独立 PR；4 份飞书文档仍 3380004 无权限。

### 下一步

1. [x] 功能 PR #116 已 squash-merge（main `b18c789`），合并后回归 34/34（合并后 eval `eval-M3V-2026-09-20T21:26:21`），本回填 PR 即补 PR 号 / main HEAD / eval ID。
2. env 链路三层（shell guard #19、真源 load.py #32、薄包装 #34）已闭环；再取证是否还有未钉的真实独有判定面（如 docs 契约链接同构检查、或其余 A 面脚本的负向分支），**先 /tmp 探针确认真实未覆盖再新增，不为凑数**。
3. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #34，纯 python）接进 CI。
4. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
5. 若以上均不可推进且确无新高价值项：做完整 gate + 指纹 + #18–#34 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 38 — 2026-09-21 06:19（Asia/Shanghai）— eval #35：Promptfoo eval 套件自身注册面一致性自测（功能 PR #118，squash-merge main `1ae11ca`）

### 背景与取证（先探针、后写脚本）

- re-ground：`main`=`9a81899`=origin/main（轮次37 回填 #117 后），工作区干净，仅受保护旧草稿 `docs/01-dds-request-flow.md` untracked（未碰）；本循环无在途 PR。
- env 链路三层（shell guard #19、真源 load.py #32、薄包装 #34）已闭环。本轮按「下一步」取证是否还有真实未覆盖的独有判定面，发现与 #29 **对称的 eval 侧注册面缺口**：#29（`gate_registry_selftest.py`）钉的是 gate runner 注册面（磁盘 gate 脚本 ↔ `run_all_gates.GATES` 双向），其 scope note 明确只对 `scripts/`、**不覆盖 eval 侧**；而 Promptfoo 套件自身的三方注册关系——磁盘 `evals/*_selftest.py`、yaml `script:` 引用、README 标题用例数——此前零机器断言。
- 探针逐字取证（python 精确建模，BSD sed 不认 `\s` 的坑已在 python 通道规避）：①磁盘 **17** 个 `*_selftest.py`（#34 后）；yaml `script:` 共 **34** 行 == `- description:` **34** 个 case（一 case 一 script），其中 evals/ 引用 18（17 selftest + 固定 `evals/fingerprint_check.py`）、scripts/ 14（check_dual_chain_baseline 出现 2 次，对应两个 case）、config/env load.py print-a/print-b 2；②磁盘 selftest ↔ yaml evals selftest 引用双向差集均为空（无 orphan / 无 missing）；③每个 yaml script 路径磁盘均存在；④每个 evals 自测 + fingerprint_check 的 SUCCESS/STABLE marker 都在 yaml 被 `value:` 断言（marker 提取正则 `(?:SUCCESS_MARKER|STABLE_MARKER)\s*=\s*["']([^"']+)["']`）；⑤README 两处标题计数（配置表 / seed 叙述）均为 34 == yaml case 数；⑥README 逐用例明细表早期行（#1–#16 gate/load 用例）列格式不统一（仅 16 行符合反引号路径列格式），编号连续性**刻意不钉**（脆弱，总量已由两处标题计数 + 磁盘↔yaml 双向覆盖）。
- 漂移是静默且真实的：新增自测忘登记 yaml → promptfoo 永不运行它（**假绿**）；yaml 指向已删脚本只在运行时炸；登记脚本却不断言其 PASS marker → case 不证明成功路径（放水）；README 计数漂移无人拦。

### 改动（纯 eval-only，0 生产代码 / 0 fixture / 0 ci.yml / 0 tempdir）

- 新增 `evals/eval_registry_selftest.py`（**eval #35**，对象是 **eval 套件注册面**，中缀 `eval_registry`；纯标准库，读**真实仓库**做健康对照，负向用**内存变异**注入、不写 tempdir、不改仓库）。核心 `evaluate(disk_selftest_names, yaml_text, readme_text, exists)` 为纯函数返回问题列表，场景 **3 negative / 2 non-flag / 1 healthy / 1 mutation**：
  - healthy：真实仓库零注册问题（磁盘 selftest 集合 == yaml evals selftest 引用集合双向；每个 yaml script 路径磁盘存在；case 数 == script 行数；fingerprint_check.py 在册；每个在册自测 + fingerprint_check 的 marker 都被 yaml `value:` 断言；README 两处标题计数 == yaml case 数）；
  - N1 磁盘多注入 `zzz_orphan_selftest.py`（yaml 未引用）必报 orphan（marker 检查只对「磁盘∩yaml」交集，孤儿不读 marker）；N2 yaml 内存追加一个指向不存在脚本的 case（同时带 description 保持一 case 一 script 中性）必报 missing on disk；N3 README 标题计数动态改成 99 必报 count drift；
  - non-flag1 固定严格层 `evals/fingerprint_check.py` 必须始终在册（#17 不能掉）；non-flag2 磁盘每个自测（≥17）与 fingerprint_check 的成功 marker 必须在 yaml 有断言；
  - mutation：把 yaml 文本中 frozen 自测的 PASS marker 断言内存替换为错误串，必被检出「marker not asserted」，证明 marker 检查非恒真。
- `evals/promptfooconfig.yaml`：34→**35**，末尾追加 #35 块（2 条 contains：`eval registry selftest: PASS` + 计数串）。
- `evals/README.md`：六处登记（配置表/seed 叙述 35、文件表新增注册面自测行、枚举句追加 #35、明细表 `| 35 |`、倒序新增 #35 专节置于 #34 专节之前，并写明明细表编号连续性刻意不钉的范围边界），484→498 行。
- 自举现象（符合预期）：脚本先于 yaml 登记落地时，healthy 对照立即把自身报为 orphan（`eval_registry_selftest.py` 未登记）——正是该测试要防的假绿；登记 yaml 后 healthy 转 PASS。

### 合并前回归（分支，2026-09-21 06:18 CST）

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py`：通过；
- `python3 scripts/run_all_gates.py`：**13/13**，`run_all_gates: all gates green`；
- `python3 evals/fingerprint_check.py`：**15/15 stable**（未改任何被指纹命令的 stdout）；
- eval-only 自测：**18 个全 PASS**（fail=0，新增 `eval_registry_selftest.py` 本地 7 个 `  ok ...` + PASS + 计数串）；
- promptfoo：**35/35 passed (100%)、0 failed、0 errors**（合并前 eval `eval-Dcn-2026-09-20T22:18:59`，Duration 21s）。

### 合并后回归（main `1ae11ca`，2026-09-21 06:37 CST）

- 功能 PR **#118**（分支 `test/eval-registry-selftest`，commit `a71feeb`，4 files +303/−3）required checks（structure/contracts/boundary）+ CodeQL（actions/javascript-typescript/python + 聚合）全 pass、Cursor Approval **APPROVED**，squash-merge 至 main **`1ae11ca`**（mergeCommit `1ae11ca487e7e9622feb838d74b03c71ab374565`），远端分支已删。
- 回 main 全套回归：gate **13/13**、指纹 **15/15 stable**、eval-only 自测 **18 个全 PASS**（fail=0）、promptfoo **35/35 passed (100%)、0 failed、0 errors**（合并后 eval `eval-4gv-2026-09-20T22:37:27`，Duration 25s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；未改 shell 包装；无框架迁移/依赖升级/API 变更/架构调整（仅新增一个 eval-only 自测 + 登记）。
- 负向一律内存变异（集合/文本注入），不写 tempdir、不在原地改任何文件；不新增依赖（仅一个新 .py）。
- 《6》CVE 审计保持只读；受保护旧草稿 `docs/01-dds-request-flow.md`（untracked）未删除/覆盖/提交。

### 剩余风险与缺口

- 本机无 ROS Humble runtime：真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`，未伪造。
- 第 13 闸与全部 eval-only 自测（含 #35）仍未接 CI structure 枚举（active 账号缺 `workflow` scope）。#35 自身也是 eval-only、不进 GATES、无需 ci.yml 接线。
- README 逐用例明细表编号连续性刻意不钉（早期行格式不统一）；若未来希望机器钉明细表，需先把该表规整为单一稳定列格式（独立小 PR）。
- 《6》CVE 修复三项仍待用户明确批准、拆独立 PR；4 份飞书文档仍 3380004 无权限。

### 下一步

1. ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 35/35），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ **[x] 已完成：功能 PR #118 → main `1ae11ca`；合并后回归 35/35（eval `eval-4gv-2026-09-20T22:37:27`），本回填 PR 即补登。**
2. runner 双面（#29/#30）+ eval 注册面（#35）+ 11 guard（#18–#28）+ 指纹严格层（#31）+ env 三层（#19/#32/#34）+ provider（#33）已闭环；再取证是否还有未钉的真实独有判定面（如 docs 契约链接同构检查是否有漂移面、其余 A 面脚本边界），**先 /tmp 探针确认真实未覆盖再新增，不为凑数**。
3. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #35，纯 python）接进 CI。
4. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
5. 若以上均不可推进且确无新高价值项：做完整 gate + 指纹 + #18–#35 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 39 — 2026-09-21 07:38（Asia/Shanghai）— eval #36：docs/refactor 与 evals 文档相对链接完整性自测（功能 PR #120，squash-merge main `e5146a5`）

### 背景与取证（先探针、后写脚本）

- re-ground：`main`=`2aa0f43`=origin/main（轮次38 回填 #119 后），工作区干净，仅受保护旧草稿 `docs/01-dds-request-flow.md` untracked（未碰）；本循环无在途 PR。
- runner 双面（#29/#30）、eval 注册面（#35）、11 guard（#18–#28）、指纹严格层（#31）、env 三层（#19/#32/#34）、provider（#33）已闭环。本轮按「下一步」取证 **docs 契约链接同构面**：CI `contracts` job 只对固定白名单做 `test -f`（**不解析** markdown 链接，且白名单不含 `docs/refactor/**` 与 `evals/**`）；`scripts/_md_paths.py` 的 `parse_map` 虽解析引用，但只服务 `check_source_map.py` / `check_executor_map.py` 两份特定架构图，且把反引号 `` `path` `` 也当引用（配符号 allowlist），与「纯 markdown 链接存在性」是不同职责。
- 探针逐字取证（python，先剥围栏代码块再剥行内代码）：扫描 `docs/refactor/**/*.md`（01、02、ITERATION_LOG）+ `evals/**/*.md`（README、results/BASELINE）共 **5 个** md；inline/图片链接 **165 个，全部为相对链接**（`../../scripts/...`、`../architecture/...`、同目录 `ITERATION_LOG.md`/`02-modernization-plan.md`，无 http/锚点/mailto），目标（文件或目录）**零断链、零越界**。
- 探针第一次未剥行内代码时出现 1 个误报 `[^"']+`——来自轮次38 日志行内代码里写的 marker 正则片段，证明正式自测必须先剥围栏与行内代码（GitHub 渲染时代码内 `](...)` 不是链接）；加行内代码剥离后误报清零。
- 真实缺口：本循环每轮产出/维护的这批文档约 165 个相对链接，其目标是否仍存在**此前零机器检查**；重命名/移动文件而不更新链接会静默腐烂文档。

### 改动（纯 eval-only，0 生产代码 / 0 fixture / 0 ci.yml / 0 tempdir）

- 新增 `evals/doc_link_selftest.py`（**eval #36**，对象是**文档链接同构面**，中缀 `doc_link`；纯标准库，读**真实仓库**做健康对照，负向用**内存注入链接**、不写 tempdir、不改仓库）。核心 `find_broken(entries, root, exists)` 为纯函数：先 `strip_code`（剥 ```` ``` ```` 围栏与 `` `...` `` 行内代码），再匹配 inline/图片链接；external（http/https/mailto/`#锚点`/`<...>`/web 根绝对路径）跳过；相对路径相对当前 md 目录 resolve，越出仓库根报 `escapes repo root`、目标（文件或目录，允许末尾 `/`）不存在报 `missing target`。场景 **3 negative / 2 non-flag / 1 healthy / 1 mutation**：
  - healthy：真实仓库 5 个 md、≥100 个相对链接（实测 165）、零断链；设文件数/链接数下限，防 glob 失效导致空扫恒真；
  - N1 注入缺失同级文件链接必报 missing；N2 注入 `../../../../` 越界链接必报 escape；N3 注入缺失目录（末尾 `/`）链接必报 missing；
  - non-flag1 external/锚点/mailto 一律不检查；non-flag2 围栏代码块与行内代码中的伪 `](x.md)` 链接不被扫描；
  - mutation：用 exists 包装把一个真实存在的目标强制判失，必被报 missing，证明检查非恒真。
- `evals/promptfooconfig.yaml`：35→**36**，末尾追加 #36 块（2 条 contains：`doc link selftest: PASS` + 计数串）。
- `evals/README.md`：六处登记（配置表/seed 叙述 36、文件表新增链接自测行、枚举句追加 #36、明细表 `| 36 |`、倒序新增 #36 专节置于 #35 专节之前），498→511 行。
- 自举联动：新脚本匹配 `evals/*_selftest.py`，落地未登记 yaml 时会被 #35 eval 注册面自测报为 orphan；登记 yaml 后 #35 与 #36 同时 PASS（注册面自测再次发挥防漏登作用）。

### 合并前回归（分支，2026-09-21 07:37 CST）

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py`：通过；
- `python3 scripts/run_all_gates.py`：**13/13**，`run_all_gates: all gates green`；
- `python3 evals/fingerprint_check.py`：**15/15 stable**（未改任何被指纹命令的 stdout）；
- eval-only 自测：**19 个全 PASS**（fail=0，新增 `doc_link_selftest.py` 本地 7 个 `  ok ...` + PASS + 计数串；#35 自举 orphan 已随登记消除）；
- promptfoo：**36/36 passed (100%)、0 failed、0 errors**（合并前 eval `eval-hvz-2026-09-20T23:37:54`，Duration 7s，热缓存）。

### 合并后回归（main `e5146a5`，2026-09-21 07:52 CST）

- 功能 PR **#120**（分支 `test/doc-link-selftest`，commit `ebe87a0`，4 files +289/−3）required checks（structure/contracts/boundary）+ CodeQL（actions/javascript-typescript/python + 聚合）全 pass、Cursor Approval **APPROVED**，squash-merge 至 main **`e5146a5`**（mergeCommit `e5146a5b66d3adbb79dcfe4fefba960d3a52b2b7`），远端分支已删。
- 回 main 全套回归：gate **13/13**、指纹 **15/15 stable**、eval-only 自测 **19 个全 PASS**（fail=0）、promptfoo **36/36 passed (100%)、0 failed、0 errors**（合并后 eval `eval-D4v-2026-09-20T23:52:44`，Duration 7s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；未改 shell 包装；无框架迁移/依赖升级/API 变更/架构调整（仅新增一个 eval-only 自测 + 登记）。
- 负向一律内存注入链接（不写 tempdir、不在原地改任何文档）；不新增依赖（仅一个新 .py）；`evals/results/BASELINE.md` 历史快照只读扫描、未改。
- 《6》CVE 审计保持只读；受保护旧草稿 `docs/01-dds-request-flow.md`（untracked）未删除/覆盖/提交。

### 剩余风险与缺口

- 本机无 ROS Humble runtime：真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`，未伪造。
- 第 13 闸与全部 eval-only 自测（含 #36）仍未接 CI structure 枚举（active 账号缺 `workflow` scope）。#36 自身 eval-only、不进 GATES、无需 ci.yml 接线。
- #36 只钉 `docs/refactor/**` 与 `evals/**`（本循环产出面）；`docs/architecture/**` 等已由 source_map/executor_map 与 CI `test -f` 白名单覆盖，未重复钉；裸 URL（ITERATION_LOG 里大量 PR https 链接非 markdown 链接形式）不在解析范围。
- 《6》CVE 修复三项仍待用户明确批准、拆独立 PR；4 份飞书文档仍 3380004 无权限。

### 下一步

1. ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 36/36），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ **[x] 已完成：功能 PR #120 → main `e5146a5`；合并后回归 36/36（eval `eval-D4v-2026-09-20T23:52:44`），本回填 PR 即补登。**
2. runner 双面、eval 注册面、文档链接面、11 guard、指纹严格层、env 三层、provider 均已闭环；继续取证是否还有未钉的真实独有判定面（如其余 A 面脚本边界、config/ 下文档链接），**先 /tmp 探针确认真实未覆盖再新增，不为凑数**。
3. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #35/#36，纯 python）接进 CI。
4. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
5. 若以上均不可推进且确无新高价值项：做完整 gate + 指纹 + #18–#36 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 40 — 2026-09-21 08:16（Asia/Shanghai）— eval #37：共享 gate helper `scripts/_repo.py` 自身契约自测（功能 PR #122，squash-merge main `9625cdc`）

### 背景与取证（先探针、后写脚本）

- re-ground：`main`=`00a8fb8`=origin/main（轮次39 回填 #121 后），工作区干净，仅受保护旧草稿 `docs/01-dds-request-flow.md` untracked（未碰）；本循环无在途 PR。
- runner 双面（#29/#30）、eval 注册面（#35）、文档链接面（#36）、11 guard（#18–#28）、指纹严格层（#31）、env 三层（#19/#32/#34）、provider（#33）已闭环。本轮盘点 **selftest 直接 import 的 scripts 模块**：11 个 guard、`run_all_gates`、`print_bench_gates`、`_freeze_paths`、`_md_paths` 均被覆盖；未被任何 selftest 直接钉到的有 `_repo.py`、`check_risk_matrix.py`（marker/order 断言重叠，已确认合理空缺）、`prove_rmw.py`（恒 exit0、无 FAIL 分支，已确认合理空缺）。
- 取证 `scripts/_repo.py`（《2》§5.3 下沉的**共享底座**，7 个函数 `repo_root`/`read_utf8`/`line_at`/`emit_render`/`append_bullets`/`report_missing_file`/`append_failures_block`，被 11 个 gate 复用）：#18–#28 只钉**消费** helper 的 gate，#29 仅把 `_repo.py` 列为"非 gate 库"用于注册面排除——helper 模块自身的分支/渲染契约**零直接断言**。底座一旦回归（root 解析到错目录、`emit_render` 吞掉非零退出码、FAIL 块丢标题）会同时静默削弱所有 gate。对称 #32（钉 load.py 真源）、#34（钉薄包装），这是真实未覆盖的共享底座面。
- /tmp 探针逐字验证 14 项分支全部成立：`repo_root` cwd 命中/fallback 命中/无参 ValueError/两处无 anchor SystemExit（文案 `cannot find repo root`）/tempdir 同名 anchor 压过 fallback；`line_at` 首/中/末/换行符 index/单行无换行 5 边界；`read_utf8` 非法字节 `\ufffd` lenient replace；`emit_render` stdout 文本 + code 0/1 透传；`append_bullets` 前缀与空 items no-op；`report_missing_file`/`append_failures_block` 逐字渲染。

### 改动（纯 eval-only，0 生产代码 / 0 fixture / 0 ci.yml）

- 新增 `evals/repo_helper_selftest.py`（**eval #37**，对象是**共享 helper 底座**，中缀 `repo_helper`；import **真实** `scripts/_repo.py`，文件系统分支用 tempdir + `os.chdir` 且 try/finally 必恢复 cwd，渲染 helper 纯内存；不改仓库）。场景 **3 negative / 2 non-flag / 1 healthy / 1 mutation**：
  - healthy：cwd=真实 root 时 `repo_root(AGENTS.md)` 返回真实 root、`scripts/_repo.py` 在其下，`read_utf8` 读到 AGENTS 首行，`line_at` 对自身源码 index 0 取首行一致；
  - N1 `repo_root()` 无参必须抛 `ValueError`；N2 cwd 空 tempdir、anchor 在 cwd 与 scripts 父目录都不存在时必须 `SystemExit` 非零且文案含 `cannot find repo root`；N3 `report_missing_file` 必须同时追加 failure 条目与 `- **FAIL missing:**` bullet、`append_failures_block` 必须 `FAIL:` 开头/每失败一 bullet/尾空行（失败必须可见、逐字）；
  - non-flag1 空 items 调 `append_bullets` 不改列表、`emit_render(("...",0))` 返回 0 且写文本；non-flag2 `read_utf8` 非法字节 lenient replace 不抛、`line_at` 五边界正确；
  - mutation：tempdir 放与真实 root 同名 anchor（`AGENTS.md`）并 chdir，`repo_root` 必须返回 tempdir（cwd 优先于 scripts 父回退），证明非恒返回 scripts 父。
- `evals/promptfooconfig.yaml`：36→**37**，末尾追加 #37 块（2 条 contains：`repo helper selftest: PASS` + 计数串）。
- `evals/README.md`：六处登记（配置表/seed 叙述 37、文件表新增 helper 自测行、枚举句追加 #37、明细表 `| 37 |`、倒序新增 #37 专节置于 #36 专节之前），511→523 行。
- 自举联动：新脚本匹配 `evals/*_selftest.py`，落地未登记 yaml 时被 #35 报为 orphan（实测 `orphan self-test ... repo_helper_selftest.py`）；登记 yaml 后 #35 与 #37 同时 PASS。

### 合并前回归（分支，2026-09-21 08:16 CST）

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py`：通过；
- `python3 scripts/run_all_gates.py`：**13/13**，`run_all_gates: all gates green`；
- `python3 evals/fingerprint_check.py`：**15/15 stable**（未改任何被指纹命令的 stdout）；
- eval-only 自测：**20 个全 PASS**（fail=0，cwd 已恢复仓库根；新增 `repo_helper_selftest.py` 本地 7 个 `  ok ...` + PASS + 计数串；#35 自举 orphan 已随登记消除）；
- promptfoo：**37/37 passed (100%)、0 failed、0 errors**（合并前 eval `eval-KLh-2026-09-21T00:16:18`，Duration 6s，热缓存）。

### 合并后回归（main `9625cdc`，2026-09-21 08:29 CST）

- 功能 PR **#122**（分支 `test/repo-helper-selftest`，commit `5a11136`，4 files：新 `evals/repo_helper_selftest.py` 146 行、yaml +16、README +15/−3、日志）required checks（structure/contracts/boundary）+ CodeQL（actions/javascript-typescript/python + 聚合）全 pass、Cursor Approval **APPROVED**，squash-merge 至 main **`9625cdc`**（mergeCommit `9625cdcf7dbee0032122179a9b03a6106a6c307d`），远端分支已删。
- 回 main 全套回归：gate **13/13**、指纹 **15/15 stable**、eval-only 自测 **20 个全 PASS**（fail=0，cwd 已恢复仓库根）、promptfoo **37/37 passed (100%)、0 failed、0 errors**（合并后 eval `eval-uB3-2026-09-21T00:29:58`，Duration 6s）。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；未改 shell 包装；无框架迁移/依赖升级/API 变更/架构调整（仅新增一个 eval-only 自测 + 登记；`scripts/_repo.py` 只读 import、未改一行）。
- 文件系统分支一律 tempdir + chdir 且 try/finally 恢复 cwd；渲染断言纯内存；不新增依赖（仅一个新 .py）。
- 《6》CVE 审计保持只读；受保护旧草稿 `docs/01-dds-request-flow.md`（untracked）未删除/覆盖/提交。

### 剩余风险与缺口

- 本机无 ROS Humble runtime：真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`，未伪造。
- 第 13 闸与全部 eval-only 自测（含 #37）仍未接 CI structure 枚举（active 账号缺 `workflow` scope）。#37 自身 eval-only、不进 GATES、无需 ci.yml 接线。
- 本轮钉的是共享 helper 底座；`_md_paths.py`（解析器）虽被 source_map/executor_map guard 间接 import，但其 `to_repo_rel`/`parse_map` 解析边界（逃逸返回 None、bare-word、fragment 剥离、ambiguous line cite）是否需要独立直接断言，留待下轮探针取证，不与本轮混合。
- 《6》CVE 修复三项仍待用户明确批准、拆独立 PR；4 份飞书文档仍 3380004 无权限。

### 下一步

1. ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 37/37），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ **[x] 已完成：功能 PR #122 → main `9625cdc`；合并后回归 37/37（eval `eval-uB3-2026-09-21T00:29:58`），本回填 PR 即补登。**
2. 取证 `scripts/_md_paths.py` 解析器自身边界（`to_repo_rel` 逃逸/裸词/fragment、`parse_map` ambiguous line cite）是否有未被 source_map/executor_map guard 间接覆盖的独有判定，**先探针逐字确认再决定是否新增**；不为凑数。
3. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #35–#37，纯 python）接进 CI。
4. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
5. 若以上均不可推进且确无新高价值项：做完整 gate + 指纹 + #18–#37 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

---

## 轮次 41 — 2026-09-21 09:15（Asia/Shanghai）— eval #38：共享 markdown 源图解析器 `scripts/_md_paths.py` 自身契约自测（功能 PR #126，squash-merge main `53e8570`）

### 背景与取证（先探针、后写脚本）

- re-ground：`main`=`0a410d3`=origin/main（轮次40 回填 #124 后），工作区干净，仅受保护旧草稿 `docs/01-dds-request-flow.md` untracked（未碰）；本循环无在途 PR。
- 轮次40 下一步第 2 条点名取证 `scripts/_md_paths.py`。盘点现有覆盖：#22（executor_map_guard）直接调 `parse_map` 但**只钉两个调用方参数**（`absent_keys`/`reject_bare_words`）；#21（source_map_guard）只在一个 mutation 里 monkeypatch `symbol_lines`；#36（doc_link）仅注释提及 `parse_map`。解析器自身的细粒度契约——`to_repo_rel` 的 root 逃逸（深度敏感）、fragment/`<>`/空格剥离、非路径拒绝、`ident_re` 词边界与缓存、`symbol_lines` 1-based、`parse_map` 的 LINK/TICK 行号、同名 suffix 唯一映射、ambiguous 报错、fenced code 排除——**零直接断言**。
- 读 `_md_paths.py` 全文（253 行）后用最小 temp tree 探针逐字验证。探针发现并修正一处**期望值错误（非代码 bug）**：map 位于 `docs/architecture/` 时，`../../etc/passwd` 只上两级到 root，解析为仍在 root 内的 `etc/passwd`（合法）；必须 `../../../etc/passwd`（上三级越出 root）才返回 None——逃逸判定是**深度敏感**的，两种深度都钉进自测。其余分支（剥离、external/绝对/`...` 拒绝、bare-word 开关、ident 词边界不匹配 `foobar` 但匹配 `x-foo-y`、正则缓存同一性、行号 1-based、LINK `a.cpp:12`/TICK `b.py:7`/同名 suffix 唯一映射补 55、双同名 → ambiguous note 且不归因、fence 内排除/fence 外保留、absent key 跳过）逐字成立。

### 改动（纯 eval-only，0 生产代码 / 0 fixture / 0 ci.yml）

- 新增 `evals/md_paths_parser_selftest.py`（**eval #38**，对象是**共享解析器底座**，中缀 `md_paths_parser`；import **真实** `scripts/_md_paths.py`，在最小 temp tree 上断言，不在仓库内写文件；不是 gate、不进 GATES、不被 CI 枚举）。场景 **3 negative / 2 non-flag / 1 healthy / 1 mutation**：
  - N1 越出 root 的 `../../../etc/passwd`、`../../../outside/x.md` 与 external/绝对路径必须 `to_repo_rel` 返回 None；N2 非路径 token（`...`、内嵌 `...`、URL、绝对路径、无前缀裸 `foo/bar.py`）必须被 `looks_like_repo_path` 拒绝、含 `...` target 返回 None，而 `scripts/`、`./docs/` 必须接受；N3 一个 `filename:line` 残余同名命中多个被引路径必须报 `ambiguous line cite ... matches N cited paths` 且不把行号归因到任一路径；
  - NF1 fragment/`<>`/空格剥离、**合法深度** `../../etc/passwd`→`etc/passwd` 不误杀、bare-word 开关 True/False 行为正确；NF2 ident 词边界（不匹配子串、匹配连字符边界）、正则缓存同一性、symbol_lines 1-based；
  - healthy：真实 `docs/architecture/ros2-source-map.md` 经 `parse_map` 得非空 cited、无 ambiguous note、至少一个被引目标在磁盘存在；
  - mutation：fenced code block 内链接排除、fence 外同形链接保留（证明 fence 剥离真实生效）。
- `evals/promptfooconfig.yaml`：37→**38**，末尾追加 #38 块（2 条 contains：`md paths parser selftest: PASS` + 计数串）。
- `evals/README.md`：六处登记（配置表/seed 叙述 38、文件表新增解析器自测行、枚举句追加 #38、明细表 `| 38 |`、倒序新增 #38 专节置于 #37 专节之前），523→535 行。
- 自举联动：新脚本落地未登记 yaml 时被 #35 报 orphan（实测 `orphan ... md_paths_parser_selftest.py`）；登记后 #35 与 #38 同时 PASS。#22 已钉的两个调用方参数只在 NF1 轻触、不重复。

### 合并前回归（分支，2026-09-21 09:15 CST）

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py`：通过；
- `python3 scripts/run_all_gates.py`：**13/13**，`run_all_gates: all gates green`；
- `python3 evals/fingerprint_check.py`：**15/15 stable**（未改任何被指纹命令的 stdout；`_md_paths.py` 只读 import、未改一行）；
- eval-only 自测：**21 个全 PASS**（fail=0；新增 `md_paths_parser_selftest.py` 本地逐行 `  ok ...` + PASS + 计数串；#35 自举 orphan 已随登记消除）；
- promptfoo：**38/38 passed (100%)、0 failed、0 errors**（合并前 eval `eval-5gX-2026-09-21T01:15:11`，Duration 8s，热缓存）。

### 合并后回归（main `53e8570`，2026-09-21 09:34 CST）

- 功能 PR **#126**（分支 `test/md-paths-parser-selftest`，commit `ed66081`，4 files +247/−3）required checks（structure/contracts/boundary）+ CodeQL 全 pass、Cursor **APPROVED**（1m12s）、MERGEABLE，squash-merge main **`53e8570`**（mergeCommit `53e8570a1b1a7039b8fc0dad43d58c4ffe9d9b3e`），远端分支已删；合并后本地 pull 撞 2 次网断，API 确认 MERGED 后重试成功（未重复 merge）。
- 合并后回归：gate **13/13**（all gates green）；`fingerprint_check.py` 单独连跑 **2 次均 15/15 stable、exit 0**；**21 个** eval-only 自测全 PASS（fail=0）。
- promptfoo：合并后**权威结果 38/38 passed (100%)、0 failed、0 errors**（eval `eval-8dC-2026-09-21T01:34:41`，Duration 12s）。
- **高负载瞬时 flaky 记录（非本轮引入、非断言漂移）**：合并后首轮 promptfoo（`eval-P3D-2026-09-21T01:27:18`）报 3 errors、次轮（`eval-5k9-2026-09-21T01:30:55`）报 1 error，均为既有 `evals/fingerprint_check.py`（#17，内部串行 15 个 gate/load 子进程）在本机高负载（`vm.loadavg` 实测 19–35）叠加 promptfoo concurrency=4 时偶发非零退出；0 failed（无任何 contains 断言失败）。该脚本单独串行连跑两次均 stable，负载缓解后第三轮 promptfoo 即 38/38、12s。结论：#38 纯 tempdir/内存、不起子进程，不增加该 flaky 面；fingerprint_check 在高负载并发下的健壮性（超时/重试）可作为后续独立改进项，**不在本轮处理、不为此放水断言**。

### Hold 合规

- 未编辑 `config/fastdds.xml`；未改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未启用 Agnocast/zenoh；未改 `dimos_bridge` DDS 行为与 vendor 源码；未集成 Cega、未重写 Bridge runtime；未改 shell 包装；无框架迁移/依赖升级/API 变更/架构调整（仅新增一个 eval-only 自测 + 登记；`scripts/_md_paths.py` 只读 import、未改一行）。
- 所有 temp tree 仅在 `tempfile.TemporaryDirectory()` 内、自动清理；不新增依赖（仅一个新 .py）。
- 《6》CVE 审计保持只读；受保护旧草稿 `docs/01-dds-request-flow.md`（untracked）未删除/覆盖/提交。

### 剩余风险与缺口

- 本机无 ROS Humble runtime：真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`，未伪造。
- 第 13 闸与全部 eval-only 自测（含 #38）仍未接 CI structure 枚举（active 账号缺 `workflow` scope）。#38 自身 eval-only、不进 GATES、无需 ci.yml 接线。
- `check_cited_paths`（存在性 + allowlist symbol + stale-line warning 渲染）经 source/executor guard 黑盒与 #21 mutation 间接覆盖，本轮未对其逐字渲染重复断言；若后续取证发现 stale-line WARN vs symbol-gone FAIL 的边界仍有未覆盖细支，再单独探针。
- 《6》CVE 修复三项仍待用户明确批准、拆独立 PR；4 份飞书文档仍 3380004 无权限。

### 下一步

1. [x] 功能 PR **#126** 已 squash-merge main `53e8570`；合并后回归 38/38（权威 eval `eval-8dC-2026-09-21T01:34:41`），结果已回填本小节（本回填 PR）。
2. 三个共享底座（`_repo` #37、`_md_paths` #38、`_freeze_paths` 真源）中，`_freeze_paths.py`（frozen 字面量真源生成）目前仅经 #18 guard 黑盒与 `from _freeze_paths import` 间接覆盖；下轮探针其真源生成/集合契约是否需要独立直接断言，**先探针逐字确认再决定**，不为凑数。
3. 若 `workflow` scope 已授权：用离线备份开**独立 PR** 把第 13 闸与 eval-only 自测（含 #35–#38，纯 python）接进 CI。
4. 若用户批准 CVE 修复三项：拆 3 个独立 PR（不与重构/eval 混合）。
5. 若以上均不可推进且确无新高价值项：做完整 gate + 指纹 + #18–#38 + promptfoo 回归并在日志标注「等待新指令」，不制造无意义提交。

## 轮次 42 — 2026-09-21 10:32（Asia/Shanghai）— eval #39：共享 markdown 源图校验渲染器 `scripts/_md_paths.check_cited_paths` 自身契约自测（功能 PR #129，squash-merge main `dd706e1`）

### 本轮做了什么（评估驱动，一个小步，纯 eval-only）

- re-ground：main `d6c9460`=origin/main，工作区仅受保护旧草稿 `docs/01-dds-request-flow.md` untracked，本循环无在途 PR。
- 按轮次41 下一步先取证 `scripts/_freeze_paths.py`（frozen 字面量真源）：全文仅 26 行、**4 个纯常量、无函数/无生成逻辑/无集合**（`FASTDDS_XML_REL`、`SCOREBOARD_REL`、`XML_EXISTENCE_NOTE`、`SCOREBOARD_EXISTENCE_NOTE`）。查清：①第 13 gate `check_frozen_path_literals.py` **不 import 它**，只静态扫描有无第二个 `Path(...)` 硬编码（#18 钉的是该检测器）；②4 常量被 **8 个 gate** import 消费（cega/dod/dual_chain_baseline/risk_matrix/sink/three_chain/unitree/print_bench），路径值由 gate existence 检查、NOTE 字符串由 #17 stdout 指纹（15 fixtures）+ 8 个 guard 黑盒**三重间接逐字钉死**。结论：纯常量真源无独有分支逻辑，另写 selftest 只会重复断言同样 4 个字面量，判为**合理空缺，不为凑数新增**。
- 转向轮次41 明确挂起项：`scripts/_md_paths.py` 的另一半公共函数 `check_cited_paths`（把 `parse_map` 解析出的 `{path: cited 行号}` 转成存在性 + allowlist symbol 裁决 + 渲染 + 计数）。盘点确认 #21（source_map_guard）经 guard `render()` 黑盒只覆盖 missing path→FAIL / allowlisted symbol gone→FAIL / cited 行与 symbol 全不交集→WARN-only / healthy→exit0 四主判定 + 一个 `symbol_lines` mutation，#22 只钉 `parse_map` 参数；下列细粒度契约**零直接断言**。
- 内联探针（tempdir + 真实 `_md_paths`）逐字取证后新增 `evals/md_paths_cited_selftest.py`（**eval #39**，中缀 `md_paths_cited`，import 真实 `_md_paths` 与真实 `check_source_map.SYMBOL_ALLOWLIST`，文件只建在 `TemporaryDirectory`；被测 `_md_paths.py` **只读 import、不改一行**）。场景 **3 negative / 2 non-flag / 1 healthy / 1 mutation**：
  - N1 不存在的被引路径必进 failures（`missing path`）且**不计入** ok_paths、不计 symbol；
  - N2 文件存在但 allowlisted symbol 消失必进 failures（`symbol ... gone`）且**不计入** symbol_ok；
  - N3 被引的是**目录**时，即使 allowlist 给它配了 symbol，也必须渲染 `ok dir`、**跳过 symbol 检查**（不读目录、不 FAIL、不计 symbol_ok）——防 false-positive；
  - NF1 cited 行与真实 symbol 行**全不交集**时只进 warnings（WARN stale line）、不进 failures、present symbol **仍计入** symbol_ok（warn-only 不改 exit）；
  - NF2 计数口径（ok_paths 数 file+dir、missing 排除；symbol_ok 数 present、gone 排除、无 allowlist 文件不查）、多 hit 渲染 `at L<first> (+N-1)`、被引行号渲染 `(cited L…)`；
  - healthy：真实 `docs/architecture/ros2-source-map.md` 经 `parse_map` + 真实 `SYMBOL_ALLOWLIST` 跑 `check_cited_paths`，failures 为空、ok_paths == cited 数（全在盘）、至少 1 个 symbol 命中；
  - mutation：cited 行集合与真实 symbol 行**部分交集**（cited {1,2}、symbol 在 {2,9}）时**不得**报 stale warning 且 symbol 计 ok——钉死 `cited_lines.isdisjoint(hits)` 的**集合**语义，防退化为「首行不等就 warn」。
- 探针修正：首版自测把三元组返回值误按二元组解包（`ValueError: too many values to unpack`），改为 `lines, ok_paths, symbol_ok` 后全绿（自测脚本自身笔误，非被测代码问题）。
- 登记：`evals/promptfooconfig.yaml` 38→39（EOF 追加，2 条 contains：PASS marker + 计数串）；`evals/README.md` 六处（535→548 行：配置表、seed 叙述、文件表、枚举句、明细表 `| 39 |`、倒序 #39 专节置于 #38 专节前）。自举：未登记 yaml 时 #35 立即报 orphan `md_paths_cited_selftest.py`，登记后 #35/#39 同 PASS。

### 分数前后对比

| 项 | 轮次41 后 | 轮次42 后 |
| --- | --- | --- |
| `run_all_gates.py` | 13/13 all gates green | **13/13**（不变） |
| stdout 指纹 `fingerprint_check.py` | 15/15 stable | **15/15 stable**（单独串行） |
| eval-only 自测脚本数 | 21（#18–#38） | **22（#18–#39）**，循环 fail=0 |
| Promptfoo seed 用例 | 38/38 (100%) | **39/39 (100%)、0 failed、0 errors** |
| 合并前权威 eval ID | eval-5gX-2026-09-21T01:15:11 | **eval-Od8-2026-09-21T02:32:02**（Duration 3s，loadavg 已降到 11–16） |

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py` 通过。
- 轮次41 记录的高负载 fingerprint flaky 本轮未复现（本轮 promptfoo 3s、0 error；仍作为独立健壮性改进项保留）。

### 产物检查结果

- 新增 `evals/md_paths_cited_selftest.py` 单独运行 PASS（计数串 `3 negative, 2 non-flag, 1 healthy, 1 mutation`）；#35 注册面自测在登记前报 orphan、登记后 PASS（自举符合预期）。
- 22 个 eval-only 自测循环全 PASS；gate 13/13；指纹 stable；Promptfoo 39/39。
- 改动文件仅 4 个：新自测 1 个、yaml、README、本日志；无 fixture 新增、无树内文件改动。

### 合并后回归（main `dd706e1`，2026-09-21 10:38 CST）

- 功能 PR **#129**（分支 `test/md-paths-cited-selftest`，commit `ee2ef8a`，4 files +272/−3）required checks（structure/contracts/boundary）+ CodeQL（actions/javascript-typescript/python + 聚合）全 pass、Cursor **APPROVED**（1m28s）、MERGEABLE，squash-merge main **`dd706e1`**（mergeCommit `dd706e15f04743cbf8fe6d7418ebf8a1e95de646`），远端分支已删。
- 合并后回归：gate **13/13**（all gates green）；`fingerprint_check.py` 单独 **15/15 stable**；**22 个** eval-only 自测全 PASS（fail=0）。
- promptfoo：**39/39 passed (100%)、0 failed、0 errors**（合并后权威 eval `eval-3ee-2026-09-21T02:37:59`，Duration 4s，loadavg 12–15）。合并前 eval `eval-Od8-2026-09-21T02:32:02`（3s）同为 39/39；轮次41 记录的高负载 fingerprint flaky 本轮合并前后均未复现（根因未除，仍列独立改进项）。

### Hold 合规

- 不编辑 `config/fastdds.xml`；不改 `docs/artifacts/bench/SCOREBOARD.md` 数字；负向场景一律 tempdir 副本 / 内存变异，不在原地改。
- 不启用 Agnocast/zenoh（无 vendor 树/kmod/rmw_zenoh）；不改 `dimos_bridge/dimos/**` DDS 行为与 vendor 源码；不集成 Cega、不重写 Bridge runtime；不改 shell 包装。
- `scripts/_md_paths.py`、`scripts/check_source_map.py` 只读 import，未改一行；无框架迁移/依赖升级/API 变更；新自测纯标准库、tempdir-only，不新增运行时依赖（promptfoo 仅 npx 缓存运行）。
- 《6》CVE 审计保持只读；受保护旧草稿 `docs/01-dds-request-flow.md` 未跟踪、未提交、未改动。

### 剩余风险

- 与 #38 同：eval-only 自测不是 CI gate，不进 `run_all_gates.GATES`、不被 CI structure 枚举（第 13 gate 与全部 selftest 接 ci.yml 仍卡在 active 账号缺 `workflow` scope）。
- `check_cited_paths` 的真实 guard 集成路径仍由 #21/#22 黑盒兜底；本轮补齐的是函数级直接断言，二者互补。
- 本机无 ROS Humble runtime：真·双链 pub/sub、p99、跨机 UDP、三链实际复现仍 `STATUS: blocked`，未伪造。
- 高负载下 `fingerprint_check.py` 在 promptfoo concurrency=4 偶发非零（轮次41 记录）本轮未复现，根因未除，留作独立改进。

### 下一步

1. [x] 功能 PR **#129** 已 squash-merge main `dd706e1`；合并后回归 39/39（权威 eval `eval-3ee-2026-09-21T02:37:59`），结果已回填本小节（本回填 PR）。
2. 共享底座盘点：`_repo`（#37）、`_md_paths` 解析半（#38）与校验渲染半（#39）均已直接钉；`_freeze_paths`（纯常量）、`prove_rmw`（恒 exit0）、`check_risk_matrix`（marker/order 与既有断言重叠）维持**合理空缺**倾向，下轮若要动须先探针找到真实未覆盖的独有判定。
3. 独立改进候选（需先探针、拆清楚，勿与小步重构混 PR）：fingerprint_check 高负载并发健壮性（子进程超时/重试，或评估 promptfoo 侧降并发/重跑该 case），注意可能影响 #17/#31。
4. 长期阻塞不变：ci.yml 接线（需用户本机 `gh auth refresh -h github.com -s workflow`）；《6》CVE 修复三项待用户明确批准后拆独立 PR；4 份飞书文档 3380004 无权限；Humble Linux 主机解除端到端 blocked。

## 轮次 43 — 2026-09-21 12:43（Asia/Shanghai）— local-script provider 超时预算硬化（修轮次41 fingerprint 高负载 flaky 根因）（功能 PR #132，squash main `178cfc3`）

- **主题**：轮次41 合并后 promptfoo 在整机高负载（`vm.loadavg` 实测 19–35）下，最重的 `evals/fingerprint_check.py`（#17，内部**串行**跑 13 gate + 2 个 `load.py print-*` 共 15 个 python 子进程）case 偶发 provider 层 `[ERROR] ... exited`、**0 failed**（无断言失败），当时留作独立健壮性改进项。本轮先只读取证、再最小修复，不改 gate/生产代码、不改 fingerprint 判定与 fixtures。

### 取证（先探针、不臆测）

- re-ground：main `7f119af`=origin/main、工作区仅受保护旧草稿 untracked、本循环无在途 PR。
- **纯并发压力不复现**：/tmp 脚本以并发 8 连开 8 波、每波 4 个 fingerprint_check + 2 个会 chdir 的 repo_helper selftest（共 32 个 fingerprint 实例、16 个 selftest），4s 内**全部 rc=0**。说明非零**不是** fork/进程资源竞争，也不是 gate 输出不确定。
- 读 `evals/localScriptProvider.mjs`：`execFileSync('python3', argv, { timeout: 30000, ... })` 是**固定 30s** 硬超时。fingerprint 正常 2–4s，但在整机 loadavg≈35 且 promptfoo concurrency=4 争抢时，15 个串行子进程墙钟可超 30s，被 node 杀掉 → provider 返回 error（轮次41 单次 promptfoo 总时长飙到 3m14s 与此一致）；这是 provider 层超时，**不是**断言失败，故 0 failed。
- node 探针（`timeout:200` 跑 sleep 1.5）逐字取超时 err 字段：`status=null`、`signal="SIGTERM"`、`code="ETIMEDOUT"`、`message="spawnSync python3 ETIMEDOUT"`。旧 catch 用 `typeof err.status==='number' ? err.status : 'unknown'`，会把超时**误标成 `code unknown`**，无法与主动非零退出区分。
- 确认 #33 `local_script_provider_selftest.py` 此前**无超时用例**、也不钉 30000 数值（`timeout:30000` 仅出现在 .mjs 与测试内盲桩副本），故提高预算不破坏既有断言。

### 改动（仅 eval 工具层 + 其自测，0 gate / 0 fixture / 0 ci.yml）

- `evals/localScriptProvider.mjs`（76→106 行，`node --check` 通过）：
  - 新增具名 `DEFAULT_TIMEOUT_MS = 120000`（30s→120s，给过载下串行 15 子进程 4 倍余量）；
  - 新增 `resolveTimeoutMs()`：读 env `LOCAL_SCRIPT_TIMEOUT_MS`，正整数 ms 生效、否则回退默认（`Number.isFinite && >0`，非法/非正不清零预算）；
  - catch 中分类：`err.code==='ETIMEDOUT' || err.signal==='SIGTERM'` → `code` 标为 `timeout` 并附 ` after {N}ms`；主动非零退出仍是数字 `code`（如 `code 1`）。
  - **不加重试、不软化**：超时与非零一样返回 error（promptfoo 仍判失败）；真实 exit1 / stdout drift 行为逐字不变；成功 output 仍仅 stdout。
- `evals/local_script_provider_selftest.py`（#33，225→282 行）在既有 7 项检查上新增 2 项（真实行为先经 /tmp node 探针逐字取证）：
  - **N4 超时负向**：harness 末尾临时 `LOCAL_SCRIPT_TIMEOUT_MS=250` 跑 sleep 1.2s 夹具 → 必须 error 且含 `code timeout`、`ETIMEDOUT`/`SIGTERM`、`after 250ms`；同时钉主动 exit1 仍报 `code 1`（不被误标/软化）；删除覆盖后再跑快速 exit0 夹具必须成功（env 不泄漏）。
  - **超时预算契约（静态）**：.mjs 必须有具名 `DEFAULT_TIMEOUT_MS` 且 ≥60000（防退回过紧的 30s）、`LOCAL_SCRIPT_TIMEOUT_MS` 覆盖已接线、含 `ETIMEDOUT`/`SIGTERM` 分类、非法覆盖回退默认。
  - 计数串由 `3 negative, 2 non-flag, 1 healthy, 1 mutation` 更新为 `4 negative, 2 non-flag, 1 healthy, 1 mutation, 1 timeout-budget contract`（9 项检查全 ok）。
- 登记同步：`evals/promptfooconfig.yaml` **仅 #33 块**（description 补超时语义 + 计数串；#32/#34–#39 的同名计数串未动）；`evals/README.md` 文件表行、明细表 #33 行、#33 专节（新增超时负向 + 预算契约两 bullet，并把过时的「不修改 provider 行为（行为不变）」范围边界改为如实说明本次唯一行为变更），548→550 行。用例总数仍 **39**（未新增 promptfoo case，#33 内部加断言）。

### 行为不变与产物检查

- provider 非零→error、成功 output 仅 stdout 的裁决语义未变；`evals/fingerprint_check.py` 与 15 个 fixtures **一行未改**（provider 不在 fingerprint 的 15 个被跑命令内），指纹仍 **stable、无需 `--update`**；#31 钉的「恒非零 gate 必 FAIL」不受影响（本轮未碰 fingerprint）。
- 端到端 /tmp node 探针实测：主动 exit1→`exited with code 1`；env250+sleep1.2→`exited with code timeout after 250ms: spawnSync python3 ETIMEDOUT`；删 env 后快速命令 OK；env=garbage 回退默认真实命令 OK。
- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py` 通过。

### 分数前后对比（本机 macOS，无 ROS runtime）

- gate：**13/13** all gates green（不变）；stdout 指纹：**15/15 stable**（不变）；eval-only 自测：**22 个全 PASS（fail=0）**（#33 由 7 项断言增至 9 项）。
- promptfoo：**39/39 passed (100%)、0 failed、0 errors**，合并前 eval `eval-pQI-2026-09-21T04:42:54`（Duration 4s，loadavg 10–13）。

### 合并后回归（main `178cfc3`，2026-09-21 12:49 CST）

- 功能 PR **#132**（分支 `fix/local-script-provider-timeout`，commit `8a0d2a1`，5 files +154/−9）required checks（structure/contracts/boundary）+ CodeQL（actions/javascript-typescript/python + 聚合）全 pass、Cursor Approval **APPROVED**（1m24s），已 squash-merge 并删远端分支，mergeCommit `178cfc3e6d0123d48a6d0d57e1ceae7b7d765310`。
- 回 main 拉取后：compileall 通过；gate **13/13** all gates green；stdout 指纹 **15/15 stable**（fixtures 未改）；22 个 eval-only 自测 **fail=0**（#33 为 9 项断言）。
- 合并后权威 promptfoo：**39/39 passed (100%)、0 failed、0 errors**，eval `eval-d5a-2026-09-21T04:49:03`（Duration 4s，loadavg 10–13）。provider 预算硬化后本轮高负载窗口 fingerprint case 未再超时（合并前 `eval-pQI-2026-09-21T04:42:54` 同为 39/39、0 error）。

### Hold 合规

- 不编辑 `config/fastdds.xml`；不改 `docs/artifacts/bench/SCOREBOARD.md` 数字；未碰任何 fixtures、ci.yml、shell 包装、vendor、`dimos_bridge/dimos/**`；不启用 Agnocast/zenoh、不集成 Cega、不重写 Bridge runtime。
- 仅改 eval 工具（custom provider）与其 eval-only 自测；无框架迁移/依赖升级/API 变更；新断言纯标准库 + tempdir node harness，不新增运行时依赖（promptfoo 仅 npx 缓存运行，node 本就是其依赖）；CVE 审计只读；旧草稿未跟踪未改。

### 剩余风险

- 120s 是工程余量而非无界保证：若整机持续极端过载（远超 loadavg 35）fingerprint 墙钟仍可能超 120s——那属资源争抢，正确做法是降载/降并发，不应靠无限放宽超时或重试掩盖；本轮刻意**不加重试**，避免把严格层变软（真实 drift/非零仍稳定复现并失败）。
- provider 超时分类与预算下限已由 #33 两条新断言钉死，退回 30s / 吞掉超时 / env 泄漏都会让 #33 FAIL。
- eval-only 自测仍不是 gate、不进 GATES、CI structure 不枚举（第 13 gate 与把 fingerprint/selftest 接 ci.yml 仍待 `workflow` scope，离线备份在 `~/ros2_hzj_pending/`）。
- 真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`（无 Humble 主机），未伪造。

### 下一步

1. [x] 功能 PR **#132** 已合并（main `178cfc3`）；合并后全套回归 39/39、0 error（eval `eval-d5a-2026-09-21T04:49:03`），PR 号 / main HEAD / eval ID 已由本回填 PR 补入。
2. 轮次41 flaky 的运行面缓解（provider 预算已硬化）可在后续高负载窗口再观察：若仍偶发超时，考虑在 promptfoo 侧对 fingerprint 单 case 降并发（独立 PR、先取证），而不是继续加大全局超时。
3. 共享底座 `_repo`(#37)/`_md_paths` 解析半(#38)/校验渲染半(#39) 已直接钉；`_freeze_paths`（纯常量）、`prove_rmw`（恒 exit0）、`check_risk_matrix`（marker/order 重叠）维持**合理空缺**倾向，要动须先 /tmp 探针找到真实未覆盖的独有判定，不为凑数新写低价值自测。
4. 长期外部阻塞不变：ci.yml 接线需 `gh auth refresh -s workflow`；CVE 修复三项待用户批准拆独立 PR；4 份飞书文档 3380004；Humble 主机解除端到端 blocked。

## 轮次 44 — 2026-09-21 13:17（Asia/Shanghai）— doc-link 自测扫描面扩到全部自有（A 面）文档（功能 PR #134，main ca975b9）

- **主题**：轮次43 收尾后按日志下一步候选，深化《5》评估套件的**真实覆盖广度**。#36 `evals/doc_link_selftest.py` 首版（轮次39）只扫本循环每轮产出的 `docs/refactor/**` 与 `evals/**`（5 个 md、165 个相对链接），而双链中间件的**权威文档**（`docs/architecture/` 各 feishu-* 图 / source-map、`docs/security/` CVE 审计、`docs/testing/` Mac HIL、`config/**`、`scripts/bench/README` 等）此前不在任何链接完整性检查内——CI contracts job 只对固定白名单 `test -f`、不解析链接。本轮把扫描面扩到全部自有 A 面文档，并明确只读/冻结树的排除边界。

### 取证（先全仓探针、不臆测）

- re-ground：main `087468f`=origin/main、无在途本循环 PR、仅受保护旧草稿 untracked。
- 用 #36 同款解析（剥围栏+行内代码、外链/锚点/mailto 跳过、相对路径解析+越界/缺失裁决）扫**全部 260 个 tracked md / 1226 个相对链接**，分组结果：
  - 旧扫描面 current（docs/refactor+evals）：5 文件 / 165 链接 / **0 broken**；
  - 自有其余 A 面（根 README/AGENTS、docs/architecture 16、docs/security、docs/testing、docs/usage、docs/eval、config/env、scripts/bench、dimos_bridge/SOURCE、docker/ros）：29 文件 / 758 链接 / **0 broken**；
  - `docs/artifacts/**`（132 个 bench 快照/产物，含数字冻结 SCOREBOARD）：207 链接 / 0 broken；
  - `vendor/**`（94 个第三方 DDS/rmw md）：96 链接 / **3 broken，全部是上游文档自身问题**——CycloneDDS `README.md → docs/manual/config.rst`、CycloneDDS `docs/dev/dds_security_effort.md → multi_process_testing.md`、Fast-DDS `test/performance/latency/README.md → latency-measure`。
- glob 命中探针：12 条 SCAN_GLOBS 精确命中 34 个自有文件（=current+A-own），0 遗漏、0 多扫、vendor/artifacts 零泄漏；untracked 旧草稿 `docs/01-dds-request-flow.md` 位于 `docs/` 根，不被任何 `docs/<area>/**` glob 命中，天然不扫。

### 改动（仅 eval-only 自测 + 登记文档；解析裁决逻辑零改动）

- `evals/doc_link_selftest.py`（#36，约 200→292 行）：
  - `SCAN_GLOBS` 由 2 条扩到 12 条（新增 docs/architecture|security|testing|usage|eval、config、scripts、dimos_bridge、docker 的 `**/*.md`，以及根 `*.md` 覆盖 README.md/AGENTS.md）；
  - 新增 `EXCLUDE_PREFIXES=("vendor/","docs/artifacts/")` 与纯函数 `_excluded(rel)`，`_real_entries()` 据此过滤；
  - healthy 下限由「≥5 md / ≥100 链接」上调为「**≥30 md / ≥900 链接**」（扩面时实测 34/923，留余量且能抓住大面积回退）；
  - healthy 新增**扫描面契约**：9 个钉选 A 面权威文档（ros2-source-map、CVE 审计、Mac HIL、config/env/README、scripts/bench/README、根 README/AGENTS、ITERATION_LOG、evals/README）必须在扫描集，且 vendor/artifacts 不得泄漏进扫描集——防 glob 笔误静默缩面/扩面；
  - 新增 **NF3（non-flag）**：`_excluded()` 真值表（vendor/artifacts=True、architecture/evals=False）+ 真实扫描集不含任何排除树，并以 vendor 两处已知上游断链作为「为何必须排除」的对照；
  - 计数串 `2 non-flag`→`3 non-flag`（3 negative / 3 non-flag / 1 healthy / 1 mutation）；模块 docstring 同步说明扩面历史与排除理由。
  - `find_broken`/`strip_code`/外链裁决等**纯函数一行未改**，只扩大了喂入的 entries 来源；N1/N2/N3、NF1/NF2、mutation 全部仍通过。
- 登记：`evals/promptfooconfig.yaml` **仅 #36 块**（description 改为全 A 面 + vendor/artifacts 排除 + 钉选文档；计数串 3 non-flag）；`evals/README.md` 文件表行、明细表 #36 行、#36 专节（扩面历史、34/923、排除两棵树、健康表面契约、3 non-flag），550→551 行。promptfoo 用例总数仍 **39**（#36 内部加断言，未新增 case）。

### 行为不变与产物检查

- 扩面后真实 A 面 **0 broken**——本轮**没有为让检查通过而修改任何被扫文档的链接**（A 面本来就健康）；3 处 broken 全在只读 vendor，按 Hold 只记录、不修。
- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py` 通过；#36 实跑 8 行 ok（healthy 34/923/0、表面契约、3 negative、3 non-flag、mutation）后 PASS。

### 分数前后对比（本机 macOS，无 ROS runtime）

- gate：**13/13** all gates green（不变）；stdout 指纹：**15/15 stable**（未改 gate/fixtures，无需 `--update`）；eval-only 自测：**22 个全 PASS（fail=0）**（#36 由 7 项断言增至 8 项、non-flag 2→3）。
- promptfoo：**39/39 passed (100%)、0 failed、0 errors**，合并前 eval `eval-uH8-2026-09-21T05:16:59`（Duration **4s**，当时 `vm.loadavg`≈28 偏高仍 0 error——轮次43 把 provider 预算从 30s 提到 120s 后，高负载窗口 fingerprint case 未再超时，初步佐证硬化有效）。

### Hold 合规

- 不编辑 `config/fastdds.xml`；不改 `docs/artifacts/bench/SCOREBOARD.md` 数字（且本轮把整个 `docs/artifacts/**` 列为不扫描的冻结面）；**未改 vendor 任何文件**（发现的 3 处上游断链只在日志/自测注释中记录，归上游修）；未改 shell 包装、未改 `dimos_bridge/dimos/**`；不启用 Agnocast/zenoh、不集成 Cega、不重写 Bridge runtime。
- 仅改 eval-only 自测与其登记文档；#36 仍非 gate、不进 GATES、CI structure 不枚举、无需 ci.yml 接线；纯标准库 + 读真实仓库/内存注入，不新增依赖、不写 tempdir、不改仓库文档；CVE 审计只读；旧草稿未跟踪未扫未改。

### 剩余风险

- vendor 的 3 处断链是上游 CycloneDDS/Fast-DDS 文档自身问题，已如实记录、刻意不扫不修；若未来 vendor 升级改变文档布局，以新版本实际为准，不影响本仓 A 面。
- `docs/artifacts/**` 不扫是刻意范围（冻结产物/快照）；其链接若腐烂不影响构建与 guard，且 SCOREBOARD 数字面另有 boundary/fingerprint 保护。
- 全新的**顶层 A 面 md 目录**若日后出现，需要在 SCAN_GLOBS 加一条；9 个钉选文档 + ≥30/≥900 下限能捕获主要缩面回退，但不会自动发现一个未登记的新目录（README 已说明枚举式 glob 的边界，属可接受）。
- 真·双链 pub/sub、p99、跨机 UDP、三链**实际复现**仍 `STATUS: blocked`（无 Humble 主机），未伪造。

### 合并后权威回归（main ca975b9，PR #134 squash-merge）

- 功能 PR #134（分支 test/doc-link-widen-surface，commit 218672c，4 files +164/−21）required 三检 structure/contracts/boundary 全 pass、CodeQL pass、Cursor Approval APPROVED（1m9s）→ squash-merge，main `ca975b9c2ba449843421cf276f2e706068889983`，远端分支已删。
- 回 main 同步后回归：gate **13/13** all gates green；stdout 指纹 **15/15 stable**；22 个 eval-only 自测 fail=0；promptfoo **39/39 passed (100%)、0 failed、0 errors**，合并后权威 eval `eval-1lR-2026-09-21T05:22:36`（Duration 4s）。
- 合并前 eval `eval-uH8-2026-09-21T05:16:59`（4s/0 error，loadavg≈28）与合并后 eval 双样本均 0 error，轮次43 provider 预算硬化在高负载下继续有效。

### 下一步

1. [x] ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 39/39、0 error），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ 已完成：#134 merged→main ca975b9，合并后 39/39 eval-1lR-2026-09-21T05:22:36，本回填 PR 即收尾。回 main 跑合并后全套回归（应 39/39、0 error），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。
2. 继续在高负载窗口观察轮次43 provider 预算硬化后 fingerprint flaky 是否消除（本轮 loadavg≈28 下 4s/0 error 为首个正面样本，需更多样本）；若仍偶发再独立 PR 取证降并发。
3. 共享底座 `_repo`(#37)/`_md_paths`(#38/#39)/文档链接面(#36 本轮扩面) 已直接钉；`_freeze_paths`（纯常量）、`prove_rmw`（恒 exit0）、`check_risk_matrix`（marker/order 重叠）维持**合理空缺**倾向，要动须先 /tmp 探针证实真实未覆盖的独有判定，不为凑数新写低价值自测。
4. 长期外部阻塞不变：ci.yml 接线需 `gh auth refresh -s workflow`（离线备份在 `~/ros2_hzj_pending/`）；CVE 修复三项待用户批准拆独立 PR；4 份飞书文档 3380004；Humble 主机解除端到端 blocked。

## 轮次 45 — 2026-09-21 17:24（Asia/Shanghai）— 修复 AGENTS.md 命令清单漏登第 13 gate + 新增操作员命令注册面自测 #40（功能 PR #136，main 2ca88ad）

### 触发与只读取证

- re-ground：`main`=`8c9bed6`=origin/main（轮次44 回填 #135 的 squash HEAD），无在途本循环 PR，工作区仅受保护 untracked 旧草稿 `docs/01-dds-request-flow.md`（未碰）。
- 探针（内联 python，import `scripts/run_all_gates` 取 `GATES`，正则解析 `AGENTS.md` 的 `## Commands` 围栏 bash 块）证实一处真实文档↔代码漂移：
  - `GATES` 13 个脚本，AGENTS.md 命令块 13 个脚本路径（`load.py` 出现 print-a/print-b 两行但折叠为一个脚本）；
  - 差集 GATES−AGENTS = `{'scripts/check_frozen_path_literals.py'}`：**第 13 gate（轮次5 加入 runner）从未登记进操作员命令清单**；
  - 反向差集 AGENTS−GATES = `{'config/env/load.py'}`（手动 print-a/print-b 命令，非 gate，属预期白名单）；
  - AGENTS 命令块所列脚本磁盘全部存在（missing=空）。
- 根因：轮次5 加第 13 gate 时 ci.yml 接线因缺 `workflow` scope 长期阻塞、CI structure 至今只硬编码枚举前 12 gate，AGENTS.md 是唯一向操作员记录完整本地集合之处却漏登；#29 只钉 scripts/ 侧 gate 注册面、#35 只钉 eval 注册面，操作员文档面零断言。

### 改动（行为不变，最小，5 文件）

1. `AGENTS.md`：Commands bash 块按 GATES 顺序在 `check_cega_bridge_hold.py` 之后、`load.py` 之前补登 `python3 scripts/check_frozen_path_literals.py`（纯文档同步，未重排既有行）。
2. 新增 `evals/agents_commands_selftest.py`（#40，eval-only、纯标准库、读真实仓库、负向全内存变异、无 tempdir）：只解析 `## Commands` 围栏 bash 块（块外散文不枚举）、取每行 `python3` 后首个 token（`load.py print-a/print-b` 折叠为一个脚本）；钉 ①每个 GATES 脚本必在块中登记、②块中所列脚本磁盘必存在、③非 gate 脚本精确等于白名单 `{config/env/load.py}`。计数 `3 negative, 2 non-flag, 1 healthy, 1 mutation`，SUCCESS_MARKER `agents commands selftest: PASS`。
3. `evals/promptfooconfig.yaml`：末尾注册 #40 case（PASS marker + 计数串），case 39→**40**。
4. `evals/README.md`：两处 #35 钉的标题计数 39→40、文件表加 #40 行（紧随 #35 注册面行）、明细表加 `| 40 |`、seed 用例长枚举句尾加 #40 片段、新增 #40 专节（倒序置于 #39 专节之前）。
5. 本日志小节。

### 评估驱动证据（先证非恒真再修复）

- 修复前实跑 #40：真实 FAIL，逐字 `gate missing from AGENTS.md Commands block: scripts/check_frozen_path_literals.py`（exit 1），证明检查 live、确实抓到漂移；补登 AGENTS.md 后 PASS（13 gates documented、14 listed commands、0 problems）。
- 负向/non-flag/变异全过：删真实 gate 行、注入未登记新 gate、列入磁盘缺失脚本必报；load.py 带参折叠为一个白名单项、块外散文 python3 不枚举；exists 包装把 prove_rmw.py 判失必报。

### 分数前后对比

| 项 | 轮次44 | 轮次45 |
|---|---|---|
| gate | 13/13 | **13/13** all gates green |
| stdout 指纹 | 15/15 stable | **15/15 stable**（#40 不在 15 个指纹命令内，fixtures 未改） |
| eval-only 自测 | 22 个 fail=0 | **23 个 fail=0**（新增 #40） |
| promptfoo | 39/39 | **40/40 passed (100%)、0 failed、0 errors**，合并前 eval `eval-bBE-2026-09-21T09:24:06`（Duration 4s，loadavg 高负载窗口仍 0 error） |
| compileall | OK | OK |
| #35 注册面 | PASS | PASS（磁盘 23 selftest ↔ yaml 40 script ↔ 40 case ↔ README 40 全一致） |

### 产物检查

- `python3 -m compileall -q evals scripts config/env dimos_bridge/dual_chain_env.py` 通过；
- #36 doc_link 自测在 AGENTS.md 被纳入扫描后仍 PASS（新增行无链接，0 broken）；
- yaml 权威计数（#35 正则）cases=40、scripts=40；磁盘 `*_selftest.py`=23；
- 改动仅限 AGENTS.md、evals/agents_commands_selftest.py、evals/promptfooconfig.yaml、evals/README.md、本日志；未改任何 gate 代码/fixtures/ci.yml/被扫文档正文。

### Hold 合规

未编辑 config/fastdds.xml、未改 SCOREBOARD 数字；未启用 Agnocast/zenoh；未改 dimos_bridge DDS 行为/vendor 源码/shell 包装；未集成 Cega、未重写 Bridge runtime；新 eval 纯标准库 + 读真实仓库/内存变异，不新增运行时依赖、不在树内建 fixture、不跑不受信代码；promptfoo 仅 npx 缓存运行；旧草稿未跟踪未提交。

### 剩余风险

- ci.yml 的 structure job 仍只硬编码前 12 gate（#40 与第 13 gate 一样不被 CI 枚举），根因是 active 账号缺 `workflow` scope，需用户本机 `gh auth refresh -h github.com -s workflow` 后用离线备份补独立 PR；本轮只修操作员文档面与本地 eval，未触碰 ci.yml。
- #40 的白名单是**精确集合** `{config/env/load.py}`：未来若确需在 Commands 块新增其他手动非 gate 命令，需同步改白名单（这是有意的防杂项累积设计）。
- 本机无 Humble runtime，真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`，未伪造。

### 合并后权威回归（main 2ca88ad，PR #136 squash-merge）

- 功能 PR #136（分支 test/agents-commands-registry，commit d640718，5 files +291/−3：AGENTS.md 补 1 行、新增 agents_commands_selftest.py、yaml +17、README +18/−3、日志）required 三检 structure/contracts/boundary 全 pass、CodeQL 与 Analyze(actions/js/python) 全 pass、Cursor Approval APPROVED（1m16s）→ squash-merge，main `2ca88ad8cd1b2001ec727f5cc67e00ebf320388b`，远端分支已删。
- 回 main 同步后回归：gate **13/13** all gates green；stdout 指纹 **15/15 stable**；**23 个** eval-only 自测 fail=0；promptfoo **40/40 passed (100%)、0 failed、0 errors**，合并后权威 eval `eval-mRA-2026-09-21T09:32:15`（Duration 4s）。
- 合并前 eval `eval-bBE-2026-09-21T09:24:06`（4s/0 error）与合并后 eval 双样本均 0 error，轮次43 provider 预算硬化在高负载窗口继续有效（连续正面样本）。

### 下一步

1. [x] ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 40/40、0 error），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ 已完成：#136 merged→main 2ca88ad，合并后 40/40 eval-mRA-2026-09-21T09:32:15，本回填 PR 即收尾。回 main 跑合并后全套回归（应 40/40、0 error），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。
2. 继续在高负载窗口收集轮次43 provider 预算硬化后 fingerprint 0-error 样本（本轮 loadavg 高负载仍 4s/0 error，为又一正面样本）。
3. `prove_rmw`/`check_risk_matrix`/`_freeze_paths` 维持合理空缺倾向，须先 /tmp 探针证实独有未覆盖判定分支才新增自测，不为凑数。
4. 外部阻塞不变：workflow scope（ci.yml 接线）、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 46 — 2026-09-21 18:17（Asia/Shanghai）— risk-matrix §9.4 Hold guard 负向自测 #41（功能 PR #138，main c26401b）

### 只读取证（先排查、不为凑数造测试）

- **gate 计数"12/13"表述面排查（轮次45 自然延续）**：全仓 grep A 面（排除 vendor/artifacts/.git）"12/13 gate"表述，分类结论——
  - `docs/testing/2026-09-mac-hil.md:25/27` 的"12 个 gate / 12/12"是 **2026-09-19 带日期的实测分诊报告**，当天第 13 gate 尚未随本循环落地，写 12 是**准确历史证据**，改数字即篡改历史 → 不改；
  - `docs/eval/2026-09-loop.md:5/18` 的"12 个 gate"是迭代0 方法论**历史快照** → 不改；
  - `docs/architecture/ci-cd-gates.md:139-144`、`docs/refactor/01-dds-request-flow.md`、`evals/*` 里的"12/twelve"均**准确描述 CI structure 仍只枚举前 12 gate**（第 13 gate ci.yml 接线受 workflow scope 阻塞）→ 不改；
  - 结论：gate 计数面**无真实漂移可修**，不制造无意义文档提交。
- **三个长期"合理空缺"候选探针**：
  - `scripts/_freeze_paths.py`（26 行）：纯常量（2 Path + 2 字符串），无函数无分支，其消费已由 #18 frozen guard 钉 → **确认合理空缺**；
  - `scripts/prove_rmw.py`（222 行）：恒 exit0 的信息打印器（设计如此），本机完整 stdout 已被 #17 指纹逐字节钉、伪造环境诚实文案被 mac-hil 用例2 钉；未覆盖分支（找到 .so 的 loaded/identifier-unavailable 渲染态）在无 ROS 机恒不触发且非 PASS/FAIL 裁决，造假日录树价值低 → **维持空缺**；
  - `scripts/check_risk_matrix.py`（139 行）：是 13 gate 中少数**无专属负向自测、却会 exit1** 的文档 guard，且源码 line 42-47 有作者明确注释的**反缩写契约**——矩阵必须逐 token 含 `《3》《4》《5》《6》`，裸 `《3》–《6》` 区间不得替代缺失项；正向 gate 证明不了它被削弱时 fail-closed → **选定为本轮目标**。

### 改动（行为不变，4 文件，eval-only）

1. 新增 `evals/risk_matrix_guard_selftest.py`（#41，纯标准库、tempdir-only、读真实仓库）：把 guard 实读的 8 个文件（6 份内容文档 + 只读 fastdds.xml / SCOREBOARD.md）**复制进 temp 树**后逐树变异，经可注入的 `render(root=...)` 驱动，绝不写仓库/不改两个冻结文件。
   - **3 negative**：N1 删矩阵独立 `《4》`、保留 `《3》–《6》` 区间 → exit1 逐字 `FAIL markers ... (need 《4》)`（钉反缩写契约）；N2 删 R0 必需文件 → exit1 `FAIL missing`；N3 ADR 去 `§9.4` → exit1（钉 marker 逐文件强制）；
   - **2 non-flag（双向）**：SCOREBOARD 副本仅留 `STATUS`（无数字）、fastdds.xml 副本仅留 `<domainId>42</domainId>`，两棵最小锚点树都 exit0——钉死冻结文件"只验存在/最小锚点、不读数字/不读其余内容"的 Hold 边界；
   - **2 healthy**：真实仓 `render()` 与纯复制 temp 树都 exit0 含 `Risk matrix healthy`；
   - **1 mutation**：模块级 `read_utf8` 换成对矩阵总返回未篡改原文的盲桩 → N1 漏报成 exit0，恢复后重新 exit1。计数串 `3 negative, 2 non-flag, 2 healthy, 1 mutation`。
2. `evals/promptfooconfig.yaml`：注册 #41，case **40→41**（cases=41、scripts=41）。
3. `evals/README.md`：两处标题计数 40→41、文件表新增行、明细表 #41、seed 用例长枚举句尾新增 #41 片段、新增 #41 专节（倒序置于 #40 专节之前）。
4. 本日志小节。

### 评估驱动证据（先证非恒真）

- N1 在真实 guard 上独立复现：code=1，逐字 `- **FAIL markers:** `docs/architecture/feishu-risk-matrix.md` (need 《4》)`；
- 新脚本未注册时 #35 注册面自测真实 FAIL：`orphan self-test on disk not registered in yaml: risk_matrix_guard_selftest.py`，注册后转 PASS（证明注册面 live）；
- #41 自测自身：`negative 3/3、non-flag 2/2、healthy 2/2、mutation 1/1` PASS。

### 实测（本机 macOS，2026-09-21 18:17 CST）

- `python3 -m compileall evals scripts config/env dimos_bridge/dual_chain_env.py`：OK；
- `python3 scripts/run_all_gates.py`：**13/13 all gates green**；
- `python3 evals/fingerprint_check.py`：**15/15 stable**（#41 不在 15 个指纹命令内，fixtures 零改动）；
- eval-only 自测：**24 个 fail=0**（23→24，新增 #41）；#35 注册面 PASS（磁盘 24 selftest ↔ yaml 41 script ↔ 41 case ↔ README 41 一致）；#36 doc_link PASS（README 新增锚点/专节无断链）；
- `npx promptfoo@0.123.1 eval`：**41/41 passed (100%)、0 failed、0 errors**，合并前 eval `eval-9KB-2026-09-21T10:17:10`（Duration 4s，高负载窗口 0 error，轮次43 provider 预算硬化继续有效）。

### 合并后权威回归（main `c26401b`）

- 功能 PR #138（分支 test/risk-matrix-guard-selftest，commit 2dd55c6，4 files +370/−3：新增 risk_matrix_guard_selftest.py 279 行、yaml +17、README +19/−3、日志 +58）required 三检 structure/contracts/boundary 全 pass、CodeQL 与 Analyze(actions/js/python) 全 pass、Cursor Approval APPROVED（1m17s）→ squash-merge，mergeCommit `c26401b2e82a314e684aacabccd7ded8745f02a7`，远端分支已删。
- 回 main 同步后回归：compileall OK；gate **13/13** all gates green；stdout 指纹 **15/15 stable**；**24 个** eval-only 自测 fail=0；promptfoo **41/41 passed (100%)、0 failed、0 errors**，合并后权威 eval `eval-41F-2026-09-21T10:23:53`（Duration 5s）。
- 合并前 eval `eval-9KB-2026-09-21T10:17:10`（4s/0 error）与合并后 eval 双样本均 0 error，轮次43 provider 预算硬化在高负载窗口继续有效。

### Hold 合规

未编辑 config/fastdds.xml（仅在 tempdir 放其内容副本，原文件只读未改）、未改 SCOREBOARD 数字（同上，tempdir 副本）；未启用 Agnocast/zenoh；未改 dimos_bridge DDS 行为/vendor/shell 包装；未集成 Cega、未重写 Bridge runtime；未碰 ci.yml / 任何 gate 代码 / 15 个指纹 fixtures；新 eval 纯标准库 + tempdir/内存变异，不新增运行时依赖、不在树内建 fixture、不跑不受信代码；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（纯新增 eval-only 自测 + 文档），runner/gate/公共 API/fixtures 零改动。
- N1 依赖矩阵文档当前 `《4》` 仅 1 次独立出现；若未来文档改写使区间与独立 token 合并，自测健康树 H2 会先红（夹具有效性保护），需同步评估而非改测试放水。
- `prove_rmw` 找到 .so 的渲染态、真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 ROS Humble runtime），未伪造。

### 下一步

1. [x] ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 41/41、0 error），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ 已完成：#138 merged→main c26401b，合并后 41/41 eval-41F-2026-09-21T10:23:53，本回填 PR 即收尾。
2. 剩余无专属负向自测、会 exit1 的文档 guard 候选：`check_dual_chain_baseline.md` 指针检查（先探针确认是否有独有判定，还是与 #19/#32/#34 双链族重复）；同样须先 /tmp 探针证实独有未覆盖分支才新增，不为凑数。
3. 继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本。
4. 外部阻塞不变：workflow scope（ci.yml 接线 + 把纯 python 指纹/selftest 纳入 CI）、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 47 — 2026-09-22 18:28（Asia/Shanghai）— dual-chain baseline 文档/指针面负向自测 #42（功能 PR #141，main aa43c78）

### 只读取证（先判重复、不为凑数造测试）

- 接续轮次46 下一步第 2 条，探针 `scripts/check_dual_chain_baseline.py`（475 行，最大的文档 guard 之一）是否有区别于双链族（#19/#32/#34）的独有未覆盖判定。
- 读 `evals/dual_chain_env_guard_selftest.py`（#19）确认覆盖面：它钉的是该 guard 的 **env/shell/wrapper 交叉面**（load.py 单一真源 ↔ chain_a.sh/chain_b.sh 字面 export ↔ 薄包装、chain_b.sh `unset CYCLONEDDS_URI`），且**刻意建缺文档的 temp 树、只断言 5 个 `FAIL env|chain` 行族、明确忽略文档失败**。#32 钉 load.py 本体、#34 钉薄包装。
- 因此该 guard 的**文档/指针面长期无负向自测**，且含 #19 不碰的独有判定：
  - 9 个必需文件 + 逐文件 marker（baseline 26 个 marker、ADR §13(3) 4 个、R0/MAP/SWAP）；
  - baseline 文档里**独立于 marker 元组**的 paused 连续短语（`same-topology XML tuning is paused` 不在 `_BASELINE_MARKERS` 内，单独 `FAIL paused`）；
  - **禁止伪造预订分位数的反伪造正则** `_PERCENTILE_RE`（独立 p50/p90/p95/p99 或 “Nth percentile” → `FAIL percentiles`，中文旁 token 经 ASCII lookaround 也命中，政策词“分位数”允许）——这是全仓独有、其他自测都没有的反伪造分支；
  - fastdds.xml / SCOREBOARD 在本 guard **仅 existence-only**（docstring 明示内容冻结归 `boundary` job）。
- /tmp 探针（完整复制 guard 实读的 11 个文件进 tempdir）证实：纯复制树 code=0（env 面在复制树保持绿，夹具可行）；删 paused 仅 `FAIL paused`；追加 `measured p99 = 1.2 ms` 仅 `FAIL percentiles`；ADR 删 `不重写 XML` 仅点名 ADR `FAIL markers`；删 Unitree swap 文档 `FAIL missing`；空 SCOREBOARD 与改成 `<domainId>99</domainId>` 的 XML 均 code=0；把 `_PERCENTILE_RE` 换成永不匹配正则后伪造 p99 漏报成 code=0、恢复后重新 code=1。结论：独有判定成立、与 #19 互补不重复 → 选定。

### 改动（行为不变，4 文件，eval-only）

1. 新增 `evals/dual_chain_baseline_doc_selftest.py`（#42，纯标准库、tempdir-only）：把 guard 实读的 **11 个文件**（9 个 required + `config/env/load.py` + 薄包装，保持相对路径）完整复制进 tempdir，使 env 交叉面保持绿、文档变异是唯一变量，经可注入 `render(root=...)` 驱动。
   - **4 negative**：N1 删 paused 短语 → 仅 `FAIL paused`（断言不连带 marker/percentile）；N2 注入 p99 → 仅 `FAIL percentiles`；N3 ADR 删 `不重写 XML` → 仅点名 ADR 的 `FAIL markers`、健康 baseline 不误报；N4 删 Unitree swap 文档 → `FAIL missing`；
   - **2 non-flag（existence-only 双向）**：SCOREBOARD 副本清空、fastdds.xml 副本改成 `<domainId>99</domainId>`，两棵树都必须 exit0 且无 `- **FAIL` 行；
   - **2 healthy**：真实仓 `render()` 与纯复制 temp 树都 exit0 且含两个 success marker（健康判定用行前缀 `- **FAIL`，避开固定文案里的 “drop-in FAIL” 字样）；
   - **1 mutation**：盲 `_PERCENTILE_RE` 让伪造 p99 漏报成 exit0，恢复后重新 exit1（finally 必恢复）。计数串 `4 negative, 2 non-flag, 2 healthy, 1 mutation`。
2. `evals/promptfooconfig.yaml`：注册 #42，case **41→42**（cases=42、scripts=42）。
3. `evals/README.md`：两处标题计数 41→42、文件表新增行、明细表 #42、seed 用例长枚举句尾新增 #42 片段、新增 #42 专节（倒序置于 #41 专节之前）。
4. 本日志小节。

### 评估驱动证据（先证非恒真）

- 新脚本未注册时 #35 注册面自测真实 FAIL：`orphan self-test on disk not registered in yaml: dual_chain_baseline_doc_selftest.py`，注册后转 PASS（注册后一度报 README 计数 41 != yaml 42，更新 README 后 PASS，证明计数断言 live）；
- N2 在真实 guard 上独立复现 code=1，逐字 `- **FAIL percentiles:** do not invent booked pNN tokens`；
- #42 自测自身：`negative 4/4、non-flag 2/2、healthy 2/2、mutation 1/1` PASS；与 #19 无重叠（#19 钉 env 面、本项钉文档面）。

### 实测（本机 macOS，2026-09-22 18:28 CST）

- `python3 -m compileall evals scripts config/env dimos_bridge/dual_chain_env.py`：OK；
- `python3 scripts/run_all_gates.py`：**13/13 all gates green**；
- `python3 evals/fingerprint_check.py`：**15/15 stable**（#42 不在 15 个指纹命令内，fixtures 零改动）；
- eval-only 自测：**25 个 fail=0**（24→25，新增 #42）；#35 注册面 PASS（磁盘 25 selftest ↔ yaml 42 script ↔ 42 case ↔ README 42 一致）；#36 doc_link PASS（README 新增锚点/专节无断链）；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-FOo-2026-09-22T10:28:01`（Duration 4s，高负载窗口 0 error，轮次43 provider 预算硬化继续有效）。

### 合并后权威回归（main aa43c78，功能 PR #141）

- required checks `structure` / `contracts` / `boundary` 均 success（gh api 核实合并 commit aa43c78 的 check-runs），CodeQL（actions / python / javascript-typescript + 聚合）pass，Cursor Approval pass（1m21s）；squash merge main `aa43c787a7df40e5496598c34c132fa24de1aba5`，远端分支已删。
- 回 main 重跑：compileall OK、`run_all_gates.py` 13/13 all gates green、`fingerprint_check.py` 15/15 stable、25 个 eval-only selftest fail=0。
- promptfoo 合并后权威回归：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-Isu-2026-09-22T10:41:35`（Duration 4s，concurrency 4）。

### Hold 合规

未编辑 config/fastdds.xml（仅在 tempdir 放内容副本并改成 domainId 99 验证 existence-only，原文件只读未改）、未改 SCOREBOARD 数字（tempdir 副本清空）；未启用 Agnocast/zenoh；未改 dimos_bridge DDS 行为/vendor/shell 包装（wrapper 与 load.py 仅复制进 tempdir 读取）；未集成 Cega、未重写 Bridge runtime；未碰 ci.yml / 任何 gate 代码 / 15 个指纹 fixtures；新 eval 纯标准库 + tempdir/内存变异，不新增运行时依赖、不在树内建 fixture、不跑不受信代码；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（纯新增 eval-only 自测 + 文档），runner/gate/公共 API/fixtures 零改动。
- N2 依赖 baseline 文档当前不含任何独立 pNN token（健康树 H1/H2 守护）；若未来确需引用真实预订分位数，应先解除 blocked 取到实测数据并同步更新 guard 策略，而非改测试放水。
- 13 个 gate 中 `prove_rmw`（恒 exit0，#17 指纹 + mac-hil 已钉）维持合理空缺；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 ROS Humble runtime），未伪造。

### 下一步

1. [x] ~~本功能 PR 合并后：回 main 跑合并后全套回归（应 42/42、0 error），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。~~ 已完成：#141 merged→main aa43c78，合并后 42/42 eval-Isu-2026-09-22T10:41:35，本回填 PR 即收尾。
2. 13 gate 的负向自测覆盖已基本闭合（仅 prove_rmw 维持合理空缺）；后续深化方向转向**断言质量**：复查各 selftest 的 non-flag/healthy 是否仍有盲区、跨 guard 共享 fixture（tempdir 复制真实文件）是否值得抽公共 helper（仅在出现第三处重复时再抽，避免过早抽象）。
3. 继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本。
4. 外部阻塞不变：workflow scope（ci.yml 接线 + 把纯 python 指纹/selftest 纳入 CI）、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 48 — 2026-09-22 19:18（Asia/Shanghai）— 加强 #42 百分位反伪造断言：CJK 紧邻 / p95 / 政策词放行（功能 PR #144，main c956d7a）

### 只读取证（断言质量复查，不新增 case）

- 接续轮次47 下一步第 2 条，本轮转向**断言质量**而非铺新用例。先对 25 个 `evals/*_selftest.py` 做模式 inventory（行数 / tempfile / 是否复制真实文件 / render 注入 / seed helper）。
- **公共 helper 抽取判定**：完整复制真实 required 文件集 + edits/drop 变异的 seed 模式只有 #41 `risk_matrix_guard`（复制 8 文件）与 #42 `dual_chain_baseline_doc`（复制 11 文件）两处，其余 guard 的 seed 多为各自合成内容、结构差异大。按轮次47 自定的“出现第三处重复再抽 helper、避免过早抽象”，本轮**不抽**公共 helper。
- **真实盲区**：复查 #42 的百分位反伪造分支发现 3 个未钉边界——轮次47 的 N2 只测了英文带 ASCII 空格的 `measured p99`，未验证：(a) guard 注释明确声称的“中文紧邻 token（如 `链A的p99`，lookbehind 前是 CJK 字符）经 ASCII 字符类 lookaround 仍命中”；(b) 字符类覆盖 p50/p90/p95/p99 而非只 p99（若正则被收窄成 p99-only，p95 漏报无人捕获）；(c) 双向契约的放行侧——政策词“分位数”不带裸 pNN 数字时必须绿（若未来正则被过度收紧到禁“分位数”，无人捕获）。
- /tmp 探针（只变异 baseline、其余 10 文件原样复制）：追加 `链A的p99约1.2ms` → code1 仅 `FAIL percentiles`；追加 `measured p95 = 0.4 ms` → code1 仅 `FAIL percentiles`；追加纯政策词句（无 pNN 数字）→ code0 无 FAIL；纯复制树 code0。（首次探针误把变异文本追加到全部文件、污染 load.py 引出 `FAIL env truth`，修正为只对 baseline 变异后结论干净，记录为夹具教训。）

### 改动（行为不变，3 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`（#42）：新增 **N5**（中文紧邻 `链A的p99约1.2ms` → `FAIL percentiles` 且不连带 paused/markers，钉 CJK lookaround）、**N6**（裸 `p95` → `FAIL percentiles`，钉字符类非 p99-only）、**NF3**（仅含政策词“分位数”、无裸 pNN 的句子 → exit0 无 FAIL，钉放行侧双向契约）；计数 **4→6 negative、2→3 non-flag**（2 healthy、1 mutation 不变），同步 docstring 与末行计数串 `6 negative, 3 non-flag, 2 healthy, 1 mutation`。
2. `evals/promptfooconfig.yaml`：更新 #42 的 description（补 CJK 紧邻 / p95 / 政策词）与计数 value；cases=42、scripts=42 不变。
3. `evals/README.md`：#42 专节 negative/non-flag bullet、明细表 #42 行、文件表行同步新边界（两处标题计数仍 42，因未增减 case）。
4. 本日志小节。

### 评估驱动证据

- 三条新边界先在真实 guard 上 /tmp 探针逐字取证（N5/N6 code1 且仅 `FAIL percentiles`、NF3 code0），再写进自测；脚本运行 PASS 且计数串更新；
- 该族断言非恒真由轮次47 的 mutation（盲 `_PERCENTILE_RE` 漏报 N2）已证；本轮 N5/N6/NF3 与 N2 同构、探针直接取自真实 guard 输出；
- 不新增 case、不改 gate 代码 / fixtures / runner，纯加强既有 #42 的判别宽度。

### 实测（本机 macOS，2026-09-22 19:18 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-qt2-2026-09-22T11:17:51`（Duration 4s，高负载窗口 0 error）。

### 合并后权威回归（main c956d7a）

- 功能 PR #144（分支 test/dcb-doc-percentile-bounds，commit 4bfd0b2，4 files +98/−9）required 三检 structure/contracts/boundary 均 success、CodeQL pass、Cursor Approval pass（1m41s）→ squash 合并 main **c956d7ac55be503bbcb9e1cc6ac5927a95cb0eef**（远端分支已删）。
- 合并后回 main（ff-only）权威回归：`run_all_gates.py` **13/13 all gates green**、`fingerprint_check.py` **15/15 stable**、25 个 selftest fail=0；`npx promptfoo@0.123.1 eval` **42/42 passed (100%)、0 failed、0 errors**，合并后权威 eval `eval-O3Q-2026-09-22T11:24:08`（Duration 4s，高负载窗口 0 error）。
- 合并 commit c956d7a 的 required 三检经 `gh api .../check-runs` 核实均 success。
- 合并前 eval `eval-qt2-2026-09-22T11:17:51`（42/42）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh；未改 dimos_bridge/vendor/shell/load.py（仅复制进 tempdir 读取）；未集成 Cega、未重写 Bridge runtime；未碰 ci.yml / gate 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），runner/gate/公共 API/fixtures 零改动；case 数不变（42）。
- 断言质量复查为渐进工作：本轮只深化了 #42；其余 selftest 的 non-flag/healthy 盲区待后续逐轮用同样“先探针证盲区、再加强”的方式推进，不为凑数改断言。
- `prove_rmw` 维持合理空缺；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #144 已合并 main c956d7a；合并后权威回归 42/42、0 error（eval `eval-O3Q-2026-09-22T11:24:08`），本回填 PR 补齐 PR 号 / main HEAD / eval ID。
2. 断言质量复查继续：下一轮按 inventory 挑第二个 selftest（候选 `unitree_swap_guard` / `three_chain_repro_guard` 的 non-flag 放行侧）做盲区探针，证据成立才加强；公共 tempdir 复制 helper 仍等第三处重复。
3. 继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 49 — 2026-09-22 20:17（Asia/Shanghai）— 给 #20 unitree swap guard 补 existence-only non-flag 放行断言（功能 PR #146，main 2eac0e0）

### 只读取证（断言质量复查第二个 selftest）

- 接续轮次48 下一步第 2 条，本轮复查 `unitree_swap_guard_selftest.py`（#20，276 行）。读 `scripts/check_unitree_cyclone_swap.py`（206 行）逐分支对照：guard 的 FAIL 面有 verdict / quote / VERSIONS SHA row / CMake project() / swap-doc markers / missing，#20 的 5 negative（N1–N5）+ 1 mutation（CMake 正则放宽）已覆盖篡改/删除面，**但完全没有 non-flag 放行侧**。
- 真实盲区：guard 把 `config/fastdds.xml` 与 `docs/artifacts/bench/SCOREBOARD.md` 列为 required 但 markers 为空（docstring 明示 existence-only、内容冻结归 boundary job）。#20 没有任何场景证明“这两个文件内容被任意改写时本 guard 仍保持绿”——若未来有人在该 guard 里加内容校验（越界读 XML/SCOREBOARD），现有 5 negative/2 healthy/1 mutation 全绿却无人捕获。
- /tmp 探针（复制 guard 实读的 5 个真实文件进 tempdir）：SCOREBOARD 副本清空 → code0、无 FAIL 行、两文件仍 `ok file`；fastdds.xml 副本改成 `<domainId>99</domainId>` → code0、无 FAIL；控制组删除 XML → code1 `FAIL missing`（证明 existence 仍被检查，non-flag 只放行内容、不放行缺失）。

### 改动（行为不变，3 文件，eval-only，case 数不变仍 42）

1. `evals/unitree_swap_guard_selftest.py`（#20）：新增 `_check_nonflags()` 与 **NF1**（SCOREBOARD 副本清空 → exit0 + marker + 无 FAIL 行）、**NF2**（fastdds.xml 副本改成 domainId 99 的任意内容 → exit0 + marker + 无 FAIL 行）；计数由 `5 negative, 2 healthy, 1 mutation` 扩为 **`5 negative, 2 non-flag, 2 healthy, 1 mutation`**；同步汇总行与 docstring 断言枚举（新增第 2 点 non-flag，原 healthy/mutation 顺延为 3/4）。
2. `evals/promptfooconfig.yaml`：更新 #20 description（补 existence-only 放行）与计数 value；该计数串在 yaml 出现 2 次（#20 与 #25 runtime），按 unitree 块整段上下文精确替换、#25 保持不变；cases=42、scripts=42。
3. `evals/README.md`：#20 文件表行、明细表行、专节（在 N5 与健康对照之间插入 non-flag bullet）同步；两处标题计数仍 42。
4. 本日志小节。

### 评估驱动证据

- NF1/NF2 先在真实 guard 上 /tmp 探针逐字取证（空 SCOREBOARD / bogus XML 均 code0、删文件 code1），再写进自测；
- non-flag 断言要求 code0 + success marker + 无 `- **FAIL` 行，与 #42 NF1/NF2 同构；控制组（删 XML FAIL missing）证明它放行的是“内容”而非“缺失”，非恒真；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #20 的放行侧判别；公共 tempdir 复制 helper 仍只 #41/#42 两处，本轮 unitree 是第三处“复制真实文件”但结构（5 文件、`_seed_tree`+`_mutate`+`_remove`）与前两处差异明显，仍不抽 helper。

### 实测（本机 macOS，2026-09-22 20:17 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-gN8-2026-09-22T12:17:40`（Duration 4s，0 error）。

### 合并后权威回归（main 2eac0e0，功能 PR #146 squash 合并）

- 功能 PR #146（分支 test/unitree-swap-existence-nonflag，commit 6038e04，4 files +109/−8）required 三检 structure/contracts/boundary 均 success、CodeQL 四检 pass、Cursor Approval pass（1m20s）→ squash 合并 main `2eac0e0d291b32cc6bf531531985ada6e3c27b62`，远端分支已删；gh api 核实合并 commit 三检 success。
- 回 main pull 后权威回归：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0。
- 合并后权威 `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-LRs-2026-09-22T12:24:40`（Duration 4s，0 error）。


### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh；未改 dimos_bridge/vendor/shell/load.py（vendor/CycloneDDS/CMakeLists.txt、vendor/VERSIONS.md 仅复制进 tempdir 读取）；未集成 Cega、未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- #20 的 swap-doc 18-marker 元组里，合法 external 路径两个 marker（`unitree_sdk2_hzj`、`UNITREE_DDS_PROVIDER=external`）目前只走通用 marker 检查、尚无专门负向场景（删其一应 FAIL markers 且独立检查仍 ok），可作后续断言深化候选；本轮聚焦 non-flag 放行侧，不堆叠。
- 断言质量复查仍渐进：three_chain_repro_guard 等待后续同类探针；`prove_rmw` 维持合理空缺；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #146 已 squash 合并 main 2eac0e0；合并后权威回归 42/42、0 error（eval `eval-LRs-2026-09-22T12:24:40`），PR 号 / main HEAD / eval ID 已回填本小节。
2. 断言质量复查继续：下一轮候选 three_chain_repro_guard 的 non-flag 放行侧，或给 #20 补 external 合法路径 marker 的专门负向场景；均先探针证盲区再加强；公共 tempdir 复制 helper 仍等真正同构的第三处。
3. 继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 50 — 2026-09-22 21:11（Asia/Shanghai）— 给 #27 three-chain repro guard 补 existence-only non-flag 放行断言（功能 PR #148，main 6d2ca0f）

### 只读取证（断言质量复查第三个 selftest）

- 接续轮次49 下一步，本轮复查 `three_chain_repro_guard_selftest.py`（#27）。读 `scripts/check_three_chain_repro.py`（217 行）逐分支对照：#27 已有 2 negative（N1 追加裸 `map = reproduce`、N2 追加 `three-chain repro: PROVEN`）、1 non-flag（同行禁止句「不要把 map = reproduce…」豁免）、2 healthy、1 mutation（map=reproduce 正则 neuter 即漏报）。
- 真实盲区（与轮次49 unitree 对称）：guard 把 `config/fastdds.xml`、`docs/artifacts/bench/SCOREBOARD.md` 列为 required 但 markers 为空（行 127–128，docstring 明示 existence-only、内容冻结归 boundary）。#27 复制了这 6 个真实文件，却只钉了 repro 文档的禁止句豁免，**没有任何场景证明这两个 existence-only 文件内容被任意改写时 guard 仍绿**——若未来在该 guard 越界加 XML/SCOREBOARD 内容校验，现有断言全绿却无人捕获。
- /tmp 探针（复制 6 个真实文件进 tempdir）：SCOREBOARD 副本清空 → code0、无 FAIL 行；fastdds.xml 副本改成 `<domainId>99</domainId>` → code0、无 FAIL；控制组删除 XML → code1 `FAIL missing`（证明 existence 仍被检查，non-flag 只放行内容、不放行缺失）。

### 改动（行为不变，3 文件，eval-only，case 数不变仍 42）

1. `evals/three_chain_repro_guard_selftest.py`（#27）：新增 `_check_existence_nonflags()` 与 **NF1**（SCOREBOARD 副本清空 → exit0 + marker + 无 FAIL 行）、**NF2**（fastdds.xml 副本改成 domainId 99 的任意内容 → exit0 + marker + 无 FAIL 行）；原禁止句豁免 non-flag 保留为 1 个，non-flag 合计 1→3，计数由 `2 negative, 1 non-flag, 2 healthy, 1 mutation` 扩为 **`2 negative, 3 non-flag, 2 healthy, 1 mutation`**；汇总行新增 `existence-only content green: 2/2`；同步 docstring 断言枚举第 2 点（1 豁免 + 2 existence-only）。
2. `evals/promptfooconfig.yaml`：更新 #27 description（补 existence-only 放行）与计数 value；该计数串在 yaml 出现 3 次（#27/#28/#29 同形），按 #27 块整段上下文精确替换、#28/#29 保持不变；cases=42、scripts=42。
3. `evals/README.md`：#27 文件表行、明细表行、专节（原「1 个 non-flag（豁免契约）」扩为「3 个 non-flag：①豁免 ②③existence-only」）同步；两处标题计数仍 42。
4. 本日志小节。

### 评估驱动证据

- NF1/NF2 先在真实 guard 上 /tmp 探针逐字取证（空 SCOREBOARD / bogus XML 均 code0、删文件 code1），再写进自测；
- existence non-flag 断言要求 code0 + success marker + 无 `- **FAIL` 行，与 #20/#42 的 existence-only NF 同构；控制组（删 XML FAIL missing）证明放行的是“内容”而非“缺失”，非恒真；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #27 的放行侧判别；至此 #20/#27/#42 三个“复制真实文件 + existence-only XML/SCOREBOARD”的 selftest 都钉了同一放行契约（公共 tempdir 复制 helper 仍因 seed 签名不同而不抽）。

### 实测（本机 macOS，2026-09-22 21:11 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-Ma1-2026-09-22T13:11:28`（Duration 4s，0 error）。

### 合并后权威回归（功能 PR #148 已 squash-merge）

- 功能 PR #148（分支 test/three-chain-existence-nonflag，commit 8f9b071，4 files +109/−10）required 三检 + CodeQL + Cursor Approval(1m28s) 全 pass，squash-merge 到 main，mergeCommit `6d2ca0fd08223ba43a747ccf5d483804fb22616f`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `6d2ca0f`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-mJb-2026-09-22T13:19:47`（Duration 5s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh；未改 dimos_bridge/vendor/shell/load.py（4 个内容文档 + vendor 文件仅复制进 tempdir 读取）；未集成 Cega、未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- existence-only non-flag 模式现已在 #20/#27/#42 三处重复（各 guard 的 required 文件集与 seed 签名仍不同）；是否抽公共“existence-only 放行”小 helper 可在第四处出现或签名趋同后再评估，本轮不抽（避免过早抽象）。
- #20 的合法 external 路径 marker（`unitree_sdk2_hzj`、`UNITREE_DDS_PROVIDER=external`）仍只走通用 marker 检查、无专门负向场景，留作候选；`prove_rmw` 维持合理空缺；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #148 已合并（main `6d2ca0f`），合并后权威回归 42/42、0 error（eval `eval-mJb-2026-09-22T13:19:47`），本回填 PR 即补登。
2. 断言质量复查继续：候选给 #20 补 external 合法路径 marker 的专门负向场景（删其一应 FAIL markers 且独立检查仍 ok），或对其余复制真实文件型 selftest（#41 risk_matrix）做 existence-only/放行侧盲区探针；均先探针证盲区再加强。
3. existence-only 放行 helper 等第四处或签名趋同；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 51 — 2026-09-22 22:21（Asia/Shanghai）— 给 #20 unitree guard 补合法 external 路径 marker 删除负向场景（功能 PR #150，main 13c6323）

### 只读取证（断言质量复查，接续轮次50 下一步候选 a）

- 读 `scripts/check_unitree_cyclone_swap.py`（206 行）与 `evals/unitree_swap_guard_selftest.py`（轮次49 后含 NF1/NF2）逐分支对照：#20 原有 5 negative（N1 裁决句翻转→FAIL verdict、N2 引文 0.10.2 篡改→FAIL quote、N3 vendor SHA 行篡改→FAIL VERSIONS row、N4 CMake project() VERSION 篡改→FAIL CMake project()、N5 删交换文档→FAIL missing）、2 non-flag（existence-only NF1/NF2）、2 healthy、1 mutation（CMake 正则改宽即漏报 N4）。
- 真实盲区：guard docstring 与安全契约把「唯一合法替换路径 = `unitree_sdk2_hzj` + opt-in `UNITREE_DDS_PROVIDER=external`」列为关键结论，这两个 marker 走通用 18-marker substring 元组（guard 行 56–57），缺失会 FAIL markers 并点名；但 #20 的 5 个 negative **没有任何一个删除这两个合法路径 marker**。若未来有人把它们从 `_SWAP_MARKERS` 元组里「简化」掉，删除文档里的合法路径就不再报 FAIL，现有断言全绿、安全契约悄悄丢失。
- /tmp 探针（复制 5 个真实文件进 tempdir，真实交换文档中 `UNITREE_DDS_PROVIDER=external` 出现 5 次、`unitree_sdk2_hzj` 出现 11 次）：删前者 → code1 `FAIL markers (need UNITREE_DDS_PROVIDER=external)`；删后者 → code1 `FAIL markers (need unitree_sdk2_hzj)`；两者均不连带——`ok quoted 0.10.2`、`ok verdict phrase`、`ok VERSIONS row`、`ok CMake project()` 四个独立检查仍报 ok（marker 缺失只 continue 交换文档的 ok file 行，texts 已载入故引文/裁决独立检查照跑，VERSIONS/CMake 是独立文件）；pristine code0。

### 改动（行为不变，3 文件，eval-only，case 数不变仍 42）

1. `evals/unitree_swap_guard_selftest.py`（#20）：新增 **N6**（删除 opt-in env marker `UNITREE_DDS_PROVIDER=external`）与 **N7**（删除合法外部工作区 marker `unitree_sdk2_hzj`），各要求 code1 + 无 success marker + `FAIL markers` 且点名被删 marker，并断言引文/裁决/VERSIONS/CMake 四个独立检查仍 ok（不连带）；negative 5→7，计数由 `5 negative, 2 non-flag, 2 healthy, 1 mutation` 扩为 **`7 negative, 2 non-flag, 2 healthy, 1 mutation`**；汇总行 `/5`→`/7`；同步 docstring 第 1 点枚举（five→seven，列 N6/N7）。
2. `evals/promptfooconfig.yaml`：更新 #20 description（补 dropped legal-path markers）与计数 value；该 `5 negative, 2 non-flag…` 串在 yaml 另属一个 case（行 329），按 #20 块整段上下文精确替换、另一处不动；cases=42、scripts=42。
3. `evals/README.md`：#20 文件表行、明细表行（整行，#23 同形串不动）、专节（5→7 负向场景并补 N6/N7 说明）同步。
4. 本日志小节。

### 评估驱动证据

- N6/N7 先在真实 guard 上 /tmp 探针逐字取证（删 marker 的 FAIL markers 点名行 + 四个独立 ok 行）再写进自测；
- 两场景都断言「该 FAIL 的点名 + 不该 FAIL 的独立检查仍 ok」，与 N1–N4 的独立性断言同构，非恒真（健康对照 H2 不删则绿，证明删除确实触发）；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #20 对合法路径 marker 的负向判别；不额外加 mutation（N6/N7 由 H2 健康对照与真实删除探针自证非恒真，避免过度堆夹具）。

### 实测（本机 macOS，2026-09-22 22:21 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-0Jy-2026-09-22T14:21:36`（Duration 5s，0 error）。

### 合并后权威回归（功能 PR #150 已 squash-merge）

- 功能 PR #150（分支 test/unitree-legal-path-marker-negatives，commit c68188c，4 files +113/−10）required 三检 + CodeQL + Cursor Approval(1m9s) 全 pass，squash-merge 到 main，mergeCommit `13c63234191d5d3ef67393ea72893ae6c8b66690`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `13c6323`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-BW2-2026-09-22T14:28:38`（Duration 6s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh；未改 dimos_bridge/vendor/shell/load.py（vendor 文件仅复制进 tempdir 读取，未写）；未集成 Cega、未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- 合法 external 路径契约现有 N6/N7 钉删除侧；其「default bundled、external 必须 opt-in」的正向语义仍由正向 #7 与 marker 存在性覆盖，未单独造 env 组合夹具（guard 本身只读文档不执行 env，造 env 夹具属越界，不做）。
- existence-only 放行 helper 仍在 #20/#27/#42 三处重复（seed 签名不同，本轮不抽）；`prove_rmw` 维持合理空缺；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #150 已合并（main `13c6323`），合并后权威回归 42/42、0 error（eval `eval-BW2-2026-09-22T14:28:38`），本回填 PR 即补登。
2. 断言质量复查继续：对 #41 risk_matrix_guard（复制 8 真实文件型）做 existence-only/放行侧盲区探针；或复查其余复制真实文件型 selftest 是否还有「关键 marker 走通用元组却无删除负向场景」的同类缺口；均先探针证盲区再加强。
3. existence-only 放行 helper 等第四处或签名趋同；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 52 — 2026-09-22 23:13（Asia/Shanghai）— 给 #41 risk_matrix guard 补三个核心 Hold 禁令词的删除负向场景（功能 PR #153，main 8895d34）

### 只读取证（断言质量复查，接续轮次51 下一步候选 a）

- 读 `scripts/check_risk_matrix.py`（139 行）与 `evals/risk_matrix_guard_selftest.py`（轮次46 后）逐分支对照：#41 原有 3 negative（N1 删独立 `《4》` 但保留 `《3》–《6》` 区间→FAIL markers 点名《4》、N2 删 R0 必需文件→FAIL missing、N3 ADR 去 `§9.4`→FAIL markers）、2 non-flag（NF1 仅 STATUS 的 SCOREBOARD、NF2 仅 domainId 锚点的 fastdds.xml 最小锚点树保持绿）、2 healthy、1 mutation（盲 read_utf8 静默 N1）。
- 真实盲区：矩阵的 19-marker 元组里含三个**核心 Hold 禁令词** `Agnocast` / `zenoh` / `Cega`（对应「不启用 Agnocast/zenoh」「不集成 Cega」硬边界），但 3 个 negative 没有一个删除它们。若未来有人从 `_MATRIX_MARKERS` 元组里「简化」掉其中任一禁令词，矩阵文档删掉该词不再报 FAIL，N1–N3 全绿、Hold 边界在风险矩阵文档面悄悄失效。
- /tmp 探针（复制 8 个真实文件进 tempdir；真实矩阵中 Agnocast/zenoh 各出现 3 次、Cega 2 次）：各删一词 → code1，打印 `FAIL markers` 并逐字点名 `need Agnocast` / `need zenoh` / `need Cega`，且其余 7 个文件仍打印 `ok file`（ADR/SCOREBOARD 在内，不连带）；pristine code0、8 个 ok file。
- 与《3》–《6》逐 token 反缩写契约同构：三词必须**各占一个**删除 case（不能合并成「三词全删」单 case），否则只从元组删掉其一时会被保留的另两个掩盖而漏报。order 检查（env/XML→…→core forks）的 token 全是 marker 子集、永远被 marker FAIL 遮蔽，无法独立触发，故不单独造负向。

### 改动（行为不变，3 文件，eval-only，case 数不变仍 42）

1. `evals/risk_matrix_guard_selftest.py`（#41）：`expect()` 增加可选 `also_ok=()` 形参（断言这些串仍在输出，钉「不连带」）；新增 **N4/N5/N6**，从矩阵各删一个 Hold 禁令词（Agnocast / zenoh / Cega），要求 code1 + 无健康 marker + `need <词>` 点名 + 其余文件 ok file / ADR 行仍在；negative 3→6，计数由 `3 negative, 2 non-flag, 2 healthy, 1 mutation` 扩为 **`6 negative, 2 non-flag, 2 healthy, 1 mutation`**；汇总行 `/3`→`/6`；同步 docstring 枚举与结尾散文。
2. `evals/promptfooconfig.yaml`：更新 #41 description（补 dropped Agnocast/zenoh/Cega、other files still ok）与计数 value（旧 3-neg 串全仓仅 #41 一处）；cases=42、scripts=42。
3. `evals/README.md`：#41 文件表行、明细表行（整行）、专节（3→6 negative 并补 N4/N5/N6 说明）同步。
4. 本日志小节。

### 评估驱动证据

- N4/N5/N6 先在真实 guard 上 /tmp 探针逐字取证（删词的 FAIL markers 点名行 + 其余 7 文件 ok file 行）再写进自测；
- 三场景各自独立、与 H2 纯复制健康树配对（不删则绿），证明删除确实触发、非恒真；`also_ok` 钉死矩阵 marker 缺失不误伤兄弟文件；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #41 对 Hold 禁令词的负向判别；既有 mutation（盲 read_utf8 静默 N1）保持不变。

### 实测（本机 macOS，2026-09-22 23:13 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-G4m-2026-09-22T15:12:59`（Duration 5s，0 error）。

### 合并后权威回归（功能 PR #153 已 squash-merge）

- 功能 PR #153（分支 test/risk-matrix-holdban-marker-negatives，commit 6bffcee，4 files）required 三检 + CodeQL + Cursor Approval(1m35s) 全 pass，squash-merge 到 main，mergeCommit `8895d34ea98eeff84855581ef6a278ddd6cc97a2`（远端分支已删；#152 被他人占用，本功能 PR 号为 #153）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `8895d34`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-wPp-2026-09-22T15:19:36`（Duration 5s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega（本轮恰恰是把这三条 Hold 禁令在风险矩阵文档面的存在性断言补严）；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- 本轮只钉矩阵文档面的三词存在性；这三条 Hold 的**代码/配置面**由 boundary job、fastdds.xml 冻结、vendor 只读等其他机制覆盖，#41 不越界读代码。
- R0 的 `Hold`、MAP 的 `vendor`、METHOD 的 `wiki`、GATES 的 `structure` 四个单 marker 文件仍只有正向、无各自删除负向（安全关键性低于三禁令词，留待后续按需补）；existence-only 放行 helper 仍在 #20/#27/#42 三处重复；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #153 已合并（main `8895d34`），合并后权威回归 42/42、0 error（eval `eval-wPp-2026-09-22T15:19:36`），本回填 PR 即补登。
2. 断言质量复查继续：类推审计其余复制真实文件型 selftest（#42 dual_chain_baseline、#27 three_chain 已补 existence non-flag/legal-path）的 marker 元组里安全关键项是否都有删除负向；或补 R0/MAP/METHOD/GATES 单 marker 文件的删除负向（先探针证盲区）。
3. existence-only 放行 helper 等第四处或签名趋同；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 53 — 2026-09-23 00:15（Asia/Shanghai）— 给 #41 四个单 marker 文件补「文件保留、内容丢 marker」删除负向 N7/N8/N9/N10（功能 PR #156，main eb5d91e）

### 只读取证（断言质量复查，接续轮次52 下一步第2条）

- 读 `scripts/check_risk_matrix.py`（139 行）required 表：8 个必需文件中，R0 / 源映射 / 延迟方法 / CI gates 四个文件各只带**一个** marker——R0 `Hold`、MAP `vendor`、METHOD `wiki`、GATES `structure`。
- 真实盲区：#41 的 N2 只覆盖 R0 文件**整文件缺失**（`FAIL missing`）；文件仍在、但内容里唯一 marker 被删（present-but-weakened）这一形态对 R0 没有断言，而 MAP/METHOD/GATES 三个文件**原本零负向**。若未来有人保留文件外壳却删掉该 marker（例如源映射文档不再提 vendor、CI gates 文档不再提 structure），guard 对该文件的强制在文档面失效，其余断言全绿。
- /tmp 探针（复制 8 真实文件；marker 在各文件出现次数：Hold 3、vendor 72、wiki 8、structure 6）：文件保留、各删该 marker 全部分出现处 → code1，逐字 `FAIL markers` 点名 `(need Hold)` / `(need vendor)` / `(need wiki)` / `(need structure)`，且其余 7 个文件仍打印 `ok file`（ADR 在内，不连带）；pristine code0、8 个 ok file。
- 四个场景结构同构、安全逻辑一致（每个必需文件的唯一内容 marker 被删必 fail markers 且不连带），作为同一项「单 marker 文件 present-but-weakened 负向」一次补齐；与 N4/N5/N6 同型，复用 `expect(..., also_ok=...)`。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/risk_matrix_guard_selftest.py`（#41）：`_seed_tree()` 扩展，新增 `r0_text` / `map_text` / `method_text` / `gates_text` 四个 override（此前这四个文件只能整文件 drop、不能改内容）；新增 **N7/N8/N9/N10**（文件保留、各删唯一 marker，要求 code1 + 无健康 marker + `need <词>` 点名 + 其余 7 文件 ok），negative 6→10，计数扩为 **`10 negative, 2 non-flag, 2 healthy, 1 mutation`**；汇总行 `/6`→`/10`；同步 docstring 枚举与结尾散文。
2. `evals/promptfooconfig.yaml`：#41 description 补 present-but-marker-stripped 四文件、计数 value 6→10；cases=42、scripts=42。
3. `evals/README.md`：#41 文件表行、明细表行（整行）、专节（6→10 negative 并补 N7–N10）同步。
4. 本日志小节。

### 评估驱动证据

- N7–N10 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + 其余 7 文件 ok file 行 + adr 不连带）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；`also_ok` 钉单文件 marker 缺失不误伤兄弟文件；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #41 对单 marker 文件 present-but-weakened 的负向判别；既有 N1–N6、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 00:15 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-cO4-2026-09-22T16:15:15`（Duration 4s，0 error）。

### 合并后权威回归（功能 PR #156 已 squash-merge）

- 功能 PR #156（分支 test/risk-matrix-singlefile-marker-negatives，commit 1b458ab，4 files）required 三检 + CodeQL + Cursor Approval(1m15s) 全 pass（mergeStateStatus CLEAN），squash-merge 到 main，mergeCommit `eb5d91e76e0d174690307bf3b3c53ff99d1c1804`（远端分支已删；#155 被他人占用，本功能 PR 号为 #156）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `eb5d91e`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-CiQ-2026-09-22T16:20:28`（Duration 4s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- 至此 #41 对 8 个必需文件的负向覆盖：矩阵（N1 + N4/N5/N6）、ADR（N3）、R0（N2 缺失 + N7 内容）、MAP/METHOD/GATES（N8/N9/N10 内容）、冻结两文件（NF1/NF2 最小锚点）；矩阵 order 检查 token 全是 marker 子集、必被 marker FAIL 遮蔽，不单独造负向。
- 类推审计尚未做到 #42 dual_chain_baseline（复制 11 文件）marker 元组安全关键项的删除负向；existence-only 放行 helper 仍在 #20/#27/#42 三处重复；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #156 已合并（main `eb5d91e`），合并后权威回归 42/42、0 error（eval `eval-CiQ-2026-09-22T16:20:28`），本回填 PR 即补登。
2. 断言质量复查转向 #42 dual_chain_baseline_doc selftest：读 guard 复制的 11 个文件 marker/指针元组，定位安全关键项（Hold 指针、SCOREBOARD/XML 只读锚点、blocked 标注等）是否都有删除负向，先探针证独有未覆盖边界再补。
3. existence-only 放行 helper 等第四处或签名趋同；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 54 — 2026-09-23 01:12（Asia/Shanghai）— 给 #42 baseline 文档 marker 元组补三个核心安全词（Hold / STATUS: blocked / 只读）删除负向 N7/N8/N9（功能 PR #159，main 99f9282）

### 只读取证（断言质量复查，接续轮次53 下一步第2条）

- 读 guard `scripts/check_dual_chain_baseline.py`（475 行）required 表与 `_BASELINE_MARKERS`（27 个 marker）。baseline 文档面此前的负向：N1 删 paused 短语（该串**不在** marker 元组，故只 FAIL paused）、N2/N5/N6 追加 p99/CJK-p99/p95（FAIL percentiles）；**没有任何删除 marker 元组成员的负向**（ADR 仅 N3 覆盖一个串）。
- 排除伪盲区：docstring 提到的四个独立短语中，map verdict / no-rewrite / pointer-only 三个串同时是 marker 元组成员（行72/73/77），render 里它们的独立 FAIL 分支（FAIL map/rewrite/pointer）删词时**必然伴随** FAIL markers（与 paused 不同，物理上无法独立触发），属冗余分支，不单独造负向（脚本 docstring 已钉此结论）。
- 真实盲区：marker 元组里三个核心安全词——`Hold`（Hold 边界，真实出现 6 次）、`STATUS: blocked`（blocked 诚实性，7 次）、`只读`（fastdds.xml 只读契约，5 次）——文件保留却删词会让 baseline 文档面的 Hold/诚实/只读强制失效，而既有 N1–N6 全绿。
- /tmp 探针（复制 11 真实文件）：各删该词全部分出现处 → code1，逐字 `FAIL markers: docs/architecture/feishu-dual-chain-baseline.md (need Hold)` / `(need STATUS: blocked)` / `(need 只读)`，ok file 数 8（只 baseline 自己不 ok，其余 8 文件 ok，ADR 在内不连带），且不触发 paused/percentile/map/rewrite/pointer 任一独立检查；pristine code0。
- 三个场景同文件、同型、同安全逻辑（核心安全 marker 删除必 fail markers、不连带），作为同一项一次补齐；swap 文档 present-but-stripped（drop-in FAIL/0.10.2/11.0.1 探针亦 code1）留下一轮。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`（#42）：新增参数化 **N7/N8/N9**（文件保留、各删 Hold / STATUS: blocked / 只读，要求 code1 + FAIL markers 点名 `need <词>` + 不触发 paused/percentile/map/rewrite/pointer + ADR 仍 ok 不连带），negative 6→9，计数扩为 **`9 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（six→nine、补核心 marker 与冗余短语结论）。
2. `evals/promptfooconfig.yaml`：#42 description 补核心 marker stripped、计数 value 6→9；cases=42、scripts=42。
3. `evals/README.md`：#42 文件表行、明细表行（整行计数）、专节（6→9 negative 并补 N7–N9）同步。
4. 本日志小节。

### 评估驱动证据

- N7–N9 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + ok file 8 + 不触发任何独立检查）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言不连带兄弟文件、不误触独立短语；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #42 对 baseline 核心安全 marker 的删除负向；既有 N1–N6、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 01:12 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-yu3-2026-09-22T17:12:11`（Duration 4s，0 error）。

### 合并后权威回归（功能 PR #159 已 squash-merge）

- 功能 PR #159（分支 test/dcb-baseline-core-marker-negatives，commit b132b5a，4 files）required 三检 + CodeQL + Cursor Approval(1m16s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `99f92823d424b88ada154071eaf762b9f1e59b26`（远端分支已删；#158 被他人占用，本功能 PR 号为 #159）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `99f9282`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-ohj-2026-09-22T17:19:06`（Duration 5s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- #42 仍未覆盖：swap 文档 present-but-stripped（N4 只覆盖整文件缺失；drop-in FAIL/0.10.2/11.0.1 内容 marker 删除探针已证 code1，待补）；R0（Hold）、MAP（vendor/不是复现）内容 marker 删除负向；baseline 元组其余诚实性词（Not Feishu field proof 等）。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #159 已合并（main `99f9282`），合并后权威回归 42/42、0 error（eval `eval-ohj-2026-09-22T17:19:06`），本回填 PR 即补登。
2. 给 #42 补 swap 文档 present-but-stripped 内容 marker（drop-in FAIL 等）删除负向（N4 只覆盖缺失），先探针证独有边界；R0/MAP 内容 marker 类推。
3. existence-only 放行 helper 等签名趋同再抽；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本（轮次44–54 持续 0 error）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 55 — 2026-09-23 02:12（Asia/Shanghai）— 给 #42 Unitree swap 文档补 present-but-stripped 内容 marker（drop-in FAIL / 0.10.2 / 11.0.1）删除负向 N10/N11/N12（功能 PR #161，main 015e42b）

### 只读取证（断言质量复查，接续轮次54 下一步第2条）

- guard required 表（行209）：Unitree swap 文档 `unitree-sdk2-dds-swap.md` 带三个内容 marker `drop-in FAIL`（drop-in 失败结论）、`0.10.2`（bundled 版本）、`11.0.1`（vendor 版本）。
- 真实盲区：#42 的 N4 只覆盖 swap 文档**整文件缺失**（FAIL missing）；文件保留、却删掉任一版本/结论 marker（present-but-weakened）这一形态**零负向**。保留文件外壳却删掉 drop-in FAIL 结论或某个版本号，会让 Unitree 0.10.2-vs-11.0.1 的证据在文档面失效，而既有 N1–N9 全绿。
- /tmp 探针（复制 11 真实文件；marker 出现次数 drop-in FAIL 3 / 0.10.2 23 / 11.0.1 24）：文件保留、各删该词全部分出现处 → code1，逐字 `FAIL markers: docs/architecture/unitree-sdk2-dds-swap.md (need drop-in FAIL)` / `(need 0.10.2)` / `(need 11.0.1)`，ok file 数 8（只 swap 自己不 ok，baseline 不连带），且不触发 paused/percentile/missing 任一检查；pristine code0。
- 三个场景同文件、同型、同安全逻辑（swap 内容 marker 删除必 fail markers、只点名 swap、不连带），作为同一项一次补齐；R0/MAP 内容 marker 删除负向留下一轮。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`（#42）：新增参数化 **N10/N11/N12**（swap 文件保留、各删 drop-in FAIL / 0.10.2 / 11.0.1，要求 code1 + FAIL markers 点名 `need <词>` + baseline 不连带 + 不触发 paused/percentile/missing），negative 9→12，计数扩为 **`12 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（nine→twelve、补 swap present-but-stripped）。
2. `evals/promptfooconfig.yaml`：#42 description 补 swap 内容 marker stripped、计数 value 9→12；cases=42、scripts=42。
3. `evals/README.md`：#42 文件表行、明细表行（整行计数）、专节（9→12 negative 并补 N10–N12）同步。
4. 本日志小节。

### 评估驱动证据

- N10–N12 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + ok file 8 + baseline 不连带）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言不连带 baseline、不误触 paused/percentile/missing；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #42 对 swap present-but-weakened 的负向判别；既有 N1–N9、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 02:12 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-eQ6-2026-09-22T18:12:03`（Duration 5s，0 error）。

### 合并后权威回归（功能 PR #161 已 squash-merge）

- 功能 PR #161（分支 test/dcb-swap-content-marker-negatives，commit 3b8745a，4 files）required 三检 + CodeQL + Cursor Approval(1m17s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending；合并时一次 TLS handshake timeout 重试即过），squash-merge 到 main，mergeCommit `015e42b9ef5e7b7d0510ad73ba37663bcf10c9c5`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `015e42b`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-eYv-2026-09-22T18:17:21`（Duration 5s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- #42 仍未覆盖：R0（Hold）、MAP（vendor / 不是复现）内容 marker 删除负向（这两个文件 present-but-stripped 探针尚未做）；baseline 元组其余诚实性词（Not Feishu field proof 等）。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #161 已合并（main `015e42b`），合并后权威回归 42/42、0 error（eval `eval-eYv-2026-09-22T18:17:21`），本回填 PR 即补登。
2. 给 #42 补 R0（Hold）、MAP（vendor / 不是复现）内容 marker present-but-stripped 删除负向，先探针证独有边界；baseline 其余诚实性词类推。
3. existence-only 放行 helper 等签名趋同再抽；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本（轮次44–55 持续 0 error）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 56 — 2026-09-23 03:10（Asia/Shanghai）— 给 #42 R0 冻结文档（Hold）与源映射文档（vendor / 不是复现）补 present-but-stripped 内容 marker 删除负向 N13/N14/N15（功能 PR #163，main 7f6f03e）

### 只读取证（断言质量复查，接续轮次55 下一步第2条）

- guard required 表：R0 冻结文档 `ros2-dds-r0-interface-freeze.md` 带 marker `Hold`；源映射文档 `ros2-source-map.md` 带 marker `vendor` 与 `不是复现`（非复现结论）。
- 真实盲区：#42 此前 N1 只覆盖 paused 短语、N4 只覆盖 swap 整文件缺失、N7–N12 只覆盖 baseline/swap marker；**R0 与源映射的 present-but-weakened 形态零负向**。保留文件外壳却删掉 R0 的 Hold，或源映射的 vendor / 不是复现，会让接口冻结或源映射证据在文档面失效，而既有 N1–N12 全绿。
- /tmp 探针（复制 11 真实文件；出现次数 R0 Hold 3；MAP vendor 72、不是复现 1）：文件保留、各删该词全部分出现处 → code1，逐字 `FAIL markers: docs/architecture/ros2-dds-r0-interface-freeze.md (need Hold)`、`ros2-source-map.md (need vendor)`、`(need 不是复现)`，ok file 数 8（只该文件不 ok、baseline 不连带），且不触发 paused/percentile/missing/map 任一检查；pristine code0。
- 三个场景同型、同安全逻辑（内容 marker 删除必 fail markers、只点名该文件、不连带），作为同一项一次补齐；baseline 元组其余诚实性词留下一轮。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`（#42）：新增参数化 **N13/N14/N15**（R0 保留删 Hold、源映射保留删 vendor / 不是复现，要求 code1 + FAIL markers 点名 `need <词>` + baseline 不连带 + 不触发 paused/percentile/missing/map），negative 12→15，计数扩为 **`15 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（twelve→fifteen、补 R0/MAP present-but-stripped）。
2. `evals/promptfooconfig.yaml`：#42 description 补 R0/MAP marker stripped、计数 value 12→15；cases=42、scripts=42。
3. `evals/README.md`：#42 文件表行、明细表行（整行计数）、专节（12→15 negative 并补 N13–N15）同步。
4. 本日志小节。

### 评估驱动证据

- N13–N15 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + ok file 8 + baseline 不连带）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言不连带 baseline、不误触 paused/percentile/missing/map；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #42 对 R0/源映射 present-but-weakened 的负向判别；既有 N1–N12、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 03:10 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-5pu-2026-09-22T19:10:50`（Duration 5s，0 error）。

### 合并后权威回归（功能 PR #163 已 squash-merge）

- 功能 PR #163（分支 test/dcb-r0-map-content-marker-negatives，commit 5f0d683，4 files）required 三检 + CodeQL + Cursor Approval(1m59s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending；创建时一次 TLS handshake timeout 重试即过），squash-merge 到 main，mergeCommit `7f6f03ec23a9cb477feacb32c908bcbafd3bba0a`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `7f6f03e`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-ob4-2026-09-22T19:16:02`（Duration 5s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- #42 仍未覆盖：baseline 元组其余诚实性词（Not Feishu field proof、派生自 等）present-but-stripped 删除负向；ADR 文档除「不重写 XML」外其余 marker（FastDDS + Cyclone / SCOREBOARD）的 present-but-stripped 删除负向。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #163 已合并（main `7f6f03e`），合并后权威回归 42/42、0 error（eval `eval-ob4-2026-09-22T19:16:02`），本回填 PR 即补登。
2. 给 #42 补 baseline 元组其余诚实性词（Not Feishu field proof、派生自）与 ADR 其余 marker（FastDDS + Cyclone / SCOREBOARD）present-but-stripped 删除负向，先探针证独有边界。
3. existence-only 放行 helper 等签名趋同再抽；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本（轮次44–56 持续 0 error）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 57 — 2026-09-23 04:11（Asia/Shanghai）— 给 #42 中间件 ADR 补 present-but-stripped 其余内容 marker（FastDDS + Cyclone / SCOREBOARD / baseline 回指）删除负向 N16/N17/N18（功能 PR #165，main c6f1e3f）

### 只读取证（断言质量复查，接续轮次56 下一步第2条）

- guard required 表：中间件 ADR `feishu-middleware-adr.md` 带 4 个 marker `FastDDS + Cyclone`（双链范围）、`不重写 XML`、`SCOREBOARD`、`feishu-dual-chain-baseline.md`（baseline 回指）。
- 真实盲区：#42 的 N3 只覆盖 ADR 删「不重写 XML」；ADR **保留**却删掉双链范围 / SCOREBOARD 指针 / baseline 回指（present-but-weakened）这三个形态**零负向**。保留 ADR 外壳却删掉其中一个，会让 ADR 的双链范围声明或指针在文档面失效，而既有 N1–N15 全绿。
- /tmp 探针（复制 11 真实文件；出现次数 FastDDS + Cyclone 2、SCOREBOARD 4、baseline 回指 6）：文件保留、各删该词全部分出现处 → code1，逐字 `FAIL markers: docs/architecture/feishu-middleware-adr.md (need FastDDS + Cyclone)` / `(need SCOREBOARD)` / `(need feishu-dual-chain-baseline.md)`，ok file 数 8（只 ADR 不 ok、baseline 不连带），且不触发 paused/percentile/missing/rewrite 任一检查；pristine code0。
- 三个场景同文件、同型、同安全逻辑（ADR 内容 marker 删除必 fail markers、只点名 ADR、不连带），与 N3 同文件补齐 ADR present-but-stripped 全覆盖，作为同项一次完成；baseline 诚实词（Not Feishu field proof、派生自）留下一轮。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`（#42）：新增参数化 **N16/N17/N18**（ADR 保留删 FastDDS + Cyclone / SCOREBOARD / baseline 回指，要求 code1 + FAIL markers 点名 `need <词>` + baseline 不连带 + 不触发 paused/percentile/missing/rewrite），negative 15→18，计数扩为 **`18 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（fifteen→eighteen、补 ADR 其余 marker）。
2. `evals/promptfooconfig.yaml`：#42 description 补 ADR marker stripped、计数 value 15→18；cases=42、scripts=42。
3. `evals/README.md`：#42 文件表行、明细表行（整行计数）、专节（15→18 negative 并补 N16–N18）同步。
4. 本日志小节。

### 评估驱动证据

- N16–N18 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + ok file 8 + baseline 不连带）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言不连带 baseline、不误触 paused/percentile/missing/rewrite；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #42 对 ADR present-but-weakened 的负向判别；既有 N1–N15、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 04:11 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-mfo-2026-09-22T20:11:31`（Duration 5s，0 error）。

### 合并后权威回归（功能 PR #165 已 squash-merge）

- 功能 PR #165（分支 test/dcb-adr-content-marker-negatives，commit 95fc051，4 files）required 三检 + CodeQL + Cursor Approval(1m24s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `c6f1e3fb8ab173e21c712f4afef55771caea1328`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `c6f1e3f`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-ZFS-2026-09-22T20:16:26`（Duration 4s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- #42 仍未覆盖：baseline 元组诚实词 `Not Feishu field proof`（1 次）、`派生自`（3 次）present-but-stripped 删除负向（探针已证 code1、本轮未加）。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #165 已合并（main `c6f1e3f`），合并后权威回归 42/42、0 error（eval `eval-ZFS-2026-09-22T20:16:26`），本回填 PR 即补登。
2. 给 #42 补 baseline 元组诚实词 Not Feishu field proof / 派生自 present-but-stripped 删除负向（探针已证 code1），先复核独有边界。
3. existence-only 放行 helper 等签名趋同再抽；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本（轮次44–57 持续 0 error）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 58 — 2026-09-23 05:09（Asia/Shanghai）— 给 #42 baseline 文档补 present-but-stripped 诚实词 marker（Not Feishu field proof / 派生自）删除负向 N19/N20（功能 PR #168，main 69304a9）

### 只读取证（断言质量复查，接续轮次57 下一步第2条）

- guard required 表：baseline 文档 `feishu-dual-chain-baseline.md` 的 `_BASELINE_MARKERS` 含两个诚实性词 `Not Feishu field proof`（明确声明 baseline 不是飞书现场证据，1 次）、`派生自`（派生关系措辞，3 次）。
- 真实盲区：#42 的 N7–N9 只覆盖 baseline 删 `Hold` / `STATUS: blocked` / `只读`；baseline **保留**却删掉非飞书现场证据声明 / 派生措辞（present-but-weakened）这两个形态**零负向**。保留 baseline 外壳却删掉其中一个，会让 baseline 的诚实性记录在文档面失效，而既有 N1–N18 全绿。
- /tmp 探针（复制 11 真实文件）：文件保留、各删该词全部分出现处 → code1，逐字 `FAIL markers: docs/architecture/feishu-dual-chain-baseline.md (need Not Feishu field proof)` / `(need 派生自)`，ok file 数 8（只 baseline 不 ok、ADR 不连带），且不触发 paused/percentile/missing/map/rewrite/pointer 任一检查；pristine code0。
- 两个场景同文件、同型、同安全逻辑（baseline 诚实词删除必 fail markers、只点名 baseline、不连带），作为同项一次完成。至此 #42 对 baseline 文档的核心安全/诚实词（Hold / STATUS: blocked / 只读 / Not Feishu field proof / 派生自）present-but-stripped 负向补齐。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`（#42）：新增参数化 **N19/N20**（baseline 保留删 Not Feishu field proof / 派生自，要求 code1 + FAIL markers 点名 `need <词>` + ADR 不连带 + 不触发 paused/percentile/missing/map/rewrite），negative 18→20，计数扩为 **`20 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（eighteen→twenty、补 baseline 诚实词）。
2. `evals/promptfooconfig.yaml`：#42 description 补 baseline 诚实词 stripped、计数 value 18→20；cases=42、scripts=42。
3. `evals/README.md`：#42 文件表行、明细表行（整行计数）、专节（18→20 negative 并补 N19–N20）同步。
4. 本日志小节。

### 评估驱动证据

- N19/N20 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + ok file 8 + ADR 不连带）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言不连带 ADR、不误触 paused/percentile/missing/map/rewrite；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #42 对 baseline present-but-weakened 的负向判别；既有 N1–N18、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 05:09 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-Crd-2026-09-22T21:09:20`（Duration 5s，0 error）。

### 合并后权威回归（功能 PR #168 已 squash-merge）

- 功能 PR #168（分支 test/dcb-baseline-honesty-marker-negatives，commit 4a127ce，4 files；#167 被他人占用）required 三检 + CodeQL + Cursor Approval(1m54s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `69304a919e2a75f06c6a915c3d016d5bf50aa8bb`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `69304a9`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-lxU-2026-09-22T21:14:07`（Duration 5s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- #42 对 baseline/ADR/R0/MAP/SWAP 五个 marker 文件的 present-but-stripped 核心词已基本补齐；后续若再扩，应先系统比对 guard 各 per-file marker 元组与现有 N 场景，确认仍有独有未覆盖边界，不为凑数。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #168 已合并（main `69304a9`），合并后权威回归 42/42、0 error（eval `eval-lxU-2026-09-22T21:14:07`），本回填 PR 即补登。
2. 系统复查 #42 各 per-file marker 元组（尤其 CHAIN_A/CHAIN_B export 之外、SWAP/R0 已覆盖词之外）是否仍有安全关键 present-but-stripped 独有边界，先探针再决定是否加。
3. existence-only 放行 helper 等签名趋同再抽；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本（轮次44–58 持续 0 error）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 59 — 2026-09-23 06:11（Asia/Shanghai）— 给 #42 baseline 文档补 present-but-stripped 双链 RMW/domain 身份词（rmw_fastrtps_cpp / ROS_DOMAIN_ID=42 / rmw_cyclonedds_cpp / 域 0）删除负向 N21–N24（功能 PR #171，main be278d1）

### 只读取证（系统复查 per-file marker 元组，接续轮次58 下一步第2条）

- 系统盘点 guard required 表各 per-file marker 与现有 N 场景：ADR 4 marker（N3/N16/N17/N18）、R0 Hold（N13）、MAP vendor/不是复现（N14/N15）、SWAP 3 marker（N10/N11/N12）已全覆盖；baseline 27 marker 中已覆盖 Hold/STATUS: blocked/只读（N7–N9）、Not Feishu field proof/派生自（N19/N20）。
- 真实盲区：baseline 文档里的**双链身份四要素** Chain A `rmw_fastrtps_cpp`、`ROS_DOMAIN_ID=42`，Chain B `rmw_cyclonedds_cpp`、`域 0` present-but-stripped **零负向**。保留 baseline 外壳却删掉任一链的 RMW 实现标识或 domain 标识，会让双链身份在文档面失效，而既有 N1–N20 全绿。
- /tmp 探针（复制 11 真实文件；出现次数 rmw_fastrtps_cpp 3、ROS_DOMAIN_ID=42 3、rmw_cyclonedds_cpp 2、域 0 2）：文件保留、各删该词全部分出现处 → code1，逐字 `FAIL markers: docs/architecture/feishu-dual-chain-baseline.md (need rmw_fastrtps_cpp)` / `(need ROS_DOMAIN_ID=42)` / `(need rmw_cyclonedds_cpp)` / `(need 域 0)`，ok file 数 8（只 baseline 不 ok、ADR 不连带），且**不触发 chain A/chain B 检查**（chain 检查读 chain_a.sh/chain_b.sh 而非 baseline），不触发 paused/percentile/missing/map/rewrite；pristine code0。
- 四个场景同文件、同型、同安全逻辑（双链 RMW/domain 身份词删除必 fail markers、只点名 baseline、不连带 chain），作为同项一次完成。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`（#42）：新增参数化 **N21/N22/N23/N24**（baseline 保留删 Chain A rmw/domain、Chain B rmw/domain，要求 code1 + FAIL markers 点名 `need <词>` + ADR 不连带 + 不触发 chain A/B 及其余检查），negative 20→24，计数扩为 **`24 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（twenty→twenty-four、补双链身份词）。
2. `evals/promptfooconfig.yaml`：#42 description 补双链身份词 stripped、计数 value 20→24；cases=42、scripts=42。
3. `evals/README.md`：#42 文件表行、明细表行（整行计数）、专节（20→24 negative 并补 N21–N24）同步。
4. 本日志小节。

### 评估驱动证据

- N21–N24 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + ok file 8 + 不连带 chain/ADR）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言不连带 chain A/B、不误触 paused/percentile/missing/map/rewrite；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #42 对 baseline 双链身份词 present-but-weakened 的负向判别；既有 N1–N20、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 06:11 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-9WN-2026-09-22T22:11:44`（Duration 5s，0 error）。中途一次后台 TaskOutput 句柄 TASK_NOT_FOUND，重跑 promptfoo 取到上述权威结果（非 eval 失败）。

### 合并后权威回归（功能 PR #171 已 squash-merge）

- 功能 PR #171（分支 test/dcb-chain-identity-marker-negatives，commit 5035784，4 files；#170 被他人占用）required 三检 + CodeQL + Cursor Approval(1m55s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `be278d18a88f3c52efb91f88f4cf6bcc85621e95`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `be278d1`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-HDG-2026-09-22T22:16:47`（Duration 5s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- baseline 元组其余未加 present-but-stripped 负向的词（§13、chain_a.sh/chain_b.sh、fastdds.xml、CYCLONEDDS_URI、cross-host、three-chain、《3》–《6》等）多为指针/范围/锚点词，安全权重低于身份/诚实/Hold 词；map/rewrite/pointer 三词删除会同时触发独立 FAIL 分支（轮次54 已钉为冗余不造负向）。后续若再扩须先逐个探针确认独有未覆盖边界，不为凑数。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #171 已合并（main `be278d1`），合并后权威回归 42/42、0 error（eval `eval-HDG-2026-09-22T22:16:47`），本回填 PR 即补登。
2. 评估 baseline 其余指针/范围词（CYCLONEDDS_URI、cross-host、three-chain、《3》–《6》等）是否值得补 present-but-stripped 负向，先探针确认独有边界与安全权重，低价值不凑。
3. existence-only 放行 helper 等签名趋同再抽；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本（轮次44–59 持续 0 error）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 60 — 2026-09-23 07:12（Asia/Shanghai）— 给 #42 baseline 文档补 present-but-stripped blocked/契约边界词（cross-host / three-chain / CYCLONEDDS_URI）删除负向 N25–N27（功能 PR #173，main 355e907）

### 只读取证（接续轮次59 下一步第2条，评估其余指针/范围词）

- 对 baseline 元组中尚未加 present-but-stripped 负向的词逐个 /tmp 探针（出现次数：CYCLONEDDS_URI 3、cross-host 4、three-chain 10、《3》5/《4》2/《5》2/《6》5、drop-in FAIL 5/0.10.2 5/11.0.1 6、chain_a.sh 7/chain_b.sh 7、fastdds.xml 11、SCOREBOARD 21、§13 8）：所有词删除均 code1、只点名 baseline、ok file 8、无其他 trip（物理上都能独立触发）。
- 按安全权重取舍：**cross-host（跨机 UDP blocked 诚实词）、three-chain（三链复现 blocked 诚实词）、CYCLONEDDS_URI（Chain B 必须 unset 的配置契约词）** 直接对应「哪些实验 blocked / 哪个变量必须 unset」的安全边界，权重最高；《3》–《6》为范围边界、drop-in FAIL/0.10.2/11.0.1 在 baseline 是 swap 结论的重复（swap 文档 N10–N12 已覆盖）、chain_a.sh/chain_b.sh/fastdds.xml/SCOREBOARD/§13 为指针/锚点，权重低，本轮不凑。
- 真实盲区：N21–N24 只覆盖 baseline 删双链 RMW/domain 身份；baseline 保留却删 blocked 范围诚实词或 Chain B unset-URI 契约词 **零负向**，会让 blocked 诚实记录 / Chain B unset 契约在文档面失效，而既有 N1–N24 全绿。
- /tmp 探针：文件保留、各删该词全部分出现处 → code1，逐字 `FAIL markers: docs/architecture/feishu-dual-chain-baseline.md (need cross-host)` / `(need three-chain)` / `(need CYCLONEDDS_URI)`，ok file 8（只 baseline 不 ok、ADR 不连带），不触发 chain A/B（chain 检查读 chain_a.sh/chain_b.sh 而非 baseline），不触发 paused/percentile/missing/map/rewrite；pristine code0。
- 三个场景同文件、同型、同安全逻辑（blocked/契约边界词删除必 fail markers、只点名 baseline、不连带 chain），作为同项一次完成。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`（#42）：新增参数化 **N25/N26/N27**（baseline 保留删 cross-host / three-chain / CYCLONEDDS_URI，要求 code1 + FAIL markers 点名 `need <词>` + ADR 不连带 + 不触发 chain 及其余检查），negative 24→27，计数扩为 **`27 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（twenty-four→twenty-seven、补 blocked/契约边界词）。
2. `evals/promptfooconfig.yaml`：#42 description 补 blocked/契约边界词 stripped、计数 value 24→27；cases=42、scripts=42。
3. `evals/README.md`：#42 文件表行、明细表行（整行计数）、专节（24→27 negative 并补 N25–N27）同步。
4. 本日志小节。

### 评估驱动证据

- N25–N27 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + ok file 8 + 不连带 chain/ADR）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言不连带 chain、不误触 paused/percentile/missing/map/rewrite；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #42 对 baseline blocked/契约边界词 present-but-weakened 的负向判别；既有 N1–N24、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 07:12 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-Ol8-2026-09-22T23:12:46`（Duration 5s，0 error）。

### 合并后权威回归（功能 PR #173 已 squash-merge）

- 功能 PR #173（分支 test/dcb-blocked-boundary-marker-negatives，commit b80b68d，4 files）required 三检 + CodeQL + Cursor Approval(1m8s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `355e9070fd373c3211a8662b4398cb5970ae942b`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `355e907`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-1WQ-2026-09-22T23:17:52`（Duration 4s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- baseline 元组剩余未加负向的词（《3》–《6》范围、chain_a.sh/chain_b.sh/fastdds.xml/SCOREBOARD/§13 指针、baseline 内 swap 结论重复）安全权重低，多数与其他文件/检查重复；继续加会偏向凑数。后续若再扩 #42，应先论证独有安全价值。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #173 已合并（main `355e907`），合并后权威回归 42/42、0 error（eval `eval-1WQ-2026-09-22T23:17:52`），本回填 PR 即补登。
2. #42 baseline 安全关键身份/诚实/Hold/blocked/契约词已系统补齐，继续加低权重词价值有限；转向类推审计其余复制真实文件型 selftest（如 #20/#27/#41）的 marker 元组是否仍有安全关键独有边界。
3. existence-only 放行 helper 等签名趋同再抽；继续高负载窗口收集 provider 预算硬化后 fingerprint 0-error 样本（轮次44–60 持续 0 error）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 61 — 2026-09-23 08:11（Asia/Shanghai）— 类推审计：给 #20 unitree swap 文档补 present-but-stripped Hold 禁令词（Agnocast / zenoh）与 CVE 修复版本契约（cyclonedds>=0.10.5）删除负向 N8–N10（功能 PR #175，main 91f98bf）

### 只读取证（接续轮次60 下一步第2条，类推审计复制真实文件型 selftest）

- 审计 #20/#27/#41 三个复制真实文件型 selftest 的 marker 元组与现有负向：
  - #41（risk_matrix）已在轮次52 N4/N5/N6 覆盖 Hold 禁令词 Agnocast/zenoh/Cega、轮次53 N7–N10 覆盖单文件 marker，最完整。
  - #20（unitree_swap）原 7 negative：N1 verdict flip、N2 quote tamper、N3 VERSIONS SHA、N4 CMake VERSION、N5 doc deleted、N6/N7 合法 external 路径两 marker（UNITREE_DDS_PROVIDER=external / unitree_sdk2_hzj）。**N6/N7 只覆盖合法替换路径 marker；swap 文档保留却删其余安全契约词零负向。**
  - #27（three_chain）原 2 negative 只覆盖 fabricate（追加 map=reproduce / three-chain repro:PROVEN），其 marker present-but-stripped 全部零负向。
- /tmp 探针（swap 文档出现次数：Agnocast 1、zenoh 2、cyclonedds>=0.10.5 5、STATUS: blocked 3）：文件保留、各删该词 → code1，逐字 `FAIL markers: docs/architecture/unitree-sdk2-dds-swap.md (need Agnocast)` / `(need zenoh)` / `(need cyclonedds>=0.10.5)`，独立 verdict/quote/VERSIONS/CMake 检查读其他内容仍报 ok。
- 按安全权重取舍本轮做 #20 三个：**Agnocast/zenoh（Hold 禁令词，与 #41 轮次52 同型）+ cyclonedds>=0.10.5（external Cyclone 必须 ≥0.10.5 以修复 CVE-2024-10838 的版本契约，swap 文档独有）**；STATUS: blocked 诚实词留下轮（baseline #42 已大量覆盖 blocked 诚实模式）。#27 的 Hold 禁令词补全作为下一轮类推项。
- 真实盲区：swap 文档保留 shell、删任一 Hold 禁令词或 CVE 修复版本契约，会让 Hold 禁令 / CVE 修复版本契约在文档面失效，而既有 N1–N7 全绿。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/unitree_swap_guard_selftest.py`（#20）：新增 **N8/N9/N10**（文档保留删 Agnocast / zenoh / cyclonedds>=0.10.5，要求 code1 + FAIL markers 点名 need 词 + verdict/quote/VERSIONS/CMake 独立检查仍 ok），negative 7→10，计数扩为 **`10 negative, 2 non-flag, 2 healthy, 1 mutation`**；同步 docstring（seven→ten、补 N8–N10）与进度分母 /7→/10。
2. `evals/promptfooconfig.yaml`：#20 description 补 Hold 禁令/CVE-fix 词 stripped、计数 value 7→10；cases=42、scripts=42。
3. `evals/README.md`：#20 文件表行、明细表行（整行计数）、专节（7→10 negative 并补 N8–N10）同步。
4. 本日志小节。

### 评估驱动证据

- N8–N10 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + 独立检查仍 ok）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言 verdict/quote/VERSIONS/CMake 等独立检查仍报 ok（不连带）；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #20 对 swap 文档 Hold 禁令/CVE 修复版本契约 present-but-weakened 的负向判别；既有 N1–N7、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 08:11 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-9Ak-2026-09-23T00:11:20`（Duration 4s，0 error）。

### 合并后权威回归（功能 PR #175 已 squash-merge）

- 功能 PR #175（分支 test/unitree-swap-holdban-marker-negatives，commit 6a70fc9，4 files）required 三检 + CodeQL + Cursor Approval(1m25s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `91f98bfc2e3b9752dca4a7e86fc60cde035e09f2`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `91f98bf`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-0Hm-2026-09-23T00:16:26`（Duration 4s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。《6》CVE 审计保持只读：本轮只断言文档已记录的修复版本契约，未安装/升级任何被审计依赖。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- #27 three_chain repro 文档的 Hold 禁令词（Agnocast/zenoh 各 1）与其余 marker present-but-stripped 仍零负向，是下一轮类推项；#20 的 STATUS: blocked 诚实词 present-but-stripped 未加（与 baseline 模式重复，价值待论证）。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #175 已合并（main `91f98bf`），合并后权威回归 42/42、0 error（eval `eval-0Hm-2026-09-23T00:16:26`），本回填 PR 即补登。
2. 继续类推：给 #27 three_chain repro 文档补 Hold 禁令词（Agnocast/zenoh）present-but-stripped 负向（先探针、确认走 marker 扫描而非 phrase/status/chains 独立检查）。
3. #20 STATUS: blocked、#27 其余 marker 扩前先论证独有安全价值；existence-only helper 签名趋同再抽。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 62 — 2026-09-23 09:17（Asia/Shanghai）— 继续类推：给 #27 three-chain repro 文档补 present-but-stripped Hold 禁令词（Agnocast / zenoh）删除负向 N3/N4（功能 PR #177，main 47162d6）

### 只读取证（接续轮次61 下一步第2条）

- Read #27 guard（check_three_chain_repro.py）确认：`Agnocast`/`zenoh` 在 `_REPRO_MARKERS` 元组（行58/59），走通用 marker 扫描（行139–144）；**不在** phrase（只查 MAP_NE_REPRODUCE）、status（只查 STATUS_BLOCKED）、chains（publish/History/wait→callback 或 WaitSet/callback）、fabricate（PASS/PROVEN）四个独立检查里。
- repro 文档出现次数：Agnocast 1、zenoh 1（另有 Not Feishu field proof 1、not-run-here 3、ros2-source-map.md 12、feishu-executor-waitset.md 9 等）。
- /tmp 探针：文档保留、各删该词 → code1，逐字 `FAIL markers: docs/architecture/feishu-three-chain-repro.md (need Agnocast)` / `(need zenoh)`；phrase/status/chains/honesty 独立检查读其他内容仍报 ok（不连带、不触发 fabricate）。
- 真实盲区：repro 文档保留 shell、删任一 Hold 禁令词，会让 Hold 禁令在该文档面失效，而既有 N1/N2（只追加伪造句、从不删 marker）、non-flag、healthy、mutation 全绿。本轮只做这两个 Hold 禁令词（与 #41 轮次52、#20 轮次61 同型，把三处复制真实文件型 selftest 的 Hold 禁令词负向补齐）；其余 marker（Not Feishu field proof、not-run-here、指针等）留下轮并需先论证独有安全价值。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/three_chain_repro_guard_selftest.py`（#27）：`_seed_tree`/`_render` 加 `repro_drop` 参数；新增 **N3/N4**（文档保留删 Agnocast/zenoh，要求 code1 + FAIL markers 点名 need 词 + phrase/status/chains/honesty 仍 ok + 不触发 fabricate），negative 2→4，计数扩为 **`4 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（普通链词仍不重测、补 Hold ban 例外与 N3/N4）与进度分母 /2→/4。
2. `evals/promptfooconfig.yaml`：#27 description 补 Hold ban stripped、计数 value 2→4；cases=42、scripts=42。
3. `evals/README.md`：#27 文件表行、明细表行（整行计数）、专节（2→4 negative 并补 N3/N4）同步。
4. 本日志小节。

### 评估驱动证据

- N3/N4 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + phrase/status/chains/honesty 仍 ok）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言独立检查不连带、不触发 fabricate；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #27 对 repro 文档 Hold 禁令词 present-but-weakened 的负向判别；既有 N1/N2、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 09:17 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-ltn-2026-09-23T01:17:33`（Duration 4s，0 error）。

### 合并后权威回归（功能 PR #177 已 squash-merge）

- 功能 PR #177（分支 test/three-chain-holdban-marker-negatives，commit 17c221e，4 files）required 三检 + CodeQL + Cursor Approval(1m18s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `47162d6b8ded5a70eb85501a5a8ad9ea8c4520a3`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `47162d6`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-Ujb-2026-09-23T01:26:08`（Duration 4s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- repro 文档其余 marker（Not Feishu field proof、not-run-here、Humble、指针 ros2-source-map.md/feishu-executor-waitset.md 等）present-but-stripped 仍零负向，扩前先探针 + 论证独有安全价值；#20 STATUS: blocked 诚实词未加（与 baseline 模式重复，价值待论证）。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #177 已合并（main `47162d6`），合并后权威回归 42/42、0 error（eval `eval-Ujb-2026-09-23T01:26:08`），本回填 PR 即补登。
2. 评估 #27 repro 文档其余 marker（Not Feishu field proof 诚实词、not-run-here、Humble、指针）present-but-stripped：先探针 + 论证独有安全价值再决定是否加，不凑数。
3. #20 STATUS: blocked 扩前先论证独有价值；existence-only helper 签名趋同再抽。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 63 — 2026-09-23 10:20（Asia/Shanghai）— 给 #27 three-chain repro 文档补 present-but-stripped 独有诚实词（not-run-here / Humble）删除负向 N5/N6（功能 PR #179，main dbb51e1）

### 只读取证（接续轮次62 下一步第2条）

- 对 repro 文档全部候选 marker 探针（出现次数：not-run-here 3、Not Feishu field proof 1、Humble 10、fastdds.xml 3、SCOREBOARD 5、ros2-source-map.md 12、feishu-executor-waitset.md 9）：删光任一词 → code1 `FAIL markers ... (need <词>)`，phrase/status/chains/honesty 独立检查读其他内容仍报 ok（不连带）。
- 先排除冗余：MAP_NE_REPRODUCE / STATUS_BLOCKED 已由 phrase/status 独立检查覆盖，publish/History/wait→callback/WaitSet/callback 已由 chains 覆盖——删它们会 FAIL phrase/status/chains，不需要额外 marker 负向。
- 按安全权重取舍本轮做两个 repro 文档**独有诚实词**：**not-run-here（本机未实际运行链）+ Humble（无 ROS Humble runtime、三链复现 blocked）**，直接钉死 not-run / no-runtime 两条 blocked 诚实边界。
- 有意不加（不凑数）：Not Feishu field proof 与 baseline #42 轮次58 N19 同名同模式（重复）；ros2-source-map.md / feishu-executor-waitset.md / fastdds.xml / SCOREBOARD 是交叉引用/指针锚点、权重低（同轮次60 对 §13 指针的判断）。
- 真实盲区：repro 文档保留 shell、删 not-run-here 或 Humble，会让"本机未运行 / 无 Humble runtime"诚实契约在该文档面失效，而既有 N1–N4 全绿。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/three_chain_repro_guard_selftest.py`（#27）：复用 repro_drop 通道，新增 **N5/N6**（文档保留删 not-run-here/Humble，要求 code1 + FAIL markers 点名 need 词 + phrase/status/chains/honesty 仍 ok），negative 4→6，计数扩为 **`6 negative, 3 non-flag, 2 healthy, 1 mutation`**；同步 docstring（补 N5/N6）与进度分母 /4→/6。
2. `evals/promptfooconfig.yaml`：#27 description 补 honesty 词 stripped、计数 value 4→6；cases=42、scripts=42。
3. `evals/README.md`：#27 文件表行、明细表行（整行计数）、专节（4→6 negative 并补 N5/N6 与取舍说明）同步。
4. 本日志小节。

### 评估驱动证据

- N5/N6 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need 行 + phrase/status/chains/honesty 仍 ok）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言独立检查不连带；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #27 对 repro 文档独有诚实词 present-but-weakened 的负向判别；既有 N1–N4、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 10:20 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-0JE-2026-09-23T02:20:01`（Duration 11s，0 error）。

### 合并后权威回归（功能 PR #179 已 squash-merge）

- 功能 PR #179（分支 test/three-chain-honesty-marker-negatives，commit 8ed080d，4 files）required 三检 + CodeQL + Cursor Approval(1m13s) 全 pass（reviewDecision APPROVED；mergeStateStatus CLEAN），squash-merge 到 main，mergeCommit `dbb51e1d4bf462c2984658545f25c2b205dce915`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `dbb51e1`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-92a-2026-09-23T02:28:15`（Duration 4s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- repro 文档的 Not Feishu field proof（与 baseline 重复）与四个指针锚点 present-but-stripped 仍零负向，已论证权重低、有意不加；#20 STATUS: blocked 诚实词未加（与 baseline 模式重复，价值待论证）。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #179 已合并（main `dbb51e1`），合并后权威回归 42/42、0 error（eval `eval-92a-2026-09-23T02:28:15`），本回填 PR 即补登。
2. #27 repro 文档 marker 已按安全权重覆盖到位（Hold 禁令 + 独有诚实词；重复诚实词/指针有意不加）。转去复查其他复制真实文件型 selftest（如 #20 STATUS: blocked、#41 其余 per-file marker）是否仍有独有未覆盖边界，先探针论证、不凑数。
3. existence-only helper 签名趋同再抽（单独 PR、行为不变）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 64 — 2026-09-23 11:38（Asia/Shanghai）— 给 #20 unitree swap 文档补 present-but-stripped Hold 环境隔离路径（/opt/ros/humble）删除负向 N11（功能 PR #181，main 1b308f2）

### 只读取证（接续轮次63 下一步第2条）

- 对 swap 文档全部候选 marker 探针（出现次数：STATUS: blocked 3、/opt/ros/humble 4、bundled 13、in-place overwrite 4、libddsc 15、libddscxx 7、Unitree 12、0.10.2 23、11.0.1 24、fastdds.xml 4、SCOREBOARD 6、vendor/VERSIONS.md 10）：删光任一词 → code1 `FAIL markers ... (need <词>)`，quote/verdict/VERSIONS/CMake 独立检查读其他内容仍报 ok（不连带；仅删 0.10.2 会连带 quote，因引文含 0.10.2，属冗余）。
- 按安全权重取舍本轮做 swap 文档**独有 Hold 环境隔离路径**：**/opt/ros/humble（guard 末尾明确 "Do not copy rolling vendor onto a robot or /opt/ros/humble"）**，承载"不把 vendor rolling 污染到机器人 / Humble 安装目录"契约；该路径为 swap 文档独有，baseline/repro 无此 marker，且只走通用 marker 元组、不在四个独立检查。
- 有意不加（不凑数）：STATUS: blocked 与 baseline 轮次58 N8、repro status 同模式（重复）；bundled/in-place overwrite 与 DOC_VERDICT/默认 bundled 语义重叠；libddsc/libddscxx 为库名技术内容；fastdds.xml/SCOREBOARD/vendor/VERSIONS.md 是指针锚点；11.0.1/Unitree 版本/主体名已由 VERSIONS/CMake 实际 pin 覆盖。
- 真实盲区：swap 文档保留 shell、删 /opt/ros/humble，会让"不得污染 Humble 安装"的环境隔离契约在该文档面失效，而既有 N1–N10 全绿。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/unitree_swap_guard_selftest.py`（#20）：复用 `_drop` 通道，新增 **N11**（文档保留删 /opt/ros/humble，要求 code1 + FAIL markers 点名 need 路径 + quote/verdict/VERSIONS/CMake 仍 ok），negative 10→11，计数扩为 **`11 negative, 2 non-flag, 2 healthy, 1 mutation`**；同步 docstring（补 N11）与进度分母 /10→/11。
2. `evals/promptfooconfig.yaml`：#20 description 补 Hold 环境隔离路径 stripped、计数 value 10→11；cases=42、scripts=42。
3. `evals/README.md`：#20 文件表行、明细表行（整行计数）、专节（10→11 negative 并补 N11 与取舍说明）同步。
4. 本日志小节。

### 评估驱动证据

- N11 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers 点名 need /opt/ros/humble + 四个独立检查仍 ok）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言独立检查不连带；
- 不新增 case、不改 guard 代码 / fixtures / runner，纯补 #20 对 swap 文档独有 Hold 环境隔离路径 present-but-weakened 的负向判别；既有 N1–N10、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 11:38 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-oK5-2026-09-23T03:38:33`（Duration 7s，0 error）。

### 合并后权威回归（功能 PR #181 已 squash-merge）

- 功能 PR #181（分支 test/unitree-humble-path-marker-negative，commit dcbfd21，4 files）required 三检 + CodeQL + Cursor Approval(1m29s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `1b308f283bd8bc728ad54e305b518680bf9a6735`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `1b308f2`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-fmG-2026-09-23T03:44:33`（Duration 8s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- swap 文档的 STATUS: blocked（重复）、bundled/in-place/libddsc/指针/版本号 present-but-stripped 仍零负向，已论证权重低/重复/语义重叠、有意不加。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #181 已合并（main `1b308f2`），合并后权威回归 42/42、0 error（eval `eval-fmG-2026-09-23T03:44:33`），本回填 PR 即补登。
2. #20 swap 文档 marker 已按安全权重覆盖到位（裁决/引文/合法路径/Hold 禁令/CVE 版本/Humble 隔离；重复诚实词/库名/指针/版本有意不加）。转去复查 #41/#42 是否仍有独有未覆盖 per-file marker，先探针论证、不凑数。
3. existence-only helper 签名趋同再抽（单独 PR、行为不变）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 65 — 2026-09-23 12:34（Asia/Shanghai）— 给 #41 risk_matrix 反缩写契约补 range 中间项《5》删除负向 N11（功能 PR #183，main f7e5e05）

### 只读取证（接续轮次64 下一步第2条）

- Read guard `check_risk_matrix.py`（139 行）：required 8 项，matrix 走 19-marker `_MATRIX_MARKERS`（含反缩写契约要求的 《3》《4》《5》《6》 各自 token）。原 selftest N1 只覆盖删 standalone 《4》，《3》《5》《6》 三个 token 的 standalone 被删、range 保留时零断言。
- 矩阵实际结构（grep 取证）：行21 是区间句 `《3》–《6》仍 Hold`（字面含端点 《3》《6》），行73 表格行 `《3》90%/LLM、《4》Mac/preprod、《5》Promptfoo、《6》CVE`（四个 standalone token）。count：《3》2、《4》1、《5》1、《6》2。
- 探针（只删表格 standalone、保留完整区间）：
  - 删 standalone **《5》**（range 中间项、区间字面不含）→ **code1** 逐字 `FAIL markers ... (need 《5》)`，其余 7 文件 ok、FAIL order False（不连带）；
  - 删 standalone 《3》 / 《6》（区间**端点**、被区间《3》–《6》字面满足）→ **code0**（substring 检测无法区分 standalone 与区间里的同名词）。
- 真实盲区＝**《5》**：与 N1《4》完全同模式（都是 range 中间项、区间字面不含、必须靠 standalone），此前漏网。
- 《3》/《6》 物理上无法用 substring 独立触发（删表格 token 区间仍满足），属与轮次54 map/rewrite/pointer 同类的不可触发冗余分支；收紧需改 guard 检测逻辑（属行为变更、非 eval-only），且区间本身已声明《3》/《6》 Hold，有意不造负向，仅在 docstring 钉明边界。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/risk_matrix_guard_selftest.py`（#41）：新增 **N11**（只删表格 `《5》Promptfoo`→`Promptfoo`、区间完整保留，要求 code1 + need 《5》 + sibling ok），negative 10→11，计数扩为 **`11 negative, 2 non-flag, 2 healthy, 1 mutation`**；同步 docstring（N11 + 《3》/《6》端点边界）、进度分母 /10→/11、收尾散文；把 `sibling_ok` 定义前移到 N1 之前（N11 早于原位）。
2. `evals/promptfooconfig.yaml`：#41 description 补 range 中间项《4》/《5》与端点不可区分说明、计数 value 10→11；cases=42、scripts=42。
3. `evals/README.md`：#41 文件表行、长描述行、明细表行（整行计数）、专节（10→11 negative 并补 N11 与端点边界）同步。
4. 本日志小节。

### 评估驱动证据

- N11 先在真实 guard 上 /tmp 探针逐字取证（need 《5》 + 其余 7 文件 ok + order 不连带）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式 also_ok 断言兄弟文件不连带；
- 不新增 case、不改 guard/fixtures/runner，纯补 #41 反缩写契约 range 中间项《5》present-but-weakened 判别；既有 N1–N10、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 12:34 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-Jjm-2026-09-23T04:34:57`（Duration 4s，0 error）。

### 合并后权威回归（功能 PR #183 已 squash-merge）

- 功能 PR #183（分支 test/risk-matrix-subtask5-negative，commit 7390d32，4 files）required 三检 + CodeQL + Cursor Approval(1m8s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `f7e5e05ffb219e89b3bd7615d684a43f1b6c0388`（远端分支已删）；`gh api` 核实合并 commit：structure: success、contracts: success、boundary: success。
- 回 main（=origin/main `f7e5e05`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-u7L-2026-09-23T04:41:57`（Duration 4s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- matrix 反缩写契约对端点《3》/《6》无法用 substring 区分 standalone 与区间（探针 code0），已在 docstring 钉明、有意不改 guard；matrix 其余 Hold/Humble/Rolling/blocked/指针 marker present-but-stripped 仍零负向，待下一轮按权重评估。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #183 已合并（main `f7e5e05`），合并后权威回归 42/42、0 error（eval `eval-u7L-2026-09-23T04:41:57`），本回填 PR 即补登。
2. #41 反缩写中间项已补齐；继续评估 matrix 其余安全词（Hold / Humble·Rolling / blocked）present-but-stripped 是否独有未覆盖，先探针论证、不凑数；或转 #42 per-file marker 复查。
3. existence-only helper 签名趋同再抽（单独 PR、行为不变）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 66 — 2026-09-23 13:28（Asia/Shanghai）— 给 #41 risk_matrix 补 matrix 自身总 Hold 立场 / 跨机 blocked 诚实词删除负向 N12/N13（功能 PR #185，main fb1ada1）

### 只读取证（接续轮次65 下一步第2条）

- Read guard `check_risk_matrix.py`（139 行）：matrix 走 19-marker `_MATRIX_MARKERS`。原 selftest 对 matrix 文档本身 present-but-stripped 只覆盖三个具体 Hold 禁令词（N4/N5/N6 Agnocast/zenoh/Cega）与反缩写中间项（N1/N11 《4》/《5》）；matrix 文件保留却删其**总立场/诚实词**零负向。
- grep 出现次数：Hold 14、Humble 5、Rolling 3、blocked 4、§9.4 8、fastdds.xml 8、SCOREBOARD 11。
- 探针（matrix 文件保留、replace 删词，其余 7 文件不动）：
  - 删总 **Hold** 立场 → code1 逐字 `FAIL markers ... (need Hold)`，okfile 7、FAIL order False（不连带）；
  - 删跨机 **blocked** 诚实词 → code1 逐字 `FAIL markers ... (need blocked)`，okfile 7、FAIL order False；
  - 删 Humble / Rolling 同样 code1 点名、不连带（本轮先不取，见下）。
- 真实盲区＝matrix 自身的 **Hold（总立场）** 与 **blocked（跨机诚实）**：N4–N6 是具体禁令词、N7 的 Hold 在 R0 文件，matrix 丢自己的总 Hold 立场或跨机 blocked 判决此前无断言。
- Humble/Rolling 是「Rolling ≠ Humble」版本诚实**一对**，更适合作为独立主题下一轮成对补（本轮有意只取 Hold/blocked，不堆叠）；fastdds.xml/SCOREBOARD/§9.4 是指针/锚点、权重低，有意不加。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/risk_matrix_guard_selftest.py`（#41）：新增 **N12**（matrix 保留、删总 Hold）、**N13**（matrix 保留、删跨机 blocked），均要求 code1 + need 词 + sibling ok（其余 7 文件 ok、order 不连带）；negative 11→13，计数扩为 **`13 negative, 2 non-flag, 2 healthy, 1 mutation`**；同步 docstring（N12/N13 段）、进度分母 /11→/13、收尾散文。
2. `evals/promptfooconfig.yaml`：#41 description 补 matrix 丢总 Hold/blocked、计数 value 11→13；cases=42、scripts=42。
3. `evals/README.md`：#41 文件表行、长描述行、明细表行（整行计数）、专节（11→13 negative 并补 N12/N13）同步。
4. 本日志小节。

### 评估驱动证据

- N12/N13 先在真实 guard 上 /tmp 探针逐字取证（need Hold/blocked + okfile 7 + order 不连带）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式 also_ok 断言兄弟文件不连带、order 不触发；
- 不新增 case、不改 guard/fixtures/runner，纯补 matrix 自身总立场/跨机诚实 present-but-weakened；既有 N1–N11、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 13:28 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-3DJ-2026-09-23T05:28:11`（Duration 7s，0 error）。

### 合并后权威回归（功能 PR #185 已 squash-merge）

- 功能 PR #185（分支 test/risk-matrix-hold-blocked-negatives，commit 26ded20，4 files）required 三检 + CodeQL + Cursor Approval(1m16s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `fb1ada1920c12bb020cf6061b8bd8295db360d21`（远端分支已删）；`gh api` 核实合并 commit：structure: success、boundary: success、contracts: success。
- 回 main（=origin/main `fb1ada1`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-sPB-2026-09-23T05:33:14`（Duration 8s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- matrix 的 Humble/Rolling 版本诚实对 present-but-stripped 仍零负向（探针 code1），留下一轮成对补；fastdds.xml/SCOREBOARD/§9.4 指针锚点权重低有意不加。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #185 已合并（main `fb1ada1`），合并后权威回归 42/42、0 error（eval `eval-sPB-2026-09-23T05:33:14`），本回填 PR 即补登。
2. 给 #41 matrix 补 **Humble/Rolling 版本诚实对**（成对、先探针），或转 #42 per-file marker 复查。
3. existence-only helper 签名趋同再抽（单独 PR、行为不变）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。

---

## 轮次 67 — 2026-09-23 15:17（Asia/Shanghai）— 给 #41 risk_matrix 补 Rolling ≠ Humble 版本诚实对删除负向 N14/N15（功能 PR #187，main b1c3060）

### 只读取证（接续轮次66 下一步第2条）

- Read guard `check_risk_matrix.py`（139 行）：matrix 走 19-marker `_MATRIX_MARKERS`，含版本诚实词 Humble、Rolling。原 selftest 对 matrix 文档 present-but-stripped 已覆盖具体禁令词（N4–6）、反缩写中间项（N1/11）、总 Hold/跨机 blocked（N12/13）；matrix 文件保留却删 **Rolling ≠ Humble 版本诚实对**任一词零负向。
- 语义取证（matrix 行19/行71）：「**Rolling ≠ Humble。** vendor 树是 rolling/master 快照，运行时目标是 Humble，严禁把 vendor 文件直接覆盖发行版树」、表格「Rolling ≠ Humble **严禁** 覆盖」。count：Humble 5、Rolling 3。
- 探针（matrix 文件保留、replace 删词，其余 7 文件不动）：
  - 删 **Humble** → code1 逐字 `FAIL markers ... (need Humble)`，okfile 7、FAIL order False；
  - 删 **Rolling** → code1 逐字 `FAIL markers ... (need Rolling)`，okfile 7、FAIL order False。
- 真实盲区＝版本诚实对两个词：matrix 保留却删任一会让「rolling vendor 不得覆盖 Humble 发行版」契约失去字面锚点，此前无断言；两词成对、各占一个 case（同 N4–6 逐 token 逻辑），防止只删其一时被另一个掩盖。
- fastdds.xml/SCOREBOARD/§9.4 仍是指针/锚点、权重低，有意不加。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/risk_matrix_guard_selftest.py`（#41）：新增 **N14**（matrix 保留、删 Humble）、**N15**（matrix 保留、删 Rolling），均要求 code1 + need 词 + sibling ok（其余 7 文件 ok、order 不连带）；negative 13→15，计数扩为 **`15 negative, 2 non-flag, 2 healthy, 1 mutation`**；同步 docstring（N14/N15 段）、进度分母 /13→/15、收尾散文。
2. `evals/promptfooconfig.yaml`：#41 description 补版本诚实对、计数 value 13→15；cases=42、scripts=42。
3. `evals/README.md`：#41 文件表行、长描述行、明细表行（整行计数）、专节（13→15 negative 并补 N14/N15）同步。
4. 本日志小节。

### 评估驱动证据

- N14/N15 先在真实 guard 上 /tmp 探针逐字取证（need Humble/Rolling + okfile 7 + order 不连带）再写进自测；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式 also_ok 断言兄弟文件不连带、order 不触发；
- 不新增 case、不改 guard/fixtures/runner，纯补版本诚实对 present-but-weakened；既有 N1–N13、non-flag、healthy、mutation 全保持。

### 实测（本机 macOS，2026-09-23 15:17 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-t8X-2026-09-23T07:17:30`（Duration 6s，0 error）。

### 合并后权威回归（功能 PR #187 已 squash-merge）

- 功能 PR #187（分支 test/risk-matrix-humble-rolling-negatives，commit 2e80229，4 files）required 三检 + CodeQL + Cursor Approval(1m47s) 全 pass（reviewDecision APPROVED；mergeStateStatus UNSTABLE 仅因非 required 的 Security Reviewer pending），squash-merge 到 main，mergeCommit `b1c30605b8b07721508db0e61a3869bd8c41c87e`（远端分支已删）；`gh api` 核实合并 commit：structure: success、boundary: success、contracts: success。
- 回 main（=origin/main `b1c3060`）重跑：compileall OK；`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- `npx promptfoo@0.123.1 eval` 合并后权威结果：**42/42 passed (100%)、0 failed、0 errors**，eval `eval-RPX-2026-09-23T07:23:14`（Duration 7s，0 error）。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- matrix 19 marker 中安全权重高的立场/诚实/版本词已全部覆盖（禁令 N4–6、反缩写 N1/11、总 Hold/blocked N12/13、版本对 N14/15）；仅剩 fastdds.xml/SCOREBOARD/§9.4 指针锚点（权重低、有意不加）。#41 matrix 面负向深化基本到顶，下一轮宜转 #42 per-file marker 复查或其他 guard。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·双链 pub/sub/p99/跨机 UDP/三链实际复现仍 `STATUS: blocked`（无 Humble runtime），未伪造。

### 下一步

1. [x] 功能 PR #187 已合并（main `b1c3060`），合并后权威回归 42/42、0 error（eval `eval-RPX-2026-09-23T07:23:14`），本回填 PR 即补登。
2. #41 matrix 面负向已到顶；转 **#42 dual_chain_baseline per-file marker 复查**（27 negative 基础上找独有 present-but-stripped，先探针），或复查其他 guard。
3. existence-only helper 签名趋同再抽（单独 PR、行为不变）。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、Humble Linux 主机解 blocked。
---

## 轮次 68 — 2026-09-23（Asia/Shanghai）— 给 #42 dual_chain_baseline 补四个 Hold 范围标记删除负向 N28–N31（功能 PR #189，main a5cf98c）

### 只读取证

- Read guard `check_dual_chain_baseline.py`（474 行）：baseline 文档强制 27 词 marker 元组 + 4 个独立短语检查 + 反伪造分位数正则。
- 盲区：baseline 中 `《3》《4》《5》《6》` 四个 Hold 范围标记此前无「文件保留却删词」负向。
- /tmp 探针（复用 guard 实读 11 个真实文件）逐字取证：删任一标记均 code1、恰一行 `FAIL markers: docs/architecture/feishu-dual-chain-baseline.md (need 《N》)`，兄弟 ADR 保持 ok，不触发 chain/paused/percentile/missing/map/rewrite；纯复制对照 code0。

### 改动（行为不变，3 文件，eval-only，case 数不变仍 42）

1. `evals/dual_chain_baseline_doc_selftest.py`：新增 N28–N31（27→31 negative），收尾计数 `31 negative, 3 non-flag, 2 healthy, 1 mutation`。
2. `evals/promptfooconfig.yaml`：#42 描述追加、断言 value 27→31（cases 仍 42）。
3. `evals/README.md`：5 处同步（文件表、case42 计数、新增子句、明细表头、详细列表 N28–N31）。README 因 77K 超大无法用 Edit 注册，改用带唯一匹配断言的 Python 精确替换脚本落盘（每处替换前断言 count==1，否则中止）。

### 实测与合并

- compileall OK；`run_all_gates.py` **13/13**；`fingerprint_check.py` **15/15 stable**；25 selftest fail=0；`promptfoo@0.123.1` **42/42 (100%)**，#42 输出含 `31 negative, 3 non-flag, 2 healthy, 1 mutation`。
- 功能 PR #189（分支 round-68-baseline-hold-scope-markers，commit 436f0c1，3 files）required 三检 + CodeQL + Cursor 全 pass，squash-merge 到 main，mergeCommit `a5cf98c`。

---

## 轮次 69 — 2026-09-23（Asia/Shanghai）— 原生 arm64 DDS pub/sub 与时延探针，解除《3》《4》功能 blocked（功能 PR #190，main 39c016d）

### 背景与根因

- 为解真·pub/sub blocked，启动 Colima。本机仅有 `osrf/ros:humble-desktop` 的 **linux/amd64** 镜像，在 arm64 上经 **qemu-user** 模拟：talker 正常发、listener 全收不到（单容器 loopback、强制 UDP-only 亦然，无报错）→ **BUG-H1 High（环境，非 ROS 源码缺陷）**；qemu 下 `ros2 node/topic list` 为空、易误导 → **BUG-H2 Low**。
- Docker Hub SSL 超时、packages.ros.org 证书名不匹配、各国内 docker registry 前缀直拉均失败，无法取得 arm64 jammy（Humble）镜像。
- Colima VM 本体 = Ubuntu 24.04 aarch64 原生、apt 可用；绕过失效代理（`Acquire::*::Proxy=false`），密钥取自 keyserver.ubuntu.com（指纹尾号 F42ED6FBAB17C654），TUNA noble 源，原生安装 **Jazzy**（FastDDS 2.14.6 / rmw 8.4.4、Cyclone）。

### 结果（VM loopback，1000 有效样本 + 300 warmup，100Hz，小 String，RELIABLE/depth10，全部 loss=0；µs）

| 配置(domain) | min | mean | p50 | p90 | p95 | p99 | max | jitter | stdev |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| FastDDS 默认(42) | 187 | 476 | 420 | 696 | 817 | 1163 | 1897 | 743 | 175 |
| FastDDS UDP-only(42) | 280 | 490 | 439 | 698 | 821 | 1055 | 1462 | 616 | 148 |
| Cyclone 默认(0) | 250 | 440 | 388 | 607 | 750 | 1166 | 2585 | 777 | 185 |

- 原生 Jazzy demo talker/listener sanity 听到 11 条（PASS），对照确认 qemu 为失败根因。
- 新增 `hil/`（lat_talker/listener、run_latency/run_fast、测试专用 udp_only.xml、mc_rx/tx、README，9 文件）与 `docs/testing/2026-09-mac-hil-native.md`；新增文件下 gates 仍 **13/13**。
- 功能 PR #190（分支 round-69-native-dds-hil，commit 0907b58）required 三检 + CodeQL + Cursor 全 pass；因 #189 先合导致 BEHIND，`gh pr update-branch` 后 required 三检复跑 pass，squash-merge 到 main，mergeCommit `39c016d`。本地两特性分支已清理。

### 边界与剩余风险

- Jazzy ≠ Humble（FastDDS 2.14.6 vs 2.6.x），本结果是**功能/时延代理，非 Humble 认证**；VM loopback、单机，**跨物理机/真实网卡 p99 仍 blocked**；数字未写入冻结 SCOREBOARD、未编辑 config/fastdds.xml。
- 非阻塞：VM 残留失效代理致 apt 超时；打包脚坑（同批装 Cyclone 满足 rmw 虚拟依赖致 FastDDS 被跳过，需显式装）。
- 外部阻塞不变：4 份飞书文档 3380004、原生 arm64 Humble（jammy 镜像）、跨机测试、CVE 修复三项待批准。

### 下一步

1. [x] PR #189、#190 已合并（main `39c016d`），本回填 PR 即补登轮次 68/69。
2. 取得 arm64 jammy 镜像或 Humble Linux 主机后，重跑 `hil/` 以做 Humble 认证；补第二台主机做跨机/真实网卡 p99。
3. existence-only helper 签名趋同再抽（单独 PR、行为不变）。
4. 外部阻塞：飞书权限、CVE 修复三项待书面批准。

---

## 轮次 70 — 2026-09-24 13:18（Asia/Shanghai）— 给 #26 sink_layers 补两个独有 Hold 策略句删除负向 N3/N4（功能 PR #193，main ffbc30d）

### 只读取证（接续轮次69 下一步，选全仓最薄弱 selftest）

- 盘点 25 个 selftest 的 negative 计数：sink_layers 仅 **2 negative、无 non-flag**，与 bench_gates/gate_registry 并列最少。轮次70 复查 #26 `check_sink_layers.py`（241 行）。
- Read guard：sink 文档走 `_SINK_MARKERS`（含 5 个 `_POLICY_CLAUSES` 连续策略句）+ 六层表格行 `_LAYER_ROW_RE` + 4 个 ABSENT_VENDOR_TREES；原 selftest 只覆盖独有行锚解析器（N1 rcl / N2 DDS），docstring 并声明 policy/marker 删除"由正向用例覆盖"。
- 真实盲区＝sink 文档**独有**、未被其他 selftest 断言的两个策略句：
  - **`AUTO ≠ 已开零拷`**（零拷贝状态诚实：自动共享内存传输≠零拷贝已开，防谎报）；
  - **`没有 vendor/iceoryx`**（iceoryx Hold 策略句）。
  - 其余策略句（不改 XML/SCOREBOARD、不启用 Agnocast/zenoh、《3》–《6》仍 Hold）核心词已在 #41/#20/#27/#42 多处覆盖，不重复；总立场短语 `Hold vs allowed`（出现 6 次）与 risk-matrix 总立场 N12 同模式，留下一轮。
- 探针（sink 文件保留、replace 删句，其余 6 文件不动）：
  - 删 `AUTO ≠ 已开零拷` → code1，**同时** `FAIL markers (need AUTO ≠ 已开零拷)` + `FAIL policy (need `AUTO ≠ 已开零拷`)`，okfile 6、ok layers True；
  - 删 `没有 vendor/iceoryx` → code1，同样 FAIL markers + FAIL policy，okfile 6、ok layers True；
  - （对照）删 `Hold vs allowed` → code1，FAIL markers + FAIL Hold vs allowed，留下一轮。
- policy 句同时在 `_SINK_MARKERS` 与独立 policy 检查中，故删句两道同时 fail，六层行与其他文件不连带。

### 改动（行为不变，4 文件，eval-only，case 数不变仍 42）

1. `evals/sink_layers_guard_selftest.py`：新增 `_check_policy_negatives` 与 **N3/N4**，negative 2→4，计数扩为 **`4 negative, 2 healthy, 1 mutation`**（本 selftest 无 non-flag 类别）；同步 docstring（Scope 改为行锚 + 两独有策略句、列举 N1–N4）、进度分母 /2→/4、收尾散文。
2. `evals/promptfooconfig.yaml`：#26 description 补两策略句、计数 value 2→4；cases=42、scripts=42。
3. `evals/README.md`：文件表行、明细表行（计数 + 子句）、Scope 段、负向场景段（2→4 并补 N3/N4）同步。
4. 本日志小节。

### 评估驱动证据

- N3/N4 先在真实 guard 上 /tmp 探针逐字取证（FAIL markers + FAIL policy 双发、点名、ok layers、6 ok files）再写断言；
- 与 H2 纯复制健康树配对（不删则绿）证明非恒真；显式断言六层行与其余文件不连带、行检查不触发；
- 不新增 case、不改 guard/fixtures/runner，纯补独有策略句 present-but-weakened；既有 N1/N2、healthy、mutation 全保持。
- 中途两次脚本失误（外层三引号内嵌三引号 docstring 致 SyntaxError；收尾散文锚点漏字面 `\n` 致 count 0）均在 write_text 前被拦下、文件未损坏，改用注释与小锚点后通过。

### 实测（本机 macOS，2026-09-24 13:18 CST）

- compileall OK；#35 注册面 PASS（25 selftest markers ↔ yaml 42 一致）；#36 doc_link PASS；
- `run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**（fixtures 零改动）；25 个 selftest fail=0；
- `npx promptfoo@0.123.1 eval`：**42/42 passed (100%)、0 failed、0 errors**，合并前 eval `eval-dAz-2026-09-24T05:18:34`（Duration 5s，0 error）。

### 合并后权威回归（回填）

- 功能 PR **#193**（分支 test/sink-policy-clause-negatives）required 三检 + CodeQL + Cursor Approval 全 pass、reviewDecision APPROVED，squash-merge 到 main，**mergeCommit `ffbc30d`**，远端分支已删。
- 合并 commit `ffbc30d` 三检经 API 核实最终全 **success**（structure 首轮 conclusion=null、重试后 success）。
- 合并后回 main 实测：`run_all_gates.py` **13/13 all gates green**；`fingerprint_check.py` **15/15 stable**；25 个 selftest fail=0。
- 合并后 promptfoo：首次 `eval-gPM-2026-09-24T05:25:01` 因系统高负载（loadavg≈30、Duration 2m20s）出现 **1 个 provider 层 ERROR（41 passed、0 failed）**——为 #17 fingerprint 串行子进程的已知高负载 timeout flaky、非断言失败；间隔 30s 重跑 `eval-8FM-2026-09-24T05:28:06` 恢复 **42/42 passed (100%)、0 failed、0 errors**（Duration 5s），以此为合并后权威结果。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge/vendor/shell/load.py；未重写 Bridge runtime；未碰 ci.yml / guard 代码 / 15 个指纹 fixtures；改动纯标准库 eval + tempdir/内存，无新依赖、不在树内建 fixture；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动；case 数不变（42）。
- sink_layers negative 2→4，行锚与两独有策略句已覆盖；总立场短语 `Hold vs allowed` present-but-stripped 留下一轮；其余直白 marker（eCAL/DPDK/Isaac 等）权重低或与正向同形，有意不加。
- existence-only 放行/seed helper 仍在 #20/#27/#42/#41 四处签名不同；真·跨物理机/真实网卡 p99、Humble 认证仍 `STATUS: blocked`（轮次69 仅 Jazzy loopback 代理），未伪造。

### 下一步

1. [x] 功能 PR #193 已合并（main `ffbc30d`），合并后 gate 13/13、fingerprint 15/15、25 selftest fail=0、promptfoo 42/42（权威 eval `eval-8FM-2026-09-24T05:28:06`）；本回填 PR 即补登。
2. 给 #26 sink 补总立场短语 `Hold vs allowed` present-but-stripped 负向（与 risk-matrix 总立场 N12 同模式）。
3. 继续次薄弱 selftest（bench_gates / gate_registry 各 2 negative）的独有边界复查，先探针。
4. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、arm64 jammy/Humble 主机与跨机测试。

## 轮次 71 — 2026-09-24 14:14（Asia/Shanghai）— 给 #26 sink_layers 补总立场短语 Hold vs allowed present-but-stripped 负向 N5（功能 PR TBD）

### 改了什么

- 承接轮次70（#26 已 4 negative），补 sink 文档**总立场裁决短语** `Hold vs allowed` 的 present-but-stripped 负向 **N5**，与 risk-matrix N12（matrix 自身总 Hold 立场）同模式。
- 只读取证：该短语在 sink 文档出现 **6 处**（行3 Status 副标题、行22 核对指针、行26 章节标题、行32 表头列名、行73 success marker 描述、行77 表格描述）。guard 对它只做**全文 contiguous-phrase 存在检查**（`"Hold vs allowed" in text`，marker + 行183–187 独立检查），**单点删除（如表头列）仍被其余 5 处救回**，故负向变异必须 `text.replace("Hold vs allowed","")` 移除全部 6 处。
- 新增 `_check_stance_negatives`：全删后探针逐字证实 **code 1**、`FAIL markers (need Hold vs allowed)` + 独立 `FAIL Hold vs allowed`，而六层行 `ok layers`、5 个 policy 策略句 `ok policy`、其余 6 文件 `ok file`（stance 检查独立于 policy，不连带）。
- negative 4 → **5**，分母 /5，收尾计数 `5 negative, 2 healthy, 1 mutation`（本 selftest 无 non-flag）；同步 yaml #26 description/value、README 四处（文件表/明细表/Scope/负向场景）；case 数不变（42）。

### 分数前后对比

| 项 | 轮次70 | 轮次71 |
|---|---|---|
| gate | 13/13 exit 0 | **13/13 exit 0** |
| fingerprint | 15/15 stable | **15/15 stable**（fixtures 零改动） |
| promptfoo | 42/42 (100%) | **42/42 (100%)、0 error** |
| #26 sink negative | 4 | **5** |
| selftest | 25 fail=0 | **25 fail=0** |

- 合并前 promptfoo `eval-ADt-2026-09-24T06:14:22`，42/42、0 failed、0 errors，Duration 7s。

### 产物检查结果

- compileall OK；#35 eval_registry PASS（42 case/42 script 双向一致、#26 SUCCESS/STABLE 在 yaml 被断言、README 标题计数 42）；#36 doc_link PASS；
- gates 13/13、fingerprint 15/15、25 selftest fail=0；
- 纯标准库 eval + tempdir/内存，未新增脚本/fixture/依赖、不在树内建 fixture。

### Hold 合规

未编辑 config/fastdds.xml / SCOREBOARD（仅 tempdir 副本，原文件只读）；未启用 Agnocast/zenoh、未集成 Cega；未改 dimos_bridge / vendor / shell / load.py / ci.yml / guard 代码 / 15 个指纹 fixtures；未重写 Bridge runtime；promptfoo 仅 npx 缓存；受保护旧草稿 docs/01-dds-request-flow.md 保持未跟踪未提交。

### 剩余风险

- 行为不变（仅加强 eval 断言与文档），guard/runner/公共 API/fixtures 零改动，case 数不变。
- 总立场检查本质是**全文存在性**、不保护具体某一处（单点删除被冗余救回）——这是 guard 现状，N5 已如实钉明；若未来要锚定具体位置需改 guard，属独立任务。
- 真·跨物理机/真实网卡 p99、Humble 认证仍 `STATUS: blocked`（轮次69 仅 Jazzy loopback 代理），未伪造。

### 下一步

1. 本功能 PR 合并后：回 main 跑合并后全套回归（应 42/42、0 error），开 docs-only 回填 PR 把功能 PR 号 / main HEAD / 合并后 eval ID 补进本小节。
2. sink 行锚/策略/总立场已较完整；转向次薄弱 guard（bench_gates / gate_registry 各 2 negative）的独有边界复查，先探针。
3. 外部阻塞不变：workflow scope、CVE 修复三项待批准、4 份飞书文档 3380004、arm64 jammy/Humble 主机与跨机测试。

