import os
import sys
import time
import subprocess
from pyngrok import ngrok
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_backend():
    # 1. Setup Ngrok
    print("\n[NGROK] Starting tunnel...")
    # You can set your auth token in .env as NGROK_AUTH_TOKEN
    auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if auth_token:
        ngrok.set_auth_token(auth_token)
    
    try:
        # Create a tunnel to port 8000
        public_url = ngrok.connect(8000).public_url
        print(f"\n[NGROK] Public URL: {public_url}")
        print(f"[NGROK] Update your Config.h with:")
        print(f"       AI_BRAIN_GLOBAL_HOST: \"{public_url.replace('https://', '').replace('http://', '')}\"")
        print(f"       AI_BRAIN_GLOBAL_PORT: 80")
        print("-" * 50)
    except Exception as e:
        print(f"[ERROR] Could not start ngrok: {e}")
        print("Make sure you have an account at ngrok.com and have set your auth token.")
        return

    # 2. Start FastAPI/Uvicorn
    print("[BACKEND] Starting AI Brain on http://localhost:8000")
    try:
        # We run uvicorn as a subprocess so we can keep the ngrok tunnel alive
        subprocess.run(["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping Backend and Ngrok...")
        ngrok.disconnect(public_url)

if __name__ == "__main__":
    start_backend()
