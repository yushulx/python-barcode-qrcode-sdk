import os
import json
import cv2
import sys
import barcodeQrSDK
import time
import numpy as np
# set license
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

# initialize barcode reader
reader = barcodeQrSDK.createInstance()

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
        rval, frame = vc.read()
    else:
        return

    windowName = "Barcode Reader"

    max_buffer = 2
    max_results = 10
    image_format = 1 # 0: gray; 1: rgb888

    reader.startVideoMode(max_buffer, max_results, video_width, video_height, image_format, onBarcodeResult)

    while True:
        if results != None:
            thickness = 2
            color = (0,255,0)
            for result in results:
                print("barcode format: " + result.format)
                print("barcode value: " + result.text)
                x1 = result.x1
                y1 = result.y1
                x2 = result.x2
                y2 = result.y2
                x3 = result.x3
                y3 = result.y3
                x4 = result.x4
                y4 = result.y4

                cv2.drawContours(frame, [np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)

            results = None

        cv2.imshow(windowName, frame)
        rval, frame = vc.read()

        # start = time.time()
        try:
            ret = reader.appendVideoFrame(frame)
        except:
            pass

        # cost = (time.time() - start) * 1000
        # print('time cost: ' + str(cost) + ' ms')

        # 'ESC' for quit
        key = cv2.waitKey(1)
        if key == 27:
            break

    reader.stopVideoMode()
    cv2.destroyWindow(windowName)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    read_barcode()
