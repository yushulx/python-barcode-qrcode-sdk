import os
import dbr
import cv2

import sys
sys.path.append('../')
from license import dbr_license

# 1D, PDF417, QRCODE, DataMatrix
formats = 0x3FF | 0x2000000 | 0x4000000 | 0x8000000


def initLicense(license):
    dbr.initLicense(license)


def decodeFile(fileName):
    results = dbr.decodeFile(fileName, formats)

    for result in results:
        print("barcode format: " + result[0])
        print("barcode value: " + result[1])


def decodeBuffer(image):
    results = dbr.decodeBuffer(image, formats)

    for result in results:
        print("barcode format: " + result[0])
        print("barcode value: " + result[1])


if __name__ == "__main__":
    import sys
    if sys.version_info < (3, 0):
        barcode_image = raw_input("Enter the barcode file: ")
    else:
        barcode_image = input("Enter the barcode file: ")

    if not os.path.isfile(barcode_image):
        print("It is not a valid file.")
    else:
        initLicense(dbr_license)
        decodeFile(barcode_image)
        # image = cv2.imread(barcode_image, 1)
        # decodeBuffer(image)
