# VaultKeeper — local recovery, contest result disputed

**Category:** Android reverse engineering  
**Recovered locally:** 30 October 2026, Asia/Samarkand  
**Candidate:** `hiCTF{!!I_10v3_4ndr0!d_m4n_m4k!ng_th3m_f331_g0Od!!}`  
**Status:** locally consistent, but the user reported rejection. This is not included in the eight verified solves.

## Why this is separate

The original chat returned the candidate, then the user said “the flag is incorrect.” A later local checksum check matched the APK, but no later contest acceptance was recorded. That conflict must remain visible.

Archive SHA-256:

```text
7c0ccbd218561af27d1f51dcb18cf3ef5ab566e538788d88e285de1fb8d7aa10
```

## What was recovered

The APK contains `classes.dex`, `assets/vault.bin`, and architecture-specific `libvaultnative.so` libraries. It also contains decoy flags, so a strings scan alone was insufficient.

The investigation traced the Java claim pipeline and native bridge. The preserved loader performs:

```text
vault.bin
  -> nv_seed
  -> Java K1 word mixer
  -> nv_unseal
  -> Java K2 byte mixer
  -> nv_exec
  -> nv_final
```

The K1 mixer updates 128 32-bit cells for seven rounds, alternating traversal direction. It uses neighboring cells, rotations, and multiplication by `0x85ebca6b`. K2 derives 256-byte keystream blocks from those cells and XORs them into the 2048-byte unsealed payload.

The macOS loader maps the x86-64 ELF library, resolves its imports, and reproduces the Java transformations in C. It captures `nv_sync` output. It also bypasses an Android environment audit and clears an internal flags word before `nv_final`. Consequently, this is extraction through a modified execution environment, not proof that the unmodified Android app accepted the interaction.

The exact loader is preserved in `loader.c`, including those modifications. Its binary offsets and file paths are specific to this APK.

## Local integrity evidence

The recovered bytes produce:

```text
SHA256("VK-TAG-2026" || candidate)
= 62672db15a0b6a4793b351292f29a0b370783347eb3c973dc2e84c138facc1e1
```

The prefix matches the final-check constant recorded from the APK:

```text
62672db15a0b6a4793b351292f29a0b3
```

This calculation was repeated on 1 November:

```python
import hashlib

candidate = b"hiCTF{!!I_10v3_4ndr0!d_m4n_m4k!ng_th3m_f331_g0Od!!}"
digest = hashlib.sha256(b"VK-TAG-2026" + candidate).hexdigest()
assert digest.startswith("62672db15a0b6a4793b351292f29a0b3")
print(digest)
```

The spelling includes uppercase `I`, digit `1` in `10v3` and `f331`, and uppercase `O` in `g0Od`.

## Remaining uncertainty

The saved record does not establish why the contest rejected the candidate. Copying, challenge mismatch, an additional condition, or a decoy path cannot be resolved from the checksum alone. No accepted replacement is known from the reviewed chats.

**Source chat:** “Locate the file in Downloads”, `01a18d2d-f089-7cc3-97b8-51e3533733b3`.
