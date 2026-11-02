#!/usr/bin/env python3
# Operation Chimera solver: pcap -> decrypted ELF -> flag
# usage: python3 solve_chimera.py operation_chimera.pcap
import hashlib, hmac, subprocess, sys

PCAP = sys.argv[1]
# ServerHello.random from the fake TLS handshake with delta.corp.internal (10.142.18.250)
KEY = bytes.fromhex("3c891e45aad02f81b7649e125088da7c913247f008c3296b8a714e5d2319bb04")

def crc16_ccitt_false(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

# 1. pull the UDP payloads of the tunnel queries
out = subprocess.run(["tshark", "-r", PCAP, "-Y", 'dns.qry.name contains "telemetry"',
                      "-T", "fields", "-e", "udp.payload"], capture_output=True, text=True, check=True).stdout

chunks = {}
for line in out.split():
    pkt = bytes.fromhex(line)
    i = pkt.find(b"CHIM")                      # EDNS0 option 0xfde9 data starts with "CHIM"
    optlen = int.from_bytes(pkt[i-2:i], "big")
    body = pkt[i+4:i+optlen]                   # [nonce 2][crc16 2][enc(seq 2 + data)]
    nonce, crc, ct = body[:2], int.from_bytes(body[2:4], "big"), body[4:]
    ks = b"".join(hmac.new(KEY, nonce + c.to_bytes(2, "big"), hashlib.sha256).digest()
                  for c in range(len(ct) // 32 + 1))
    pt = bytes(a ^ b for a, b in zip(ct, ks))
    seq, data = int.from_bytes(pt[:2], "big"), pt[2:]
    assert crc16_ccitt_false(data) == crc, f"CRC mismatch on seq {seq}"
    chunks[seq] = data

elf = b"".join(chunks[k] for k in sorted(chunks))
open("exfil.bin", "wb").write(elf)
print(f"[+] {len(chunks)} chunks, {len(elf)} bytes -> exfil.bin")

# 2. invert the flag checker at 0x1580
sbox, tgt = elf[0x6280:0x6380], elf[0x6240:0x6240 + 43]
inv = {v: i for i, v in enumerate(sbox)}
state, prev, add, flag = 0xA5, 0x5C, 13, bytearray()
for i in range(43):
    state = ((state << 1) ^ 0x1D) & 0xFF if state & 0x80 else (state << 1) & 0xFF
    x = tgt[i] ^ prev
    t = ((x >> 3) | (x << 5)) & 0xFF           # undo rol 3
    flag.append(inv[(t - add) & 0xFF] ^ state)
    prev, add = tgt[i], add + 7
print("[+] flag:", flag.decode())
