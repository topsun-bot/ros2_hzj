#!/usr/bin/env python3
"""Latency probe talker: publishes 'seq,monotonic_ns' on topic 'latprobe'."""
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Talker(Node):
    def __init__(self):
        super().__init__('lat_talker')
        self.pub = self.create_publisher(String, 'latprobe', 10)

    def run(self, total, rate_hz):
        period = 1.0 / rate_hz
        # Give the listener time to discover and subscribe.
        time.sleep(3.0)
        next_t = time.monotonic()
        for seq in range(total):
            msg = String()
            msg.data = '%d,%d' % (seq, time.monotonic_ns())
            self.pub.publish(msg)
            next_t += period
            sleep_for = next_t - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
        time.sleep(1.0)  # flush the last samples


def main():
    total = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    rate_hz = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
    rclpy.init()
    node = Talker()
    try:
        node.run(total, rate_hz)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
