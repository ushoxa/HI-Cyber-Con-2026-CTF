# Pruned Ledger

**Category:** Blockchain · **Event:** HI Cyber Con 2026

## Result

```text
hiCTF{pruned_storage_calldata_never_forgets}
```

The task was to reconstruct case `0xca5ef11e` after selected storage fields were cleared. The archive SHA-256 was `aefb1f1300ca8758ba53fa17ae485a06ed1d48afd5bca941c305a23210dc78fd`.

## Use history rather than the final state

The archive included Solidity contracts, a genesis configuration, a replay script, and signed transactions in `chain/transactions.jsonl`. Replaying locally was attempted but unavailable in the original environment. Instead, `cast decode-transaction` decoded each raw signed transaction offline.

Keep the transaction's sequence number, recovered signer, destination, value, and calldata. For contract creations, derive the CREATE address from the deployer and nonce using Keccak-256 of their RLP encoding. This connects constructor arguments to subsequent calls without needing a live RPC endpoint.

## Reconstruct the case fields

The relevant contract was `0x68fb8760b1353f7349c431442d6e97ab61685ee7`. Its constructor's last 96 argument bytes supplied the reference and masked note material. The reference decoded to `pruned_storage`.

Track authorized `configure(bytes32)` calls in sequence. Transaction 123 set the record to `calldata`; transaction 136 sealed the entry. Later calls changed the current record, so decoding only the final state would lose the value needed for sealing.

The seal mask used the contract address and the record at that point:

```python
# K is Keccak-256; address is the raw 20-byte address; record is bytes32.
mask = K(K(b'hictf.pruned-ledger.seal') + address + record)
entry = bytes(a ^ b for a, b in zip(seal_argument, mask))
```

This recovered `never`. The computed archive slot was:

```text
0x7fecf3326bbe68a7d2e335f9cc6846a837d09eae111b401eaef20dadbac9ce59
```

It is derived from `Keccak256(b'hictf.pruned-ledger.archive' + record) - 1`.

## Recover the caller-bound note

The final note was masked using another domain separator and a caller address:

```python
mask = K(K(b'hictf.pruned-ledger.note') + address + caller)
note = bytes(a ^ b for a, b in zip(masked_note, mask)).rstrip(b'\0')
```

Tracing the settlement participants and testing candidate addresses identified `0x123332679fb9643cb4302de5dc8f7efba76d060f`. Its decoded note was `forgets`.

Join the reference, the record at sealing, the recovered archive entry, and the caller-bound note with underscores. The key observation is that clearing storage does not erase signed transaction calldata or deployment arguments.
