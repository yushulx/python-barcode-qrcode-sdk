import os
import dbr
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

    for result in results:
        print("barcode format: " + result[0])
        print("barcode value: " + result[1])


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
        decodeFile(barcode_image)
        # image = cv2.imread(barcode_image, 1)
        # decodeBuffer(image)
