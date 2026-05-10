# 🧠 AI Super-Brain (Cognitive Layer)

The AI Super-Brain is a high-level Python backend built with FastAPI that provides "consciousness" to the Transformer hardware. It bridges the gap between raw motor control and intelligent behavior.

## 🚀 Key Capabilities

### 1. Multi-Model Intelligence
The brain utilizes a **LLM Factory** that can dynamically switch between providers:
- **Gemini 1.5 Pro/Flash**: Primary engine used for multimodal vision and complex reasoning.
- **Ollama (Llama 3)**: Local fallback engine that takes over if internet connectivity is lost, ensuring the robot remains functional offline.
- **OpenAI/Claude**: Secondary providers available for specialized tasks.

### 2. Autonomous Internet Tools
The AI is not limited to its internal training data. It can autonomously decide to use tools to fetch real-world information:
- **Web Search**: Uses DuckDuckGo to answer questions about current events.
- **Wikipedia**: Performs deep lookups on specific topics.
- **Media Playback**: Can play YouTube music or videos upon request.

### 3. Persistent Memory Vaults
Unlike basic chatbots, this system uses **Isolated Persistence** to give each robot a unique soul:
- **Identity-Linked**: Memories are indexed by the `ROBOT_NAME` (e.g., Sentinel Prime vs. Bumblebee).
- **Recall**: The AI retrieves the last 5 conversation exchanges and specific facts about the user/environment.
- **Evolution**: The robot "remembers" past interactions, allowing its personality to evolve over time.

### 4. Proactive Engagement
The brain features a **Proactive Loop** that runs in the background. Every 60 seconds, if the robot is idle, the AI will:
1. Capture a frame from the camera.
2. Analyze the environment.
3. Initiate a curious observation or question to engage nearby humans.

## 🛠️ Software Stack
- **Framework**: FastAPI (Asynchronous Python)
- **Communication**: WebSockets (Real-time binary/text stream)
- **Vision**: OpenCV & Google MediaPipe
- **Memory**: SQLite (Persistent local storage)
- **Audio**: gTTS & Pydub (PCM Audio generation)

## 📡 WebSocket API
The hardware communicates with the brain on `/ws`:
- **Inbound (Hardware -> Brain)**:
    - `IDENTITY:{"name": "...", "persona": "..."}`
    - `DISTANCE:int` (Ultrasonic reading)
    - `BATTERY:float` (Voltage)
    - `CURRENT:float` (Amperage)
- **Outbound (Brain -> Hardware)**:
    - `CMD:MOVE`, `CMD:TRANSFORM`, etc.
    - `SAY:Text` (Triggers TTS)
    - `Binary PCM Data` (Direct audio stream)
