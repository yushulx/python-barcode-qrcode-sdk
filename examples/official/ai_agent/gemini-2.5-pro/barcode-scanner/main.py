import os
from dbr import *

# Initialize the barcode reader
try:
    # You can get a free trial license key from https://www.dynamsoft.com/customer/license/trialLicense?product=dbr
    BarcodeReader.init_license("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
    reader = BarcodeReader()
except BarcodeReaderError as bre:
    print(bre)

def decode_file(file_path):
    """Decodes barcodes from a file."""
    try:
        results = reader.decode_file(file_path)
        if results is not None:
            for result in results:
                print(f"Barcode Format: {result.barcode_format_string}")
                print(f"Barcode Text: {result.barcode_text}")
                print("--------------------")
    except BarcodeReaderError as bre:
        print(bre)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py <image_file>")
    else:
        image_file = sys.argv[1]
        if not os.path.exists(image_file):
            print(f"File not found: {image_file}")
        else:
            decode_file(image_file)
