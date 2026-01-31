#!/bin/bash
# Sync Inky Photo Frame to Raspberry Pi via SSH
#
# Usage: ./sync-to-pi.sh [pi-host]
#
# Default host: pi@inky-frame.local

set -e

# Configuration
PI_HOST="${1:-pi@inky-frame.local}"
REMOTE_DIR "~/inky-photo-frame"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Syncing to: $PI_HOST:$REMOTE_DIR"
echo "Project directory: $PROJECT_DIR"
echo ""

# Check if host is reachable
if ! ssh -o ConnectTimeout=5 "$PI_HOST" "echo -n 'pong'" >/dev/null 2>&1; then
    echo "Error: Cannot connect to $PI_HOST"
    echo "Please check:"
    echo "  1. The Pi is powered on and connected to the network"
    echo "  2. SSH is enabled on the Pi"
    echo "  3. The hostname/IP address is correct"
    exit 1
fi

echo "Host reachable. Starting sync..."
echo ""

# Create remote directory if it doesn't exist
ssh "$PI_HOST" "mkdir -p $REMOTE_DIR"

# Sync files using rsync
rsync -avz --delete \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.venv/' \
    --exclude='venv/' \
    --exclude='*.egg-info/' \
    --exclude='.pytest_cache/' \
    --exclude='config.toml' \
    "$PROJECT_DIR/" \
    "$PI_HOST:$REMOTE_DIR/"

echo ""
echo "Sync complete!"
echo ""
echo "Next steps on the Pi:"
echo "  1. Edit config: ssh $PI_HOST 'nano $REMOTE_DIR/config.toml'"
echo "  2. Restart service: ssh $PI_HOST 'sudo systemctl restart photo-frame'"
echo "  3. View logs: ssh $PI_HOST 'sudo journalctl -u photo-frame -f'"
