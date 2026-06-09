# Retail Checkout Barcode Reader (Python + PySide6 + Dynamsoft)

A point-of-sale style barcode scanner that reads the symbologies a real retail
checkout encounters — **EAN-13, UPC-A, EAN-8, Code 128, GS1-128, and QR** —
from a **live camera** or an **image file**, using the
[Dynamsoft Barcode Reader Bundle](https://www.dynamsoft.com/barcode-reader/overview/) for Python.

https://github.com/user-attachments/assets/204c6adb-3cfd-45c2-8f45-c297279b49c5

## Setup

```bash
pip install -r requirements.txt
```

## Generate the Image Set

```bash
python generate_retail_images.py
```

## Run the Scanner App

```bash
python retail_scanner_gui.py
```

- **Open Image** — pick `images/checkout-belt.png` to decode a whole frame at once.
- **Start Camera** — point a webcam at any product barcode.


## License

Get a 30-day free trial license at
[dynamsoft.com/customer/license/trialLicense](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform)
and replace `LICENSE_KEY` in `retail_scanner_gui.py`.

## Blog
[How to Choose a Barcode Reader for Retail Checkout Systems](https://www.dynamsoft.com/codepool/choose-barcode-reader-retail-checkout-systems.html)
