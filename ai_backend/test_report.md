# Backend Test Report

**Date:** 2026-05-11 19:44:20

## Performance Metrics
| Prompt | Latency (ms) |
|---|---|
| Look at the camera and describe everything you see in detail. | 4887.26 |
| Is there anything moving in front of you? | 4552.72 |
| Identify any objects or people in the current camera view. | 2618.47 |
| What is the most prominent color in the frame? | 918.54 |
| Tell me if you see any text or signs in the background. | 2632.69 |

## Hardware Simulation Summary
- **Audio Packets Received:** 5
- **Commands Received:** 5

## Detailed Logs
```
[19:43:42] Starting End-to-End Backend Test...
[19:43:44] WebSocket connected to backend.
[19:43:44] Sent IDENTITY packet.
[19:43:44] --- Sending Prompt: Look at the camera and describe everything you see in detail. ---
[19:43:48] Received WS Text: SAY:I can see the camera feed, but I'm having trouble identifying everything clearly.
[19:43:49] Received WS Binary Audio: 196608 bytes (Chunk #1)
[19:43:49] AI Response received in 4887.26ms
[19:43:49] Commands: ["SAY:I can see the camera feed, but I'm having trouble identifying everything clearly."]
[19:43:52] --- Sending Prompt: Is there anything moving in front of you? ---
[19:43:56] Received WS Text: SAY:I can see the camera feed, but I'm having trouble identifying everything clearly.
[19:43:57] Received WS Binary Audio: 196608 bytes (Chunk #2)
[19:43:57] AI Response received in 4552.72ms
[19:43:57] Commands: ["SAY:I can see the camera feed, but I'm having trouble identifying everything clearly."]
[19:44:00] --- Sending Prompt: Identify any objects or people in the current camera view. ---
[19:44:02] Received WS Text: SAY:I can see the camera feed, but I'm having trouble identifying everything clearly.
[19:44:03] Received WS Binary Audio: 196608 bytes (Chunk #3)
[19:44:03] AI Response received in 2618.47ms
[19:44:03] Commands: ["SAY:I can see the camera feed, but I'm having trouble identifying everything clearly."]
[19:44:06] --- Sending Prompt: What is the most prominent color in the frame? ---
[19:44:06] Received WS Text: SAY:urn
[19:44:06] Received WS Binary Audio: 29184 bytes (Chunk #4)
[19:44:06] AI Response received in 918.54ms
[19:44:06] Commands: ['SAY:urn']
[19:44:09] --- Sending Prompt: Tell me if you see any text or signs in the background. ---
[19:44:11] Received WS Text: SAY:I can see the camera feed, but I'm having trouble identifying everything clearly.
[19:44:12] Received WS Binary Audio: 196608 bytes (Chunk #5)
[19:44:12] AI Response received in 2632.69ms
[19:44:12] Commands: ["SAY:I can see the camera feed, but I'm having trouble identifying everything clearly."]
[19:44:15] Waiting for final responses...
[19:44:20] Generating Test Report...
```
