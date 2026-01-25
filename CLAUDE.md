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

### Disply info
- **6-color palette only** - all other colors approximated via Floyd-Steinberg dithering
- Images require preprocessing for best results:
  - Boost saturation (factor 2.0-3.0) to compensate for e-paper
  - Increase contrast (factor ~1.5)
  - High-contrast images work best
  - Limited color palette images (artwork) display better than subtle gradients
- Faint traces of previous images may persist - avoid
- Mitigated by periodic full refreshes
- For photo frames with infrequent updates, ghosting is minimal
- **Wide viewing angle** (~170°)
- **Contrast ratio**: ~30:1 (lower than LCD/OLED)
- Requires well-lit environment (no backlight)
- Paper-like matte appearance
- **Native resolution**: 1600 x 1200 pixels
- **Formats**: PNG, JPEG (library handles conversion)
- **Best content**: High contrast, bold colors, clear subject matter
- **Avoid**: Subtle gradients, low contrast, muted tones

## Project Status

Early stage - architecture and implementation in progress.

## Planned Features

### Photo Sources (Modular)
1. **Local folder** - Watch directory for new photos via `watchdog`
2. **iCloud Photos** - Direct API access via `pyicloud` library

### iCloud Integration Constraints
- **Library**: `pyicloud` (https://github.com/picklepete/pyicloud)
- **Authentication**: Apple ID + password (app-specific passwords NOT supported)
- **2FA**: Interactive code entry on first run, session stored (~2 month expiry)
- **Critical constraint**: Advanced Data Protection must be disabled on iCloud account
- **Rate limiting**: ~30 seconds per photo (Apple throttling)
- Downloads to local cache before display

### Image Processing Pipeline
- Smart cropping (4:3 aspect ratio, bias top for portraits)
- P3 → sRGB conversion for iPhone photos
- Resize to 1600x1200 (LANCZOS)
- 6-color palette + Floyd-Steinberg dithering

### Key Dependencies
```
inky[rpi,example-depends]>=1.5.0   # Pimoroni Inky library
Pillow>=10.0.0                      # Image processing
pillow-heif>=0.13.0                # HEIC support
watchdog>=3.0.0                     # File watching
pyicloud>=1.0.0                     # iCloud Photos API
numpy>=1.24.0
toml>=0.10.0
```

### Architecture (Simple, Few Files)
```
inky-photo-frame/
├── main.py                  # Entry point
├── src/
│   ├── display_manager.py   # Inky display (singleton with retry logic)
│   ├── photo_processor.py   # Smart crop + color processing
│   ├── photo_sources.py     # Local + iCloud sources (unified interface)
│   └── config.py            # TOML configuration
├── requirements.txt
└── config.toml
```
