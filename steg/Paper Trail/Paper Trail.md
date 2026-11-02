# Paper Trail

**Category:** Forensics / Steganography (PDF)  **Flag:** `hiCTF{n3w_ar34_fOr_hid!ng_d4t4_n4m3d_TJ}`

> The document passed its final review without raising any concerns. What was submitted appeared complete, and nothing seemed out of place. But the archived copy tells a different story. Some changes leave no visible trace. Your task: Investigate the provided artifact and recover the flag.

File: `paper-trail.zip` → `chall.pdf` (a real published academic paper, 6 pages)

## Solution

### 1. Things that looked wrong but weren't the answer
- The XMP metadata claims 13 pages but the PDF has 6.
- There's one `/ActualText` entry and a font with a custom `/Differences` encoding that includes `braceleft`.

Neither led anywhere.

### 2. Diff against the archived original
The hint says "the archived copy tells a different story", so I pulled the original paper from the Wayback Machine and compared the two files. The visible text is **identical**. The challenge PDF has 7 more objects (183 vs 176). After matching objects by content (the object numbers were reshuffled), the only real difference is **four extra page content streams** (objects 179–182).

### 3. What those streams contain
Each added stream draws text in **render mode `3 Tr` (invisible)**, and every string it draws is empty (`()`). So nothing appears on the page, and all the data sits in the **kerning numbers of the `TJ` arrays**:

```
3 Tr ... [ 24 () 24 () 174 () 4 () 89 () 136 () ... ] TJ
```

The flag's own text, "data named TJ", points at exactly this.

- In 3 of the streams, one TJ row is much longer than the others and holds only values 0–255.
- Dropping the first two numbers of each long row leaves 21 + 21 + 22 = **64 bytes**, which is four AES blocks.
- The short rows, and the whole 4th stream, are filler.

### 4. Decrypting
The key and IV come from the PDF's own history, its trailer `/ID` array:

| | value |
|---|---|
| AES-128 key | `/ID[0]` = `e3b51a3ba231502d79c55593eb522037` |
| CBC IV | `/ID[1]` = `6749db1175e3e659a640695dcc830c82` |

I found the key by trying the `/ID` values from both PDFs with ECB on blocks 2–4 and looking for readable text. The IV was the other `/ID` entry. The plaintext is:

```
'CTF1' 00 28 | hiCTF{n3w_ar34_fOr_hid!ng_d4t4_n4m3d_TJ} | 8-byte tag | padding
 magic    len=40
```

## Files
- `solve/solve.py` decompresses the PDF with `mutool`, finds the `3 Tr` streams, pulls the TJ numbers and decrypts with the trailer IDs
- `artifacts/chall_decompressed.pdf` is the PDF with all streams decompressed
- `artifacts/hidden_stream_obj179..182.txt` are the four injected invisible-text content streams
- `artifacts/solver_output.txt` is the solver output
