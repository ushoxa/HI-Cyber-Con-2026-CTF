#!/usr/bin/env python3
"""Broken Signals - restore the PNG magic and validate every chunk.
usage: python3 repair.py broken_signal.dat fixed.png"""
import sys, struct, zlib
d = bytearray(open(sys.argv[1], 'rb').read())
print("original header:", d[:8].hex(" "))
d[0:4] = b"\x89PNG"                         # first 4 bytes of the signature were zeroed
assert d[:8] == b"\x89PNG\r\n\x1a\n"
o, idat = 8, b""
while o < len(d):
    ln, typ = struct.unpack(">I4s", d[o:o+8])
    data = d[o+8:o+8+ln]; crc = struct.unpack(">I", d[o+8+ln:o+12+ln])[0]
    ok = zlib.crc32(typ + data) & 0xffffffff == crc
    print(f"{typ.decode():4s} len={ln:6d} crc_ok={ok}")
    if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", data[:10]); print(f"     {w}x{h} bitdepth={bd} colortype={ct}")
    if typ == b"tEXt": print("     ", bytes(data).replace(b"\0", b" = ").decode(errors="replace"))
    if typ == b"IDAT": idat += data
    o += 12 + ln
    if typ == b"IEND": break
raw = zlib.decompress(idat)
print("decompressed IDAT:", len(raw), "expected:", h * (1 + w * 8))  # RGBA16 = 8 bytes/pixel + filter byte
open(sys.argv[2], "wb").write(d)
print("written", sys.argv[2])
