# Backend Test Report

**Date:** 2026-05-11 19:50:49

## Performance Metrics
| Prompt | Latency (ms) |
|---|---|
| Who is the current Chief Minister of Tamil Nadu? | 6967.59 |
| What is the latest score or news about the Indian Cricket Team? | 14783.05 |
| Look at the camera and identify the most prominent object in view. | 5232.33 |
| Do you see any humans or faces right now? | 7045.64 |
| Describe the background environment behind the camera. | 8856.02 |

## Hardware Simulation Summary
- **Audio Packets Received:** 5
- **Commands Received:** 6

## Detailed Logs
```
[19:49:44] Starting End-to-End Backend Test...
[19:49:46] WebSocket connected to backend.
[19:49:46] Sent IDENTITY packet.
[19:49:46] --- Sending Prompt: Who is the current Chief Minister of Tamil Nadu? ---
[19:49:52] Received WS Text: SAY:Shri @actorvijay
[19:49:53] Received WS Binary Audio: 56832 bytes (Chunk #1)
[19:49:53] AI Response received in 6967.59ms
[19:49:53] Commands: ['SAY:Shri @actorvijay']
[19:49:56] --- Sending Prompt: What is the latest score or news about the Indian Cricket Team? ---
[19:50:02] Received WS Text: SAY:Here is what I found: Stay updated with the latest news on the Indian cricket team, including live scores, match results, fixtures, squads, rankings, player performances ... Follow Mail Sport s live blog for the latest sco
[19:50:10] AI Response received in 14783.05ms
[19:50:10] Commands: ['SAY:Here is what I found: Stay updated with the latest news on the Indian cricket team, including live scores, match results, fixtures, squads, rankings, player performances ... Follow Mail Sport s live blog for the latest sco']
[19:50:10] Received WS Binary Audio: 602880 bytes (Chunk #2)
[19:50:13] --- Sending Prompt: Look at the camera and identify the most prominent object in view. ---
[19:50:17] Received WS Text: SAY:I can see the camera feed, but I'm having trouble identifying everything clearly.
[19:50:19] Received WS Binary Audio: 196608 bytes (Chunk #3)
[19:50:19] AI Response received in 5232.33ms
[19:50:19] Commands: ["SAY:I can see the camera feed, but I'm having trouble identifying everything clearly."]
[19:50:22] --- Sending Prompt: Do you see any humans or faces right now? ---
[19:50:26] Received WS Text: SAY:In the image, there is an old wooden door with a metal lock on it. The door appears to be closed and has some damage to its surface. There are no people visible in the frame of the photo, but there is a keyhole located near the bottom left corner of the door.
[19:50:29] AI Response received in 7045.64ms
[19:50:29] Commands: ['SAY:In the image, there is an old wooden door with a metal lock on it. The door appears to be closed and has some damage to its surface. There are no people visible in the frame of the photo, but there is a keyhole located near the bottom left corner of the door.']
[19:50:29] Received WS Binary Audio: 587520 bytes (Chunk #4)
[19:50:32] --- Sending Prompt: Describe the background environment behind the camera. ---
[19:50:36] Received WS Text: SAY:The image shows a room with a wooden ceiling and white walls, giving it an old-fashioned appearance. The ceiling has a few missing boards, adding to its rustic charm. A small window can be seen on one side of the room, allowing natural light to enter. In front of the window is a door that appears to be closed or locked.
[19:50:38] Received WS Text: SAY:I'm thinking, but I couldn't find a clear answer for that right now.
[19:50:41] AI Response received in 8856.02ms
[19:50:41] Commands: ['SAY:The image shows a room with a wooden ceiling and white walls, giving it an old-fashioned appearance. The ceiling has a few missing boards, adding to its rustic charm. A small window can be seen on one side of the room, allowing natural light to enter. In front of the window is a door that appears to be closed or locked.']
[19:50:41] Received WS Binary Audio: 751872 bytes (Chunk #5)
[19:50:44] Waiting for final responses...
[19:50:49] Generating Test Report...
```
