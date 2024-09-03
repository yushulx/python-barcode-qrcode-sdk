import cv2 as cv
import numpy as np
import time
from dbr import *

license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
BarcodeReader.init_license(license_key)
reader = BarcodeReader()
color = (0, 0, 255)
thickness = 2


def decodeframe(frame):

    try:
        text_results = reader.decode_buffer(frame)

        if text_results != None:
            for text_result in text_results:
                print("Barcode Format :")
                print(text_result.barcode_format_string)
                print("Barcode Text :")
                print(text_result.barcode_text)
                print("Localization Points : ")
                print(text_result.localization_result.localization_points)
                print("-------------")
                points = text_result.localization_result.localization_points

                cv.line(frame, points[0], points[1], color, thickness)
                cv.line(frame, points[1], points[2], color, thickness)
                cv.line(frame, points[2], points[3], color, thickness)
                cv.line(frame, points[3], points[0], color, thickness)

                cv.putText(frame, text_result.barcode_text, (min([point[0] for point in points]), min(
                    [point[1] for point in points])), cv.FONT_HERSHEY_SIMPLEX, 1, color, thickness)
    except BarcodeReaderError as bre:
        print(bre)


# Load an frame
frame = cv.imread("416x416.jpg")
decodeframe(frame)

cv.imshow('QR Detection', frame)
cv.waitKey()
