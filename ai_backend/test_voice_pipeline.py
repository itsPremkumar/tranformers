import os
import asyncio
import time
from gtts import gTTS
from pydub import AudioSegment
import io
import wave
import tempfile
import sys

# Ensure the app context is available
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.tools.voice_assistant import voice_assistant
except ImportError as e:
    print(f"Failed to import voice_assistant: {e}")
    print("Please make sure you have run: pip install -r requirements.txt")
    sys.exit(1)

def generate_test_audio(text: str, lang: str):
    """Generates a .wav file with TTS to simulate a human speaking into the mic."""
    print(f"Generating test audio for: '{text}' ({lang})")
    
    # 1. Generate MP3 using gTTS
    tts = gTTS(text=text, lang=lang)
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    
    # 2. Convert to PCM 16kHz Mono using pydub
    audio = AudioSegment.from_file(mp3_fp, format="mp3")
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    
    # 3. Save to temp wav file
    fd, temp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    
    with wave.open(temp_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(16000)
        wf.writeframes(audio.raw_data)
        
    return temp_path

async def run_voice_tests():
    print("========================================")
    print("   VOICE ASSISTANT PIPELINE TEST")
    print("========================================\n")
    
    tests = [
        {"name": "English STT", "text": "Move forward and look for the ball", "lang": "en"},
        {"name": "Tamil STT", "text": "Munnadi po", "lang": "ta"} # "Go forward" in Tamil
    ]
    
    results = []
    
    for test in tests:
        print(f"--- Running Test: {test['name']} ---")
        audio_file = generate_test_audio(test['text'], test['lang'])
        
        start_time = time.time()
        print("[TEST] Transcribing with Faster-Whisper...")
        
        try:
            # We bypass the wake-word microphone recording and directly test the Whisper model
            segments, info = await asyncio.to_thread(voice_assistant.whisper_model.transcribe, audio_file, beam_size=5)
            transcribed_text = "".join([segment.text for segment in segments]).strip()
            
            latency = (time.time() - start_time) * 1000
            
            print(f"[TEST] Expected Language: {test['lang']}")
            print(f"[TEST] Detected Language: {info.language}")
            print(f"[TEST] Transcribed Text: '{transcribed_text}'")
            print(f"[TEST] Latency: {latency:.2f}ms")
            
            # Simple check to see if the detected language matches our expected language
            # Whisper uses 'en' for English and 'ta' for Tamil.
            status = "PASS" if info.language == test['lang'] else "FAIL"
            print(f"Result: {status}\n")
            
            results.append({
                "name": test["name"],
                "status": status,
                "detected": info.language,
                "latency": latency
            })
            
        except Exception as e:
            print(f"Test Failed with Error: {e}")
            results.append({"name": test["name"], "status": "ERROR"})
            
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
    # Print Summary Report
    print("========================================")
    print("              TEST REPORT")
    print("========================================")
    for r in results:
        status = r.get("status", "FAIL")
        print(f"Test: {r['name']:<15} | Status: {status:<4} | Lang: {r.get('detected', 'N/A'):<2} | Latency: {r.get('latency', 0):.2f}ms")

if __name__ == "__main__":
    asyncio.run(run_voice_tests())
