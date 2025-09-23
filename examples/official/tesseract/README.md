# OCR-Enhanced Barcode Validation 

This project demonstrates how to use **Tesseract OCR** as a complementary technology to enhance barcode reading accuracy, especially when dealing with damaged or low-quality barcode images.


## Features

- **Dual Recognition**: Attempts barcode scanning first, falls back to OCR if needed
- **Multiple Format Support**: Handles various 1D barcode formats (Codabar, Code 128, etc.)
- **Damage Resilience**: Extracts text from damaged or low-quality barcode images
- **Detailed Output**: Provides barcode location coordinates and format information
- **Digit Extraction**: Filters OCR results to extract only numeric characters

## Prerequisites
- Obtain a [30-day free trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) for Dynamsoft Barcode Reader.
- Python 3.6 or higher
- Tesseract OCR installation
  - Windows: Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS:
    
     ```bash
     brew install tesseract
     ```
  
  - Linux:
  
       ```bash
       sudo apt update
       sudo apt install tesseract-ocr -y
       sudo apt install libtesseract-dev -y
       ```

- Python dependencies:
    
    ```bash
    pip install dynamsoft-capture-vision-bundle pytesseract pillow
    ```

## Quick Start
1. Set the license key in `app.py`:
   ```python
   error_code, error_message = LicenseManager.init_license("YOUR_LICENSE_KEY_HERE")
   ```

2. Run the application:
   ```bash
   python app.py
   ```

## Sample Images
The project includes two test images:
- `codabar.jpg` - A clear Codabar barcode image
- `damaged.png` - A damaged barcode image to demonstrate OCR fallback

