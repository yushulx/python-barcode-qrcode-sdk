# Dynamsoft Capture Vision SDK for Barcode Detection
This repository contains example code for using the Dynamsoft Capture Vision SDK to detect barcodes in images.


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
- [camera.py](./camera.py): Detect barcodes from a camera video stream.
- [file.py](./file.py): Detect barcodes from an image file and display the results in a window.