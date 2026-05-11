# Backend Test Report

**Date:** 2026-05-11 19:34:27

## Performance Metrics
| Prompt | Latency (ms) |
|---|---|
| Hello robot, identify yourself. | 10502.28 |
| What is the current time and weather in New York? | 11295.30 |
| Look at the camera and tell me what you see. | 4294.77 |
| Calculate the square root of 256. | 726.17 |
| Tell me a joke about transformers. | 1103.64 |

## Hardware Simulation Summary
- **Audio Packets Received:** 0
- **Commands Received:** 6

## Detailed Logs
```
[19:33:37] Starting End-to-End Backend Test...
[19:33:39] WebSocket connected to backend.
[19:33:39] Sent IDENTITY packet.
[19:33:39] --- Sending Prompt: Hello robot, identify yourself. ---
[19:33:49] Received WS Text: SAY:I am currently processing. Please try again.
[19:33:49] AI Response received in 10502.28ms
[19:33:49] Commands: ['SAY:I am currently processing. Please try again.']
[19:33:53] --- Sending Prompt: What is the current time and weather in New York? ---
[19:33:58] Received WS Text: SAY:Here is what I found: Get New York, NY current weather report with temperature, feels like, wind, humidity, pressure, UV and more from TheWeatherNetwork.com. Current local time in New York, New York, United States. Get map
[19:33:59] Received WS Text: SAY:I am currently processing. Please try again.
[19:34:04] AI Response received in 11295.30ms
[19:34:04] Commands: ['SAY:Here is what I found: Get New York, NY current weather report with temperature, feels like, wind, humidity, pressure, UV and more from TheWeatherNetwork.com. Current local time in New York, New York, United States. Get map']
[19:34:07] --- Sending Prompt: Look at the camera and tell me what you see. ---
[19:34:11] Received WS Text: SAY:I am currently processing. Please try again.
[19:34:11] AI Response received in 4294.77ms
[19:34:11] Commands: ['SAY:I am currently processing. Please try again.']
[19:34:14] --- Sending Prompt: Calculate the square root of 256. ---
[19:34:14] Received WS Text: SAY:I am currently processing. Please try again.
[19:34:15] AI Response received in 726.17ms
[19:34:15] Commands: ['SAY:I am currently processing. Please try again.']
[19:34:18] --- Sending Prompt: Tell me a joke about transformers. ---
[19:34:18] Received WS Text: SAY:Why did the transformer turn off? Because it was fried.
[19:34:19] AI Response received in 1103.64ms
[19:34:19] Commands: ['SAY:Why did the transformer turn off? Because it was fried.']
[19:34:22] Waiting for final responses...
[19:34:27] Generating Test Report...
```
