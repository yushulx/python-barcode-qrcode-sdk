# Dynamsoft Barcode Reader

[Dynamsoft Barcode Reader SDK](https://www.dynamsoft.com/Products/Dynamic-Barcode-Reader.aspx) enables you to efficiently embed barcode reading functionality in your web, desktop and mobile application using just a few lines of code. This can save you months of added development time and extra costs. With our SDK, you can create high-speed and reliable barcode scanner software to meet your business needs.

## Supported Barcode Types

Code 39, Code 93, Code 128, Codabar, Interleaved 2 of 5, EAN-8, EAN-13, UPC-A, UPC-E, Industrial 2 of 5, QR code, Datamatrix and PDF417 .

## How to Install and Use the SDK

Install Dynamsoft Barcode Reader:

```bash
pip install dbr
```

Invoke the API:

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

## Contact 
support@dynamsoft.com




    


