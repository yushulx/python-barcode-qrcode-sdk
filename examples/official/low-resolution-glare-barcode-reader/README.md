# Low-resolution and Glare Barcode Reader Benchmark

This sample generates synthetic Code 128 and QR test images with low resolution,
low light, glare, blur, inverted polarity, and inverted low-light conditions. It
then compares Dynamsoft Capture Vision's built-in `PT_READ_BARCODES` preset
against a focused custom template that adds grayscale inversion and restricts
formats to Code 128 and QR Code.

https://github.com/user-attachments/assets/b07bbbc0-5069-4466-9133-b3d00cb95874

## Run

```bash
pip install -r requirements.txt
python generate_test_images.py
python benchmark_dbr_templates.py
```

Set `DYNAMSOFT_LICENSE_KEY` to your [own license key](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) for production runs. The
benchmark script includes a public trial key fallback for reproducible demos.

## Outputs

- `assets/images/*.png`: generated barcode and QR test images
- `assets/ground_truth.json`: expected barcode text for each test image
- `templates/read-barcodes-fast-inverted.json`: fast custom template
- `reports/benchmark-results.json`: per-image decode results
- `reports/benchmark-report.html`: visual report with bar charts and files
  recovered by the custom template
