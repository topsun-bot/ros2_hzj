"""合成报文和时钟的回归测试，不产生或声称 ROS 性能结果。"""

from __future__ import annotations

from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from metrics import read_cpu_jiffies
from wire import pack
from worker import MeasurementResources, MeasurementSamples, _wait_go, _write_result, measurement_bounds, parse_args


class MeasurementTests(unittest.TestCase):
    def test_half_open_send_window_excludes_warmup_and_accepts_drain(self) -> None:
        samples = MeasurementSamples(100, 200, 1024)
        samples.observe(pack(1, 99, 1024), 110)
        samples.observe(pack(2, 100, 1024), 120)
        samples.observe(pack(3, 199, 1024), 250)
        samples.observe(pack(4, 200, 1024), 210)
        self.assertEqual(samples.samples_ns, [20, 51])
        self.assertEqual(samples.outside_window_count, 2)

    def test_duplicate_and_malformed_messages_are_excluded(self) -> None:
        samples = MeasurementSamples(100, 200, 1024)
        samples.observe(pack(1, 100, 1024), 120)
        samples.observe(pack(1, 100, 1024), 121)
        samples.observe(pack(2, 150, 1024), 149)
        samples.observe(pack(3, 150, 1024)[:-1], 160)
        bad_magic = bytearray(pack(4, 150, 1024))
        bad_magic[0] ^= 0xFF
        samples.observe(bad_magic, 160)
        self.assertEqual(samples.samples_ns, [20])
        self.assertEqual(samples.duplicate_count, 1)
        self.assertEqual(samples.invalid_count, 3)

    def test_rtt_requires_matching_sequence_and_send_stamp(self) -> None:
        samples = MeasurementSamples(100, 200, 1024)
        pending = {1: 100}
        samples.observe(pack(1, 110, 1024), 130, pending)
        self.assertEqual(pending, {1: 100})
        samples.observe(pack(1, 100, 1024), 140, pending)
        samples.observe(pack(1, 100, 1024), 150, pending)
        self.assertEqual(samples.samples_ns, [40])
        self.assertEqual(pending, {})
        self.assertEqual(samples.duplicate_count, 1)

    def test_zero_samples_are_blocked(self) -> None:
        result = MeasurementSamples(100, 200, 1024).result(10)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["received"], 0)

    def test_failed_worker_results_are_strict_json(self) -> None:
        result = MeasurementSamples(100, 200, 1024).result(10)
        result["resources"] = {"values": [float("inf"), float("-inf")]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.json"
            _write_result(path, result)
            def reject_constant(value):
                raise ValueError(value)
            parsed = json.loads(path.read_text(), parse_constant=reject_constant)
        self.assertEqual(parsed["status"], "blocked")
        self.assertIsNone(parsed["p99_us"])
        self.assertEqual(parsed["resources"]["values"], [None, None])

    def test_throughput_uses_full_window_even_with_missing_tail(self) -> None:
        samples = MeasurementSamples(0, 10_000_000_000, 1024)
        for seq in range(10):
            stamp = seq * 500_000_000
            samples.observe(pack(seq, stamp, 1024), stamp + 1000)
        result = samples.result(10)
        self.assertEqual(result["throughput_msg_s"], 1.0)
        self.assertEqual(result["window_s"], 10)
        self.assertEqual(len(result["samples_ns"]), 10)

    def test_all_roles_derive_identical_bounds(self) -> None:
        self.assertEqual(measurement_bounds(10.25, 0.5, 2), (10_750_000_000, 12_750_000_000))

    def test_resources_exclude_warmup_and_drain(self) -> None:
        sampler = Mock()
        sampler.as_dict.return_value = {}
        with patch("worker.ProcSampler", return_value=sampler):
            resources = MeasurementResources(100, 200)
            resources.update(99)
            sampler.start.assert_not_called()
            resources.update(100)
            resources.update(150)
            sampler.start.assert_called_once()
            sampler.stop.assert_not_called()
            resources.update(200)
            resources.update(250)
            resources.finish()
            sampler.stop.assert_called_once()

    def test_proc_stat_comm_may_contain_spaces_and_parentheses(self) -> None:
        suffix = ["S"] + ["0"] * 10 + ["123", "45"] + ["0"] * 5
        with patch("metrics.Path.read_text", return_value="42 (worker with ) spaces) " + " ".join(suffix)):
            self.assertEqual(read_cpu_jiffies(42), 168)

    def test_missing_or_expired_go_is_failure(self) -> None:
        with patch("worker.time.monotonic", side_effect=[0, 61]):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                _wait_go(Path("synthetic-sync"), None)
        with patch("worker.time.monotonic", return_value=20):
            with self.assertRaisesRegex(RuntimeError, "expired"):
                _wait_go(None, 10)

    def test_nonfinite_and_unbounded_worker_values_rejected(self) -> None:
        base = ["--role", "pub", "--size", "1024", "--hz", "10", "--duration", "1", "--result-json", "unused"]
        for flag, value in (("--hz", "nan"), ("--duration", "inf"), ("--warmup", "-1"), ("--discover", "0"), ("--margin", "nan"), ("--size", "4194305"), ("--go-at-mono", "inf")):
            with self.subTest(flag=flag, value=value), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    parse_args(base + [flag, value])
                self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
