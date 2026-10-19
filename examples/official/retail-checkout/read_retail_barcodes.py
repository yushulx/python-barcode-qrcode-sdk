"""
read_retail_barcodes.py
-----------------------
A point-of-sale style batch barcode decoder built on the Dynamsoft Barcode
Reader Bundle. It scans every image in the ./images tree, restricts decoding
to the symbologies a retail checkout actually sees, and prints a per-item
"receipt" plus a throughput summary.

Run:  python read_retail_barcodes.py
"""

import os
import time

from dynamsoft_barcode_reader_bundle import *

# Public trial license. Request your own 30-day license at:
# https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform
LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="

# Symbologies that dominate retail checkout: the EAN/UPC family for products,
# GS1 DataBar for produce/coupons, plus Code 128 / GS1-128 for logistics and
# QR for loyalty and digital coupons.
RETAIL_FORMATS = (
    EnumBarcodeFormat.BF_ONED          # EAN-13, EAN-8, UPC-A, UPC-E, Code 128, Code 39 ...
    | EnumBarcodeFormat.BF_GS1_DATABAR
    | EnumBarcodeFormat.BF_QR_CODE
)

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


def configure_router():
    """Create a CaptureVisionRouter tuned for retail symbologies."""
    cvr = CaptureVisionRouter()
    err_code, err_str, settings = cvr.get_simplified_settings(EnumPresetTemplate.PT_READ_BARCODES)
    settings.barcode_settings.barcode_format_ids = RETAIL_FORMATS
    # A self-checkout frame can hold many items; 0 means "find them all".
    settings.barcode_settings.expected_barcodes_count = 0
    err_code, err_str = cvr.update_settings(EnumPresetTemplate.PT_READ_BARCODES, settings)
    if err_code != EnumErrorCode.EC_OK:
        print("Warning: update_settings:", err_str)
    return cvr


def collect_images(root):
    paths = []
    for current_dir, _dirs, files in os.walk(root):
        for name in sorted(files):
            if name.lower().endswith(IMAGE_EXTS):
                paths.append(os.path.join(current_dir, name))
    return paths


def scan_image(cvr, image_path):
    """Return a list of (format, text) tuples for one image."""
    result = cvr.capture(image_path, EnumPresetTemplate.PT_READ_BARCODES)
    if result.get_error_code() not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_WARNING):
        print("  Error:", result.get_error_string())
        return []
    barcode_result = result.get_decoded_barcodes_result()
    if barcode_result is None:
        return []
    return [(item.get_format_string(), item.get_text()) for item in barcode_result.get_items()]


def main():
    err_code, err_str = LicenseManager.init_license(LICENSE_KEY)
    if err_code != EnumErrorCode.EC_OK and err_code != EnumErrorCode.EC_LICENSE_WARNING:
        print("License initialization failed:", err_code, err_str)
        return

    image_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    images = collect_images(image_root)
    if not images:
        print("No images found. Run generate_retail_images.py first.")
        return

    cvr = configure_router()

    total_codes = 0
    start = time.perf_counter()
    for image_path in images:
        rel = os.path.relpath(image_path, image_root)
        codes = scan_image(cvr, image_path)
        total_codes += len(codes)
        print(f"\n=== {rel} ===")
        if not codes:
            print("  No barcode detected.")
        for fmt, text in codes:
            print(f"  [{fmt:<12}] {text}")
    elapsed = time.perf_counter() - start

    print("\n--------------------------------------------------")
    print(f"Scanned {len(images)} images, decoded {total_codes} barcodes "
          f"in {elapsed:.2f}s ({total_codes / elapsed:.1f} codes/s).")


if __name__ == "__main__":
    main()
