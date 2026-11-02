# ChronoGrind

**Category:** sequential computation / cryptography  
**Recovered:** 30 October 2026, Asia/Samarkand  
**Evidence:** completed chain and authenticated decryption. Final-state decryption was repeated on 1 November.

Recovered flag: `hiCTF{n1c3_w0rk_n0w_t4k3_s0m3_r3$t}`

The provided archive's SHA-256 is
`5a5316e688fdd9ee3ae30d85a5659a52d0a5c0adf74ac71ba95583467ac256b3`.

`state.dat` begins with `CGD1`. Byte 4 contains the XOR byte, `0x4c`;
XOR bytes from offset 6 onward with it. Starting at offset `0x17`, each
record has a one-byte tag, a four-byte little-endian length, and its data.
The values in records `0x11` and `0x22` are integers encoded in base 241:
for each byte, set `value = value * 241 + byte`.

Record `0x11` is the 2048-bit modulus N, record `0x22` is the initial seed,
and record `0x33` gives 9,000,000,000 rounds. Record `0x44` matches the first
eight bytes of SHA-256 of the decimal string `N:seed:rounds`.

Compute the chain:

```python
v = seed
for _ in range(9_000_000_000):
    v = v * v % N
key = sha256(v.to_bytes(256, 'big')).digest()
```

The chain was evaluated in C using OpenSSL Montgomery multiplication,
with resumable checkpoints. Small runs were compared with direct Python
arithmetic and GMP. The reused 600,000,000-round checkpoint was also
independently recomputed from the original seed with GMP and matched.

`flag.enc` is laid out as `CGFX` (4 bytes), version (1 byte), nonce
(12 bytes), authentication tag (16 bytes), and ciphertext (the remaining
35 bytes). Decrypt the ciphertext using ChaCha20-Poly1305 with the derived
key and stored nonce, verifying the stored authentication tag.

All 9,000,000,000 rounds completed, and the ChaCha20-Poly1305 authentication
tag verified successfully.

SHA-256 of the final 256-byte chain value:
`96156b5d6965bf3ba35616cd280de13b2f7ae6e3734772083b7faf686cdf6148`.

## Reproduce the completed result

The `./` folder includes the original state and encrypted flag, the modulus and seed, and the saved final value. From that folder, this check derives the key and verifies the authentication tag:

```python
from pathlib import Path
import hashlib
from Crypto.Cipher import ChaCha20_Poly1305

v = int(Path("final_v.hex").read_text().strip(), 16)
key = hashlib.sha256(v.to_bytes(256, "big")).digest()
assert key.hex() == "96156b5d6965bf3ba35616cd280de13b2f7ae6e3734772083b7faf686cdf6148"
blob = Path("flag.enc").read_bytes()
assert blob[:5] == b"CGFX\x01"
cipher = ChaCha20_Poly1305.new(key=key, nonce=blob[5:17])
flag = cipher.decrypt_and_verify(blob[33:], blob[17:33])
assert flag == b"hiCTF{n1c3_w0rk_n0w_t4k3_s0m3_r3$t}"
print(flag.decode())
```

This uses PyCryptodome. It checks the saved endpoint, not all nine billion transitions again.

## Recompute the chain

The original OpenSSL implementation is preserved in `ossl_grind.c`. It converts the seed to Montgomery form, repeatedly squares it, saves resumable checkpoints, and converts the final result back to an ordinary integer.

With an OpenSSL development environment configured, its command structure is:

```sh
cc -O3 ossl_grind.c -lcrypto -o ossl_grind
./ossl_grind modulus.hex seed.hex 9000000000 fresh-run.chk recomputed-final.hex
```

On the original Mac, the compiler also needed Homebrew's OpenSSL include and library paths. Use a new checkpoint filename for a new computation; the saved tool does not bind a checkpoint to a modulus and seed. Checkpoint contents are Montgomery values, whereas `final_v.hex` contains the converted ordinary integer.

The full chain is deliberately expensive. It was completed during the original solve and was not rerun to prepare this collection.

**Source chat:** “Clarify bismillah request”, `01a18d67-3b19-7ca3-a2d8-a75811ab3652`. The user acknowledged the result positively; explicit contest-server acceptance was not captured.
