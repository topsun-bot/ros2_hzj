# 《Rust 重构 ROS 2 DDS》迁移方案（ros2_hzj）

- 日期：2026-11-19
- 状态：**计划已获用户批准（2026-11-19，迁移计划 v1），进入 Phase 0 脚手架实施。** 路线裁决为 R2 终态 + 分阶段证据门禁（终态不改、施工不可跳步），代码落同仓 `rust/` D 面，colima+Docker 跑 Humble 互通，push 限 feature 分支开 PR（merge 归人类）。决策与 Hold 边界已制度化于 [rust-rmw-adr.md](../architecture/rust-rmw-adr.md)；Phase 0 仅新增隔离骨架与文档、默认链零变化，Phase 4 的 C-ABI shim 仍须人类 `allow-hold-bypass` + 专门 ADR。
- 边界：遵守根 [AGENTS.md](../../AGENTS.md)。不编辑 `config/fastdds.xml`、`docs/artifacts/bench/SCOREBOARD.md`、`vendor/**`、`dimos_bridge/dimos/**` 运行时；不启用 Agnocast / zenoh / Cega；《3》–《6》在根 AGENTS.md 中仍为 Hold，本文只登记现状与解锁条件，不自行突破。
- 方法论输入：Anthropic《How Anthropic runs large-scale code migrations with Claude Code》六步法（<https://claude.com/resources/articles/ai-code-migration>），按本仓"文档+闸门"实际形态裁剪，不照搬其多代理流水线。
- 前序文档：[01-dds-request-flow.md](01-dds-request-flow.md)（《1》代码流）、[02-modernization-plan.md](02-modernization-plan.md)（《2》Python 面现代化）、[ITERATION_LOG.md](ITERATION_LOG.md)（轮次 1–75）。本文不重复其结论，只引用。

---

## 0. 结论先行（TL;DR）

1. **本仓没有"自己的 DDS"可重构。** 运行时 DDS 是上游 C/C++ 整树拷贝（`vendor/`，只读冻结）与 Humble apt 包；本仓自有代码是 13 个 Python 闸门、bench 脚本和 `dimos_bridge` 只读拷贝，**当前零 Rust 代码**。"用 Rust 重构 ROS2 DDS"本质是**新建一条 Rust 技术线**，不是对现有自研代码的翻译。
2. **重构对象的量级是数十万人月级别，不能一次性重写。** 仅上游自有核心代码：Fast-DDS `src/` 约 **24.7 万行**、CycloneDDS `src/` 约 **34.4 万行**，外加两个 RMW 适配层约 4.1 万行（实测 `wc -l`，见 §2）。完整 DDS/RTPS 纯 Rust 等价物属于多人数年工程。
3. **Rust 生态在 2026 年已有可用砖块，但没有可直接 drop-in 的成熟纯 Rust RMW。** 纯 Rust DDS 实现以 RustDDS 0.15.1 为代表（可与 ROS 2 互通）；官方 rclrs 等是 rcl 之上的客户端库，**底层 DDS 不变**；自称带 rmw C 层的 HDDS 仅 0.1.0。详见 §3。
4. **推荐 strangler（绞杀者）路线 R3**：新代码全部进新目录/新仓，先建"对等裁判（judge）"再做垂直薄切片，以**线协议互通证据**为每阶段门禁；保留 Fast-DDS / Cyclone 双链为默认，Rust 线长期 opt-in，绝不 in-place 替换。这与本仓既有的 `unitree_sdk2_hzj` + `UNITREE_DDS_PROVIDER=external` 合法换库模式同构。
5. **当前有 7 个硬阻塞（§10），最关键的三个**：飞书问题清单文档 3380004 无权限（《2》指定输入读不到）；《4》测试用例仍是占位符且混入与中间件无关的"注册/计费"模板；GitHub push 与新仓创建属于不可逆动作，尚未获本次会话授权。**在这些解除前，工作停在方案层。**

---

## 1. 勘察事实（2026-11-19 本机实测，可复跑）

| 项 | 实测结果 | 命令 / 证据 |
|----|----------|-------------|
| 工作区性质 | Python 闸门 + 文档 + vendor 只读快照；75 轮迭代全部是 guard/文档/eval，无 DDS 运行时改造 | `git log --oneline`；[ITERATION_LOG.md](ITERATION_LOG.md) |
| Rust 代码 | 0 个 `.rs` / `Cargo.toml` | `find . -name '*.rs'` |
| 当前闸门基线 | **13/13 exit 0，all gates green** | `python3 scripts/run_all_gates.py` |
| Promptfoo 基线 | 轮次 75 记录 **42/42 (100%)、0 error**；本会话未重跑（npx 拉取耗时） | [evals/promptfooconfig.yaml](../../evals/promptfooconfig.yaml)、ITERATION_LOG 轮次 75 |
| Rust 工具链 | cargo / rustc **1.99.0** 已装（`~/.cargo/bin`） | `cargo --version` |
| ROS 运行时 | `/opt/ros` 不存在；colcon 可执行但无底层；Docker 已装但 **colima daemon 未启动**（`Cannot connect to the Docker daemon`） | `ls /opt/ros`；`docker ps` |
| Node / Promptfoo | node v22.23.2、npx 可用 | `node --version` |
| GitHub 身份 | `gh` 已登录 `yixinzhangagent`（SSH）；轮次 75 记录该 token **无 `workflow` scope** | `gh auth status`；ITERATION_LOG 剩余风险 1 |
| 现有 remote | `origin = https://github.com/topsun-bot/ros2_hzj.git`，分支 main 与 origin 同步 | `git remote -v` |
| 飞书文档 | 《2》指定文档 `CsjGd7Dq...` 返回 **3380004 无权限**；轮次记录显示 4 份飞书文档同症 | `lark-cli docs +fetch` 实测错误体 |
| 未跟踪文件 | `docs/01-dds-request-flow.md`（478 行，轮次 75 注明"受保护旧草稿，保持未跟踪未提交"） | `git status`；本方案不触碰它 |

---

## 2. 真实重构对象：规模与边界

### 2.1 代码量实测（`vendor/`，含头文件；2026-11-19 `wc -l`）

| 树 | 文件数 | 总行数 | 其中 |
|----|-------:|-------:|------|
| `vendor/Fast-DDS/` | 3,870 | 1,621,030 | `src/` 自有 **247,077**；`thirdparty/`（asio/fastcdr/tinyxml2 等）488,035；余为 IDL/示例/fuzz |
| `vendor/CycloneDDS/` | 858 | 351,531 | `src/` 核心 **344,368** |
| `vendor/rmw_fastrtps/` | 222 | 28,995 | RMW C ABI 适配（三个子包） |
| `vendor/rmw_cyclonedds/` | 23 | 11,592 | RMW C ABI 适配 |
| `vendor/rmw/` | 117 | 17,666 | RMW 接口契约（头文件为主） |
| `vendor/rmw_implementation/` | 25 | 8,822 | 动态装载器 |

信封背面估算：一个可用的 RTPS 线协议 + DDS 子集（发现、History、可靠/best-effort、基础 QoS、CDR）开源工程普遍在**十万行量级、1–2 人年起步**达到"能与 ROS 2 通话"；补齐 RELIABLE 重传状态机、全 QoS 策略、Security（DDS-Security 插件）、SHM/zero-copy、兼容性认证则是**数人年**。这还不含 RMW C ABI 适配层与长期互操作回归。结论：**可行，但必须切片、必须有对等裁判、必须长期双栈并存**。

### 2.2 三个不可逾越的语义事实（来自《1》代码流，不在此重复论证）

1. **RMW 是真实抽象边界**：`rcl_publish → rmw_publish（动态分派）→ 厂商实现 → DDS DataWriter → RTPS → transport`。替换发生在 RMW 之下或其本身，app/rcl 层可以不动。
2. **线协议互通是硬需求，不是可选测试**：链 A 域 42（Fast-DDS）要与既有导航/Foxglove 通话；链 B 域 0 要与 Unitree 机内 bundled Cyclone 0.10.2 通话。Rust 实现必须在**同一 RTPS 网络上被对端发现并正确收发**，否则没有产品意义。
3. **运行时是 Humble、vendor 是 rolling/master 快照**（[feishu-runtime-provenance.md](../architecture/feishu-runtime-provenance.md)）。任何 Rust 线的认证目标先钉 **Humble 互操作**，不得拿 rolling 头文件行为替代。

### 2.3 可改面 / 只读面（沿用 02 计划的分层，Rust 线默认落在全新 D 面）

| 面 | 路径 | Rust 迁移能否动 |
|----|------|----------------|
| A. 自有闸门/契约/文档 | `scripts/*.py`、`config/env/*`、`docs/**`、`evals/**` | 可新增、小步改；命令名/exit code/marker 契约不变 |
| B. 只读运行时拷贝 | `dimos_bridge/dimos/**` | 不改；需要时只登记独立任务 |
| C. 冻结面 | `vendor/**`、`config/fastdds.xml`、`SCOREBOARD.md` | **禁改** |
| **D. Rust 新技术线（本方案新增）** | 建议 `rust/`（同仓新目录）或独立新仓；二者取舍见 §7 | **全部新增，不修改 A–C 任何现有文件即可独立编译测试** |

---

## 3. Rust 生态选型核实（2026-11，来源见 §12）

| 砖块 | 形态 | 2026 状态 | 对本任务的意义 |
|------|------|-----------|----------------|
| **RustDDS**（Atostek，crate `rustdds`） | 纯 Rust DDS + RTPS | 0.15.1（2026-10-29）；文档自述"complete enough to do data exchange with ROS2"；内置 `ros2` 模块已废弃，官方改推 `ros2-client` | R2/R3 的 DDS 内核首选候选；版本号仍在 0.x，API 未稳定，需 vendor 钉版本 + 锁依赖 |
| **rclrs**（ros2-rust 官方） | Rust 客户端库，绑定 C `rcl` | FOSDEM 2026 有官方演讲；覆盖 pub/sub/service/action/parameter，支持 zero-copy；底层仍走现有 RMW/DDS | 只支撑 R1（节点 Rust 化），**不替换 DDS** |
| **R2R** | 异步 Rust 绑定（rcl ABI） | 学术评测持续（arXiv 2505.21323） | 同上，R1 候选 |
| **safe_drive / oxidros-rcl** | 形式化验证（TLA+）的 rcl 绑定 | safe_drive 0.4.3；oxidros 为其 fork，0.5.x（2026-03），支持 Humble/Jazzy + Cyclone/FastDDS | R1 候选；其 executor 无饥饿证明对实时任务有参考价值 |
| **HDDS** | Rust DDS，带 C/C++/Python/TS SDK 与 **rmw(C) 层**，宣称 Humble/Iron/Jazzy、no_std | 仅 0.1.0（2026-02），106K SLoC，新仓生态未经验证 | 持续观察，不进首阶段生产路径 |
| 缺口 | 成熟、被广泛采用、可替换 `rmw_fastrtps_cpp` 的纯 Rust **rmw implementation** | 不存在现货；HDDS 最接近但成熟度不足 | R2 的 shim（`rmw_rustdds_hzj`）需要自研，这是主要工作量与风险所在 |

选型原则（对应长期偏好中的"port 薄层、零外部依赖、前后向兼容"）：Rust 线把平台/FFI/网络差异收敛到薄 `port` 层；核心库保持可在 vanilla macOS 上 `cargo test`；所有外部 crate 钉精确版本 + 锁文件入库（确定性优先）。

---

## 4. 三条路线对比与推荐

| 维度 | R1 客户端 Rust 化 | R2 自研纯 Rust RMW（全量替换取向） | R3 strangler 渐进（推荐） |
|------|------------------|-----------------------------------|--------------------------|
| 做什么 | 用 rclrs/R2R 写新节点；DDS 仍是 Fast/Cyclone | | 基于 RustDDS 写 `rmw_rustdds_hzj`（extern "C" 实现 `rmw.h` 全套） | 新目录独立 workspace：先 judge，再 Rust 旁路工具/单 topic 薄切片，证据达标后才决定是否做 R2 shim |
| 是否"重构 DDS" | 否（换语言写应用） | 是 | 分阶段回答：先证明能力，再决定深度 |
| 起步工作量 | 小（周级） | 极大（shim + 互操作认证，年级） | 中（Phase 0–1 月级可见证据） |
| 线协议风险 | 无（不经手） | 全部自担 | 每阶段用互通测试提前暴露，失败可停在工具层 |
| 对双链 Hold 的冲击 | 无 | 高（需要 allow-hold-bypass 与新 RMW 名） | 低（长期 opt-in，默认链不变） |
| 回滚成本 | 删除节点即可 | 高 | 任意 phase 可整体停用，默认链不受影响 |
| 可验证性 | 现有 rcl 测试 | 需自建全套 conformance | judge 与切片同步建设，每步可证 |
| 适配本仓程度 | 可作为 Phase 1 的练兵 | 不作为起步承诺 | **推荐主干**；R1 作为其中的人员/工具热身，R2 作为 Phase 4 的可选决策门而非既定承诺 |

**推荐 R3 的理由**：本仓前 75 轮最强的资产是"诚实闸门文化"（map ≠ reproduce、STATUS: blocked、禁止伪造分位）。R3 把这种文化延伸到 Rust：没有互通证据之前，不宣称替代；每个 Phase 都有退出门，投入可在任意决策门止损。

---

## 5. Anthropic 六步法在本仓的落地映射

六步法的前置条件是"strong judge（对等裁判），且要先用故意破坏的代码验证裁判真会红"。本仓已有裁判文化，但现有 13 gate 守的是文档/契约，**无法裁判 Rust 工件行为**，必须新建第二层 judge。

| 六步法 | 本仓落地 |
|--------|----------|
| 前置：可移植 judge | 新建 Rust 裁判套件（§6 Phase 1）：CDR 序列化 golden samples、RTPS 报文捕获/回放对照、与 Humble 容器的跨实现 pub/sub 互通、pingpong 时延分布对照。裁判先对现有 Fast/Cyclone 跑出基线，再用变异样本验证它会变红 |
| 1. rulebook + 依赖图 + gap 清单 | rulebook：Rust FFI/unsafe/错误处理/实时性编码规约（unsafe 必须注释论证不变量，对应既有偏好）；依赖图：以 `vendor/rmw/rmw/include/rmw/rmw.h` 为 shim 契约根，逐符号标注覆盖状态；gap 清单：RustDDS 未覆盖的 QoS/Security/SHM 列表 |
| 2. 压力测试规则 | 选 1 个最简单消息类型做两次独立实现（直译式 vs 资深工程式），diff 反过来修 rulebook；产物丢弃，只留规则 |
| 3. 翻译/实现 | 仅对已裁决要做的模块扇出；不追求全量翻译上游，按垂直切片推进 |
| 4. 编译 | `cargo build --workspace` + clippy `-D warnings` + rustfmt 检查进入 CI 新 job |
| 5. 冒烟 | loopback 自测 → 与 RustDDS 自测互通 → Humble 容器跨实现互通，逐级扩大 |
| 6. 行为对齐 | 同一 topic/QoS/载荷下，Rust 线与 Fast/Cyclone 的收发正确性、延迟分布（p50/p95/p99 + 抖动）对照；未达标只记 blocked，不写 PASS |

---

## 6. 分阶段路线图（每阶段含进入条件、交付物、验证、退出门）

### Phase 0 — 决策门与脚手架（获批后；全部可逆，不接网络运行时）

- 进入条件：用户确认目录策略（§7 D1）、批准新建分支/PR 策略。
- 交付：`rust/` Cargo workspace 骨架（空 lib + bin）、`rust/README.md` 声明 Hold 边界与"非默认 RMW"、`.gitignore` 加 `target/`、根 AGENTS.md 增补 Rust 线命令（仅文档行）、依赖锁文件。
- 验证：`cargo test`（空测试绿）、`cargo clippy --all-targets -- -D warnings`、原有 `python3 scripts/run_all_gates.py` 仍 13/13。
- 退出门禁：CI 原有三 job 零改动全绿；新增 Rust job 为**独立可选 job**，失败不阻断旧闸门（初期）。

### Phase 1 — judge 先行（不写生产 DDS，只写裁判与观测）

- 交付：(a) CDR golden-sample 生成器与固定夹具（从真实消息类型导出，种子固定）；(b) Rust 版 pingpong 探针（先只打 loopback，复刻 `scripts/bench/pingpong.py` 的统计口径 p50/p95/p99/到达间隔）；(c) 一份 gap 清单文档（对照 `rmw.h` 符号与 RustDDS API）。
- 验证：裁判对现有 Python 探针结果可复跑；变异 CDR 字节必被裁判判失败（证明裁判不是橡皮图章）；指纹思路沿用 `evals/fingerprint_check.py`。
- 退出门禁：在无 ROS 的 macOS 上纯 Rust 测试全绿；文档明确"尚未与任何 ROS 节点互通"。

### Phase 2 — 垂直薄切片：单消息类型、best-effort、UDP loopback 互通

- 交付：Rust 发布者与订阅者各一，载荷选 IMU 64B 场景同款定长结构；基于 RustDDS；与一个 Humble 容器内 `ros2 topic pub/echo`（或 C++ demo 节点）做**跨实现**互通。
- 验证：双向发现、双向收发、CDR 字节级一致；丢包/乱序下 best-effort 语义正确；抓包归档到 `docs/artifacts/rust/`（新目录，不碰 bench/SCOREBOARD）。
- 退出门禁：互通证据可复跑且有第二实现对照；失败即停，记录 blocked，不扩大 QoS 面。
- 前置环境：需要 colima/Docker 启动 Humble 镜像（当前 daemon 未运行，见 D5）。

### Phase 3 — QoS 与可靠性扩展（按 02 计划已冻结的 QosContract 逐项对齐）

- 交付：RELIABLE + History(KEEP_LAST/ALL) + depth、domain 隔离、生命周期/发现稳定性；每加一项补一组对照测试。
- 验证：与 Fast-DDS（域 42 测试实例，非生产 XML）和 Cyclone 11.0.1 双侧互通；重传/ACKNACK 行为抓包佐证。
- 退出门禁：每项 QoS 有独立证据文件；任何"线协议行为不一致但测试碰巧通过"的情况打回。

### Phase 4 — 决策门：是否投入 `rmw_rustdds_hzj` C ABI shim

- 这是**人工决策点，不是自动继续点**。仅当 Phase 2/3 证据稳定、gap 清单收敛、用户明确批准突破 Hold 时启动。
- 交付：独立包，实现 `vendor/rmw/rmw/include/rmw/rmw.h` 所需符号子集；`RMW_IMPLEMENTATION` 可显式指定；默认链 A/B 完全不变。
- 验证：rclcpp/rclpy 标准 demo 节点在该 RMW 下通过；与两条既有链三方共存不互扰。
- 门禁：通过 `allow-hold-bypass` 流程（见 [ci-cd-gates.md](../architecture/ci-cd-gates.md)），并先有书面 ADR。

### Phase 5 — opt-in 双栈试运行与性能证据

- 沿用 `unitree_sdk2_hzj` 模式：环境变量显式选择，不做 in-place overwrite；同主机对照跑分，跨机 UDP 仍需第二台物理机（当前长期 blocked，不得伪造 p99）。
- 退出门禁：达到用户在《3》中要求的"评分 >90%"才谈默认切换；在此之前 Rust 线永远是可选项。

---

## 7. 目录、仓库与 CI 策略

| 决策点 | 选项 | 倾向 |
|--------|------|------|
| 代码位置 | (a) 本仓 `rust/` 子目录；(b) 独立新仓（如 `topsun-bot/dds_rs_hzj`） | 倾向 (a) 起步：证据/闸门/文档同仓，复用现有 PR 评审与诚实性文化；Phase 4 shim 成熟后若要独立发版再拆仓 |
| 依赖策略 | crate 精确钉版 + `Cargo.lock` 入库 + 供应商镜像可行性评估 | 确定性优先；新增第三方 crate 走 ADR |
| CI | 新增独立 `rust` job（fmt/clippy/test），不改 structure/contracts/boundary 三旧 job | 防止新线波动污染既有 100% 基线 |
| 提交方式 | 每 Phase 内小 PR，单个 PR 不超过约 50 个文件（用户硬约束），不做无关重构 | 沿用轮次 1–75 的小步 PR 模式 |
| GitHub 权限 | push/建仓需用户批准；`workflow` scope 缺失需用户本机 `gh auth refresh -s workflow` | 本轮不执行任何 git push |

---

## 8. 《1》–《6》逐项裁决（现状 + 本方案如何承接）

| 子任务 | 仓内现状（证据） | 裁决 |
|--------|-------------------|------|
| 《1》请求流/模块/验证/陷阱/阅读清单/测试命令 | 已完整产出：根 `docs/01-dds-request-flow.md`（478 行，7 章 + 附）与 `docs/refactor/01-dds-request-flow.md`（229 行，含四问四答） | **已完成，无需重写**；Rust 线的代码流地图在 Phase 1 gap 清单中增量补充 |
| 《2》现代化重构（行为不变、小步、识别死代码） | [02-modernization-plan.md](02-modernization-plan.md) 已给四步 A 面计划；飞书输入 3380004 无权限，问题来自本仓 grep 证据 | 继续有效；Rust 线是其 §6"独立迁移任务"的具体化。**飞书原文仍缺，需授权（D2）** |
| 《3》评估驱动改进循环（目标 >90%） | 13/13 gate、15/15 fingerprint、42/42 promptfoo（轮次 75）均已 100%；但裁判对象是 guard/文档，**不是 DDS 时延**；真实跨机 p99 长期 blocked | 百分比目标对现有 judge 已达成；对 Rust DDS 的 judge 从 Phase 1 另建，两套分数分开报告，不合成为一个虚假总分 |
| 《4》Mac/预发布测试（含注册、邀请、计费） | [docs/testing/2026-09-mac-hil.md](../testing/2026-09-mac-hil.md) 已做过诚实分诊：本机无 ROS runtime，选了三个实际可跑用例；"注册/邀请队友/升级计费"与本中间件仓无关，疑为通用模板误贴 | **用例占位符必须由用户填实（D3）**；计费/注册类在本仓无对应系统，建议明确剔除；Rust 线测试在 Phase 2 随 Docker/Humble 环境补齐 |
| 《5》Promptfoo 套件 | 已存在且成熟：custom local-script provider、42 用例、25 个负向自测、README 含最小评估计划 | 无需新建；Rust judge 以 cargo 原生测试为主，必要时再按同模式新增 provider，不提前造 |
| 《6》CVE 只读审计 | [docs/security/2026-09-vendor-cve-audit.md](../security/2026-09-vendor-cve-audit.md) 已完成：Unitree Cyclone 0.10.2 命中 CVE-2024-10838 / CVE-2025-67109；tinyxml2 需验证；三项修复待批准 | 本轮用户未给新公告编号（D4），不重复审计；Rust 线自身供应链安全在 Phase 0 依赖策略中预防（钉版、`cargo audit` 入 CI） |

---

## 9. 风险登记册

| # | 风险 | 触发条件 | 缓解 / 证据要求 |
|---|------|----------|----------------|
| R1 | RTPS 线协议不兼容（发现、DATA/DATAACK、分片） | Phase 2 跨实现互通 | 抓包归档 + 双向（Rust 发/收各测）；不通过即 blocked |
| R2 | CDR 序列化细节差异（字节序、encapsulation、DHE/key） | 任何非定长消息 | golden samples 字节级比对，先定长后变长 |
| R3 | QoS 语义缺口（Reliability/History/Durability/Deadline 等） | Phase 3 | 逐 QoS 独立用例 + 双厂商对照，禁止"一个 demo 全绿"式推断 |
| R4 | 无声地改变实时行为（抖动、线程调度、内存分配） | shim 上线 | 沿用 p50/p95/p99 + 到达间隔口径；无隔离 CPU 的机器只出 loopback/同机数据，标注噪声限制 |
| R5 | SHM / DataSharing / zero-copy 无对等实现 | 需要同机零拷贝时 | 首版仅 UDP；零拷贝列为后续独立 ADR，不承诺时间点 |
| R6 | DDS-Security 空白 | 现场启安全插件 | 首版明确不支持并在文档声明；RustDDS 安全能力进入 gap 清单跟踪 |
| R7 | 上游 crate 0.x API 破坏（RustDDS 仍 0.15） | 升级时 | 钉版 + lock + 升级走独立 PR + 全套 judge 回归 |
| R8 | Hold 边界被工程冲动突破 | 任何阶段 | 新线 D 面物理隔离；默认 RMW 不变；shim 必须过 allow-hold-bypass + ADR |
| R9 | 人力/周期误判 | 全周期 | 每 phase 独立可交付可止损；不以"已投入"作为继续理由 |
| R10 | Rust unsafe/FFI 内存安全让步 | shim 与 C 交互 | 每条 unsafe 注释对应编号不变量（并发与内存序论证制度化），clippy + 评审双闸 |

---

## 10. 硬阻塞与待用户拍板事项（本轮停止点）

| 编号 | 事项 | 需要的动作 |
|------|------|-----------|
| D1 | Rust 代码落点：本仓 `rust/` 还是独立新仓 | 用户选定；本方案倾向同仓 |
| D2 | 飞书文档 `CsjGd7Dq...` 3380004 无权限（另有 3 份同症） | 用户在飞书侧给当前账号开阅读权限，或导出 Markdown/PDF 提供本地副本 |
| D3 | 《4》三个测试用例仍是 `[核心用例 1/2]`、`[hero 用例 3]` 占位；"注册/邀请/计费"与中间件仓不匹配 | 用户填实真实用例，或确认沿用 2026-09 Mac HIL 三用例并剔除计费模板内容 |
| D4 | 《6》未给具体安全公告/CVE 编号 | 给出公告链接或 CVE 号；否则沿用 2026-09 审计结论，三项修复仍等显式批准 |
| D5 | Docker/colima daemon 未启动、本机无 Humble | Phase 2 前需用户确认启动 colima 或提供 arm64 jammy/Humble 主机；跨机需第二台物理机 |
| D6 | GitHub push / 新仓 / CI workflow scope | 任何 push 与 `.github/workflows/` 改动均需显式批准；token 缺 `workflow` scope，需用户本人授权刷新 |
| D7 | 路线裁决：是否接受 R3 推荐（而非直接承诺 R2 全量重写） | 用户确认主干路线后，Phase 0 才能动工 |

---

## 11. 获批后 Phase 0 的最小动作清单（预告，不在本轮执行）

1. 新建分支（如 `rust/phase0-scaffold`），新增 `rust/` workspace 骨架与 `rust/README.md`，不修改任何现有文件（`.gitignore` 除外，单行追加 `/target/`）。
2. 新增 CI rust job 的**提案文档**先评，落地随第二个 PR。
3. 本地跑双基线：`cargo test`（空绿）+ `python3 scripts/run_all_gates.py`（仍 13/13），截图/日志归档。
4. PR 描述链接本方案与 Hold 合规声明；变更文件数远小于 50；不做无关重构。
5. 每个动作满足"行为不变"举证：旧 job 全绿、默认链 A/B 环境变量与 RMW 名零变化。

---

## 12. 引用

- Anthropic, *How Anthropic runs large-scale code migrations with Claude Code*: <https://claude.com/resources/articles/ai-code-migration>
- RustDDS 0.15.1 docs（2026-10-29）: <https://docs.rs/crate/rustdds/latest>
- rclrs 官方介绍（FOSDEM 2026）: <https://fosdem.org/2026/events/attachments/J8ZLKG-introducing_rclrs_the_official_ros_2_client_library_for_rust/slides/266838/fosdem_20_yvdpxuz.pdf>
- safe_drive 0.4.3: <https://docs.rs/safe_drive/0.4.3/safe_drive/>
- oxidros-rcl（safe_drive fork，2026）: <https://lib.rs/crates/oxidros-rcl>
- HDDS 0.1.0（含 rmw C 层声明）: <https://lib.rs/crates/hdds-stress>
- 异步 Rust ROS 2 应用评测（arXiv 2505.21323）: <https://arxiv.org/pdf/2505.21323v3>
- 本仓版本钉扎：[../../vendor/VERSIONS.md](../../vendor/VERSIONS.md)；闸门现状：[../../scripts/run_all_gates.py](../../scripts/run_all_gates.py)；CVE 审计：[../security/2026-09-vendor-cve-audit.md](../security/2026-09-vendor-cve-audit.md)
