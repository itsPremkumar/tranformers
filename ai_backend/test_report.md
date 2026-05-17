# Backend Test Report

**Date:** 2026-05-17 18:57:41

## Performance Metrics
| Prompt | Latency (ms) |
|---|---|
| Who is the current Chief Minister of Tamil Nadu as of May 11, 2026? | 11770.46 |
| Which political party does the current CM of Tamil Nadu belong to? | 1025.46 |

## Hardware Simulation Summary
- **Audio Packets Received:** 2
- **Commands Received:** 2

## Detailed Logs
```
[18:57:15] Starting End-to-End Backend Test...
[18:57:17] WebSocket connected to backend.
[18:57:17] Sent IDENTITY packet.
[18:57:17] --- Sending Prompt: Who is the current Chief Minister of Tamil Nadu as of May 11, 2026? ---
[18:57:28] Received WS Text: SAY:C Joseph Vijay
[18:57:29] Received WS Binary Audio: 56064 bytes (Chunk #1)
[18:57:29] AI Response received in 11770.46ms
[18:57:29] Commands: ['SAY:C Joseph Vijay']
[18:57:32] --- Sending Prompt: Which political party does the current CM of Tamil Nadu belong to? ---
[18:57:33] Received WS Text: SAY:செர்கேர்
[18:57:33] Received WS Binary Audio: 31488 bytes (Chunk #2)
[18:57:33] AI Response received in 1025.46ms
[18:57:33] Commands: ['SAY:செர்கேர்']
[18:57:36] Waiting for final responses...
[18:57:41] Generating Test Report...
```
