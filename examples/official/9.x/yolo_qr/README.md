# QR Detection with OpenCV and YOLO Model in Python
This repository provides samples demonstrating how to detect QR codes using **YOLO** and how to read QR codes with the [Dynamsoft Barcode Reader](https://www.dynamsoft.com/barcode-reader/overview/).

## Prerequisites
- OpenCV 4.x
    
    ```
    pip install opencv-python
    ```

- Dynamsoft Barcode Reader

    ```
    pip install dbr
    ```
- Obtain a [Dynamsoft Barcode Reader trial license](https://www.dynamsoft.com/customer/license/trialLicense?product=dbr) and update your code with the provided license key:
    
    ```python
    from dbr import *

    license_key = "LICENSE-KEY"
    BarcodeReader.init_license(license_key)
    reader = BarcodeReader()
    ```
    

## Usage

#### QR Detection

- From Image File:

    ```
    python3 opencv-yolo.py
    ```

- From Camera:

    ```
    python3 opencv-yolo-camera.py
    ```

    ![OpenCV YOLO for QR detection](https://www.dynamsoft.com/codepool/img/2020/11/opencv-dnn-yolo3-qr-detection.gif)

#### QR Reading with Dynamsoft Barcode Reader

Below is a sample code snippet for reading QR codes with the Dynamsoft Barcode Reader:

```py
from dbr import *

license_key = "LICENSE-KEY"
BarcodeReader.init_license(license_key)
reader = BarcodeReader()
settings = reader.reset_runtime_settings() 
settings = reader.get_runtime_settings()
settings.region_bottom  = bottom
settings.region_left    = left
settings.region_right   = right
settings.region_top     = top
reader.update_runtime_settings(settings)

try:
    text_results = reader.decode_buffer(frame)

    if text_results != None:
        for text_result in text_results:
            print("Barcode Format :")
            print(text_result.barcode_format_string)
            print("Barcode Text :")
            print(text_result.barcode_text)
            print("Localization Points : ")
            print(text_result.localization_result.localization_points)
            print("-------------")
except BarcodeReaderError as bre:
    print(bre)
```

- From Image File:

    ```
    python3 yolo-dbr.py
    ```

- From Camera:

    ```
    python3 yolo-dbr-camera.py
    ```

## Blog
[How to Detect and Decode QR Code with YOLO, OpenCV, and Dynamsoft Barcode Reader](https://www.dynamsoft.com/codepool/qr-code-detect-decode-yolo-opencv.html)