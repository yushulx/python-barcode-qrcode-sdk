import cv2
from dynamsoft_capture_vision_bundle import *
import numpy as np
capture = cv2.VideoCapture(0)

if not capture.isOpened():
    print("Cannot open camera")
    exit()

error_code, error_message = LicenseManager.init_license(
        "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
    print("License initialization failed: ErrorCode:",
            error_code, ", ErrorString:", error_message)
else:
    cvr_instance = CaptureVisionRouter()
    index = 0
    while True:
        ret, frame = capture.read()

        if cv2.waitKey(1) == ord('q'):
            break

        result = cvr_instance.capture(
                frame, EnumPresetTemplate.PT_READ_BARCODES.value)
        
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

                pts = np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.drawContours(frame, [pts], 0, (0, 255, 0), 2)

                cv2.putText(frame, text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            cv2.imshow(
                "Original Image with Detected Barcodes", frame)

    cv2.destroyAllWindows()
