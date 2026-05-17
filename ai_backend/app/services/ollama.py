import subprocess
import socket

def check_ollama():
    """Ensures Ollama is running before the backend starts."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', 11434)) != 0:
            print("[OLLAMA] Server not detected. Starting Ollama automatically...")
            # Try to start Ollama in the background
            try:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("[OLLAMA] Started successfully.")
            except Exception as e:
                print(f"[OLLAMA] Error starting: {e}")
