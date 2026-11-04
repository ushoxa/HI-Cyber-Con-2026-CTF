# RESURRECTION (Operation Eclipse Void)

**HI Cyber Con 2026 CTF · Forensics**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Rebuild partition and NTFS geometry from surviving backup metadata rather than trusting the wiped primary structures.

2. Recover five labeled fragments: a DLL overlay XORed with its timestamp bytes; hidden NTFS run lengths beyond a misleading attribute boundary; USN timestamp differences with the baseline removed; character codes stored in EVTX fields typed as Boolean; and spacing between allocated clusters unclaimed by files.

3. Preserve fragment ordering and concatenate their decoded contents. This requires parsing low-level structures rather than relying on ordinary file extraction. The source article explains the hiding locations but does not publish a complete recovery script.

## Reported result

```text
hiCTF{p3_0v3rl4y_71m3d473574mp_k3y_n7f5_runl157_cl5_g30m37ry_7r4ns4c710n_n4n0_f1l371m3_3v7x_b1n4ry_xml_70k3n5_b17m4p_orph4n_v01d_r35urr3c710n}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — RESURRECTION (Operation Eclipse Void)](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/resurrection). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
