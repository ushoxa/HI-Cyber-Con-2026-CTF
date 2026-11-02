import sys, hashlib, subprocess, csv, os

EV = sys.argv[1]  # evidence dir
fw = open(os.path.join(EV, "firmware.elf"), "rb").read()
fl = open(os.path.join(EV, "flash_dump.bin"), "rb").read()

# --- 1. 24-byte device secret at VMA 0x08000ca0 -> file off 0x10ca0
#        (.rodata VMA 0x8000c94 == file off 0x10c94)
secret = fw[0x10ca0:0x10ca0 + 24]
print("secret (24):", secret.hex())

# --- 2. nonce: capture.csv channel 1 payload  (AA 55 LEN CMD <payload> CRC CRC)
ch1 = []
with open(os.path.join(EV, "capture.csv")) as f:
    for row in csv.DictReader(f):
        if row["channel"] == "1":
            ch1.append(int(row["byte"], 16))
assert ch1[0] == 0xAA and ch1[1] == 0x55, ch1[:2]
ln, cmd = ch1[2], ch1[3]
nonce = bytes(ch1[4:4 + ln])
print("SE frame LEN=%#x CMD=%#x" % (ln, cmd))
print("nonce (%d): %s" % (len(nonce), nonce.hex()))

# --- 3. key = SHA256(secret || nonce); AES-128 uses first 16 bytes
digest = hashlib.sha256(secret + nonce).digest()
key = digest[:16]
iv = nonce
print("sha256 full:", digest.hex())
print("aes128 key :", key.hex())
print("iv (nonce) :", iv.hex())

# --- 4. ciphertext: 48 bytes @ flash 0x6A000, per-32-bit-word byte reversal
ct_raw = fl[0x6A000:0x6A000 + 48]
print("ct raw     :", ct_raw.hex())
ct = b"".join(ct_raw[i:i + 4][::-1] for i in range(0, 48, 4))
print("ct swapped :", ct.hex())


def dec(c, key, iv):
    p = subprocess.run(
        ["openssl", "enc", "-aes-128-cbc", "-d", "-nopad",
         "-K", key.hex(), "-iv", iv.hex()],
        input=c, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr.decode())
    return p.stdout


for label, c in [("SWAPPED", ct), ("RAW", ct_raw)]:
    pt = dec(c, key, iv)
    print("\n== decrypt (%s ciphertext) ==" % label)
    print("hex :", pt.hex())
    print("repr:", pt)
    if pt:
        pad = pt[-1]
        if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad:
            print("PKCS7 ok, pad=%d -> FLAG: %s" % (pad, pt[:-pad].decode("latin1")))

