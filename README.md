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

- distutils:
    
    ```bash
    python .\setup_distutils.py build
    ```

- scikit-build:
    
    ```bash
    pip wheel . --verbose
    ```


## Quick Start

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

## Online Documentation
To customize Python API based on C/C++, please refer to the
[online documentation](https://www.dynamsoft.com/barcode-reader/programming/c/user-guide.html?ver=latest).

