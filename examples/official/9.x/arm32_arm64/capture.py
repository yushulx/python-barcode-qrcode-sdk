import cv2 as cv
from dbr import *

capture = cv.VideoCapture(0)

if not capture.isOpened():
    print("Cannot open camera")
    exit()

BarcodeReader.init_license(
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
reader = BarcodeReader()

index = 0

while True:
    frame = capture.read()[1]
    cv.imshow("frame", frame)

    if cv.waitKey(1) == ord('q'):
        break

    results = reader.decode_buffer(frame)
    if results != None and len(results) > 0:
        cv.imwrite('images/' + str(index) + '.png', frame)
        index += 1

    if index == 10:
        break
