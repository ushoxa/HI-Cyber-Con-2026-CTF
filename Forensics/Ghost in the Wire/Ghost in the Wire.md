# Ghost in the Wire

**Category:** Forensics / Network  **Flag:** `hiCTF{1cmp_3xf1l_d3t3ct3d}`

> Our network monitoring team detected anomalous ICMP traffic during a routine packet capture. Something is being exfiltrated through the wire — but the data blends in with normal network noise. Analyze the capture and extract the hidden message before the ghost disappears.

File: `ghost-in-the-wire.zip` → `ghost_traffic.pcap` (30 ICMP echo requests)

## Solution

1. Open the capture: it contains only ICMP echo requests. They all share the same ICMP identifier (`4919` = `0x1337`) and the same TTL, so filtering on those fields alone doesn't separate anything.
2. Split the traffic by **source/destination pair**:

   | Flow | Packets | Payloads |
   |---|---|---|
   | `192.168.1.100 → 10.0.0.5` | 4 | `AAAA…`, `ping from server1`, `health check ok`, `monitor alive 001` (decoy noise) |
   | `10.13.37.1 → 10.13.37.2` | 26 | **one byte each**, sequence numbers 1–26 |

3. Sort the second flow by ICMP sequence number and concatenate the single-byte payloads:

   ```
   h i C T F { 1 c m p _ 3 x f 1 l _ d 3 t 3 c t 3 d }
   ```

The trick is that each exfil packet looks like a tiny ping. The covert stream only becomes visible once you group by endpoints and notice that its payload length is exactly 1.

## Files
- `solve/solve.py` groups ICMP by flow and rebuilds the 1-byte stream (needs `scapy`)
- `artifacts/icmp_packets.tsv` is every ICMP packet (src, dst, id, seq, payload hex)
- `artifacts/solver_output.txt` is the solver output
- `challenge/` has the original zip
