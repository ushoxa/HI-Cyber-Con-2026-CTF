# Entitlement

**HI Cyber Con 2026 CTF · Reverse Engineering**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Unpack the protected checker while accounting for its tracer and code-integrity checks, then extract the bytecode’s mathematical checks.

2. Invert the 13th-power map in GF(2^64) using the inverse exponent modulo 2^64−1, undoing the surrounding XORs. The source obtains serial 8f7db18bd70e193b.

3. Reconstruct the elliptic curve from its point arithmetic. Its order equals the field prime, enabling Smart’s anomalous-curve attack; validate the recovered scalar by multiplication.

4. Use activation value 2977e17b118de75b3b4e921a4 and allow the expensive final derivation to complete. The article reports approximately eleven minutes; an equivalent curve scalar is not necessarily an equivalent flag key.

## Reported result

```text
hiCTF{>o<_C0ngrats_Her3_1s_Y0ur_HI4_Subscript1on_^_^}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Entitlement](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/entitlement). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
