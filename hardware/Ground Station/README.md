# GSC-7 Ground Station — Write-up

**CTF:** HI Cyber Con 2026  
**Category:** Reverse Engineering / ICS / Network  
**Challenge:** Ground Station  
**Flag Format:** `hiCTF{...}`

## 1. Challenge Overview

We were given access to a fictional GSC-7 industrial controller responsible for satellite ground-station fueling and cooling.

The controller refused to pass its safety validation because someone had modified its ladder logic. Our objective was to authenticate as an engineer, identify and correct the unsafe logic, ensure the changes persisted, and successfully complete the controller's validation test.

The provided archive contained four main resources:

- `gsc-fw.bin` — stripped x86-64 controller firmware.
- `gsc_tech.py` — a basic protocol client.
- `GSP_reference.md` — protocol specification.
- `README.txt` — setup instructions.

The challenge used a custom protocol called **GSP/1.0**, exposed over TLS.

## 2. Understanding the Protocol

The protocol documentation showed that the controller presents a randomly generated 8-byte nonce whenever a client connects.

The initial greeting follows this structure:

```text
GSP/1.0 GSC-7 Ground Station Controller
UNIT GS-ALPHA-07
NONCE <16 hex characters>
READY
OK greeting
```

To authenticate, the client must calculate a response and submit:

```text
AUTH <response-hex>
```

A correct response produces:

```text
OK access=engineer
```

The main problem was that the protocol reference did not explain how to calculate this response. Instead, the algorithm was embedded in the firmware.

## 3. Reverse Engineering the Firmware

First, we inspected the binary:

```bash
file gsc-fw.bin
strings gsc-fw.bin
chmod +x gsc-fw.bin
./gsc-fw.bin
```

The firmware identified itself as version 2.3.1 and printed a diagnostic signature:

```text
POST: controller self-check OK
image-sig=de8c1297
```

This signature was useful for checking whether our reconstructed authentication algorithm was correct.

Analyzing the binary revealed a custom challenge-response function. The algorithm generates a 16-byte key using a deterministic linear congruential generator.

Its initial state and constants are:

```text
Seed       = 0x1F2E3D4C
Multiplier = 0x0019660D
Increment  = 0x3C6EF35F
Rounds     = 12
```

Each key byte is generated using:

```python
state = (state * 0x19660D + 0x3C6EF35F) & 0xffffffff
key_byte = ((state >> 17) ^ (i * 0x5B)) & 0xff
```

The resulting key is interpreted as four little-endian 32-bit integers. The 8-byte nonce is interpreted as two more integers.

The controller then performs 12 rounds of additions, XOR operations, 32-bit rotations, and state permutations.

We reconstructed the algorithm in Python:

```python
import struct

MASK = 0xffffffff

def rol(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK

def response(nonce):
    state = 0x1F2E3D4C
    key = bytearray()

    for i in range(16):
        state = (
            state * 0x19660D + 0x3C6EF35F
        ) & MASK

        key.append(
            ((state >> 17) ^ (i * 0x5B)) & 0xff
        )

    a, b, c, d = struct.unpack("<4I", key)
    e, f = struct.unpack("<2I", nonce)

    for i in range(12):
        a = rol((a + e) & MASK, 7)
        b = rol(b ^ a, 11)
        c = rol((c + b + f) & MASK, 17)
        d = rol(d ^ c, 19)

        e = (e + d + i * 0x9E3779B9) & MASK
        f = rol(f ^ a, 13)

        a, b, c, d = b, c, d, a

    return struct.pack("<2I", a ^ c, b ^ d)
```

We verified the implementation using the firmware's internal diagnostic vector:

```text
Nonce:     4753432d37000123
Response:  de8c1297e603570f
Image sig: de8c1297
```

The first four response bytes matched the firmware's diagnostic signature.

This confirmed the reconstruction and allowed us to calculate authentication responses for arbitrary session nonces.

## 4. Authenticating as an Engineer

With the authentication algorithm recovered, the next step was to connect to the controller through TLS.

The server requires SNI, so a standard plaintext TCP connection is insufficient.

Our solver established a TLS connection, extracted the nonce from the greeting, calculated its corresponding response, and sent the `AUTH` command.

Once authenticated, the controller exposed engineering commands for reading and modifying ladder logic.

## 5. Identifying the Safety Logic Problem

The controller uses ladder-style expressions to operate four main coils:

- `COOLANT_PUMP`
- `VENT_VALVE`
- `INTERLOCK_OK`
- `FUEL_VALVE`

We inspected the current program using:

```text
PROG LIST
```

The reference documentation defined the required safety behavior.

Most importantly, fueling was permitted only when both conditions were satisfied:

```text
TANK_TEMP <= 45
TANK_PSI  <= 100
```

Therefore, the correct fueling interlock was:

```text
(TANK_TEMP <= 45) AND (TANK_PSI <= 100)
```

The `AND` operator is essential because temperature and pressure must both be within their safe limits.

The fuel valve must also depend on the interlock, active test state, emergency-stop state, and fill level.

We applied the documented safety condition:

```text
PROG SET INTERLOCK_OK (TANK_TEMP <= 45) AND (TANK_PSI <= 100)
```

We then requested `PROG LIST` again to verify the corrected expression and ensure the other rungs remained unchanged.

## 6. Understanding the Integrity Watchdog

Correcting the ladder logic was not enough.

The controller had an integrity watchdog that compared the active ladder program against a trusted checksum whenever a test was armed.

If the checksums differed, the watchdog restored an older backup of the program and aborted the test.

The relevant diagnostic commands were:

```text
BACKUP GET
BACKUP STATUS
WDOG STATUS
```

The `BACKUP STATUS` command exposed the active checksum, backup checksum, trusted checksum, and whether the watchdog would restore the backup.

The important field was:

```text
arm_will_restore=1
```

A value of `1` meant that the controller would reject the modified program when the validation test started.

Rather than disabling the watchdog, we used the intended maintenance mechanism:

```text
BACKUP SAVE
```

This copied the corrected ladder program to the backup slot and updated the trusted checksum.

We checked the status again, requiring:

```text
arm_will_restore=0
```

This was a critical part of the challenge: the fix had to survive the watchdog's integrity check, not merely appear correct in memory.

## 7. Running the Validation Test

After correcting the interlock and saving the trusted backup, the final step was:

```text
RUNTEST
```

The controller runs a deterministic fueling and cooling simulation.

A successful validation requires the cooling system to operate, tank pressure and temperature to remain within the required limits, and fueling to complete without triggering an unsafe condition.

The reference specifies that a successful run returns a response containing:

```text
DATA result=SUCCESS ...
DATA flag=hiCTF{...}
```

Finally, `STATUS` can be used to inspect the controller's solved state and last test result.

The flag is generated by the challenge service, not stored directly inside the firmware image.

## 8. Automated Solver

We combined the entire process into one Python script.

The solver:

1. Reconstructs the firmware's challenge-response algorithm.
2. Authenticates using the live session nonce.
3. Reads the ladder program and watchdog configuration.
4. Repairs the fueling interlock.
5. Saves the corrected program as the trusted backup.
6. Verifies that the watchdog will not restore the old program.
7. Executes `RUNTEST` and searches the response for `hiCTF{...}`.

Run the solver using:

```bash
python3 gsc_solve.py
```

The script requires only Python's standard library.

## 9. Conclusion

The challenge combined firmware reverse engineering, a custom network authentication protocol, industrial control logic, and integrity-check persistence.

The key observations were that the engineer authentication algorithm could be reconstructed from the provided firmware, the fueling interlock had to enforce temperature and pressure limits simultaneously, and modifying the active program alone would not survive the watchdog.

The intended solution was to restore the documented safety logic and update the controller's trusted backup before running validation.

**Verification note:** The authentication reconstruction was checked against the real firmware's diagnostic signature, and the solver was tested against a local protocol mock. A successful live-instance validation and its generated flag were not captured in the available results.
