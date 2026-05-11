import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Transformer Robot AI Brain"
    VERSION = "2.0.0"
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    
    # Vision
    ESP32_CAM_URL = os.getenv("ESP32_CAM_URL", "http://192.168.1.50/mjpeg")
    USE_LOCAL_CAMERA = os.getenv("USE_LOCAL_CAMERA", "False").lower() == "true"
    LOCAL_CAMERA_INDEX = int(os.getenv("LOCAL_CAMERA_INDEX", "0"))
    
    # Model Selection
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama-omni2")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

settings = Settings()
