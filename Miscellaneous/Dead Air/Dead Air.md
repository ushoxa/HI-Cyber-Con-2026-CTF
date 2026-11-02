# Dead Air

**Category:** Miscellaneous · **Event:** HI Cyber Con 2026

> Status: the message was recovered, but the recorded conversation did not confirm an accepted final flag. The first uppercase submission was reported wrong; lowercase was subsequently suggested. Preserve this distinction when reproducing the solve.

## Inspect both channels

The supplied `dead-air.zip` had SHA-256 `dfe73eb9bb3fc8e02e4f5fa5dddbd6689791d9eb49f7d042941d3e31df55637f`. It contained a recording, `kestrel_last_recording.wav`, and an encrypted archive, `kestrel_logbook.7z`.

A separate spectrogram for each stereo channel was essential. The right channel visually spelled `KSTR-7742-VXQ`. Using that exact text as the 7z password opened the logbook, exposing `logbook_page.png` and `operator_codepad.png`.

```bash
7z x -pKSTR-7742-VXQ -ologbook kestrel_logbook.7z
```

The left channel carried a timed tone sequence. Band-pass filtering around 600–800 Hz and measuring a smoothed amplitude envelope separated dots, dashes, character gaps, and word gaps. The recorded decoder used a 0.15-second threshold for marks and character gaps and 0.4 seconds for word gaps.

The Morse decoded to:

```text
KESTREL STATION OFF AIR KEY IS NIGHTJAR LISTEN WITH YOUR EYES
```

## Decode the symbols

Transcribe the logbook's 28 glyphs in numbered order using the operator code pad. This yielded `59R_6L3Q9BYGBQ3QZAYZMP3QIZ92`. The key is `NIGHTJAR`; the alphabet includes digits and underscore, so ordinary 26-letter Vigenere is insufficient.

```python
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
ciphertext = '59R_6L3Q9BYGBQ3QZAYZMP3QIZ92'
key = 'NIGHTJAR'
message = ''.join(
    alphabet[(alphabet.index(c) - alphabet.index(key[i % len(key)])) % len(alphabet)]
    for i, c in enumerate(ciphertext)
)
assert message == 'S1L3NC3_W4S_TH3_M3SS4G3_6R3V'
print('hiCTF{' + message.lower() + '}')
```

## Flag candidate and caveat

```text
hiCTF{s1l3nc3_w4s_th3_m3ss4g3_6r3v}
```

The decoding is reproducible from the transcription above. Lowercasing the message was a proposed submission correction, not something demonstrated by an acceptance response in the available history.
