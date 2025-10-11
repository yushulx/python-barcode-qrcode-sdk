import cv2 as cv
import numpy as np
import time
from dynamsoft_capture_vision_bundle import *

errorCode, errorMsg = LicenseManager.init_license(
        "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
    print("License initialization failed: ErrorCode:",
            errorCode, ", ErrorString:", errorMsg)

cvr_instance = CaptureVisionRouter() 
color = (0, 0, 255)
thickness = 2


def decodeframe(frame):

    result = cvr_instance.capture(frame, EnumPresetTemplate.PT_READ_BARCODES.value)
    items = result.get_items()
    for item in items:
        location = item.get_location()
        x1 = location.points[0].x
        y1 = location.points[0].y
        x2 = location.points[1].x
        y2 = location.points[1].y
        x3 = location.points[2].x
        y3 = location.points[2].y
        x4 = location.points[3].x
        y4 = location.points[3].y

        pts = np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], np.int32).reshape((-1, 1, 2))
        cv.drawContours(
            frame, [pts], 0, (0, 255, 0), 2)

        cv.putText(frame, item.get_text(), (x1, y1 - 10),
                    cv.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)


# Load an frame
frame = cv.imread("416x416.jpg")
decodeframe(frame)

cv.imshow('QR Detection', frame)
cv.waitKey()
