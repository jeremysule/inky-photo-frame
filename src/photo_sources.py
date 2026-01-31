"""Photo source abstractions for Inky Photo Frame.

Provides:
- Abstract PhotoSource base class
- LocalPhotoSource with file watching
- ICloudPhotoSource with 2FA flow
- Unified photo selection (sequential/random)
"""

import logging
import random
import shutil
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class SelectionMode(Enum):
    """Photo selection mode."""

    RANDOM = "random"
    SEQUENTIAL = "sequential"


class PhotoSource(ABC):
    """Abstract base class for photo sources."""

    def __init__(self, name: str) -> None:
        """Initialize the photo source.

        Args:
            name: Human-readable name for this source.
        """
        self.name = name
        self._index = 0
        self._photos: list[Path] = []
        self._selection_mode = SelectionMode.RANDOM

    @abstractmethod
    def refresh(self) -> None:
        """Refresh the list of available photos."""

    @abstractmethod
    def get_photo_path(self, index: int) -> Path | None:
        """Get the path to a photo by index.

        Args:
            index: Index of the photo.

        Returns:
            Path to the photo, or None if index is invalid.
        """

    @abstractmethod
    def load_photo(self, index: int) -> bytes | None:
        """Load photo data by index.

        Args:
            index: Index of the photo.

        Returns:
            Photo data as bytes, or None if loading failed.
        """

    def set_selection_mode(self, mode: SelectionMode | str) -> None:
        """Set the photo selection mode.

        Args:
            mode: Selection mode (RANDOM or SEQUENTIAL).
        """
        if isinstance(mode, str):
            mode = SelectionMode(mode.lower())
        self._selection_mode = mode
        logger.info(f"Photo source '{self.name}' selection mode set to {mode.value}")

    def get_photo_count(self) -> int:
        """Get the number of available photos.

        Returns:
            Number of photos.
        """
        return len(self._photos)

    def has_photos(self) -> bool:
        """Check if any photos are available.

        Returns:
            True if photos are available.
        """
        return len(self._photos) > 0

    def select_photo_index(self) -> int | None:
        """Select a photo index based on current selection mode.

        Returns:
            Selected index, or None if no photos available.
        """
        if not self.has_photos():
            return None

        if self._selection_mode == SelectionMode.RANDOM:
            return random.randint(0, len(self._photos) - 1)
        else:
            # Sequential mode
            index = self._index % len(self._photos)
            self._index += 1
            return index

    def select_photo(self) -> Path | None:
        """Select a photo path based on current selection mode.

        Returns:
            Path to selected photo, or None if no photos available.
        """
        index = self.select_photo_index()
        if index is None:
            return None
        return self.get_photo_path(index)


class LocalPhotoSource(PhotoSource):
    """Local file system photo source.

    Monitors a directory for photo files and provides access.
    """

    SUPPORTED_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".heic", ".heif", ".webp"
    }

    class _PhotoFileHandler(FileSystemEventHandler):
        """Handler for file system events."""

        def __init__(self, callback) -> None:
            self.callback = callback

        def on_created(self, event: FileSystemEvent) -> None:
            if not event.is_directory:
                self.callback()

        def on_deleted(self, event: FileSystemEvent) -> None:
            if not event.is_directory:
                self.callback()

        def on_moved(self, event: FileSystemEvent) -> None:
            if not event.is_directory:
                self.callback()

    def __init__(
        self,
        path: str | Path,
        watch: bool = True,
        recursive: bool = True
    ) -> None:
        """Initialize the local photo source.

        Args:
            path: Path to directory containing photos.
            watch: Enable file watching for auto-refresh.
            recursive: Watch subdirectories recursively.
        """
        super().__init__(name="Local")
        self.path = Path(path).expanduser()
        self.watch = watch
        self.recursive = recursive
        self._observer: Observer | None = None

        # Create directory if it doesn't exist
        self.path.mkdir(parents=True, exist_ok=True)

        # Initial scan
        self.refresh()

        # Start watching if enabled
        if self.watch:
            self._start_watching()

    def _start_watching(self) -> None:
        """Start watching the photo directory for changes."""
        if self._observer is not None:
            return

        handler = self._PhotoFileHandler(callback=self.refresh)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.path), recursive=self.recursive)

        try:
            self._observer.start()
            logger.info(f"Started watching directory: {self.path}")
        except Exception as e:
            logger.warning(f"Failed to start file watcher: {e}")
            self._observer = None

    def stop_watching(self) -> None:
        """Stop watching the photo directory."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped file watcher")

    def refresh(self) -> None:
        """Refresh the list of available photos."""
        photos: list[Path] = []

        try:
            if self.recursive:
                files = self.path.rglob("*")
            else:
                files = self.path.iterdir()

            for file in files:
                if file.is_file() and file.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    photos.append(file)

            self._photos = sorted(photos)
            logger.info(f"Local photo source: {len(self._photos)} photos found")

        except Exception as e:
            logger.error(f"Error scanning photo directory: {e}")

    def get_photo_path(self, index: int) -> Path | None:
        """Get the path to a photo by index.

        Args:
            index: Index of the photo.

        Returns:
            Path to the photo, or None if index is invalid.
        """
        try:
            return self._photos[index]
        except IndexError:
            return None

    def load_photo(self, index: int) -> bytes | None:
        """Load photo data by index.

        Args:
            index: Index of the photo.

        Returns:
            Photo data as bytes, or None if loading failed.
        """
        path = self.get_photo_path(index)
        if path is None:
            return None

        try:
            return path.read_bytes()
        except Exception as e:
            logger.error(f"Failed to load photo {path}: {e}")
            return None

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.stop_watching()


class ICloudPhotoSource(PhotoSource):
    """iCloud Photos source using pyicloud.

    Provides access to iCloud Photos library.
    Requires 2FA authentication on first use.
    """

    def __init__(
        self,
        apple_id: str,
        password: str | None = None,
        cache_path: str | Path = "~/.cache/inky-photo-frame/icloud",
    ) -> None:
        """Initialize the iCloud photo source.

        Args:
            apple_id: Apple ID for iCloud authentication.
            password: iCloud password (or prompt if None).
            cache_path: Path to cache downloaded photos.
        """
        super().__init__(name="iCloud")
        self.apple_id = apple_id
        self._password = password
        self.cache_path = Path(cache_path).expanduser()
        self.cache_path.mkdir(parents=True, exist_ok=True)

        self._api: Any = None
        self._authenticated = False

        # Try to load session
        self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with iCloud Photos.

        Returns:
            True if authentication successful.
        """
        try:
            from pyicloud import PyiCloudService

            password = self._password
            if password is None:
                # Prompt for password
                import getpass
                password = getpass.getpass(f"iCloud password for {self.apple_id}: ")

            logger.info(f"Authenticating with iCloud as {self.apple_id}...")

            self._api = PyiCloudService(self.apple_id, password)

            # Check if 2FA is required
            if self._api.requires_2fa:
                logger.info("2FA required. Please enter the code sent to your devices.")
                code = input("Enter 2FA code: ")
                if not self._api.validate_2fa_code(code):
                    logger.error("Invalid 2FA code")
                    return False

            self._authenticated = True
            logger.info("iCloud authentication successful")
            return True

        except ImportError:
            logger.error("pyicloud not installed. Install with: pip install pyicloud")
            return False
        except Exception as e:
            logger.error(f"iCloud authentication failed: {e}")

            if "Advanced Data Protection" in str(e) or "2FA" in str(e):
                logger.error(
                    "Note: iCloud integration requires Advanced Data Protection to be disabled. "
                    "Also, app-specific passwords are NOT supported - use your main Apple ID password."
                )

            return False

    def refresh(self) -> None:
        """Refresh the list of available photos from iCloud."""
        if not self._authenticated:
            if not self._authenticate():
                return

        try:
            photos = self._api.photos.all
            self._photos = [p for p in photos]
            logger.info(f"iCloud photo source: {len(self._photos)} photos found")
        except Exception as e:
            logger.error(f"Error fetching iCloud photos: {e}")

    def get_photo_path(self, index: int) -> Path | None:
        """Get the local cached path to a photo by index.

        Args:
            index: Index of the photo.

        Returns:
            Path to the cached photo, or None if index is invalid.
        """
        if index < 0 or index >= len(self._photos):
            return None

        # Get photo metadata
        photo_obj = self._photos[index]
        filename = f"{photo_obj.id}.jpg"
        cache_file = self.cache_path / filename

        # Download if not cached
        if not cache_file.exists():
            self._download_photo(index, cache_file)

        return cache_file if cache_file.exists() else None

    def _download_photo(self, index: int, dest: Path) -> bool:
        """Download a photo from iCloud.

        Args:
            index: Index of the photo.
            dest: Destination path.

        Returns:
            True if download successful.
        """
        if not self._authenticated:
            return False

        try:
            photo_obj = self._photos[index]

            # Create download with quality
            download = photo_obj.download(version="original")
            if not download:
                logger.warning(f"Could not download photo at index {index}")
                return False

            # Stream the download to file
            with dest.open("wb") as f:
                for chunk in download.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Downloaded photo to: {dest}")
            return True

        except Exception as e:
            logger.error(f"Error downloading photo: {e}")
            return False

    def load_photo(self, index: int) -> bytes | None:
        """Load photo data by index.

        Args:
            index: Index of the photo.

        Returns:
            Photo data as bytes, or None if loading failed.
        """
        path = self.get_photo_path(index)
        if path is None:
            return None

        try:
            return path.read_bytes()
        except Exception as e:
            logger.error(f"Failed to load cached photo {path}: {e}")
            return None

    def clear_cache(self) -> int:
        """Clear the photo cache.

        Returns:
            Number of files deleted.
        """
        count = 0
        try:
            for file in self.cache_path.iterdir():
                if file.is_file():
                    file.unlink()
                    count += 1
            logger.info(f"Cleared {count} cached photos")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
        return count


class CompositePhotoSource(PhotoSource):
    """Composite photo source combining multiple sources.

    Provides unified access to photos from multiple sources.
    """

    def __init__(self, sources: list[PhotoSource]) -> None:
        """Initialize the composite source.

        Args:
            sources: List of photo sources to combine.
        """
        super().__init__(name="Composite")
        self.sources = sources
        self._source_offsets: list[PhotoSource, int] = []
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild the index mapping."""
        self._source_offsets = []
        total_offset = 0

        for source in self.sources:
            self._source_offsets.append((source, total_offset))
            total_offset += source.get_photo_count()

        logger.info(f"Composite source: {total_offset} total photos")

    def refresh(self) -> None:
        """Refresh all sources and rebuild index."""
        for source in self.sources:
            source.refresh()
        self._rebuild_index()

    def _find_source_for_index(self, index: int) -> tuple[PhotoSource, int] | None:
        """Find the source and local index for a global index.

        Args:
            index: Global index.

        Returns:
            Tuple of (source, local_index), or None if not found.
        """
        for source, offset in self._source_offsets:
            source_count = source.get_photo_count()
            if offset <= index < offset + source_count:
                return source, index - offset

        return None

    def get_photo_path(self, index: int) -> Path | None:
        """Get the path to a photo by index.

        Args:
            index: Index of the photo.

        Returns:
            Path to the photo, or None if index is invalid.
        """
        result = self._find_source_for_index(index)
        if result is None:
            return None
        source, local_index = result
        return source.get_photo_path(local_index)

    def load_photo(self, index: int) -> bytes | None:
        """Load photo data by index.

        Args:
            index: Index of the photo.

        Returns:
            Photo data as bytes, or None if loading failed.
        """
        result = self._find_source_for_index(index)
        if result is None:
            return None
        source, local_index = result
        return source.load_photo(local_index)

    def set_selection_mode(self, mode: SelectionMode | str) -> None:
        """Set the photo selection mode for all sources.

        Args:
            mode: Selection mode (RANDOM or SEQUENTIAL).
        """
        super().set_selection_mode(mode)
        for source in self.sources:
            source.set_selection_mode(mode)

    def get_photo_count(self) -> int:
        """Get the total number of photos across all sources.

        Returns:
            Total number of photos.
        """
        return sum(source.get_photo_count() for source in self.sources)


def create_photo_sources(config) -> CompositePhotoSource:
    """Create photo sources from configuration.

    Args:
        config: Configuration object.

    Returns:
        CompositePhotoSource with configured sources.
    """
    sources: list[PhotoSource] = []

    # Add local source
    local_path = config.photo.expand_local_path()
    local_source = LocalPhotoSource(local_path)
    sources.append(local_source)

    # Add iCloud source if enabled
    if config.icloud.enabled and config.icloud.apple_id:
        icloud_source = ICloudPhotoSource(
            apple_id=config.icloud.apple_id,
            cache_path=config.icloud.expand_session_path() / "cache",
        )
        sources.append(icloud_source)

    # Set selection mode
    composite = CompositePhotoSource(sources)
    composite.set_selection_mode(config.photo.selection_mode)

    return composite
