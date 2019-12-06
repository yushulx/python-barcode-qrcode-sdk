# Dynamsoft Barcode Reader

[![Build status](https://ci.appveyor.com/api/projects/status/62oeg7hytq77sict?svg=true)](https://ci.appveyor.com/project/yushulx/python)

[Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/Products/Dynamic-Barcode-Reader.aspx) enables you to efficiently embed barcode reading functionality in your web, desktop and mobile application using just a few lines of code. This can save you months of added development time and extra costs. With our SDK, you can create high-speed and reliable barcode scanner software to meet your business needs.

## Environment
**Python 2/3**

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


## How to Install and Use the SDK

Install Dynamsoft Barcode Reader:

```bash
pip install dbr
```

A simple Python barcode reader app:

```python
from dbr import DynamsoftBarcodeReader
dbr = DynamsoftBarcodeReader()
dbr.initLicense('YOUR-LICENSE') # https://www.dynamsoft.com/CustomerPortal/Portal/Triallicense.aspx
results = dbr.decodeFile(fileName, dbr.BF_ONED | dbr.BF_PDF417 | dbr.BF_QR_CODE | dbr.BF_DATAMATRIX | dbr.BF_AZTEC)
for result in results:
    print("barcode format: " + result[0])
    print("barcode value: " + result[1])
```

## Screenshot
![webcam barcode reader with OpenCV Python](https://www.codepool.biz/wp-content/uploads/2017/04/python-barcode-reader.png)


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
https://www.dynamsoft.com/Products/Barcode-Reader-Resources.aspx#documentation


## Contact 
support@dynamsoft.com




    


