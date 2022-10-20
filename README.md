# Python Extension: Barcode and QR Code SDK 
The project is a CPython binding to [Dynamsoft C/C++ Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/sdk-desktop-server/). It aims to help developers build **Python barcode and QR code scanning** apps on `Windows`, `Linux` and `macOS`. Besides desktop PCs, it can work well on embedded and IoT devices such as `Raspberry Pi` and `Jetson Nano`. You are **free** to customize the Python API for Dynamsoft Barcode Reader.

## About Dynamsoft Barcode Reader
- [Dynamsoft C/C++ Barcode Reader SDK v9.4.0](https://www.dynamsoft.com/barcode-reader/downloads)
- Get a [30-day FREE trial license](https://www.dynamsoft.com/customer/license/trialLicense?product=dbr) to activate the SDK.


## Supported Python Edition
* Python 3.x

## Install Dependencies
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
    barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

    reader = barcodeQrSDK.createInstance()

    results, elapsed_time = reader.decodeFile("test.png")
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
        barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

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
    
    ![Python barcode and QR code scanner](https://camo.githubusercontent.com/4463fa22e7bb08d196623b2ff181f22c7d92f4399298c37fd5ea43b396ed5b04/68747470733a2f2f7777772e64796e616d736f66742e636f6d2f636f6465706f6f6c2f696d672f323032322f31302f707974686f6e2d6465736b746f702d626172636f64652d71722d7363616e6e65722e706e67)



## Methods
- `barcodeQrSDK.initLicense('YOUR-LICENSE-KEY')` # set barcode SDK license globally
    
    ```python
    barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
    ```

- `barcodeQrSDK.createInstance()` # create a barcode reader instance
    
    ```python
    reader = barcodeQrSDK.createInstance()
    ```
- `decodeFile(filename)` # decode barcode and QR code from an image file

    ```python
    results, elapsed_time = reader.decodeFile("test.png")
    ```
- `decodeMat(Mat image)` # decode barcode and QR code from Mat
    ```python
    image = cv2.imread("test.png")
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

- `getParameters()` # return JSON string
    
    ```python
    params = reader.getParameters()
    ```

- `setParameters(JSON string)` # set barcode SDK parameters
    
    ```python
    import json
    json_obj = json.loads(params)
    json_obj['ImageParameter']['DPMCodeReadingModes'][0]['Mode'] = 'DPMCRM_GENERAL'
    json_obj['ImageParameter']['LocalizationModes'][0]['Mode'] = 'LM_STATISTICS_MARKS'
    params = json.dumps(json_obj)
    ret = reader.setParameters(params)
    ```

- `addAsyncListener(callback function)` # start a native thread and register a Python function for receiving barcode QR code results
- `decodeMatAsync(<opencv mat data>)` # decode barcode QR code from OpenCV Mat asynchronously
    ```python
    def callback(results, elapsed_time):
        print(results)
                                                        
    import cv2
    image = cv2.imread("test.png")
    reader.addAsyncListener(callback)
    reader.decodeMatAsync(image)
    sleep(1)
    ```
- `clearAsyncListener()` # stop the native thread and clear the registered Python function
- `decodeBytes(bytes, width, height, stride, imageformat)` # 0: gray; 1: rgb888
    ```python
    import cv2
    image = cv2.imread("test.png")
    results, elapsed_time = scanner.decodeBytes(image.tobytes(), image.shape[1], image.shape[0], image.strides[0], barcodeQrSDK.ImagePixelFormat.IPF_BGR_888)
    ```
- `decodeBytesAsync` # decode image byte array asynchronously

    ```python
    def callback(results, elapsed_time):
        print(results)
                                                        
    import cv2
    image = cv2.imread("test.png")
    imagebytes = image.tobytes()
    scanner.decodeBytesAsync(image.tobytes(), image.shape[1], image.shape[0], image.strides[0], barcodeQrSDK.ImagePixelFormat.IPF_BGR_888)
    sleep(1)
    ```

## Online Documentation for Dynamsoft C/C++ Barcode SDK
To customize Python API based on C/C++, please refer to the
[online documentation](https://www.dynamsoft.com/barcode-reader/programming/c/user-guide.html?ver=latest).

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