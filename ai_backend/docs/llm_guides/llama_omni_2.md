# 🗣️ Llama-Omni 2 (Local Speech-to-Speech)

## Overview
Llama-Omni 2 is the premier open-source model for **Native Speech Interaction**. It is built on Llama 3.1 and optimized for ultra-low latency.

## Key Capabilities
*   **Speech-to-Speech (S2S)**: The model processes raw audio input and generates raw audio output natively.
*   **Latency**: Achieves ~200ms response time, making conversations feel fluid and human-like.
*   **No Internet Required**: Runs entirely on your local PC via Ollama or vLLM.

## Configuration in `.env`
```bash
OLLAMA_MODEL="llama-omni2"
OLLAMA_HOST="http://localhost:11434"
```

## Best Use Cases
*   Instant, interactive chatting without cloud lag.
*   Offline robot autonomy.
*   Simple control commands via direct voice.
