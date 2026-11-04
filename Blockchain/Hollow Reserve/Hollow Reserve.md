# Hollow Reserve

**HI Cyber Con 2026 CTF · Blockchain**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Map the lending contracts and identify the oracle’s dependence on a thin pool’s instantaneous reserve ratio rather than a manipulation-resistant price.

2. Within one transaction, obtain RSV through the flash lender and swap into COL in the oracle pool. The source uses a 2,000,000 RSV swap to inflate the apparent collateral price.

3. Deposit the acquired COL, borrow the vault’s available RSV against its inflated valuation, then repay the flash loan before returning. Confirm vault depletion and the challenge success condition. Pool reserves and instance addresses must be recovered from the original challenge; this summary supplies no deployable attack contract.

## Reported result

```text
hiCTF{th1n_p00l_was_the_r3al_0racle}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Hollow Reserve](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/hollow-reserve). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
