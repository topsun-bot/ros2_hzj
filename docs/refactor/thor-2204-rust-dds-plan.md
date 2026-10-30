# Thor 2204 / Rust DDS — plan-only track

Status: **plan document — not an implementation, not a measured result, not DoD PASS.**  
Branch: `plan/thor-2204-rust-dds` (docs + stubs). Ambition of **~100× vs stock ROS 2 DDS** is a **target hypothesis to measure**, never an achieved claim. This page invents **no** latency numbers, **no** `DoD: PASS`, **no** cross-host results.

Scope of this PR: documentation only. No Rust crate, no RMW `.so`, no vendor compile, no XML rewrite.

**Not** Feishu field proof / Thor bring-up proof / cross-host UDP proof.

---

## 0. Explicit Hold (this track does not lift them)

The following stay frozen. A later implementation PR that needs any of these must be a **separate** human-approved cut (often also `allow-hold-bypass`). This plan does **not** authorize them.

| Hold | Why it stays |
|------|----------------|
| Do not edit [`config/fastdds.xml`](../../config/fastdds.xml) | Chain A contract seed (iter7). Content freeze. |
| Do not edit [`docs/artifacts/bench/SCOREBOARD.md`](../artifacts/bench/SCOREBOARD.md) | Current-best pointer only. Do not copy or invent percentiles. |
| Do not enable Agnocast / zenoh | No vendor trees, no kmod, no `rmw_zenoh`. Path names with those tokens fail the `boundary` job. |
| Do not integrate Cega / rewrite Bridge runtime | wiki3 §13(4); [feishu-cega-bridge-hold.md](../architecture/feishu-cega-bridge-hold.md) |
| Do not change `dimos_bridge` DDS behavior | Copied DimOS modules stay behavior-unchanged. |
| Do not edit `vendor/` sources | Snapshots are read-only contrast, not a patch surface. |
| Do not change CI gate logic / thresholds | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) `structure` / `contracts` / `boundary`; `scripts/check_*.py` phrases stay. |
| Do not invent PASS / PROVEN / measured-delta | Product DoD remains **`DoD: unmet` / `STATUS: blocked`** until real evidence exists: [feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md). |
| Custom RMW remains Hold until a human lifts it | [AGENTS.md](../../AGENTS.md): “No custom RMW.” [ros2-dds-r0-interface-freeze.md](../architecture/ros2-dds-r0-interface-freeze.md) §4. M1 is a **spike proposal**, not a Hold lift. |
| 《3》–《6》 stay Hold | Bench score loops, Mac HIL, Promptfoo, CVE — out of this track’s v0. |

Same-topology XML tuning stays **paused**. Cross-host UDP stays **`STATUS: blocked`** until a second physical host exists. Chain A (`rmw_fastrtps_cpp`, domain **42**) and Chain B (Cyclone domain **0**) stay **two stacks**. Mixing defaults is a **discovery failure**, not a single-stack latency bug.

---

## 1. Problem / scope

### 1.1 Problem (why this track exists)

`ros2_hzj` today is a dual-chain ROS 2 / DDS workspace. The stock path this plan treats as **functional baseline** is **Chain A**:

1. App / `rclpy` / `ROSTransport`
2. Humble `rcl` (not vendored here)
3. `rmw` → `rmw_implementation` → **`rmw_fastrtps_cpp`**
4. Fast-DDS, domain **42**, profiles file pointed at the frozen [`config/fastdds.xml`](../../config/fastdds.xml) seed

Map: [ros2-source-map.md](../architecture/ros2-source-map.md). Contract: [ros2-dds-r0-interface-freeze.md](../architecture/ros2-dds-r0-interface-freeze.md). Attribution method (no numbers): [latency-attribution.md](../architecture/latency-attribution.md).

The stated product ambition is to **rebuild that DDS/RMW path in Rust** for **NVIDIA Jetson Thor / Thor 2204**, keep **identical function** for what this repo actually uses, and then **measure** whether a large speedup (informally “100×”) is real on that board.

This page does **not** claim the rebuild exists, that Thor is brought up, or that any speedup was observed.

### 1.2 What “identical function” means (v0 definition)

“Identical function” here is **observable ROS 2 / RMW behavior used by `ros2_hzj`**, not “every OMG DDS profile Fast-DDS ever shipped.”

| Surface | In-scope meaning for v0 |
|---------|-------------------------|
| **Discovery** | Participants on the same domain find matching writers/readers. Domain **42** for the Chain A–shaped path. Domain **0** must **not** silently join. SPDP/SEDP (or an equivalent that still interops with stock Fast-DDS peers **if** wire parity is required — see §6) must be inventory’d in M0. |
| **QoS** | Honor the R0 frozen nav-path contracts in [`dds_topics.py`](../../dimos_bridge/dimos/protocol/dds_topics.py) / R0 §2: `/foxglove_teleop` `BEST_EFFORT`/`KEEP_LAST`/`depth=1`; `/goal_pose` and `/way_point` `RELIABLE`/`VOLATILE`/`KEEP_LAST`/`depth=5`; `/joy` topic frozen, QoS unspecified. Library default `RELIABLE`/`KEEP_LAST`/`VOLATILE`/`depth=5000` in `rospubsub.py` is **not** nav-path QoS — do not conflate. |
| **Pub/sub** | Create publisher/subscription, `rmw_publish` / `rmw_take` / `rmw_wait`, matched counts, type support for the frozen message types (`geometry_msgs/*`, `sensor_msgs/Joy`, Go2 `PointCloud2` / `Image` / `PoseStamped` bindings). `RMW_RET_OK` on publish ≠ peer delivered — same honesty rule as the source map. |
| **Services** | Stock ROS 2 service client/server over the RMW request/response API, **as used by this repo**. M0 must list actual service names. If none are in the frozen table, the row stays **TBD** rather than inventing names. |
| **Actions** | Stock ROS 2 actions (goal / feedback / result / cancel) **as used via ROS 2 RMW**. Unitree `G1ArmActionClient` in `dds_sdk.py` is a **vendor SDK** client, not proof of ROS 2 action graph coverage. M0 separates the two. |

Identity of the loaded RMW remains `prove_rmw.py` (env / string, **not** a modified `.so` proof).

### 1.3 Explicitly out of scope for v0

- Replacing Chain B / Unitree bundled Cyclone 0.10.2, or claiming vendor Cyclone 11.0.1 is a drop-in (`drop-in: FAIL / wire: UNPROVEN`).
- LCM / Darwin SHM / `ZenohTransport` (stub only).
- Agnocast, zenoh, eCAL, DPDK, Isaac / NITROS, Cega.
- Editing `fastdds.xml`, SCOREBOARD numbers, vendor trees, `dimos_bridge` runtime, CI gate phrases.
- DDS-Security, XTypes / dynamic types, content-filtered topics, Persistence Service, Recording Service.
- Graph extras beyond what M0 inventories (`ros2 topic echo` cosmetics, Foxglove-specific transports).
- Loaned messages / Data Sharing / iceoryx2 as a **required** v0 feature (may appear later as an opt-in memory path; today memory-layer zero-copy is Hold — [feishu-sink-layers.md](../architecture/feishu-sink-layers.md)).
- Declaring Humble certified, Thor flashed, or 100× achieved.
- 《3》 score loops / 《4》 Mac HIL / 《5》 Promptfoo / 《6》 CVE as this track’s exit.

---

## 2. Target platform notes — Thor 2204 (**UNVERIFIED**)

“Thor 2204” in this track means **NVIDIA Jetson Thor (AGX Thor class) with a 22.04-shaped userspace**. Every hardware/OS row below is an assumption to verify on the real board. **Do not treat this table as a flash sheet.**

| Item | Working assumption | Status |
|------|--------------------|--------|
| ISA | ARM64 (`aarch64`) | **UNVERIFIED** on a Thor we own; class-level public fact only |
| Userspace | Ubuntu 22.04 (“2204”) | **UNVERIFIED** — L4T may be 22.04 or newer; confirm `lsb_release` / `/etc/os-release` on device |
| NVIDIA stack | JetPack / L4T for Thor | **UNVERIFIED** — exact JetPack and L4T versions unknown here; do not invent a version |
| ROS distro on device | Humble (matches [`docker/ros/Dockerfile`](../../docker/ros/Dockerfile) `ROS_DISTRO=humble` on `ubuntu:22.04`) | **UNVERIFIED** — Thor images may ship Jazzy / other; Humble ≠ rolling vendor snapshot ([feishu-runtime-provenance.md](../architecture/feishu-runtime-provenance.md)) |
| CUDA / TensorRT / kernel | whatever that JetPack ships | **UNVERIFIED** — not needed for a docs plan; needed before blaming GPU or P2P |
| NIC / multicast / SHM | stock Fast-DDS UDP + implicit SHM behavior from the **frozen** XML seed | **UNVERIFIED** on Thor; do not retune XML in this track |
| This CI / agent host | No Humble runtime, not Thor | Known: `prove_rmw.py` → `ROS not loaded`. Not a Thor result. |
| Cross-host UDP | second machine | **`STATUS: blocked`** until a peer exists |

M3’s first job is to replace this table with **device-attested** rows (command output + git SHA), not to fill µs.

---

## 3. Parity matrix

Stock column = Chain A Fast-DDS path **as this repo contracts it today** (`rmw_fastrtps_cpp`, domain 42, frozen XML seed, R0 topics).  
Rust candidate = not chosen. Names below are **survey labels only** (eProsima `dust-dds`, Atostek `rustdds`, or a from-scratch RTPS). **No crate is added in this PR.**

Every status is **TBD**. TBD means “not inventoried / not implemented / not measured” — not fail, not pass.

| Feature | Stock ROS 2 DDS (Chain A / Fast-DDS) | Rust candidate | Status |
|---------|--------------------------------------|----------------|--------|
| Domain isolation (42 vs 0) | Contract: 42 via `chain_a.sh`; must not join 0 | Must honor the same domain contract | TBD |
| Participant discovery | Fast-DDS SPDP (vendor snapshot for reading only) | TBD mechanism | TBD |
| Endpoint matching (SEDP) | Fast-DDS | TBD | TBD |
| Pub/sub `std` / `geometry_msgs` / `sensor_msgs` used by R0 | Humble type support + `rmw_fastrtps_cpp` | TBD RMW + type support | TBD |
| QoS BEST_EFFORT / RELIABLE as R0 table | Frozen rows in R0 §2 | Must apply the same contracts | TBD |
| History KEEP_LAST + depth | Frozen depths 1 / 5; library 5000 is not nav QoS | Must not silently use the other | TBD |
| Durability VOLATILE (nav rows) | Frozen | TBD | TBD |
| `rmw_wait` / WaitSet | mapped, not timed: [feishu-executor-waitset.md](../architecture/feishu-executor-waitset.md) | TBD | TBD |
| `rmw_take` + executor callback | Humble `rclcpp`/`rclpy` (not vendored) | App still uses ROS 2 API | TBD |
| Services (ROS 2 RMW request/response) | Stock Humble; **names used by this repo: UNVERIFIED** | TBD | TBD |
| Actions (ROS 2 action graph) | Stock Humble; **names used by this repo: UNVERIFIED** (Unitree arm action ≠ ROS action) | TBD | TBD |
| Graph introspection (`ros2 topic list` / count matched) | Distro tools | TBD | TBD |
| Wire interop with stock Fast-DDS peer | Today’s Chain A peers | Optional vs isolated-domain — decide in M0 | TBD |
| DDS-Security | Not in R0 freeze | v0 out of scope | TBD (out of v0) |
| Loaned / zero-copy | Hold; AUTO ≠ enabled | v0 not required | TBD (out of v0) |
| Thor ARM64 build | N/A (stock is x86 CI / Docker recipe) | M3 | TBD |
| 100× vs stock on Thor | Hypothesis only | Hypothesis only | TBD — **not achieved** |

---

## 4. Benchmark plan (how a “100×” claim would be falsified)

### 4.1 What to measure (when a host exists)

Use the **same method family** as [latency-attribution.md](../architecture/latency-attribution.md) and [`scripts/bench/README.md`](../../scripts/bench/README.md). Do **not** copy SCOREBOARD percentiles into this page.

| Metric | How | Notes |
|--------|-----|--------|
| Throughput | messages / s at a declared payload and QoS | Separate tables per topology |
| Latency p50 / p99 | per-message RTT from existing `pingpong.py` style (one closed loop) **or** a declared one-way if both ends timestamp | **Do not** sum per-stage P99 into e2e P99 |
| CPU | process + system % on the Thor cores used by the RMW/DDS threads | Same governor / same isolated-CPU policy both sides |
| Memory | RSS / unique set of pub + sub processes | Include RMW `.so` mapped size if measurable |

Topologies (pick **exactly one** per run, same labels as today’s bench):

- `same-process`
- `same-host`
- `cross-host-UDP` — remains **`STATUS: blocked`** until a second host exists; do not fill fake numbers

Payloads: start from the existing default size set `64, 1024, 16384, 65536` and the opt-in large-packet lengths already documented in the bench README. Product Hz / bytes remain **product-defined**, not middleware defaults.

### 4.2 Apples-to-apples vs current Fast-DDS path

A Rust-vs-stock row is valid only if **all** of these match:

1. **Same machine class** — Thor device (or a named substitute labeled **not Thor**). CI/x86 and SCOREBOARD same-host tables are **not** a Thor baseline.
2. **Same topology label** — do not put `same-process` next to `same-host`.
3. **Same domain / QoS / payload / rate** — Chain A shaped: `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`, same frozen XML seed **unread as a knob** (do not retune it for the stock side).
4. **Same API altitude** — both sides go through ROS 2 RMW (`rclpy`/`rclcpp` → `rmw_*`). A raw Rust DDS ping-pong is a **different experiment**; it may exist as a diagnostic but cannot carry the 100× claim against stock ROS 2 DDS.
5. **Same sample set** — p50/p99 from one population; no mixing Docker vs bare-metal in one table without a label.
6. **No A-vs-B table** — Chain B Cyclone is not the stock column for this track.

Stock command shape (already in-tree; blocked here without Humble):

```bash
source /opt/ros/humble/setup.bash   # if present
source config/env/chain_a.sh        # rmw_fastrtps_cpp, domain 42
./scripts/bench/run_chain_a.sh
```

Rust-candidate command: **TBD in M2/M4**. It must be a wrapper that prints the same topology / size / RMW identifier fields. Until it exists, write `STATUS: blocked`.

### 4.3 How the 100× hypothesis is falsified

Declare **one primary metric** *before* the M4 run (recommended: `same-host` p99 RTT at one booked payload, **or** saturated throughput at that payload — not both as “the” 100×).

Let `S` = stock Chain A Fast-DDS on that Thor. Let `R` = Rust candidate on the same Thor, same topology/QoS/payload/API.

- **Throughput primary:** hypothesis is `R_throughput / S_throughput ≥ 100`. **Falsified** if the measured ratio is `< 100` (including 1.0×, 2×, 10×).
- **Latency primary:** hypothesis is `S_p99 / R_p99 ≥ 100`. **Falsified** if the ratio is `< 100`.
- **Also falsified** if parity in §3 fails (wrong QoS, no discovery, domain leak, missing take/wait), even if a microbench looks fast.
- **Also falsified** if the stock or candidate run is blocked, uses a different host, or compares raw DDS to ROS 2 RMW.
- A ratio `≥ 100` on one payload is **not** a product DoD PASS and **not** a cross-host result.

There is **no** number on this page to “beat.” SCOREBOARD is a pointer to a **different** host/config history. `DoD: unmet` until M4 evidence is checked in as a new dated artifact — **without** editing SCOREBOARD.md.

---

## 5. Phased milestones

Each milestone is **docs/harness/spike** work unless a later PR explicitly lifts a Hold. Exit criteria are binary and evidence-based. None of them are met by this PR.

### M0 — Inventory

**Goal.** Write down what “stock ROS 2 DDS as used by `ros2_hzj`” actually calls, without a crate.

| Exit criteria | Hold list (still) |
|---------------|-------------------|
| RMW API subset used by this repo is listed (node, pub, sub, wait, take, service/action if present) against [`vendor/rmw/rmw/include/rmw/rmw.h`](../../vendor/rmw/rmw/include/rmw/rmw.h) as **read-only** | No vendor edits; no custom RMW |
| Frozen topic / QoS table copied by reference (R0 + `dds_topics.py`), plus a grep-backed list of any extra ROS 2 services/actions | No `dimos_bridge` behavior change |
| Wire-interop decision recorded: isolated domain vs must talk to stock Fast-DDS peers | No XML rewrite |
| Thor 2204 assumption table still marked UNVERIFIED or replaced with device facts | No SCOREBOARD edits; no invented µs |

### M1 — Rust RMW spike

**Goal.** Smallest possible `rmw_*` in Rust that can pub/sub one `std_msgs` (or equivalent) **after** a human lifts “No custom RMW.”

| Exit criteria | Hold list (still) |
|---------------|-------------------|
| Written approval that custom RMW Hold is lifted **for the spike only** | Agnocast / zenoh / Cega / vendor sources / XML / SCOREBOARD |
| Spike builds on **one** declared host (x86 CI image **or** Thor — label which). Identifier string visible to `prove_rmw.py`-style env/string check | Do not change gate thresholds or required CI phrases |
| One same-process pub/sub smoke (PASS/FAIL only, **no** percentiles required) | Do not claim 100×; do not edit `dimos_bridge` |
| Lives out-of-tree or under a clearly labeled **WIP** path that CI does not compile unless a workflow change is separately approved | 《3》–《6》 Hold |

### M2 — Parity harness

**Goal.** Automated checks that the spike matches §3 rows that M0 marked in-scope.

| Exit criteria | Hold list (still) |
|---------------|-------------------|
| Harness covers discovery, domain isolation, each R0 QoS row, pub/sub take/wait, and any M0-listed services/actions | No XML / SCOREBOARD / vendor patches |
| Each row records `PASS` / `FAIL` / `blocked` from **that** run — no pre-filled PASS | No fake cross-host |
| Failures do not get “fixed” by loosening stock QoS | No Agnocast / zenoh |

### M3 — Thor bring-up

**Goal.** Run stock Chain A **and** the spike on a real Thor (or record why not).

| Exit criteria | Hold list (still) |
|---------------|-------------------|
| Device facts replace §2 UNVERIFIED rows (OS, ISA, JetPack/L4T if present, ROS distro) | Do not invent JetPack versions |
| Stock `run_chain_a.sh` (or Docker recipe) produces a dated artifact **or** an honest `STATUS: blocked` with the missing package/runtime | Do not edit SCOREBOARD.md; new numbers go under `docs/artifacts/bench/<date>/` if/when humans ask |
| Spike cross-compiles or natively builds on ARM64; smoke from M1 re-run on device | Do not flash/tune as a latency cheat; no XML rewrite |

### M4 — Perf evidence

**Goal.** Execute §4. Compare. Accept or **falsify** 100×.

| Exit criteria | Hold list (still) |
|---------------|-------------------|
| Primary metric declared in writing before the run | No SCOREBOARD content edits |
| Stock and candidate artifacts on the same Thor, same topology/payload/QoS/API | No A-vs-B table; no summed P99 |
| Report states **hypothesis held** or **hypothesis falsified** with the ratio — never “DoD PASS” from docs CI | Cross-host still blocked unless a second host is real |
| Product DoD items in [feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md) stay unmet until those five evidence types exist | No Cega / Bridge rewrite |

---

## 6. Risks

| Risk | Why it matters | Mitigation on this track |
|------|----------------|--------------------------|
| **Wire protocol** | RTPS interop with stock Fast-DDS is a different (harder) target than an isolated Rust domain. Wrong choice looks like “parity FAIL” or silent packet loss. | M0 records the decision. Isolated-domain v0 is allowed if apps only see ROS 2 API. Interop is TBD, not assumed. |
| **Vendor DDS** | Patching `vendor/Fast-DDS` or swapping Unitree Cyclone looks faster to start and violates Hold; 0.10.2 vs 11.0.1 is already `drop-in FAIL`. | Read vendor as a map only. Spike is a new RMW, not a vendor fork. |
| **QoS edge cases** | Nav-path QoS ≠ `DimosROS` library default. Deadline / liveliness / durability mismatches break matching. | Parity harness keys off R0 rows first; extra QoS stays TBD. |
| **CI / Humble** | Required CI is structure/contracts/boundary on a host **without** Humble. Vendor trees are rolling/master, not Humble. Thor distro is UNVERIFIED. | Keep this track docs-only until M1. Never treat `check_*.py` green as DDS PASS. Do not vendor `rcl*`. |
| **Security** | DDS-Security, auth, identity — out of v0. Enabling later can change discovery and latency. | Leave security rows TBD / out of v0. 《6》 CVE remains Hold. |
| **100× storytelling** | A 2× win plus marketing language becomes a false DoD. | §4.3 falsification is mandatory. No number on this page. |
| **Memory-layer shortcuts** | iceoryx2 / Agnocast / loaned samples can look like 100× on `same-process` and fail `same-host` or ROS API parity. | Memory Hold stays. A later memory spike is not this plan’s M1. |

---

## 7. Remaining UNVERIFIED (do not fill casually)

- Exact JetPack / L4T / kernel / Ubuntu version on the Thor we will use.
- Whether Humble is installable and supported on that image vs Jazzy/other.
- Whether stock Fast-DDS implicit SHM works on that L4T.
- Complete list of ROS 2 **services** and **actions** actually exercised by `ros2_hzj` (frozen table is pub/sub).
- Whether wire interop with existing Fast-DDS peers is a product requirement.
- Any latency, throughput, CPU, or memory figure on Thor or elsewhere for a Rust candidate (**none exist in this PR**).
- Whether a human will lift “No custom RMW” for M1.

---

## 8. Related docs (pointers)

- [AGENTS.md](../../AGENTS.md) — dual-chain contract + Hold
- [ros2-dds-r0-interface-freeze.md](../architecture/ros2-dds-r0-interface-freeze.md) — domains, topics, QoS
- [ros2-source-map.md](../architecture/ros2-source-map.md) — publish / ingress / wait map
- [latency-attribution.md](../architecture/latency-attribution.md) — stage method, no SCOREBOARD copies
- [feishu-dual-chain-baseline.md](../architecture/feishu-dual-chain-baseline.md) — pointer only, no XML rewrite
- [feishu-dod-evidence.md](../architecture/feishu-dod-evidence.md) — `DoD: unmet`
- [feishu-sink-layers.md](../architecture/feishu-sink-layers.md) — custom RMW Hold
- [ci-cd-gates.md](../architecture/ci-cd-gates.md) — required jobs
- Stub index: [thor-2204/README.md](thor-2204/README.md)
