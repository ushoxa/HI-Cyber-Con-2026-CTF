# Dormant Signer

**HI Cyber Con 2026 CTF · Blockchain**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Identify the destroyed Authorizer from the archived transactions. Reconstruct both the stored escrow value and the settlement digest used to mask it.

2. Find ECDSA signatures with identical r and opposite recovery parity. Account for nonces k and n−k when solving the pair of signature equations; verify the recovered private key against the trusted signer address.

3. Replay settlement validation in transaction order, including rejected entries. Recreate the liveness signature, hash it according to the contract, and XOR both masks away from the filed escrow value. Wrap the recovered text in the flag format. Correct signature normalization and replay rules matter.

## Reported result

```text
hiCTF{layout_undead_borrowed_betrays}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Dormant Signer](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/dormant-signer). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
