# Python Extension: Barcode and QR Code SDK 
The project uses CPython to bind [Dynamsoft C/C++ Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/sdk-desktop-server/). It aims to help developers build **Python barcode and QR code scanning** apps on Windows, Linux, macOS, Raspberry Pi and Jetson Nano. You are free to customize the Python API for Dynamsoft Barcode Reader.

## Dynamsoft Barcode Reader Version
v9.0.0

## License Key for SDK
Click [here](https://www.dynamsoft.com/customer/license/trialLicense?product=dbr) to get a 30-day FREE trial license. 


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


## Supported Python Edition
* Python 3.x

## Requirements
- [Dynamsoft C/C++ Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/downloads).

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

    reader = barcodeQrSDK.DynamsoftBarcodeReader()

    results = reader.decodeFile("test.png")
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
    import cv2
    import barcodeQrSDK
    import time
    import numpy as np
    # set license
    barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

    # initialize barcode reader
    reader = barcodeQrSDK.DynamsoftBarcodeReader()

    def get_time():
        localtime = time.localtime()
        capturetime = time.strftime("%Y%m%d%H%M%S", localtime)
        return capturetime


    def read_barcode():

        vc = cv2.VideoCapture(0)

        if vc.isOpened():  # try to get the first frame
            rval, frame = vc.read()
        else:
            return

        windowName = "Barcode Reader"

        while True:
            cv2.imshow(windowName, frame)
            rval, frame = vc.read()
            results = reader.decodeMat(frame)
            if (len(results) > 0):
                print(get_time())
                print("Total count: " + str(len(results)))
                for result in results:
                    print("Type: " + result.format)
                    print("Value: " + result.text + "\n")
                    x1 = result.x1
                    y1 = result.y1
                    x2 = result.x2
                    y2 = result.y2
                    x3 = result.x3
                    y3 = result.y3
                    x4 = result.x4
                    y4 = result.y4

                    cv2.drawContours(frame, [np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)

            # 'ESC' for quit
            key = cv2.waitKey(20)
            if key == 27:
                break

        cv2.destroyWindow(windowName)


    if __name__ == "__main__":
        print("OpenCV version: " + cv2.__version__)
        read_barcode()
    ```
    
    ![Python barcode and QR code scanner](https://user-images.githubusercontent.com/2202306/170233943-a48012e3-1b16-4d10-89ef-3120f6ea2d44.png)

## Online Documentation
To customize Python API based on C/C++, please refer to the
[online documentation](https://www.dynamsoft.com/barcode-reader/programming/c/user-guide.html?ver=latest).

