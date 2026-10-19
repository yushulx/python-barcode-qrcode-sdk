# Dynamsoft Barcode Scanner CLI

A command-line barcode scanner built with the Dynamsoft Barcode Reader SDK for Python.

## Installation

1. Install the Dynamsoft Barcode Reader SDK:
```bash
pip install dynamsoft-barcode-reader-bundle
```

2. Download the scanner script:
```bash
# The barcode_scanner.py file should be in this directory
```

## Usage

### Scan a single image:
```bash
python barcode_scanner.py path/to/your/image.jpg
```

### Scan all images in a directory:
```bash
python barcode_scanner.py path/to/images --batch
```

### Filter by barcode format:
```bash
python barcode_scanner.py image.jpg --format QR_CODE
```

### Verbose output:
```bash
python barcode_scanner.py image.jpg --verbose
```

### Combined options:
```bash
python barcode_scanner.py /path/to/images --batch --format CODE_128 --verbose
```

## Supported Barcode Formats

- QR_CODE
- CODE_128, CODE_39
- EAN_13, EAN_8
- UPC_A, UPC_E
- CODABAR, ITF
- PDF417
- DATAMATRIX
- AZTEC
- MAXICODE

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- GIF (.gif)

## License

The script uses a free public trial license that requires an internet connection. For offline use or production deployment, get a 30-day trial license from: https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform

## Examples

```bash
# Scan a QR code
python barcode_scanner.py qr_code.png

# Batch scan with detailed output
python barcode_scanner.py ./test_images --batch --verbose

# Look for specific format only
python barcode_scanner.py product.jpg --format CODE_128
```

## Troubleshooting

1. **License errors**: Make sure you have an internet connection for the trial license, or get an offline license.
2. **No barcodes found**: Try adjusting image quality, lighting, or ensure barcode is clearly visible.
3. **Import errors**: Ensure you've installed `dynamsoft-barcode-reader-bundle` correctly.