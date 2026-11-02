# Memory Liar

**Category:** Forensics / Memory  **Flag:** `hiCTF{dk0m_unl1nk_3pr0c3ss_l1st_cr0ss_ch3ck_7c3a9f}`

> A critical workstation on the financial management subnet was suspected of being compromised by an APT. Our tier-1 triage team collected a physical memory capture and ran an automated process audit. The automated audit reported everything clean: all running processes appear ordinary, can you retrieve the flag?

File: `memory-liar.zip` → `memory.raw` (16 MB synthetic Windows memory capture)

## Solution

### 1. The decoy
`strings` finds this straight away:

```
Status: System integrity validated. No hidden tasks or hooks found.
Forensics Verification Token: hiCTF{th1s_1s_4_f4k3_d3c0y_fl4g_f0r_n00bs_883a1c}
```

It's bait for anyone who only greps. The audit "says it's clean", which is exactly what the title warns about.

### 2. Carving process records (psscan-style)
The dump has EPROCESS-like records every `0x8000` bytes. Each record keeps the image name at `+0x174`, the PID at `+0xbc` and `ActiveProcessLinks` (Flink, Blink) at `+0xc0`. Kernel VAs are `0x80000000 + physical offset`.

| offset | name | PID | Flink | Blink |
|---|---|---|---|---|
| 0x313000 | smss.exe | 264 | → csrss | → System |
| … | csrss, wininit, services, lsass, svchost×2, explorer | | linked | linked |
| 0x353000 | notepad.exe | 2180 | → list head | → explorer |
| **0x35d000** | **winxnet.exe** | **1337** | **0x8035d0c0 (itself)** | **0x8035d0c0 (itself)** |

`winxnet.exe` is the 11th process. Its Flink and Blink both point **at itself**, and notepad's Flink skips over it to the list head. That is classic **DKOM unlinking**: the rootkit removed its EPROCESS from the doubly linked active-process list. A list-walking audit (`pslist`) never visits it, but a pool/signature scan (`psscan`) still finds the structure. That's the "process list cross-check" the flag refers to.

### 3. The payload
Right after the hidden process, at `0x35f000`, there's a tagged blob:

```
52 4f 4f 54 | 39 05 00 00 | 5d 00 00 00 | 33 00 00 00 | 35 34 1e 09 ...
  "ROOT"       pid=1337      key=0x5d      len=51        data
```

It sits next to the C2 address `c2.darkshadow-apt.org:8443` and the marker `OP_SHADOW_LIAR_ACTIVE`. XOR the 51 data bytes with `0x5d` to get the flag.

## Files
- `solve/solve.py` carves the process records, flags the self-linked one and decodes the ROOT blob
- `artifacts/winxnet_eprocess_0x35d000.bin` is the hidden process record (4 KB)
- `artifacts/root_payload_0x35f000.bin` is the ROOT blob, C2 string and marker
- `artifacts/strings.txt` is the full strings dump with offsets
- `artifacts/solver_output.txt` is the solver output
