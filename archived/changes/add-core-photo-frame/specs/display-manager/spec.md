## ADDED Requirements

### Requirement: Display Manager Singleton
The system SHALL provide a singleton display manager for controlling the Inky Impression e-paper display.

#### Scenario: Display manager initialization
- **WHEN** the application starts
- **THEN** a single display manager instance is created
- **AND** the Inky display is initialized with 1600x1200 resolution

#### Scenario: Display image
- **WHEN** a processed image is provided to the display manager
- **THEN** the image is displayed on the e-paper display
- **AND** the display refresh cycle completes (27-35 seconds)

### Requirement: Hardware Retry Logic
The system SHALL implement retry logic for hardware operations to handle transient failures.

#### Scenario: Retry on transient failure
- **WHEN** a display operation fails due to a transient hardware error
- **THEN** the operation is retried up to 3 times with exponential backoff
- **AND** an error is logged if all retries are exhausted

#### Scenario: Successful retry
- **WHEN** a retried operation succeeds
- **THEN** the image is displayed normally
- **AND** the retry is logged for debugging

### Requirement: Full Refresh Support
The system SHALL support full refresh cycles to mitigate ghosting effects on the e-paper display.

#### Scenario: Full refresh for ghosting mitigation
- **WHEN** N photos have been displayed (configurable, default: 10)
- **THEN** a full refresh cycle is performed
- **AND** ghosting artifacts from previous images are cleared
