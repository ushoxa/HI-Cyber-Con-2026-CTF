# Orphaned Context

**HI Cyber Con 2026 CTF · Web**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Inspect the relay console and validation errors to reconstruct the capture, interrupt, note and recovery operations.

2. Create a capture, retain its signed recovery descriptor, then interrupt it so its slot becomes available. Store an untrusted maintenance-format note in that same slot under a newer epoch.

3. Ask recovery preview to use the old descriptor. Missing comparison against the current slot epoch lets the replacement note inherit trusted execution and read the incident seal.

4. The article displays hiCTF{local_dev_fixture_not_a_real_flag_5c5296be6f}. This is explicitly labeled a local fixture by its own text; it is not presented here as a validated competition flag. The summary documents the reported trust-boundary failure only.

## Sources and reproduction

[p4ndora.ai — Orphaned Context](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/orphaned-context). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
