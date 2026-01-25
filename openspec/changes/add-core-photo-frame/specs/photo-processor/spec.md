## ADDED Requirements

### Requirement: Smart Cropping
The system SHALL crop images to 4:3 aspect ratio with bias toward the top for portraits.

#### Scenario: Landscape image cropping
- **WHEN** a landscape image is processed
- **THEN** it is cropped to 1600x1200 (4:3 aspect ratio)
- **AND** the center of the image is preserved

#### Scenario: Portrait image cropping
- **WHEN** a portrait image is processed
- **THEN** it is cropped to 1600x1200 (4:3 aspect ratio)
- **AND** the top portion of the image is preserved (face/subject bias)

### Requirement: Color Space Conversion
The system SHALL convert P3 color space images to sRGB for compatibility with the e-paper display.

#### Scenario: iPhone photo conversion
- **WHEN** an iPhone photo in P3 color space is processed
- **THEN** it is converted to sRGB color space
- **AND** color accuracy is preserved as much as possible

### Requirement: Image Enhancement
The system SHALL enhance images for optimal e-paper display by boosting saturation and contrast.

#### Scenario: Saturation boost
- **WHEN** any image is processed
- **THEN** saturation is increased by 2.0-3.0x (configurable)
- **AND** colors appear more vibrant on the limited e-paper palette

#### Scenario: Contrast increase
- **WHEN** any image is processed
- **THEN** contrast is increased by ~1.5x (configurable)
- **AND** images appear clearer on the low-contrast e-paper display

### Requirement: Resampling
The system SHALL resize images to native display resolution using LANCZOS resampling.

#### Scenario: Resize to native resolution
- **WHEN** an image is processed
- **THEN** it is resized to exactly 1600x1200 pixels
- **AND** LANCZOS resampling is used for quality

### Requirement: Color Palette Mapping
The system SHALL map all colors to the 6-color e-paper palette using Floyd-Steinberg dithering.

#### Scenario: 6-color palette mapping
- **WHEN** an image is displayed
- **THEN** all colors are mapped to the 6-color palette (black, white, red, green, blue, yellow)
- **AND** Floyd-Steinberg dithering is applied for smooth gradients

### Requirement: HEIC Support
The system SHALL support HEIC image format for iPhone photos.

#### Scenario: HEIC image processing
- **WHEN** a HEIC image is loaded
- **THEN** it is converted to a processable format
- **AND** processing continues normally
