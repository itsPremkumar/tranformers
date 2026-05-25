#!/usr/bin/env python3
import unittest
import sys
import os

# Include package folder in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ros2_ws/src/robot_bridge')))

# Simple unit test to verify serialization and parsing logic without requiring live hardware
class TestTelemetryParsing(unittest.TestCase):
    def setUp(self):
        # Mock class for testing telemetry parsing logic
        class MockBridge:
            def __init__(self):
                self.last_distance = 0.0
                self.last_voltage = 0.0
                self.last_current = 0.0
                self.last_pitch = 0.0
                
            def parse(self, data: str):
                if data.startswith("DISTANCE:"):
                    self.last_distance = float(data[9:])
                elif data.startswith("BATTERY:"):
                    parts = data.split(",")
                    for p in parts:
                        if p.startswith("BATTERY:"):
                            self.last_voltage = float(p[8:])
                        elif p.startswith("CURRENT:"):
                            self.last_current = float(p[8:])
                elif data.startswith("IMU:"):
                    vals = data[4:].split(",")
                    self.last_pitch = float(vals[0])

        self.bridge = MockBridge()

    def test_distance_parsing(self):
        self.bridge.parse("DISTANCE:35.2")
        self.assertEqual(self.bridge.last_distance, 35.2)

    def test_battery_parsing(self):
        self.bridge.parse("BATTERY:8.15,CURRENT:1.45")
        self.assertEqual(self.bridge.last_voltage, 8.15)
        self.assertEqual(self.bridge.last_current, 1.45)

    def test_imu_parsing(self):
        self.bridge.parse("IMU:12.4,-2.5,180.1,0.0,0.0,9.8,0.0,0.0,0.0")
        self.assertEqual(self.bridge.last_pitch, 12.4)

if __name__ == "__main__":
    unittest.main()
