#!/usr/bin/env python3
"""Synthetic report fixtures only; these tests are not ROS performance data."""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest

from report import GROUP_COLUMNS, REPEAT_METRICS, render_summary, summarize_repeats, write_reports


def fixture() -> dict:
    rows = []
    for repeat in (1, 2, 3):
        rows.append({
            "status": "ok", "repeat": repeat, "rmw": "synthetic_rmw",
            "rmw_version": "synthetic", "host_class": "synthetic",
            "ros_distro": "synthetic", "topology": "same-host", "qos": "reliable",
            "mode": "oneway", "size_bytes": 1024, "hz_offered": 20,
            "duration_s": 10, "warmup_s": 2,
            **{metric: repeat * 10.0 for metric in REPEAT_METRICS},
        })
    return {
        "status": "ok", "fixture_type": "synthetic_not_a_ros_measurement",
        "expected_repeats": 3, "not_final_baseline": True,
        "environment": {"disclaimer": "Synthetic unit-test data; not a ROS measurement."},
        "cases": rows,
    }


class RepeatReportsTest(unittest.TestCase):
    def test_three_distinct_runs_use_sample_standard_deviation(self) -> None:
        summary = summarize_repeats(fixture())
        self.assertEqual(summary["status"], "complete")
        group = summary["groups"][0]
        self.assertEqual(group["successful_runs"], 3)
        self.assertEqual(group["expected_repeats"], 3)
        self.assertEqual(group["warnings"], [])
        self.assertEqual(group["metrics"]["p99_us"], {
            "n": 3, "mean": 20.0, "sample_stdev": 10.0,
            "min": 10.0, "max": 30.0, "cv": 0.5,
        })

    def test_every_grouping_dimension_stays_separate(self) -> None:
        for column in GROUP_COLUMNS:
            with self.subTest(column=column):
                payload = fixture()
                other = copy.deepcopy(payload["cases"])
                for row in other:
                    value = row[column]
                    row[column] = value + 1 if isinstance(value, (int, float)) else value + "_other"
                payload["cases"] += other
                summary = summarize_repeats(payload)
                self.assertEqual(len(summary["groups"]), 2)
                self.assertEqual(summary["status"], "complete")

    def test_failure_preserves_reason_and_cannot_complete(self) -> None:
        for status in ("blocked", "partial", None):
            with self.subTest(status=status):
                payload = fixture()
                payload["cases"][1].update(status=status, blocked_reason="synthetic failure")
                group = summarize_repeats(payload)["groups"][0]
                self.assertEqual(group["status"], "partial")
                self.assertEqual(group["successful_runs"], 2)
                self.assertEqual(group["missing_successful_repeat_ids"], [2])
                self.assertEqual(group["metrics"]["p50_us"]["n"], 2)
                self.assertIn("synthetic failure", " ".join(group["warnings"]))

    def test_duplicate_repeat_excludes_all_copies(self) -> None:
        payload = fixture()
        payload["cases"].append(copy.deepcopy(payload["cases"][1]))
        group = summarize_repeats(payload)["groups"][0]
        self.assertEqual(group["status"], "partial")
        self.assertEqual(group["successful_runs"], 4)
        self.assertEqual(group["valid_successful_runs"], 2)
        self.assertEqual(group["duplicate_repeat_ids"], [2])
        self.assertEqual(group["metrics"]["p50_us"]["n"], 2)

    def test_missing_repeat_and_larger_expected_count(self) -> None:
        payload = fixture()
        payload["expected_repeats"] = 4
        group = summarize_repeats(payload)["groups"][0]
        self.assertEqual(group["status"], "partial")
        self.assertEqual(group["missing_successful_repeat_ids"], [4])

    def test_unknown_expected_or_invalid_repeat_cannot_complete(self) -> None:
        for expected in (None, 0, -1, "3", True):
            with self.subTest(expected=expected):
                payload = fixture()
                payload["expected_repeats"] = expected
                self.assertEqual(summarize_repeats(payload)["status"], "partial")
        for repeat in (None, 0, -1, "1", True, 9):
            with self.subTest(repeat=repeat):
                payload = fixture()
                payload["cases"][0]["repeat"] = repeat
                group = summarize_repeats(payload)["groups"][0]
                self.assertEqual(group["status"], "partial")
                self.assertTrue(group["warnings"])

    def test_nonfinite_missing_or_nonnumeric_metric_is_visible(self) -> None:
        for value in (float("nan"), float("inf"), -float("inf"), None, "12", True):
            with self.subTest(value=value):
                payload = fixture()
                payload["cases"][1]["p99_us"] = value
                group = summarize_repeats(payload)["groups"][0]
                self.assertEqual(group["status"], "partial")
                self.assertEqual(group["successful_runs"], 3)
                self.assertEqual(group["valid_successful_runs"], 2)
                self.assertEqual(group["metrics"]["p99_us"]["n"], 2)
                self.assertEqual(group["metrics"]["p50_us"]["n"], 3)
                self.assertIn("p99_us", " ".join(group["warnings"]))

    def test_one_run_does_not_invent_variability(self) -> None:
        payload = fixture()
        payload["cases"] = payload["cases"][:1]
        payload["expected_repeats"] = 1
        group = summarize_repeats(payload)["groups"][0]
        self.assertEqual(group["status"], "partial")
        self.assertEqual(group["metrics"]["p50_us"]["n"], 1)
        self.assertIsNone(group["metrics"]["p50_us"]["sample_stdev"])
        self.assertIsNone(group["metrics"]["p50_us"]["cv"])

    def test_zero_mean_has_no_cv(self) -> None:
        payload = fixture()
        for row in payload["cases"]:
            row["pub_cpu_percent"] = 0.0
        group = summarize_repeats(payload)["groups"][0]
        self.assertEqual(group["status"], "complete")
        self.assertEqual(group["metrics"]["pub_cpu_percent"]["sample_stdev"], 0.0)
        self.assertIsNone(group["metrics"]["pub_cpu_percent"]["cv"])

    def test_empty_and_all_failed_are_blocked(self) -> None:
        payload = fixture()
        for row in payload["cases"]:
            row["status"] = "blocked"
        summary = summarize_repeats(payload)
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["groups"][0]["metrics"]["p50_us"]["n"], 0)
        payload["cases"] = []
        summary = summarize_repeats(payload)
        self.assertEqual(summary["status"], "blocked")
        self.assertTrue(summary["warnings"])

    def test_written_json_is_strict_and_csv_has_stats(self) -> None:
        payload = fixture()
        payload["cases"][0]["p99_us"] = float("nan")
        payload["nested_nonfinite"] = [float("inf"), {"x": -float("inf")}]
        def reject_constant(value: str) -> None:
            raise AssertionError(f"non-standard JSON constant {value}")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_reports(out, payload)
            for filename in ("results.json", "repeats.json", "environment.json"):
                parsed = json.loads((out / filename).read_text(), parse_constant=reject_constant)
                self.assertIsInstance(parsed, dict)
            parsed = json.loads((out / "results.json").read_text())
            self.assertIsNone(parsed["cases"][0]["p99_us"])
            self.assertEqual(parsed["nested_nonfinite"], [None, {"x": None}])
            with (out / "repeats.csv").open(newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), len(REPEAT_METRICS))
            self.assertEqual(rows[0]["sample_stdev"], "10.0")
            self.assertEqual(rows[0]["status"], "partial")

    def test_markdown_repeat_status_reason_columns_align(self) -> None:
        payload = fixture()
        payload["cases"][1].update(status="blocked", blocked_reason="synthetic failure")
        text = render_summary(payload)
        rows = [line for line in text.splitlines() if line.startswith("| ")]
        cases = [line for line in rows if "synthetic failure" in line or line.startswith(("| 1 |", "| 3 |"))]
        header = next(line for line in rows if line.startswith("| repeat |"))
        self.assertEqual(len(cases), 3)
        self.assertTrue(all(line.count("|") == header.count("|") for line in cases))
        self.assertIn("不是合并样本后的总体分位数", text)
        self.assertIn("synthetic failure", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
