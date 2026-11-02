# Roof of Africa

**Category:** Steganography / OSINT  **Flag:** `hiCTF{h4kun4_m4t4t4_m34ns_n0_w0rr13s}`

> They say Africa's highest peak holds ancient secrets in its frozen glaciers. A photograph has been intercepted — but its true meaning is locked away, protected by the mountain's most famous number. Can you reach the summit and uncover what lies hidden?

File: `roof-of-africa.zip` → `roof_of_africa.jpg`

## Solution

1. "Africa's highest peak" is **Mount Kilimanjaro**. Its "most famous number" is its height: **5,895 m** (19,341 ft).
2. "Locked away" in a JPEG suggests steghide with a passphrase. `5895` works:

   ```
   steghide info roof_of_africa.jpg -p 5895
     embedded file "roof_flag_v2.txt": 38 bytes, rijndael-128 cbc, compressed
   steghide extract -sf roof_of_africa.jpg -p 5895
   → hiCTF{h4kun4_m4t4t4_m34ns_n0_w0rr13s}
   ```

("Hakuna matata" is Swahili, which fits the Tanzania/Kilimanjaro theme.)

## Files
- `solve/solve.sh` is the steghide extraction
- `artifacts/steghide_extracted.txt` is the hidden file
- `artifacts/exiftool.txt` is the image metadata
