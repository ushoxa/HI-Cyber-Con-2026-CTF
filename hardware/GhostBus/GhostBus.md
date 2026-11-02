# Ghost Bus

**Category:** Hardware / Embedded RE  **Flag:** `hiCTF{gh0st_bu5_uart_n0nc3_r3v3al_9c3f12}`

> A smart-lock sensor hub was pulled from a decommissioned site. The vendor insists the secure element is locked and the sealed region cannot be read. A field engineer probed the hub's internal UART bus between the MCU and the secure element, and separately dumped the hub's external SPI NOR flash… Recover the hidden read, reverse the key derivation and open the sealed region. No brute force needed.

Files: `ghost_bus.zip` → `capture.csv`, `capture.vcd` (UART logic capture), `diagram.png` (board/protocol notes), `firmware.elf` (STM32F103, stripped), `flash_dump.bin` (1 MB SPI NOR)

## Solution

### 1. The hidden read (UART capture)
`diagram.png` gives the frame format `AA 55 | LEN | CMD | PAYLOAD | CRC16-LE` (CRC16-Modbus over LEN|CMD|PAYLOAD). It also gives the flash map: the sealed region is at `0x6A000` (48 bytes) and board metadata is at `0x7F000`.

In `capture.csv`:

| channel | bytes | meaning |
|---|---|---|
| 0 hub→SE | `AA 55 0C 01 "GB2.2 SE OK!" crc` | status |
| 0 hub→SE | `AA 55 00 10 00 7C` | **CMD 0x10**, no payload: the undocumented "read nonce" |
| 1 SE→hub | `AA 55 10 10 <16 bytes> F3 E2` | the nonce |

```
nonce = 9e3b7a44 c1d05f82 a6e1b490 7cd3f5a2
```

### 2. Key derivation (firmware.elf)
The `.rodata` contains the SHA-256 K constants and the AES S-box, inverse S-box and Rcon, plus a 24-byte blob at `0x08000ca0`: `04325a9c117f3da0 c0ffee5aa55a00ff 1234567890abcdef`.

The command handler at `0x08000380` (radare2, Thumb, Cortex-M; see `artifacts/fcn_08000380_cmd_handler.asm`):

1. waits for maintenance-open (CMD `0x55`)
2. sends CMD `0x10` to the SE and reads the 16-byte nonce (checks LEN = 16)
3. `SHA256_init → update(secret, 24) → update(nonce, 16) → final`
4. SPI-reads 48 bytes from `0x06A000` (opcode `03 06 A0 00`)
5. **byte-reverses every 32-bit word** of that ciphertext
6. key expansion copies **only 16 bytes** of the digest and builds 11 round keys (176 bytes), so it's **AES-128**
7. `fcn.08000bdc` is textbook **CBC decrypt** with IV = nonce
8. checks PKCS#7, then checks the plaintext starts `hiCTF{` and ends `}`

### 3. Open the sealed region

```
key = SHA256(secret ‖ nonce)[:16] = 664ecd32a0a21d02a90afb1efb6919b1
iv  = nonce
ct  = flash[0x6A000:0x6A030] with each 4-byte word reversed
AES-128-CBC-decrypt → hiCTF{gh0st_bu5_uart_n0nc3_r3v3al_9c3f12} + 07×7
```

The one trap is the per-word byte swap: decrypting the raw flash bytes gives garbage (the solver shows both).

## Files
- `solve/solve.py` takes the secret from the ELF and the nonce from the CSV, derives the key, swaps the words and decrypts (uses `openssl`)
- `artifacts/sealed_region_0x6A000.bin` is the 48-byte sealed ciphertext from the flash
- `artifacts/board_metadata_0x7F000.bin` is the board metadata (`GB-HUB-01 rev C`, `fw=2.2.0`, `sealed=0x6A000 len=48`)
- `artifacts/fcn_08000380_cmd_handler.asm` is the radare2 disassembly of the command handler
- `artifacts/capture.csv`, `artifacts/diagram.png` are the UART capture and the protocol diagram
- `artifacts/solver_output.txt` shows the swapped-word and raw decryptions
