#!/usr/bin/env python3
"""Echoes of a Forgotten Canvas - full multilayer chain.
usage: python3 solve.py chall.png outdir      (needs Pillow, numpy, steghide)

 1. PNG IHDR height 4000 -> real 4500 (CRC + IDAT size prove it); hidden strip's alpha = flag part 1
 2. ZipCrypto zip appended after IEND, zip key 'dreamcatcher' (found with zip2john + john/rockyou)
 3. carrier.jpg = poem "WILDER ECHOES"; steghide key 'profound' (found with stegseek/rockyou) -> finall.jpg
 4. finall.jpg SOF0 height shrunk (libjpeg: '3379 extraneous bytes before EOI'); enlarge -> flag part 2
"""
import io, os, struct, subprocess, sys, zipfile, zlib
import numpy as np
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
d = bytearray(open(src, "rb").read())

# ---- layer 1: PNG height trick -------------------------------------------------
w, h = struct.unpack(">II", d[16:24])
stored_crc = struct.unpack(">I", d[29:33])[0]
print(f"IHDR says {w}x{h}, stored CRC {stored_crc:08x}, crc of header as-is {zlib.crc32(d[12:29]) & 0xffffffff:08x}")
for newh in range(h, h + 2000):
    ihdr = b"IHDR" + struct.pack(">II", w, newh) + d[24:29]
    if zlib.crc32(ihdr) & 0xffffffff == stored_crc:
        print("CRC matches height", newh); break
d[20:24] = struct.pack(">I", newh)
iend = d.find(b"IEND") + 8
open(f"{out}/chall_fixed_height.png", "wb").write(d[:iend])
a = np.array(Image.open(io.BytesIO(bytes(d[:iend]))))
alpha = a[h:, :, 3]
ys, xs = np.nonzero(alpha)
crop = alpha[ys.min() - 5:ys.max() + 6, xs.min() - 5:xs.max() + 6]
Image.fromarray(crop).resize((crop.shape[1] * 3, crop.shape[0] * 3)).save(f"{out}/flag_part1_alpha.png")
print("part 1 is drawn in the alpha channel of the hidden strip -> flag_part1_alpha.png")

# ---- layer 2: appended ZipCrypto archive ----------------------------------------
trail = bytes(d[iend:])
open(f"{out}/appended.zip", "wb").write(trail)
z = zipfile.ZipFile(io.BytesIO(trail))
print("appended zip members:", z.namelist())
z.extractall(out, pwd=b"dreamcatcher")

# ---- layer 3: steghide in carrier.jpg -------------------------------------------
carrier = os.path.join(out, "carrier.jpg")
subprocess.run(["steghide", "extract", "-sf", carrier, "-p", "profound", "-xf", f"{out}/finall.jpg", "-f"], check=True)

# ---- layer 4: JPEG SOF height trick ---------------------------------------------
j = bytearray(open(f"{out}/finall.jpg", "rb").read())
i = j.find(b"\xff\xc0")
jh, jw = struct.unpack(">HH", j[i + 5:i + 9])
print(f"finall.jpg SOF0 says {jw}x{jh}")
j[i + 5:i + 7] = struct.pack(">H", 1300)
open(f"{out}/finall_tall.jpg", "wb").write(j)
im = Image.open(f"{out}/finall_tall.jpg"); im.load()
im = im.convert("RGB")
# keep only the rows that actually decoded (rest is grey fill)
arr = np.array(im); rows = [r for r in range(arr.shape[0]) if arr[r].std() > 1]
im.crop((0, 0, jw, rows[-1] + 1)).save(f"{out}/finall_revealed.png")
im.crop((0, jh - 10, jw, rows[-1] + 1)).save(f"{out}/flag_part2_hidden_rows.png")
print(f"real height ~{rows[-1] + 1}; hidden rows -> flag_part2_hidden_rows.png")
print("flag: hiCTF{mu1t!14y3r3d_ + st3g0o_ju5t_l0v333}")
