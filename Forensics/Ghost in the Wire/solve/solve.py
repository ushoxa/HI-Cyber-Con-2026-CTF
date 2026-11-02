#!/usr/bin/env python3
"""Ghost in the Wire - rebuild the ICMP covert channel.
usage: python3 solve.py ghost_traffic.pcap"""
import sys
from scapy.all import rdpcap, IP, ICMP, Raw

pkts = rdpcap(sys.argv[1])
streams = {}
for p in pkts:
    if IP in p and ICMP in p and p[ICMP].type == 8:          # echo requests only
        key = (p[IP].src, p[IP].dst)
        payload = bytes(p[Raw].load) if Raw in p else b""
        streams.setdefault(key, []).append((p[ICMP].seq, p[ICMP].id, payload))

for (src, dst), lst in streams.items():
    print(f"{src} -> {dst}: {len(lst)} packets, ids={sorted({i for _, i, _ in lst})}")
    for seq, _, pl in sorted(lst)[:5]:
        print(f"   seq={seq} payload={pl[:40]!r}")

# the covert stream is the one carrying exactly 1 byte per packet
for key, lst in streams.items():
    if all(len(pl) == 1 for _, _, pl in lst):
        msg = b"".join(pl for _, _, pl in sorted(lst)).decode()
        print("\nCovert stream", key, "->", msg)
