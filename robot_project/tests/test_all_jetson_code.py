#!/usr/bin/env python3
"""
Master Unit Test Suite for NVIDIA Jetson Upgrades
-------------------------------------------------
Validates syntax, import reliability, and execution logic of all newly added 
Jetson python scripts and ROS 2 package components under mocked conditions.
"""

import unittest
import sys
import os
import sqlite3
import json
from unittest.mock import MagicMock, patch

# Add directories to system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jetson/ai')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jetson/vision')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jetson/speech')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jetson/communications')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ros2_ws/src/robot_bridge')))

# Imports
from ollama_client import OllamaClient
from memory_vault import LocalMemoryVault
from camera_streamer import JetsonCameraStreamer
from whisper_stt import WhisperTranscriber
from piper_tts import PiperSpeaker
from mqtt_client import RobotMqttClient
from webrtc_streamer import WebRtcStreamer

class TestJetsonAI(unittest.TestCase):
    @patch('urllib.request.urlopen')
    def test_ollama_client_success(self, mock_urlopen):
        # Mock successful JSON response from Ollama API
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"response": "I am the robot brain."}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = OllamaClient(model="test-model")
        res = client.query("Who are you?")
        self.assertEqual(res, "I am the robot brain.")
        
    @patch('urllib.request.urlopen')
    def test_ollama_client_connection_error(self, mock_urlopen):
        # Mock connection failure raising URLError
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        client = OllamaClient()
        res = client.query("Hello")
        self.assertIn("offline", res.lower())

    def test_memory_vault_db_operations(self):
        # Test SQLite parent-child RAG database representation
        temp_db = "temp_test_vault.db"
        vault = LocalMemoryVault(temp_db)
        
        # Insert test memory
        vault.store_memory("Omni-Morph has 18 joints.", "specs")
        vault.store_memory("Transform mode uses L298N.", "specs")
        
        # Retrieve and verify
        results = vault.retrieve_memories("joints")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "Omni-Morph has 18 joints.")
        self.assertEqual(results[0]["category"], "specs")
        
        # Cleanup
        if os.path.exists(temp_db):
            os.remove(temp_db)

class TestJetsonVision(unittest.TestCase):
    def test_gstreamer_pipeline_generation(self):
        streamer = JetsonCameraStreamer(width=1280, height=720, framerate=60, flip_method=2)
        pipeline = streamer.get_gstreamer_pipeline()
        
        # Verify accelerated nvarguscamerasrc parameters are formatted correctly
        self.assertIn("nvarguscamerasrc", pipeline)
        self.assertIn("width=(int)1280", pipeline)
        self.assertIn("height=(int)720", pipeline)
        self.assertIn("framerate=(fraction)60/1", pipeline)
        self.assertIn("flip-method=2", pipeline)

class TestJetsonSpeech(unittest.TestCase):
    def test_whisper_transcription_missing_file(self):
        transcriber = WhisperTranscriber()
        # Verify node handles missing wave inputs cleanly
        res = transcriber.transcribe_wav("non_existent_audio.wav")
        self.assertEqual(res, "")

    @patch('subprocess.run')
    def test_whisper_transcription_success(self, mock_run):
        # Mock successful subprocess execution outputting transcript text
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello robot\n"
        mock_run.return_value = mock_result
        
        # Create a dummy empty file to satisfy path checks
        dummy_file = "dummy_transcribe.wav"
        with open(dummy_file, "w") as f:
            f.write("")
            
        transcriber = WhisperTranscriber(whisper_bin="mock-bin")
        res = transcriber.transcribe_wav(dummy_file)
        self.assertEqual(res, "hello robot")
        
        if os.path.exists(dummy_file):
            os.remove(dummy_file)

    @patch('subprocess.Popen')
    def test_piper_tts_success(self, mock_popen):
        # Mock successful subprocess audio generation
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("stdout", "stderr")
        mock_popen.return_value = mock_process
        
        speaker = PiperSpeaker(piper_bin="mock-piper")
        
        # Mock audio play method to prevent executing Alsa system tools
        speaker.play_audio = MagicMock()
        
        success = speaker.speak("Testing voice synthesis.", "output.wav")
        self.assertTrue(success)
        speaker.play_audio.assert_called_with("output.wav")

class TestJetsonCommunications(unittest.TestCase):
    def test_mqtt_telemetry_payload(self):
        client = RobotMqttClient(endpoint="test-endpoint", client_id="RobotTest")
        client.connect()
        
        success = client.publish_telemetry("test/topic", {"battery": 8.0})
        self.assertTrue(success)

    def test_webrtc_streamer_instantiation(self):
        streamer = WebRtcStreamer(port=9999)
        self.assertEqual(streamer.port, 9999)
        self.assertFalse(streamer.is_running)

if __name__ == "__main__":
    print("[TESTS] Running Master Jetson Unit Test Suite...")
    unittest.main()
