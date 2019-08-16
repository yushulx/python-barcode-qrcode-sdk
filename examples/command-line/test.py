import os
import json
from dbr import DynamsoftBarcodeReader
dbr = DynamsoftBarcodeReader()
# print(dir(dbr))

import cv2

import sys
sys.path.append('../')
import config

def initLicense(license):
    dbr.initLicense(license)


def decodeFile(fileName):
    results = dbr.decodeFile(fileName, config.barcodeTypes)

    for result in results:
        print("barcode format: " + result[0])
        print("barcode value: " + result[1])


def decodeBuffer(image):
    results = dbr.decodeBuffer(image, config.barcodeTypes)

    thickness = 2
    color = (0,255,0)
    for result in results:
        print("barcode format: " + result[0])
        print("barcode value: " + result[1])
        x1 = result[2]
        y1 = result[3]
        x2 = result[4]
        y2 = result[5]
        x3 = result[6]
        y3 = result[7]
        x4 = result[8]
        y4 = result[9]

        cv2.line(image, (x1, y1), (x2, y2), color, thickness)
        cv2.line(image, (x2, y2), (x3, y3), color, thickness)
        cv2.line(image, (x3, y3), (x4, y4), color, thickness)
        cv2.line(image, (x4, y4), (x1, y1), color, thickness)

    cv2.imshow("Localization", image)
    cv2.waitKey(0)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    import sys
    if sys.version_info < (3, 0):
        barcode_image = raw_input("Enter the barcode file: ")
    else:
        barcode_image = input("Enter the barcode file: ")

    if not os.path.isfile(barcode_image):
        print("It is not a valid file.")
    else:
        initLicense(config.license)
        ##### Set dbr parameters
        # settings = {}
        # params = json.dumps(settings)
        # ret = dbr.setParameters(params)
        # dbr.setFurtherModes(dbr.GRAY_SCALE_TRANSFORMATION_MODE, [dbr.GTM_INVERTED, dbr.GTM_ORIGINAL])
        decodeFile(barcode_image)
        image = cv2.imread(barcode_image, 1)
        decodeBuffer(image)
