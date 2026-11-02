# hiCTF — Operation Chimera (Forensics / Network)

> Our SOC team detected suspicious traffic from an internal engineering system. Analyze the provided file, investigate the suspicious activity, and find the flag.
>
> `operation_chimera.zip` — SHA-256 `2f54e06473ae4ef3356a013209e402c26a88c000d630d73cece634865be453a0`

**Flag:** `hiCTF{0daaY_c1tTy_0f_pcAP_1s_nN1C3_looK!!!}`

## TL;DR

1. A workstation leaks a file over DNS. 136 queries for `sync-NNN.telemetry.corp.internal` each carry 266 bytes in a custom EDNS0 option starting with `CHIM`, and they're sent in shuffled order.
2. Each chunk is `[nonce 2][CRC16 2] ‖ Enc(seq 2 ‖ data 256)`. 31 chunks share CRC `0x41e8`, which is the CRC-16/CCITT-FALSE of 256 zero bytes. Those chunks are encrypted zeros, so their ciphertext is the raw keystream (known plaintext for free).
3. The keystream is `HMAC-SHA256(K, nonce ‖ counter)`. `K` is the **ServerHello random** from a fake TLS handshake with `delta.corp.internal`, which the SOC alert points at.
4. Decrypting and reordering the chunks gives a stripped x86-64 ELF that checks a flag. Its check is invertible: a GF(2⁸) LFSR, an S-box, an add, a rotate, and XOR chaining. Inverting it gives the flag.

There are a lot of decoys, including the fake flag `hiCTF{17s_A_f@K3_FlAG!!!}` planted five times.

---

## 1. Triage

The archive holds one file, `operation_chimera.pcap`: 159k packets, 238 MB, 26 seconds. Everything comes from one host, **10.142.18.105** (`dev-ws-davis`, a DevSecOps workstation according to the alert).

```
tshark -r operation_chimera.pcap -q -z io,phs
tshark -r operation_chimera.pcap -q -z conv,ip
```

Most of the traffic is noise:

| Traffic | What it is |
|---|---|
| 230 MB from `142.250.190.46` (`googlevideo.com`) | "YouTube" range requests. The body is one ~1.5 KB block repeated, which is why the pcap compresses about 50× |
| `web-prod01` | ffuf scan, LFI/XSS/cmdi probes, 5 failed admin logins |
| `api-prod01` | sqlmap UNION injection dumping `users` |
| `staging-app02:8080` | PNG/JPG/GIF, PDF, zips, WAV/MP3, a 2.8 MB SQL dump, a telemetry CSV, `SEC-ALERT-49102.json` |
| `github.com` | `git-upload-pack` response: a decompression bomb (11.9 MB of one repeated Python stub plus 17 MB of one repeated 4 KB block) |
| FTP, SSH banners, Redis PING, PG SSLRequest, syslog, 50 NTP queries | filler |
| `10.142.18.250:443` | **one TLS ClientHello/ServerHello, then RST** |
| DNS to `10.142.18.1` | **~120 normal lookups mixed with 136 `sync-NNN.telemetry.corp.internal` queries that get no responses** |

The alert served over HTTP explains the setup:

```json
"event_type": "HIGH_FREQUENCY_DNS_TUNNEL_SUSPECT",
"source_ip": "10.142.18.105", "destination_ip": "10.142.18.1",
"notes": "NetFlow collector also noted a prior brief TCP/443 connection from the same host
          to infrastructure node delta.corp.internal (10.142.18.250). ..."
```

So the plan is: the DNS burst is the exfiltration and the TLS session holds the key.

## 2. The DNS tunnel

The tunnel queries are 270-byte UDP packets. The data is in the OPT record:

```
0060  00 00 29 10 00 00 00 80 00 01 0e fd e9 01 0a 43 48 49 4d bc   ..)............CHIM.
      │  │     │     │           │     │     │     └ "CHIM" + 262 bytes
      │  │     │     │           │     │     └ option length 0x010a = 266
      │  │     │     │           │     └ option code 0xfde9 = 65001 (private use)
      │  │     │     │           └ RDLEN 270
      │  │     │     └ ext-RCODE/ver/DO
      │  │     └ UDP size 4096
      │  └ TYPE OPT
      └ root
```

```
tshark -r operation_chimera.pcap -Y 'dns.qry.name contains "telemetry"' \
       -T fields -e frame.number -e udp.srcport -e dns.qry.name -e udp.payload > dns.tsv
```

What I saw:

- 135 payloads are 262 bytes after `CHIM` and one is 134 bytes. The short one, the obvious last chunk, is at capture index 55, so **the chunks were sent shuffled**.
- The qname numbers, source ports and timing don't give the order. Five qnames repeat with different payloads.
- The payload bytes look uniformly random, except that **bytes 2–3 equal `41 e8` in 31 of the 136 chunks**.

### The `41e8` trick

If a field had the same ciphertext under 31 different keystreams, that would be suspicious. A cleartext field taking the same value is easy to explain. Sizes suggested `262 = 6 + 256` and `134 = 6 + 128`, so I checked whether `0x41e8` is a common checksum of a constant 256-byte block:

```python
>>> crc16_ccitt_false(b"\x00" * 256)   # poly 0x1021, init 0xFFFF, no reflection, xorout 0
0x41e8
```

It matches exactly. Bytes 2–3 are the **CRC-16/CCITT-FALSE of the plaintext data**, sent in the clear. The 31 matching chunks are blocks of zeros from the exfiltrated file (padding inside an ELF), so **their ciphertext is the keystream itself**. That gives about 8 KB of known keystream, each piece tied to a known 2-byte header value.

## 3. Recovering the cipher

Since I had pure keystream, I could test generator guesses directly:

- **Plain LFSR?** Berlekamp–Massey on a zero chunk gives linear complexity ≈1024 out of 2048 bits. Running BM separately on each bit position of the bytes also gives the maximum. So it isn't any LFSR or other GF(2)-linear generator, and not a CSS-style add-with-carry combiner (whose low bit would stay linear). The khanacademy "Modular Arithmetic & LFSR Sequences" response was a lure here. The LFSR shows up later, in the binary.
- **No overlap** between keystreams of different chunks, so each chunk is keyed separately by its nonce (bytes 0–1).
- **AES-CTR/CBC/CFB keyed with the TLS material?** For CTR, decrypting a known keystream block with ECB under the right key should reveal a structured counter block. None of the candidate keys did.
- **Hash/HMAC counter mode?** I swept `H(key ‖ nonce ‖ ctr)` and `HMAC(key, nonce ‖ ctr)` over candidate keys, nonce slices and counter encodings, looking for matches inside the keystream:

```
HMAC HIT sha256  key=ServerHello.random  msg=nonce(2) ‖ ctr=0x0001  -> found at payload offset 36
```

The TLS handshake to `delta.corp.internal` is built by hand. The ClientHello has `random = "G"×32`, `session_id = 0x88×32`, SNI `delta.corp.internal`, and only one cipher suite. The ServerHello `random` is the real value:

```
3c891e45aad02f81b7649e125088da7c913247f008c3296b8a714e5d2319bb04
```

Counter 1 lands at offset 36, so counter 0 starts at offset 4. XORing that block against a zero chunk leaves `00 5f 00 00 …`, i.e. a 2-byte **sequence number** (95) at the start of the encrypted region. Final chunk layout:

```
offset  0      2        4       6                                 262
        ┌──────┬────────┬───────┬──────────────────────────────────┐
        │nonce │ CRC16  │  seq  │           data (256)             │
        └──────┴────────┴───────┴──────────────────────────────────┘
          clear   clear  └────── XOR keystream ───────────────────┘
keystream = HMAC-SHA256(ServerRandom, nonce‖0x0000) ‖ HMAC(…, nonce‖0x0001) ‖ …
CRC16 = CRC-16/CCITT-FALSE(data)
```

All 136 chunks decrypt, every CRC checks out, and the sequence numbers cover 0–135 exactly. The reassembled 34,688 bytes are:

```
exfil.bin: ELF 64-bit LSB pie executable, x86-64, static-pie linked, stripped
```

## 4. Reversing the payload

> I analyzed the binary statically only and never ran it.

`strings` shows a banner (`OPERATION CHIMERA // HARDWARE SECURITY ENCLAVE`), the fake flag again under "Hardware trace probe detected… Key Token:", and `Usage: %s <flag_candidate>`.

`main` (at `0x1090`):

1. Calls `ptrace(PTRACE_TRACEME)`. If it fails (debugger attached), it prints the "trace probe" message with the **decoy flag** and exits.
2. Requires `strlen(argv[1]) == 0x2b` (43), `strncmp(argv[1], "hiCTF{", 6) == 0` and `argv[1][42] == '}'`.
3. Calls the checker at `0x1580` and prints `[SUCCESS] … Flag Confirmed` if it returns 1.

The checker:

```asm
1581  movzx ecx, byte [0x9008]      ; state = 0xa5   (.data, file offset 0x8008)
158d  mov   edi, 13                 ; add constant
1598  mov   esi, 0x5c               ; chain byte
159d  lea   r10, [0x6280]           ; S-box (a permutation)
15a4  lea   r9,  [0x6240]           ; 43-byte target
15b0  lea   eax, [rcx+rcx]          ; state <<= 1
15b5  xor   ebx, 0x1d               ;   ^ 0x1d if the top bit was set   (GF(2^8) xtime / Galois LFSR)
15bf  xor   al, [r11+rdx]           ; state ^ flag[i]
15c6  movzx ebx, byte [r10+rax]     ; sbox[...]
15cb  add   ebx, edi                ; + (13 + 7i)
15cf  rol   al, 3
15d2  xor   eax, esi                ; ^ previous target byte
15d9  cmp   sil, al                 ; == target[i] ?
15e3  add   edi, 7
```

Forward, per byte:

```
state   = xtime(state)                        # poly 0x11d, starts at 0xa5
target[i] = rol8((sbox[state ^ flag[i]] + 13 + 7i) & 0xff, 3) ^ target[i-1]   # target[-1] = 0x5c
```

Every step can be reversed (the S-box is a bijection), so:

```
flag[i] = sbox⁻¹[(ror8(target[i] ^ target[i-1], 3) - (13 + 7i)) & 0xff] ^ state_i
```

That gives `hiCTF{0daaY_c1tTy_0f_pcAP_1s_nN1C3_looK!!!}`. Re-running the forward check in Python on this value matches all 43 target bytes.

## 5. Decoys and red herrings

| Where | What |
|---|---|
| `/qa/audit/reports/sso_idp_matrix.html` | `hiCTF{17s_A_f@K3_FlAG!!!}` in a test-fixture row |
| `devops_deployment_configs.zip` → `env/staging.env` | `AUTH_TEST_SECRET="hiCTF{17s_A_f@K3_FlAG!!!}"` |
| `ivr_call_hold_tone.wav` | 750 Hz Morse code → `HICTF(17S_A_F@K3_FLAG!!!)` |
| `exfil.bin` | the same fake flag in the ptrace anti-debug branch |
| `security_soc_workflow_diagram.png` | identical to `cluster_dashboard_q3.png` except the IHDR CRC is `DEADBEEF`, which leads nowhere |
| `refs?service=git-upload-pack` | zlib decompression bomb |
| YouTube stream, MP3, CSV, SQL dump, other images | repeated filler, nothing hidden (checked LSBs, trailers, metadata, PNG chunk CRCs) |
| "Personal browsing" JSON (Coursera *Cryptography Fundamentals*, Khan Academy *Modular Arithmetic & LFSR Sequences*) | thematic hints. The LFSR is in the checker, not the tunnel cipher |

## 6. Solver

The script goes from the pcap to the flag in one run. It needs `tshark`.

> Note: this combined script merges the two scripts that produced the flag during the solve (decrypt/reassemble and checker inversion). The original challenge files were gone when I wrote this up, so the merged version hasn't been rerun as one piece.

```python
#!/usr/bin/env python3
# Operation Chimera solver: pcap -> decrypted ELF -> flag
# usage: python3 solve_chimera.py operation_chimera.pcap
import hashlib, hmac, subprocess, sys

PCAP = sys.argv[1]
# ServerHello.random from the fake TLS handshake with delta.corp.internal (10.142.18.250)
KEY = bytes.fromhex("3c891e45aad02f81b7649e125088da7c913247f008c3296b8a714e5d2319bb04")

def crc16_ccitt_false(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

# 1. pull the UDP payloads of the tunnel queries
out = subprocess.run(["tshark", "-r", PCAP, "-Y", 'dns.qry.name contains "telemetry"',
                      "-T", "fields", "-e", "udp.payload"], capture_output=True, text=True, check=True).stdout

chunks = {}
for line in out.split():
    pkt = bytes.fromhex(line)
    i = pkt.find(b"CHIM")                      # EDNS0 option 0xfde9 data starts with "CHIM"
    optlen = int.from_bytes(pkt[i-2:i], "big")
    body = pkt[i+4:i+optlen]                   # [nonce 2][crc16 2][enc(seq 2 + data)]
    nonce, crc, ct = body[:2], int.from_bytes(body[2:4], "big"), body[4:]
    ks = b"".join(hmac.new(KEY, nonce + c.to_bytes(2, "big"), hashlib.sha256).digest()
                  for c in range(len(ct) // 32 + 1))
    pt = bytes(a ^ b for a, b in zip(ct, ks))
    seq, data = int.from_bytes(pt[:2], "big"), pt[2:]
    assert crc16_ccitt_false(data) == crc, f"CRC mismatch on seq {seq}"
    chunks[seq] = data

elf = b"".join(chunks[k] for k in sorted(chunks))
open("exfil.bin", "wb").write(elf)
print(f"[+] {len(chunks)} chunks, {len(elf)} bytes -> exfil.bin")

# 2. invert the flag checker at 0x1580
sbox, tgt = elf[0x6280:0x6380], elf[0x6240:0x6240 + 43]
inv = {v: i for i, v in enumerate(sbox)}
state, prev, add, flag = 0xA5, 0x5C, 13, bytearray()
for i in range(43):
    state = ((state << 1) ^ 0x1D) & 0xFF if state & 0x80 else (state << 1) & 0xFF
    x = tgt[i] ^ prev
    t = ((x >> 3) | (x << 5)) & 0xFF           # undo rol 3
    flag.append(inv[(t - add) & 0xFF] ^ state)
    prev, add = tgt[i], add + 7
print("[+] flag:", flag.decode())
```

## Takeaways

- **Fields that repeat across packets reveal structure.** One cleartext CRC turned an unknown cipher into a known-plaintext problem.
- **Follow the alert's side note.** The "brief TCP/443 connection" was the key exchange. The ServerHello random was the only non-filler value in the handshake.
- **Test hints against the data.** Berlekamp–Massey ruled out an LFSR tunnel cipher within minutes, so I stopped chasing it.
- The challenge throws a lot at you on purpose: 230 MB of filler, a decompression bomb, Morse audio, and the same fake flag five times. Don't submit the first `hiCTF{` you find.

## Folder contents
- `solve/solve_chimera.py` runs pcap → decrypt 136 DNS-tunnel chunks → `exfil.bin` → inverts the flag checker
- `artifacts/exfil.bin` is the recovered exfiltrated file (stripped static-PIE x86-64 ELF holding the flag checker)
- `artifacts/dns_tunnel_queries.tsv` has all 136 `sync-NNN.telemetry.corp.internal` queries (frame, time, name, raw UDP payload with the `CHIM` EDNS0 option)
- `artifacts/fake_tls_serverhello.tsv` is the staged ServerHello from `delta.corp.internal`; its random field is the HMAC key
- `artifacts/http_objects/` holds the small HTTP objects exported from the capture (decoys, `SEC-ALERT-49102.json`, `sso_idp_matrix.html` with the fake flag, and so on). Objects over 300 KB, which are only repeated filler, were left out.
- `artifacts/solver_output.txt` is the solver output
