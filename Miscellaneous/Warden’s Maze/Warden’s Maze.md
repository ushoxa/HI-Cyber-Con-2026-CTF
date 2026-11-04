# Warden’s Maze

**HI Cyber Con 2026 CTF · Miscellaneous**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Reconstruct the Rust game’s 24×21 tile array and its exploration-bit update. Legal movement alone cannot cross the vault wall.

2. Compare the sight calculation with the write-back offset. Six rows correspond to 144 bytes, which becomes −112 when truncated to a signed byte; visibility can therefore modify a different tile.

3. The source identifies row 14, column 4 as the trigger location satisfying the required line of sight. Navigate there while avoiding the warden, then use the altered top wall to enter the vault. Coordinates and tile behavior should be checked against the supplied binary rather than assuming a generic maze layout.

## Reported result

```text
hiCTF{maze-warden-vault-seed-2026_f8dd7f12cf}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Warden’s Maze](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/wardens-maze). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
