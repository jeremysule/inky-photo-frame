## Context

Building a photo frame system for the Inky Impression 13.3" e-paper display. Key constraints:
- E-paper refresh takes 27-35 seconds (not suitable for dynamic content)
- 6-color palette only (black, white, red, green, blue, yellow)
- iCloud requires ADP disabled and 2FA setup
- Raspberry Pi 4 with wall power (no extreme power optimization needed)

## Goals / Non-Goals

**Goals**:
- Display family photos from local folder and/or iCloud
- Automatic photo rotation on configurable interval
- Smart image processing for e-paper display
- Simple configuration via TOML

**Non-Goals**:
- Real-time photo updates (refresh too slow)
- Advanced image manipulation (keep it simple)
- Web UI or remote control (future enhancement)
- Power optimization (plugged into wall)

## Decisions

### Architecture: Singleton for Display Manager
- **Decision**: Use singleton pattern for display manager
- **Rationale**: Hardware resource - only one Inky display exists per system
- **Alternatives considered**: Class instantiation (unnecessary complexity)

### Configuration Format: TOML
- **Decision**: Use TOML for configuration
- **Rationale**: Readable, supports comments, Python has good toml library
- **Alternatives considered**: JSON (no comments), YAML (complex), INI (limited)

### iCloud Session Storage
- **Decision**: Store session in local file (`~/.pyicloud/` or config directory)
- **Rationale**: Avoids re-entering 2FA codes (~2 month expiry)
- **Alternatives considered**: No storage (annoying)

### Image Processing Pipeline Order
- **Decision**: Crop → Color Convert → Resize → Enhance → Dither
- **Rationale**: Crop first to avoid processing unnecessary pixels; enhance before dither for better color mapping
- **Alternatives considered**: Various orderings (tested for best results)

## Risks / Trade-offs

### Risk: iCloud Rate Limiting
- **Impact**: ~30 seconds per photo download (Apple throttling)
- **Mitigation**: Download to local cache, display from cache

### Risk: Temperature Sensitivity
- **Impact**: Slower refresh below 25°C
- **Mitigation**: Document constraint; indoor use typical temperature range acceptable

### Trade-off: Simplicity vs Features
- Keep initial implementation simple (no slideshow transitions, no metadata display)
- Add complexity only when explicitly requested

## Migration Plan

N/A - new system, no existing code to migrate.

## Open Questions

None - requirements are clear from project documentation.
