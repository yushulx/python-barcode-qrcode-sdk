# IP Camera Viewer

A desktop application for viewing IP camera streams with real-time barcode/QR code scanning, built with PySide6 and the Dynamsoft Capture Vision SDK.

## Requirements

- Python 3.9 – 3.12
- Windows x64 (the Dynamsoft native DLLs bundled in this project target `win_amd64`)

## Run from source

```bash
pip install -r requirements.txt
python main.py
```

## Build a standalone executable with PyInstaller

The provided `IPCameraViewer.spec` packages everything—including all Dynamsoft DLLs, model files, and template JSON files—into a **single self-contained `.exe`** that can be copied to any Windows PC without requiring Python or any additional packages.

### 1. Install dependencies (one-time)

```bash
pip install -r requirements.txt
```

### 2. Build the executable

Run this command from the `gui_client` directory:

```bash
pyinstaller IPCameraViewer.spec
```

The finished executable is written to:

```
dist/IPCameraViewer.exe
```

### 3. Distribute

Copy **both files** to the same folder on the target machine:

```
IPCameraViewer.exe
config.json
```

`config.json` is intentionally **not** embedded in the exe so the license key and other settings can be edited with any text editor without rebuilding.

> **Note:** On first launch the application unpacks its embedded files to a temporary folder (`%TEMP%\_MEIxxxxxx`). This is normal PyInstaller behaviour for one-file executables and takes a few seconds.

---

### What the spec does

| Problem | Fix applied in `IPCameraViewer.spec` |
|---|---|
| Dynamsoft DLLs (`Dynamsoft*x64.dll`) not found at runtime | `collect_all('dynamsoft_capture_vision_bundle')` adds all DLLs as `binaries` |
| Dynamsoft model/template/resource `.data` and `.json` files missing | Same `collect_all` call adds them as `datas` under `dynamsoft_capture_vision_bundle/` |
| Sub-modules imported by name at runtime not detected by PyInstaller | Full list added to `hiddenimports` |
| One-folder output inconvenient for distribution | Switched to **one-file** mode (`a.binaries` + `a.datas` embedded directly in `EXE`) |
| `config.json` (contains license key) inaccessible when embedded in exe | Excluded from `datas`; resolved at runtime from `sys.executable`'s directory so users can edit it freely |

### Regenerating the spec from scratch

If you need to rebuild the spec (e.g., after a major dependency change), use:

```bash
pyinstaller --onefile --noconsole --name IPCameraViewer \
    --collect-all dynamsoft_capture_vision_bundle \
    --hidden-import cv2 \
    --hidden-import numpy \
    --hidden-import requests \
    --add-data "config.json;." \
    main.py
```

> On Windows use `;` as the path separator in `--add-data`. On Linux/macOS use `:`.
