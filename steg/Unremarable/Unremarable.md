# Unremarable

**HI Cyber Con 2026 CTF · steg**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Inspect PNG row-filter choices instead of accepting the first-row low-bit decoy. Decode the specially chosen filter transitions as base-five data, then decompress the settings.

2. Build the specified Sobel edge map and breadth-first traversal. The source reports threshold 114 and starting pixel (3319, 2198).

3. Recover three bits per seven pixels using Hamming matrix embedding on green/blue parity. The decoded header specifies a second traversal.

4. Follow its weighted Dijkstra path and extract red/blue parity data. Verify the recovered payload CRC, open the ZIP and read flag.txt. The original photograph and exact traversal tie-breaking are needed for reproduction; this article summary is not an extraction script.

## Reported result

```text
hiCTF{fr0nt13rs_f4d3_but_w31ght3d_p4ths_r3m41n}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Unremarable](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/unremarable). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
