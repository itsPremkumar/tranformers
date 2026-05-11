# Backend Test Report

**Date:** 2026-05-11 19:57:39

## Performance Metrics
| Prompt | Latency (ms) |
|---|---|
| Who is the current Chief Minister of Tamil Nadu as of May 11, 2026? | 8326.45 |
| Which political party does the current CM of Tamil Nadu belong to? | 1432.66 |

## Hardware Simulation Summary
- **Audio Packets Received:** 2
- **Commands Received:** 3

## Detailed Logs
```
[19:57:16] Starting End-to-End Backend Test...
[19:57:18] WebSocket connected to backend.
[19:57:18] Sent IDENTITY packet.
[19:57:18] --- Sending Prompt: Who is the current Chief Minister of Tamil Nadu as of May 11, 2026? ---
[19:57:23] Received WS Text: SAY:Here is what I found: 10 hours ago - There have been four instances of President's rule in Tamil Nadu, most recently in 1991. C. Joseph Vijay of the Tamilaga Vettri Kazhagam is the incumbent since 10 May 2026, and the firs
[19:57:26] Received WS Text: SAY:I'm thinking, but I couldn't find a clear answer for that right now.
[19:57:27] AI Response received in 8326.45ms
[19:57:27] Commands: ["SAY:Here is what I found: 10 hours ago - There have been four instances of President's rule in Tamil Nadu, most recently in 1991. C. Joseph Vijay of the Tamilaga Vettri Kazhagam is the incumbent since 10 May 2026, and the firs"]
[19:57:27] Received WS Binary Audio: 649728 bytes (Chunk #1)
[19:57:30] --- Sending Prompt: Which political party does the current CM of Tamil Nadu belong to? ---
[19:57:30] Received WS Text: SAY:ระมายงสวนี้ทองการบัดพิมายง
[19:57:31] Received WS Binary Audio: 102912 bytes (Chunk #2)
[19:57:31] AI Response received in 1432.66ms
[19:57:31] Commands: ['SAY:ระมายงสวนี้ทองการบัดพิมายง']
[19:57:34] Waiting for final responses...
[19:57:39] Generating Test Report...
```
