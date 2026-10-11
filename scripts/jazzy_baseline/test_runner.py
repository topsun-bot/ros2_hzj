"""Synthetic regression tests for orchestration; these are not ROS measurements."""

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import envinfo
import run


class RunnerTests(unittest.TestCase):
    def spec(self, mode="oneway"):
        return run.build_specs(run.parse_args([
            "--rmw", "rmw_fastrtps_cpp", "--sizes", "1024", "--qos", "reliable",
            "--repeats", "1", "--mode", mode,
        ]))[0]

    def test_bad_config_is_rejected(self):
        for arguments in (
            ["--duration", "nan"], ["--hz", "inf"], ["--warmup", "-1"],
            ["--repeats", "0"], ["--qos", "unknown"], ["--rmw", "../escape"],
            ["--sizes", "1024,1024"], ["--sizes", "4194305"], ["--domain", "233"],
            ["--qos", ","], ["--topic-prefix", "/bad-prefix"],
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                run.build_specs(run.parse_args(arguments))

    def test_default_matrix_has_three_repeats(self):
        specs = run.build_specs(run.parse_args([]))
        self.assertEqual(len(specs), 48)
        self.assertEqual({s["repeat"] for s in specs}, {1, 2, 3})

    def test_only_jazzy_is_accepted(self):
        with mock.patch.dict(os.environ, {"ROS_DISTRO": "humble", "AMENT_PREFIX_PATH": "/opt/ros/humble"}):
            self.assertFalse(envinfo.ros_sourced())
        with mock.patch.dict(os.environ, {"ROS_DISTRO": "jazzy", "AMENT_PREFIX_PATH": "/opt/ros/jazzy"}):
            self.assertTrue(envinfo.ros_sourced())

    def test_os_pretty_handles_python39_and_missing_linux_release(self):
        for error in (AttributeError("Python 3.9"), OSError("no os-release")):
            with mock.patch.object(envinfo.platform, "freedesktop_os_release", create=True,
                                   side_effect=error), mock.patch.object(envinfo.platform, "system", return_value="Darwin"):
                self.assertEqual(envinfo.os_pretty(), "Darwin")

    def test_stock_child_does_not_inherit_profiles_or_peers(self):
        keys = ("FASTRTPS_DEFAULT_PROFILES_FILE", "FASTDDS_DEFAULT_PROFILES_FILE",
                "CYCLONEDDS_URI", "RMW_FASTRTPS_USE_QOS_FROM_XML",
                "RMW_FASTRTPS_PUBLICATION_MODE", "ROS_STATIC_PEERS")
        with mock.patch.dict(os.environ, {key: "synthetic-private-config" for key in keys}):
            child = run._child_env("rmw_cyclonedds_cpp", 87, True)
        self.assertTrue(all(key not in child for key in keys))
        self.assertEqual(child["ROS_AUTOMATIC_DISCOVERY_RANGE"], "LOCALHOST")
        self.assertEqual(child["SKIP_DEFAULT_XML"], "1")

    def test_invalid_results_cannot_be_ok(self):
        good = {"status": "ok", "rmw": "rmw_fastrtps_cpp", "sent": 10, "received": 8,
                **{key: 1.0 for key in ("p50_us", "p90_us", "p99_us", "max_us",
                                        "throughput_msg_s", "throughput_mbyte_s")}}
        for patch in ({"received": 0}, {"received": 11}, {"received": "8"},
                      {"p99_us": float("nan")}, {"rmw": "different_rmw"}):
            row = run._merge_case(spec=self.spec(), pub=good, sub={**good, **patch},
                                  rmw_version="synthetic", host_class="test")
            self.assertEqual(row["status"], "blocked", patch)
        row = run._merge_case(spec=self.spec(), pub=good, sub=good,
                              rmw_version="synthetic", host_class="test")
        self.assertEqual(row["status"], "ok")
        self.assertAlmostEqual(row["loss_ratio"], .2)

    def test_rtt_zero_received_does_not_fall_back_to_echo_count(self):
        pub = {"status": "ok", "sent": 3, "received": 0}
        sub = {"status": "ok", "received": 3}
        row = run._merge_case(spec=self.spec("rtt"), pub=pub, sub=sub,
                              rmw_version="synthetic", host_class="test")
        self.assertEqual(row["received"], 0)
        self.assertEqual(row["status"], "blocked")

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "results.json"
            marker.write_text("existing user artifact")
            with self.assertRaises(ValueError):
                run.run_matrix(run.parse_args(["--out", temp]))
            self.assertEqual(marker.read_text(), "existing user artifact")

    def test_partial_matrix_exits_nonzero(self):
        with mock.patch.object(run, "run_matrix", return_value={"status": "partial"}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run.main(["--smoke"]), 2)

    def test_worker_nonzero_dominates_valid_json_and_is_logged(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            worker = temp / "synthetic_worker.py"
            worker.write_text('''import json, pathlib, sys, time
def arg(key): return sys.argv[sys.argv.index(key)+1]
role = arg('--role')
sync = pathlib.Path(arg('--sync-dir'))
(sync / (role+'.ready')).write_text('ready')
while not (sync / 'go').exists(): time.sleep(.01)
pathlib.Path(arg('--result-json')).write_text(json.dumps({'status':'ok','sent':1,'received':1}))
print('synthetic worker output', flush=True)
sys.exit(7 if role == 'pub' else 0)
''')
            args = run.parse_args(["--worker", str(worker), "--discover", "2", "--margin", ".1"])
            case = temp / "case"
            pub, sub = run._run_pair(args, self.spec(), case, os.environ.copy())
            self.assertEqual(pub["status"], "blocked")
            self.assertIn("exited 7", sub["blocked_reason"])
            evidence = json.loads((case / "processes.json").read_text())
            self.assertEqual(evidence["exit_codes"], {"sub": 0, "pub": 7})
            self.assertIn("synthetic worker output", (case / "pub.log").read_text())
            before = (case / "pub.json").read_bytes()
            with self.assertRaises(FileExistsError):
                run._run_pair(args, self.spec(), case, os.environ.copy())
            self.assertEqual((case / "pub.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
