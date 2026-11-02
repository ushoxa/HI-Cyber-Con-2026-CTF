# Rocinate Revenge — write-up

**Category:** algebraic cryptanalysis  
**Recovered:** 1 November 2026, Asia/Samarkand  
**Evidence:** recovered flag satisfies all 100 published products. Rechecked from the saved seed for this collection.

**Flag:** `hiCTF{r4nd05_15_53cu43d_7h15_71m3_w0t_y0u_g0nN4_d0??}`

The attack combines short integer relations, polynomial GCD, and Bézout's identity. It recovers the initial LCG state, removes the multiplicative masks, and then recovers the flag integer. The hidden exponent `e` is unnecessary.

This describes the completed computation. The recovered flag was checked against all 100 published samples, including a separate run of the packaged Python verifier.

## 1. What the challenge publishes

The archive's SHA-256 is:

```text
78540bed7e1e9fbe4deb67f710abde453b7fd87116fda6c61360749c735d9101
```

The relevant generator is:

```python
r = secrets.randbelow(N)
Rs = [r]
e = secrets.randbelow(N)
a, b = secrets.randbelow(N), secrets.randbelow(N)

for _ in range(n - 1):
    Rs.append((a * Rs[-1] + b) % N)

Cs = [secrets.randbelow(N) for _ in range(n)]
Zs = [ri * pow(s, ci, N) for ri, ci in zip(Rs, Cs)]
Ts = [pow(ri, e, N) for ri in Rs]
print(a, b, N, Zs, Cs, Ts)
```

Here `s` is the flag interpreted as a big-endian integer, `N = p*q`, and there are 100 samples. The supplied modulus has 2047 bits.

Using indices starting at zero, the public values satisfy:

\[
r_{i+1}=(a r_i+b)\bmod N,
\]

\[
Z_i=r_i\,(s^{C_i}\bmod N).
\]

The multiplication producing `Z_i` is **not reduced modulo `N`**. Once a nonce is known, exact integer division reveals the corresponding modular power of the flag.

The `T_i = r_i^e mod N` values initially suggest a related-message attack. However, `e` is hidden. The successful attack uses `a`, `b`, `N`, `Z`, and `C`; it does not use `T`.

## 2. Express every nonce using one unknown

Because the LCG parameters are public, write every state as an affine function of the initial state:

\[
r_i\equiv\alpha_i r_0+\beta_i\pmod N.
\]

The coefficients are public and follow:

\[
\alpha_0=1,\quad\beta_0=0,
\]

\[
\alpha_{i+1}=a\alpha_i\bmod N,\qquad
\beta_{i+1}=a\beta_i+b\bmod N.
\]

Normalize each sample by defining:

\[
t_i=\beta_i\alpha_i^{-1}\bmod N,\qquad
v_i=Z_i\alpha_i^{-1}\bmod N.
\]

Then:

\[
v_i\equiv(r_0+t_i)s^{C_i}\pmod N.
\]

This leaves two secrets: the seed `r_0` and the flag integer `s`. The needed inverses exist in this instance; the verifier also checked the relevant values are coprime to `N`.

## 3. Cancel the flag powers with integer relations

Find a nonzero integer vector `k` such that:

\[
\sum_{i=0}^{99} k_i C_i=0.
\]

This is an **exact integer relation**, not a relation modulo `N`.

Raise the normalized samples to those exponents and multiply:

\[
\prod_i v_i^{k_i}
\equiv
\prod_i(r_0+t_i)^{k_i}\,
s^{\sum_i k_iC_i}
\equiv
\prod_i(r_0+t_i)^{k_i}\pmod N.
\]

The flag disappears because its total exponent is zero. Negative powers mean modular inverses.

Set the known constant:

\[
K_k=\prod_i v_i^{k_i}\bmod N.
\]

Separate the positive and negative entries of `k` to obtain a polynomial:

\[
F_k(X)=
\prod_{k_i>0}(X+t_i)^{k_i}
-K_k\prod_{k_i<0}(X+t_i)^{-k_i}
\quad\text{in }(\mathbb Z/N\mathbb Z)[X].
\]

By construction, `F_k(r_0) = 0 mod N`.

This is the central step: an integer relation among the public challenges turns the masked samples into a polynomial with the secret seed as a root.

## 4. Keep the polynomial degrees manageable

Any exact relation works algebraically, but large coefficients create enormous polynomials. The relevant degree bound is:

\[
D(k)=\max\left(\sum_{k_i>0}k_i,\sum_{k_i<0}(-k_i)\right).
\]

I used lattice reduction to find short relations. A standard construction uses rows of the form:

\[
(e_i,\ M C_i),
\]

where `e_i` is a coordinate unit vector and `M` is a large integer. A lattice vector is therefore `(k, M*sum(k_i*C_i))`. Reduced vectors whose last coordinate is zero give exact relations. Every selected relation is checked explicitly before use.

Initial LLL relations produced degrees around 44 million. Applying BKZ with block size 45 reduced the two selected polynomial degrees to:

```text
23,939,964
24,671,009
```

The exact two relation vectors are included in the solver's `relations.json`, so reproducing the final attack does not require repeating lattice reduction.

## 5. Recover the seed by polynomial GCD

Construct two polynomials from independent short relations:

\[
F_1(r_0)=F_2(r_0)=0\pmod N.
\]

Both contain the factor `X-r_0`. For the selected relations in this instance, their normalized GCD was exactly:

\[
\gcd(F_1,F_2)=X-r_0.
\]

For a degree-one result `u*X+v`, recover the seed as:

\[
r_0=-v u^{-1}\bmod N.
\]

This was the expensive part of the solve. The implementation used Python to orchestrate a C++ helper built with NTL and GMP. It constructed products in trees, used auxiliary-prime FFT arithmetic with sequential CRT reconstruction for large products, and stored polynomial coefficients on disk.

The GCD ran in checkpointed half-GCD stages, restarting the native process between stages to release temporary allocations. The real computation finished after 27 reductions with a degree-one GCD.

Polynomial arithmetic modulo a composite is not field arithmetic: an attempted inverse can fail on a nonunit. Such a failure can reveal a factor of `N`. In this completed run, the GCD path succeeded and recovered the seed directly.

## 6. Remove the nonces and recover the flag

With `r_0` known, regenerate all 100 LCG states. Because the published products were unreduced, compute:

\[
m_i=Z_i/r_i=s^{C_i}\bmod N
\]

using exact integer division. The verifier requires `Z_i % r_i == 0` and `0 <= m_i < N` for every sample.

The first two challenge exponents are coprime:

\[
\gcd(C_0,C_1)=1.
\]

Extended Euclid gives integers `u` and `v` satisfying:

\[
uC_0+vC_1=1.
\]

Therefore:

\[
m_0^u m_1^v
\equiv s^{uC_0+vC_1}
\equiv s\pmod N.
\]

The flag integer is smaller than `N`, so this residue is the original flag integer. Decode it as big-endian bytes.

The essential final step is:

```python
g, u, v = extended_gcd(C[0], C[1])
assert g == 1
s = pow(masks[0], u, N) * pow(masks[1], v, N) % N
assert all(pow(s, c, N) == m for c, m in zip(C, masks))
flag = s.to_bytes((s.bit_length() + 7) // 8, 'big')
```

## 7. Verification and reproduction

The completed recovery checked:

- The original archive's SHA-256.
- Both exact integer relations against the 100 public challenges.
- Exact division of every `Z_i` by its regenerated nonce.
- The range of every recovered modular power.
- `pow(s, C_i, N) == Z_i // r_i` for **all 100 samples**.
- The decoded flag's `hiCTF{...}` syntax.

The final consistency check was also rerun separately using the packaged Python verifier and the saved seed. The hidden-`e` commitments were not needed for these checks.

The solver bundle contains `solve.py`, the native helper sources, the two precomputed relations, a build script, and the NTL source archive. After extracting it, run:

```sh
sh build.sh
python3 solve.py /path/to/rocinate-revenge.zip
```

The tested environment was macOS ARM64 with Python 3, a C++17 compiler, GMP, and 24 GB RAM. Plan for a multi-hour computation and substantial temporary disk space; the bundle README recommends roughly 160 GB free. Its native memory accounting targets macOS and needs adaptation for Linux.

The output is:

```text
hiCTF{r4nd05_15_53cu43d_7h15_71m3_w0t_y0u_g0nN4_d0??}
```

The weakness is algebraic: public LCG parameters link the nonces through one seed, and exact relations cancel the flag exponents. Replacing predictable randomness with `secrets` does not remove those relations.

No flag submission to the contest server was performed.

## Files in this collection

The complete original solver bundle is included as [rocinate-revenge-solver.zip](rocinate-revenge-solver.zip). The parsed challenge data and recovered seed are preserved in `./`.

For a quick verification without repeating the polynomial GCD, extract the solver ZIP, import its `recover_flag` function, and call it with the JSON object from `parsed.json` and integer from `seed.txt`. That function regenerates the nonces, requires exact division and valid ranges, recovers the flag with Bézout coefficients, and checks all 100 exponent equations. This check was run again for the collection.

The million-degree polynomial work was not repeated. The full solver requires the original challenge archive; it validates that archive against the SHA-256 above. Some archive files are no longer present in Downloads, so this collection preserves the small evidence needed for final verification separately.

**Source chat:** “Find the cairn.zip flag”, `01a19590-1e94-7c12-b7ae-e720a78b2413`. This chat moved from Cairn to Rocinate Revenge; its title alone does not describe every challenge solved within it.
