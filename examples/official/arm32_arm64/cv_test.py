#!/usr/bin/env python3
import os
import cv2 as cv
from dynamsoft_capture_vision_bundle import *
import time


def main():
    
    error_code, error_message = LicenseManager.init_license(
            "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
    if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print("License initialization failed: ErrorCode:",
                error_code, ", ErrorString:", error_message)

    # read file list
    folder = '../../../images'
    target_dir = os.path.join(os.getcwd(), folder)
    cvr_instance = CaptureVisionRouter()
    if os.path.exists(target_dir):
        filelist = os.listdir(target_dir)

        index = 0
        while index < 3:
            file = filelist[index]
            filapath = os.path.join(target_dir, file)

            if os.path.isfile(filapath):
                image = cv.imread(filapath)

                start_time = time.time()
                result = cvr_instance.capture(image, EnumPresetTemplate.PT_READ_BARCODES.value)
                elapsed_time = time.time() - start_time

                print(filelist[index] + ", elapsed time: " +
                      str(round(elapsed_time * 1000)) + "ms, ")
                if result.get_error_code() != EnumErrorCode.EC_OK:
                        print("Error:", result.get_error_code(),
                            result.get_error_string())
                else:
                    items = result.get_items()
                    print('Found {} barcodes.'.format(len(items)))
                    for item in items:
                        format_type = item.get_format_string()
                        text = item.get_text()
                        print("Barcode Format:", format_type)
                        print("Barcode Text:", text)

                
                print("-------------------------------------------------")

            index += 1
            
if __name__ == '__main__':
    main()
