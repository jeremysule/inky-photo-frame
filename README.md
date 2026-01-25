# inky-photo-frame

Personal project to create a personal photo frame based on ePAper display. It is not meant to be shared publicly. The goal is to display family photos.

# Material 
 - screen https://thepihut.com/products/inky-impression-13-3-2025-edition 
 - Raspberry Pi 4 model B
 - SD Card

# Chosen Constaints and loose requirements
- Tech Stack: python
- Simplicity. Keep few files that are easy to understand
- Rely on known algorithms
- Sources of photos: modular, I can change implementations later. I want to start with a local folder of photos. The goal is to eventually support
- Single place to configure known config: like duration of rotation
- This will be plugged in the wall power outlet, we don't need extremely low power consumption
- preconfigure raspi user, wifi settings
- I want to be able to iterate qiuckly 


# Artefact:
This will create a script that once run will generate a minmal SDCard image that can be used with Balena Etcher to write to the SDCard.

# inspiration and reference
- https://github.com/mehdi7129/inky-photo-frame A similar project, aimed to run directly on the 4
- https://github.com/pimoroni/inky
- https://learn.pimoroni.com/article/getting-started-with-inky-impression
- https://alcom.be/uploads/E-Ink-Spectra%E2%84%A2-6.pdf


#ideas
## Core nctionality
Photo display on 1600x1200 e-paper (6-color palette with Floyd-Steinberg dithering)
Smart cropping (maintain aspect ratio, bias toward top for portraits)
HEIC support for iPhone File watching for real-time new photo detection

## Photo Sources (modular)
1. **Local folder** - Watch directory for new photos (using `watchdog`)
2. **iCloud Photos** - Direct API access via `pyicloud` library  