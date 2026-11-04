# The Inner Engine

**HI Cyber Con 2026 CTF · Reverse Engineering**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Locate the 24-byte license gate and decode the embedded stack-machine program. Translate its handlers into constraints over pairs of input bytes, including modular products, sums and XORs.

2. Solve the 23 checks to enumerate 1,024 candidate keys. The activation-record hash provides the final selection criterion, so algebra alone does not identify the accepted key.

3. The source reports L1c#N0d3_7mQ9f3a2b8c6d1e as the accepted input. Run candidates against the original checker without triggering its tracer guard; the accepted activation record contains the flag. Existing supporting files in this folder are retained.

## Reported result

```text
hiCTF{vm_byt3c0d3_1nn3r_3ng1n3_unw0und!}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — The Inner Engine](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/the-inner-engine). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
