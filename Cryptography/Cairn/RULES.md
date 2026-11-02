# Cairn: Specification

## 1. Field and notation

Let `p` be the prime given by the field `p` of `challenge.json`. Work in

```
GF(p^2) = GF(p)[i] / (i^2 + 1),
```

which is a field with `p^2` elements (`p = 3 mod 4`, so `i^2 + 1` is
irreducible over GF(p)).

Every element `z` of GF(p²) is written `z = a + b*i` with **canonical**
integer representatives `a, b ∈ [0, p)`. All integer coefficients occurring
below are reduced modulo `p` into `[0, p)` before use.

## 2. Canonical serialization

For `z = a + b*i` define the 64-byte string

```
ser(z) = LE32(a) || LE32(b),
```

where `LE32(x)` is the 32-byte little-endian encoding of the integer
`x ∈ [0, p)`, least significant byte first, and `||` is byte-string
concatenation.

## 3. Parameters

| Symbol | Field in `challenge.json` | Meaning |
|---|---|---|
| `p` | `p` | prime field modulus |
| `j_0` | `j0` | start of the walk, given as the pair `[a, b]` |
| `salt` | `salt_hex` | 32-byte public salt, hex-encoded |
| `T` | `T` | number of walk steps |
| `L` | `L` | the list `[2, 3, 5, 7]` |
| `Phi_l(X, Y)` | `phi` | modular polynomials, see below |
| | `ciphertext_b64`, `nonce_b64`, `tag_b64` | AES-256-GCM ciphertext, base64 |

For each `l ∈ L`, the field `phi` maps `l` to a list of triples
`[x_exp, y_exp, coefficient]`, and

```
Phi_l(X, Y) = Σ  coefficient · X^x_exp · Y^y_exp
```

the sum being over all triples of that list. Each `Phi_l` has integer
coefficients, is symmetric in `X` and `Y`, and is monic of degree `l + 1` in
each variable; in particular `f(Y) = Phi_l(j_i, Y)` is monic of degree
`l + 1`.

## 4. The walk

Set `j := j_0`. For each step index `i = 0, 1, …, T-1`, in order:

1. **Hash.** Compute
   `h = SHA256( ser(j) || BE8(i) || salt )`,
   where `BE8(i)` is the 8-byte big-endian encoding of `i`, and `SHA256` is
   FIPS 180-4. Write `h[k]` for byte `k` of the digest (`h[0]` first).

2. **Degree.** Set `l = L[ h[0] mod 4 ]`.

3. **Polynomial.** Form `f(Y) = Phi_l(j, Y)` over GF(p²): substitute `X = j`
   in `Phi_l` and read the result as a polynomial in `Y` with coefficients in
   GF(p²).

4. **Squarefree part.** Let `f'` be the formal derivative of `f` with respect
   to `Y`, and set

   ```
   f_sq = f / gcd(f, f')
   ```

   (the quotient is exact; if `gcd(f, f')` is constant, take `f_sq = f`).
   Then `f_sq` is monic and has no repeated roots.

5. **Root set.** Compute all distinct roots of `f_sq` in GF(p²); their number
   equals the degree of `f_sq`. Order them as follows: for
   `z = a + b*i` and `z' = a' + b'*i`, put `z` before `z'` if and only if the
   pair `(a, b)` is lexicographically smaller than `(a', b')`, comparing `a`
   with `a'` and `b` with `b'` as unsigned 256-bit integers, smallest first.
   Denote the resulting list by `r_0, r_1, …, r_{n-1}`, where `n` is the
   number of distinct roots.

6. **Step.** Set `j := r_{ h[1] mod n }`.

After the loop, write `j_T` for the final value of `j`.

## 5. Key derivation

```
key = SHA256( ser(j_T) || "IsogenyLabyrinth" ),
```

where `"IsogenyLabyrinth"` is the 16-byte ASCII string exactly as written,
without a terminating newline.

## 6. Encryption

The flag was encrypted under `key` with **AES-256-GCM**, with empty additional
authenticated data. The plaintext is the exact flag bytes, without a trailing
newline:

* nonce: `nonce_b64` (base64, 12 bytes),
* ciphertext: `ciphertext_b64` (base64),
* authentication tag: `tag_b64` (base64, 16 bytes).

## 7. Parsing note

The integers in `challenge.json` (`p`, `j0`, and the polynomial
coefficients) are exact and up to 70 decimal digits long. They must be
parsed with arbitrary-precision integer support. IEEE-754-based JSON parsers
(including JavaScript's default `JSON.parse`) silently corrupt them.
