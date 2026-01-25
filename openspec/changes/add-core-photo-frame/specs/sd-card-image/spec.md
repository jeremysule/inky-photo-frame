## ADDED Requirements

### Requirement: Image Build Script
The system SHALL provide a script that generates a minimal Raspberry Pi SD card image.

#### Scenario: Execute build script
- **WHEN** `./build-image.py` is executed
- **THEN** a flashable `.img` file is generated
- **AND** the image contains the photo frame application and all dependencies

#### Scenario: Build script usage
- **WHEN** `./build-image.py --help` is executed
- **THEN** usage instructions are displayed
- **AND** available options are documented

### Requirement: WiFi Preconfiguration
The system SHALL preconfigure WiFi credentials in the generated image.

#### Scenario: WiFi configuration via build script
- **WHEN** `./build-image.py --wifi-ssid "MyNetwork" --wifi-password "secret"` is executed
- **THEN** the generated image connects to the specified WiFi on first boot
- **AND** no manual WiFi configuration is required

#### Scenario: Default WiFi config file
- **WHEN** a `wifi.conf` file exists in the project
- **THEN** those credentials are used if no command-line args are provided
- **AND** credentials are not hardcoded in the image script

### Requirement: Auto-Login Configuration
The system SHALL configure the image to auto-login on boot for headless operation.

#### Scenario: Auto-login on boot
- **WHEN** the SD card is booted on the Raspberry Pi
- **THEN** the system auto-logins without user interaction
- **AND** the photo frame service starts automatically

### Requirement: Auto-Start Service
The system SHALL configure a systemd service to auto-start the photo frame application.

#### Scenario: Service enabled
- **WHEN** the image is built
- **THEN** a systemd service file is included
- **AND** the service is enabled to start on boot

#### Scenario: Service behavior
- **WHEN** the photo frame service starts
- **THEN** it runs as the `pi` user
- **AND** restarts automatically if it crashes
- **AND** logs output to journald

### Requirement: Dependency Installation
The system SHALL include all Python dependencies in the generated image.

#### Scenario: Python packages installed
- **WHEN** the image is built
- **THEN** all packages from requirements.txt are installed
- **AND** the Inky library is installed (rpi-specific dependencies included)

### Requirement: Application Inclusion
The system SHALL include the photo frame application in the generated image.

#### Scenario: Application files copied
- **WHEN** the image is built
- **THEN** all application files are copied to `/home/pi/inky-photo-frame/`
- **AND** permissions are set correctly for the `pi` user

### Requirement: User Configuration
The system SHALL configure the default user account in the generated image.

#### Scenario: Default user creation
- **WHEN** the image is built
- **THEN** a `pi` user is configured
- **AND** default password is set (documented for user to change)
- **AND** sudo access is enabled

### Requirement: SSH Enablement
The system SHALL enable SSH access in the generated image.

#### Scenario: SSH enabled on boot
- **WHEN** the SD card is booted
- **THEN** SSH is enabled
- **AND** the user can SSH in for debugging
