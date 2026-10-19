# Python Barcode Scanner & Reader
This repository contains example code for using the [Dynamsoft Barcode Reader Bundle](https://pypi.org/project/dynamsoft-barcode-reader-bundle/) to detect barcodes from a camera video stream or an image file.

https://github.com/user-attachments/assets/18503750-68bd-4043-8187-353e7e8a7808

## Prerequisites
- [Dynamsoft Capture Vision Trial License](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform)
    
    ```python
    errorCode, errorMsg = LicenseManager.init_license(
        "LICENSE-KEY")
    ```
    
- SDK Installation
 
    ```bash
    pip install -r requirements.txt
    ```

## Supported Platforms
- Windows
- Linux
- macOS
    
  
## Examples
- [camera.py](./camera.py): Scan barcodes from a camera video stream.
- [file.py](./file.py): Read barcodes from an image file and display the results in a window.
