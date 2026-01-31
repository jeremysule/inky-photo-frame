## ADDED Requirements

### Requirement: Dev Sync Script
The system SHALL provide a script to sync local development files to the Raspberry Pi via SSH.

#### Scenario: Sync all files
- **WHEN** `./sync-to-pi.sh` is executed
- **THEN** all project files are uploaded to the Pi
- **AND** the photo frame service is restarted
- **AND** success is confirmed

#### Scenario: Sync specific files
- **WHEN** `./sync-to-pi.sh src/` is executed with a path argument
- **THEN** only files in that path are uploaded
- **AND** other files remain unchanged

### Requirement: SSH Configuration
The system SHALL use standard SSH for file transfer with configurable host.

#### Scenario: Default host
- **WHEN** no host is specified
- **THEN** `pi@inky-frame.local` is used as the default target
- **AND** connection is attempted via mDNS/bonjour

#### Scenario: Custom host
- **WHEN** `--host pi@192.168.1.100` is provided
- **THEN** that host is used for the connection
- **AND** files are transferred to the specified host

#### Scenario: SSH key auth
- **WHEN** SSH keys are configured
- **THEN** no password prompt occurs
- **AND** sync completes non-interactively

### Requirement: Service Restart
The system SHALL restart the photo frame service after syncing to apply changes.

#### Scenario: Auto-restart on sync
- **WHEN** files are synced successfully
- **THEN** `systemctl restart photo-frame` is executed on the Pi
- **AND** the new code takes effect immediately

#### Scenario: Skip restart
- **WHEN** `--no-restart` flag is provided
- **THEN** files are synced but service is NOT restarted
- **AND** user must manually restart to apply changes

### Requirement: File Transfer Method
The system SHALL use rsync over SSH for efficient file transfer.

#### Scenario: Incremental sync
- **WHEN** sync is executed multiple times
- **THEN** only changed files are transferred
- **AND** transfer completes quickly

#### Scenario: Exclude patterns
- **WHEN** sync is executed
- **THEN** `.git/`, `__pycache__/`, `*.pyc`, `.pytest_cache/` are excluded
- **AND** unnecessary files are not transferred

### Requirement: Configuration Sync
The system SHALL support syncing configuration files with optional backup.

#### Scenario: Config file sync
- **WHEN** config files are included in sync
- **THEN** the existing config on the Pi is backed up
- **AND** the new config is applied

#### Scenario: Dry run
- **WHEN** `--dry-run` flag is provided
- **THEN** files that would be transferred are listed
- **AND** no actual transfer occurs

### Requirement: Development Mode Toggle
The system SHALL support a development mode that enables additional debugging.

#### Scenario: Enable dev mode
- **WHEN** `--dev` flag is provided
- **THEN** verbose logging is enabled on the Pi
- **AND** the service runs in foreground with console output

#### Scenario: Production mode
- **WHEN** no `--dev` flag is provided
- **THEN** the service runs normally as a daemon
- **AND** logs go to journald only
