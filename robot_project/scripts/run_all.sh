#!/usr/bin/env bash
# Startup Orchestrator for Jetson Robotic Stack

set -eo pipefail

echo "========================================================"
echo "🚀 Initializing Jetson Humanoid Robot Software Stack..."
echo "========================================================"

# Check if docker daemon is running
if ! systemctl is-active --quiet docker; then
    echo "[SYSTEM] Starting Docker daemon..."
    sudo systemctl start docker
fi

# Run CAN setup
if [ -f "./setup_can.sh" ]; then
    echo "[COMM] Loading SocketCAN drivers..."
    ./setup_can.sh || echo "[WARN] CAN interface setup failed. Check physical transceiver connections."
fi

# Launch Docker Compose
echo "[DEPLOY] Launching container orchestrations..."
cd ../deployment
docker-compose up -d

echo "[DEPLOY] Container statuses:"
docker-compose ps

echo "========================================================"
echo "✅ All robot services running in background."
echo "========================================================"
