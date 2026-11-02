# The Quiet Divide

**Category:** Network · **Event:** HI Cyber Con 2026

## Result

```text
hiCTF{c8c46fdbd6e5e4eacabfba53a156ff9ab10567f2}
```

The final AES-GCM authentication succeeded in the recorded solve. The winning transaction was `6dd9ec588c9914ca95df44b2`, in the third recovered archive.

## Recover the evidence chain

`the-quiet-divide.zip` had SHA-256 `15c7f337f5eae52865fbece148237ca5f01b2f4fa703d64a54c4f35a7bb40225`. Its packet capture contained 110,248 packets spanning about 98.8 seconds. Start with protocol hierarchy and conversations, then export HTTP objects:

```bash
tshark -r the-quiet-divide.pcap -q -z io,phs -z conv,tcp
tshark -r the-quiet-divide.pcap --export-objects http,objects
```

The relevant traffic supplied an SDK, split firmware, attestations, frames, audit records, checkpoints, and encrypted archives. The SDK was valuable because it specified the encoding and cryptographic derivations. Review that code before using it; network-extracted code is an artifact, not automatically trusted software.

Reassemble the four firmware objects in order. Use the production attestation, the QUIC observation, the deployed frame, and the audit events as inputs to the SDK's `evidence_components`. This yields the evidence bytes and codec needed for subsequent derivations.

## Keep conflicting observations separate

The deployed PLS2 frame decoded to sequence `10450910`, scheduler queue **23**, load **71**, and epoch milliseconds `1793517529318`. The QUIC observation instead reported queue **31**, load **8**. Treating those as interchangeable destroys the evidence chain; the disagreement is part of the challenge.

Use the audit seal's `archive_salt_hex` with `archive_key`, and decrypt the candidate archives using the terminal event hash. The three plaintext archives were SQLite databases containing `transfers`, `receipts`, `fragments`, and `operations`.

## Select and authenticate the transaction

For each transfer, read fragments in `ord` order. Apply `unmask_fragment(codec, tx_id, ord, payload)` to each and concatenate the recovered bytes. Check `transaction_material_commit` against the receipt's `fragment_commit`. Do not select a candidate merely because its disposition says `accepted`: several candidates carried plausible metadata.

The successful row in archive three matched the production nonce and frozen checkpoint, and its reconstructed material passed the commitment check. The SDK's final derivation used the material, evidence, checkpoint signature, and seal salt:

```python
key = sdk.final_key(material, evidence, checkpoint_signature, body['salt_hex'])
plaintext = sdk.decrypt_seal(ciphertext, key, body['nonce_hex'], body)
```

AES-GCM authentication then produced the flag. The recovered SDK is required to reproduce its challenge-specific canonicalization and key derivations; the two lines above describe the final stage, not a standalone solver.
