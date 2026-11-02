#!/usr/bin/env python3
"""Signal Lock - recover the token accepted by signal_lock:verify/1 and decrypt the flag offline.
usage: python3 solve.py signal_lock.beam
 - .beam is gzip-compressed -> FOR1/BEAM IFF container
 - verify(<<N:64>>) accepts iff transform(N) == 12675316763487955908
 - transform = xor C1 -> *C2 mod 2^64 -> rotl 29 -> +C3 mod 2^64 (all bijections -> invert)
 - unlock(N) = 48-byte literal XOR sha256-based keystream
"""
import gzip, hashlib, struct, sys, zlib, itertools

data = open(sys.argv[1], "rb").read()
if data[:2] == b"\x1f\x8b":
    data = gzip.decompress(data)
assert data[:4] == b"FOR1" and data[8:12] == b"BEAM"
chunks, off = {}, 12
while off < len(data):
    name, size = data[off:off + 4], struct.unpack(">I", data[off + 4:off + 8])[0]
    chunks[name] = data[off + 8:off + 8 + size]
    off = (off + 8 + size + 3) & ~3
print("chunks:", [c.decode() for c in chunks])

# atoms
b = chunks[b"AtU8"]; n = struct.unpack(">I", b[:4])[0]; p = 4; atoms = []
for _ in range(n):
    ln = b[p]; atoms.append(b[p + 1:p + 1 + ln].decode()); p += 1 + ln
print("atoms:", atoms)

# literal table (zlib) -> 48-byte cipher binary
raw = zlib.decompress(chunks[b"LitT"][4:]); n = struct.unpack(">I", raw[:4])[0]; p = 4; lits = []
for _ in range(n):
    sz = struct.unpack(">I", raw[p:p + 4])[0]; lits.append(raw[p + 4:p + 4 + sz]); p += 4 + sz
cipher = None
for t in lits:
    if t[:2] == b"\x83m":                       # external term format: BINARY_EXT
        L = struct.unpack(">I", t[2:6])[0]; cipher = t[6:6 + L]
print("cipher literal (%d bytes): %s" % (len(cipher), cipher.hex()))

# ---- invert transform -------------------------------------------------------
M = 1 << 64
C1, C2, C3 = 11936128517019425370, 11400714819323198485, 81985529216486895
T = 12675316763487955908
rotl = lambda x, r: ((x << r) | (x >> (64 - r))) & (M - 1)
def transform(x):
    return (rotl((x ^ C1) * C2 % M, 29) + C3) % M
N = (rotl((T - C3) % M, 64 - 29) * pow(C2, -1, M) % M) ^ C1
token = N.to_bytes(8, "big")
assert transform(N) == T
print("N = %#018x  token = %r" % (N, token))

# ---- unlock: keystream built from sha256 blocks seeded by the token -------------------
def ks_variants(seed):
    for ctr_fmt in (lambda i: bytes([i]), lambda i: i.to_bytes(4, "big"), lambda i: i.to_bytes(8, "big"),
                    lambda i: str(i).encode()):
        for start in (0, 1):
            for order in ("seed|ctr", "ctr|seed"):
                ks = b""
                for i in itertools.count(start):
                    c = ctr_fmt(i)
                    ks += hashlib.sha256(seed + c if order == "seed|ctr" else c + seed).digest()
                    if len(ks) >= len(cipher): break
                yield ks
    h = hashlib.sha256(seed).digest(); ks = h                 # hash chain
    while len(ks) < len(cipher):
        h = hashlib.sha256(h).digest(); ks += h
    yield ks
for seed in (token, str(N).encode()):
    for ks in ks_variants(seed):
        pt = bytes(a ^ b for a, b in zip(cipher, ks))
        if pt.startswith(b"hiCTF{"):
            print("flag:", pt.decode()); sys.exit()
print("keystream variant not matched offline - run in Erlang: signal_lock:verify(<<\"%s\">>)." % token.decode())
