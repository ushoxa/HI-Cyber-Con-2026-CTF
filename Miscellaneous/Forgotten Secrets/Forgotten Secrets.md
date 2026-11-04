# Forgotten Secrets

**HI Cyber Con 2026 CTF · Miscellaneous**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Ignore obvious flag-related decoys and inspect the dump as bytes. High entropy across the file does not rule out a simple substitution applied to scattered text.

2. Test every single-byte XOR key, using the known hiCTF{ prefix to detect candidates. Key 0x42 exposes repeated matching strings.

3. Extract complete brace-delimited candidates and compare repeated copies. The source reports 22 identical occurrences bracketed by DEADBEEF and CAFEBABE markers. Repetition and context distinguish the result from planted plaintext decoys.

## Reported result

```text
hiCTF{m3m0ry_dump_d1g_d33p}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Forgotten Secrets](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/forgotten-secrets). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
