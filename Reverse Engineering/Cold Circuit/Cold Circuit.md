# Cold Circuit

**Category:** Reverse Engineering · **Event:** HI Cyber Con 2026

## Result

```text
hiCTF{6e305f6a7461675f6e65656465642121}
```

The hex payload decodes to `n0_jtag_needed!!`. The checker accepted the flag after its anti-debug environment branch was disabled in a temporary copy. This is the verification recorded during the CTF, not a fresh execution.

## Inspect the checker

`cold-circuit.zip` had SHA-256 `cd9e56173d294497a6e07d560db89c46abe359a702b40be1165332cb9adb4c1c`. It contained a 14,472-byte stripped Linux x86-64 PIE executable named `check`.

`strings` exposed the prefix `hiCTF{`, format failures, `Incorrect.`, and `Access granted.`. Imports included `memcmp` and `ptrace`. Disassembly separated format validation, hex decoding, round transformations, and the final comparison.

The payload goes through 20 rounds before comparison. Reversing those rounds recovered the bytes represented by `6e305f6a7461675f6e65656465642121`. Keep the outer flag payload as hex; submitting the decoded English text would not match the checker format.

## Explain the initial failed check

The first attempt with the recovered flag printed `Incorrect.`. Inspection showed that the executable altered its calculation when `ptrace` was denied. The restricted analysis environment took that branch, so the failure did not necessarily indicate a bad reversal.

For this exact binary, the historical solve changed bytes at file offsets `0x154c:0x154e` to `eb 16` in a separate `check-normal` copy. This bypassed the ptrace-result branch while retaining the normal round constants and comparison logic.

```python
from pathlib import Path
data = bytearray(Path('check').read_bytes())
data[0x154c:0x154e] = bytes.fromhex('eb16')
Path('check-normal').write_bytes(data)
```

Running the temporary copy with the flag as an argument returned:

```text
Access granted.
```

This patch is specific to the supplied challenge binary. It is not a general patch for other versions, and the observed result should be described as verification with the environment check disabled, rather than acceptance by an unmodified checker under all environments.
