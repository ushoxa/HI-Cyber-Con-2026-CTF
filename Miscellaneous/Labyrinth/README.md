# Labyrinth — hiCTF 2026 (Misc)

**Category:** Misc / Custom Protocol / Maze  
**Target:** `labyrinth-079a44b78574.chall.hiddeninvestigations.net:1337` (TLS; each instance/session may differ)  
**Status:** **SOLVED.** The screenshot of a live run confirms that answering the sealed gate with raw direction bytes returns the genuine flag. `hiCTF{not_the_exit}` is a deliberate decoy.

**Flag:** `hiCTF{l34rn3d_th3_t0ngu3_w4lk3d_th3_l4byr1nth_a93074db3d}`

## Challenge

> Somewhere on this port a server is talking in a language no tool has ever heard of. It has no manual and no patience for strangers, but it does answer, and every answer tells you a little more. Listen closely, learn to speak its tongue, and find your way out of the labyrinth behind it. Not every door that glows is an exit.

## 1. Discovering the framing

Connect using `ncat --ssl <host> 1337`. The server's first bytes are:

```
4c 42 59 7f 80 00 24 01 4c 41 42 59 52 49 4e 54 48 ...
```

Decoded:

```
magic     = b'LBY\x7f'     # 4 bytes
opcode    = 0x80           # 1 byte
length    = 0x0024         # 2 bytes, big-endian
payload   = 01 + b'LABYRINTH speaks in frames. listen.'
```

Raw `HELP`/`ping` lines did not work. Sending a length-prefixed text string (without magic) returned: `bad magic; frames start with my banner's first 4 bytes`. All subsequent requests must be framed as:

```python
def frame(op, payload=b''):
    return b'LBY\x7f' + bytes([op]) + len(payload).to_bytes(2, 'big') + payload
```

## 2. Enumerating opcodes

A scanner sent framed requests with different opcode bytes. The recognizable request codes were:

| Request opcode | Observed purpose |
|---|---|
| `0x01` | HELLO / obtain nonce |
| `0x02` | State hint (e.g., prompts which step is expected) |
| `0x10` | PROBE fresh nonce |
| `0x20` | MOVE in maze |
| `0x30` | ANSWER a challenge |
| `0x40` | Fake exit / decoy flag |
| `0x50` | Debug message (apparent distraction) |
| `0x60` | WARP, requires unknown key |

Server responses used `0x80` (banner), `0x81` (nonce), `0x90` (transformation challenge), `0xA0` (room), `0xA1` (sealed gate), `0xEE` (error) and `0xF0` (flag result; decoy or genuine depending on state).

An important reversing lesson: an error containing `wrong move for this state: PROBE with the nonce you were given` was not a request to try additional encodings under `0x01` or `0x02`. **The required opcode was `0x10`.** Hundreds of guesses using the wrong opcode naturally failed.

## 3. Nonce handshake

Send `0x01` with the one-byte payload `01`. The `0x81` response begins with a stage byte followed by an **8-byte nonce**:

```
0x81: 01 | <nonce:8 bytes> | "PROBE the nonce"
```

Send those eight nonce bytes *unchanged* using request opcode `0x10`. The server then responds with opcode `0x90` and binary known-answer examples.

Use the nonce from the **same connection**. It changes between sessions.

## 4. Reverse-engineering T(x)

After a successful nonce probe, the `0x90` payload contains:

```
03 | input_0(4) | output_0(4)
   | input_1(4) | output_1(4)
   | input_2(4) | output_2(4)
   | challenge(4) | "ANSWER T(challenge)"
```

One captured session included:

```
00000000 -> dcdcdcdc
01020304 -> d8dfdedd
de629761 -> bd4bbe02
challenge = 87424ebb
```

These pairs satisfy:

```
T(x) = reverse_bytes(x) XOR mask
mask = dcdcdcdc          # THIS SESSION ONLY
```

For that example:

```
reverse(87424ebb) = bb4e4287
bb4e4287 XOR dcdcdcdc = 67929e5b
```

Send `0x30` with exactly four answer bytes. In a new session, derive the mask dynamically from the first pair (`mask = reverse(input_0) XOR output_0`) and validate against the other two.

A successful response returns an `0xA0` room at the maze entrance.

## 5. Parsing rooms and moving

The payload of a room frame `0xA0` consists of:

```
x(1) | y(1) | door_mask(1) | flags(1) | token(2) | optional text
```

Example:

```
00 00 04 00 fe 0e | "entrance. MOVE dir+token"
```

This describes room `(0,0)`, door bitmask `0x04` (South), flags `0`, and movement token `fe0e`.

Direction encoding is:

| Byte | Direction | Bit |
|---|---|---|
| `00` | North | `0x01` |
| `01` | East  | `0x02` |
| `02` | South | `0x04` |
| `03` | West  | `0x08` |

Make a move with request opcode `0x20` and three payload bytes:

```
<direction:1> + <current_room_token:2>
```

For the sample entrance: `02 fe 0e` requests a move South. Successful moves return a new room frame and **a new token**; always replace the old token. Moving through walls returns `wall. token unchanged`. Reusing a stale token can reset the session.

The maze is session-specific, so replaying the same path on a new connection can hit walls.

## 6. Lights are not the true exit

Some rooms are marked with `flags = 0x02` and a description such as `a light!`. Exploring them can cause the server to return:

```
0xf0: hiCTF{not_the_exit}
```

Opcode `0x40` can also return that same string. Do not submit it; the challenge explicitly warns that glowing doors are not necessarily exits.

## 7. The sealed gate and shortest route

A separate response, **opcode `0xA1`**, was observed when entering a sealed gate:

```
03 00 02 01 f2 a1 | "a sealed gate. it asks how you came, by the shortest way"
```

The first two bytes encode the **destination gate coordinates**, not the position you just left. The server transitions into a state that expects `ANSWER with the shortest route from the entrance`. Further MOVE commands fail with a state error.

The exploration algorithm should:

1. Map rooms and legal edges from the door masks while staying in one authenticated TLS session.
2. Record all movements using the fresh token from each successful room frame.
3. On receiving `0xA1`, **add the final edge into the gate** to the graph.
4. Use BFS from `(0,0)` to the gate's coordinates to compute the shortest direction sequence.
5. Submit that sequence to opcode `0x30` without trying to move/backtrack further.

Earlier solver versions computed the path to the *previous room* instead of the sealed gate. That off-by-one destination error was fixed in the later solver.

A test with an empty `ANSWER` returned:

```text
0xee: gate: wrong length route; staying at gate
```

The final breakthrough was to serialize the shortest BFS route as **one raw byte per direction** (`N=0x00`, `E=0x01`, `S=0x02`, `W=0x03`), not as ASCII letters or a string of digits. Send that exact byte sequence with opcode `0x30` while still in the gate-answer state.

In the successful screenshot, the gate was at `(2,1)` and the solver computed the 15-step shortest path:

```text
SESESSENNNENWWS
```

The corresponding raw answer payload was:

```text
02 01 02 01 02 02 01 00 00 00 01 00 03 03 02
```

The service returned `op=0xf0` with the real flag:

```text
hiCTF{l34rn3d_th3_t0ngu3_w4lk3d_th3_l4byr1nth_a93074db3d}
```

The maze and shortest route vary by instance/session; the route shown above is an observed successful example and must not be hardcoded for other sessions.

A minimal encoding function for this final phase is:

```python
DIRECTION_BYTE = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
route = 'SESESSENNNENWWS'             # illustration from winning screenshot
payload = bytes(DIRECTION_BYTE[d] for d in route)
sock.sendall(frame(0x30, payload))    # on the already-authenticated TLS connection
```

## 8. Local solver and usage

The accompanying `labyrinth_gate_solver.py` automates the nonce, reverse/XOR transformation, maze exploration and BFS gate-route candidates. Point it at the current challenge instance:

```bash
python3 labyrinth_gate_solver.py \
  --host labyrinth-079a44b78574.chall.hiddeninvestigations.net \
  --port 1337 --sessions 20
```

The screenshot shows `labyrinth_gate_solver.py` recovered the flag from a fresh instance. For reliability, confirm that the instance is still reachable and let the script discover the maze and tokens live. The winning response was `op=0xf0` after `ANSWER [raw direction bytes]`.

## Takeaways

- Extract protocol structure from raw bytes and error messages, not from assumptions about text commands.
- Distinguish request opcodes from server-side state numbers.
- Validate reverse-engineered transforms using all provided input/output examples.
- Keep stateful nonce and token interactions on one connection.
- Treat visible flags as possible decoys.
- Follow the *gate* coordinates when building the graph; compute BFS only after adding the gate edge.
- Encode the BFS route as **raw direction bytes**, not human-readable `N/E/S/W` text.

**Verified fake flag:** `hiCTF{not_the_exit}`.  
**Real flag (verified in winning screenshot):** `hiCTF{l34rn3d_th3_t0ngu3_w4lk3d_th3_l4byr1nth_a93074db3d}`.
