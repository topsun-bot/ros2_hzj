# Unitree SDK2 DDS swap（vendor Cyclone 11.0.1 ≠ drop-in）

Status: **drop-in FAIL / wire UNPROVEN** — 版本对照记录，不是已测时延、不是飞书现场、不是跨机根因。  
查阅日期：2026-09-12。钉扎来自本仓 [`vendor/VERSIONS.md`](../../vendor/VERSIONS.md)、[`vendor/CycloneDDS/CMakeLists.txt`](../../vendor/CycloneDDS/CMakeLists.txt)，以及只读核对的 [`topsun-bot/unitree_sdk2`](https://github.com/topsun-bot/unitree_sdk2) `main` @ `9754cd15` 与 [`topsun_dimos`](https://github.com/topsun-bot/topsun_dimos) `pyproject.toml` extras。默认 **bundled 0.10.2**；合法换库走 [`unitree_sdk2_hzj`](https://github.com/topsun-bot/unitree_sdk2_hzj) + opt-in `UNITREE_DDS_PROVIDER=external`（不是 in-place overwrite）。本切**不开** `topsun_dimos` PR，**不**改 `unitree_sdk2` `main` 的 `thirdparty/`。

决策背景：[feishu-middleware-adr.md](feishu-middleware-adr.md)。vendor 是对照快照、不是 Humble 已加载 `.so`：[feishu-runtime-provenance.md](feishu-runtime-provenance.md)。CI 闸门：[ci-cd-gates.md](ci-cd-gates.md)。

**不是** 飞书现场 / 实机 / 跨机根因证明。Not Feishu field proof. 无假分位数。

---

## 0. 硬规则

1. **drop-in 把 `vendor/CycloneDDS` 11.0.1 覆盖进 Unitree `thirdparty/lib/*/libddsc.so`（及 `libddscxx.so`）= FAIL。** 主版本 / ABI 不同。见 §2。
2. **不是 in-place overwrite。** 不改 [`topsun-bot/unitree_sdk2`](https://github.com/topsun-bot/unitree_sdk2) `main` 的 `thirdparty/` 0.10.2。默认永远是 **bundled** Cyclone **0.10.2**，保证原树还能编、还能链自带 `.so`。
3. **合法换库路径**在独立仓 [`topsun-bot/unitree_sdk2_hzj`](https://github.com/topsun-bot/unitree_sdk2_hzj)（新 SDK HZJ 版本；已 seed）。那边以后加 opt-in `UNITREE_DDS_PROVIDER=external`（**default bundled**）。不是只在 fork 上就地改 `thirdparty`。见 §4。
4. **不要**把 rolling vendor 文件拷到机器人，或铺进 **`/opt/ros/humble`**。Humble underlay ≠ vendor snapshot。见 [vendor/MANIFEST.md](../../vendor/MANIFEST.md)。
5. **不改** [`config/fastdds.xml`](../../config/fastdds.xml)、[`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md)。
6. **不**启用 Agnocast / zenoh / eCAL / DPDK / Isaac。不 vendor `rmw_zenoh`，不装 kmod。《3》–《6》仍 Hold。跨机 UDP 仍 **blocked**。
7. 线缆互通（本进程 11.0.1 ↔ Unitree 0.10.2 participant）= **UNPROVEN**。未跑通之前写 `STATUS: blocked`，禁止编造时延。

核对本文 + VERSIONS 钉扎仍一致：[`scripts/check_unitree_cyclone_swap.py`](../../scripts/check_unitree_cyclone_swap.py)。

---

## 1. 三处钉扎（从树里核对，不发明版本）

| 面 | 是什么 | 核对到的版本 | 本仓 / 上游落点 |
|----|--------|--------------|-----------------|
| **Unitree SDK2 bundled Cyclone** | 预编译 `.so`（ABI 替换目标） | **0.10.2** | fork [`topsun-bot/unitree_sdk2`](https://github.com/topsun-bot/unitree_sdk2) = 上游 [`unitreerobotics/unitree_sdk2`](https://github.com/unitreerobotics/unitree_sdk2) `main` @ `9754cd153af3da471b0fe5f3aa535e426fb11db3`。`thirdparty/include/dds/version.h` 写 `DDS_VERSION "0.10.2"`。预编译库：`thirdparty/lib/{x86_64,aarch64}/libddsc.so` + `libddscxx.so`（另有 `libddsc.so.0` / `libddscxx.so.0` soname 链接，主版本 **0**） |
| **ros2_hzj vendor Cyclone** | **源码快照**，不是 Humble 运行时 | **11.0.1** | 本仓 [`vendor/VERSIONS.md`](../../vendor/VERSIONS.md)：`eclipse-cyclonedds/cyclonedds` tag `11.0.1`，SHA `e54e991f75a3e67f8e628da3171122e36ea5b872`。同树 [`vendor/CycloneDDS/CMakeLists.txt`](../../vendor/CycloneDDS/CMakeLists.txt) `project(CycloneDDS VERSION 11.0.1 …)`；[`src/core/CMakeLists.txt`](../../vendor/CycloneDDS/src/core/CMakeLists.txt) `SOVERSION ${PROJECT_VERSION_MAJOR}` → **11** |
| **DimOS Python pin** | `cyclonedds` **绑定**，不是 C 核心发行标签 | **`cyclonedds>=0.10.5`** | `topsun_dimos` `pyproject.toml` extras **`unitree-dds`** / **`dds`**（只读核对，本切不开 PR）。同 0.10.x 家族，**不是** 11.0.1。本仓对照：[`scripts/bench/requirements-chain-b.txt`](../../scripts/bench/requirements-chain-b.txt) 也写 `cyclonedds>=0.10.5` |

Unitree 头文件原文（fork `main` @ `9754cd15`，不是本仓文件）：

```c
#define DDS_VERSION "0.10.2"
#define DDS_VERSION_MAJOR 0
#define DDS_VERSION_MINOR 10
#define DDS_VERSION_PATCH 2
```

vendor 钉扎原文（本仓 [`vendor/VERSIONS.md`](../../vendor/VERSIONS.md)）：

```
| `vendor/CycloneDDS/` | … | tag `11.0.1` | `11.0.1` | `e54e991f75a3e67f8e628da3171122e36ea5b872` |
```

`vendor/CycloneDDS` 是对照阅读用的发行标签快照，**不是** `/opt/ros/humble` 已加载的 `.so`，也不是 Unitree 机器人上那份 0.10.2。身份闸仍是 [`scripts/prove_rmw.py`](../../scripts/prove_rmw.py)（已加载 RMW），不是本页版本表。

---

## 2. 裁决：drop-in FAIL

**Verdict: drop-in replacement of Unitree `thirdparty` `libddsc` / `libddscxx` with `vendor/CycloneDDS` 11.0.1 is FAIL**（major version / ABI）。

| | Unitree bundled | 本仓 vendor |
|--|-----------------|-------------|
| 形态 | 预编译 `.so` | 源码快照 |
| 版本 | 0.10.2 | 11.0.1 |
| SONAME / SOVERSION | `libddsc.so.0`（主版本 0） | CMake `SOVERSION` = major **11** |

0 → 11 是不兼容 ABI。把 11.0.1 的 `libddsc.so` / `libddscxx.so` 拷进 `thirdparty/lib/{x86_64,aarch64}/` 去「换掉」0.10.2，不是 drop-in。

**禁止：**

- 把 `vendor/CycloneDDS` 构建产物 **in-place overwrite** 进 Unitree `thirdparty/lib/**`（原 fork `main` 必须保持 bundled 0.10.2）
- 把 rolling vendor 铺进机器人根文件系统
- 把 rolling vendor 铺进 **`/opt/ros/humble`**（Humble ≠ 11.0.1 snapshot）
- 把 `cyclonedds>=0.10.5` Python wheel 接到 11.0.1 C 库上当已验证组合

本切只记录 FAIL，**不**改 `dimos_bridge` DDS 行为，**不**改 vendor 源码，**不开** `topsun_dimos` PR。

---

## 3. 线缆互通：UNPROVEN

**Wire interop**（本仓进程链上 **11.0.1** Cyclone，对端是 Unitree **0.10.2** participant）= **UNPROVEN**。

DDS 线协议有时能跨小版本互通；**本环境没有跑通**，所以不是 PASS，也不是测得的 FAIL。禁止把「同家族 / RTPS」写成已证明。禁止发明 p50 / p95 / 跨机数字。

### 3.1 同机 smoke 配方（仅配方；本切未执行）

`STATUS: blocked` — 本环境未克隆 `unitree_sdk2`、未编译 vendor Cyclone、未起两个 participant。跨机 UDP 仍 Hold，不要把下面步骤扩成跨机。

同机、域 **0**（链 B 契约；Unitree `ChannelFactoryInitialize(0)`）：

1. **侧 A（0.10.2）：** `topsun-bot/unitree_sdk2` @ `9754cd15`，链接自带 `thirdparty/lib/$(uname -m)/libddsc.so`（及 `libddscxx.so`）的 example / `ChannelFactory`，域 0 发布一个已知 topic。
2. **侧 B（11.0.1）：** 另开进程，使用**单独构建**的 Cyclone **11.0.1**（本仓 `vendor/CycloneDDS` 源码；**本切 CI 不编译 vendor**），域 0 建 `DomainParticipant`，尝试 discovery + take 至少一条样本。
3. **通过：** 两侧看见对方 participant，且至少一条样本到达。  
   **失败：** 无 discovery、解码失败、或加载 `.so` 崩溃。
4. **本切：** 未跑 → 保持 **UNPROVEN** / `STATUS: blocked`。跑通另开 PR，写实测日志，仍不要改 XML / SCOREBOARD。

不要在本页填分位数。数字未测之前只是假设。

---

## 4. 合法换库路径（新仓 + opt-in；保证原树还能用）

**Replacement is not an in-place overwrite** of Unitree `thirdparty` 0.10.2。  
**Default remains bundled Cyclone 0.10.2。** 原 fork [`topsun-bot/unitree_sdk2`](https://github.com/topsun-bot/unitree_sdk2) `main` @ `9754cd15` 继续链自带 `.so`，本切不动它。

合法路径是**另一棵树**，不是在 fork 上就地改 `thirdparty/`：

| 树 | 角色 | 默认 | 换库怎么开 |
|----|------|------|------------|
| [`topsun-bot/unitree_sdk2`](https://github.com/topsun-bot/unitree_sdk2) | 原 SDK2（上游 `unitreerobotics/unitree_sdk2` @ `9754cd15`） | **bundled 0.10.2** | **不**在这棵树上 in-place 覆盖 `thirdparty/` |
| [`topsun-bot/unitree_sdk2_hzj`](https://github.com/topsun-bot/unitree_sdk2_hzj) | 新 SDK HZJ 版本（已 seed；独立于 `topsun_dimos`） | 仍是 **bundled 0.10.2** | 后续在该仓加 opt-in **`UNITREE_DDS_PROVIDER=external`**（unset / `bundled` = 自带 0.10.2；`external` = 链外部选定的 Cyclone，需对该版本 **rebuild**，不是拷 `.so`） |

`UNITREE_DDS_PROVIDER=external` 是 **opt-in**。没设、或设成 bundled，行为必须等于今天的 0.10.2 自带库。这样原机器人 / 原 fork 消费者不受影响。

若 `external` 选本仓 vendor **11.0.1**：仍要在 `unitree_sdk2_hzj` **整树重编**（及所有链接 `libddsc` / `libddscxx` 的二进制）。**drop-in 11.0.1 仍是 FAIL。** 贴近机器人 ABI 则 `external` 只指向 **0.10.x**（与 bundled 0.10.2、DimOS Python `cyclonedds>=0.10.5` 同家族）。不要铺进 `/opt/ros/humble`。

那是 **`unitree_sdk2_hzj` 后续 PR**，不是本切。本切：**不开** `topsun_dimos` PR，**不**改 `unitree_sdk2` `main` 的 `thirdparty/`，不 vendor SDK2，不编译 Cyclone。`unitree_sdk2_hzj` 当前只是 seed README（「cloud agent will land the rewrite」），开关尚未落地。

---

## 5. 闸门怎么跑

```bash
python3 scripts/check_unitree_cyclone_swap.py
```

无 ROS 时应 exit 0，并打印 `drop-in: FAIL / wire: UNPROVEN`。脚本打开这些文件：

| 打开 | 断言 |
|------|------|
| 本文 [`unitree-sdk2-dds-swap.md`](unitree-sdk2-dds-swap.md) | 连续裁决句 **`drop-in FAIL / wire UNPROVEN`**（不是拆开的 `drop-in` / `FAIL` / `UNPROVEN`）、`DDS_VERSION "0.10.2"` 引文、Hold 标记 |
| [`vendor/VERSIONS.md`](../../vendor/VERSIONS.md) | 同一行同时有 `vendor/CycloneDDS/` + `11.0.1` + SHA `e54e991f75a3e67f8e628da3171122e36ea5b872` |
| [`vendor/CycloneDDS/CMakeLists.txt`](../../vendor/CycloneDDS/CMakeLists.txt) | `project(CycloneDDS … VERSION 11.0.1 …)` 声明（不是文件里任意一处 `VERSION 11.0.1`） |
| [`config/fastdds.xml`](../../config/fastdds.xml) | **只检查存在**。内容冻结由 CI **`boundary`** 管 |
| [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) | **只检查存在**。不读数字；内容冻结由 **`boundary`** 管 |

CI 登记见 [ci-cd-gates.md](ci-cd-gates.md)。**不要**为了本地绿去编译 vendor 或改 XML / SCOREBOARD。

---

## 6. 引用

1. 本仓 [vendor/VERSIONS.md](../../vendor/VERSIONS.md) — Cyclone tag `11.0.1` / SHA `e54e991f75a3e67f8e628da3171122e36ea5b872`
2. 本仓 [vendor/CycloneDDS/CMakeLists.txt](../../vendor/CycloneDDS/CMakeLists.txt) — `project(CycloneDDS VERSION 11.0.1 …)`
3. [topsun-bot/unitree_sdk2](https://github.com/topsun-bot/unitree_sdk2) `thirdparty/include/dds/version.h` — `DDS_VERSION "0.10.2"`（`main` @ `9754cd15`）
4. [topsun_dimos](https://github.com/topsun-bot/topsun_dimos) `pyproject.toml` extras `unitree-dds` / `dds` — `cyclonedds>=0.10.5`（本切不开 PR）
5. [topsun-bot/unitree_sdk2_hzj](https://github.com/topsun-bot/unitree_sdk2_hzj) — 合法换库落点（default bundled 0.10.2；opt-in `UNITREE_DDS_PROVIDER=external`）
6. [feishu-middleware-adr.md](feishu-middleware-adr.md) · [feishu-runtime-provenance.md](feishu-runtime-provenance.md) · [ci-cd-gates.md](ci-cd-gates.md)
7. [scripts/check_unitree_cyclone_swap.py](../../scripts/check_unitree_cyclone_swap.py)
