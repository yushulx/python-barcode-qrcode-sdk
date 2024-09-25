# Python Extension: Barcode and QR Code SDK 
This project provides a CPython binding to the [Dynamsoft C/C++ Barcode Reader SDK v9.x](https://www.dynamsoft.com/barcode-reader/sdk-desktop-server/). It demonstrates how to build a **Python 1D/2D barcode SDK** package for `Windows`, `Linux` and `macOS` from scratch. Beyond desktop PCs, it's also compatible with embedded and IoT devices such as `Raspberry Pi` and `Jetson Nano`. You are **free** to customize the Python API for Dynamsoft Barcode Reader to suit your specific needs.

> Note: This project is an unofficial, community-maintained Python wrapper for the Dynamsoft Barcode SDK. For those seeking the most reliable and fully-supported solution, Dynamsoft offers an official Python package. Visit the [Dynamsoft Barcode Reader](https://pypi.org/project/dbr/) page on PyPI for more details.

## About Dynamsoft Python Barcode SDK
- Get a [30-day FREE trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) to activate the SDK.
- Install the official Python barcode SDK via `pip install dbr`.

### Comparison Table
| Feature | Unofficial Wrapper (Community) | Official Dynamsoft Python Barcode SDK |
| --- | --- | --- |
| Support | Community-driven, best effort | Official support from Dynamsoft |
| Documentation | README only | [Comprehensive Online Documentation](https://www.dynamsoft.com/barcode-reader/programming/python/index.html) |
| API Coverage | Limited | Full API coverage |
|Feature Updates| May lag behind the official SDK | First to receive new features |
| Compatibility | Limited testing across environments| Thoroughly tested across all supported environments|

## Supported Python Edition
* Python 3.x

## Installation of Dependencies
To show UI, you need to install the OpenCV package:
```bash 
pip install opencv-python
```

## Command-line Usage
```bash 
$ scanbarcode <file-name> -l <license-key>

# Show the image with OpenCV
$ scanbarcode <file-name> -u 1 -l <license-key>
```

![python barcode QR code scanner](https://www.dynamsoft.com/codepool/img/2022/08/python-scan-barcode.png)


## How to Build the Python Barcode and QR Code Extension
- Create a source distribution:
    
    ```bash
    python setup.py sdist
    ```

- setuptools:
    
    ```bash
    python setup_setuptools.py build
    python setup_setuptools.py develop # Copy libraries to barcodeQrSDK folder
    ```

- scikit-build:
    
    ```bash
    python setup.py build
    python setup.py develop # Copy libraries to barcodeQrSDK folder
    ```
- Build wheel:
    
    ```bash
    pip wheel . --verbose
    # Or
    python setup_setuptools.py bdist_wheel
    # Or
    python setup.py bdist_wheel
    ```


## Quick Start
- Console App
    ```python
    import barcodeQrSDK

    # set license
    barcodeQrSDK.initLicense("LICENSE-KEY")

    reader = barcodeQrSDK.createInstance()

    results, elapsed_time = reader.decodeFile("IMAGE-FILE")
    for result in results:
        print(result.format)
        print(result.text)
        print(result.x1)
        print(result.y1)
        print(result.x2)
        print(result.y2)
        print(result.x3)
        print(result.y3)
        print(result.x4)
        print(result.y4)
    ```
- Video App
    ```python
    import barcodeQrSDK
    import numpy as np
    import cv2
    import json

    g_results = None

    def callback(results, elapsed_time):
        global g_results
        g_results = (results, elapsed_time)

    def run():
        # set license
        barcodeQrSDK.initLicense("LICENSE-KEY")

        # initialize barcode scanner
        scanner = barcodeQrSDK.createInstance()
        params = scanner.getParameters()
        # Convert string to JSON object
        json_obj = json.loads(params)
        # json_obj['ImageParameter']['ExpectedBarcodesCount'] = 999
        params = json.dumps(json_obj)
        ret = scanner.setParameters(params)
        
        scanner.addAsyncListener(callback)

        cap = cv2.VideoCapture(0)
        while True:
            ret, image = cap.read()
            if image is not None:
                scanner.decodeMatAsync(image)
                
            if g_results != None:
                print('Elapsed time: ' + str(g_results[1]) + 'ms')
                cv2.putText(image, 'Elapsed time: ' + str(g_results[1]) + 'ms', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                for result in g_results[0]:
                    x1 = result.x1
                    y1 = result.y1
                    x2 = result.x2
                    y2 = result.y2
                    x3 = result.x3
                    y3 = result.y3
                    x4 = result.x4
                    y4 = result.y4
                    
                    cv2.drawContours(image, [np.int0([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)
                    cv2.putText(image, result.text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('Barcode QR Code Scanner', image)
            ch = cv2.waitKey(1)
            if ch == 27:
                break
        
        scanner.clearAsyncListener()

    if __name__ == '__main__':
        run()
    ```
    
    ![Python barcode and QR code scanner](https://www.dynamsoft.com/codepool/img/2024/08/python-barcode-scanner.png)



## Methods
- `barcodeQrSDK.initLicense('YOUR-LICENSE-KEY')`: Set the global license key for the barcode SDK.
    
    ```python
    barcodeQrSDK.initLicense("LICENSE-KEY")
    ```

- `barcodeQrSDK.createInstance()`: Create a new barcode reader instance.
    
    ```python
    reader = barcodeQrSDK.createInstance()
    ```
- `decodeFile(filename)`: Decode barcodes and QR codes from an image file.

    ```python
    results, elapsed_time = reader.decodeFile("IMAGE-FILE")
    ```
- `decodeMat(Mat image)`: Decode barcodes and QR codes from an OpenCV Mat.
    ```python
    image = cv2.imread("IMAGE-FILE")
    results = reader.decodeMat(image)
    for result in results:
        print(result.format)
        print(result.text)
        print(result.x1)
        print(result.y1)
        print(result.x2)
        print(result.y2)
        print(result.x3)
        print(result.y3)
        print(result.x4)
        print(result.y4)
    ```

- `getParameters()`: Retrieve the current SDK parameters as a JSON string.
    
    ```python
    params = reader.getParameters()
    ```

- `setParameters(JSON string)`: Set barcode SDK parameters using a JSON string.
    
    ```python
    import json
    json_obj = json.loads(params)
    json_obj['ImageParameter']['DPMCodeReadingModes'][0]['Mode'] = 'DPMCRM_GENERAL'
    json_obj['ImageParameter']['LocalizationModes'][0]['Mode'] = 'LM_STATISTICS_MARKS'
    params = json.dumps(json_obj)
    ret = reader.setParameters(params)
    ```

- `addAsyncListener(callback function)`: Register a Python function to receive barcode results asynchronously.
- `decodeMatAsync(<opencv mat data>)`: Asynchronously decode barcodes and QR codes from an OpenCV Mat.
    ```python
    def callback(results, elapsed_time):
        print(results)
                                                        
    import cv2
    image = cv2.imread("IMAGE-FILE")
    reader.addAsyncListener(callback)
    reader.decodeMatAsync(image)
    sleep(1)
    ```
- `clearAsyncListener()`: Stop the asynchronous listener and clear the registered callback.
- `decodeBytes(bytes, width, height, stride, imageformat)`: Decode barcodes from a raw image byte array.

    ```python
    import cv2
    image = cv2.imread("IMAGE-FILE")
    results, elapsed_time = scanner.decodeBytes(image.tobytes(), image.shape[1], image.shape[0], image.strides[0], barcodeQrSDK.ImagePixelFormat.IPF_BGR_888)
    ```
- `decodeBytesAsync`: Asynchronously decode image byte arrays.

    ```python
    def callback(results, elapsed_time):
        print(results)
                                                        
    import cv2
    image = cv2.imread("IMAGE-FILE")
    imagebytes = image.tobytes()
    scanner.decodeBytesAsync(image.tobytes(), image.shape[1], image.shape[0], image.strides[0], barcodeQrSDK.ImagePixelFormat.IPF_BGR_888)
    sleep(1)
    ```

## Supported Barcode Symbologies
- Linear Barcodes (1D)

    - Code 39 (including Code 39 Extended)
    - Code 93
    - Code 128
    - Codabar
    - Interleaved 2 of 5
    - EAN-8
    - EAN-13
    - UPC-A
    - UPC-E
    - Industrial 2 of 5

- 2D Barcodes:
    - QR Code (including Micro QR Code)
    - Data Matrix
    - PDF417 (including Micro PDF417)
    - Aztec Code
    - MaxiCode (mode 2-5)

- Patch Code
- GS1 Composite Code
