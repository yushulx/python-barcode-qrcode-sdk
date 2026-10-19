# Command-Line Barcode Scanner

A Python command-line application for scanning barcodes from images using the Dynamsoft Barcode Reader SDK.

## Features

- Scan barcodes from a single image file
- Batch scan multiple images from a directory
- Supports various barcode formats (QR Code, Code 39, Code 128, EAN, UPC, DataMatrix, PDF417, and more)
- Simple command-line interface

## Prerequisites

- Python 3.8 or higher
- Internet connection (for license validation on first use)

## Installation

1. Install the Dynamsoft Barcode Reader SDK:

```bash
pip install dynamsoft-barcode-reader-bundle
```

2. Clone or download this repository

## Usage

### Scan a Single Image

```bash
python barcode_scanner.py <image_path>
```

Example:
```bash
python barcode_scanner.py barcode.jpg
```

### Scan All Images in a Directory

```bash
python barcode_scanner.py --dir <directory_path>
```

Example:
```bash
python barcode_scanner.py --dir ./images
```

### Help

```bash
python barcode_scanner.py --help
```

## License

This application uses a public trial license that requires a network connection. The license key is embedded in the code: `DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==`

For production use or offline applications, you can request a 30-day free trial license from the [Dynamsoft Customer Portal](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform).

## Output Format

The scanner will display:
- Number of barcodes detected
- Barcode format (e.g., QR_CODE, CODE_128, EAN_13)
- Decoded text content

Example output:
```
Scanning barcode from: barcode.jpg

✓ Decoded 2 barcode(s):

Result 1:
  Format: QR_CODE
  Text: https://www.dynamsoft.com

Result 2:
  Format: CODE_128
  Text: 1234567890
```

## Supported Barcode Formats

The Dynamsoft Barcode Reader SDK supports:
- 1D barcodes: Code 39, Code 93, Code 128, Codabar, EAN-8, EAN-13, UPC-A, UPC-E, Interleaved 2 of 5, Industrial 2 of 5, ITF-14
- 2D barcodes: QR Code, DataMatrix, PDF417, Aztec, MaxiCode
- Postal Codes: USPS Intelligent Mail, Postnet, Planet, Australian Post, UK Royal Mail (RM4SCC)
- GS1 barcodes: GS1 DataBar, GS1 Composite

## Documentation

For more information about the Dynamsoft Barcode Reader SDK:
- [Python SDK Documentation](https://www.dynamsoft.com/barcode-reader/docs/server/programming/python/)
- [API Reference](https://www.dynamsoft.com/barcode-reader/docs/server/programming/python/api-reference/)
- [Sample Code Repository](https://github.com/Dynamsoft/barcode-reader-python-samples)