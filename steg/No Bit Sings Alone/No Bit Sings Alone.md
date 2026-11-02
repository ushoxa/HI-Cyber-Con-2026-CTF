# No Bit Sings Alone

**Category:** Audio steganography / Crypto  **Flag:** `hiCTF{m4th3m4t!c5_g4v3_m3_4_l0t_Of_p4!n_8d52ae513}`

> A suspicious audio file. Nothing more. Or maybe that is exactly what it wants you to think. Listen carefully. Look deeper.

Files: `no-bit-sings-alone.zip` → `suspicious.wav` (stereo, 16-bit, 44.1 kHz, 2,635,988 frames); `hints.zip` → `hints.txt`

## Solution

### 1. Spectrogram text (both channels, ~0.7–5 s, 7–18 kHz)
A tone-bitmap text block (`artifacts/spectrogram_text_0-5s.png`) reads:

```
AES256GCM
N=99CB9C49E4C83527CE6F89D9                 ← 12-byte GCM nonce
C0=8A845BA500DE25B749F1FF63CCFF
C1=9D2D9FD8D2614E19BCA42CC7E438
C2=B31407AE896311C3AADCF9327610
C3=478444A09EF6FE3650DF7EBEC3B7
C4=1FF18CF0EB728DBFA791B7485D76
C5=7172AE8493A8715210B5                     ← 80 bytes = 64-byte ciphertext + 16-byte tag
```

That gives the cipher, nonce and ciphertext, but not the key.

### 2. Tone guide (right channel, blocks 585–642)
The last 58 blocks of 4096 samples (from sample 0, ending at the last complete block) each hold **one pure tone**. Its peak FFT bin `k` is always odd (1305–1801). These are the step sizes. All 58 are listed in `artifacts/tone_guide_bins.txt`.

### 3. Sample selection + parity (left channel)
The hint says to use the bin as a step for choosing samples in the *other* channel, with positions wrapping around inside each block.

For block `b` with step `k`, take the LSBs of the left-channel samples at

```
pos_j = b·4096 + ((j+1)·k mod 4096),   j = 0..30          (31 bits per block)
```

Reading those bits directly gives noise. They are a **Hamming(31,26) codeword**, and the message is the **syndrome**: XOR the column index of every set bit. The block's frequency also **shifts the parity layout**, so bit `j` gets column `(j − k) mod 31 + 1`. Each block then yields a 5-bit syndrome, MSB first.

58 blocks × 5 bits = 290 bits (288 used, 2 left over).

### 4. Finite field + inverse NTT
- Group the bits into **32 nine-bit values**. They are all ≤ 256, so they are elements of **GF(257)**.
- They are an NTT of length 32 over GF(257). Applying the **inverse NTT** (root `136`, then multiplying by `32⁻¹ mod 257`) gives 32 values that are all < 256. That is the AES-256 key:

```
8da8dca0aa79a8a2b1e1aef181e98e63fcca7da26d49d6dbffdb461e3ecd544d
```

### 5. Decrypt
AES-256-GCM with the spectrogram nonce authenticates and decrypts:

```
00 32 | hiCTF{m4th3m4t!c5_g4v3_m3_4_l0t_Of_p4!n_8d52ae513} | padding
len=50
```

### What made it findable
There are many plausible variants (selection order, column offset, bit order, which channel). The quick filter was **"all 32 nine-bit values ≤ 256"**. A wrong configuration passes that with probability about 2⁻³². Only the correct layout passed, so I knew it was right before even trying the GCM tag.

## Files
- `solve/solve.py` is the full solver (tone bins → LSB selection → Hamming syndromes → GF(257) inverse NTT → AES-GCM)
- `artifacts/spectrogram_text_0-5s.png` is the spectrogram of the text block
- `artifacts/tone_guide_bins.txt` has the peak bin per guide block
- `artifacts/hints.txt` is the official hint
- `artifacts/solver_output.txt` has the GF(257) values, the key and the decrypted plaintext
- `challenge/` has the original zip and `hints.zip`
