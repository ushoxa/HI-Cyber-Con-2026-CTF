# Cold Beacon — Writeup

## Part 2: Evidence Tag IR-2231-A (`cold-beacon`) — Complete Writeup

### 1. Challenge Overview & Static Triage

| Property | Value |
| :--- | :--- |
| **Archive (`cold-beacon.zip`) SHA-256** | `a01791f8259c7bcf1eb07f578abc686b2a4ab78d4fe410f565c74624e52610d8` |
| **Binary (`cold-beacon`) SHA-256** | `018def3f2f64dbf57abfde394dc063cae2fbe294ff832afcf3881626e95fd562` |
| **File Type** | `ELF 64-bit LSB executable, x86-64, dynamically linked, stripped` |
| **Source Language / Runtime** | Nim (`syncio.nim`, `cmdline.nim`, `paramStr`) |

The main module logic resides at `0x404271` (invoked from `0x404508` via `main` at `0x400530`):

1. **Argument Length Check (`0x4042bb`–`0x4042e2`):** Calls `paramCount` (`0x403a6a`) and `paramStr(1)` (`0x403342`), checking that `argc == 1` and `len(argv[1]) == 24` (`0x18`).
2. **Anti-Debug Check (`0x403aec`):** Reads `/proc/self/status`, locates `"TracerPid:"`, and parses the integer value that follows. If `TracerPid != 0`, it aborts decryption and calls `0x4041f9` to XOR 14 bytes at `0x405e00` (`954<3=z)?;6?>P`) with `0x5a`, printing `"config sealed\n"`.
3. **Table-Driven Constraint Check (`0x403cff`):** Evaluates 23 byte-level constraints defined by four parallel tables in `.rodata`:
   - `ops` at `0x406070` (`23` bytes)
   - `counts` at `0x406050` (`23` bytes)
   - `indices` at `0x405fc0` (`23 * 6 = 138` bytes, padded with `0xff`)
   - `targets` at `0x405fa0` (`23` bytes)
4. **Secondary Constraint Check (`0x403dc4`):** Verifies three additional equations on key bytes `k[0..23]`:
   - `(k[9] + k[10]) & 0xff == 0xa8`
   - `k[12] ^ k[4] == k[20]`
   - `(k[12] + k[13]) & 0xff == 0xe3`

---

### 2. Constraint Table Breakdown (`0x403cff`)

For each constraint $i \in \{0, \dots, 22\}$, the function selects `cnt = counts[i]` byte positions from `indices[6*i : 6*i + cnt]` and combines those bytes of the 24-byte key $k$ modulo 256 according to `ops[i]`:
- `op in {0, 3, 5}`: Bitwise XOR ($\bigoplus k[\text{idx}] = \text{targets}[i]$)
- `op in {1, 4}`: Modular sum ($\sum k[\text{idx}] \equiv \text{targets}[i] \pmod{256}$)
- `op == 2`: Modular product ($k[\text{idx}_0] \cdot k[\text{idx}_1] \equiv \text{targets}[i] \pmod{256}$)

| # | Op Type | Byte Indices | Target (Hex) | Equation ($\bmod\ 256$) |
| :--- | :--- | :--- | :--- | :--- |
| **0** | `0` (XOR) | `[5, 6]` | `0x07` | $k_5 \oplus k_6 = \text{0x07}$ |
| **1** | `1` (SUM) | `[9, 10]` | `0xa8` | $k_9 + k_{10} \equiv \text{0xa8}$ |
| **2** | `1` (SUM) | `[10, 11]` | `0x74` | $k_{10} + k_{11} \equiv \text{0x74}$ |
| **3** | `1` (SUM) | `[12, 13]` | `0xe3` | $k_{12} + k_{13} \equiv \text{0xe3}$ |
| **4** | `1` (SUM) | `[13, 14]` | `0xda` | $k_{13} + k_{14} \equiv \text{0xda}$ |
| **5** | `1` (SUM) | `[14, 15]` | `0x9c` | $k_{14} + k_{15} \equiv \text{0x9c}$ |
| **6** | `1` (SUM) | `[16, 17]` | `0xce` | $k_{16} + k_{17} \equiv \text{0xce}$ |
| **7** | `1` (SUM) | `[17, 18]` | `0xa5` | $k_{17} + k_{18} \equiv \text{0xa5}$ |
| **8** | `1` (SUM) | `[18, 19]` | `0x74` | $k_{18} + k_{19} \equiv \text{0x74}$ |
| **9** | `1` (SUM) | `[19, 20]` | `0x71` | $k_{19} + k_{20} \equiv \text{0x71}$ |
| **10** | `1` (SUM) | `[20, 21]` | `0x98` | $k_{20} + k_{21} \equiv \text{0x98}$ |
| **11** | `1` (SUM) | `[21, 22]` | `0x94` | $k_{21} + k_{22} \equiv \text{0x94}$ |
| **12** | `1` (SUM) | `[22, 23]` | `0x99` | $k_{22} + k_{23} \equiv \text{0x99}$ |
| **13** | `1` (SUM) | `[23, 0]` | `0xa9` | $k_{23} + k_0 \equiv \text{0xa9}$ |
| **14** | `2` (MUL) | `[3, 15]` | `0xc0` | $k_3 \cdot k_{15} \equiv \text{0xc0}$ |
| **15** | `2` (MUL) | `[7, 21]` | `0x83` | $k_7 \cdot k_{21} \equiv \text{0x83}$ |
| **16** | `2` (MUL) | `[11, 19]` | `0x24` | $k_{11} \cdot k_{19} \equiv \text{0x24}$ |
| **17** | `3` (XOR) | `[4, 12, 20]` | `0x00` | $k_4 \oplus k_{12} \oplus k_{20} = \text{0x00}$ |
| **18** | `3` (XOR) | `[2, 10, 18]` | `0x6c` | $k_2 \oplus k_{10} \oplus k_{18} = \text{0x6c}$ |
| **19** | `4` (SUM) | `[0, 4, 8, 12, 16, 20]` | `0xc4` | $k_0 + k_4 + k_8 + k_{12} + k_{16} + k_{20} \equiv \text{0xc4}$ |
| **20** | `5` (XOR) | `[1, 5, 9, 13, 17, 21]` | `0x09` | $k_1 \oplus k_5 \oplus k_9 \oplus k_{13} \oplus k_{17} \oplus k_{21} = \text{0x09}$ |
| **21** | `4` (SUM) | `[2, 7, 10, 15, 18, 23]` | `0xd9` | $k_2 + k_7 + k_{10} + k_{15} + k_{18} + k_{23} \equiv \text{0xd9}$ |
| **22** | `5` (XOR) | `[3, 6, 11, 14, 19, 22]` | `0x0f` | $k_3 \oplus k_6 \oplus k_{11} \oplus k_{14} \oplus k_{19} \oplus k_{22} = \text{0x0f}$ |

---

### 3. Standalone Solver Script for `cold-beacon`

```python
#!/usr/bin/env python3
import hashlib
import struct

EXPECTED_HASH = bytes.fromhex(
    "0502f285cdf9105600a27444181c3016"
    "09e2a30aaa7516c555f60802b066ad40"
)
ENC_BLOB = bytes.fromhex(
    "62e8732e8602c5dd3c16a976ae2a8991"
    "d4a18ed112e7405fbfb1352674256bff"
    "fdfe12332534e3b3fc9581c945e0a6"
)

def solve_cold_beacon():
    for s19 in range(256):
        s18 = (0x74 - s19) & 0xFF
        s17 = (0xA5 - s18) & 0xFF
        s16 = (0xCE - s17) & 0xFF
        s20 = (0x71 - s19) & 0xFF
        s21 = (0x98 - s20) & 0xFF
        s22 = (0x94 - s21) & 0xFF
        s23 = (0x99 - s22) & 0xFF
        s0  = (0xA9 - s23) & 0xFF
        if (s21 & 1) == 0:
            continue
        s7 = (0x83 * pow(s21, -1, 256)) & 0xFF
        for s11 in range(256):
            if (s11 * s19) & 0xFF != 0x24:
                continue
            s10 = (0x74 - s11) & 0xFF
            s9  = (0xA8 - s10) & 0xFF
            s2  = s10 ^ s18 ^ 0x6C
            s15 = (0xD9 - (s2 + s7 + s10 + s18 + s23)) & 0xFF
            s14 = (0x9C - s15) & 0xFF
            s13 = (0xDA - s14) & 0xFF
            s12 = (0xE3 - s13) & 0xFF
            s4  = s12 ^ s20
            s8  = (0xC4 - (s0 + s4 + s12 + s16 + s20)) & 0xFF
            for s3 in range(256):
                if (s3 * s15) & 0xFF != 0xC0:
                    continue
                s6 = s3 ^ s11 ^ s14 ^ s19 ^ s22 ^ 0x0F
                s5 = s6 ^ 0x07
                s1 = s5 ^ s9 ^ s13 ^ s17 ^ s21 ^ 0x09
                key = bytes([
                    s0, s1, s2, s3, s4, s5, s6, s7,
                    s8, s9, s10, s11, s12, s13, s14, s15,
                    s16, s17, s18, s19, s20, s21, s22, s23,
                ])
                h0 = hashlib.sha256(key).digest()
                ks = (
                    hashlib.sha256(h0 + struct.pack(">I", 0)).digest()
                    + hashlib.sha256(h0 + struct.pack(">I", 1)).digest()
                )
                dec = bytes(a ^ b for a, b in zip(ENC_BLOB, ks[:0x2F]))
                if hashlib.sha256(dec).digest() == EXPECTED_HASH:
                    print(f"[+] Beacon Key  : {key.decode()}")
                    print(f"[+] Flag        : {dec.decode()}")

if __name__ == "__main__":
    solve_cold_beacon()
```
