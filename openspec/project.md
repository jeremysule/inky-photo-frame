# Project Context

## Purpose
Personal photo frame project using an e-paper display for displaying family photos. This is a private project not intended for public sharing.

**Outcome**: A script that generates a minimal SD card image which can be written using Balena Etcher. Once flashed and booted on the Raspberry Pi, the system displays rotating family photos on a 13.3" E Ink display.

## Tech Stack
- **Python** - Primary language
- **inky** (Pimoroni Inky library >=1.5.0) - E-paper display control
- **Pillow** (>=10.0.0) - Image processing
- **pillow-heif** (>=0.13.0) - HEIC support for iPhone photos
- **watchdog** (>=3.0.0) - File watching for local photo detection
- **pyicloud** (>=1.0.0) - iCloud Photos API integration
- **numpy** (>=1.24.0) - Image processing operations
- **toml** (>=0.10.0) - Configuration file parsing

## Project Conventions

### Code Style
- **Simplicity first**: Keep few files that are easy to understand
- **Modular design**: Photo sources should be swappable (local folder, iCloud, future sources)
- **Single source of truth**: Configuration in `config.toml`
- Use well-known algorithms (Floyd-Steinberg dithering, LANCZOS resampling)
- Snake_case naming for Python files and variables

### Architecture Patterns
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
- Singleton pattern for display manager (hardware resource)
- Unified interface for photo sources (local, iCloud, future)
- Sequential image processing pipeline

### Testing Strategy
Not yet defined - project in early development stage.

### Git Workflow
- Main branch: `main`
- Use descriptive commit messages

## Domain Context

### Hardware Specifications
- **Display**: Inky Impression 13.3" (2025 edition) - 1600 x 1200 pixels
- **Colors**: 6-color E Ink Spectra 6 palette (black, white, red, green, blue, yellow)
- **Refresh time**: 27-35 seconds total cycle (not suitable for dynamic content)
- **Viewing angle**: ~170°
- **Contrast ratio**: ~30:1

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
- **pyicloud** - iCloud Photos API access
- **Apple iCloud** - Photo source (requires account with ADP disabled)
- **Local filesystem** - Primary photo source (watched folder)
