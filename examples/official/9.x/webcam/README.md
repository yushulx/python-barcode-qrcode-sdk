# Reading Barcodes and QR Codes Using Webcam, Python, and OpenCV
This repository provides samples demonstrating how to create a simple barcode and QR code reader using a webcam in Python. The OpenCV Stitcher API is utilized to stitch multiple barcode and QR code results together.

## License Activation
To activate the [Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/sdk-desktop-server/), obtain a desktop license key from [here](https://www.dynamsoft.com/customer/license/trialLicense?product=dbr):

```python
BarcodeReader.init_license("LICENSE-KEY")
```

## Installation
Install the required dependencies using pip:

```
pip install opencv-python dbr
```

## Examples

- [scanner.py](./scanner.py)
    
    Use your webcam to scan barcodes and QR codes in real-time.

    ![Python barcode and QR code reader](https://www.dynamsoft.com/codepool/img/2022/04/multiple-barcode-qrcode-scan.png)

- [stitcher.py](./stitcher.py)
    
    Move the camera closer to scan barcodes and QR codes with higher precision, and stitch them into a panorama image.

    ![Python barcode and QR code reader with panorama stitching](https://www.dynamsoft.com/codepool/img/2022/04/panorama-barcode-qr-code.png)

- [barcode_based_panorama.py](./barcode_based_panorama.py)
    Concatenate images based on barcode and QR code detection results, without using any advanced image processing algorithms.
    
    ![concatenate barcode and QR code images](./output.png)
    
- [barcode_reader.py](./barcode_reader.py)
    Read barcodes and QR codes from image files:
    
    ```bash
    python barcode_reader.py <image-file>
    ```

## Blog
[Scanning Barcode and QR Code Using Webcam, OpenCV and Python](https://www.dynamsoft.com/codepool/opencv-python-webcam-barcode-reader.html)

