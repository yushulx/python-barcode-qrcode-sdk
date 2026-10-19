#!/usr/bin/env python3
"""
Command Line Barcode Scanner using Dynamsoft Barcode Reader SDK
"""

import sys
import argparse
from dbr import *

def main():
    parser = argparse.ArgumentParser(description='Scan barcodes from an image file.')
    parser.add_argument('image_path', help='Path to the image file containing barcodes')
    parser.add_argument('--license', default='', help='License key for Dynamsoft Barcode Reader (optional for trial)')

    args = parser.parse_args()

    # Initialize license
    if args.license:
        error = LicenseManager.init_license(args.license)
        if error[0] != EnumErrorCode.EC_OK:
            print(f"License initialization failed: {error[1]}")
            return 1
    else:
        # Use trial license
        error = LicenseManager.init_license("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2JvFpZGl0bGUiOiJ3ZWIiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
        if error[0] != EnumErrorCode.EC_OK:
            print(f"Trial license initialization failed: {error[1]}")
            return 1

    # Create a CaptureVisionRouter instance
    cvr = CaptureVisionRouter()

    # Capture barcodes from the image
    result = cvr.capture(args.image_path, EnumPresetTemplate.PT_READ_BARCODES.value)

    if result.get_error_code() != EnumErrorCode.EC_OK:
        print(f"Error: {result.get_error_string()}")
        return 1

    items = result.get_items()
    if not items:
        print("No barcodes detected.")
        return 0

    print(f"Detected {len(items)} barcode(s):")
    for i, item in enumerate(items, 1):
        print(f"{i}. Format: {item.get_format_string()}")
        print(f"   Text: {item.get_text()}")
        print()

    return 0

if __name__ == "__main__":
    sys.exit(main())