#!/usr/bin/env python3
import socket, struct, sys
group = '224.1.1.1'; port = 50000
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', port))
mreq = struct.pack('4sl', socket.inet_aton(group), socket.INADDR_ANY)
s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
s.settimeout(20)
try:
    data, addr = s.recvfrom(1024)
    print('MULTICAST_RX got %r from %s' % (data, addr))
except socket.timeout:
    print('MULTICAST_RX timeout: no multicast received')
