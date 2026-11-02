# Whispers in the Margin

**Category:** Steganography  **Flag:** `hiCTF{573g4n0gr4phy_!5_fun}`

> Sometimes the most crucial details are right in front of you, hidden where no one bothers to look. Inspect the provided documents closely—what appears empty might hold the key to unravelling the final secret.

Files: `whispers-in-the-margin.zip` → `chall/chall.jpg`, `chall/Those numbers are process counts.docx`

## Solution

### Layer 1: whitespace stego in the Word document
The visible text of the `.docx` is a harmless chat answer about browser process counts (`artifacts/docx_visible_text.txt`). After it, the document has a run of paragraphs that **look empty** but contain only spaces and tabs ("what appears empty might hold the key").

From `word/document.xml`, every such paragraph ends in 8 whitespace characters. Read them as bits, with **space = 0** and **tab (`<w:tab/>`) = 1**. Each paragraph gives one ASCII byte:

```
haha! u got me, now what?
```

It reads like a taunt, but it is the key for the next layer.

### Layer 2: steghide in the JPEG
`chall.jpg` doesn't open with an empty steghide passphrase. The decoded taunt works:

```
steghide extract -sf chall.jpg -p "haha! u got me, now what?"
→ hiCTF{573g4n0gr4phy_!5_fun}
```

## Files
- `solve/docx_whitespace.py` decodes the space/tab bits from the docx
- `solve/solve.sh` runs the full chain (docx → key → steghide)
- `artifacts/document.xml` is the raw document XML (the whitespace paragraphs are at the end)
- `artifacts/docx_visible_text.txt` is the visible decoy text
- `artifacts/steghide_extracted.txt` is the extracted flag file
