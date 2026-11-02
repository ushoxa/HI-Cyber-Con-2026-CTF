# Snapfile

**Category:** Reverse Engineering · **Event:** HI Cyber Con 2026

## Result

```text
hiCTF{r3c0nstruct3d_th3_sn4pf1l3_by73_by_by73}
```

The original `snaptool` printed this flag when given the constructed `valid.snap`; the recovered label's SHA-256 also matched the embedded digest.

## Recover the container format

The archive SHA-256 was `33ba2e74970adb7f6f25c9b6a85eae326b2e7b5724c09e71fad6ed7a28f51eb6`. It provided a Linux x86-64 Crystal executable with a simple interface: accept a genuine snapshot and print its label, otherwise print `invalid snapfile`.

The useful path was the parser and validation logic, not the large Crystal runtime. Disassembly around the file-processing calls revealed big-endian header fields, bounded sections, and a rolling 64-bit integrity value. A minimal valid layout was enough; it did not require reconstructing a real dataset.

| Field | Value |
| :--- | :--- |
| Magic | `SNAP` |
| Version | 2 |
| Flags / reserved | 3 / 0 |
| Marker | `0x534e41502d4c4e47` |
| Section offset/size pairs | `(40,16)`, `(56,32)`, `(88,8)` |
| Integrity input | bytes 8 through 95 |

The checksum starts at `0x1357bdf02468ace1`. For each input byte, add the byte, multiply by `0xd1b54a32d192ed03` modulo 2^64, then XOR the result with itself shifted right by 29. The stored trailer is the resulting value XOR 88, encoded big-endian.

## Construct and verify

Run the following in a directory containing the original executable:

```python
from pathlib import Path
import hashlib, struct

blob = bytearray(b'SNAP' + struct.pack(
    '>HBBQ6I', 2, 3, 0, 0x534e41502d4c4e47,
    40, 16, 56, 32, 88, 8) + bytes(56))
h = 0x1357bdf02468ace1
for value in blob[8:96]:
    h = ((h + value) * 0xd1b54a32d192ed03) & ((1 << 64) - 1)
    h ^= h >> 29
blob += struct.pack('>Q', h ^ 88)
Path('valid.snap').write_bytes(blob)

# Independently recover the embedded label for this exact supplied binary.
raw = Path('snaptool').read_bytes()
encrypted = raw[0x5d740:0x5d760] + bytes.fromhex('e3073fe8d92dd49440dd1e147814')
seed = hashlib.sha256(blob[:40]).digest()
stream = b''.join(hashlib.sha256(seed + struct.pack('>I', i)).digest()
                  for i in range(2))
flag = bytes(a ^ b for a, b in zip(encrypted, stream))
assert hashlib.sha256(flag).digest() == raw[0x5d760:0x5d780]
print(flag.decode())
```

Then run `./snaptool valid.snap`. The offsets above are specific to the challenge executable, not a general Crystal file format.
