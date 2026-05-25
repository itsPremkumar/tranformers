#!/usr/bin/env bash
# Network Configuration & Auto-Failover Setup Script for Jetson
# -----------------------------------------------------------
# Configures:
# 1. Direct Wi-Fi Access Point (Hotspot) for PC wireless control.
# 2. Priority metrics for Wi-Fi Client connections vs. USB Cellular Modems.
# 3. Dynamic network health checker cron script.

set -euo pipefail

echo "=========================================================="
echo "🌐 Configuring Autonomous Robot Network Settings..."
echo "=========================================================="

# Check for NetworkManager
if ! command -v nmcli &> /dev/null; then
    echo "[NET] NetworkManager (nmcli) is not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y network-manager
fi

# 1. Create Wi-Fi Hotspot Connection Profile
# This ensures that even in the field, the robot broadcasts its own SSID.
HOTSPOT_SSID="OmniMorph_AP"
HOTSPOT_PASS="omnimorph123"
INTERFACE="wlan0"

echo "[NET] Configuring wireless hotspot on interface: ${INTERFACE}"
echo "[NET] SSID: ${HOTSPOT_SSID} | Password: ${HOTSPOT_PASS}"

# Remove existing hotspot configuration if it exists to avoid duplicates
sudo nmcli connection delete "${HOTSPOT_SSID}" 2>/dev/null || true

# Setup Hotspot profile
sudo nmcli device wifi hotspot \
    ssid "${HOTSPOT_SSID}" \
    password "${HOTSPOT_PASS}" \
    ifname "${INTERFACE}" \
    con-name "${HOTSPOT_SSID}"

# Set the hotspot to auto-start if no other client Wi-Fi is available
sudo nmcli connection modify "${HOTSPOT_SSID}" connection.autoconnect yes
sudo nmcli connection modify "${HOTSPOT_SSID}" connection.autoconnect-priority 1

echo "[PASS] Hotspot profile '${HOTSPOT_SSID}' registered successfully."

# 2. Configure Metric Priorities (Failover Routing)
# We set Cellular/Ethernet backups to lower priority (higher metric value)
# than client Wi-Fi networks.
echo "[NET] Setting default route metrics..."

# Update standard USB cellular network metrics (e.g. usb0 or eth1 interfaces)
for con in $(nmcli -g NAME connection show); do
    if [[ "$con" == *"Cellular"* || "$con" == *"Wired"* || "$con" == *"usb"* ]]; then
        echo "[NET] Lowering priority of backup link: ${con}"
        sudo nmcli connection modify "${con}" ipv4.route-metric 200 || true
    elif [[ "$con" != "${HOTSPOT_SSID}" ]]; then
        echo "[NET] Raising priority of primary Wi-Fi link: ${con}"
        sudo nmcli connection modify "${con}" ipv4.route-metric 100 || true
    fi
done

# 3. Generate Autonomous Network Health Checker Script
HEALTH_CHECK_SCRIPT="/usr/local/bin/check_network_health.sh"
echo "[NET] Creating network health monitor script at: ${HEALTH_CHECK_SCRIPT}"

sudo bash -c "cat << 'EOF' > ${HEALTH_CHECK_SCRIPT}
#!/usr/bin/env bash
# Network Health Monitor: Pings 8.8.8.8 to verify internet connectivity.
# If primary Wi-Fi connection drops, it verifies failover is active.

TARGET_PING=\"8.8.8.8\"

if ping -c 2 -W 2 \${TARGET_PING} &> /dev/null; then
    # Internet is active.
    exit 0
else
    echo \"[NET_WARN] Internet lookup failed. Checking interfaces...\"
    # If connection fails, restart the network manager interface to trigger auto-reconnection
    sudo systemctl restart NetworkManager
fi
EOF"

sudo chmod +x "${HEALTH_CHECK_SCRIPT}"

# Set up cron job to execute checker script every 5 minutes
echo "[NET] Installing network health check cron job..."
CRON_JOB="*/5 * * * * ${HEALTH_CHECK_SCRIPT} >> /var/log/robot_network_health.log 2>&1"
(sudo crontab -l 2>/dev/null | grep -Fv "${HEALTH_CHECK_SCRIPT}"; echo "${CRON_JOB}") | sudo crontab -

echo "=========================================================="
echo "✅ Networking features implemented successfully!"
echo "=========================================================="
