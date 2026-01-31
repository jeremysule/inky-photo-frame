#!/usr/bin/env bash
# Docker wrapper for build-image.py that works on macOS
# Uses a privileged container to access loop devices for mounting images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Docker image to use
DOCKER_IMAGE="ubuntu:24.04"

echo "Building Inky Photo Frame SD card image via Docker..."

# Parse arguments to pass through to Python script
PYTHON_ARGS=()
while [[ $# -gt 0 ]]; do
    PYTHON_ARGS+=("$1")
    shift
done

# Run in privileged container with access to loop devices
# We mount the project directory and build directory
docker run --rm -it \
    --privileged \
    -v "$(pwd):/workspace:rw" \
    -w /workspace \
    "$DOCKER_IMAGE" \
    bash -c '
        # Install dependencies
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq
        apt-get install -y -qq python3 python3-pip lzma sudo wget > /dev/null

        # Install Python dependencies (if any needed beyond stdlib)
        pip3 install -q break-system-packages 2>/dev/null || true

        # Run the build script
        echo "Running build-image.py..."
        python3 build-image.py "${@}"
    ' bash -- "${PYTHON_ARGS[@]}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Image built successfully!${NC}"
    echo "Location: build/inky-frame-inky-frame.img"
    echo ""
    echo "Flash with:"
    echo "  - Raspberry Pi Imager: https://www.raspberrypi.com/software/"
    echo "  - Or from terminal: sudo dd if=build/inky-frame-inky-frame.img of=/dev/rdiskN bs=1m"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
