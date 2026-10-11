#!/usr/bin/env python3
"""Read-only independent audit of real Colima artifacts; never imports ROS."""

import argparse
from collections import Counter
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=Path(__file__).resolve().parent.parent / "matrix")
    parser.add_argument("--source-commit", default="faadb365f2211ed9d007d803b72d6fa6e445cd22")
    args = parser.parse_args()
    path = args.matrix.resolve()
    repo = Path(__file__).resolve().parents[5]
    errors = []

    def load(filename):
        def reject_constant(value):
            raise ValueError(f"non-standard JSON constant {value} in {filename}")
        return json.loads(filename.read_text(), parse_constant=reject_constant)

    def check(condition, description):
        if not condition:
            errors.append(description)

    def finite(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

    def near(value, expected):
        return finite(value) and math.isclose(value, expected, rel_tol=1e-10, abs_tol=1e-7)

    results = load(path / "results.json")
    repeats = load(path / "repeats.json")
    rows = results["cases"]
    keys = (
        "rmw", "rmw_version", "host_class", "ros_distro", "topology", "qos",
        "mode", "size_bytes", "hz_offered", "duration_s", "warmup_s",
    )
    metrics = (
        "p50_us", "p99_us", "max_us", "throughput_msg_s", "throughput_mbyte_s",
        "pub_cpu_percent", "sub_cpu_percent", "pub_rss_kb_peak", "sub_rss_kb_peak",
    )
    expected = set(itertools.product(
        ("rmw_fastrtps_cpp", "rmw_cyclonedds_cpp"), ("reliable", "best_effort"),
        (1024, 65536, 1048576, 4194304), (1, 2, 3),
    ))
    actual = [(r["rmw"], r["qos"], r["size_bytes"], r["repeat"]) for r in rows]
    check(len(rows) == 48 and len(set(actual)) == 48 and set(actual) == expected, "matrix mismatch")
    check(results["expected_repeats"] == repeats["expected_repeats"] == 3, "expected repeats mismatch")
    check(results["status"] == "ok" and repeats["status"] == "complete", "top-level status mismatch")
    check(results["not_final_baseline"] and repeats["not_final_baseline"], "final-baseline flag")
    check(len(repeats["groups"]) == 16, "group count mismatch")
    resources, delays, counts, resource_offsets, resource_counts = [], [], [], [], []
    actual_rmws = Counter()
    invalid_samples = duplicate_samples = 0
    for row in rows:
        case = f"{row['rmw']}/{row['qos']}/{row['mode']}/{row['size_bytes']}/r{row['repeat']}"
        case_path = path / "cases" / case
        pub, sub, processes = (load(case_path / name) for name in ("pub.json", "sub.json", "processes.json"))
        check(row["status"] == pub["status"] == sub["status"] == "ok", case + " status")
        check(processes["exit_codes"] == {"sub": 0, "pub": 0} and not processes["error"], case + " exit")
        for role, raw in (("pub", pub), ("sub", sub)):
            actual_rmws[raw["rmw"]] += 1
            check(raw["rmw"] == raw["requested_rmw"] == row["rmw"], case + " actual RMW")
            check(raw["resource_window_observed"], case + " resource window")
            check(raw["sample_count"] >= 2, case + " resource samples")
            resource_counts.append(raw["sample_count"])
            for metric in ("cpu_percent", "rss_kb_avg", "rss_kb_peak", "elapsed_s"):
                check(finite(raw[metric]) and raw[metric] >= 0, case + " " + metric)
            for metric in ("cpu_percent", "rss_kb_avg", "rss_kb_peak"):
                check(near(row[role + "_" + metric], raw[metric]), case + " merged " + metric)
            check(raw["rss_kb_peak"] >= raw["rss_kb_avg"], case + " rss peak")
            resource_offsets.append((raw["resource_sample_end_mono_s"] - raw["measure_end_ns"] / 1e9) * 1000)
            resources.append(raw["cpu_percent"])
        check(pub["measure_start_ns"] == sub["measure_start_ns"] and pub["measure_end_ns"] == sub["measure_end_ns"], case + " timestamps")
        check(sub["measure_end_ns"] - sub["measure_start_ns"] == int(row["duration_s"] * 1e9), case + " measurement duration")
        samples = sub["samples_ns"]
        counts.append(len(samples))
        delays.extend(samples)
        check(row["sent"] == pub["sent"] and row["received"] == sub["received"] == len(samples), case + " sample count")
        check(len(samples) <= pub["sent"], case + " received exceeds sent")
        invalid_samples += sub["invalid_count"]
        duplicate_samples += sub["duplicate_count"]
        check(sub["invalid_count"] == sub["duplicate_count"] == 0, case + " invalid/duplicate sample")
        check(all(finite(value) and value >= 0 for value in samples), case + " bad latency")
        check(near(row["loss_ratio"], 1 - len(samples) / pub["sent"]), case + " loss")
        for metric, value in (
            ("throughput_msg_s", len(samples) / row["duration_s"]),
            ("throughput_mbyte_s", len(samples) * row["size_bytes"] / row["duration_s"] / 1e6),
        ):
            check(near(row[metric], value) and near(sub[metric], value), case + " " + metric)
        ordered = sorted(samples)
        for metric, percentile in (("p50_us", .5), ("p90_us", .9), ("p99_us", .99)):
            index = (len(ordered) - 1) * percentile
            lo, hi = int(index), min(int(index) + 1, len(ordered) - 1)
            value = (ordered[lo] * (1 - (index - lo)) + ordered[hi] * (index - lo)) / 1000
            check(near(sub[metric], value) and near(row[metric], value), case + " " + metric)
        for metric, value in (
            ("min_us", min(samples) / 1000), ("max_us", max(samples) / 1000),
            ("mean_us", statistics.mean(samples) / 1000),
        ):
            check(near(sub[metric], value) and near(row[metric], value), case + " " + metric)
    for group in repeats["groups"]:
        members = [row for row in rows if all(row[key] == group[key] for key in keys)]
        check(len(members) == 3 and sorted(row["repeat"] for row in members) == [1, 2, 3], "group membership")
        check(group["status"] == "complete" and not group["warnings"], "group incomplete")
        check(group["observed_runs"] == group["successful_runs"] == group["valid_successful_runs"] == 3, "group run count")
        for metric in metrics:
            values = [row[metric] for row in members]
            stats = group["metrics"][metric]
            mean, stdev = statistics.mean(values), statistics.stdev(values)
            check(stats["n"] == 3, "metric count " + metric)
            for key, value in (("mean", mean), ("sample_stdev", stdev), ("min", min(values)), ("max", max(values))):
                check(near(stats[key], value), "metric statistic " + metric + "/" + key)
            check(near(stats["cv"], stdev / abs(mean)) if mean else stats["cv"] is None, "metric CV " + metric)
    with (path / "results.csv").open(newline="") as file:
        csv_rows = list(csv.DictReader(file))
    with (path / "repeats.csv").open(newline="") as file:
        csv_groups = list(csv.DictReader(file))
    check(len(csv_rows) == 48 and len(csv_groups) == 144, "CSV row count")
    for csv_row, row in zip(csv_rows, rows):
        for key, value in csv_row.items():
            check(value == str(row.get(key, "")), "results CSV mismatch " + key)
    for csv_group in csv_groups:
        members = [group for group in repeats["groups"] if all(str(group[key]) == csv_group[key] for key in keys)]
        check(len(members) == 1, "repeats CSV group mismatch")
        if members:
            stats = members[0]["metrics"][csv_group["metric"]]
            for key, value in stats.items():
                check(csv_group[key] == (str(value) if value is not None else ""), "repeats CSV stat mismatch " + key)
    check(load(path / "environment.json") == results["environment"], "environment differs")
    hashes = {}
    worktree_differences = []
    for filename, recorded in results["environment"]["source_sha256"].items():
        relative = "scripts/jazzy_baseline/" + filename
        source = subprocess.run(["git", "show", f"{args.source_commit}:{relative}"], cwd=repo, capture_output=True, check=True).stdout
        committed = hashlib.sha256(source).hexdigest()
        current = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        check(recorded == committed, "recorded source SHA256 does not match committed source " + filename)
        if current != recorded:
            worktree_differences.append(filename)
        hashes[filename] = {
            "recorded": recorded, "committed": committed, "current": current,
            "recorded_matches_commit": recorded == committed,
            "current_matches_recorded": current == recorded,
        }
    loss_groups = []
    for group in repeats["groups"]:
        members = [row for row in rows if all(row[key] == group[key] for key in keys)]
        if any(row["loss_ratio"] for row in members):
            loss_groups.append({
                **{key: group[key] for key in ("rmw", "qos", "size_bytes")},
                "received": [row["received"] for row in members],
                "loss_ratio": [row["loss_ratio"] for row in members],
            })
    print(json.dumps({
        "cases": len(rows), "groups": len(repeats["groups"]), "worker_processes": 2 * len(rows),
        "actual_rmw_workers": dict(actual_rmws),
        "case_statuses": dict(Counter(row["status"] for row in rows)),
        "repeat_statuses": dict(Counter(group["status"] for group in repeats["groups"])),
        "sent_total": sum(row["sent"] for row in rows), "received_total": sum(row["received"] for row in rows),
        "latency_samples_per_run_range": [min(counts), max(counts)],
        "resource_samples_per_process_range": [min(resource_counts), max(resource_counts)],
        "loss_ratio_range": [min(row["loss_ratio"] for row in rows), max(row["loss_ratio"] for row in rows)],
        "invalid_samples": invalid_samples, "duplicate_samples": duplicate_samples,
        "cpu_percent_range": [min(resources), max(resources)],
        "latency_us_range": [min(delays) / 1000, max(delays) / 1000],
        "p99_cv_range": [min(group["metrics"]["p99_us"]["cv"] for group in repeats["groups"]), max(group["metrics"]["p99_us"]["cv"] for group in repeats["groups"])],
        "resource_end_offset_ms_range": [min(resource_offsets), max(resource_offsets)],
        "loss_groups": loss_groups,
        "source_commit": args.source_commit,
        "run_recorded_git_sha": results["environment"]["git_sha_ros2_hzj"],
        "run_recorded_worktree_dirty": results["environment"]["git_worktree_dirty"],
        "source_sha256": hashes,
        "current_worktree_differs_from_measured_source": worktree_differences,
        "provenance_note": "Run-source verification uses the pinned source commit. Subsequent working-tree edits are recorded separately and are not claimed as measured.",
        "limits": "Only same-host processes in Colima; 12-30 latency samples per run over 3 s. These p99 observations do not establish stable tail performance or final baseline acceptance.",
        "verification_errors": errors,
    }, indent=2, sort_keys=True, allow_nan=False))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
