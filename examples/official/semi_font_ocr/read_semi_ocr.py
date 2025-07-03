import os
from dynamsoft_capture_vision_bundle import *
import cv2
import numpy as np

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

if __name__ == '__main__':
    # 1.Initializes license.
    # You can request or extend a trial license at: https://www.dynamsoft.com/customer/license/trialLicense?product=dcv&utm_source=samples&package=python
    # The string below is a free public trial license. Note: an active internet connection is required for this license to work.
    err_code, err_str = LicenseManager.init_license("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
    if err_code != EnumErrorCode.EC_OK and err_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print("License initialization failed: ErrorCode: " + str(err_code) + ", ErrorString: " + err_str)
    else:
        # 2.Creates an instance of CaptureVisionRouter.
        cvr = CaptureVisionRouter()
        with open('models/semi-ocr.data', 'rb') as f:
            model_data = f.read()
            
        err_code, err_str = cvr.append_model_buffer('semi-ocr', model_data, 1)
        print("Model initialization: ErrorCode: " + str(err_code) + ", ErrorString: " + err_str)
        
        # 3.Performs capture jobs(recognizing text lines) on an image
        err_code, err_str = cvr.init_settings_from_file("semi-ocr.json")
        print("Template initialization: ErrorCode: " + str(err_code) + ", ErrorString: " + err_str)
        
        while True:
            files_list = []
            path = input(
                ">> Input your image full path:\n"
                ">> 'Enter' for sample image or 'Q'/'q' to quit\n"
            ).strip('\'"')

            if path.lower() == "q":
                sys.exit(0)

            if not os.path.exists(path):
                print("File not found: " + path)
                continue
            else:
                files_list = []

                if os.path.isfile(path):
                    files_list.append(path)
                elif os.path.isdir(path):
                    files = os.listdir(path)
                    for file in files:
                        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                            files_list.append(os.path.join(path, file))
                
                for image_path in files_list:
                    cv_image = cv2.imread(image_path)
                    
                    result = cvr.capture(image_path, "recognize_semi_ocr")
                    
                    # 4.Outputs the result.
                    if result.get_error_code() != EnumErrorCode.EC_OK:
                        print("Error: " + str(result.get_error_code())+ result.get_error_string())
                    else:
                        items = result.get_items()
                        # print(f'read {len(items)} items')
                        for item in items:
                            if isinstance(item, TextLineResultItem):
                                print(f"{RED}{item.get_text()}{RESET}")

                                location = item.get_location()
                                x1 = location.points[0].x
                                y1 = location.points[0].y
                                x2 = location.points[1].x
                                y2 = location.points[1].y
                                x3 = location.points[2].x
                                y3 = location.points[2].y
                                x4 = location.points[3].x
                                y4 = location.points[3].y

                                cv2.drawContours(
                                    cv_image, [np.intp([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)

                                cv2.putText(cv_image, item.get_text(), (x1 + 10, y1 + 20),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    
                        cv2.imshow(
                            os.path.basename(image_path), cv_image)
                        
                cv2.waitKey(0)
                cv2.destroyAllWindows()