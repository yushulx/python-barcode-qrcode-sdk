# Command Line Barcode Scanner

A powerful command-line barcode scanner built with Python using the Dynamsoft Barcode Reader SDK. This tool can scan barcodes from images, webcam feeds, and batch process entire folders.

## Features

- 📷 **Multiple Input Sources**: Scan from image files, webcam, or entire folders
- 🔍 **Multiple Barcode Formats**: Supports various barcode formats (QR Code, Code 128, Code 39, DataMatrix, PDF417, and many more)
- 📊 **Detailed Results**: Get barcode text, format, confidence level, and location coordinates
- 💾 **Export Results**: Save scan results to JSON format
- 🔄 **Batch Processing**: Scan multiple images in folders with recursive support
- 🎥 **Real-time Scanning**: Interactive webcam scanning with live preview
- 📋 **Comprehensive CLI**: Full-featured command-line interface

## Installation

### Prerequisites

- Python 3.7 or higher
- Windows, macOS, or Linux

### Install Dependencies

1. Clone or download this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

### Alternative Installation

You can also install the dependencies manually:

```bash
# Install Dynamsoft Barcode Reader SDK
pip install dynamsoft-barcode-reader

# Install OpenCV for webcam support
pip install opencv-python
```

## Usage

### Basic Commands

#### Scan a Single Image

```bash
python barcode_scanner.py --image path/to/image.jpg
```

#### Scan from Webcam

```bash
python barcode_scanner.py --webcam
```

#### Scan All Images in a Folder

```bash
python barcode_scanner.py --folder path/to/images/
```

### Advanced Options

#### Scan with License Key

```bash
python barcode_scanner.py --image sample.jpg --license YOUR_LICENSE_KEY
```

#### Save Results to JSON

```bash
python barcode_scanner.py --folder images/ --output results.json
```

#### Recursive Folder Scanning

```bash
python barcode_scanner.py --folder images/ --recursive
```

#### Use Different Camera

```bash
python barcode_scanner.py --webcam --camera 1
```

#### Verbose Output

```bash
python barcode_scanner.py --folder images/ --verbose
```

### Complete Examples

```bash
# Scan a single image and save results
python barcode_scanner.py --image product.jpg --output scan_results.json

# Scan entire folder recursively with verbose output
python barcode_scanner.py --folder ./products/ --recursive --verbose --output complete_scan.json

# Use webcam with external camera
python barcode_scanner.py --webcam --camera 1

# Batch process with license key
python barcode_scanner.py --folder ./inventory/ --license DLS2eyJoYW5kc2hha2VDb2Rl... --output inventory_scan.json
```

## Command Line Arguments

| Argument | Short | Description | Required |
|----------|--------|-------------|----------|
| `--image` | `-i` | Scan a single image file | * |
| `--webcam` | `-w` | Scan from webcam feed | * |
| `--folder` | `-f` | Scan all images in a folder | * |
| `--license` | `-l` | Dynamsoft license key | |
| `--output` | `-o` | Output JSON file to save results | |
| `--camera` | `-c` | Camera index for webcam mode (default: 0) | |
| `--recursive` | `-r` | Scan folder recursively | |
| `--verbose` | `-v` | Enable verbose output | |

*One of `--image`, `--webcam`, or `--folder` is required.

## Webcam Controls

When using webcam mode, use these keyboard shortcuts:

- **`c`** - Capture and scan current frame
- **`s`** - Save current frame as image
- **`q`** - Quit webcam mode

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- GIF (.gif)

## Supported Barcode Formats

The Dynamsoft Barcode Reader SDK supports numerous barcode formats including:

- **1D Barcodes**: Code 39, Code 128, Code 93, Codabar, EAN-8, EAN-13, UPC-A, UPC-E, ITF, Industrial 2 of 5, MSI Code
- **2D Barcodes**: QR Code, DataMatrix, PDF417, Aztec, MaxiCode
- **Postal Codes**: USPS Intelligent Mail, Postnet, Planet, Royal Mail, Australia Post, Deutsche Post
- **And many more**

## Output Format

### Console Output

```
Results for: sample.jpg
--------------------------------------------------
Found 2 barcode(s):

Barcode #1:
  Text: 1234567890
  Format: CODE_128
  Confidence: 95
  Location: [(10, 20), (200, 20), (200, 80), (10, 80)]

Barcode #2:
  Text: https://example.com
  Format: QR_CODE
  Confidence: 98
  Location: [(250, 50), (350, 50), (350, 150), (250, 150)]
```

### JSON Output

```json
{
  "sample.jpg": [
    {
      "text": "1234567890",
      "format": "CODE_128",
      "confidence": 95,
      "location": {
        "points": [[10, 20], [200, 20], [200, 80], [10, 80]]
      }
    },
    {
      "text": "https://example.com",
      "format": "QR_CODE",
      "confidence": 98,
      "location": {
        "points": [[250, 50], [350, 50], [350, 150], [250, 150]]
      }
    }
  ]
}
```

## License

### Trial License

The scanner works with a trial license by default. The trial license has some limitations:

- Limited number of scans
- Watermark on some outputs
- Time-limited usage

### Full License

For production use, you need a full license from Dynamsoft:

1. Visit [Dynamsoft Barcode Reader](https://www.dynamsoft.com/barcode-reader/overview/)
2. Sign up for a free trial or purchase a license
3. Use your license key with the `--license` parameter

## Troubleshooting

### Common Issues

#### "Dynamsoft Barcode Reader SDK not found"

```bash
pip install dynamsoft-barcode-reader
```

#### "Could not open camera"

- Check if your camera is being used by another application
- Try a different camera index: `--camera 1`
- Ensure you have camera permissions

#### "No module named 'cv2'"

```bash
pip install opencv-python
```

#### Poor Barcode Recognition

- Ensure good lighting
- Use high-resolution images
- Make sure barcodes are not blurry or damaged
- Try different angles or distances

### Performance Tips

1. **Image Quality**: Use high-resolution, well-lit images for better accuracy
2. **File Formats**: JPEG and PNG generally work best
3. **Batch Processing**: Use folder scanning for multiple files instead of individual scans
4. **Memory Usage**: For large folders, consider processing in smaller batches

## Development

### Code Structure

- `BarcodeScanner`: Main class handling all scanning operations
- `scan_image()`: Process individual image files
- `scan_webcam()`: Handle real-time webcam scanning
- `scan_folder()`: Batch process image folders
- `main()`: Command-line interface and argument parsing

### Extending the Scanner

You can extend the scanner by:

1. Adding new output formats
2. Implementing additional image preprocessing
3. Adding support for different input sources
4. Integrating with databases or APIs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues related to:
- **This script**: Create an issue in this repository
- **Dynamsoft SDK**: Visit [Dynamsoft Support](https://www.dynamsoft.com/barcode-reader/docs/core/introduction/)
- **OpenCV**: Check [OpenCV Documentation](https://docs.opencv.org/)

## Examples and Use Cases

### Inventory Management

```bash
# Scan product images with barcodes
python barcode_scanner.py --folder ./product_photos/ --recursive --output inventory.json
```

### Quality Control

```bash
# Quick single item check
python barcode_scanner.py --image item.jpg
```

### Bulk Processing

```bash
# Process large batches with detailed logging
python barcode_scanner.py --folder ./batch_images/ --verbose --output batch_results.json
```

### Interactive Scanning

```bash
# Real-time scanning for receiving goods
python barcode_scanner.py --webcam
```