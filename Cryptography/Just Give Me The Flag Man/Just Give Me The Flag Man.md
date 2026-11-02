# CTF Challenge Write-Up: Shifting Through the Bases (`chall.zip`)

**Flag:** `hiCTF{sh1ft1ng_7hr0ugh_7h3_b4s3s}`

## Challenge Overview and Initial Reconnaissance

The challenge provides a single archive, `chall.zip` (SHA-256: `47250d4a65be0eb4ff5e8b4c31ae2120f95bb086f301ebb2467f7640614952c0`), accompanied by a short dialogue hinting at a note containing a "strange code" and a flag format of `hiCTF{}`.

Extracting `chall.zip` yields a single 156-byte ASCII text file, `chall.txt`, containing 52 space-separated two-character tokens:

```text
53 74 u3 17 35 x3 x2 76 24 33 93 u3 16 v4 36 v4 93 32 64 22 z3 x2 42 w4 54 05 v2 v5 63 v6 26 23 26 33 86 u3 33 x3 74 x2 06 54 62 x5 22 74 44 04 45 v5 93 x2
```

| Property | Value |
| :--- | :--- |
| **Archive Name** | `chall.zip` |
| **Archive SHA-256** | `47250d4a65be0eb4ff5e8b4c31ae2120f95bb086f301ebb2467f7640614952c0` |
| **Extracted File** | `chall.txt` (156 bytes, 52 space-separated tokens) |
| **Category** | Cryptography / Multi-Layer Encoding |
| **Recovered Flag** | `hiCTF{sh1ft1ng_7hr0ugh_7h3_b4s3s}` |

## Layer 1 & Layer 2: Reversing the Obfuscated Hex Dump

Inspecting the 52 two-character tokens in `chall.txt` reveals two immediate structural anomalies that point to an obfuscated hexadecimal dump:

1. **Reversed Nibble Positions**: In Every two-character token, the second character belongs strictly to the set `{2, 3, 4, 5, 6, 7}`. In standard ASCII hexadecimal encoding, printable characters (`0x20`–`0x7e`) always have `2` through `7` as their *first* (upper) nibble. This indicates that the character order of the hex string was reversed.
2. **Atbash-Substituted Hex Letters**: The first character of each token consists of digits `0`–`9` along with the lowercase letters `{u, v, w, x, z}`. Whereas standard hexadecimal uses the first six letters of the alphabet (`a`–`f`), this ciphertext uses the last six letters (`u`–`z`). Applying the Atbash cipher to the lowercase alphabet (`a` $\leftrightarrow$ `z`, `b` $\leftrightarrow$ `y`, `c` $\leftrightarrow$ `x`, `d` $\leftrightarrow$ `w`, `e` $\leftrightarrow$ `v`, `f` $\leftrightarrow$ `u`) maps these characters back to valid hexadecimal digits.

Reversing the entire string and applying Atbash to the letters recovers a valid 52-byte hexadecimal sequence:

```text
2c 39 5e 54 40 44 47 22 5c 26 45 60 2c 47 3c 33 3f 68 33 62 32 62 6e 36 5e 2e 50 45 4d 24 2c 3a 22 46 23 39 4e 63 4e 61 3f 39 33 42 67 2c 3c 53 71 3f 47 35
```

Decoding these 52 hex bytes into ASCII produces the intermediate string:

```text
,9^T@DG"\&E`,G<3?h3b2bn6^.PEM$,:"F#9NcNa?93Bg,<Sq?G5
```

## Layer 3: Decoding Standard Ascii85 (Base85)

The 52-character intermediate string consists entirely of characters within the ASCII range `0x21` (`!`) to `0x75` (`u`), which is the exact alphabet of standard Ascii85 (`Base85`). Furthermore, its length of 52 characters decomposes into ten 5-character blocks plus a 2-character tail (`G5`), which canonically encodes `10 * 4 + 1 = 41` bytes.

Decoding this string with standard Ascii85 yields a 41-byte printable ASCII string:

```text
#!dvnJk6rRHc9"NB7NnI*/1##$!DLYv$^:z3#<Tjw
```

## Layer 4 & Layer 5: Undoing ROT47 and Base91

The 41-character output from Ascii85 contains letters, digits, and punctuation spanning `0x21` (`!`) to `0x7a` (`z`), including characters above `u` (`v`, `w`, `z`) and double quotes (`"`). Because length 41 (`41 % 5 == 1` and `41 % 4 == 1`) cannot be produced by standard chunked Base85 or Base64, we look for printable-ASCII ciphers and variable-bit encodings:

1. **ROT47 Rotation**: Rotating all printable ASCII characters (`33`–`126`) by 47 positions (`ROT47`) transforms the 41-character string into:

```text
RP5G?y<eC#w4hQ}qf}?xY^`RRSPs{*GS/iKbRk%;H
```

2. **Base91 Decoding**: Every character in `RP5G?y<eC#w4hQ}qf}?xY^`RRSPs{*GS/iKbRk%;H` belongs to the 91-character Henke `basE91` alphabet (`A–Z`, `a–z`, `0–9`, and `!#$%&()*+,./:;<=>?@[]^_`{|}~"`, which excludes `-`, `\`, and `'`). Decoding this string using `basE91` reveals a 34-character string matching the exact structure and braces of the target flag:

```text
feKTH{uf1ht1zg_7fv0sgf_7f3_l4u3u}
```

## Layer 6: Recovering the Flag via Atbash and ROT13

The output of Base91 (`feKTH{uf1ht1zg_7fv0sgf_7f3_l4u3u}`) preserves the curly braces, underscores, and leetspeak digits (`1`, `7`, `0`, `3`, `4`) of the flag while substituting the alphabetic characters. Comparing the prefix `feKTH` against the expected `hiCTF` prefix reveals the final cipher pair:

* Applying **Atbash** (`a`–`z` $\leftrightarrow$ `z`–`a`, `A`–`Z` $\leftrightarrow$ `Z`–`A`) transforms `feKTH{uf1ht1zg_7fv0sgf_7f3_l4u3u}` into `uvPGS{fu1sg1at_7ue0htu_7u3_o4f3f}`.
* Applying **ROT13** (`a`–`z` shifted by 13) transforms `uvPGS{fu1sg1at_7ue0htu_7u3_o4f3f}` into the plaintext flag:

```text
hiCTF{sh1ft1ng_7hr0ugh_7h3_b4s3s}
```

## Complete Decoding Pipeline Summary

| Step | Operation | Output |
| :--- | :--- | :--- |
| **0** | Raw `chall.txt` | `53 74 u3 17 35 x3 x2 76 24 33 93 u3 ... 45 v5 93 x2` |
| **1** | Reverse + Atbash | `2c 39 5e 54 40 44 47 22 5c 26 45 60 ... 3f 47 35` |
| **2** | From Hex | `,9^T@DG"\&E`,G<3?h3b2bn6^.PEM$,:"F#9NcNa?93Bg,<Sq?G5` |
| **3** | From Base85 (Ascii85) | `#!dvnJk6rRHc9"NB7NnI*/1##$!DLYv$^:z3#<Tjw` |
| **4** | ROT47 | `RP5G?y<eC#w4hQ}qf}?xY^`RRSPs{*GS/iKbRk%;H` |
| **5** | From Base91 | `feKTH{uf1ht1zg_7fv0sgf_7f3_l4u3u}` |
| **6** | Atbash + ROT13 | `hiCTF{sh1ft1ng_7hr0ugh_7h3_b4s3s}` |

## Standalone Python Solver

```python
#!/usr/bin/env python3
import base64
import codecs

B91_ALPHABET = (
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'abcdefghijklmnopqrstuvwxyz'
    '0123456789!#$%&()*+,./:;<=>?@[]^_`{|}~"'
)
B91_TABLE = {c: i for i, c in enumerate(B91_ALPHABET)}


def atbash(text: str) -> str:
    out = []
    for c in text:
        if 'a' <= c <= 'z':
            out.append(chr(ord('z') - (ord(c) - ord('a'))))
        elif 'A' <= c <= 'Z':
            out.append(chr(ord('Z') - (ord(c) - ord('A'))))
        else:
            out.append(c)
    return ''.join(out)


def rot47(text: str) -> str:
    return ''.join(
        chr(33 + (ord(c) - 33 + 47) % 94) if 33 <= ord(c) <= 126 else c
        for c in text
    )


def b91decode(encoded: str) -> bytes:
    v = -1
    b = 0
    n = 0
    out = bytearray()
    for c in encoded:
        if c not in B91_TABLE:
            continue
        c_val = B91_TABLE[c]
        if v < 0:
            v = c_val
        else:
            v += c_val * 91
            b |= v << n
            n += 13 if (v & 8191) > 88 else 14
            while True:
                out.append(b & 255)
                b >>= 8
                n -= 8
                if n <= 7:
                    break
            v = -1
    if v + 1:
        out.append((b | v << n) & 255)
    return bytes(out)


def solve() -> None:
    ct = (
        '53 74 u3 17 35 x3 x2 76 24 33 93 u3 16 v4 36 v4 93 32 64 22 '
        'z3 x2 42 w4 54 05 v2 v5 63 v6 26 23 26 33 86 u3 33 x3 74 x2 '
        '06 54 62 x5 22 74 44 04 45 v5 93 x2'
    )

    # Step 1 & 2: Reverse string, apply Atbash, and decode from Hex
    hex_str = atbash(ct[::-1])
    step2 = bytes.fromhex(hex_str).decode('ascii')

    # Step 3: Decode from Standard Base85 (Ascii85)
    step3 = base64.a85decode(step2).decode('ascii')

    # Step 4: Apply ROT47
    step4 = rot47(step3)

    # Step 5: Decode from Base91
    step5 = b91decode(step4).decode('ascii')

    # Step 6: Apply Atbash followed by ROT13
    flag = codecs.encode(atbash(step5), 'rot_13')
    print(f'Recovered Flag: {flag}')


if __name__ == '__main__':
    solve()
```
