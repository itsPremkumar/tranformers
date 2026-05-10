# 🌌 Gemini 2.0 Omni (Cloud Primary)

## Overview
Gemini 2.0 represents the state-of-the-art in "Omni" models as of 2026. It is the robot's primary "Conscious Brain" when an internet connection is available.

## Key Capabilities
*   **Multimodal Live API**: Processes live video from the ESP32-CAM and audio from the robot's mic simultaneously.
*   **Agentic Reasoning**: Best-in-class at planning multi-step actions (e.g., "Find the human, wave, and ask for a charging cable").
*   **Unified Context**: Understands the relationship between what it sees, hears, and its past memories from the SQLite vault.

## Configuration in `.env`
```bash
GEMINI_MODEL="gemini-2.0-flash"
GEMINI_API_KEY="your_key_here"
```

## Best Use Cases
*   Complex environmental navigation.
*   High-fidelity conversational persona (Sentinel Prime's wise character).
*   Visual object identification and deep reasoning.
