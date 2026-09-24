#!/usr/bin/env python3
"""Latency probe listener: measures one-way latency over DDS.

Both containers share the Colima VM kernel, so CLOCK_MONOTONIC is consistent
across containers; one-way latency = recv_ns - send_ns is meaningful.
"""
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def percentile(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    if lo == hi:
        return float(sorted_vals[lo])
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


class Listener(Node):
    def __init__(self, need, warmup):
        super().__init__('lat_listener')
        self.need = need
        self.warmup = warmup
        self.samples = []
        self.max_seq = -1
        self.create_subscription(String, 'latprobe', self.cb, 10)
        self.t0 = time.monotonic()

    def cb(self, msg):
        recv_ns = time.monotonic_ns()
        try:
            seq_s, send_s = msg.data.split(',', 1)
            seq = int(seq_s)
            send_ns = int(send_s)
        except (ValueError, AttributeError):
            return
        if seq > self.max_seq:
            self.max_seq = seq
        if seq < self.warmup:
            return
        self.samples.append((seq, recv_ns - send_ns))

    def enough(self):
        return len(self.samples) >= self.need


def main():
    need = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    warmup = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    timeout_s = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0

    rclpy.init()
    node = Listener(need, warmup)
    deadline = time.monotonic() + timeout_s
    last = time.monotonic()
    try:
        while not node.enough() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            now = time.monotonic()
            if now - last >= 5.0:
                print('progress collected=%d max_seq=%d'
                      % (len(node.samples), node.max_seq), flush=True)
                last = now
    finally:
        us = sorted(lat / 1000.0 for _, lat in node.samples)
        n = len(us)
        print('=== latency report (us) ===')
        print('collected: %d (need %d, warmup %d, max_seq %d)'
              % (n, need, warmup, node.max_seq))
        # Expected measured seqs are [warmup .. warmup+need-1]; loss vs max seen.
        expected_span = max(0, node.max_seq - warmup + 1)
        loss = expected_span - n
        print('missing/dup delta: %d (expected_span %d)' % (loss, expected_span))
        if n:
            mean = sum(us) / n
            var = sum((v - mean) ** 2 for v in us) / n
            print('min: %.1f' % us[0])
            print('mean: %.1f' % mean)
            print('p50: %.1f' % percentile(us, 0.50))
            print('p90: %.1f' % percentile(us, 0.90))
            print('p95: %.1f' % percentile(us, 0.95))
            print('p99: %.1f' % percentile(us, 0.99))
            print('max: %.1f' % us[-1])
            print('jitter p99-p50: %.1f us'
                  % (percentile(us, 0.99) - percentile(us, 0.50)))
            print('stdev: %.1f us' % var ** 0.5)
        print('SUMMARY collected=%d loss=%d '
              'p50=%.1f p90=%.1f p95=%.1f p99=%.1f max=%.1f'
              % (n, loss,
                 percentile(us, 0.50), percentile(us, 0.90),
                 percentile(us, 0.95), percentile(us, 0.99),
                 us[-1] if us else 0.0))
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
