# Epsilon Drift

**HI Cyber Con 2026 CTF · Reverse Engineering**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Interpret the 32-byte calibration vector as four little-endian IEEE 754 doubles. Reverse the sign, exponent and mantissa constraints on the first two fields to obtain 1.1 and 2.2.

2. Compute the third field using the actual floating-point addition 1.1 + 2.2. Its representation is one ULP above the literal 3.3, so substituting the literal fails.

3. Use negative zero for the fourth field: it compares equal to zero while retaining the sign bit required by the success path. Pack the four values in order and supply their hexadecimal encoding to the validator.

## Reported result

```text
hiCTF{1eee754_s1gn3d_z3r0_1u1p_dr1ft_eps!}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Epsilon Drift](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/epsilon-drift). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
