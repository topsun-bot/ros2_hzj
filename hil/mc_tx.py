#!/usr/bin/env python3
import socket, sys, time
group = '224.1.1.1'; port = 50000
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
for i in range(5):
    s.sendto(b'hello-mcast-%d' % i, (group, port))
    time.sleep(0.3)
print('MULTICAST_TX sent 5 packets to %s:%d' % (group, port))
