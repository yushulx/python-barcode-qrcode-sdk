# QR Detection with OpenCV and YOLO Model in Python
This repository provides samples demonstrating how to detect QR codes using **YOLO** and how to read QR codes with the [Dynamsoft Barcode Reader](https://www.dynamsoft.com/barcode-reader/overview/).

## Prerequisites
- OpenCV 4.x
    
    ```
    pip install opencv-python
    ```

- Dynamsoft Barcode Reader

    ```
    pip install dynamsoft-capture-vision-bundle
    ```
- Obtain a [Dynamsoft Barcode Reader trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) and update your code with the provided license key:
    
    ```python
    from dynamsoft_capture_vision_bundle import *

    errorCode, errorMsg = LicenseManager.init_license("LICENSE-KEY")
    if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print("License initialization failed: ErrorCode:",
                errorCode, ", ErrorString:", errorMsg)
    
    cvr_instance = CaptureVisionRouter() 
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

![QR code detection with YOLO and Dynamsoft Barcode Reader](https://www.dynamsoft.com/codepool/img/2020/11/python-qr-code-scan.png)

Below is a sample code snippet for reading QR codes with the Dynamsoft Barcode Reader:

```py
from dynamsoft_capture_vision_bundle import *

errorCode, errorMsg = LicenseManager.init_license("LICENSE-KEY")
if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
    print("License initialization failed: ErrorCode:",
            errorCode, ", ErrorString:", errorMsg)

cvr_instance = CaptureVisionRouter() 

error_code, error_msg, settings = cvr_instance.get_simplified_settings(EnumPresetTemplate.PT_READ_BARCODES.value)
quad = Quadrilateral()
quad.points = [Point(left, top), Point(right, top), Point(right, bottom), Point(left, bottom)]
settings.roi = quad
settings.roi_measured_in_percentage = False
cvr_instance.update_settings(EnumPresetTemplate.PT_READ_BARCODES.value, settings)

result = cvr_instance.capture(frame, EnumPresetTemplate.PT_READ_BARCODES.value)

items = result.get_items()
for item in items:
    print("Barcode Format :")
    print(item.get_format_string())
    print("Barcode Text :")
    print(item.get_text())

    location = item.get_location()
    x1 = location.points[0].x
    y1 = location.points[0].y
    x2 = location.points[1].x
    y2 = location.points[1].y
    x3 = location.points[2].x
    y3 = location.points[2].y
    x4 = location.points[3].x
    y4 = location.points[3].y

    print("Location Points:")
    print("({}, {})".format(x1, y1))
    print("({}, {})".format(x2, y2))
    print("({}, {})".format(x3, y3))
    print("({}, {})".format(x4, y4))
    print("-------------------------------------------------")
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
