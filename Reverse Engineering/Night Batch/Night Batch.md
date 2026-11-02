# Night Batch — Writeup

## Part 1: NIGHTBATCH (`night-batch`) — Complete Writeup

### 1. Challenge Overview & Triage

**Challenge Prompt:**
> `NIGHTBATCH acct-validation step. the load module is all we kept; the COPYLIB and source rode out with the frame. it still runs: ./night-batch <account-key>. a good key clears the step. everything else bounces. the key was on a card by the console -- card's gone. recover it from the module.`

**Artifact Hashes & Binary Properties:**

| Property | Value |
| :--- | :--- |
| **Archive (`night-batch.zip`) SHA-256** | `64ad99c6d690a7fac13b7d7cb56e2cc7c8553feceda2b503305dcb3ff6afcc9c` |
| **Binary (`night-batch`) SHA-256** | `b5bf307fc486d3fd3c7f37d938df6a44a694d0236ed7a6f9db15d1cfb1d2ac01` |
| **File Type** | `ELF 64-bit LSB executable, x86-64, dynamically linked, stripped` |
| **Build ID (SHA-1)** | `04dd085be7caef7b53b4876989949592c301406f` |
| **Source Language / Runtime** | GnuCOBOL (`libcob` statically linked into `.text`, GMP math routines) |

Running `strings` on `night-batch` reveals standard GnuCOBOL runtime diagnostics (`libcob`, `PACKED-DECIMAL`, `COMP-3`, `COB_RUNTIME_CONFIG`, `cob_move_display_to_edited`) along with an obfuscated string in `.rodata` at `0x44d0a0`:

```text
;995/4.z(?0?9.?>P
```

XORing each byte of `;995/4.z(?0?9.?>P` (`17` bytes) with `0x5a` yields `"account rejected\n"`. Immediately following this string at `0x44d0c0` is a 42-byte (`0x2a`) encrypted payload, followed at `0x44d0f0` by the standard SHA-256 initial state words (`0x6a09e667`, `0xbb67ae85`, `0x3c6ef372`, `0xa54ff53a`, `0x510e527f`, `0x9b05688c`, `0x1f83d9ab`, `0x5be0cd19`).

---

### 2. GnuCOBOL Runtime & Data Structures

The C `main` entry point at `0x400940` initializes the GnuCOBOL runtime and invokes the compiled COBOL program entry point:

```c
int main(int argc, char **argv) {
    cob_init(argc, argv);      // 0x40c270
    int ret = NIGHTBATCH(0);   // 0x400a70
    cob_stop_run(ret);         // 0x40c470
}
```

GnuCOBOL represents every COBOL variable and literal via a 24-byte `cob_field` descriptor and a 16-byte `cob_field_attr` structure:

```c
typedef struct {
    unsigned char type;    // 0x10 = NUMERIC_DISPLAY, 0x11 = BINARY, 0x12 = PACKED, 0x21 = ALPHANUMERIC
    unsigned char digits;  // Total decimal digits
    signed char   scale;   // Decimal scale
    unsigned char flags;   // Attribute flags (e.g. HAVE_SIGN, UNSIGNED)
    const char   *pic;     // Picture string pointer (or NULL)
} cob_field_attr;

typedef struct {
    size_t                size;  // Storage byte length
    unsigned char        *data;  // Pointer to working-storage or constant bytes
    const cob_field_attr *attr;  // Pointer to field attribute descriptor
} cob_field;
```

Inspecting `.rodata` (`0x44cd30`–`0x44cf90`) and `.data` (`0x45e2e0`–`0x45e390`) reveals the program's Working-Storage fields and numeric literal descriptors:

| Descriptor Address | Field Size | Data Address | Attribute Address (`type`) | COBOL Equivalent / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `0x45e2e0` | `2` | `0x460120` | `0x44cec0` (`0x11` BINARY) | `WS-IDX PIC 9(4) COMP-5` (1-based loop index `1..18`) |
| `0x45e300` | `2` | `0x460130` | `0x44cec0` (`0x11` BINARY) | `WS-LEN PIC 9(4) COMP-5` (trimmed input length) |
| `0x45e320` | `40` | `0x460140` | `0x44ce90` (`0x21` ALPHANUM) | `WS-KEY-IN PIC X(40)` (command-line argument buffer) |
| `0x45e340` | `2` | `0x460170` | `0x44cec0` (`0x11` BINARY) | `WS-ARGC PIC 9(4) COMP-5` (argument count) |
| `0x45e360` | `3` | `0x4600e0` | `0x44ce60` (`0x12` PACKED) | `WS-REM PIC 9(4) COMP-3` (modular arithmetic result) |
| `0x45e380` | `1` | `0x4600f0` | `0x44cea0` (`0x11` BINARY) | `WS-VALID PIC 9 COMP-5` (`1` = valid, `0` = rejected) |
| `0x44cd30` | `3` | `0x44a7e4` | `0x44ce50` (`0x10` DISPLAY) | Literal `100` |
| `0x44cd50` | `1` | `0x44a7e8` | `0x44ceb0` (`0x10` DISPLAY) | Literal `9` |
| `0x44cd70` | `1` | `0x44a96b` | `0x44ceb0` (`0x10` DISPLAY) | Literal `5` |
| `0x44cd90` | `1` | `0x44a92d` | `0x44ceb0` (`0x10` DISPLAY) | Literal `4` |
| `0x44cdb0` | `1` | `0x44a7e2` | `0x44ceb0` (`0x10` DISPLAY) | Literal `2` |
| `0x44cdd0` | `1` | `0x44a7ea` | `0x44ceb0` (`0x10` DISPLAY) | Literal `3` |
| `0x44cdf0` | `2` | `0x44a7ec` | `0x44ce70` (`0x10` DISPLAY) | Literal `10` |
| `0x44ce10` | `1` | `0x44cc74` | `0x44ceb0` (`0x10` DISPLAY) | Literal `1` |
| `0x44ce30` | `1` | `0x44cd12` | `0x44ceb0` (`0x10` DISPLAY) | Literal `0` |

---

### 3. Input Validation & `PACKED-DECIMAL` Unpacking (`0x400b44`–`0x400d11`)

Inside `NIGHTBATCH_` (`0x400a70`), the program initializes `WS-VALID` (`0x4600f0`) to `1` (`0x40269c`) and executes the following validation pipeline:

1. **Argument Count Check (`0x400b5f`–`0x400b75`):**
   Calls `cob_accept_arg_number` (`0x405010`) into `WS-ARGC` (`0x460170`). If `WS-ARGC != 1`, it sets `WS-VALID = 0` (`0x400b77`) and jumps to the output routine `0x402f40`.
2. **Command-Line Read & Trim Length Check (`0x400bce`–`0x400c16`):**
   Pads `WS-KEY-IN` (`0x460140`, 40 bytes) with spaces (`0x20`), reads `argv[1]` via `cob_accept_arg_value` (`0x405070`), and computes `FUNCTION LENGTH(FUNCTION TRIM(WS-KEY-IN))` via `cob_intr_trim` (`0x41e3e0`) and `cob_intr_length` (`0x41e340`). If `WS-LEN` (`0x460130`) is not `18` (`0x12`), validation fails.
3. **Numeric Check (`0x400c1c`–`0x400c50`):**
   Constructs a temporary `cob_field` describing the 18-byte prefix `WS-KEY-IN(1:18)` (`size = 18`, `data = 0x460140`, `attr = 0x44ce90`) and calls `cob_is_numeric` (`0x404bc0`). Every character must be an ASCII digit `'0'`–`'9'`.
4. **Unpacking to `COMP-3` (`PACKED-DECIMAL`) Digits (`0x400c54`–`0x400d11`):**
   Loops `WS-IDX` (`0x460120`) from `1` to `18` (`0x12`). In each iteration, it calls `cob_move` (`0x40f900`) to move the single character `WS-KEY-IN(WS-IDX:1)` (`0x46013f + WS-IDX`) into a 1-byte `PACKED-DECIMAL` (`COMP-3`, attribute `0x44ce80`) slot at `0x4600ff + WS-IDX`.
   - For 0-indexed digits $d_0, d_1, \dots, d_{17} \in \{0, \dots, 9\}$, digit $d_i$ is stored at `0x460100 + i` as a packed BCD byte `(d[i] << 4) | 0x0f`.

---

### 4. Extracting & Solving the 23 Modular Equations (`0x400d13`–`0x4025c3`)

After unpacking $d_0 \dots d_{17}$, the COBOL program evaluates 23 arithmetic expressions using GnuCOBOL intrinsic functions:
- `cob_intr_binop(f1, op, f2)` (`0x41df30`), where `op` is `0x2a` (`'*'`) or `0x2b` (`'+'`)
- `cob_intr_mod(expr, modulus)` (`0x41e530`), where `modulus` is either `0x44cdf0` (`10`) or `0x44cd30` (`100`)
- `cob_decimal_set_field` (`0x4113c0`) and `cob_decimal_get_field` (`0x411de0`) to store the remainder into `WS-REM` (`0x45e360`)
- `cob_cmp_int(WS-REM, expected)` (`0x413920`), jumping to `0x400b77` (failure) if `eax != 0` (except the final check, which jumps to `0x400b86` on `eax == 0`)

#### Complete List of Extracted Equations

| # | Address Range | Modular Equation |
| :--- | :--- | :--- |
| **0** | `0x400d13`–`0x400d9a` | $(d_1 \cdot d_{10}) \bmod 10 = 8$ |
| **1** | `0x400da0`–`0x400e8f` | $(d_3 + d_4 + d_8) \bmod 10 = 3$ |
| **2** | `0x400e95`–`0x401063` | $(3d_2 + d_3 + 2d_4 + 3d_5 + d_6) \bmod 10 = 1$ |
| **3** | `0x401069`–`0x401139` | $(d_2 + d_{10} + d_{17}) \bmod 10 = 7$ |
| **4** | `0x40113f`–`0x401298` | $(3d_5 + d_6 + 2d_7 + 3d_8) \bmod 10 = 7$ |
| **5** | `0x40129e`–`0x401401` | $(3d_8 + d_9 + 2d_{10} + 3d_{11}) \bmod 10 = 7$ |
| **6** | `0x401407`–`0x40153a` | $(3d_{11} + d_{12} + 2d_{13}) \bmod 10 = 9$ |
| **7** | `0x401540`–`0x401718` | $(3d_{14} + d_{15} + 2d_{16} + 3d_{17} + d_0) \bmod 10 = 2$ |
| **8** | `0x40171e`–`0x4017ee` | $(d_0 + d_{11} + d_{17}) \bmod 10 = 7$ |
| **9** | `0x4017f4`–`0x4018b3` | $(d_6 + d_{10} + d_{14}) \bmod 10 = 6$ |
| **10** | `0x4018b9`–`0x401978` | $(d_7 + d_9 + d_{14}) \bmod 10 = 2$ |
| **11** | `0x40197e`–`0x401a3d` | $(d_0 + d_{13} + d_{17}) \bmod 10 = 3$ |
| **12** | `0x401a43`–`0x401b02` | $(d_7 + d_8 + d_{12}) \bmod 10 = 2$ |
| **13** | `0x401b08`–`0x401cc8` | $(2d_{16} + 3d_{17} + d_0 + 2d_1 + 3d_2) \bmod 10 = 2$ |
| **14** | `0x401cce`–`0x401de1` | $(d_{12} + 2d_{13} + 3d_{14}) \bmod 10 = 5$ |
| **15** | `0x401de7`–`0x401ea6` | $(d_0 + d_{12} + d_{13}) \bmod 10 = 5$ |
| **16** | `0x401eac`–`0x401ffe` | $(2d_7 + 3d_8 + d_9 + 2d_{10}) \bmod 10 = 1$ |
| **17** | `0x402004`–`0x402109` | $(3d_5 + d_6 + 2d_7) \bmod 10 = 9$ |
| **18** | `0x40210f`–`0x402255` | $(d_{12} + 2d_{13} + 3d_{14} + d_{15}) \bmod 10 = 4$ |
| **19** | `0x40225b`–`0x402311` | $(d_4 + d_5 + d_{16}) \bmod 10 = 4$ |
| **20** | `0x402317`–`0x40235e` | $(d_1 \cdot d_9) \bmod 10 = 4$ |
| **21** | `0x402364`–`0x402424` | $(d_0 + d_4 + d_8) \bmod 10 = 0$ |
| **22** | `0x40242a`–`0x4025c3` | $(4d_3 + 5d_6 + 5d_{10} + 2d_{15} + 9d_{16}) \bmod 100 = 94$ |

#### Step-by-Step Algebraic Reduction

1. **Determine $d_{15}$ and $d_8$ directly:**
   - Subtracting **Eq 14** from **Eq 18** modulo 10 gives:
     $$d_{15} \equiv 4 - 5 \equiv 9 \pmod{10} \implies d_{15} = 9$$
   - Subtracting **Eq 17** from **Eq 4** modulo 10 gives:
     $$3d_8 \equiv 7 - 9 \equiv 8 \pmod{10} \implies d_8 = 6$$
2. **Determine $(d_3 - d_0)$ and $(d_{11} - d_{13})$:**
   - Subtracting **Eq 21** ($d_0 + d_4 + d_8 \equiv 0$) from **Eq 1** ($d_3 + d_4 + d_8 \equiv 3$) yields:
     $$d_3 \equiv d_0 + 3 \pmod{10}$$
   - Subtracting **Eq 11** ($d_0 + d_{13} + d_{17} \equiv 3$) from **Eq 8** ($d_0 + d_{11} + d_{17} \equiv 7$) yields:
     $$d_{11} \equiv d_{13} + 4 \pmod{10}$$
3. **Determine $d_{13}$, $d_{11}$, and $d_{12}$:**
   - Substitute $d_{11} \equiv d_{13} + 4 \pmod{10}$ into **Eq 6** ($3d_{11} + d_{12} + 2d_{13} \equiv 9 \pmod{10}$):
     $$3(d_{13} + 4) + d_{12} + 2d_{13} \equiv 5d_{13} + d_{12} + 2 \equiv 9 \pmod{10} \implies d_{12} + 5d_{13} \equiv 7 \pmod{10}$$
   - Using $d_8 = 6$ in **Eq 12** ($d_7 + 6 + d_{12} \equiv 2 \pmod{10}$) gives $d_7 \equiv 6 - d_{12} \pmod{10}$.
4. **Propagate multiplicative constraints (**Eq 0** and **Eq 20**):**
   - Since $(d_1 \cdot d_{10}) \bmod 10 = 8$ and $(d_1 \cdot d_9) \bmod 10 = 4$, $d_1 \in \{1, 2, 3, 4, 6, 7, 8, 9\}$.
   - Propagating each $(d_1, d_9, d_{10})$ triple through **Eq 16**, **Eq 10**, **Eq 9**, **Eq 14**, **Eq 5**, **Eq 15**, **Eq 17**, **Eq 2**, **Eq 19**, **Eq 7**, **Eq 13**, and finally the modulo-100 checksum **Eq 22** eliminates all branches except a single unique solution:

$$(d_0, d_1, \dots, d_{17}) = (4, 8, 1, 7, 0, 2, 5, 9, 6, 3, 1, 8, 7, 4, 0, 9, 2, 5)$$

Thus the account key is **`481702596318740925`**.

---

### 5. Flag Decryption Routine (`0x402f40` & `0x4027e0`)

When all 23 equations pass, execution reaches `0x400b86` with `WS-VALID = 1` (`esi = 1`) and calls `0x402f40(rdi = 0x460140, esi = 1, edx = 0)`:

1. **Key Hash ($H_0$):** Calls the vectorized SHA-256 function `0x4027e0(0x460140, 18, rsp)` to compute the 32-byte digest $H_0 = \text{SHA-256}(\text{"481702596318740925"})$.
2. **Counter-Mode Keystream Expansion (`0x402fa0`–`0x403036`):**
   For counter $c \in \{0, 1\}$, appends `bswap32(c)` (`BE32(c)`) to $H_0$ (forming a 36-byte buffer at `rsp+0x60`) and hashes it with `0x4027e0` to obtain two 32-byte blocks:
   $$K = \text{SHA-256}(H_0 \parallel \text{BE32}(0)) \parallel \text{SHA-256}(H_0 \parallel \text{BE32}(1))$$
   It XORs the first 42 bytes (`0x2a`) of $K$ against the 42-byte ciphertext stored at `0x44d0c0` (`0x44d0bf + 1`).
3. **Plaintext Integrity Verification (`0x403040`–`0x403090`):**
   Computes $\text{SHA-256}(\text{plaintext})$ (`42` bytes) and compares the resulting 32-byte digest against four 64-bit little-endian constants embedded in the code:
   - `0x2c146846b66a3fbd` (`0x403057`)
   - `0x181654efa527e488` (`0x403066`)
   - `0x6dbc8ff6323aeadb` (`0x403078`)
   - `0xb0a680efaef6a08f` (`0x403085`)
   Upon matching, it writes the 42-byte plaintext and a newline to `stdout`:
   ```text
   hiCTF{c0b0l_p4ck3d_d3c1mal_n1ghtly_b4tch!}
   ```

---

### 6. Standalone Solver Script for `night-batch`

```python
#!/usr/bin/env python3
import hashlib
import struct

# 42-byte ciphertext from .rodata at 0x44d0c0 (file offset 0x4d0c0)
ENC_BLOB = bytes.fromhex(
    "3ea7a91f1d638ea53076040fde44c8f2"
    "76d3ee376a7e3699357c5cd01f61ad1a"
    "e06ef78e4970f8acf6f9"
)

# Expected SHA-256 digest of the decrypted flag from 0x403057..0x403085
EXPECTED_SHA256 = struct.pack(
    "<QQQQ",
    0x2C146846B66A3FBD,
    0x181654EFA527E488,
    0x6DBC8FF6323AEADB,
    0xB0A680EFAEF6A08F,
)

def solve_night_batch():
    # Deduced directly from (Eq 18 - Eq 14) and (Eq 4 - Eq 17)
    d8 = 6
    d15 = 9

    for d1 in range(10):
        for d10 in range(10):
            if (d1 * d10) % 10 != 8:  # Eq 0
                continue
            for d9 in range(10):
                if (d1 * d9) % 10 != 4:  # Eq 20
                    continue
                for d7 in range(10):
                    if (2 * d7 + 3 * d8 + d9 + 2 * d10) % 10 != 1:  # Eq 16
                        continue
                    d14 = (2 - d7 - d9) % 10       # Eq 10
                    d6 = (6 - d10 - d14) % 10      # Eq 9
                    d12 = (2 - d7 - d8) % 10       # Eq 12
                    for d13 in range(10):
                        if (d12 + 2 * d13 + 3 * d14) % 10 != 5:  # Eq 14
                            continue
                        for d11 in range(10):
                            if (3 * d11 + d12 + 2 * d13) % 10 != 9:  # Eq 6
                                continue
                            if (3 * d8 + d9 + 2 * d10 + 3 * d11) % 10 != 7:  # Eq 5
                                continue
                            d0 = (5 - d12 - d13) % 10   # Eq 15
                            d4 = (0 - d0 - d8) % 10     # Eq 21
                            d3 = (3 - d4 - d8) % 10     # Eq 1
                            d17 = (7 - d0 - d11) % 10   # Eq 8
                            if (d0 + d13 + d17) % 10 != 3:  # Eq 11
                                continue
                            d2 = (7 - d10 - d17) % 10   # Eq 3
                            for d5 in range(10):
                                if (3 * d5 + d6 + 2 * d7) % 10 != 9:  # Eq 17
                                    continue
                                if (3 * d2 + d3 + 2 * d4 + 3 * d5 + d6) % 10 != 1:  # Eq 2
                                    continue
                                d16 = (4 - d4 - d5) % 10  # Eq 19
                                if (3 * d14 + d15 + 2 * d16 + 3 * d17 + d0) % 10 != 2:  # Eq 7
                                    continue
                                if (2 * d16 + 3 * d17 + d0 + 2 * d1 + 3 * d2) % 10 != 2:  # Eq 13
                                    continue
                                if (4 * d3 + 5 * d6 + 5 * d10 + 2 * d15 + 9 * d16) % 100 != 94:  # Eq 22
                                    continue

                                digits = [
                                    d0, d1, d2, d3, d4, d5, d6, d7, d8,
                                    d9, d10, d11, d12, d13, d14, d15, d16, d17
                                ]
                                key_str = "".join(map(str, digits))
                                h0 = hashlib.sha256(key_str.encode()).digest()
                                ks = (
                                    hashlib.sha256(h0 + struct.pack(">I", 0)).digest()
                                    + hashlib.sha256(h0 + struct.pack(">I", 1)).digest()
                                )
                                plaintext = bytes(a ^ b for a, b in zip(ENC_BLOB, ks[:42]))
                                assert hashlib.sha256(plaintext).digest() == EXPECTED_SHA256
                                print(f"[+] Account Key : {key_str}")
                                print(f"[+] Flag        : {plaintext.decode()}")

if __name__ == "__main__":
    solve_night_batch()
```

---
