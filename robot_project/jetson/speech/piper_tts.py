#!/usr/bin/env python3
import subprocess
import os

class PiperSpeaker:
    def __init__(self, model_path="models/en_US-lessac-medium.onnx", piper_bin="piper"):
        self.model_path = model_path
        self.piper_bin = piper_bin

    def speak(self, text: str, output_wav="response.wav"):
        # Invoke local Piper TTS executable
        cmd = [
            self.piper_bin,
            "--model", self.model_path,
            "--output_file", output_wav
        ]
        
        try:
            # Write text to stdin of piper process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=text, timeout=10)
            
            if process.returncode == 0:
                print(f"[TTS] Generated audio: {output_wav}")
                self.play_audio(output_wav)
                return True
            else:
                print(f"[TTS] Synthesis failed: {stderr}")
                return False
        except Exception as e:
            print(f"[TTS] Execution exception: {e}")
            return False

    def play_audio(self, filepath: str):
        # Plays audio using system ALSA interface directed to I2S
        try:
            subprocess.run(["aplay", "-D", "plughw:card=tegrasndt186ref,device=0", filepath], check=True)
        except FileNotFoundError:
            # Fallback if running locally
            try:
                subprocess.run(["play", filepath], check=True) # SoX
            except Exception:
                print(f"[AUDIO] Mock playing sound: {filepath}")

if __name__ == "__main__":
    speaker = PiperSpeaker()
    speaker.speak("Offline cognitive systems activated successfully.")
