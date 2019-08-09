import cv2
from dbr import DynamsoftBarcodeReader
dbr = DynamsoftBarcodeReader()
import time
import os

import sys
sys.path.append('../')
import config

# The callback function for receiving barcode results
def onBarcodeResult(format, text):
    print("Type: " + format)
    print("Value: " + text + "\n")

def get_time():
    localtime = time.localtime()
    capturetime = time.strftime("%Y%m%d%H%M%S", localtime)
    return capturetime

def read_barcode():
    video_width = 640
    video_height = 480

    vc = cv2.VideoCapture(0)
    vc.set(3, video_width) #set width
    vc.set(4, video_height) #set height

    if vc.isOpened():  
        dbr.initLicense('LICENSE-KEY')
        rval, frame = vc.read()
    else:
        return

    windowName = "Barcode Reader"

    max_buffer = 2
    max_results = 10
    barcodeTypes = config.barcodeTypes
    image_format = 1 # 0: gray; 1: rgb888

    dbr.startVideoMode(max_buffer, max_results, video_width, video_height, image_format, barcodeTypes, onBarcodeResult)

    while True:
        cv2.imshow(windowName, frame)
        rval, frame = vc.read()

        # start = time.time()
        try:
            ret = dbr.appendVideoFrame(frame)
        except:
            pass

        # cost = (time.time() - start) * 1000
        # print('time cost: ' + str(cost) + ' ms')

        # 'ESC' for quit
        key = cv2.waitKey(1)
        if key == 27:
            break

    dbr.stopVideoMode()
    dbr.destroy()
    cv2.destroyWindow(windowName)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    read_barcode()
