from pydub import AudioSegment
import os

def resample_to_robot_pcm(source_path: str) -> bytes:
    """
    Dynamically loads any MP3, WAV, or other audio files, resamples it to 16kHz Mono 16-bit PCM,
    and returns the raw PCM byte array for direct ESP32 speaker playback.
    """
    print(f"[RESAMPLER] Resampling '{source_path}' to 16kHz Mono 16-bit PCM...")
    try:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Audio file not found: {source_path}")
            
        # Load audio file using pydub
        audio = AudioSegment.from_file(source_path)
        
        # Enforce 16000Hz, mono (1 channel), and 16-bit width (2 bytes)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        return audio.raw_data
    except Exception as e:
        print(f"[RESAMPLER] Resampling error: {e}")
        return b""
