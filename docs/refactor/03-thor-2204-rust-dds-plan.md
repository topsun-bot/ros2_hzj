# 《3》Thor 2204 Rust DDS 重构计划（plan-only）

Status: **计划文档 — 不是实现、不是复现报告、不是时延数字、不是飞书现场证明。**
范围：本仓 `ros2_hzj`（TOPSUN / 桦之坚独立 ROS 2 / DDS 双链工作区，**不是** `topsun_dimos`）。
本切只新增本文 + [ITERATION_LOG.md](ITERATION_LOG.md) 一轮短记。**无 Rust crate、无 rmw 源码、无 vendor 编译、无 SCOREBOARD 改写。**

**Do not merge until 张益新 answers §8.** Do **not** treat this page as `DoD` / cross-host / latency **PASS**.
**DoD: unmet** / **STATUS: blocked** still apply to product evidence ([feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md)).
Cross-host UDP remains **STATUS: blocked**. Three-chain remains **map ≠ reproduce**.

边界遵守 [AGENTS.md](../../AGENTS.md)：不动 `config/fastdds.xml`、不动 `docs/artifacts/bench/SCOREBOARD.md` 数字、不启用 Agnocast / zenoh / Cega、不改 `dimos_bridge` 运行时 DDS、不编译 vendor。本计划**提议**将来如何用 Rust 重构；它**不**解除现有 Hold。解除 Hold 必须由人类批准（通常还要 `allow-hold-bypass`）。

飞书 4 篇输入在撰写时按仓库惯例视为**无匿名读权限**；本文只复用已合入的 ADR / 地图 / SCOREBOARD **指针**，不编造飞书原文。

---

## 0. 一句话

在 NVIDIA Jetson Thor / Ubuntu 22.04（本文称 **Thor 2204**）上，用 Rust 做一条**可切换**的 DDS 路径，使本仓已依赖的 ROS 2 DDS 行为（发现、pub/sub、QoS、rmw 边界、链 A FastDDS 域 42 / 链 B Cyclone 域 0）保持功能对等，并把本仓已跟踪的延迟 / 吞吐指标设计到 **~100× vs Thor 上测得的同一套 SCOREBOARD 配方基线**。100× 是硬设计目标，**不是**已测数字。本仓今天**没有** Thor 2204 基线。

```
应用仍写 rclpy / ROSTransport / DDSTransport
        │
        ▼
rmw  ──RMW_IMPLEMENTATION──▶  今天: rmw_fastrtps_cpp / rmw_cyclonedds_cpp
                              计划: 可选 Rust rmw（须先解 Hold）或继续 FFI 进现有 DDS
        │
        ▼
DDS  ──链A Fast-DDS 域42 / 链B Cyclone 域0（对等发现必须还能跟现网对端互通）
```

---

## 1. Scope / non-goals

### 1.1 In scope (this document)

| Item | Meaning |
|------|---------|
| Functional parity | Same APIs / behaviors this repo already depends on: discovery domains, pub/sub, QoS contracts, rmw load boundary, FastDDS XML **path** (read-only seed), dual-chain env |
| Performance **target** | ~100× vs a **Thor 2204 Humble remasure** of the recipes SCOREBOARD already books (not vs the cloud-VM booked tables; not invented µs) |
| Stack choice | Compare rmw-only vs full-stack vs shim; pick a default **recommendation**, leave the Hold-lift to 张益新 |
| Measurement recipe | How we will prove 100× without writing fake numbers |
| Phased milestones | M0 (this page) → M1 Thor baseline → Mn implementation gates |

### 1.2 Non-goals (hard)

| Non-goal | Why |
|----------|-----|
| Rust implementation in this PR | User asked plan-only |
| Edit gate scripts / `.github/workflows/ci.yml` | Frozen by this task |
| Edit `config/fastdds.xml` or SCOREBOARD **numbers** | AGENTS.md + CI `boundary` |
| Edit `dimos_bridge` DDS runtime or `vendor/**` sources | §13(4) Hold + vendor snapshots |
| Enable Agnocast / zenoh / `rmw_zenoh` / eCAL / DPDK / Isaac / Cega | ADR Hold |
| Claim `DoD: met`, cross-host PASS, latency PASS, three-chain reproduced | Honesty gates |
| LCM / SHM DimOS default transports | Out of scope ([R0 freeze](../architecture/ros2-dds-r0-interface-freeze.md)) |
| Module dual-stack at app layer | 《通信中间件》次优；本仓不做 |
| Copy Rolling vendor over Humble | [feishu-runtime-provenance.md](../architecture/feishu-runtime-provenance.md) |
| Mix Chain A and Chain B in one speed table | Discovery failure, not a single-stack latency bug |
| 《3》–《6》 bench-score / Mac HIL / Promptfoo / CVE loops as this plan's delivery | Still Hold as **product** work; local gates may stay green |

Reuse, do not rewrite: [01-dds-request-flow.md](01-dds-request-flow.md), [02-modernization-plan.md](02-modernization-plan.md), [feishu-middleware-adr.md](../architecture/feishu-middleware-adr.md), [ros2-dds-r0-interface-freeze.md](../architecture/ros2-dds-r0-interface-freeze.md), [ros2-source-map.md](../architecture/ros2-source-map.md), [latency-attribution.md](../architecture/latency-attribution.md), [feishu-dual-chain-baseline.md](../architecture/feishu-dual-chain-baseline.md), [feishu-sink-layers.md](../architecture/feishu-sink-layers.md).

---

## 2. Current baseline — what this repo measures today

Identity first, numbers second. `prove_rmw.py` is an **env/string** gate, not a modified `.so` proof. `check_*.py` are filesystem / marker gates. None of them measure RTT.

### 2.1 What is booked (pointer only)

Authoritative current-best **pointer**: [docs/artifacts/bench/SCOREBOARD.md](../artifacts/bench/SCOREBOARD.md) (iter10 Path B, iter7 `fastdds.xml` seed). This plan **does not** remeasure and **does not** rewrite that page.

| Booked surface | Host / image | Recipe | Metrics this repo actually tracks |
|----------------|--------------|--------|-----------------------------------|
| Chain A large-packet **same-host** | `cursor-cloud-vm` + `osrf/ros:humble-desktop` | `scripts/bench/run_large_packet.sh` — 102400 / 262144 / 1048576 B, 100 ms gap (10 Hz), 80 samples, `pingpong.py` RTT | RTT p50 / p95 / p99; timeout count. Booked table: `docs/artifacts/bench/2026-09-10-iter5/chain_a_same_host/summary.md` |
| Chain A IMU HF **same-host** | same image | `scripts/bench/run_imu_hf.sh` — **64 B**, **5 ms** (200 Hz), 400 samples | **Jitter gate**: RTT p95/p99 + arrival `\|I−5 ms\|` p95/p99. Do **not** claim success from p50/mean. Booked table: `docs/artifacts/bench/2026-09-11-iter7/chain_a_same_host/summary.md` |
| Chain A **cross-host-UDP** | — | `scripts/bench/run_cross_host_a.sh` | **STATUS: blocked** (single VM). No p50 / p95 / p99. Do not invent. |
| Chain B Cyclone | wrappers in `scripts/bench/run_chain_b.sh` | pytest `-m tool -k dds` (drain time) + `pingpong.py` RTT | Do **not** put A and B in one table. Native B without RouDi = localhost UDP, **not** SHM. |
| same-process tables | SCOREBOARD | honesty only | **Do not tune** for them |

How to re-run: [scripts/bench/README.md](../../scripts/bench/README.md), [docs/usage/benchmark-dds.md](../usage/benchmark-dds.md). Attribution method (no SCOREBOARD rewrite): [latency-attribution.md](../architecture/latency-attribution.md).

`T_e2e` stages (method, **not** measured µs on this host):

```
T_e2e = T_app_pub + T_rmw_pub + T_dds_write + T_transport + T_dds_ingress + T_rmw_take + T_callback
```

`pingpong.py` records **one** quantity: closed-loop RTT on one chain × one topology × one size. That is **not** Feishu one-way `T_e2e` and **not** the sum of stage P99s (percentiles are not additive).

### 2.2 Headline booked numbers (citation, not a new measurement)

These are **SCOREBOARD booked same-host Chain A** values on a **4-vCPU cloud VM**, not Thor, not Feishu field, not cross-host. Copied here only so the 100× **design budget** has a real numerator family. Do not treat them as the 100× denominator.

| Case (Chain A same-host) | Booked RTT p50 | Booked jitter-ish | Source |
|--------------------------|----------------|-------------------|--------|
| IMU 64 B / 200 Hz `ros_high_throughput` | 988.38 µs | RTT p95 1147.9 µs; arr `\|I−5 ms\|` p95 375.21 µs | SCOREBOARD IMU HF table (iter7) |
| IMU 64 B / 200 Hz `ros_reliable` | 970.54 µs | RTT p95 1173.4 µs; arr `\|I−5 ms\|` p95 569.21 µs | same |
| 1 MiB `ros_high_throughput` | 2312.2 µs | p95 2841.0 µs | SCOREBOARD large-packet table (iter5) |
| 1 MiB `ros_reliable` | 2368.5 µs | p95 2699.1 µs | same |

**Arithmetic design implication only** (not a prediction, not Thor): 100× vs those p50s would land near **~10 µs** (64 B) and **~23 µs** (1 MiB) RTT. That budget almost certainly requires cutting `T_app_pub` (Python / rclpy serialize) and `T_callback` (Humble executor), plus a zero-copy `T_transport` — most of which are **Hold** today. A Rust rmw that still calls Fast-DDS + Python ping-pong **cannot** honestly promise 100×.

### 2.3 Related measurements that are **not** the SCOREBOARD baseline

| Artifact | What it is | What it is not |
|----------|------------|----------------|
| [ITERATION_LOG.md](ITERATION_LOG.md) 轮次 69 / `hil/` | Native **arm64 Ubuntu 24.04** Colima VM, **Jazzy** talker/listener loopback (FastDDS 2.14.6 / Cyclone), 100 Hz small String | **Not Humble.** Jazzy ≠ Humble. Not Thor. Not SCOREBOARD. Cross-host still blocked. |
| Mac HIL docs | Host-side triage | True pub/sub blocked without Humble |
| `prove_rmw.py` / 13 local gates | Structure / Hold honesty | Not latency |

### 2.4 TODO — missing Thor 2204 baseline (how we will measure)

**Thor 2204 Humble remasure does not exist in this repo.** Until it does, 100× has no legal denominator.

M1 recipe (do **not** edit SCOREBOARD; write a **new** dated dir under `docs/artifacts/bench/` and leave current-best pointer unchanged until a human asks):

1. Board: NVIDIA Jetson Thor, Ubuntu **22.04**, ROS 2 **Humble** underlay (`/opt/ros/humble`). Image class: `docker/ros/` (`FROM ubuntu:22.04`, `ROS_DISTRO=humble`) or a JetPack-provided Humble — record which in `environment.md`.
2. Identity first: `source config/env/chain_a.sh` then `python3 scripts/prove_rmw.py` (must show Humble + `rmw_fastrtps_cpp` + domain 42 + `FASTRTPS_DEFAULT_PROFILES_FILE` → `config/fastdds.xml`). Chain B: `source config/env/chain_b.sh`, domain 0, **unset** `CYCLONEDDS_URI`.
3. Same commands as SCOREBOARD:
   - `BENCH_DATE=YYYY-MM-DD-thor2204-baseline CHAIN_A_IMAGE=<recorded> LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh`
   - `BENCH_DATE=YYYY-MM-DD-thor2204-baseline IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh`
   - Optional Chain B: `./scripts/bench/run_chain_b.sh` into a **separate** directory. No A-vs-B table.
4. One topology label per run: `same-process` / `same-host` / `cross-host-UDP`. Cross-host stays **blocked** until a second physical host exists.
5. Artifacts per run: `summary.md` + `raw.json` + `environment.md` (SoC, nvpmodel, clocks, isolcpus, RMW identifier, git SHA). See [latency-attribution.md](../architecture/latency-attribution.md) §2.
6. **Do not** copy those new percentiles into SCOREBOARD or this plan as “PASS”. Index them from `docs/artifacts/bench/README.md` only after the run exists.

---

## 3. Rust stack choices

ADR today ([feishu-middleware-adr.md](../architecture/feishu-middleware-adr.md)): keep the ROS 2 **app** API; switch implementations with `RMW_IMPLEMENTATION`; **no custom RMW** on this cut; do not rewrite the whole middleware; do not add a module dual-stack.

A Thor 2204 Rust path that still talks to existing peers **must** pick one of the following. Default recommendation is **S then D** (shim first for parity, native DDS only if M1+M2 prove the shim cannot approach the 100× budget). **None of these are approved** until 张益新 lifts the matching Hold.

| Option | What we would build | Parity | 100× plausibility | Hold collision |
|--------|---------------------|--------|-------------------|----------------|
| **S — Rust rmw shim** | `cdylib` implementing the C `rmw_*` ABI ([`vendor/rmw/rmw/include/rmw/rmw.h`](../../vendor/rmw/rmw/include/rmw/rmw.h) is a **snapshot**, not the Humble header). FFI into distro Fast-DDS (A) / Cyclone (B). App still `rclpy`. | Highest. Discovery / QoS stay in proven C/C++ DDS. | **Low** if ping-pong stays Python+executor. Shim can shave `T_rmw_pub` / some copies; it does not remove Fast-DDS or Humble `rclpy`. | Custom RMW is **Hold**. Needs explicit lift. Does **not** require vendor tree edits if we consume **distro** `.so`. |
| **D — Rust DDS + rmw** | Native Rust RTPS (evaluate [dust-dds](https://github.com/s2e-official/dust-dds) / [RustDDS](https://github.com/Atostek/RustDDS) at M0 crate survey — names are **candidates**, not pins) behind a Rust `rmw_*`. Wire must still discover Fast-DDS (domain 42) and Cyclone / Unitree (domain 0). | Medium. QoS + SPDP/SEDP + type hash + fragmentation are the failure mode. | Medium–high **only** with zero-copy same-host + a non-Python hot path. Still need a like-to-like remasure. | Custom RMW **and** “core fork last” ([feishu-risk-matrix.md](../architecture/feishu-risk-matrix.md) §9.4 layer 5). Wire vs Unitree 0.10.2 is **UNPROVEN** today. |
| **F — Full stack (rcl + rmw + DDS in Rust)** | Replace Humble `rcl` / executor. | Breaks R0: apps must keep writing `rclpy` / `ROSTransport`. Humble `rcl*` is **not** in vendor. | Speculative. | **Out of scope.** Fork `rcl` is last and this repo does not vendor it. |
| **H — Hot-path bypass** | Native Rust DDS for IMU/lidar only; ROS 2 for the rest. | Two discovery domains / two type systems. Easy to silently drop R0 topics. | Can look fast on a custom bench while ROS path is unchanged. | App-layer dual-stack = **不做**. Also tempts zenoh / Agnocast. **Reject** unless 张益新 rewrites R0. |
| **B — C bindings only** | `cyclonedds-rs` / Fast-DDS CXX bindgen, no rmw. Used by DimOS-like native B. | Matches Chain B native (`ddspubsub.py` listener), not Chain A `rclpy`. | Same as today’s native B plus Rust overhead/gain. | Changing `ddspubsub.py` = `dimos_bridge` runtime edit = **Hold**. |

**Recommendation (pending §8):**

1. **M0–M1:** no Rust — Thor 2204 Humble remasure of SCOREBOARD recipes.
2. **M2:** Option **S** spike (`rmw_hzj_rs` name TBD) loaded via `RMW_IMPLEMENTATION`, **distro** Fast-DDS, domain 42, read-only `config/fastdds.xml`. Prove discovery + the R0 topic/QoS subset against a stock `rmw_fastrtps_cpp` peer.
3. **M3:** Option **D** spike **only if** M2 same-host RTT cannot enter the same order of magnitude as the §2.2 design budget **and** 张益新 lifts core-fork Hold. Wire-compat with Fast-DDS and Cyclone is a go/no-go, not a tuning loop.
4. Never land Option F or H in this repo without a new R0 freeze.

Crate survey (M0 homework, not a pin):

| Crate / tree | Role | Notes for this repo |
|--------------|------|---------------------|
| `rmw` C ABI | Boundary we must keep if apps stay on `rclpy` | Snapshot at `vendor/rmw`; runtime is Humble |
| dust-dds / RustDDS | Native Rust DDS candidates | Must prove RTPS interoperability; do not vendor until Hold lift |
| cyclonedds-sys / cyclonedds-rs | FFI to Cyclone | Useful for S-on-B; Unitree bundled is **0.10.2**, vendor tag is **11.0.1** = drop-in **FAIL** ([unitree-sdk2-dds-swap.md](../architecture/unitree-sdk2-dds-swap.md)) |
| iceoryx2 | Rust SHM | Cited in [cn-jp-ros2-absorb.md](../architecture/cn-jp-ros2-absorb.md) §6.10 as industry (~100 ns **vendor** claim). **Not** our number. `rmw_iceoryx2` / iceoryx2 vendor = Hold. AUTO ≠ 已开零拷. |
| `rclrs` / ros2-rust | Rust **app** client | Optional later; does not replace rmw for existing Python |
| zenoh / Agnocast / NITROS | — | **Hold.** Do not design 100× around them |

---

## 4. Thor 2204 constraints

Working assumption (confirm in §8): **Thor** = NVIDIA Jetson Thor class SoC; **2204** = Ubuntu 22.04 = Humble’s distro OS ([`docker/ros/Dockerfile`](../../docker/ros/Dockerfile) `FROM ubuntu:22.04`, `ROS_DISTRO=humble`). aarch64.

| Constraint | Implication for the plan |
|------------|--------------------------|
| aarch64 / Ubuntu 22.04 | All crates must have aarch64 + glibc 2.35 story. No “works on the cloud VM” as proof. |
| Humble underlay | Process links `/opt/ros/humble`, not `vendor/**` rolling/master snapshots. Custom rmw must build **against Humble headers**. |
| JetPack / L4T (version **TODO**) | Record nvpmodel, clocks, isolcpus, EMC in `environment.md`. SCOREBOARD already refused thread-affinity knobs on a shared 4-vCPU VM; Thor **may** isolate cores — that is a host recipe, not an XML knob. |
| Same-host vs NIC | 100× is most plausible on **same-host SHM / intra-SoC**. Cross-host UDP is still **blocked** until a second host exists; do not promise 100× on a blocked topology. |
| GPU / NITROS | [nitros-vs-dual-chain.md](../architecture/nitros-vs-dual-chain.md): NITROS is same-process GPU, **not** a dual-chain substitute. Hold. |
| Power / thermals | A 200 Hz jitter gate will move if the board throttles. Remasure after clocks are pinned. |
| Unitree on the same box | If G1/Go2 SDK shares the Thor, bundled Cyclone **0.10.2** stays default; vendor 11.0.1 drop-in **FAIL**. Rust path must not overwrite `thirdparty/lib/**`. |
| This automation host | No Humble, no Thor. M1 **cannot** run here. `STATUS: blocked` until a board is attached. |

---

## 5. Parity checklist (vs in-repo ROS 2 DDS usage)

Parity means the **R0 frozen subset + dual-chain contract + rmw load story**, not “every DimOS topic in the universe.” Topics not in the freeze have **no** behavior-unchanged promise ([ros2-dds-r0-interface-freeze.md](../architecture/ros2-dds-r0-interface-freeze.md) §2).

| # | Behavior the project depends on | Authority | Rust-path acceptance (when implementation starts) |
|---|--------------------------------|-----------|---------------------------------------------------|
| P1 | Two **independent** stacks; mixing defaults = discovery failure | R0 §1, [feishu-dual-chain-baseline.md](../architecture/feishu-dual-chain-baseline.md) | Chain A domain **42** + `rmw_fastrtps_cpp` (or approved replacement) still isolated from Chain B domain **0** |
| P2 | Operator must `source` / apply; `import load.py` does not write `os.environ` | [config/env/load.py](../../config/env/load.py), AGENTS.md | New RMW name added to env **only** after gate/docs update in a later PR; import stays pure |
| P3 | `FASTRTPS_DEFAULT_PROFILES_FILE` → `config/fastdds.xml` (iter7 seed, **read-only**) | SCOREBOARD, dual-chain baseline | Rust path **reads** the seed; no XML rewrite. `RMW_FASTRTPS_USE_QOS_FROM_XML` stays unset unless a later PR says otherwise (SCOREBOARD leftover family) |
| P4 | Chain B **unset** `CYCLONEDDS_URI` | `chain_b.sh` | Do not invent a Cyclone network XML to “win” same-host |
| P5 | App APIs: `rclpy` / `ROSTransport` / `DDSTransport` | R0, sink-layers **app** | Apps do not switch to a new Rust API. `dimos_bridge` runtime **not** edited this program |
| P6 | R0 nav QoS: `/foxglove_teleop`→`/cmd_vel` BEST_EFFORT KEEP_LAST depth 1; `/goal_pose` + `/way_point` RELIABLE VOLATILE KEEP_LAST depth 5; `/joy` topic frozen | R0 §2, [dds_topics.py](../../dimos_bridge/dimos/protocol/dds_topics.py), [config/topics.yaml](../../config/topics.yaml) | Interop: stock Humble peer on those QoS still matches. Library default `depth=5000` in `rospubsub.py` is **not** nav QoS |
| P7 | Go2 ROS bindings `lidar` / `global_map` / `odom` / `color_image` | R0 §2 | Type names unchanged (`PointCloud2` / `PoseStamped` / `Image`) |
| P8 | rmw load: `RMW_IMPLEMENTATION` → `rmw_implementation` `load_library()` | [01-dds-request-flow.md](01-dds-request-flow.md), `prove_rmw.py` | Identifier string printed by `get_rmw_implementation_identifier()` is the proof, not the env var |
| P9 | `publish()` / `rmw_publish()` OK ≠ delivered / History / callback | [ros2-source-map.md](../architecture/ros2-source-map.md) | Do not redefine success as “write returned OK” |
| P10 | wait → take → callback (Chain A Humble executor; native B = `on_data_available`) | [feishu-executor-waitset.md](../architecture/feishu-executor-waitset.md) | Shim must implement `rmw_wait` / `rmw_take`. Native B listener path stays untouched |
| P11 | Unitree 0.10.2 vs vendor 11.0.1 = **drop-in FAIL / wire UNPROVEN** | [unitree-sdk2-dds-swap.md](../architecture/unitree-sdk2-dds-swap.md) | Rust DDS must not overwrite bundled `.so`. Wire test is a later milestone, default **UNPROVEN** |
| P12 | Loaned / Data Sharing / Iceoryx **not** on | sink-layers **memory** | Enabling them for 100× is a **new Hold-lift**, not implied by this plan |

---

## 6. Phased milestones

Each milestone is a **separate PR**. This PR is **M0 only**. Do not combine Hold-lifts with measurement PRs.

| ID | Goal | Deliverable | Exit criteria (honest) | Blocked by |
|----|------|-------------|------------------------|------------|
| **M0** | Research / plan | This file + ITERATION_LOG note | Humans can decide S vs D; 100× recipe written; no code | — (this PR) |
| **M1** | Thor 2204 **baseline** | New `docs/artifacts/bench/<date>-thor2204-baseline/` (`summary.md` / `raw.json` / `environment.md`). **Do not** edit SCOREBOARD numbers | Like-to-like Humble remasure of large-packet + IMU HF on Thor; `prove_rmw.py` identity recorded. Status = **measured-on-Thor**, not PASS vs a product SLA | Physical Thor + Humble. **STATUS: blocked** on this host |
| **M2** | Option S spike | Out-of-tree (or later in-tree **new** dir, not `vendor/` overlay) Rust `cdylib` rmw + README. **No** `dimos_bridge` edits | Discovers and exchanges the P6 subset with stock `rmw_fastrtps_cpp` on domain 42; `prove_rmw.py` shows the new identifier when sourced. Perf numbers optional and **not** 100× claims | Custom-RMW Hold lift (张益新) |
| **M3** | Wire-compat / Option D decision | Crate survey notes + SPDP/SEDP interop log vs Fast-DDS and vs Cyclone 0.10.x | Go/no-go written. If no-go, stay on S. If go, still no SCOREBOARD edit | M2 data + core-fork Hold lift |
| **M4** | Thor host recipe | isolcpus / clocks / hugepage **notes** (docs). No XML knob from SCOREBOARD leftover families (lease / WLP / `port_queue_capacity` / exclusive SHM = **Forbidden to retry**) | Remasure vs **M1** on the same board. Report ratio. Do not retry discarded XML families | M1 |
| **M5** | 100× proof protocol | Dated bench dir + a short method note pointing at M1 as denominator | See §7. **May fail.** Failure is a result, not a license to invent numbers | M1 + (M2 or M3) + same topology |
| **Mn** | Product DoD | Only after wiki3 §6.3 five items exist | Still **DoD: unmet** until real build, loaded modified `.so`, this-host delta, rollback, product thresholds | Humble + Thor + human SLA |

A-side modernization in [02-modernization-plan.md](02-modernization-plan.md) (gate helper cleanup) is **orthogonal**. Do not mix those PRs with M2+.

---

## 7. How we prove 100× without inventing numbers

**Rule:** a ratio needs two **like-to-like** runs. The only legal denominator is **M1 on Thor 2204**. SCOREBOARD cloud-VM tables, Jazzy `hil/` loopback, and same-process honesty tables are **not** denominators.

```
ratio_metric = booked_or_M1(metric) / rust_path(metric)     # same chain, topology, size, Hz, QoS name, pingpong.py
100×  :=  ratio_RTT_p95 ≥ 100  AND  ratio_jitter_gate ≥ 100
```

Use **p95 (and the IMU jitter gate)**, not p50/mean — SCOREBOARD already says IMU success is jitter, not p50.

| Proof step | Required | Forbidden |
|------------|----------|-----------|
| Same chain | A vs A, or B vs B | A-vs-B table |
| Same topology label | `same-host` vs `same-host` | Mixing `same-process` into the 100× headline |
| Same payload / gap / samples | 64 B / 5 ms / 400; 100 KiB–1 MiB / 100 ms / 80 | A custom micro-bench that skips `rclpy` compared against SCOREBOARD Python RTT |
| Same harness | `scripts/bench/pingpong.py` + the SCOREBOARD wrapper env vars | New timer that reports one-way as if it were RTT |
| Identity | `prove_rmw.py` on both runs | Claiming vendor SHA is the cause |
| Cross-host | Second host + `run_cross_host_a.sh` | Filling p50 while **STATUS: blocked** |
| Percentiles | Compute p99 from the **same** e2e sample set | `P99(A)+P99(B)+…` |
| SCOREBOARD | Leave numbers frozen; new dirs only | Quietly “updating” iter7 tables |
| Failure | Write `ratio = 12× (miss)` or `STATUS: blocked` | Rounding a 20× run to “~100×” |

**If M1 is missing, 100× is unprovable.** That is the current state.

Industry citations (iceoryx2 ~100 ns, etc. in [cn-jp-ros2-absorb.md](../architecture/cn-jp-ros2-absorb.md)) are **other people’s benches**. They may inform Option D research; they are not our 100× proof.

---

## 8. Open questions for 张益新

Please answer in the PR thread. This plan must not be merged until the marked items have an owner.

1. **SKU:** Confirm “Thor 2204” = Jetson Thor + Ubuntu 22.04 + Humble? JetPack / L4T version? One board or a fleet?
2. **100× denominator:** Agree that M1 Thor remasure of SCOREBOARD recipes is the only legal baseline (not cloud-VM SCOREBOARD, not Jazzy `hil/`)?
3. **Which chain must hit 100×?** A only, B only, or both (still **separate** tables)?
4. **Hold lift for Option S (custom rmw)?** ADR currently: 无自定义 RMW. Without a lift, M2 cannot start.
5. **Hold lift for Option D / iceoryx2 / Loaned?** Needed only if S cannot approach the §2.2 budget. Default this plan stays inside Hold.
6. **May we change `dimos_bridge`?** Default **no** (cega-bridge Hold). If the 100× hot path cannot stay behind `RMW_IMPLEMENTATION`, that is a new R0.
7. **Unitree on Thor:** Must the Rust path stay wire-compatible with bundled Cyclone 0.10.2, or is Unitree traffic staying on today’s bundled stack?
8. **Who runs M1?** Board access, network (second host for cross-host), and whether `osrf/ros:humble-desktop` aarch64 or `docker/ros/` is the image of record.
9. **Feishu 3380004:** If wiki 《通信中间件》 / §13 text has changed since the ADR, we need login before M2 so we do not fight a newer 飞书 decision.
10. **Merge policy:** This PR is **plan-only. Do not merge** until you accept the recommendation (S then D) or name a different option.

---

## 9. Risk list (checklist, not scores)

Do **not** invent High/Medium/Low percentages ([feishu-risk-matrix.md](../architecture/feishu-risk-matrix.md)).

| Risk | What goes wrong | Mitigation in this program |
|------|-----------------|----------------------------|
| 100× vs the **wrong** baseline | Marketing a cloud-VM 988 µs → Thor-native 80 µs as “12× on Thor” or as 100× | §7: denominator = M1 only |
| Custom RMW Hold ignored | PR lands `rmw_*` and CI `boundary` / ADR drift | M2 blocked on Q4 |
| Wire incompatibility | Rust DDS does not discover Fast-DDS or Unitree 0.10.2 | Option S first; D is go/no-go; drop-in FAIL stays |
| Rolling headers vs Humble ABI | Building against `vendor/rmw` 7.11.2 then loading on Humble | Build against `/opt/ros/humble` |
| XML / leftover knobs | Re-trying lease / WLP / exclusive SHM | SCOREBOARD **Forbidden to retry**; M4 is host recipe only |
| App dual-stack | Silent second discovery domain | Option H rejected |
| Claiming DoD / PASS | Honesty gates go red; reviews lose trust | This page keeps **DoD: unmet**, cross-host **blocked**, map ≠ reproduce |
| `dimos_bridge` edit | Hold + copied-module drift vs `topsun_dimos` | No runtime edits |
| qemu / wrong arch | 轮次 69: amd64 Humble under qemu did not receive | M1 must be native aarch64 Humble, not qemu |
| Thermals / unlocked clocks | Jitter gate flaps | Pin nvpmodel; record in `environment.md` |
| Mixing A and B | False “win” | Separate dirs / tables forever |
| iceoryx2 vendor claim | Treating ~100 ns as our RTT | Citation only |

---

## 10. What this PR does / does not do

| Does | Does not |
|------|----------|
| Add this plan | Add Rust crates, `Cargo.toml`, or rmw sources |
| Append ITERATION_LOG 轮次 76 | Edit gates, `ci.yml`, `fastdds.xml`, SCOREBOARD numbers, vendor, `dimos_bridge` |
| Point at existing architecture docs | Claim DoD / cross-host / latency PASS |
| Define how 100× will be measured | Invent Thor µs or a fake ratio |

Local check after this docs-only change (expected exit 0, no ROS):

```bash
python3 scripts/run_all_gates.py
```

---

## 11. References

In-repo:

1. [AGENTS.md](../../AGENTS.md)
2. [01-dds-request-flow.md](01-dds-request-flow.md) — six-layer walk + traps
3. [02-modernization-plan.md](02-modernization-plan.md) — A-side only; B/C Hold
4. [ros2-dds-r0-interface-freeze.md](../architecture/ros2-dds-r0-interface-freeze.md)
5. [feishu-middleware-adr.md](../architecture/feishu-middleware-adr.md)
6. [ros2-source-map.md](../architecture/ros2-source-map.md) — map ≠ reproduce
7. [latency-attribution.md](../architecture/latency-attribution.md)
8. [feishu-dual-chain-baseline.md](../architecture/feishu-dual-chain-baseline.md) — SCOREBOARD pointer only; no XML rewrite
9. [feishu-sink-layers.md](../architecture/feishu-sink-layers.md)
10. [feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md) — **DoD: unmet**
11. [feishu-three-chain-repro.md](../architecture/feishu-three-chain-repro.md) — **STATUS: blocked**
12. [unitree-sdk2-dds-swap.md](../architecture/unitree-sdk2-dds-swap.md) — drop-in FAIL / wire UNPROVEN
13. [feishu-cega-bridge-hold.md](../architecture/feishu-cega-bridge-hold.md)
14. [feishu-risk-matrix.md](../architecture/feishu-risk-matrix.md) — §9.4 order, no scores
15. [feishu-runtime-provenance.md](../architecture/feishu-runtime-provenance.md)
16. [feishu-executor-waitset.md](../architecture/feishu-executor-waitset.md)
17. [cn-jp-ros2-absorb.md](../architecture/cn-jp-ros2-absorb.md) — iceoryx2 citation, not our bench
18. [docs/artifacts/bench/SCOREBOARD.md](../artifacts/bench/SCOREBOARD.md) — current-best pointer
19. [scripts/bench/README.md](../../scripts/bench/README.md) · [docs/usage/benchmark-dds.md](../usage/benchmark-dds.md)
20. [config/env/load.py](../../config/env/load.py) · [config/env/chain_a.sh](../../config/env/chain_a.sh) · [config/env/chain_b.sh](../../config/env/chain_b.sh)

Feishu (login-walled; **not** re-read for this page):

21. 《通信中间件》 <https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe>
22. 《ROS 2 源码闭环》 <https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf>
23. Cyclone 工业级 fork 研究 <https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e>
