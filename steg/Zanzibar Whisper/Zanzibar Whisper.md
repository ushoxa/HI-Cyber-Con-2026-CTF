# Zanzibar Whisper

**Category:** Steganography  **Flag:** `hiCTF{sp1c3_1sl4nd_s3cr3ts}`

> A mysterious image from the shores of Zanzibar has surfaced. Locals say it carries a hidden message — a whisper from the Spice Island. Can you uncover its secret?

File: `zanzibar-whisper.zip` → `zanzibar_whisper.jpg`

## Solution

1. EXIF data, `strings` and `binwalk` show nothing interesting (see `artifacts/exiftool.txt`).
2. A JPEG "whisper" suggests steghide. `steghide info` with an **empty passphrase** already lists the payload:

   ```
   embedded file "zanzibar_flag2.txt": size 28 bytes, encrypted rijndael-128 cbc, compressed
   ```

3. Extract it:

   ```
   steghide extract -sf zanzibar_whisper.jpg -p ""
   cat zanzibar_flag2.txt   # hiCTF{sp1c3_1sl4nd_s3cr3ts}
   ```

The data is "encrypted", but the passphrase is the empty string, so trying `-p ""` first is all it takes.

## Files
- `solve/solve.sh` is the steghide extraction
- `artifacts/zanzibar_flag2.txt` is the extracted hidden file
- `artifacts/exiftool.txt` is the image metadata (nothing hidden there)
- `challenge/` has the original zip
