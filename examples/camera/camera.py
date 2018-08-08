import cv2
import dbr
import time
import os

import sys
sys.path.append('../')
from license import dbr_license


def get_time():
    localtime = time.localtime()
    capturetime = time.strftime("%Y%m%d%H%M%S", localtime)
    return capturetime


def read_barcode():

    vc = cv2.VideoCapture(0)

    if vc.isOpened():  # try to get the first frame
        dbr.initLicense(dbr_license)
        rval, frame = vc.read()
    else:
        return

    windowName = "Barcode Reader"
    # 1D, PDF417, QRCODE, DataMatrix
    formats = 0x3FF | 0x2000000 | 0x4000000 | 0x8000000

    while True:
        cv2.imshow(windowName, frame)
        rval, frame = vc.read()
        results = dbr.decodeBuffer(frame, formats)
        if (len(results) > 0):
            print(get_time())
            print("Total count: " + str(len(results)))
            for result in results:
                print("Type: " + result[0])
                print("Value: " + result[1] + "\n")

        # 'ESC' for quit
        key = cv2.waitKey(20)
        if key == 27:
            dbr.destroy()
            break

    cv2.destroyWindow(windowName)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    read_barcode()
