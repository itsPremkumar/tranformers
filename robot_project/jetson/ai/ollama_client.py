#!/usr/bin/env python3
import json
import urllib.request
import urllib.error

class OllamaClient:
    def __init__(self, host="localhost", port=11434, model="llama3:8b"):
        self.url = f"http://{host}:{port}/api/generate"
        self.model = model

    def query(self, prompt: str, system_prompt: str = "") -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_payload = json.loads(response.read().decode('utf-8'))
                return res_payload.get('response', '')
        except urllib.error.URLError as e:
            print(f"[OLLAMA] Connection failed: {e}")
            return "Cognitive engine offline. Verify Ollama service is running."
        except Exception as e:
            print(f"[OLLAMA] Error: {e}")
            return "Internal cognitive reasoning fault."

if __name__ == "__main__":
    client = OllamaClient()
    response = client.query("Hello! Introduce yourself in one sentence.")
    print("Ollama response:", response)
