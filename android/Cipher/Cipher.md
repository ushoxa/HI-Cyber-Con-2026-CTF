# Cipher

**Category:** Android · **Event:** HI Cyber Con 2026

## Result

```text
hiCTF{cryptography_should_be_implemnetd_properly}
```

The spelling `implemnetd` is intentional: it is exactly what the decrypted record contained. The historical solve authenticated all 64 AES-GCM records; the flag was in the 48th record (zero-based index 47), titled “Archived security memo.”

## Inspect the APK

The supplied `cipher.zip` had SHA-256 `d32ec3f2c705e1aefcba505d5f3af157680fe0bab50bc69418927c9298126745` and contained `cipher.apk`. Unpacking the APK exposed six DEX files and three raw resources: `m4.bin`, `n3.bin`, and `p7.bin`. The useful classes were `CryptoEngine`, `VaultStore`, and a legacy passphrase generator. The visible Android interface was not needed.

The vault used PBKDF2-HMAC-SHA256 with 32,768 iterations, followed by separate HMAC-derived keys and AES-GCM for each record. Those are strong primitives, but the passphrase generator restricted its seed to just 262,144 possibilities.

## Recover the passphrase

Reverse the resource masks and reproduce Java's 48-bit `Random` generator. The word table consists of 256 eight-byte words recovered from `m4.bin`. The verifier is 16 bytes recovered from `n3.bin`; its decoded value was `f3840a2b902c711f0ac8f924c295e815`.

The seed range began at `764149760` (`0x2d8c0000`). Each candidate selected six words, joined them with hyphens, and appended a two-digit suffix. Test the derived root using the first 16 bytes of HMAC-SHA256 over `cipher-verifier-v3`.

The matching seed was `764408707`, yielding:

```text
smxvoisk-fcxfgnpl-poznukfv-zxpmztpo-yanlxwmm-yanlxwmm-42
```

## Decrypt and authenticate

Extract `res/raw/p7.bin` from the APK, then run this Python code with PyCryptodome installed. It reproduces the final decryption using the recovered passphrase rather than rerunning the seed search.

```python
from pathlib import Path
import hashlib, hmac
from Crypto.Cipher import AES

blob = Path('p7.bin').read_bytes()
assert blob[:5] == b'V1LT\x03'
salt = blob[5:21]
password = b'smxvoisk-fcxfgnpl-poznukfv-zxpmztpo-yanlxwmm-yanlxwmm-42'
root = hashlib.pbkdf2_hmac('sha256', password, salt, 32768)
assert root.hex() == '2803a69149bea3d3535a6ae6073cfb21c76f5ddeebcf7e6b719cbbd3ffb47879'
prk = hmac.digest(salt, root, 'sha256')
pos = 22
for _ in range(blob[21]):
    index = blob[pos]
    nonce = blob[pos+1:pos+13]
    size = int.from_bytes(blob[pos+13:pos+15], 'big')
    encrypted = blob[pos+15:pos+15+size]
    pos += 15 + size
    key = hmac.digest(prk, b'v1' + bytes([index]) + b'\x01', 'sha256')
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    cipher.update(b'V1LT' + bytes([index]))
    plain = cipher.decrypt_and_verify(encrypted[:-16], encrypted[-16:])
    if b'hiCTF{' in plain:
        print(plain.decode())
assert pos == len(blob)
```

## Lesson

The weakness was the limited entropy of the passphrase source. Authenticated encryption also gave a reliable success check: a plausible-looking plaintext alone was not used as proof.
