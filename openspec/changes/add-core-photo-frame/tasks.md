## 1. Project Foundation
- [ ] 1.1 Create project directory structure (`src/` directory)
- [ ] 1.2 Create `requirements.txt` with all dependencies
- [ ] 1.3 Create `config.toml` with sensible defaults

## 2. Configuration System
- [ ] 2.1 Implement `src/config.py` with TOML parsing
- [ ] 2.2 Define configuration schema (display, sources, processing)
- [ ] 2.3 Add validation for required configuration values

## 3. Display Manager
- [ ] 3.1 Implement `src/display_manager.py` singleton class
- [ ] 3.2 Add Inky display initialization
- [ ] 3.3 Implement retry logic for hardware operations
- [ ] 3.4 Add full refresh support (for ghosting mitigation)

## 4. Photo Processor
- [ ] 4.1 Implement `src/photo_processor.py` smart crop to 4:3 (portrait bias)
- [ ] 4.2 Add P3 to sRGB color conversion for iPhone photos
- [ ] 4.3 Implement saturation boost (2.0-3.0x) for e-paper
- [ ] 4.4 Add contrast increase (~1.5x)
- [ ] 4.5 Implement resize to 1600x1200 using LANCZOS
- [ ] 4.6 Add 6-color palette mapping with Floyd-Steinberg dithering
- [ ] 4.7 Add HEIC support via pillow-heif

## 5. Photo Sources
- [ ] 5.1 Implement `src/photo_sources.py` unified interface
- [ ] 5.2 Add local folder source with watchdog file watching
- [ ] 5.3 Implement iCloud source using pyicloud
- [ ] 5.4 Add 2FA flow for iCloud authentication
- [ ] 5.5 Implement session storage for iCloud (~2 month expiry)
- [ ] 5.6 Add local caching for downloaded iCloud photos

## 6. Main Entry Point
- [ ] 6.1 Create `main.py` entry point
- [ ] 6.2 Implement photo selection logic (round-robin or random)
- [ ] 6.3 Add update interval/scheduling
- [ ] 6.4 Integrate all components (config, sources, processor, display)
- [ ] 6.5 Add graceful shutdown handling
- [ ] 6.6 Add logging for debugging

## 7. Testing & Validation
- [ ] 7.1 Test display refresh with sample images
- [ ] 7.2 Validate image processing pipeline output
- [ ] 7.3 Test local folder photo source
- [ ] 7.4 Test iCloud integration (if account available)
- [ ] 7.5 Verify watchdog file watching works correctly

## 8. SD Card Image Generation
- [ ] 8.1 Create `build-image.py` script with CLI argument parsing
- [ ] 8.2 Implement WiFi preconfiguration (wpa_supplicant or NetworkManager)
- [ ] 8.3 Add auto-login configuration (getty override)
- [ ] 8.4 Create systemd service file for photo frame auto-start
- [ ] 8.5 Implement dependency installation (pip install in Docker/chroot)
- [ ] 8.6 Add application file copying to image
- [ ] 8.7 Configure user account (pi user with sudo)
- [ ] 8.8 Enable SSH in generated image
- [ ] 8.9 Add documentation for build process and usage

## 9. Dev Sync Tool
- [ ] 9.1 Create `sync-to-pi.sh` script with rsync over SSH
- [ ] 9.2 Add CLI argument parsing (host, dry-run, no-restart, dev mode)
- [ ] 9.3 Implement rsync exclude patterns (.git, __pycache__, *.pyc)
- [ ] 9.4 Add auto service restart after successful sync
- [ ] 9.5 Implement config backup before syncing config files
- [ ] 9.6 Add dev mode flag for verbose logging/foreground output
- [ ] 9.7 Add documentation for sync workflow
