# Python Extension: Barcode and QR Code SDK 
The project uses CPython to bind [Dynamsoft C/C++ Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/sdk-desktop-server/). It aims to help developers build **Python barcode and QR code scanning** apps on Windows, Linux, macOS, Raspberry Pi and Jetson Nano. You are free to customize the Python API for Dynamsoft Barcode Reader.

## Dynamsoft Barcode Reader Version
v9.0.0

## License Key for SDK
Click [here](https://www.dynamsoft.com/customer/license/trialLicense?product=dbr) to get a 30-day FREE trial license. 


## Supported Symbologies
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
- GS1 DataBar (Omnidirectional,
Truncated, Stacked, Stacked
Omnidirectional, Limited,
Expanded, Expanded Stacked)
- GS1 Composite Code


    
## How to Build

### Requirements
- [Dynamsoft C/C++ Barcode Reader SDK](https://www.dynamsoft.com/barcode-reader/downloads).
- OpenCV  
- NumPy

## How to Use



## Examples
- examples/video

    ```
    python rtsp.py
    ```
    
- examples/camera

    ```
    python camera-decodevideo.py
    ```
    
- examples/command-line

    ```
    python test.py
    ```

## Functions
- initLicense(license-key)
- decodeFile(filename, barcodeTypes) 

    ```
    barcodeTypes = dbr.BF_ONED | dbr.BF_PDF417 | dbr.BF_QR_CODE | dbr.BF_DATAMATRIX | dbr.BF_AZTEC 
    ```

    | Barcode Format| Values            |
    | ------------- |-------------------|
    | ALL           | dbr.BF_ALL        |
    | 1D            | dbr.BF_ONED       |
    | PDF417        | dbr.BF_PDF417     |
    | QR Code       | dbr.BF_QR_CODE    |
    | DataMatrix    | dbr.BF_DATAMATRIX |
    | Aztec Code    | dbr.BF_AZTEC      |

- decodeBuffer(frame-by-opencv-capture, barcodeTypes)
- decodeFileStream(fileStream, fileSzie, barcodeTypes)
- startVideoMode(max_buffer, max_results, video_width, video_height, image_format, barcodeTypes, callback)
- stopVideoMode()
- appendVideoFrame(frame-by-opencv-capture)
- initLicenseFromLicenseContent(license-key, license-content)
- outputLicenseToString()
- initLicenseFromServer(license-key, license-server)
- setFurtherModes(mode, [values])
- setParameters(json-string)

## Online Documentation
To customize Python API based on C/C++, please refer to the
[online documentation](https://www.dynamsoft.com/Products/Barcode-Reader-Resources.aspx#documentation).

