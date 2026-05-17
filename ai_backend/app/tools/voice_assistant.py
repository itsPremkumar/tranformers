import os
import queue
import json
import asyncio
import numpy as np
import webrtcvad
import sounddevice as sd
import wave
import tempfile
from vosk import Model, KaldiRecognizer
from faster_whisper import WhisperModel
import sys

# Ensure the model directory exists or download it
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from scripts.download_models import download_vosk_model

class VoiceAssistant:
    def __init__(self, wake_word="omni"):
        self.wake_words = [wake_word.lower(), "jarvis", "optimus"]
        self.sample_rate = 16000
        
        print("[VOICE] Initializing Vosk Wake-Word Model...")
        model_path = download_vosk_model()
        self.vosk_model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.vosk_model, self.sample_rate)
        
        print("[VOICE] Initializing Faster-Whisper Model (tiny)...")
        # tiny model is fast and works well for general STT on CPU
        self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        
        self.vad = webrtcvad.Vad(3) # Aggressive silence detection
        self.audio_queue = queue.Queue()
        self.is_listening = True

    def audio_callback(self, indata, frames, time, status):
        """This is called for each audio block by sounddevice."""
        if status:
            print(f"[AUDIO] {status}")
        self.audio_queue.put(bytes(indata))

    async def listen_for_wake_word(self):
        """Continuously listens for the wake word using the local microphone."""
        print(f"[VOICE] Listening for wake words: {self.wake_words}...")
        
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000, device=None,
                               dtype='int16', channels=1, callback=self.audio_callback):
            while self.is_listening:
                data = self.audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    detected_word = next((w for w in self.wake_words if w in text), None)
                    if detected_word:
                        print(f"\n[VOICE] Wake word '{detected_word}' DETECTED!")
                        return True
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get("partial", "").lower()
                    detected_word = next((w for w in self.wake_words if w in partial_text), None)
                    if detected_word:
                        print(f"\n[VOICE] Wake word '{detected_word}' DETECTED (partial)!")
                        # Clear queue before returning to avoid processing old data
                        with self.audio_queue.mutex:
                            self.audio_queue.queue.clear()
                        return True
                await asyncio.sleep(0.01)

    def record_until_silence(self):
        """Records from the microphone until silence is detected."""
        print("[VOICE] Recording command... (Speak now)")
        
        frames = []
        silence_duration = 0.0
        max_silence = 1.5 # seconds of silence before stopping
        frame_duration = 30 # ms
        frame_size = int(self.sample_rate * (frame_duration / 1000.0) * 2) # 2 bytes per sample (int16)
        
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=int(self.sample_rate * (frame_duration / 1000.0)), 
                               device=None, dtype='int16', channels=1) as stream:
            while True:
                data, overflowed = stream.read(stream.blocksize)
                if overflowed:
                    pass
                
                raw_data = bytes(data)
                frames.append(raw_data)
                
                # Check VAD
                is_speech = self.vad.is_speech(raw_data, self.sample_rate)
                if not is_speech:
                    silence_duration += (frame_duration / 1000.0)
                else:
                    silence_duration = 0.0
                
                if silence_duration > max_silence:
                    print("[VOICE] Silence detected. Stopping recording.")
                    break
        
        # Save to temp wav file
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            
        return temp_path

    async def process_speech(self):
        """The main loop: Wait for wake word -> Record -> STT -> Return text."""
        await self.listen_for_wake_word()
        
        # We detected the wake word, now record the user's command
        audio_file = await asyncio.to_thread(self.record_until_silence)
        
        print("[VOICE] Transcribing with Whisper...")
        # Transcribe with language detection
        segments, info = await asyncio.to_thread(self.whisper_model.transcribe, audio_file, beam_size=5)
        
        text = "".join([segment.text for segment in segments]).strip()
        os.remove(audio_file) # Cleanup
        
        print(f"[VOICE] Transcription: '{text}' (Language: {info.language})")
        return text, info.language

# Singleton instance
voice_assistant = VoiceAssistant()
