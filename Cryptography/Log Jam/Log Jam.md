# Log Jam

**HI Cyber Con 2026 CTF · Cryptography**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Read the finite-field parameters and authenticated ciphertext from params.json. The public key lies in a roughly 70-bit prime-order subgroup, making a generic discrete-log attack feasible.

2. Use Pollard rho with exponent tracking and distinguished points. A collision gives a linear congruence for the secret exponent; handle non-invertible differences and verify g^x mod p = h.

3. The source reports x = 471774559909450042061. Hash its decimal ASCII representation with SHA-256 to derive the AES key, then decrypt with the supplied GCM nonce and tag. Authentication must pass before accepting the plaintext. No rho implementation is reproduced here.

## Reported result

```text
hiCTF{W0W1_y0u_4ctu4a11y_s01v3d_1t_ju$t_L1k3_tH4t}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Log Jam](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/log-jam). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
