import os
from dynamsoft_capture_vision_bundle import *

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
        
        files_list = []
        while True:
            path = input("Please enter the image file/directory path: ").strip('\'"')
            if not os.path.exists(path):
                print("File not found: " + path)
            else:
                if os.path.isfile(path):
                    files_list.append(path)
                elif os.path.isdir(path):
                    files =os.listdir(path)
                    for file in files:
                        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                            files_list.append(os.path.join(path, file))
                break
            
        for file_path in files_list:
            result=cvr.capture(file_path, "recognize_semi_ocr")

            print("File: " + file_path)
            
            # 4.Outputs the result.
            if result.get_error_code() != EnumErrorCode.EC_OK:
                print("Error: " + str(result.get_error_code())+ result.get_error_string())
            else:
                items = result.get_items()
                # print(f'read {len(items)} items')
                for item in items:
                    if isinstance(item, TextLineResultItem):
                        print(item.get_text())