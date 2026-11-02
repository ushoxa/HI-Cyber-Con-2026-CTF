#!/usr/bin/env python3
"""Memory Liar - psscan-style carve of the fake EPROCESS records, detect the DKOM-unlinked
process, then decode its ROOT payload.   usage: python3 solve.py memory.raw"""
import sys, struct, re
d = open(sys.argv[1], 'rb').read()
KBASE = 0x80000000                       # VA = 0x80000000 + physical offset in this synthetic dump
recs = []
for m in re.finditer(rb"[a-zA-Z0-9_]+\.exe\0", d):
    base = m.start() - 0x174             # image name lives at +0x174 in each record
    if base < 0 or base % 0x1000: continue
    pid = struct.unpack_from("<I", d, base + 0xbc)[0]
    flink, blink = struct.unpack_from("<II", d, base + 0xc0)
    recs.append((base, m.group()[:-1].decode(), pid, flink, blink))
print(f"{'offset':>9} {'name':14} {'pid':>6} {'Flink':>10} {'Blink':>10}  note")
for base, name, pid, fl, bl in recs:
    me = KBASE + base + 0xc0
    note = "UNLINKED (Flink==Blink==self -> DKOM)" if fl == bl == me else ""
    print(f"{base:#9x} {name:14} {pid:6d} {fl:#10x} {bl:#10x}  {note}")
# payload: "ROOT" | u32 pid | u32 xor key | u32 len | data
o = d.find(b"ROOT")
pid, key, ln = struct.unpack_from("<III", d, o + 4)
blob = d[o + 16:o + 16 + ln]
print(f"\nROOT blob @ {o:#x}: pid={pid} key={key:#x} len={ln}")
print("decoded:", bytes(b ^ key for b in blob).decode())
for s in (b"darkshadow", b"OP_SHADOW", b"f4k3_d3c0y"):
    i = d.find(s); j = d.rfind(b"\0", 0, i) + 1
    print(f"context @ {j:#x}:", d[j:d.find(b'\0', i)].decode())
