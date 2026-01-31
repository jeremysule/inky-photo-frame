"""Configuration management for Inky Photo Frame.

Loads configuration from TOML files with sensible defaults.
Generates a template config file on first run.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import toml


@dataclass
class DisplayConfig:
    """Display-related configuration."""

    refresh_interval: int = 3600
    full_refresh_every: int = 10
    saturation: float = 0.5  # Inky library saturation (0.0-1.0, palette quantization)


@dataclass
class ProcessingConfig:
    """Image processing configuration.

    Note: These are pre-processing multipliers applied BEFORE the image
    is sent to the Inky library. The Inky library then applies its own
    saturation parameter (display.saturation) for palette quantization.
    """

    saturation: float = 1.3  # Pre-processing saturation boost (1.0-2.0)
    contrast: float = 1.2  # Pre-processing contrast boost (1.0-2.0)
    portrait_bias: str = "top"  # "top" or "center"


@dataclass
class ICloudConfig:
    """iCloud Photos configuration."""

    enabled: bool = False
    apple_id: str | None = None
    session_path: str = "~/.config/inky-photo-frame/icloud_session"

    def expand_session_path(self) -> Path:
        """Return session path with ~ expanded."""
        return Path(self.session_path).expanduser()


@dataclass
class PhotoConfig:
    """Photo source configuration."""

    local_path: str = "~/Photos/Frame"
    selection_mode: str = "random"  # "random" or "sequential"

    def expand_local_path(self) -> Path:
        """Return local path with ~ expanded."""
        return Path(self.local_path).expanduser()


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: str = ""


@dataclass
class Config:
    """Main configuration container."""

    display: DisplayConfig = field(default_factory=DisplayConfig)
    photo: PhotoConfig = field(default_factory=PhotoConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    icloud: ICloudConfig = field(default_factory=ICloudConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    _config_path: Path = field(default=None, repr=False)

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "Config":
        """Load configuration from file or create with defaults.

        Args:
            config_path: Path to config file. If None, searches standard locations.

        Returns:
            Config instance with loaded or default values.
        """
        config_path = cls._find_config_path(config_path)

        if not config_path.exists():
            cls._generate_template(config_path)
            print(f"Generated default config at: {config_path}")
            print("Please edit the configuration and restart.")
            return cls(_config_path=config_path)

        try:
            data = toml.load(config_path)
            return cls._from_dict(data, config_path)
        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML in {config_path}: {e}") from e
        except Exception as e:
            raise ValueError(f"Error loading config from {config_path}: {e}") from e

    @staticmethod
    def _find_config_path(config_path: str | Path | None) -> Path:
        """Find the configuration file.

        Searches in order:
        1. Provided path
        2. ./config.toml
        3. ~/.config/inky-photo-frame/config.toml
        """
        if config_path is not None:
            return Path(config_path)

        # Check current directory
        local_config = Path.cwd() / "config.toml"
        if local_config.exists():
            return local_config

        # Check user config directory
        user_config = Path.home() / ".config" / "inky-photo-frame" / "config.toml"
        return user_config

    @classmethod
    def _generate_template(cls, path: Path) -> None:
        """Generate a default configuration file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        template_path = Path(__file__).parent.parent / "config.toml"
        if template_path.exists():
            # Copy the template from the project root
            import shutil
            shutil.copy(template_path, path)
        else:
            # Generate inline template
            default_content = """# Inky Photo Frame Configuration

[display]
# How often to refresh the display (seconds)
refresh_interval = 3600
# Perform a full refresh every N updates (removes ghosting)
full_refresh_every = 10
# Display saturation for palette quantization (0.0-1.0)
# Higher = more saturated colors, Lower = more muted/pastel
saturation = 0.5

[photo]
# Path to local photo folder (expanded ~ to home directory)
local_path = "~/Photos/Frame"
# Photo selection mode: "random" or "sequential"
selection_mode = "random"

[processing]
# Pre-processing saturation boost (1.0-2.0)
# Applied BEFORE display saturation, boosts source image colors
saturation = 1.3
# Pre-processing contrast boost (1.0-2.0)
contrast = 1.2
# Smart crop bias for portraits: "top" or "center"
portrait_bias = "top"

[icloud]
# Enable iCloud Photos as a photo source
enabled = false
# Apple ID for iCloud authentication
apple_id = ""
# Path to store iCloud session credentials
session_path = "~/.config/inky-photo-frame/icloud_session"

[logging]
# Logging level: "DEBUG", "INFO", "WARNING", "ERROR"
level = "INFO"
# Log file location (empty for stdout only)
file = ""
"""
            path.write_text(default_content)

    @classmethod
    def _from_dict(cls, data: dict[str, Any], config_path: Path) -> "Config":
        """Create Config from dictionary loaded from TOML."""
        config = cls(_config_path=config_path)

        # Display config
        if "display" in data:
            display = data["display"]
            config.display = DisplayConfig(
                refresh_interval=display.get("refresh_interval", 3600),
                full_refresh_every=display.get("full_refresh_every", 10),
                saturation=display.get("saturation", 0.5),
            )

        # Photo config
        if "photo" in data:
            photo = data["photo"]
            config.photo = PhotoConfig(
                local_path=photo.get("local_path", "~/Photos/Frame"),
                selection_mode=photo.get("selection_mode", "random"),
            )

        # Processing config
        if "processing" in data:
            processing = data["processing"]
            config.processing = ProcessingConfig(
                saturation=processing.get("saturation", 1.3),
                contrast=processing.get("contrast", 1.2),
                portrait_bias=processing.get("portrait_bias", "top"),
            )

        # iCloud config
        if "icloud" in data:
            icloud = data["icloud"]
            config.icloud = ICloudConfig(
                enabled=icloud.get("enabled", False),
                apple_id=icloud.get("apple_id") or None,
                session_path=icloud.get(
                    "session_path", "~/.config/inky-photo-frame/icloud_session"
                ),
            )

        # Logging config
        if "logging" in data:
            logging_data = data["logging"]
            config.logging = LoggingConfig(
                level=logging_data.get("level", "INFO"),
                file=logging_data.get("file", ""),
            )

        return config

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid).
        """
        errors = []

        # Validate display settings
        if self.display.refresh_interval <= 0:
            errors.append("display.refresh_interval must be positive")
        if self.display.full_refresh_every <= 0:
            errors.append("display.full_refresh_every must be positive")
        if not 0.0 <= self.display.saturation <= 1.0:
            errors.append("display.saturation must be between 0.0 and 1.0")

        # Validate processing settings
        if self.processing.saturation < 0:
            errors.append("processing.saturation must be non-negative")
        if self.processing.contrast < 0:
            errors.append("processing.contrast must be non-negative")
        if self.processing.portrait_bias not in ("top", "center"):
            errors.append("processing.portrait_bias must be 'top' or 'center'")

        # Validate photo settings
        if self.photo.selection_mode not in ("random", "sequential"):
            errors.append("photo.selection_mode must be 'random' or 'sequential'")

        # Validate iCloud settings
        if self.icloud.enabled:
            if not self.icloud.apple_id:
                errors.append("icloud.apple_id is required when icloud.enabled is true")

        # Validate logging settings
        valid_log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.logging.level.upper() not in valid_log_levels:
            errors.append(f"logging.level must be one of {valid_log_levels}")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0
