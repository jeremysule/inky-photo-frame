<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal photo frame project using an e-paper display for displaying family photos. This is a private project not intended for public sharing.

## Hardware

- **Display**: Inky Impression 13.3" (2025 edition) - https://thepihut.com/products/inky-impression-13-3-2025-edition
- **Computer**: Raspberry Pi 4 model B
- **Storage**: SD Card

## Reference Sources

- **Pimoroni Inky Library**: https://github.com/pimoroni/inky
  - Official Python library for all Inky e-paper displays
  - Source code for `inky_el133uf1.py` (13.3" Impression driver)
  - Examples for Spectra 6 color palette usage
  - Auto-detection via `inky.auto.auto()`

## Display Specifications

### Technical Specs
- **Resolution**: 1600 x 1200 pixels (4:3 aspect ratio)
- **Pixel Density**: 150 PPI
- **Colors**: 6-color E Ink Spectra 6 palette (black, white, red, green, blue, yellow)
- **Board Dimensions**: 297 x 210mm (A4 size)
- **Viewable Area**: 270.40 x 202.80mm
- **Operating Temperature**: 0°C to 50°C (optimal: 25°C to 50°C)

### Refresh Characteristics
- **Advertised Refresh**: ~12 seconds at optimal temperatures (25-50°C)
- **Real-world Refresh**: 27-35 seconds total cycle (including data transfer over SPI)
- **Cold Temperature Impact**: Significantly slower below 25°C

### Refresh Rate Constraints
- **Not suitable for dynamic content** - animations, video, or rapid updates
- E-paper technology physically repositions pigment particles (inherently slow)
- Best for static content updated infrequently (daily/weekly)

### Display Info
- **6-color palette only** - colors approximated via palette blending + Floyd-Steinberg dithering
- The Inky library handles all palette quantization and dithering via `set_image(image, saturation=0.5)`
- Two saturation controls:
  - **`display.saturation`** (0.0-1.0): Controls palette blending in the Inky library
    - 0.0 = fully desaturated palette (pure RGB colors)
    - 0.5 = balanced (default, recommended)
    - 1.0 = fully saturated palette (muted, darker colors)
  - **`processing.saturation`** (1.0-2.0): Pre-processing boost applied before quantization
    - Boosts source image colors to compensate for e-paper's limited color range
    - Typical range: 1.2-1.5
- **Wide viewing angle** (~170°)
- **Contrast ratio**: ~30:1 (lower than LCD/OLED)
- Requires well-lit environment (no backlight)
- Paper-like matte appearance
- **Best content**: High contrast, bold colors, clear subject matter
- **Avoid**: Subtle gradients, low contrast, muted tones

## Image Processing Pipeline

The image processing is split into two stages:

### Stage 1: Pre-Processing (Before Inky Library)
1. **Smart crop** to 4:3 aspect ratio (bias top for portraits)
2. **P3 → sRGB conversion** for iPhone photos with ICC profiles
3. **Resize** to 1600x1200 using LANCZOS resampling
4. **Enhance** saturation and contrast for e-paper characteristics

### Stage 2: Inky Library Processing
The Inky library's `set_image()` method handles:
- **Palette quantization**: Blends between DESATURATED_PALETTE and SATURATED_PALETTE
- **Floyd-Steinberg dithering**: Applied during quantization for smooth color transitions

**Important**: Do NOT implement custom dithering - the library handles this correctly.

### Official Color Palettes (from Inky library)

The library defines two palettes that are blended based on the `saturation` parameter:

```python
# DESATURATED_PALETTE (saturation = 0.0)
DESATURATED_PALETTE = [
    [0, 0, 0],         # Black
    [255, 255, 255],   # White
    [255, 255, 0],     # Yellow (pure)
    [255, 0, 0],       # Red (pure)
    [0, 0, 255],       # Blue (pure)
    [0, 255, 0],       # Green (pure)
]

# SATURATED_PALETTE (saturation = 1.0)
SATURATED_PALETTE = [
    [0, 0, 0],         # Black
    [161, 164, 165],   # White (grayish)
    [208, 190, 71],    # Yellow (darker/golden)
    [156, 72, 75],     # Red (dark rust)
    [61, 59, 94],      # Blue (dark navy)
    [58, 91, 70],      # Green (dark olive)
]
```

## Project Status

Implementation complete - see Deployment section for setup instructions.

## Key Dependencies

```
inky[rpi,example-depends]>=1.5.0   # Pimoroni Inky library (handles palette + dithering)
Pillow>=10.0.0                      # Image processing
pillow-heif>=0.13.0                # HEIC/HEIF support
watchdog>=3.0.0                     # File watching for local photos
pyicloud>=1.0.0                     # iCloud Photos API
toml>=0.10.0                        # Configuration parsing
colorlog>=6.0.0                     # Colored logging (optional)
```

## Architecture

```
inky-photo-frame/
├── main.py                  # Entry point, orchestrates all components
├── src/
│   ├── __init__.py
│   ├── config.py            # TOML configuration loader with validation
│   ├── display_manager.py   # Inky display singleton (wraps library, adds retry logic)
│   ├── photo_processor.py   # Pre-processing pipeline (crop, enhance, resize)
│   └── photo_sources.py     # Photo source interfaces (local + iCloud)
├── requirements.txt
├── config.toml              # User configuration template
├── sync-to-pi.sh            # SSH-based sync script for development
├── build-image.py           # SD card image generator
└── systemd/
    └── photo-frame.service  # Systemd service file
```

## Inky Library API Usage

### Initialization (Auto-Detection)
```python
from inky.auto import auto

inky = auto()  # Auto-detects display from EEPROM
# For 13.3" Impression: returns InkyEL133UF1(resolution=(1600, 1200))
```

### Setting Images
```python
from PIL import Image

image = Image.open("photo.jpg")
image = image.resize((1600, 1200))  # Must match display resolution

# saturation: 0.0 (desaturated) to 1.0 (saturated)
inky.set_image(image, saturation=0.5)
inky.show()  # Displays the image (~30 seconds)
```

### DisplayManager Wrapper (This Project)
```python
from src.display_manager import DisplayManager

display = DisplayManager.get_instance()
display.set_saturation(0.5)  # Set default saturation
display.set_image(processed_image)
display.show()
```

## Photo Sources

### Local Folder (Default)
- Path: `~/Photos/Frame` (configurable via `photo.local_path`)
- Uses `watchdog` for automatic file watching
- Supports: JPG, PNG, GIF, BMP, HEIC, HEIF, WEBP

### iCloud Photos (Optional)
- Library: `pyicloud`
- **Constraints**:
  - App-specific passwords NOT supported
  - Advanced Data Protection must be disabled
  - 2FA required on first run
  - ~30 seconds per photo (Apple rate limiting)
  - Session cached for ~2 months

## Configuration

Key configuration options in `config.toml`:

```toml
[display]
refresh_interval = 3600      # Seconds between photo changes
full_refresh_every = 10      # Full refresh cycle count
saturation = 0.5             # Palette saturation (0.0-1.0)

[processing]
saturation = 1.3             # Pre-processing boost (1.0-2.0)
contrast = 1.2               # Pre-processing boost (1.0-2.0)
portrait_bias = "top"        # Portrait crop bias

[photo]
local_path = "~/Photos/Frame"
selection_mode = "random"    # or "sequential"

[icloud]
enabled = false
apple_id = ""
```

## Deployment

### Method 1: Automated SD Card Image (Recommended)

Build a complete ready-to-flash SD card image with everything preconfigured:

```bash
# Basic build with WiFi
./build-image.py --wifi-ssid "YourNetwork" --wifi-password "YourPassword"

# Full build with SSH key and custom hostname
./build-image.py \
  --wifi-ssid "YourNetwork" \
  --wifi-password "YourPassword" \
  --ssh-pubkey "$HOME/.ssh/id_ed25519.pub" \
  --hostname "inky-frame"
```

**What the build script does:**
- Downloads latest Raspberry Pi OS Lite
- Configures WiFi via NetworkManager
- Enables SSH (headless setup)
- Sets hostname
- Installs app to `/opt/inky-photo-frame`
- Creates and enables systemd service (auto-starts on boot)

**Output:** `build/inky-frame-inky-frame.img` - flash with Raspberry Pi Imager or balenaEtcher

### Method 2: Manual Setup on Existing Pi

If you already have a Pi running:

```bash
# 1. Sync files to Pi
./sync-to-pi.sh pi@your-pi-hostname.local

# 2. SSH in and install dependencies
ssh pi@your-pi-hostname.local
sudo apt update
sudo apt install -y python3-pip python3-pil
pip3 install -r /opt/inky-photo-frame/requirements.txt

# 3. Install and enable systemd service
sudo cp /opt/inky-photo-frame/systemd/photo-frame.service /etc/systemd/system/
sudo systemctl enable photo-frame
sudo systemctl start photo-frame

# 4. View logs
sudo journalctl -u photo-frame -f
```
