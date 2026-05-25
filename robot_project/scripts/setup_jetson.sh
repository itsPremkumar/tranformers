#!/usr/bin/env bash
# Jetson Architecture Auto-Setup & Dependencies Configurator

set -eo pipefail

echo "========================================================"
echo "🤖 Preparing Jetson Edge Architecture Environment..."
echo "========================================================"

# 1. Update OS packages
echo "[SYSTEM] Updating system repositories..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Core Diagnostics & Networking Utilities
echo "[SYSTEM] Installing required system tools..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    socat \
    can-utils \
    docker.io \
    docker-compose \
    && rm -rf /var/lib/apt/lists/*

# 3. Apply udev Device Mapping Rules
echo "[HARDWARE] Applying USB udev mapping rules..."
if [ -f "../configs/99-robot.rules" ]; then
    sudo cp ../configs/99-robot.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "[PASS] udev rules deployed and reloaded."
else
    echo "[FAIL] udev rules file not found in configs/."
fi

# 4. Enable I2S Hardware Output on Pin Header
echo "[AUDIO] Configuring 40-Pin header for I2S audio..."
if [ -d "/opt/nvidia/jetson-io" ]; then
    echo "Launching Jetson-IO to configure Pinout. Please enable I2S4 manually if prompt is interactive."
    # Non-interactive DTB modification for standard JetPack dev kits:
    # sudo /opt/nvidia/jetson-io/config-by-function.py -o dtb i2s4
else
    echo "[WARNING] Jetson-IO utility not found. Verify manual pin multiplexing configurations."
fi

# 5. SocketCAN Interface Initial Setup
echo "[COMMUNICATIONS] Preparing SocketCAN initialization scripts..."
cat << 'EOF' > ./setup_can.sh
#!/usr/bin/env bash
echo "Binding MTTCAN interfaces to SocketCAN network..."
sudo modprobe can
sudo modprobe can_raw
sudo modprobe mttcan || echo "Native MTTCAN not loaded (using SPI MCP2515?)."
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up
ip link show can0
EOF
chmod +x ./setup_can.sh
echo "[PASS] CAN scripts generated. Run './setup_can.sh' once transceiver is wired."

# 6. Docker Group Permissions
echo "[SECURITY] Configuring Docker user groups..."
sudo usermod -aG docker "$USER"
echo "[INFO] User added to 'docker' group. Please reboot or start a new shell session to apply."

echo "========================================================"
echo "✅ Jetson platform setup complete! Next steps: reboot."
echo "========================================================"
EOF
