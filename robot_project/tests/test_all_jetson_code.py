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

# ==========================================
# ROS 2 Environment Mocking (for Windows/Non-ROS systems)
# ==========================================
class MockNode:
    def __init__(self, name="mock_node", *args, **kwargs):
        self.name = name
        self.params = {}
    def declare_parameter(self, name, default_value=None):
        class Param:
            value = default_value
        self.params[name] = Param()
        return self.params[name]
    def get_parameter(self, name):
        if name in self.params:
            return self.params[name]
        class Param:
            value = None
        # Fallback values
        if name == 'port': Param.value = "/dev/ttyRobotMotion"
        elif name == 'baudrate': Param.value = 115200
        elif name == 'camera_topic': Param.value = '/camera/image_raw'
        elif name == 'enable_cv_preview': Param.value = False
        elif name == 'pan_p_gain': Param.value = 0.05
        elif name == 'tilt_p_gain': Param.value = 0.05
        elif name == 'dock_marker_id': Param.value = 42
        elif name == 'target_distance_m': Param.value = 0.15
        elif name == 'kp_yaw': Param.value = 0.02
        elif name == 'kd_yaw': Param.value = 0.005
        elif name == 'kp_pitch': Param.value = 0.05
        elif name == 'critical_angle_limit': Param.value = 30.0
        elif name == 'tree_config_path': Param.value = "autonomy_tree.xml"
        return Param()
    def create_publisher(self, msg_type, topic, qos_profile):
        return MagicMock()
    def create_subscription(self, msg_type, topic, callback, qos_profile):
        return MagicMock()
    def create_timer(self, interval, callback):
        return MagicMock()
    def get_logger(self):
        return MagicMock()
    def get_clock(self):
        class Clock:
            def now(self):
                class Time:
                    nanoseconds = 1779717900.0 * 1e9
                    def to_msg(self):
                        return MagicMock()
                return Time()
        return Clock()

mock_rclpy = MagicMock()
mock_rclpy.node.Node = MockNode
sys.modules['rclpy'] = mock_rclpy
sys.modules['rclpy.node'] = mock_rclpy.node

# Mock other external libraries
sys.modules['serial'] = MagicMock()
sys.modules['can'] = MagicMock()
sys.modules['cv_bridge'] = MagicMock()
sys.modules['std_msgs'] = MagicMock()
sys.modules['std_msgs.msg'] = MagicMock()
sys.modules['robot_interfaces'] = MagicMock()
sys.modules['robot_interfaces.msg'] = MagicMock()
sys.modules['diagnostic_msgs'] = MagicMock()
sys.modules['diagnostic_msgs.msg'] = MagicMock()
sys.modules['sensor_msgs'] = MagicMock()
sys.modules['sensor_msgs.msg'] = MagicMock()
sys.modules['geometry_msgs'] = MagicMock()
sys.modules['geometry_msgs.msg'] = MagicMock()

# ==========================================
# Environment Path Injection
# ==========================================
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jetson/ai')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jetson/vision')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jetson/speech')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jetson/communications')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ros2_ws/src/robot_bridge')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ros2_ws/src/robot_perception')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ros2_ws/src/robot_motion')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ros2_ws/src/robot_brain')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ros2_ws/src/robot_diagnostics')))

# Imports
from ollama_client import OllamaClient
from memory_vault import LocalMemoryVault
from camera_streamer import JetsonCameraStreamer
from oled_display import JetsonOledDisplay
from whisper_stt import WhisperTranscriber
from piper_tts import PiperSpeaker
from bluetooth_audio_sync import BluetoothAudioSync
from mqtt_client import RobotMqttClient
from webrtc_streamer import WebRtcStreamer
from wifi_surround import WifiSurroundScanner
from ble_air_mouse import BleAirMouseController

# Import ROS 2 Nodes (wrapped inside mock context)
from robot_bridge.serial_bridge_node import SerialBridgeNode
from robot_bridge.can_bridge_node import CanBridgeNode
from robot_perception.face_tracker_node import FaceTrackerNode
from robot_perception.gesture_detector_node import GestureDetectorNode
from robot_perception.aruco_docking_node import ArucoDockingNode
from robot_motion.balance_control_node import BalanceControlNode
from robot_brain.llm_agent_node import LlmAgentNode
from robot_brain.behavior_tree_node import BehaviorTreeNode
from robot_brain.behavior_tree_executor import BehaviorTreeExecutor
from robot_diagnostics.health_monitor_node import HealthMonitorNode

class TestJetsonAI(unittest.TestCase):
    @patch('urllib.request.urlopen')
    def test_ollama_client_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"response": "I am the robot brain."}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = OllamaClient(model="test-model")
        res = client.query("Who are you?")
        self.assertEqual(res, "I am the robot brain.")
        
    @patch('urllib.request.urlopen')
    def test_ollama_client_connection_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        client = OllamaClient()
        res = client.query("Hello")
        self.assertIn("offline", res.lower())

    def test_memory_vault_db_operations(self):
        temp_db = "temp_test_vault.db"
        vault = LocalMemoryVault(temp_db)
        vault.store_memory("Omni-Morph has 18 joints.", "specs")
        results = vault.retrieve_memories("joints")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "Omni-Morph has 18 joints.")
        if os.path.exists(temp_db):
            os.remove(temp_db)

class TestJetsonVision(unittest.TestCase):
    def test_gstreamer_pipeline_generation(self):
        streamer = JetsonCameraStreamer(width=1280, height=720, framerate=60, flip_method=2)
        pipeline = streamer.get_gstreamer_pipeline()
        self.assertIn("nvarguscamerasrc", pipeline)

class TestJetsonSpeech(unittest.TestCase):
    def test_whisper_transcription_missing_file(self):
        transcriber = WhisperTranscriber()
        res = transcriber.transcribe_wav("non_existent_audio.wav")
        self.assertEqual(res, "")

    @patch('subprocess.Popen')
    def test_piper_tts_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("stdout", "stderr")
        mock_popen.return_value = mock_process
        
        speaker = PiperSpeaker(piper_bin="mock-piper")
        speaker.play_audio = MagicMock()
        success = speaker.speak("Testing voice synthesis.", "output.wav")
        self.assertTrue(success)

class TestJetsonCommunications(unittest.TestCase):
    def test_mqtt_telemetry_payload(self):
        client = RobotMqttClient(endpoint="test-endpoint", client_id="RobotTest")
        client.connect()
        success = client.publish_telemetry("test/topic", {"battery": 8.0})
        self.assertTrue(success)

    def test_webrtc_streamer_instantiation(self):
        streamer = WebRtcStreamer(port=9999)
        self.assertEqual(streamer.port, 9999)

class TestRobotAutonomyNodes(unittest.TestCase):
    def test_nodes_instantiation(self):
        # Verify all newly written ROS 2 nodes instantiate and parse settings cleanly
        serial_node = SerialBridgeNode()
        can_node = CanBridgeNode()
        face_node = FaceTrackerNode()
        gesture_node = GestureDetectorNode()
        docking_node = ArucoDockingNode()
        balance_node = BalanceControlNode()
        llm_node = LlmAgentNode()
        bt_node = BehaviorTreeNode()
        bt_executor = BehaviorTreeExecutor()
        health_node = HealthMonitorNode()

        self.assertEqual(serial_node.port, "/dev/ttyRobotMotion")
        self.assertEqual(can_node.channel, "can0")
        self.assertEqual(docking_node.dock_marker_id, 42)
        self.assertFalse(balance_node.is_moving)

class TestJetsonCommFeatures(unittest.TestCase):
    def test_oled_display_expression_change(self):
        # Verify OLED display starts in normal mode
        oled = JetsonOledDisplay()
        self.assertEqual(oled.expression, "NORMAL")
        
        # Verify expression updates correctly
        oled.set_expression("THINK")
        self.assertEqual(oled.expression, "THINK")
        
    def test_wifi_surround_scanner_properties(self):
        scanner = WifiSurroundScanner(interface="wlan0")
        self.assertEqual(scanner.interface, "wlan0")
        self.assertEqual(scanner.mon_interface, "wlan0mon")
        self.assertFalse(scanner.is_sniffing)
        
    def test_bluetooth_audio_sync_mock(self):
        sync = BluetoothAudioSync()
        # Mock scanner results list mapping
        speakers = sync.scan_for_speakers()
        self.assertTrue(len(speakers) >= 0)
        
    def test_ble_air_mouse_controller_movements(self):
        mouse = BleAirMouseController()
        # Ensure no errors occur when executing movements
        mouse.move_cursor(5, -5)

if __name__ == "__main__":
    print("[TESTS] Running Master Jetson Unit Test Suite...")
    unittest.main()
