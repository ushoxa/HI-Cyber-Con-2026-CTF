# Tasmota Vault

**Category:** firmware forensics / cryptography  
**Recovered:** 30 October 2026, Asia/Samarkand  
**Flag:** `hiCTF{b3rry_r0t4t10n_c94934d76344ab1151e03afd}`  
**Evidence:** AES-GCM authentication succeeded for epoch 8 and failed for epoch 7. Reproduced on 1 November.

## Challenge

The lab archive contains a 4 MiB ESP32 flash image, an MQTT packet capture, and pinned Tasmota source. Its recovery note identifies Tasmota 15.6.0, LittleFS disk format 2.0, and Berry bytecode v4 with 32-bit integers and floats.

Archive SHA-256:

```text
74e01ec638452b8674b70301a8270fe8607950737ca1c7a7dc3f5f62c03906ad
```

The task is offline. The MQTT traffic is a generated lab capture; no live broker is needed.

## Recover the agent and its data

Inspect the partition table, strings, and LittleFS region. The relevant physical ranges in this exact flash image are:

| Item | Start | Length |
|---|---:|---:|
| Compiled Berry agent | `0x3b4000` | `0x5b8` |
| Device ID | `0x3b2104` | 16 bytes |
| Keyring | `0x3b2204` | 108 bytes |
| Sealed flag | `0x3b2384` | 74 bytes |

These are fixture-specific offsets, not a general LittleFS extractor.

The saved solver decodes the Berry prototypes and constants using the matching `be_opcodes.h` from the supplied source. Each instruction contains a six-bit opcode, an eight-bit A register, and two nine-bit operand fields. Constants and nested prototypes expose the unwrap logic.

## Reassemble the rotation messages

The MQTT capture contains historical state, a newer rotation split across TCP packets, and retransmission. Inspecting raw packet strings alone can select the wrong event. The original investigation used tshark's MQTT dissection:

```sh
tshark -r mqtt.pcap -Y mqtt -T fields \
  -e frame.number -e mqtt.topic -e mqtt.msg
```

The two relevant epoch and nonce pairs recovered were:

```text
epoch 7: 9bb1ebe2f5663269d3be1348ee57dc7dbce22b373243aebd67897581cf6f65f0
epoch 8: 1a3dfb1382455e073f25450c8c8cee24ba89b0a924f86b7103a732ab902a2606
```

The keyring uses 36-byte entries: a four-byte little-endian epoch followed by a 32-byte secret. Select the unique keyring entry matching the rotation epoch.

## Derive the key and authenticate the plaintext

The agent's derivation is:

```python
material = (
    b"tasmota-vault/unwrap/v2\0"
    + device_id
    + epoch.to_bytes(4, "little")
    + rotation_nonce
)
key = hmac.new(epoch_secret, material, hashlib.sha256).digest()
```

The sealed record contains a 12-byte AES-GCM nonce, ciphertext, and a final 16-byte tag:

```python
cipher = AES.new(key, AES.MODE_GCM, nonce=sealed[:12])
flag = cipher.decrypt_and_verify(sealed[12:-16], sealed[-16:])
```

Epoch 7 fails authentication. Epoch 8 yields the flag and verifies its tag. That authentication check decides which historical rotation is relevant.

## Reproduce

Place `solve.py` beside the extracted `flash.bin`. Extract the supplied Tasmota source so the opcode header is at:

```text
source/Tasmota-15.6.0/lib/libesp32/berry/src/be_opcodes.h
```

Run `python3 solve.py` with PyCryptodome installed. The saved solver prints the disassembly followed by:

```text
REJECTED 7
AUTHENTICATED 8 b'hiCTF{b3rry_r0t4t10n_c94934d76344ab1151e03afd}'
```

The script contains the two rotation nonces already recovered from the capture; it does not itself reassemble MQTT. To repeat the entire analysis, recover those messages first and compare them with the script.

**Source chat:** “Locate the file in Downloads”, `01a18d2d-f089-7cc3-97b8-51e3533733b3`. Contest submission was not recorded.
