# Quiet Upgrade

**HI Cyber Con 2026 CTF · Blockchain**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Compare proxy and implementation storage layouts. The proxy administrator and implementation’s branchOperator both occupy slot zero; delegatecall makes implementation writes affect proxy storage.

2. Call registerBranch through the proxy with a controlled address, then verify that admin() changed. Deploy an implementation satisfying the proxy’s proxiableSlot check and use the newly acquired upgrade authority.

3. Invoke the treasury release path through the malicious implementation in proxy context, reducing reserves below the one-percent success threshold. Both sources agree on this storage collision; use the original QU_TAG construction and ABI rather than treating abbreviated hashes as complete values.

## Reported result

```text
hiCTF{sl0t0_c0llision_then_a_qu1et_upgrade_0cc968a1b2}
```

Reported by p4ndora; not independently verified here. CTFWU reports a different suffix; retain the result from your own challenge instance.

## Sources and reproduction

[p4ndora.ai — Quiet Upgrade](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/quiet-upgrade); [Phan Thành Danh (tinhatinh), CTFWU](https://tinhatinh.github.io/CTFWU/en/posts/hi-cyber-con-2026-ctf-quiet-upgrade/). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
