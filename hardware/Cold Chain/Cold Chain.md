# Cold Chain

**HI Cyber Con 2026 CTF · hardware**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Inspect the technician toolkit for its fleet master key and authentication encoding. Combine the controller-provided serial and nonce with that key to generate the session response.

2. Find schedule S9 forcing defrost and macro M2 restoring that schedule. Disable M2 before disabling or deleting S9; otherwise the apparent repair is undone.

3. CTFWU additionally shows explicitly selecting cooling mode for all six cases. Poll STATUS in the same session until every case remains below 5°C for at least 60 seconds and compliance is confirmed.

4. The sources report different flag suffixes and slightly different schedule commands. Follow the supplied instance’s protocol and use its returned proof token.

## Reported result

```text
hiCTF{cold_chain_restored_defrost_cleared_44c895406a}
```

Reported by p4ndora; not independently verified here. CTFWU reports a different suffix; retain the result from your own challenge instance.

## Sources and reproduction

[p4ndora.ai — Cold Chain](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/cold-chain); [Phan Thành Danh (tinhatinh), CTFWU](https://tinhatinh.github.io/CTFWU/en/posts/hi-cyber-con-2026-ctf-cold-chain/). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
