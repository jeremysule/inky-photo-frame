"""Photo processing pipeline for Inky Photo Frame.

Handles:
- Image loading with HEIC/HEIF support
- Smart cropping to 4:3 aspect ratio
- P3 to sRGB color space conversion
- Saturation and contrast enhancement

Note: Palette quantization and Floyd-Steinberg dithering are handled
by the Inky library's set_image() method with the saturation parameter.
The library blends between DESATURATED_PALETTE and SATURATED_PALETTE
based on the saturation value (0.0-1.0).
"""

import io
import logging
from pathlib import Path

from PIL import Image, ImageEnhance

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    _HEIF_AVAILABLE = True
except ImportError:
    _HEIF_AVAILABLE = False

logger = logging.getLogger(__name__)


def smart_crop(
    image: Image.Image,
    target_ratio: float = 4 / 3,
    portrait_bias: str = "top"
) -> Image.Image:
    """Smart crop to target aspect ratio with portrait awareness.

    Args:
        image: Source PIL Image.
        target_ratio: Target aspect ratio (width/height). Default 4:3.
        portrait_bias: For portrait images, bias crop to "top" or "center".

    Returns:
        Cropped image with target aspect ratio.
    """
    img_width, img_height = image.size
    img_ratio = img_width / img_height

    # If already close to target ratio, return as-is
    if abs(img_ratio - target_ratio) < 0.01:
        return image

    if img_ratio > target_ratio:
        # Image is wider than target - crop sides
        new_width = int(img_height * target_ratio)
        left = (img_width - new_width) // 2
        right = left + new_width
        return image.crop((left, 0, right, img_height))
    else:
        # Image is taller than target - crop top/bottom
        new_height = int(img_width / target_ratio)

        if portrait_bias == "top" and img_ratio < 0.8:
            # Portrait orientation - bias toward top (faces usually there)
            top = 0
            bottom = new_height
        else:
            # Landscape or square - center crop
            top = (img_height - new_height) // 2
            bottom = top + new_height

        return image.crop((0, top, img_width, bottom))


def convert_p3_to_srgb(image: Image.Image) -> Image.Image:
    """Convert Display P3 color space to sRGB.

    iPhone photos are often in Display P3, which needs conversion
    for proper display on sRGB devices like e-paper.

    Args:
        image: PIL Image (may be in P3 or already sRGB).

    Returns:
        Image in sRGB color space.
    """
    # If image has an ICC profile, convert it
    if image.info.get("icc_profile"):
        try:
            # Attempt to convert using ICC profile
            from PIL import ImageCms

            # Create sRGB profile
            srgb_profile = ImageCms.createProfile("sRGB")

            # Convert from embedded profile to sRGB
            input_profile = ImageCms.ImageCmsProfile(io.BytesIO(image.info["icc_profile"]))
            transform = ImageCms.buildTransform(
                inputProfile=input_profile,
                outputProfile=srgb_profile,
                inMode="RGB",
                outMode="RGB",
            )
            image = ImageCms.applyTransform(image, transform)
            logger.debug("Converted from ICC profile to sRGB")
        except Exception as e:
            logger.debug(f"Could not convert ICC profile: {e}, using as-is")

    return image.convert("RGB")


def enhance_for_epaper(
    image: Image.Image,
    saturation: float = 1.3,
    contrast: float = 1.2
) -> Image.Image:
    """Enhance image for e-paper display characteristics.

    E-paper displays have lower contrast and saturation than LCD/OLED,
    so we boost these values for better appearance.

    Note: The Inky library's saturation parameter (0.0-1.0) handles
    the final palette quantization. This pre-processing enhances
    the source image before that step.

    Args:
        image: PIL Image in RGB mode.
        saturation: Saturation multiplier (typical range 1.1-1.5).
        contrast: Contrast multiplier (typical range 1.1-1.4).

    Returns:
        Enhanced image.
    """
    # Apply saturation boost
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(saturation)

    # Apply contrast boost
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast)

    # Slight sharpness boost to compensate for upsizing
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.2)

    return image


class PhotoProcessor:
    """Complete photo processing pipeline for Inky Photo Frame.

    Note: This class prepares RGB images for display. The actual
    palette quantization and Floyd-Steinberg dithering are handled
    by the Inky library's set_image() method.
    """

    def __init__(
        self,
        target_width: int = 1600,
        target_height: int = 1200,
        saturation: float = 1.3,
        contrast: float = 1.2,
        portrait_bias: str = "top",
    ):
        """Initialize the photo processor.

        Args:
            target_width: Target display width in pixels.
            target_height: Target display height in pixels.
            saturation: Pre-processing saturation boost (1.0-2.0).
                        Note: This is NOT the Inky library's saturation parameter.
            contrast: Pre-processing contrast boost (1.0-2.0).
            portrait_bias: Portrait crop bias ("top" or "center").
        """
        self.target_width = target_width
        self.target_height = target_height
        self.saturation = saturation
        self.contrast = contrast
        self.portrait_bias = portrait_bias

        if not _HEIF_AVAILABLE:
            logger.warning(
                "pillow-heif not available - HEIC/HEIF files will not be supported. "
                "Install with: pip install pillow-heif"
            )

    def load_image(self, path: str | Path) -> Image.Image | None:
        """Load an image file, supporting JPEG, PNG, HEIC, and HEIF.

        Args:
            path: Path to image file.

        Returns:
            PIL Image, or None if loading failed.
        """
        path = Path(path)

        if not path.exists():
            logger.error(f"Image file not found: {path}")
            return None

        try:
            # PIL with pillow-heif registered handles HEIC automatically
            image = Image.open(path)

            # Convert to RGB if necessary
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")

            # Handle RGBA by compositing over white
            if image.mode == "RGBA":
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
                image = background

            logger.debug(f"Loaded image: {path.name} ({image.size[0]}x{image.size[1]})")
            return image

        except Exception as e:
            logger.error(f"Failed to load image {path}: {e}")
            return None

    def process(self, image: Image.Image) -> Image.Image:
        """Process an image through the complete pipeline.

        Pipeline steps:
        1. Smart crop to 4:3 aspect ratio
        2. P3 to sRGB color conversion
        3. Resize to target resolution
        4. Enhance saturation and contrast

        Note: Palette quantization and dithering are handled by
        DisplayManager.set_image() which calls the Inky library.

        Args:
            image: Source PIL Image.

        Returns:
            Processed RGB image ready for display.
        """
        # Step 1: Smart crop
        logger.debug("Applying smart crop...")
        image = smart_crop(image, target_ratio=4 / 3, portrait_bias=self.portrait_bias)

        # Step 2: Convert P3 to sRGB
        logger.debug("Converting color space...")
        image = convert_p3_to_srgb(image)

        # Step 3: Resize using LANCZOS (high-quality resampling)
        logger.debug(f"Resizing to {self.target_width}x{self.target_height}...")
        image = image.resize(
            (self.target_width, self.target_height),
            Image.Resampling.LANCZOS,
        )

        # Step 4: Enhance for e-paper
        logger.debug(
            f"Enhancing image (pre-processing saturation: {self.saturation}x, contrast: {self.contrast}x)..."
        )
        image = enhance_for_epaper(image, self.saturation, self.contrast)

        logger.debug("Image processing complete. Ready for display.")
        return image

    def process_file(self, path: str | Path) -> Image.Image | None:
        """Load and process an image file.

        Convenience method combining load_image() and process().

        Args:
            path: Path to image file.

        Returns:
            Processed image ready for display, or None if loading failed.
        """
        image = self.load_image(path)
        if image is None:
            return None
        return self.process(image)

    def process_and_save(
        self,
        input_path: str | Path,
        output_path: str | Path
    ) -> bool:
        """Load, process, and save an image.

        Useful for testing and batch processing.

        Args:
            input_path: Path to source image.
            output_path: Path to save processed image.

        Returns:
            True if successful, False otherwise.
        """
        image = self.process_file(input_path)
        if image is None:
            return False

        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG")
            logger.info(f"Saved processed image to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return False
