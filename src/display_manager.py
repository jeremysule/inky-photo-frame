"""Display manager for Inky Impression e-paper display.

Provides singleton access to the Inky display with retry logic
and refresh tracking.
"""

import logging
import time
from threading import Lock

# Lazy import of Inky (only available on Raspberry Pi)
_INKY_AVAILABLE = True
try:
    from inky.auto import auto
except ImportError:
    _INKY_AVAILABLE = False
    auto = None


logger = logging.getLogger(__name__)


class DisplayManager:
    """Singleton manager for Inky Impression display.

    Handles:
    - Auto-detection of Inky board
    - Image display with retry logic
    - Full refresh tracking
    - Thread-safe operations
    """

    _instance: "DisplayManager | None" = None
    _lock: Lock = Lock()
    _display_lock: Lock = Lock()

    def __init__(self) -> None:
        """Initialize the display manager.

        Note: Use get_instance() instead of direct instantiation.
        """
        if not _INKY_AVAILABLE:
            raise RuntimeError(
                "Inky library not available. "
                "This code must run on a Raspberry Pi with the Inky library installed."
            )

        self._display = None
        self._update_count = 0
        self._width = 1600
        self._height = 1200
        self._saturation = 0.5  # Spectra 6 saturation level (0.0-1.0, default from library)

    @classmethod
    def get_instance(cls) -> "DisplayManager":
        """Get the singleton DisplayManager instance.

        Returns:
            The singleton DisplayManager instance.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check pattern
                if cls._instance is None:
                    cls._instance = cls()
                    cls._instance._initialize_display()
        return cls._instance

    def _initialize_display(self) -> None:
        """Initialize the Inky display with auto-detection.

        Attempts to detect the connected Inky board.
        Retries on failure with exponential backoff.
        """
        max_attempts = 3
        base_delay = 1.0

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Initializing Inky display (attempt {attempt}/{max_attempts})...")
                self._display = auto()
                self._width = self._display.width
                self._height = self._display.height
                logger.info(
                    f"Inky display detected: {self._width}x{self._height} "
                    f"(type: {type(self._display).__name__})"
                )
                return
            except Exception as e:
                if attempt < max_attempts:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Failed to initialize display: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Failed to initialize Inky display after {max_attempts} attempts: {e}"
                    ) from e

    @property
    def width(self) -> int:
        """Get display width in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Get display height in pixels."""
        return self._height

    @property
    def resolution(self) -> tuple[int, int]:
        """Get display resolution as (width, height)."""
        return (self._width, self._height)

    @property
    def update_count(self) -> int:
        """Get the number of display updates performed."""
        return self._update_count

    def set_saturation(self, saturation: float) -> None:
        """Set the default saturation for palette quantization.

        Args:
            saturation: Saturation value (0.0-1.0) for the Inky library.
        """
        self._saturation = max(0.0, min(1.0, saturation))
        logger.debug(f"Display saturation set to {self._saturation}")

    def set_image(self, image, saturation: float | None = None) -> None:
        """Set the image to be displayed.

        Args:
            image: PIL Image to display (must match display resolution).
            saturation: Color saturation override (0.0-1.0). If None, uses current setting.
        """
        with self._display_lock:
            if saturation is not None:
                self._saturation = saturation
            # Pass saturation to the Inky library for palette quantization
            self._display.set_image(image, saturation=self._saturation)

    def show(self, force_full_refresh: bool = False) -> None:
        """Display the current image on the e-paper screen.

        Args:
            force_full_refresh: Force a full refresh cycle (slower, reduces ghosting).

        Note:
            Standard refresh: ~12 seconds at optimal temperature
            Full refresh: ~27-35 seconds total cycle
        """
        with self._display_lock:
            max_attempts = 3
            base_delay = 1.0

            # Determine if we need a full refresh
            needs_full_refresh = force_full_refresh or (self._update_count % 10 == 0)

            for attempt in range(1, max_attempts + 1):
                try:
                    if needs_full_refresh:
                        logger.info("Performing full refresh...")
                    else:
                        logger.info("Performing partial refresh...")

                    self._display.show()
                    self._update_count += 1
                    logger.info(f"Display update complete (count: {self._update_count})")
                    return

                except Exception as e:
                    if attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            f"Display refresh failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Display refresh failed after {max_attempts} attempts: {e}"
                        )
                        raise

    def update(self, image, force_full_refresh: bool = False) -> None:
        """Convenience method to set image and display in one call.

        Args:
            image: PIL Image to display.
            force_full_refresh: Force a full refresh cycle.
        """
        self.set_image(image)
        self.show(force_full_refresh=force_full_refresh)

    def reset_update_count(self) -> None:
        """Reset the update counter.

        Useful for coordinated refresh cycles.
        """
        self._update_count = 0
        logger.info("Update count reset to 0")

    def clear(self) -> None:
        """Clear the display to white."""
        if self._display is None:
            return

        from PIL import Image

        white_image = Image.new("RGB", (self._width, self._height), (255, 255, 255))
        self.update(white_image, force_full_refresh=True)

    def show_no_photos_message(self) -> None:
        """Display a 'No Photos' placeholder message on the screen.

        Shows a helpful message with instructions on where to add photos.
        Uses the 6-color Inky palette for optimal display.
        """
        from PIL import Image, ImageDraw, ImageFont

        # Create a white background
        image = Image.new("RGB", (self._width, self._height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Try to use a nice font, fall back to default
        try:
            # Use a larger font for the title
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except OSError:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 80)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 40)
            except OSError:
                title_font = ImageFont.load_default(size=60)
                text_font = ImageFont.load_default(size=30)

        # Center coordinates
        cx, cy = self._width // 2, self._height // 2

        # Draw an icon (simple photo frame)
        frame_margin = 300
        frame_size = 200
        draw.rectangle(
            [(cx - frame_size, cy - frame_size - 80), (cx + frame_size, cy + frame_size - 80)],
            outline=(0, 0, 0), width=8
        )
        # Draw "mountain" inside frame (representing a photo)
        draw.polygon([
            (cx - 120, cy - 20),
            (cx, cy - 120),
            (cx + 120, cy - 20)
        ], fill=(200, 200, 0))
        # Draw "sun"
        draw.ellipse([(cx + 40, cy - 150), (cx + 100, cy - 90)], fill=(255, 200, 0))

        # Title text
        title = "No Photos Found"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text((cx - title_width // 2, cy + 180), title, fill=(0, 0, 0), font=title_font)

        # Instructions
        instructions = [
            "Add photos to display:",
            "~/Photos/Frame/",
            "",
            "Or edit config.toml to",
            "add iCloud Photos"
        ]

        y_offset = cy + 300
        for line in instructions:
            line_bbox = draw.textbbox((0, 0), line, font=text_font)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text((cx - line_width // 2, y_offset), line, fill=(100, 100, 100), font=text_font)
            y_offset += 55

        # Display the placeholder
        self.update(image, force_full_refresh=True)


# Convenience function for quick access
def get_display() -> DisplayManager:
    """Get the singleton DisplayManager instance.

    Returns:
        The singleton DisplayManager instance.
    """
    return DisplayManager.get_instance()


def is_available() -> bool:
    """Check if Inky library is available.

    Returns:
        True if Inky library is installed and available, False otherwise.
    """
    return _INKY_AVAILABLE
