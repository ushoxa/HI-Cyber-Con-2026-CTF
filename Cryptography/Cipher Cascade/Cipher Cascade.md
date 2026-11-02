# Cipher Cascade

**Category:** encoding / cryptography  
**Recovered:** 30 October 2026, Asia/Samarkand  
**Flag:** `hiCTF{l4y3r_by_l4y3r_unw1nd}`  
**Evidence:** deterministic decoding reproduced on 1 November. Contest acceptance was not recorded.

## Challenge

`cipher-cascade.zip` contains `cipher_cascade.txt`. Its hint specifies the outer layers: Reverse, Base64, Hex, followed by an unknown transformation.

Archive SHA-256:

```text
d7245a4bbf50857739833d75890ae001a9ed5cbee1f7eb5873171f1234c02631
```

The encoded line is:

```text
=Q2NxcTM2EzMhZTM2gjNmVTN2MzMjZDNzkzNmVzY2YmNmVTN2MzMjZDNzkzNidzM1cDNwUjN3UzN
```

## Recovery

1. Reverse the complete encoded line. This moves the Base64 padding to the end.
2. Base64-decode the reversed line. The result is ASCII hexadecimal:

   ```text
   75765047537b79346c33655f6f6c5f79346c33655f68616a3161717d
   ```

3. Decode those hexadecimal bytes as text:

   ```text
   uvPGS{y4l3e_ol_y4l3e_haj1aq}
   ```

4. Apply ROT13. The prefix `uvPGS` becomes `hiCTF`; the rest becomes the flag.

No key search is necessary. Each layer exposes a recognizable representation for the next layer.

## Reproduce

Run this against the extracted text file:

```python
import base64
import codecs
from pathlib import Path

text = Path("cipher_cascade.txt").read_text().strip().splitlines()[-1]
hex_text = base64.b64decode(text[::-1], validate=True).decode("ascii")
rotated = bytes.fromhex(hex_text).decode("ascii")
flag = codecs.decode(rotated, "rot_13")
assert flag == "hiCTF{l4y3r_by_l4y3r_unw1nd}"
print(flag)
```

## Lesson

Stacking reversible encodings does not provide secrecy. Inspect each intermediate result before adding another decoding operation.

**Source chat:** “Locate file in Downloads”, `01a18d1d-56e2-7a32-89d1-c0efe1736c7b`. The original text is preserved in `cipher_cascade.txt`.
