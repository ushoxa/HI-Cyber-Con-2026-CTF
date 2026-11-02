# Ghost in RAM

**Category:** Forensics · **Event:** HI Cyber Con 2026

## Result

```text
hiCTF{gh0st_pr0c3ss_rng_pwn3d}
```

## Triage the memory image

The supplied `ghost-in-ram.zip` had SHA-256 `5d93dd23e89876a4d7caead1dca17121ae36a17a29941a6c0bd75fccf13f020e` and contained `mem.elf`, a 2,164,394,051-byte Linux RAM image. The machine itself had been wiped, making residual memory the source of evidence.

Start with offset-bearing strings and structural searches:

```bash
strings -a -t x -n 6 mem.elf > strings.txt
```

Several flag-shaped strings were deliberate decoys, including `hiCTF{d3bug_m3}` and `hiCTF{stop_here}`. One decoy even told the analyst to stop. Those bytes were evidence to investigate, not trustworthy instructions or proof of the solution.

## Find the custom VM

A search for `GVM1` found two occurrences. The meaningful structured header was at file offset `0x21d4038`; another occurrence at `0x7fc42131` was inside machine instructions. The meaningful header decoded to:

| Value | Observed value |
| :--- | :--- |
| RNG seed | `0x6f2e1a53` |
| Bytecode offset | `0x80` |
| Bytecode length | `0x5b` |
| Source buffer offset | `0x180` |
| Destination buffer offset | `0x1c0` |
| Data length | `0x1e` (30 bytes) |

The interpreter code could be carved from file offset `0x21d3838` and disassembled as x86-64. Its handlers manipulated registers, loaded buffer bytes, performed arithmetic and XOR, and implemented a 32-bit linear congruential generator.

## Recover the surviving buffer

The critical correction in the solve was choosing the destination buffer. The source had been wiped; the VM's output buffer survived. Reading the wiped source produced the wrong input to the reversal even though the header and RNG seed were correct.

Reconstruct the interpreter's generator exactly, preserving 32-bit overflow and the byte-selection behavior. Advance the generator for each byte and reverse the XOR against the surviving destination region. This yielded the 30-byte flag above.

The historical script printed:

```text
header: 0x6f2e1a53 0x80 0x5b 0x180 0x1c0 0x1e
hiCTF{gh0st_pr0c3ss_rng_pwn3d}
```

## Evidence limits

This writeup reconstructs the recorded solve. The original standalone solver is no longer available in this workspace, so it is not included or presented as freshly rerun. The recorded recovery came from interpreting the VM and reversing its buffer transformation, not selecting a flag-shaped string from a strings dump.
