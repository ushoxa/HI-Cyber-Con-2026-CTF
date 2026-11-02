import sys, wave
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
w = wave.open(sys.argv[1]); n = w.getnframes()
d = np.frombuffer(w.readframes(n), dtype='<i2').reshape(-1, 2).astype(np.int64)
N, P = 4096, 257
NONCE = bytes.fromhex("99CB9C49E4C83527CE6F89D9")
CT = bytes.fromhex("8A845BA500DE25B749F1FF63CCFF9D2D9FD8D2614E19BCA42CC7E438B31407AE896311C3AADCF9327610478444A09EF6FE3650DF7EBEC3B71FF18CF0EB728DBFA791B7485D767172AE8493A8715210B5")
bits = []
for b in range(585, 643):
    F = np.abs(np.fft.rfft(d[b*N:(b+1)*N, 1].astype(float))); F[:600] = 0
    k = int(F.argmax())
    syn = 0
    for j in range(31):
        if d[b*N + ((j+1)*k) % N, 0] & 1: syn ^= (j - k) % 31 + 1
    bits += [(syn >> (4-t)) & 1 for t in range(5)]
vals = [int("".join(map(str, bits[i*9:i*9+9])), 2) for i in range(32)]
print("vals", vals, "leftover bits", bits[288:])
ntt = lambda a, w: [sum(a[j]*pow(w, i*j, P) for j in range(32)) % P for i in range(32)]
roots = [r for r in range(2, P) if pow(r, 32, P) == 1 and pow(r, 16, P) != 1]
inv32 = pow(32, P-2, P)
for r in roots:
    for name, v in (("inv", [x*inv32 % P for x in ntt(vals, pow(r, P-2, P))]), ("fwd", ntt(vals, r)), ("inv_noscale", ntt(vals, pow(r, P-2, P)))):
        if max(v) > 255: continue
        try:
            pt = AESGCM(bytes(v)).decrypt(NONCE, CT, None)
            print("root", r, name, "key", bytes(v).hex()); print(pt); sys.exit()
        except Exception: pass
print("no tag match")
