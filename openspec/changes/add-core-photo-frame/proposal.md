# Change: Add Core Photo Frame System

## Why

The project needs a complete foundational implementation of the photo frame system. Currently no code exists. This change implements the core functionality needed to display family photos on the Inky Impression 13.3" e-paper display from local and iCloud sources.

## What Changes

- **Display Manager**: Singleton class for Inky display control with retry logic for hardware reliability
- **Photo Processor**: Smart cropping (4:3 aspect, portrait bias), P3→sRGB conversion, saturation/contrast boost, 6-color palette mapping with Floyd-Steinberg dithering
- **Photo Sources**: Unified interface for local folder (watchdog) and iCloud (pyicloud) sources
- **Configuration**: TOML-based configuration system for all settings
- **Main Entry Point**: Script orchestrating photo selection, processing, and display rotation
- **SD Card Image Generation**: Script to generate a minimal, flashable Raspberry Pi OS image with preconfigured WiFi, auto-login, and auto-start service
- **Dev Sync Script**: SSH-based sync tool for quick development iteration (upload local changes to Pi, restart service)

## Impact

- **New capabilities**: display-manager, photo-processor, photo-sources, config, sd-card-image, dev-sync
- **New files**: `main.py`, `src/display_manager.py`, `src/photo_processor.py`, `src/photo_sources.py`, `src/config.py`, `requirements.txt`, `config.toml`, `build-image.py`, `image-config/`, `sync-to-pi.sh`
- **Dependencies**: inky>=1.5.0, Pillow>=10.0.0, pillow-heif>=0.13.0, watchdog>=3.0.0, pyicloud>=1.0.0, numpy>=1.24.0, toml>=0.10.0
- **Output**: Flashable SD card image (.img) ready for Balena Etcher

## Implementation Notes

- E-paper refresh takes 27-35 seconds - this is a static display, not dynamic
- iCloud requires 2FA setup and ADP must be disabled on account
- Display is 1600x1200 pixels with 6-color palette only
- Best for high-contrast, bold color images
