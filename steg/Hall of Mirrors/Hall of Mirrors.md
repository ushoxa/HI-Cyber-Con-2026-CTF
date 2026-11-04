# Hall of Mirrors

**HI Cyber Con 2026 CTF · steg**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Inspect the audio spectrogram rather than trusting the obvious low-bit decoy. A high-frequency banner identifies a SplitMix64 gap/parity scheme and seed.

2. Recreate the seeded sample walk, recover bits from masked-byte parity, and verify the extracted program’s CRC32.

3. Interpret MVM1 sequentially: its rolling instruction hash decrypts later blocks, so static decoding alone misses the execution-dependent transformation.

4. The resulting output contains secp256k1 signatures whose nonces have twelve known high zero bits. Form the hidden-number lattice, reduce it with LLL, verify the candidate private key against the public key, and derive the key for the sealed flag. The source does not include a full interpreter or lattice script.

## Reported result

```text
hiCTF{h1dd3n_numb3r_l4ttice_le4k}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Hall of Mirrors](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/hall-of-mirrors). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
