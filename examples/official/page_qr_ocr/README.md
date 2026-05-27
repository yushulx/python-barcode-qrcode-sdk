# Page QR + Page Number OCR

This folder contains a small PySide6 desktop app for fixed-layout pages where a QR code sits near the top-left corner and the printed page number appears just to the left of it.

The project uses a single Dynamsoft Capture Vision template to do both tasks in one pass:

- decode the QR code
- run OCR in a barcode-referenced ROI
- choose the most likely page number from the OCR hits
- draw both results as overlays in the GUI


https://github.com/user-attachments/assets/d8ffc6a8-d2d1-45fd-98ad-fb52f1e874e8


## Project Layout

- `app.py` — Python desktop app and scanner logic
- `page_qr_ocr_template.json` — combined barcode + OCR template
- `requirements.txt` — runtime and synthetic-data dependencies
- `synthetic/` — generated images plus `manifest.json`

## Requirements

- Python 3.9+
- `dynamsoft-capture-vision-bundle>=3.4.2001`
- `PySide6>=6.5`
- `opencv-python>=4.8`
- `numpy>=1.24`

## Install

```bash
pip install -r requirements.txt
```

## Run the GUI

```bash
python app.py
```

