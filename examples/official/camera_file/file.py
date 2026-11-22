import sys
from dynamsoft_barcode_reader_bundle import *
import os
import cv2
import numpy as np
from utils import *

if __name__ == '__main__':

    print("**********************************************************")
    print("Welcome to Dynamsoft Barcode Reader Bundle - Barcode Sample")
    print("**********************************************************")

    error_code, error_message = LicenseManager.init_license(
        "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
    if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print("License initialization failed: ErrorCode:",
              error_code, ", ErrorString:", error_message)
    else:
        cvr_instance = CaptureVisionRouter()
        while (True):
            image_path = input(
                ">> Input your image full path:\n"
                ">> 'Enter' for sample image or 'Q'/'q' to quit\n"
            ).strip('\'"')

            if image_path.lower() == "q":
                sys.exit(0)

            if image_path == "":
                image_path = "../../../images/multi.png"

            if not os.path.exists(image_path):
                print("The image path does not exist.")
                continue

            result_array = cvr_instance.capture_multi_pages(
                image_path, EnumPresetTemplate.PT_READ_BARCODES.value)

            results = result_array.get_results()
            if results is None or len(results) == 0:
                print("No pages were processed.")
                continue

            total_barcodes = 0
            for page_result in results:
                page_number = 1
                tag = page_result.get_original_image_tag()
                if isinstance(tag, FileImageTag):
                    page_number = tag.get_page_number() + 1

                if page_result.get_error_code() != EnumErrorCode.EC_OK and \
                        page_result.get_error_code() != EnumErrorCode.EC_UNSUPPORTED_JSON_KEY_WARNING:
                    print("Page", page_number, "Error:",
                          page_result.get_error_code(),
                          page_result.get_error_string())
                    continue

                items = page_result.get_items()
                total_barcodes += len(items)
                print("Page {}: found {} barcode(s).".format(page_number, len(items)))
                for item in items:
                    format_type = item.get_format_string()
                    text = item.get_text()
                    print("Barcode Format:", format_type)
                    print("Barcode Text:", text)

                    location = item.get_location()
                    x1 = location.points[0].x
                    y1 = location.points[0].y
                    x2 = location.points[1].x
                    y2 = location.points[1].y
                    x3 = location.points[2].x
                    y3 = location.points[2].y
                    x4 = location.points[3].x
                    y4 = location.points[3].y
                    print("Location Points:")
                    print("({}, {})".format(x1, y1))
                    print("({}, {})".format(x2, y2))
                    print("({}, {})".format(x3, y3))
                    print("({}, {})".format(x4, y4))
                    print("-------------------------------------------------")

            print("Total: {} barcode(s) across {} page(s).".format(
                total_barcodes, len(results)))

    input("Press Enter to quit...")
