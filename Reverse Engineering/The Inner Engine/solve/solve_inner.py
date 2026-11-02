import sys, hashlib, struct

ELF = sys.argv[1]
data = open(ELF, "rb").read()

# 72-byte sealed blob at VMA 0x4062c0 -> file off 0x62c0
blob = data[0x62c0:0x62c0 + 72]
seal = blob[0:32]        # == SHA256(flag)
ct = blob[32:72]         # flag XOR keystream (40 bytes)
print("seal (SHA256 of flag):", seal.hex())
print("ct  :", ct.hex())


def sha256(b):
    return hashlib.sha256(b).digest()


def mgf1(seed, n):
    out = b""
    c = 0
    while len(out) < n:
        out += sha256(seed + struct.pack(">I", c))
        c += 1
    return out[:n]


def flag_for_key(key24):
    # key24: bytes of length 24
    input32 = sha256(key24)
    ks = mgf1(input32, 40)
    return bytes(ct[i] ^ ks[i] for i in range(40))


DOM = range(0x20, 0x7f)  # printable ASCII for free params & derived
M = 0xff

sols = []
# free: k16 -> k17..k21 ; k9 -> k10,k11 ; k12 -> k13,k14,k15 ; k0 -> k23,k22
for k16 in DOM:
    k17 = (0x94 - k16) & M
    k18 = (0x9a - k17) & M
    k19 = (0x9b - k18) & M
    k20 = (0x99 - k19) & M
    k21 = (0x9a - k20) & M
    if not all(0x20 <= x <= 0x7e for x in (k17, k18, k19, k20, k21)):
        continue
    for k9 in DOM:
        k10 = (0xa4 - k9) & M
        k11 = (0xbe - k10) & M
        if not all(0x20 <= x <= 0x7e for x in (k10, k11)):
            continue
        # C16: (k11*k19)&0xff == 0x53
        if (k11 * k19) & M != 0x53:
            continue
        for k12 in DOM:
            k13 = (0x9f - k12) & M
            k14 = (0x99 - k13) & M
            k15 = (0x94 - k14) & M
            if not all(0x20 <= x <= 0x7e for x in (k13, k14, k15)):
                continue
            # C18 -> k4
            k4 = 0x41 ^ k12 ^ k20
            if not (0x20 <= k4 <= 0x7e):
                continue
            # C14: k3*k15 == 0x43 ; enumerate k3 candidates
            k3_cands = [x for x in DOM if (x * k15) & M == 0x43]
            if not k3_cands:
                continue
            # C19 -> k2
            k2 = 0x36 ^ k10 ^ k18
            if not (0x20 <= k2 <= 0x7e):
                continue
            # C15: k7*k21 == 0xec
            k7_cands = [x for x in DOM if (x * k21) & M == 0xec]
            if not k7_cands:
                continue
            for k0 in DOM:
                k23 = (0xb1 - k0) & M
                k22 = (0x96 - k23) & M
                if not all(0x20 <= x <= 0x7e for x in (k23, k22)):
                    continue
                # C17 -> k8
                k8 = 0x21 ^ k0 ^ k16
                if not (0x20 <= k8 <= 0x7e):
                    continue
                # C20: sum
                if (k0 + k4 + k8 + k12 + k16 + k20) & M != 0x9a:
                    continue
                for k3 in k3_cands:
                    # C23 -> k6
                    k6 = 0x77 ^ k3 ^ k11 ^ k14 ^ k19 ^ k22
                    if not (0x20 <= k6 <= 0x7e):
                        continue
                    # C1 -> k5
                    k5 = k6 ^ 0x54
                    if not (0x20 <= k5 <= 0x7e):
                        continue
                    # C21 -> k1
                    k1 = 0x56 ^ k5 ^ k9 ^ k13 ^ k17 ^ k21
                    if not (0x20 <= k1 <= 0x7e):
                        continue
                    for k7 in k7_cands:
                        # C22: sum
                        if (k2 + k7 + k10 + k15 + k18 + k23) & M != 0x01:
                            continue
                        key = bytes([k0, k1, k2, k3, k4, k5, k6, k7, k9 if False else 0,  # placeholder
                                     ])
                        # build full key properly (note: index 8 is k8, index 9 is k9 ...)
                        kk = [k0, k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11,
                              k12, k13, k14, k15, k16, k17, k18, k19, k20, k21, k22, k23]
                        key = bytes(kk)
                        sols.append(key)

print("VM-constraint solutions (printable):", len(sols))
# Now apply the definitive oracle: SHA256(flag) == seal
for key in sols:
    fl = flag_for_key(key)
    if sha256(fl) == seal:
        print("\n*** FOUND KEY ***")
        print("key  :", key.decode('latin1'))
        print("flag :", fl.decode('latin1', 'replace'))
        print("verify SHA256(flag)==seal:", sha256(fl) == seal)
        break
else:
    print("no key passed the oracle among", len(sols), "candidates")
    # show a few candidates for debugging
    for key in sols[:10]:
        print("cand:", key.decode('latin1', 'replace'))

