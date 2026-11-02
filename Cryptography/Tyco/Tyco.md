# Tyco

**Category:** Cryptography (RSA)  **Flag:** `hiCTF{your_ai_slop_bores_me}`

> 🫠🤖

Files: `tyco.zip` → `chall.py`, `chall.txt`

## The challenge

```python
N = getPrime(256) * getPrime(256)
e = getPrime(16)                 # e = 56263
r = bytes_to_long(flag.encode())
d = random.randrange(1, N)
t1 = pow(r, e, N)
t2 = pow(r + d, e, N)
print(N, e, d, t1, t2)
```

The same message is encrypted twice under the same `(N, e)`, once as `r` and once as `r + d`, and the offset `d` is published. This is the textbook **Franklin–Reiter related-message attack**.

## Attack

`r` is a common root of two polynomials over Z/NZ:

```
f1(x) = x^e − t1
f2(x) = (x + d)^e − t2
```

So `gcd(f1, f2) = x − r`, which hands over the plaintext without factoring N.

### The catch: e = 56263
Both polynomials have degree ≈ 56k. A plain Euclidean GCD costs O(e²) big-integer polynomial operations, which is far too slow. You need a **half-GCD** (O(n log² n)).

- `python-flint` has a fast half-GCD, but it refuses to run when the modulus is composite (it needs a field).
- Its polynomial **multiplication and divmod do work modulo a composite N**, though. Leading coefficients never turn out non-invertible in practice, because that would reveal a factor of N.
- So `solve/solve.py` implements the half-GCD recursion (`hgcd`) itself on top of flint's `fmpz_mod_poly` arithmetic. First it reduces `f2 mod f1`, then it runs the GCD. The degree halves each round (56263 → 28131 → … → 1), and the whole run takes about 23 seconds.

At the end, the GCD is linear (`x + c0`), so `r = −c0 mod N`. The script checks `r^e ≡ t1` and `(r+d)^e ≡ t2`, then prints `long_to_bytes(r)`.

## Run

```
python3 -m venv venv && venv/bin/pip install python-flint
venv/bin/python solve/solve.py artifacts/chall.txt
```

## Files
- `solve/solve.py` is the Franklin–Reiter attack with a custom half-GCD on python-flint
- `artifacts/chall.py`, `artifacts/chall.txt` are the challenge source and output
- `artifacts/solver_output.txt` is the run log (degree sequence, then the flag)
