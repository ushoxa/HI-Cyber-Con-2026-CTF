# C3 Vault

**Category:** firmware recovery / authentication  
**Recovered:** 30 October 2026, Asia/Samarkand  
**Flag:** `hiCTF{efus3_cl34r_jt4g_0p3n_nv5_77417a8e52}`  
**Evidence:** the CTF service returned `VAULT OPENED` and the flag. The recorded response was checked on 1 November; the service was not contacted again.

## Challenge

The archive supplies an ESP32-C3 flash image and an eFuse readout from a deliberately insecure laboratory fixture. The flash stores enrollment credentials. The flag exists only on the live challenge service.

Archive SHA-256:

```text
ef94f82b12ebfb1640f9e52d6a74c6f514c4ea718bc52f7c7c05aaea3aeb4a59
```

The recovery note warns that a stale enrollment namespace can survive migration. Recovering a credential is not enough; it must be the current one.

## Decrypt the flash

The saved decoder takes 32 candidate key bytes from `efuse_read.bin[0x70:0x90]`, tries the recorded and reversed byte order, and checks the partition-table magic at flash offset `0x8000`.

For this fixture, flash decryption operates in 128-byte units using AES-XTS. The tweak is the four-byte little-endian physical address followed by twelve zero bytes. The input and output unit bytes are reversed around the XTS operation:

```python
tweak = address.to_bytes(4, "little") + bytes(12)
decryptor = Cipher(algorithms.AES(key), modes.XTS(tweak)).decryptor()
plaintext_unit = decryptor.update(ciphertext_unit[::-1])[::-1]
```

The correct candidate produces partition-table magic `aa 50`. That structural check prevents treating arbitrary decrypted bytes as firmware.

## Recover the current enrollment record

The decrypted image contains the 64-byte NVS encryption key at `0xf000`. The NVS partition begins at `0x9000`.

NVS entries require their own XTS processing. The script reads the entry-state bitmap and decrypts occupied 32-byte entries from the original flash bytes. Here the tweak is the entry offset relative to the NVS partition, encoded as a 16-byte little-endian integer. It is different from the physical-address tweak used for flash encryption.

Inspection recovered the current device ID, seed, and epoch:

```text
device = ee0315f3953aad298d7f3f43973ad618
seed   = 826e4e9e65c0ce89f413b7c291bb7e84185c64d4ec8769805227253b985083c5
epoch  = 7
```

These values belong to the challenge fixture. An older seed was also present. Firmware disassembly established the current authentication calculation.

## Answer the service's fresh challenge

Derive the device key:

```python
key = hmac.new(
    seed,
    b"c3-vault/device-key/v2\0" + device + struct.pack("<I", 7),
    hashlib.sha256,
).digest()
```

The original session connected over TLS to the challenge instance on port 1337. Its banner supplied a 32-byte hexadecimal challenge. Compute:

```python
response = hmac.new(
    key,
    b"C3VAULT-AUTH-V2\0" + nonce + device,
    hashlib.sha256,
).hexdigest()
```

Send `auth ` followed by the 64 hexadecimal characters and a newline. Preserve both domain-separation strings, their terminating zero bytes, the byte order of the epoch, and the ordering of nonce and device ID.

The server returned:

```text
VAULT OPENED
hiCTF{efus3_cl34r_jt4g_0p3n_nv5_77417a8e52}
```

## Reproduction and limits

`recover.py` contains the original offline decoder and expects both binary files beside it. It uses the `cryptography` package. `authenticate.py` preserves the successful protocol client and original instance hostname.

The original client disables TLS certificate validation to match the provided `ncat --ssl` challenge transport. It is an archived CTF client, not a production TLS example. A restarted instance may have a different hostname or credentials; its fresh nonce must always come from its current banner.

The service response is preserved in `service-response.txt`. This is historical evidence, not a claim that the old endpoint still runs.

**Source chat:** “Locate the file in Downloads”, `01a18d2d-f089-7cc3-97b8-51e3533733b3`.
