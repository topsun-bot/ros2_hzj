# iter1 change — Humble-valid History QoS in `config/fastdds.xml`

**One change.** Config-only. Ask a human to merge; this run does not merge.

## Hypothesis

2026-09-10 Chain A baselines logged Humble Fast-DDS 2.6 XMLPARSER errors:

```
Invalid element found into 'writerQosPoliciesType'. Name: history
Error parsing '/work/config/fastdds.xml'  → loadXMLFile
```

`<history>` inside `<qos>` is valid on newer Fast-DDS XSD, **not** on Humble 2.6 (`writerQosPoliciesType` / `readerQosPoliciesType`). `loadXMLFile` failing means the contract seed (default participant `domainId` 42 + named writer/reader profiles) did **not** apply. Domain 42 still came from `ROS_DOMAIN_ID`.

**Prediction:** after moving History to `<topic><historyQos>` (Humble-valid; same KEEP_LAST / depth as the freeze table), the file loads. Ping-pong still sets rclpy QoS in `scripts/bench/pingpong.py` and does not bind the named foxglove / goal_pose / way_point profiles, so p50/p95/p99 may be unchanged within run noise. That is still a successful like-to-like remasurement of “profiles actually load.”

This does **not** prove a Feishu / large-packet / real-robot root cause. 64 B same-process is not that scene.

## Exact diff (behavior)

In `config/fastdds.xml` only: for each contract `data_writer` / `data_reader`, remove

```xml
<qos>
  ...
  <history><kind>KEEP_LAST</kind><depth>N</depth></history>
</qos>
```

and write the same kind/depth as

```xml
<topic>
  <historyQos>
    <kind>KEEP_LAST</kind>
    <depth>N</depth>
  </historyQos>
</topic>
<qos>
  <!-- reliability + durability unchanged -->
</qos>
```

`foxglove_teleop_to_cmd_vel` stays BEST_EFFORT / KEEP_LAST / depth 1. `goal_pose` and `way_point` stay RELIABLE / VOLATILE / KEEP_LAST / depth 5. Participant profile unchanged (`domainId` 42, no transport knobs).

`config/fastdds.zh.md` notes the Humble schema constraint. No other files in the functional change.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / `testdata.py` / ping-pong QoS or sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`, `FASTRTPS_DEFAULT_PROFILES_FILE`)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no socket-buffer / SHM / UDP-only transport knobs
- Chain B Cyclone URI / iceoryx
- Cross-host UDP (still blocked; single VM)
- 《3》90%/LLM scoring, 《4》Mac/preprod hero cases, 《5》Promptfoo, 《6》CVE audit

## Remeasure command (same as baseline)

```bash
BENCH_DATE=2026-09-10-iter1 CHAIN_A_TOPOLOGIES='same-process same-host' \
  ./scripts/bench/docker_chain_a.sh
```

Like-to-like only: Chain A `same-process` and `same-host`, sizes 64 / 1024 / 16384 / 65536, 400 samples, cases `ros_high_throughput` and `ros_reliable`. Deltas vs `docs/artifacts/bench/2026-09-10/` in [`delta.md`](delta.md). Do not put Chain A and Chain B in one table.

Remasurement landed in this directory. Humble XMLPARSER no longer rejects the file. Large-payload p50 stayed within a few percent; the change is **kept**. This still does not prove Feishu / field root cause.
