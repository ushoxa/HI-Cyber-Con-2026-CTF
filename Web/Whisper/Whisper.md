# Whisper

**HI Cyber Con 2026 CTF · Web**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Test the token endpoint’s secret field with a JSON query object. A NoSQL operator bypass grants the report-signer identity and export scope, but does not reveal its signing secret.

2. Use anchored $regex queries as a success/failure oracle to recover the hexadecimal secret one character at a time. Restrict candidate characters and preserve the prefix already recovered.

3. Reconstruct the export signature from server validation errors: canonical method, path, sorted query, body digest, timestamp and nonce. Compute HMAC-SHA256 with the recovered client secret and submit a fresh signed export request. Confirm successful authorization rather than stopping at token issuance.

## Reported result

```text
hiCTF{bl1nd_regex_3xfil_then_f0rge_the_cust0m_s1gner_bfab05b8ca}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — Whisper](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/whisper). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
