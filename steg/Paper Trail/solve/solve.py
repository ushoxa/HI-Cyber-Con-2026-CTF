#!/usr/bin/env python3
"""Paper Trail - data hidden in TJ kerning numbers of invisible (3 Tr) text streams,
AES-128-CBC with key=/ID[0], IV=/ID[1] from the PDF trailer.
usage: python3 solve.py chall.pdf outdir     (needs mutool + python 'cryptography')"""
import re, subprocess, sys, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
pdf, out = sys.argv[1], sys.argv[2]
clean = os.path.join(out, "chall_decompressed.pdf")
subprocess.run(["mutool", "clean", "-d", pdf, clean], check=True)
raw = open(clean, "rb").read()

ids = re.search(rb"/ID\s*\[\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>", raw)
key, iv = bytes.fromhex(ids.group(1).decode()), bytes.fromhex(ids.group(2).decode())
print("trailer /ID[0] (key):", key.hex()); print("trailer /ID[1] (iv) :", iv.hex())

rows = []
for m in re.finditer(rb"(\d+) 0 obj\s*<<[^>]*?/Length \d+[^>]*?>>\s*stream\r?\n(.*?)endstream", raw, re.S):
    body = m.group(2)
    if b"3 Tr" not in body: continue                    # invisible-text streams only
    arrs = [list(map(int, re.findall(rb"-?\d+", a))) for a in re.findall(rb"\[([^\]]*)\]\s*TJ", body)]
    open(os.path.join(out, f"hidden_stream_obj{m.group(1).decode()}.txt"), "wb").write(body)
    longest = max(arrs, key=len)
    print(f"obj {m.group(1).decode()}: {len(arrs)} TJ rows, longest={len(longest)} values")
    if len(longest) > 2 * sorted(map(len, arrs))[-2] or len(arrs) == 1:   # one row much longer than the rest
        rows.append(longest)
payload = bytes(sum((r[2:] for r in rows if all(0 <= v < 256 for v in r[2:])), []))
print("payload bytes:", len(payload))
pt = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor().update(payload[:len(payload)//16*16])
print("plaintext:", pt)
assert pt[:4] == b"CTF1"
n = pt[5]; print("flag:", pt[6:6+n].decode())
