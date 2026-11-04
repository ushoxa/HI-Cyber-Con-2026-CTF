# The Foxglove Trace

**HI Cyber Con 2026 CTF · Miscellaneous**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Reconcile the notes and trusted-access-point configuration with the successful run’s debug log.

2. Infer the movement threshold from adjacent examples: a step delta of 40 is discarded while 41 is retained. Filter out untrusted networks and stationary samples before scoring.

3. Fit the scoring formula to logged subtotals: multiply each trusted network’s configured weight by the sum of retained signal values. FoxgloveCoffee_Guest scores 1044, ahead of CafeDelMundo 364, NETGEAR-8841 240 and HomePlex_5G 174.

4. Use the winning SSID as the flag payload. Neither the strongest individual reading nor the most frequently observed network is the correct selection criterion.

## Reported result

```text
hiCTF{FoxgloveCoffee_Guest}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — The Foxglove Trace](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/the-foxglove-trace). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
