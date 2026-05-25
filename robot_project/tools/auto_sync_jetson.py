#!/usr/bin/env python3
"""
Jetson Autodiscovery & Code Sync Tool
------------------------------------
This script runs on your PC. It automatically:
1. Detects the local subnet of your Wi-Fi interface.
2. Scans the subnet in parallel to locate the Jetson board (checking hostname, SSH port 22, and mDNS).
3. Caches the Jetson IP for fast reconnects.
4. Performs a wireless recursive upload of the local workspace to the Jetson over SSH.
"""

import os
import sys
import socket
import struct
import threading
import subprocess
import time
import json

# Configuration
JETSON_HOSTNAME = "jetson"       # Jetson's hostname (without .local)
DEFAULT_SSH_USER = "jetson"      # Default Jetson username
TARGET_WORKSPACE = "~/robot_project" # Destination folder on Jetson
CACHE_FILE = ".jetson_ip_cache"

class JetsonSyncTool:
    def __init__(self):
        self.jetson_ip = None
        self.ssh_user = DEFAULT_SSH_USER
        self.lock = threading.Lock()

    def get_local_ip(self):
        """Get the active local IP address of this computer."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Connect to an external IP to discover the local IP interface
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = "127.0.0.1"
        finally:
            s.close()
        return local_ip

    def get_subnet(self, ip):
        """Given an IP, return the class-C subnet prefix (e.g., 192.168.1)."""
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}"
        return None

    def test_ip_for_ssh(self, ip, results):
        """Check if an IP has SSH port 22 open and check hostname if possible."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, 22))
            if result == 0:
                # SSH Port is open! Try to get hostname
                try:
                    hostname, _, _ = socket.gethostbyaddr(ip)
                except socket.herror:
                    hostname = "unknown"
                
                with self.lock:
                    results.append((ip, hostname))
            sock.close()
        except Exception:
            pass

    def scan_network(self):
        """Scan the local subnet in parallel threads to find potential Jetson IPs."""
        local_ip = self.get_local_ip()
        subnet = self.get_subnet(local_ip)
        
        if not subnet or subnet.startswith("127.0.0"):
            print("[SCAN] Error: No active Wi-Fi or network interface found.")
            return []

        print(f"[SCAN] Detected local IP: {local_ip}. Scanning subnet {subnet}.0/24...")
        
        threads = []
        discovered_hosts = []
        
        # Scan 1 to 254 in parallel
        for i in range(1, 255):
            target_ip = f"{subnet}.{i}"
            if target_ip == local_ip:
                continue
            t = threading.Thread(target=self.test_ip_for_ssh, args=(target_ip, discovered_hosts))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        return discovered_hosts

    def resolve_mdns(self):
        """Try resolving via mDNS standard hostnames."""
        for name in [f"{JETSON_HOSTNAME}.local", f"{JETSON_HOSTNAME}"]:
            try:
                ip = socket.gethostbyname(name)
                print(f"[DISCOVERY] Successfully resolved hostname '{name}' to {ip}")
                return ip
            except socket.gaierror:
                pass
        return None

    def find_jetson(self):
        """Locates the Jetson board using cache, mDNS, and port scanning."""
        # 1. Check cache first
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    cache = json.load(f)
                    cached_ip = cache.get("ip")
                    # Quick check if SSH is open on cached IP
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    if sock.connect_ex((cached_ip, 22)) == 0:
                        sock.close()
                        print(f"[DISCOVERY] Found Jetson at cached IP: {cached_ip}")
                        self.jetson_ip = cached_ip
                        return True
                    sock.close()
            except Exception:
                pass

        # 2. Try mDNS resolution
        print("[DISCOVERY] Searching via mDNS...")
        ip = self.resolve_mdns()
        if ip:
            self.jetson_ip = ip
            self.save_cache(ip)
            return True

        # 3. Fallback to subnet scan
        print("[DISCOVERY] mDNS failed. Performing rapid subnet port scan...")
        hosts = self.scan_network()
        
        # Filter for candidates
        for ip, host in hosts:
            if JETSON_HOSTNAME in host.lower():
                print(f"[DISCOVERY] Found Jetson via scanner. IP: {ip}, Hostname: {host}")
                self.jetson_ip = ip
                self.save_cache(ip)
                return True
                
        # If hostname check didn't match, return the first IP that had port 22 open
        if hosts:
            print(f"[DISCOVERY] No hostnames matched '{JETSON_HOSTNAME}'.")
            for ip, host in hosts:
                print(f"Candidate IP: {ip} (SSH Open)")
            # Default to the first found SSH IP
            self.jetson_ip = hosts[0][0]
            self.save_cache(self.jetson_ip)
            return True

        return False

    def save_cache(self, ip):
        """Save Jetson IP details to file."""
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({"ip": ip, "timestamp": time.time()}, f)
        except Exception:
            pass

    def sync_code(self):
        """Syncs local robot_project files to the Jetson wirelessly using rsync or scp."""
        if not self.jetson_ip:
            print("[SYNC] Error: Jetson IP not set.")
            return False

        print("==================================================")
        print(f"🚀 Deploying Code Wirelessly to Jetson ({self.jetson_ip})")
        print("==================================================")

        # Get absolute workspace folder on PC (parent folder of robot_project)
        local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # Check if rsync is available on PC (Windows Git Bash or Linux/macOS)
        rsync_available = False
        try:
            result = subprocess.run(["rsync", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            rsync_available = (result.returncode == 0)
        except FileNotFoundError:
            pass

        if rsync_available:
            print("[DEPLOY] Using rsync for incremental delta transfers...")
            # Exclude folders that shouldn't be copied
            cmd = [
                "rsync", "-avz", "--delete",
                "--exclude", ".git",
                "--exclude", "__pycache__",
                "--exclude", "*.db",
                "--exclude", "*.bin",
                "--exclude", "logs/",
                local_dir + "/",
                f"{self.ssh_user}@{self.jetson_ip}:{TARGET_WORKSPACE}"
            ]
        else:
            print("[DEPLOY] rsync not found. Falling back to recursive SCP transfer...")
            # Create remote workspace folder first
            ssh_check_cmd = ["ssh", f"{self.ssh_user}@{self.jetson_ip}", f"mkdir -p {TARGET_WORKSPACE}"]
            subprocess.run(ssh_check_cmd)
            
            cmd = [
                "scp", "-r",
                local_dir,
                f"{self.ssh_user}@{self.jetson_ip}:{TARGET_WORKSPACE}/.."
            ]

        print(f"[DEPLOY] Executing command: {' '.join(cmd)}")
        try:
            # Run synchronization command
            result = subprocess.run(cmd, check=True)
            if result.returncode == 0:
                print("==================================================")
                print("✅ Code synced wirelessly successfully!")
                print("==================================================")
                
                # Proactively trigger build/run script on Jetson
                print("[DEPLOY] Restarting Docker Services on Jetson...")
                restart_cmd = ["ssh", f"{self.ssh_user}@{self.jetson_ip}", f"cd {TARGET_WORKSPACE}/scripts && ./run_all.sh"]
                subprocess.run(restart_cmd)
                return True
        except subprocess.CalledProcessError as e:
            print(f"[DEPLOY] Error during file transfer: {e}")
            print("[HELP] Make sure you have configured SSH Key authorization or that your password is correct.")
        except Exception as e:
            print(f"[DEPLOY] Unexpected error: {e}")
        return False

def main():
    sync_tool = JetsonSyncTool()
    
    # Optional CLI arguments for user customization
    if len(sys.argv) > 1:
        sync_tool.ssh_user = sys.argv[1]

    print("🔎 Starting Jetson Auto-Discovery...")
    if sync_tool.find_jetson():
        sync_tool.sync_code()
    else:
        print("[DISCOVERY] Error: Could not locate Jetson on the network.")
        print("[HELP] Check that the Jetson is powered, connected to the same Wi-Fi network, and that SSH is enabled.")

if __name__ == "__main__":
    main()
