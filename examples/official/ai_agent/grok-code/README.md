# Command Line Barcode Scanner

A simple command line tool to scan barcodes from image files using the Dynamsoft Barcode Reader SDK.

## Installation

1. Install Python 3.6 or later.

2. Install the required package:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the scanner with an image file:

```bash
python scanner.py path/to/image.jpg
```

For images with multiple barcodes, all detected barcodes will be printed.

## License

This tool uses the Dynamsoft Barcode Reader SDK. For production use, obtain a license from [Dynamsoft](https://www.dynamsoft.com/).

For trial purposes, a trial license is included in the code.