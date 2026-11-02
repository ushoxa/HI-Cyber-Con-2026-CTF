import base64
import hashlib
import json
import random
import sys
import time
from functools import lru_cache
from pathlib import Path

from Crypto.Cipher import AES
from flint import fq_default_ctx, fq_default_poly_ctx, fmpz_mod_poly_ctx

HERE = Path(__file__).parent
C = json.loads((HERE / 'cairn/challenge files/challenge.json').read_text())
P = C['p']
F = fq_default_ctx(modulus=fmpz_mod_poly_ctx(P)([1, 0, 1]))
R = fq_default_poly_ctx(F)
X = R.gen()
EXP = (P * P - 1) // 2
SALT = bytes.fromhex(C['salt_hex'])


def pair(z):
    a = list(map(int, z.to_list()))
    return tuple(a + [0] * (2 - len(a)))


def ser(z):
    return b''.join(x.to_bytes(32, 'little') for x in z)


def split(f):
    n = f.degree()
    if n == 1:
        return [-f[0] / f[1]]
    if n == 2:
        b, c = f[1] / f[2], f[0] / f[2]
        d = (b * b - 4 * c).sqrt()
        return [(-b + d) / 2, (-b - d) / 2]
    while True:
        a = F([random.randrange(P), random.randrange(P)])
        g = f.gcd((X + a).pow_mod(EXP, f) - 1)
        if 0 < g.degree() < n:
            return split(g) + split(f // g)


@lru_cache(maxsize=8192)
def roots(j, ell, fast=False):
    z = F(list(j))
    powers = [z ** k for k in range(ell + 2)]
    co = [F(0) for _ in range(ell + 2)]
    for x, y, k in C['phi'][str(ell)]:
        co[y] += powers[x] * k
    f = R(co)
    if fast:
        f = f // f.gcd(f.derivative())
        rr = split(f)
    else:
        rr = f.roots(multiplicities=False)
    result = tuple(sorted(set(map(pair, rr))))
    assert len(result) == (f // f.gcd(f.derivative())).degree()
    assert all(f(F(list(r))) == 0 for r in result)
    return result


def decrypt(j):
    key = hashlib.sha256(ser(j) + b'IsogenyLabyrinth').digest()
    aes = AES.new(key, AES.MODE_GCM, nonce=base64.b64decode(C['nonce_b64']))
    return aes.decrypt_and_verify(base64.b64decode(C['ciphertext_b64']), base64.b64decode(C['tag_b64']))


if __name__ == '__main__':
    fast = '--fast' in sys.argv
    limit = next((int(a) for a in sys.argv[1:] if a.isdigit()), C['T'])
    checkpoint = HERE / ('checkpoint-fast.json' if fast else 'checkpoint.json')
    j, start = tuple(C['j0']), 0
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        j, start = tuple(state['j']), state['step']
    t = time.monotonic()
    for i in range(start, limit):
        h = hashlib.sha256(ser(j) + i.to_bytes(8, 'big') + SALT).digest()
        rr = roots(j, C['L'][h[0] % 4], fast)
        j = rr[h[1] % len(rr)]
        if (i + 1) % 1000 == 0 or i + 1 == limit:
            state = {'step': i + 1, 'j': j}
            temporary = checkpoint.with_suffix('.tmp')
            temporary.write_text(json.dumps(state))
            temporary.replace(checkpoint)
            print(json.dumps({**state, 'seconds': round(time.monotonic() - t, 2), 'cache': str(roots.cache_info())}), flush=True)
    if limit == C['T']:
        print(decrypt(j).decode(), flush=True)
