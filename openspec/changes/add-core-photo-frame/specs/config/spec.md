## ADDED Requirements

### Requirement: TOML Configuration
The system SHALL load configuration from a TOML file.

#### Scenario: Load default config
- **WHEN** no config file exists at startup
- **THEN** sensible defaults are used
- **AND** a template config file is created

#### Scenario: Load existing config
- **WHEN** a config file exists
- **THEN** settings are loaded from the file
- **AND** values override defaults

### Requirement: Display Configuration
The system SHALL support configurable display settings.

#### Scenario: Configure refresh interval
- **WHEN** refresh_interval is set in config
- **THEN** photos are updated at that interval (in seconds)
- **AND** default is 3600 (1 hour)

#### Scenario: Configure full refresh frequency
- **WHEN** full_refresh_every is set in config
- **THEN** a full refresh is performed after N photos
- **AND** default is 10

### Requirement: Source Configuration
The system SHALL support configuring multiple photo sources.

#### Scenario: Configure local folder
- **WHEN** local.path is set in config
- **THEN** that folder is watched for photos
- **AND** default is ~/Photos/Frame

#### Scenario: Enable iCloud source
- **WHEN** icloud.enabled is true
- **THEN** iCloud photos are included
- **AND** apple_id is required
- **AND** 2FA is handled interactively if needed

#### Scenario: Disable iCloud source
- **WHEN** icloud.enabled is false or omitted
- **THEN** iCloud is not used
- **AND** only local photos are displayed

### Requirement: Processing Configuration
The system SHALL support configurable image processing parameters.

#### Scenario: Configure saturation boost
- **WHEN** processing.saturation is set
- **THEN** that value is used for saturation boost
- **AND** default is 2.5

#### Scenario: Configure contrast boost
- **WHEN** processing.contrast is set
- **THEN** that value is used for contrast boost
- **AND** default is 1.5

#### Scenario: Configure selection mode
- **WHEN** processing.selection_mode is set
- **THEN** photos are selected using that strategy
- **AND** allowed values are "sequential" or "random"
- **AND** default is "random"
