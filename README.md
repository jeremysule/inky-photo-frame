# inky-photo-frame

## Purpose
Personal photo frame project using an e-paper display for displaying family photos. This is a private project not intended for public sharing.

**Artefact**: A script that generates a minimal SD card image which can be written using Balena Etcher. Once flashed and booted on the Raspberry Pi, the system displays rotating family photos on a 13.3" E Ink display.


### Hardware Specifications
- **Display**: https://thepihut.com/products/inky-impression-13-3-2025-edition  Pimoroini Inky Impression 13.3" (2025 edition) - 1600 x 1200 pixels
- **Colors**: 6-color E Ink Spectra 6 palette (black, white, red, green, blue, yellow)
- **Refresh time**: 27-35 seconds total cycle (not suitable for dynamic content)
- **Viewing angle**: ~170°
- **Contrast ratio**: ~30:1
- Raspberry Pi 4 model B

# Chosen Constaints and loose requirements
- Tech Stack: python
- Simplicity. Keep few files that are easy to understand
- Rely on known algorithms
- Sources of photos: modular, I can change implementations later. I want to start with a local folder of photos. The goal is to eventually support
- Single place to configure known config: like duration of rotation
- This will be plugged in the wall power outlet, we don't need extremely low power consumption
- preconfigure raspi user, wifi settings
- I want to be able to iterate qiuckly 


# Artefact:
This will create a script that once run will generate a minmal SDCard image that can be used with Balena Etcher to write to the SDCard.

# inspiration and reference
- https://github.com/mehdi7129/inky-photo-frame A similar project, aimed to run directly on the 4
- https://github.com/pimoroni/inky
- https://learn.pimoroni.com/article/getting-started-with-inky-impression
- https://alcom.be/uploads/E-Ink-Spectra%E2%84%A2-6.pdf


## Photo Sources (modular)
1. **Local folder** - Watch directory for new photos (using `watchdog`)
2. **iCloud Photos** - Direct API access via `pyicloud` library  


# Project Context



## Tech Stack
- Raspberry Pi OS lite, 64bit ARM, latest version
- **inky** (Pimoroni Inky library ) - E-paper display control
- Most recent versions

## Project Conventions

### Code Style
- **Simplicity first**: Keep few files that are easy to understand
- **Modular design**: Photo sources should be swappable (local folder, iCloud, future sources)
- **Single source of truth**: Configuration in `config.toml` , easily swappable
- Snake_case naming for Python files and variables
- Singleton pattern for display manager (hardware resource)
- Unified interface for photo sources (local, iCloud, future)
- Sequential image processing pipeline



### Image Processing Pipeline
1. Smart cropping to 4:3 aspect ratio (bias toward top for portraits)
2. P3 → sRGB conversion for iPhone photos
3. Resize to 1600x1200 using LANCZOS
4. Boost saturation (2.0-3.0x) for e-paper compensation
5. Increase contrast (~1.5x)
6. Map to 6-color palette with Floyd-Steinberg dithering

### Best Content Practices
- High contrast, bold colors, clear subject matter
- Avoid: subtle gradients, low contrast, muted tones
- Limited color palette images (artwork) display better than subtle gradients

## Important Constraints

### E-Paper Display Constraints
- **Refresh rate**: ~12 seconds advertised, 27-35 seconds real-world
- **Not suitable for**: animations, video, or rapid updates
- **Optimal temperature**: 25°C to 50°C (significantly slower below 25°C)
- **Color palette**: 6 colors only - all others approximated via dithering
- **No backlight** - requires well-lit environment
- **Ghosting**: faint traces may persist (mitigated by periodic full refreshes)

### iCloud Integration Constraints
- **Authentication**: Apple ID + password (app-specific passwords NOT supported)
- **2FA**: Interactive code entry on first run, session stored (~2 month expiry)
- **Critical**: Advanced Data Protection must be disabled on iCloud account
- **Rate limiting**: ~30 seconds per photo (Apple throttling)
- Downloads to local cache before display

### Development Constraints
- Quick iteration desired
- Will be plugged into wall power (no extreme power optimization needed)
- Raspberry Pi user and WiFi preconfigured

## External Dependencies
- **Pimoroni Inky library** - Display control
- **Apple iCloud** - Photo source (requires account with ADP disabled)
- **Local filesystem** - Primary photo source (watched folder)