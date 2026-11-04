# The Collector's Trail

**HI Cyber Con 2026 CTF · Miscellaneous**

> Source-based solution summary, added 4 November 2026. Credit: p4ndora.ai / Offensive Lab. This is a paraphrased reading guide, not a claim of an independently reproduced solve.

## Approach

1. Extract one eight-byte fragment from each painting using its relevant carrier: PNG metadata, trailing data, transparent pixels, steghide, pixel bits or PNG row-filter data. Validate each against its two-byte SHA-256 seal.

2. Order fragments by artist birth year and derive a master key with HKDF-SHA256. Preserve the exact official museum locators when deriving the cabinet password.

3. Inside the cabinet, follow the keyed HMAC-based pixel selection and parity extraction. Validate the recovered payload’s CRC before following its release reference.

4. Download the referenced release artifact rather than similarly named repository decoys. Derive its AES-GCM key from the release serial and require tag verification. The source omits a complete extraction implementation.

## Reported result

```text
hiCTF{marble_sparrow_9eb44602eedb764aac082a3816b7d7cb}
```

Reported by p4ndora; not independently verified here.

## Sources and reproduction

[p4ndora.ai — The Collector's Trail](https://p4ndora.ai/benchmarks/hi-cyber-con-2026/the-collectors-trail). Read the original article for its full account. Reproduction requires the original challenge files or an equivalent instance; no third-party solver or artwork is copied here.
