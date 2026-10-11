#!/usr/bin/env python3
"""Unit tests that do not need ROS 2. Exit 0 prints a stable success marker."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from defaults import CSV_COLUMNS, HEADER_SIZE, WIRE_MAGIC, hz_for_size
from envinfo import collect, render_md, rmw_available
from metrics import percentiles_us
from report import render_summary, write_reports
from run import _blocked_row, _write_blocked_run, build_specs, parse_args
from wire import magic_ok, pack, unpack

SUCCESS_MARKER = "jazzy baseline selftest: PASS"


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_percentiles() -> None:
    empty = percentiles_us([])
    _assert(empty["p50_us"] != empty["p50_us"], "empty p50 should be nan")
    one = percentiles_us([1_000_000])
    _assert(abs(one["p50_us"] - 1000.0) < 1e-9, one)
    _assert(abs(one["p90_us"] - 1000.0) < 1e-9, one)
    xs = [i * 1000 for i in range(1, 101)]  # 1..100 µs in ns? 1000ns=1us
    # 1..100 * 1000 ns = 1..100 µs
    got = percentiles_us(xs)
    _assert(abs(got["min_us"] - 1.0) < 1e-6, got)
    _assert(abs(got["max_us"] - 100.0) < 1e-6, got)
    _assert(got["p50_us"] > 40 and got["p50_us"] < 60, got)
    _assert(got["p90_us"] >= got["p50_us"], got)
    _assert(got["p99_us"] >= got["p90_us"], got)
    print("  ok percentiles")


def test_wire() -> None:
    blob = pack(7, 123456789, 64)
    _assert(len(blob) == 64, len(blob))
    header = unpack(blob)
    _assert(header.seq == 7, header)
    _assert(header.t0_ns == 123456789, header)
    _assert(header.magic == WIRE_MAGIC, header)
    _assert(magic_ok(header), header)
    try:
        pack(0, 0, HEADER_SIZE - 1)
    except ValueError:
        print("  ok wire rejects short size")
    else:
        raise AssertionError("short pack must fail")


def test_hz() -> None:
    _assert(hz_for_size(1024, None) == 100.0, hz_for_size(1024, None))
    _assert(hz_for_size(4194304, None) == 2.0, hz_for_size(4194304, None))
    _assert(hz_for_size(999, 12.5) == 12.5, hz_for_size(999, 12.5))
    try:
        hz_for_size(1024, 0)
    except ValueError:
        print("  ok hz defaults")
    else:
        raise AssertionError("hz 0 must fail")


def test_specs_and_cli() -> None:
    args = parse_args(
        [
            "--smoke",
            "--out",
            "/tmp/jazzy-baseline-selftest-unused",
        ]
    )
    specs = build_specs(args)
    _assert(args.topology == "same-host", args.topology)
    _assert(args.repeats == 1, args.repeats)
    sizes = {s["size"] for s in specs}
    _assert(sizes == {1024, 65536}, sizes)
    _assert(all(s["mode"] == "oneway" for s in specs), specs)
    _assert(all(s["qos"] == "reliable" for s in specs), specs)
    rmws = {s["rmw"] for s in specs}
    _assert(rmws == {"rmw_fastrtps_cpp", "rmw_cyclonedds_cpp"}, rmws)
    print(f"  ok smoke matrix {len(specs)} cases")


def test_blocked_reports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        args = parse_args(["--smoke", "--out", str(out), "--allow-missing-ros"])
        payload = _write_blocked_run(out, args, "ROS not loaded (selftest)", build_specs(args))
        _assert(payload["status"] == "blocked", payload)
        _assert((out / "results.json").is_file(), "results.json")
        _assert((out / "results.csv").is_file(), "results.csv")
        _assert((out / "summary.md").is_file(), "summary.md")
        _assert((out / "environment.md").is_file(), "environment.md")
        csv_text = (out / "results.csv").read_text(encoding="utf-8")
        header = csv_text.splitlines()[0].split(",")
        _assert(header == list(CSV_COLUMNS), header)
        summary = (out / "summary.md").read_text(encoding="utf-8")
        _assert("not_final_baseline" in summary, summary[:200])
        _assert("rmw_fastrtps_cpp" in summary, "separate rmw tables")
        _assert("STATUS: blocked" in (out / "environment.md").read_text(encoding="utf-8") or "blocked" in summary, summary)
        print("  ok blocked report artifacts")


def test_env_and_rmw_probe() -> None:
    env = collect(SCRIPT_DIR.parents[1], extra={"status": "blocked", "blocked_reason": "selftest"})
    md = render_md(env)
    _assert("not_final_baseline" in md, md)
    _assert("stock Jazzy" in md or "Stock Jazzy" in md, md)
    _assert(env["host_class"], env)
    # No Jazzy prefix on this host unless someone installed it; probe must not crash.
    _assert(rmw_available("rmw_not_a_real_impl") is False, "fake rmw")
    print("  ok env render")


def test_merge_row_schema() -> None:
    spec = {
        "rmw": "rmw_fastrtps_cpp",
        "qos": "reliable",
        "mode": "oneway",
        "topology": "same-host",
        "size": 1024,
        "hz": 20.0,
        "duration": 2.0,
        "warmup": 0.5,
        "repeat": 1,
    }
    row = _blocked_row(spec, "no ros", "cursor-cloud-vm", "not-installed")
    missing = [c for c in CSV_COLUMNS if c not in row]
    _assert(not missing, missing)
    payload = {
        "status": "blocked",
        "not_final_baseline": True,
        "topology": "same-host",
        "domain": 87,
        "environment": collect(SCRIPT_DIR.parents[1], extra={"status": "blocked"}),
        "cases": [row],
    }
    text = render_summary(payload)
    _assert("## `rmw_fastrtps_cpp`" in text, text)
    print("  ok csv schema / summary sections")


def test_write_reports_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        payload = {
            "status": "ok",
            "not_final_baseline": True,
            "topology": "same-host",
            "domain": 87,
            "environment": {
                "status": "ok",
                "host_class": "cursor-cloud-vm",
                "ros_distro": "jazzy",
                "cpu": "test-cpu",
                "nproc": 2,
                "kernel": "6.12",
                "disclaimer": "selftest",
                "packages": {"rmw_fastrtps_cpp": "0.0-test"},
            },
            "cases": [
                {
                    "status": "ok",
                    "not_final_baseline": True,
                    "host_class": "cursor-cloud-vm",
                    "ros_distro": "jazzy",
                    "rmw": "rmw_fastrtps_cpp",
                    "rmw_version": "0.0-test",
                    "qos": "reliable",
                    "mode": "oneway",
                    "topology": "same-host",
                    "size_bytes": 1024,
                    "hz_offered": 20,
                    "duration_s": 2,
                    "warmup_s": 0.5,
                    "repeat": 1,
                    "sent": 40,
                    "received": 40,
                    "loss_ratio": 0.0,
                    "throughput_msg_s": 20.0,
                    "throughput_mbyte_s": 0.02,
                    "p50_us": 100.0,
                    "p90_us": 120.0,
                    "p99_us": 150.0,
                    "max_us": 200.0,
                    "min_us": 80.0,
                    "mean_us": 110.0,
                    "pub_cpu_percent": 5.0,
                    "sub_cpu_percent": 4.0,
                    "pub_rss_kb_avg": 10000,
                    "pub_rss_kb_peak": 11000,
                    "sub_rss_kb_avg": 9000,
                    "sub_rss_kb_peak": 9500,
                    "pub_pid": 1,
                    "sub_pid": 2,
                    "blocked_reason": "",
                }
            ],
        }
        write_reports(out, payload)
        summary = (out / "summary.md").read_text(encoding="utf-8")
        _assert("p50" in summary and "100" in summary, summary)
        _assert("not_final_baseline" in summary, summary)
        print("  ok write_reports roundtrip")


def main() -> int:
    try:
        test_percentiles()
        test_wire()
        test_hz()
        test_specs_and_cli()
        test_blocked_reports()
        test_env_and_rmw_probe()
        test_merge_row_schema()
        test_write_reports_roundtrip()
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
