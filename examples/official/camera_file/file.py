import sys
from dynamsoft_capture_vision_bundle import *
import os
import cv2
import numpy as np
from utils import *

if __name__ == '__main__':

    print("**********************************************************")
    print("Welcome to Dynamsoft Capture Vision - Barcode Sample")
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
            result = cvr_instance.capture(
                image_path, EnumPresetTemplate.PT_READ_BARCODES.value)
            if result.get_error_code() != EnumErrorCode.EC_OK:
                print("Error:", result.get_error_code(),
                      result.get_error_string())
            else:
                cv_image = cv2.imread(image_path)

                items = result.get_items()
                print('Found {} barcodes.'.format(len(items)))
                for item in items:
                    format_type = item.get_format()
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

                    cv2.drawContours(
                        cv_image, [np.intp([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)

                    cv2.putText(cv_image, text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                cv2.imshow(
                    "Original Image with Detected Barcodes", cv_image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    input("Press Enter to quit...")
