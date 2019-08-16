import cv2
from dbr import DynamsoftBarcodeReader
dbr = DynamsoftBarcodeReader()
import time
import os

import sys
sys.path.append('../')
import config

results = None
# The callback function for receiving barcode results
def onBarcodeResult(data):
    global results
    results = data

def get_time():
    localtime = time.localtime()
    capturetime = time.strftime("%Y%m%d%H%M%S", localtime)
    return capturetime

def read_barcode():
    global results
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
        if results != None:
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

                cv2.line(frame, (x1, y1), (x2, y2), color, thickness)
                cv2.line(frame, (x2, y2), (x3, y3), color, thickness)
                cv2.line(frame, (x3, y3), (x4, y4), color, thickness)
                cv2.line(frame, (x4, y4), (x1, y1), color, thickness)

            results = None

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
    cv2.destroyWindow(windowName)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    read_barcode()
