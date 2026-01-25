## ADDED Requirements

### Requirement: Unified Photo Source Interface
The system SHALL provide a unified interface for all photo sources (local, iCloud, future sources).

#### Scenario: Get next photo from any source
- **WHEN** a photo is requested from any configured source
- **THEN** a photo path or object is returned
- **AND** the caller does not need to know which source provided the photo

### Requirement: Local Folder Source
The system SHALL support watching a local folder for photos.

#### Scenario: Initial photo scan
- **WHEN** the local folder source is initialized
- **THEN** all supported image files in the folder are indexed
- **AND** they are available for display

#### Scenario: New photo detection via watchdog
- **WHEN** a new image file is added to the watched folder
- **THEN** the file is detected within 1 second
- **AND** it is added to the photo index

#### Scenario: Unsupported files ignored
- **WHEN** non-image files are present in the folder
- **THEN** they are ignored
- **AND** only supported formats (PNG, JPEG, HEIC) are indexed

### Requirement: iCloud Photos Source
The system SHALL support fetching photos from iCloud Photos via pyicloud.

#### Scenario: iCloud authentication
- **WHEN** iCloud source is first configured
- **THEN** the user is prompted for Apple ID credentials
- **AND** a 2FA code is requested if enabled
- **AND** the session is saved locally for future use

#### Scenario: Session persistence
- **WHEN** a valid iCloud session exists
- **THEN** the user is NOT prompted for credentials
- **AND** photos can be fetched immediately

#### Scenario: Photo download from iCloud
- **WHEN** a photo from iCloud is selected
- **THEN** it is downloaded to a local cache
- **AND** ~30 seconds is allowed per photo (Apple rate limiting)
- **AND** the cached version is returned

#### Scenario: ADP enabled error
- **WHEN** Advanced Data Protection is enabled on the iCloud account
- **THEN** a clear error message is displayed
- **AND** instructions to disable ADP are provided

### Requirement: Photo Selection Strategy
The system SHALL support configurable photo selection strategies.

#### Scenario: Sequential selection
- **WHEN** sequential mode is configured
- **THEN** photos are displayed in order
- **AND** the selection wraps around to the beginning

#### Scenario: Random selection
- **WHEN** random mode is configured
- **THEN** a random photo is selected each time
- **AND** the same photo is not repeated consecutively
