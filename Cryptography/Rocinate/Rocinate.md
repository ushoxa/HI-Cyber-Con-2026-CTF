# Rocinate

**Category:** cryptography / PRNG recovery  
**Recovered:** 31 October 2026, Asia/Samarkand  
**Flag:** `hiCTF{lmaoooo_w0t???y0u_d1d_17_??435p37++}`  
**Evidence:** all 100 products, modular powers, and nonce commitments verified, including a fresh check on 1 November.

## Challenge construction

The supplied Python generator uses `random.randint(1, N)` for the initial nonce, a secret exponent, LCG parameters, and 100 challenge exponents. The modulus is the product of two 1024-bit primes. It publishes `a`, `b`, `N`, `Z`, `C`, and `T`:

```python
r = random.randint(1, N)
e = random.randint(1, N)
a, b = random.randint(1, N), random.randint(1, N)
Rs = [r]
for _ in range(99):
    Rs.append((a * Rs[-1] + b) % N)
Cs = [random.randint(1, N) for _ in range(100)]
Zs = [ri * pow(s, ci, N) for ri, ci in zip(Rs, Cs)]
Ts = [pow(ri, e, N) for ri in Rs]
```

Here `s` is the flag encoded as a big-endian integer. The multiplication constructing `Zs` is not reduced modulo `N`.

The challenge description supplied archive SHA-256 `2f7b41f0cf2d52ca975e05f69bfd99b311c65712dcb4c5b524431c4a1c36e41a`. The original solve used extracted Downloads files, so that ZIP hash was **not verified**. The generator and parsed data used in the solve are included in this collection.

## 1. Turn public exponents into RNG output

Python's default `random` generator is MT19937. The public `C_i` values expose its output, even though the secrets were generated earlier.

For this 2047-bit modulus, a candidate draw consumes 64 32-bit words. The low 63 words of `C_i - 1` expose complete tempered words; the highest word is partial. Rejection sampling means some candidate blocks were consumed without being published.

Undo MT19937's tempering in reverse order:

```text
undo right shift by 18
undo masked left shift by 15, mask 0xefc60000
undo masked left shift by 7, mask 0x9d2c5680
undo right shift by 11
```

The saved script checks `temper(untemper(x)) == x` on test words before using the result.

## 2. Align blocks despite rejected draws

The untempered state words obey:

```text
u[i+624] = u[i+397] XOR twist(u[i], u[i+1])
```

where:

```python
def twist(x, y):
    return (((x & 0x80000000) | (y & 0x7fffffff)) >> 1) ^ (
        (y & 1) * 0x9908b0df
    )
```

The recovery script tests this relationship across published blocks. Matching triples give relative block positions; a graph traversal combines the constraints. Anchoring the second published challenge, `C[1]`, at block zero established a consistent coordinate system.

This step matters: simply concatenating accepted `randint` results would lose the rejected draws and corrupt the reconstruction.

## 3. Propagate the state backwards

The rewind script records known values and bit masks. It repeatedly applies the MT recurrence forwards and backwards, filling full words and partial word information. Any conflicting recovered bits fail an assertion.

In the recovered block numbering:

```text
block -6: initial nonce r
block -5: secret exponent e
block -4: a
block -2: b
block -1: C[0]
block  0: C[1]
```

Reconstruct a candidate integer from the 63 complete words and the top 31 bits, then add one to undo `randint`'s lower bound. Verify the alignment by matching `a`, `b`, and `C[0]` exactly. Finally check `pow(r, e, N) == T[0]`.

## 4. Remove the nonce masks

Regenerate all LCG states from the recovered `r`. Because `Z_i` was an unreduced product, exact division gives:

```text
V_i = Z_i / r_i = s^C_i mod N
```

For every sample, verify `Z_i % r_i == 0` and `pow(r_i, e, N) == T_i`. These checks independently constrain the recovered RNG state.

## 5. Recover the flag with Bézout coefficients

Combine challenge exponents with extended Euclid until their GCD is one. For a coprime pair, coefficients `u` and `v` satisfy:

```text
u*C_i + v*C_j = 1
```

Thus:

```text
V_i^u * V_j^v mod N = s
```

Negative powers use modular inverses. Decode the recovered integer as big-endian bytes and verify `pow(s, C_i, N) == V_i` for every sample.

## Reproduce

The original scripts and parsed challenge data are included. From a fresh working directory, create this layout using the supplied files:

```text
work/data.json       <- data.json
work/recover.py      <- recover.py
work/rewind.py       <- rewind.py
work/decrypt.py      <- decrypt.py
```

Then run:

```sh
python3 work/recover.py
python3 work/rewind.py
python3 work/decrypt.py
```

These scripts use Python's standard library and preserve the original path conventions. They reconstruct the state and print the flag after checking all 100 samples.

## Lesson

MT19937 is unsuitable for secrets. Exposing later outputs can reveal earlier secret draws, even when large integers and rejection sampling obscure their alignment.

**Source chat:** “Inspect rocinate.zip for flag”, `01a19252-5e1d-7543-827a-c794f502eb63`. No contest submission was recorded.
