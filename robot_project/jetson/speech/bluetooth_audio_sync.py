#!/usr/bin/env python3
import subprocess
import time
import re

class BluetoothAudioSync:
    def __init__(self):
        self.device_mac = None

    def scan_for_speakers(self, duration=5):
        """Scans for nearby Bluetooth devices and filters for potential audio speakers."""
        print("[BT-AUDIO] Scanning for wireless audio speakers...")
        try:
            # Start scan in background via bluetoothctl
            subprocess.run(["bluetoothctl", "scan", "on"], timeout=duration, stdout=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            pass # Expected timeout
        except FileNotFoundError:
            print("[BT-AUDIO] bluetoothctl tool not found. Running mock BT discovery.")
            return [("00:11:22:33:44:55", "JBL Flip Speaker Mock")]

        # Read scanned devices list
        result = subprocess.run(["bluetoothctl", "devices"], stdout=subprocess.PIPE, text=True)
        devices = []
        for line in result.stdout.strip().split('\n'):
            match = re.match(r"Device\s+([0-9A-Fa-f:]+)\s+(.+)", line)
            if match:
                mac, name = match.groups()
                # Simple name filter matching common speakers
                if any(keyword in name.lower() for keyword in ["speaker", "jbl", "audio", "headphone", "soundbar"]):
                    devices.append((mac, name))
        return devices

    def connect_speaker(self, mac: str):
        """Pairs, trusts, and connects to the target Bluetooth speaker MAC."""
        print(f"[BT-AUDIO] Attempting wireless pair connection to {mac}...")
        try:
            # Trust and pair device
            subprocess.run(["bluetoothctl", "trust", mac], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["bluetoothctl", "pair", mac], check=True, stdout=subprocess.DEVNULL)
            
            # Connect device
            result = subprocess.run(["bluetoothctl", "connect", mac], stdout=subprocess.PIPE, text=True)
            if "Connection successful" in result.stdout or self.is_connected(mac):
                print(f"[PASS] Connected successfully to Bluetooth audio speaker {mac}.")
                self.route_audio_to_bluetooth(mac)
                return True
            else:
                print(f"[FAIL] Connection failed: {result.stdout.strip()}")
        except Exception as e:
            print(f"[ERR] Bluetooth connection execution exception: {e}")
        return False

    def is_connected(self, mac: str) -> bool:
        result = subprocess.run(["bluetoothctl", "info", mac], stdout=subprocess.PIPE, text=True)
        return "Connected: yes" in result.stdout

    def route_audio_to_bluetooth(self, mac: str):
        """Finds the corresponding PulseAudio/PipeWire sink and sets it as the default output."""
        # Convert MAC address format from AA:BB:CC:DD:EE:FF to bluez format bluez_sink.AA_BB_CC_DD_EE_FF
        bluez_mac = mac.replace(":", "_")
        sink_name = f"bluez_sink.{bluez_mac}.a2dp_sink"
        
        print(f"[BT-AUDIO] Routing system audio to PulseAudio sink: {sink_name}")
        try:
            # Set default audio sink
            result = subprocess.run(["pactl", "set-default-sink", sink_name], stdout=subprocess.PIPE, text=True)
            if result.returncode == 0:
                print("[PASS] System audio output successfully routed to Bluetooth speaker.")
            else:
                # Fallback for PipeWire setups
                subprocess.run(["wpctl", "set-default", sink_name])
        except Exception:
            # Fallback mock logs
            print("[BT-AUDIO] pactl/wpctl command tools not available. Mocking audio routing.")

if __name__ == "__main__":
    sync = BluetoothAudioSync()
    speakers = sync.scan_for_speakers(duration=2)
    if speakers:
        print("Discovered speakers:")
        for mac, name in speakers:
            print(f" - {name} ({mac})")
        sync.connect_speaker(speakers[0][0])
