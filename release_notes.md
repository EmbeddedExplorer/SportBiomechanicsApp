# BioMotion Studio Release Notes

## v0.92 Packaging Beta

This release prepares BioMotion Studio for Windows executable packaging.

### Included

- PyInstaller one-folder build configuration
- Windows build script
- Source-run helper script
- App icon support
- Packaged release folder structure
- Current analysis features:
  - Weightlifting analysis
  - Sprinting analysis
  - Results Dashboard
  - History
  - HTML/TXT reports
  - Embedded plot review in HTML report
  - Sprinting interlimb coordination analysis

### Build output

After running `build_app.bat`, the executable will be created at:

```text
dist/BioMotionStudio_Release/BioMotion Studio.exe
```

### Notes

- One-folder packaging is recommended for this app because PyQt6, MediaPipe, OpenCV, Matplotlib, and RealSense dependencies are large.
- RealSense live mode depends on the Windows RealSense runtime and connected hardware.
- Code signing is not included yet.
