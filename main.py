#!/usr/bin/env python3
"""Inky Photo Frame - Main entry point.

Orchestrates all components:
- Configuration loading
- Display management
- Photo sources
- Photo processing
- Main loop with signal handling
"""

import logging
import signal
import sys
import time
from pathlib import Path

try:
    import colorlog

    _COLORLOG_AVAILABLE = True
except ImportError:
    _COLORLOG_AVAILABLE = False

from src.config import Config
from src.display_manager import DisplayManager, is_available
from src.photo_processor import PhotoProcessor
from src.photo_sources import create_photo_sources

# Global flag for graceful shutdown
_shutdown_requested = False


def setup_logging(config: Config) -> None:
    """Setup logging configuration.

    Args:
        config: Configuration object.
    """
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)

    handlers: list[logging.Handler] = []

    # Console handler with colors if available
    if _COLORLOG_AVAILABLE:
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
        )
    else:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    handlers.append(console_handler)

    # File handler if configured
    if config.logging.file:
        log_path = Path(config.logging.file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,
    )

    # Suppress noisy loggers
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def signal_handler(signum, frame) -> None:
    """Handle shutdown signals gracefully.

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    global _shutdown_requested
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    _shutdown_requested = True


def display_next_photo(
    display: DisplayManager,
    processor: PhotoProcessor,
    photo_sources,
) -> bool:
    """Process and display the next photo.

    Args:
        display: Display manager instance.
        processor: Photo processor instance.
        photo_sources: Photo sources instance.

    Returns:
        True if successful, False otherwise.
    """
    logger = logging.getLogger(__name__)

    # Check if we have photos
    if not photo_sources.has_photos():
        logger.warning("No photos available. Waiting for photos...")
        return False

    # Select a photo
    photo_path = photo_sources.select_photo()
    if photo_path is None:
        logger.warning("Failed to select a photo")
        return False

    logger.info(f"Processing photo: {photo_path.name}")

    # Process the photo
    try:
        processed_image = processor.process_file(photo_path)
        if processed_image is None:
            logger.error(f"Failed to process photo: {photo_path}")
            return False

        # Determine if we need a full refresh
        force_full = display.update_count % display.resolution[1] == 0

        # Display the photo
        display.update(processed_image, force_full_refresh=force_full)
        logger.info("Photo displayed successfully")
        return True

    except Exception as e:
        logger.error(f"Error displaying photo: {e}", exc_info=True)
        return False


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    global _shutdown_requested

    # Load configuration
    print("Inky Photo Frame starting...")
    try:
        config = Config.load()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    logger.info("Inky Photo Frame starting...")
    logger.info(f"Configuration loaded from: {config._config_path}")

    # Check if Inky is available
    if not is_available():
        logger.error(
            "Inky library not available. This application must run on "
            "a Raspberry Pi with the Inky library installed."
        )
        logger.info("For testing without hardware, set DISPLAY_TEST_MODE=1")
        return 1

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize display manager
        logger.info("Initializing display manager...")
        display = DisplayManager.get_instance()
        display.set_saturation(config.display.saturation)
        logger.info(f"Display resolution: {display.resolution}")
        logger.info(f"Display saturation: {config.display.saturation}")

        # Initialize photo processor
        logger.info("Initializing photo processor...")
        processor = PhotoProcessor(
            target_width=display.width,
            target_height=display.height,
            saturation=config.processing.saturation,
            contrast=config.processing.contrast,
            portrait_bias=config.processing.portrait_bias,
        )

        # Initialize photo sources
        logger.info("Initializing photo sources...")
        photo_sources = create_photo_sources(config)

        # Track whether we've shown the "no photos" placeholder
        placeholder_shown = not photo_sources.has_photos()

        if not photo_sources.has_photos():
            logger.warning(
                "No photos found in any source. "
                "Add photos to your local folder or configure iCloud."
            )

        # Main loop
        logger.info("Starting main loop...")
        refresh_interval = config.display.refresh_interval

        while not _shutdown_requested:
            # Refresh photo sources periodically
            photo_sources.refresh()

            has_photos = photo_sources.has_photos()

            # Display a photo or placeholder
            if has_photos:
                display_next_photo(display, processor, photo_sources)
                # Reset placeholder flag since we now have photos
                placeholder_shown = False
            else:
                # Show placeholder only once (not on every loop iteration)
                if not placeholder_shown:
                    logger.info("Displaying 'no photos' placeholder...")
                    display.show_no_photos_message()
                    placeholder_shown = True
                logger.info("Waiting for photos to become available...")

            # Wait for next refresh or shutdown
            logger.info(f"Next refresh in {refresh_interval} seconds...")
            start_time = time.time()

            while time.time() - start_time < refresh_interval:
                if _shutdown_requested:
                    break
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        _shutdown_requested = True

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    finally:
        logger.info("Shutting down...")
        # Stop file watching if any
        if "photo_sources" in locals():
            for source in photo_sources.sources:
                if hasattr(source, "stop_watching"):
                    source.stop_watching()

    logger.info("Shutdown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
