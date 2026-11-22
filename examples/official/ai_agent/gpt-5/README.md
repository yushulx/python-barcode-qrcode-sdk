# Dynamsoft Barcode Reader CLI (Python)

A simple command-line barcode scanner built on the Dynamsoft Barcode Reader (DBR) Python SDK.

## Features
- Scan single images or directories of images
- Recursive directory scanning with `-r`
- Text or JSON output formats (`-f text|json`)
- Exit code differentiation (`--fail-on-empty` returns 2 when nothing found)

Camera/live capture is not enabled in this minimal version due to SDK signature variability for `decode_buffer`. You can extend it manually once your environment confirms the buffer API signature.

## Requirements
- Python 3.8+
- Dynamsoft Barcode Reader Python package (`dbr`)
- A valid DBR license key (trial or paid)

## Installation
```powershell
python -m venv .venv; .\.venv\Scripts\activate
pip install -r requirements.txt
# Set your license (replace with your key)
$env:DBR_LICENSE = "YOUR-LICENSE-KEY"
```
Obtain a [trial key](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform)

## Usage
```powershell
# Basic scan of a single file
python scan.py image.png

# Recursive scan of a directory, JSON output
python scan.py images_dir -r -f json

# Provide license via argument instead of env var
python scan.py image.png --license YOUR-LICENSE-KEY

# Fail the build/script if no barcodes found
python scan.py image.png --fail-on-empty
```
Exit codes:
- 0: Success (may or may not have found barcodes)
- 1: Initialization or argument error
- 2: No barcodes found and `--fail-on-empty` specified

## Extending for Camera Capture (Optional)
Once you verify the correct signature for `decode_buffer`, you can add OpenCV:
```powershell
pip install opencv-python
```
Then implement a loop capturing frames and passing RGB buffers into `decode_buffer`. Refer to Dynamsoft docs for the exact parameters.

## Module Overview
- `dbr_cli/scanner.py`: Wrapper around DBR SDK (file scanning implemented)
- `dbr_cli/cli.py`: Argument parsing & orchestration
- `scan.py`: Entry script convenience wrapper

## JSON Output Example
```json
[
  {
    "text": "9781234567897",
    "format": "EAN_13",
    "source": "samples/book1.jpg",
    "confidence": 98,
    "x1": 10, "y1": 12, "x2": 180, "y2": 12, "x3": 180, "y3": 60, "x4": 10, "y4": 60
  }
]
```

## Troubleshooting
- "Failed to initialize scanner": Ensure `dbr` installed and license set.
- Empty results: Try higher resolution images or clearer focus.

## License Key Management
Prefer environment variable `DBR_LICENSE` to avoid exposing in scripts. CI example (GitHub Actions):
```yaml
env:
  DBR_LICENSE: ${{ secrets.DBR_LICENSE }}
```

## Disclaimer
This is a minimal example. For production use add: logging, retries, concurrency, camera support, and configuration profiles.
