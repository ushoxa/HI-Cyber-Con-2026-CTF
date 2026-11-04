# Last Execution

**HI Cyber Con 2026 CTF · Reverse Engineering**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Reconstruct the EXE-9 emulator and verify decoding against the image’s self-test. The source corrects three misleading manual constants: rotation 17, row bias 13 and dispatch shift 3.

2. Follow the HALT-dependent segment chain and self-modifying FINAL code. Accelerate LIMIT by measuring its 786,432-iteration state period and combining complete cycles with the remainder; compare small runs against direct emulation.

3. Keep the emulator’s final registers rather than the contradictory console log. Hash R1–R4 with the LASTEXEC framing, then reverse the image’s 16-round cipher to open the sealed will. The article does not include a complete emulator.

## Reported result

```text
hiCTF{3x3c_9_r3m3mb3rs_4ll_but_th3_l4st_h4lt_l13s}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Last Execution](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/last-execution). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
