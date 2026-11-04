# TESSERA

**HI Cyber Con 2026 CTF · Forensics**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Search raw triage artifacts as UTF-16. Although the PowerShell log appears cleared to ordinary parsers, residual script bytes identify the remaining locations and cryptographic parameters.

2. Extract the ALPC trace message for AepLocalEndpoint_Q8 and XOR its hex payload with 0x5A. It yields the first fragment and the DiagTrackSvcAux service reference.

3. Recover machine DPAPI material using SYSTEM and SECURITY hives plus registry entropy. Decrypt the service’s blob to obtain the second fragment and an AES key.

4. Read custom reparse data from MFT record 101281. Decrypt with AES-256-CBC and IV bytes 0x10 through 0x1F, remove padding and position labels, then concatenate all three fragments.

## Reported result

```text
hiCTF{alpc_p0rt_c0lloquy_s35s10n_z3r0_syst3npr0f1l3_r3p4r53_buff3r_vort3x}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — TESSERA](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/tessera). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
