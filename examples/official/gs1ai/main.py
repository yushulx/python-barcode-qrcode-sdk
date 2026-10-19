import sys
from dynamsoft_capture_vision_bundle import *
import os
import json
import cv2
import numpy as np

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
        cvr_instance.init_settings_from_file('GS1AI_Scanner.json')
        while (True):
            image_path = input(
                ">> Input your image full path:\n"
                ">> 'Enter' for sample image or 'Q'/'q' to quit\n"
            ).strip('\'"')

            if image_path.lower() == "q":
                sys.exit(0)

            if not os.path.exists(image_path):
                print("The image path does not exist.")
                continue
                
            cv_image = cv2.imread(image_path)
            result = cvr_instance.capture(
                cv_image, "ReadGS1AIBarcode")
            if result.get_error_code() != EnumErrorCode.EC_OK:
                print("Error:", result.get_error_code(),
                      result.get_error_string())
            else:
                items = result.get_items()
                for item in items:
                    if item.get_type() == EnumCapturedResultItemType.CRIT_BARCODE:
                        format_type = item.get_format_string()
                        text_bytes = item.get_bytes()
                        text = text_bytes.decode('utf-8')
                        print('Barcode text: {} '.format(text))
                        print('Barcode format: {} '.format(format_type))

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

                        cv2.putText(cv_image, text, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    
                    elif item.get_type() == EnumCapturedResultItemType.CRIT_PARSED_RESULT:
                        try:
                            json_string = item.get_json_string()
                            data = json.loads(item.get_json_string())
                            output_lines = []
                            for item in data.get("ResultInfo", []):
                                ai = item.get("FieldName", "")
                                description = ""
                                value = ""

                                child_fields = item.get("ChildFields", [[]])[0]
                                for field in child_fields:
                                    if field["FieldName"].endswith("AI"):
                                        ai = field.get("RawValue", ai)
                                        description = field.get("Value", "")
                                    elif field["FieldName"].endswith("Data"):
                                        value = field.get("Value", "")

                                output_lines.append(f"AI: {ai}")
                                output_lines.append(f"Description: {description.upper()}")
                                output_lines.append(f"Value: {value}")
                                output_lines.append("-" * 40)

                            "\n".join(output_lines)

                            print("\n".join(output_lines))
                        except json.JSONDecodeError as e:
                            print("JSON Decode Error:", e)
                            continue
            cv2.imshow(
                "Original Image with Detected Barcodes", cv_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    input("Press Enter to quit...")
