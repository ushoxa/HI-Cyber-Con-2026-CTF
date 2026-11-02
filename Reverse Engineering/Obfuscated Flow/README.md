# Sentinel Gateway / rev-obs-flow

**Category:** reverse engineering  
**Recovered:** 30 October 2026, Asia/Samarkand  
**Flag:** `hiCTF{m4th_c0ntr0l_fl0w_3ll1pt1c_dlog_4f7b2c9e}`  
**Evidence:** original checker accepted the input; a nearby incorrect input was rejected. Both checks were repeated on 1 November.

## Challenge

`rev-obs-flow.zip` contains an x86-64 ELF named `challenge`. It prints a “hiCTF Sentinel Gateway” banner and asks for a passkey.

Archive SHA-256:

```text
ddaca1f93d3f748482982814ed307b58f9fba73e6298bb4551594a2b344a2d30
```

The main function is at `0x4010c0`. Its control flow is flattened around a dispatcher, and the input checks use modular arithmetic instead of a single plaintext comparison.

## Recovery

The initial inspection used `file`, `strings`, and radare2. Useful commands were:

```sh
r2 -2 -Aqc 'afl; iz; pdc @ main' challenge
r2 -2 -qc 'pxw 192 @ 0x4030e0; px 128 @ 0x4031a0' challenge
```

The entry checks require a 46-byte string beginning with `hiCTF{` and ending with `}`. The 39 interior bytes are read in four-byte little-endian groups; the final group also contains the closing brace.

The dispatcher tables around `0x4030e0` distinguish successful states from deliberately invalid `...badc0d` states. Following the conditions feeding those tables is more useful than treating every flattened branch as an independent rule.

The arithmetic includes checks modulo `0x7fffffff`, `0xfffffffb`, and `1000000007`, plus an elliptic-curve point calculation and modular exponentiation. One inspected relation was:

```text
y² = x³ + 0x20a6e*x + 0x30730db7  (mod 1000000007)
```

The saved attempt used the constraints and readable phrase fragments to narrow candidate text, then ran the original checker. It did not preserve a standalone symbolic solver for every equation. This write-up therefore does not claim that a complete discrete-log derivation was saved.

The significant correction was `3ll1pt1c`, with a leading digit `3`. The similar `ell1pt1c` candidate failed. Swapping the two final four-character groups also failed.

## Running the checker on the Mac

The original solution used a small x86-64 loader because the supplied executable was an ELF rather than a macOS executable. The loader:

1. Mapped the ELF segments at their original virtual addresses.
2. Connected the imported C functions, including `strncmp`, `puts`, `strlen`, `printf`, `fgets`, and `fflush`.
3. Connected the `stdin` and `stdout` globals.
4. Called the original `main` at `0x4010c0`.

It did not patch the passkey predicates. The preserved source is `loader.c` and expects the executable at `work/obs-flow/challenge` relative to the working directory.

With that layout, the original build and run were:

```sh
clang -arch x86_64 -O2 -Wl,-no_pie -Wl,-pagezero_size,0x1000 \
  -o work/obs-flow/loader work/obs-flow/loader.c
printf '%s\n' 'hiCTF{m4th_c0ntr0l_fl0w_3ll1pt1c_dlog_4f7b2c9e}' \
  | work/obs-flow/loader
```

The loader is specific to this binary and macOS x86-64 execution support. On a compatible Linux environment, the original ELF can be run directly.

## Verification

The unmodified checker logic returned:

```text
[+] ACCESS GRANTED! Passkey verified.
[+] Flag: hiCTF{m4th_c0ntr0l_fl0w_3ll1pt1c_dlog_4f7b2c9e}
```

The otherwise identical candidate containing `ell1pt1c` returned `[-] Access Denied.` This distinguishes a working passkey from a plausible phrase.

**Source chat:** “Locate the file in Downloads”, `01a18d2d-f089-7cc3-97b8-51e3533733b3`. Contest submission was not recorded.
