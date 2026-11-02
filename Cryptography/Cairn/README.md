# Cairn

**Category:** computational cryptography / isogeny walk  
**Recovered:** 1 November 2026, Asia/Samarkand  
**Flag:** `hiCTF{w41k_th3_sup3rs1n9u14r_l46yr1ntH}`  
**Evidence:** AES-GCM authentication succeeded using the completed walk's final state. The final-state decryption was repeated on 1 November.

## Challenge

The archive contains an exact specification and `challenge.json`. Its historical SHA-256 was:

```text
9f8f036fbb3a25341dc58602c9d8c340c786f1ba882095c45bac69b785796f21
```

The task defines a deterministic walk through roots of modular polynomials in:

```text
GF(p²) = GF(p)[i] / (i² + 1)
p = 115792089237316195423570985008687907853269984665640564039457584007908834671663
j0 = (1728, 0)
T = 1048576
L = [2, 3, 5, 7]
```

The challenge's integers require exact arbitrary-precision parsing. Python's JSON integer handling preserves them.

## 1. Implement the serialization exactly

For `j = a + b*i`, serialize both canonical coefficients as **32-byte little-endian** integers:

```python
def ser(j):
    return j[0].to_bytes(32, "little") + j[1].to_bytes(32, "little")
```

The step index uses eight-byte **big-endian** encoding. Mixing those conventions changes every later step.

## 2. Compute each transition

For step `i`:

1. Calculate `h = SHA256(ser(j) + i.to_bytes(8, 'big') + salt)`.
2. Select `ell = L[h[0] % 4]`.
3. Substitute `X = j` into the supplied `Phi_ell(X, Y)`.
4. Divide by the GCD with its derivative to remove repeated factors.
5. Find all distinct roots in `GF(p²)`.
6. Convert roots into coefficient pairs and sort numerically by `(a, b)`.
7. Set `j = roots[h[1] % len(roots)]`.

Sorting is part of the cryptographic algorithm. A library's arbitrary root order is not acceptable.

The Python reference implementation uses python-flint. It asserts that every recovered root evaluates to zero and that the number of distinct roots equals the squarefree polynomial's degree.

## 3. Complete the million-step walk

The original solve began with Python/FLINT, then used a native C++ implementation with GMP and OpenSSL to finish the expensive computation. Checkpoints recorded both the completed step count and the exact pair representing `j`.

The completed checkpoint is:

```text
step = 1048576
a = 2951744835154356679408485058539998725114852725772335444978399055687248892073
b = 76297261829986891261504719508868871098352200233656976244600190934732692176052
```

No shortcut or recovered private key was needed: the published deterministic process was evaluated to completion.

## 4. Derive and verify the flag

The encryption key is:

```text
SHA256(ser(j_T) || "IsogenyLabyrinth")
```

The label is ASCII without a trailing newline. Decrypt the supplied ciphertext with AES-256-GCM, empty additional authenticated data, and its provided nonce and tag.

This short check reproduces final-state decryption. It verifies the saved endpoint; it does not rerun the whole walk:

```python
import base64
import hashlib
import json
from pathlib import Path
from Crypto.Cipher import AES

c = json.loads(Path("challenge.json").read_text())
step, a, b = map(int, Path("final-checkpoint.txt").read_text().split())
assert step == c["T"]
assert 0 <= a < c["p"] and 0 <= b < c["p"]
encoded = a.to_bytes(32, "little") + b.to_bytes(32, "little")
key = hashlib.sha256(encoded + b"IsogenyLabyrinth").digest()
cipher = AES.new(key, AES.MODE_GCM, nonce=base64.b64decode(c["nonce_b64"]))
flag = cipher.decrypt_and_verify(
    base64.b64decode(c["ciphertext_b64"]),
    base64.b64decode(c["tag_b64"]),
)
assert flag == b"hiCTF{w41k_th3_sup3rs1n9u14r_l46yr1ntH}"
print(flag.decode())
```

The two input files are in `./`. The original specification is preserved there too. `solve.py` is the Python reference solver; `fast.cpp` preserves the native implementation.

To rerun the Python walk, place the reference script beside a `cairn/challenge files/challenge.json` directory tree and run `python3 solve.py --fast` with python-flint and PyCryptodome installed. Use a fresh directory without stale `checkpoint-fast.json` files. Expect substantial runtime.

**Source chat:** “Find the cairn.zip flag”, `01a19590-1e94-7c12-b7ae-e720a78b2413`. No contest submission was recorded.
