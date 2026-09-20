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
| Eval 通过率 | `npx --yes promptfoo@0.123.1 eval -c evals/promptfooconfig.yaml`（仓库根执行） | 23 个 DDS 行为断言用例（custom provider 跑 gate 脚本 / `load.py print-a|b` + stdout contains 断言；#17 为全量 stdout 指纹回归；#18 为 frozen-path guard 的负向自测；#19 为双链 env 交叉断言 guard 的负向自测；#20 为 Unitree Cyclone 交换裁决 guard 的负向自测；#21 为 ros2-source-map guard 的负向自测；#22 为 Executor/WaitSet map guard 独有分支的负向自测；#23 为产品 DoD 诚实性 guard 反伪造逻辑的负向自测） |

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

> 定时任务第 17 轮。分支 `test/dod-evidence-guard-selftest`，PR 编号以实际返回为准（合并后由 docs-only 回填 PR 补登）。
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
- 合并后回归结果由 docs-only 回填 PR 补登（同轮次 13–16 两段式惯例）。

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
