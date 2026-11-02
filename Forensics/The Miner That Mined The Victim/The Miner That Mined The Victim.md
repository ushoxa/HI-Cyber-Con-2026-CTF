# The Miner That Mined The Victim

**Category:** Forensics · **Event:** HI Cyber Con 2026

## Result

```text
hiCTF{finally_u_proved_ur_worthiness}
```

The challenge asked 14 questions in order, with three consecutive wrong answers resetting progress. The original environment could not connect to the instance, so the user pasted questions and the answers were derived from the supplied Windows triage evidence. This reconstruction preserves that answer sequence.

## Evidence workflow

The archive contained Windows event logs, Edge history, Prefetch data, filesystem metadata, and deleted-file evidence. Extract carefully: archive paths used Windows backslashes, and the first extraction attempt hit a file/directory collision. Normalize separators and inspect entries rather than assuming a standard Unix directory tree.

Query Edge's `History` SQLite database for downloads and redirect chains. Parse EVTX records into named event fields, not only their rendered strings. Use Sysmon process and image-load events to distinguish a downloaded executable from one that actually ran. Correlate deleted paths and sizes with filesystem/recycle evidence rather than inferring deletion from absence.

Normalize timestamps to UTC before comparing artifacts. The victim's effective offset was UTC-7, while some artifacts displayed times seven hours apart. The chronological download, execution, assembly-load, and deletion times are consistent after normalization.

## Answers

| # | Requested evidence | Answer |
| :--- | :--- | :--- |
| 1 | OS version at execution | `Microsoft Windows NT 10.0.26200.0` |
| 2 | Effective UTC offset and bias | `UTC-7, 420` |
| 3 | Download page | `https://limewire.com/d/Ak55K#Yrx3FgK3du` |
| 4 | Redirect downloadId | `42d377fe-8948-4a32-809f-69a51e6dbcfa` |
| 5 | Browser download completion | `2026-05-13 14:25:36 UTC` |
| 6 | First execution and run count | `2026-05-13 14:26:55 UTC, 1` |
| 7 | Cryptography assembly and load time | `C:\Program Files\dotnet\shared\Microsoft.NETCore.App\9.0.16\System.Security.Cryptography.dll, 2026-05-13 14:26:58 UTC` |
| 8 | Registry value | `HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\DisableAntiSpyware` |
| 9 | Technique ID supplied in the recorded answer | `T1685` |
| 10 | Important text in triage artifacts | `hiCTF{finally_u_proved_ur_worthiness}` |
| 11 | Deleted folder's original path and time | `C:\Users\milon1\Downloads\miner, 2026-05-13 14:27:47 UTC` |
| 12 | Deleted miner folder byte size | `179623` |
| 13 | Deleted bar.txt plaintext | `I will always be there for you bro!` |
| 14 | Shred-pattern ASCII bytes | `help` |

## Interpretation notes

The registry question's wording says “successfully modify,” but the Defender event inspected in the history described the change as `Ignored` and `0x1(Not Applicable)`. The answer names the observed registry target; it does not prove Defender was actually disabled.

The technique ID above is the answer supplied during the quiz. ATT&CK mappings can change, so it is recorded as historical answer data rather than a claim about a permanently fixed taxonomy.

The flag-shaped text was recovered at question 10. The available transcript does not include a final server banner after question 14; the writeup therefore distinguishes evidence recovery from an independently captured end-of-session acceptance message.
