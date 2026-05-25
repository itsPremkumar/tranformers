#!/usr/bin/env python3
import subprocess
import os

class WhisperTranscriber:
    def __init__(self, model_path="models/ggml-base.bin", whisper_bin="./whisper-cli"):
        self.model_path = model_path
        self.whisper_bin = whisper_bin

    def transcribe_wav(self, audio_file: str) -> str:
        if not os.path.exists(audio_file):
            print(f"[STT] Audio file not found: {audio_file}")
            return ""

        # Invoke whisper-cli compiled for CUDA acceleration
        cmd = [
            self.whisper_bin,
            "-m", self.model_path,
            "-f", audio_file,
            "-nt"  # No timestamps
        ]
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"[STT] Transcription error: {result.stderr}")
                return ""
        except subprocess.TimeoutExpired:
            print("[STT] Transcription timeout.")
            return ""
        except FileNotFoundError:
            # Fallback mock for testing without compiled binary
            print("[STT] CLI binary not found. Running speech mock.")
            return "help transform robot"

if __name__ == "__main__":
    stt = WhisperTranscriber()
    print("Transcribed text:", stt.transcribe_wav("test_audio.wav"))
