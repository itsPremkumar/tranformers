# 🧠 Omni-Morph AI Backend

This is the "Super-Brain" of the Omni-Morph robot. It handles high-level reasoning, vision processing, and coordinates hardware via WebSockets.

## 🚀 Quick Start (Local Testing)

If you are testing the robot's vision and AI locally on your laptop:

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** (Optional, for local AI): [Download Ollama](https://ollama.com)

### 2. Installation
```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in this directory:
```env
# AI Choice
OLLAMA_MODEL=gemma4:e4b  # Or qwen2.5vl:3b
GEMINI_API_KEY=your_key_here

# Camera Settings
USE_LOCAL_CAMERA=True
LOCAL_CAMERA_INDEX=0  # Usually 0 for built-in, 1 for external USB
```

### 4. Running the Brain
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Access Dashboard
Open [http://localhost:8000/dashboard](http://localhost:8000/dashboard) to see the live feed and control the robot.

## 🛠 Features
- **Shared Camera Streaming**: Unified /video_feed for dashboard and AI tools.
- **Multi-Model LLM Factory**: Supports Gemini 1.5 and Local Ollama with vision.
- **Reactive Vision**: Face, ball, and gesture tracking (Local CPU).
- **Persistent Memory**: SQLite-based memory for unique robot personalities.
