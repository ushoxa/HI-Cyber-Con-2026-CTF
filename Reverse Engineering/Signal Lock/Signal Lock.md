# Signal Lock

**Category:** Reverse Engineering (Erlang/BEAM)  **Flag:** `hiCTF{b34m_byt3c0d3_n3v3r_l13s_s3ss10n_unl0ck3d}`
**Accepted token:** `g4m30v3r` (8 bytes, leetspeak "game over")

> Vaelorhand Online guards its ranked ladder with a server-side anti-cheat module… the anti-cheat ships as a single compiled, stripped .beam module with no source. A build leaked. Recover the one token the validator accepts; accepting it unlocks the flag. `signal_lock:verify(YourToken)` → `{ok, <<"hiCTF{...}">>}`

File: `signal-lock.zip` → `signal_lock.beam` (1,215 bytes)

## Solution

### 1. Unpack the module
- The `.beam` starts with `1f 8b`. It's gzip-compressed, which the BEAM loader accepts transparently.
- Decompressed, it's a normal `FOR1 … BEAM` IFF container with the chunks `Line Type AtU8 Code StrT ImpT ExpT LitT Meta`.
- Even stripped, the **atom table** gives away the algorithm's shape: `verify, ensure_exactly, transform, bxor, *, band, +, rotl, bsl, bsr, bor, unlock, keystream, sha256, crypto, hash, cipher`.
- The **literal table** (`LitT`, zlib-compressed) holds `{error,locked}`, `{error,bad_token}` and a **48-byte binary**, which is the encrypted flag.

### 2. Disassemble
There was no Erlang on the box and no root, so I ran `apt-get download` on `erlang-base` + `erlang-crypto`, unpacked them with `dpkg-deb -x` into a local prefix, and called `erlexec` through a small launcher. `beam_disasm:file/1` then gave the full symbolic disassembly:

```erlang
verify(<<N:64/big>>) ->                        % exactly 8 bytes, else {error,bad_token}
    case transform(N) of
        12675316763487955908 -> {ok, unlock(N)};
        _                    -> {error, locked}
    end.

transform(X) ->                                % all 64-bit, all bijective
    X1 = X bxor 16#A5A5…  (C1 = 11936128517019425370)
    X2 = X1 * 16#9E3779B97F4A7C15 mod 2^64     (golden-ratio constant, odd ⇒ invertible)
    X3 = rotl(X2, 29)
    X4 = X3 + 16#0123456789ABCDEF mod 2^64
```

### 3. Invert `transform`
Every step is a bijection on 64-bit words, so the target can be inverted directly with no brute force:

```
N = ((rotr(T − C3, 29)) · C2⁻¹ mod 2^64) ⊕ C1 = 0x67346d3330763372 = "g4m30v3r"
```

### 4. Unlock
`unlock(N)` XORs the 48-byte literal with a keystream made of SHA-256 blocks:

```
keystream = SHA256(<<N:64>> ‖ <<0:32>>) ‖ SHA256(<<N:64>> ‖ <<1:32>>)
flag      = cipher ⊕ keystream[0:48]
```

During the CTF I confirmed it with the real module: `signal_lock:verify(<<"g4m30v3r">>)` → `{ok,<<"hiCTF{b34m_byt3c0d3_n3v3r_l13s_s3ss10n_unl0ck3d}">>}`. Any other input returns `{error,locked}`. `solve/solve.py` reproduces it in pure Python.

## Files
- `solve/solve.py` parses the BEAM (gzip, chunks, atoms, literals), inverts `transform`, decrypts the flag
- `artifacts/solver_output.txt` is the chunk list, atoms, cipher literal, token and flag
