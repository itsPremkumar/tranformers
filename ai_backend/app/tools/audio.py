from gtts import gTTS
from pydub import AudioSegment
import io
import os

# Fix for missing ffmpeg in PATH
ffmpeg_dir = r"C:\Program Files\Shotcut"
ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe.exe")

if os.path.exists(ffmpeg_path):
    os.environ["PATH"] += os.pathsep + ffmpeg_dir
    AudioSegment.converter = ffmpeg_path
if os.path.exists(ffprobe_path):
    AudioSegment.ffprobe = ffprobe_path

def generate_tts_pcm(text: str, lang: str = 'en'):
    """
    Generates a raw PCM 16kHz Mono audio stream for the ESP32.
    This is a blocking network call.
    """
    print(f"[ACTION] Generating TTS ({lang}) for: {text}")
    try:
        # 1. Generate MP3 using gTTS
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # 2. Convert to PCM 16kHz Mono using pydub
        audio = AudioSegment.from_file(mp3_fp, format="mp3")
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # 3. Return raw bytes
        return audio.raw_data
    except Exception as e:
        print(f"TTS Error: {e}")
        return None
