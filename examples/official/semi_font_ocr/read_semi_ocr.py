import os
from dynamsoft_capture_vision_bundle import *
import cv2
import numpy as np

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def process_image(image_path, cvr):
    cv_image = cv2.imread(image_path)
                    
    result = cvr.capture(image_path, "recognize_semi_ocr")
    
    if result.get_error_code() != EnumErrorCode.EC_OK:
        print("Error: " + str(result.get_error_code())+ result.get_error_string())
    else:
        items = result.get_items()
        for item in items:
            if isinstance(item, TextLineResultItem):
                print(f"{RED}{item.get_text()}{RESET}")

                location = item.get_location()
                points = [(p.x, p.y) for p in location.points]
                cv2.drawContours(cv_image, [np.intp(points)], 0, (0, 255, 0), 2)

                cv2.putText(cv_image, item.get_text(), (points[0][0] + 10, points[0][1] + 20),
        
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
        cv2.imshow(
            os.path.basename(image_path), cv_image)

def main():
    err_code, err_str = LicenseManager.init_license("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
    if err_code != EnumErrorCode.EC_OK and err_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print("License initialization failed: ErrorCode: " + str(err_code) + ", ErrorString: " + err_str)
    else:
        cvr = CaptureVisionRouter()
        with open('models/semi-ocr.data', 'rb') as f:
            model_data = f.read()
            
        err_code, err_str = cvr.append_model_buffer('semi-ocr', model_data, 1)
        print(f"{GREEN}Model initialization: ErrorCode: " + str(err_code) + ", ErrorString: " + err_str + f"{RESET}")
        
        err_code, err_str = cvr.init_settings_from_file("semi-ocr.json")
        print(f"{GREEN}Template initialization: ErrorCode: " + str(err_code) + ", ErrorString: " + err_str + f"{RESET}")

        
        while True:
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
                if os.path.isfile(path):
                    process_image(path, cvr)
                elif os.path.isdir(path):
                    files = os.listdir(path)
                    for file in files:
                        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                            process_image(os.path.join(path, file), cvr)
                        
                cv2.waitKey(0)
                cv2.destroyAllWindows()

if __name__ == '__main__':
    main()