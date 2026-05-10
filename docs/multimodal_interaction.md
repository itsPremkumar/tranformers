# 👋 Multimodal Interaction Guide

The Transformer Robot interacts with humans using a combination of Computer Vision, Voice Synthesis, and Physical Expressions.

## 👁️ 1. Reactive Vision & Tracking

The robot utilizes an **OpenCV-powered** vision pipeline in the AI Backend to track objects in real-time.

### Tracking Modes:
- **`CMD:FOLLOW` (Face Tracking)**: The robot identifies the largest human face and uses the head gimbal (Pan/Tilt) to maintain "eye contact".
- **`CMD:PLAY_BALL` (Object Tracking)**: Tracks a red ball and autonomously navigates to "kick" it.
- **`CMD:COLLECT_WASTE` (Blob Tracking)**: Identifies dark objects on the ground and approaches them to "push" or collect them.

## 👋 2. Gesture Recognition
For silent, non-verbal control, the robot uses **Google MediaPipe** to recognize hand signals:
- **Open Palm (5 Fingers)**: Triggers an immediate **Emergency Stop**.
- **Point (Index Finger)**: Triggers **Forward Movement**.

*Note: Gesture recognition is always active in the background for safety.*

## 🗣️ 3. Physical Voice (TTS)
The robot generates its own voice locally without needing an external speaker on the PC.
1. **Generation**: The AI generates text.
2. **Synthesis**: The backend converts text to **16kHz Raw PCM** audio.
3. **Streaming**: Binary audio packets are sent via WebSocket to the **Comm Controller**.
4. **Playback**: The ESP32 outputs the audio via **I2S (MAX98357A)** to a physical speaker.

### Language Support
The robot's voice and personality can be configured for:
- **English** (`en`)
- **Tamil** (`ta`)

## 🎭 4. OLED Facial Expressions
The SSD1306 OLED display acts as the robot's "eyes" and provides visual feedback:
- **Happy/Neutral**: Default idle states.
- **Talking Animation**: Automatically triggers during audio playback.
- **Sad/Error**: Triggers if Wi-Fi or AI connection is lost.
- **Hero/Angry**: Triggered by specific AI persona emotional states.
