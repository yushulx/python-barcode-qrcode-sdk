import cv2
import barcodeQrSDK
import time
import numpy as np
from multiprocessing.pool import ThreadPool
from collections import deque

# set license
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

# initialize barcode reader
reader = barcodeQrSDK.createInstance()

def process_frame(frame):
    try:
        results, elapsed_time = reader.decodeMat(frame)
    except Exception as e:
        print(e)
        return (None, 0)
    
    return results, elapsed_time

def get_time():
    localtime = time.localtime()
    capturetime = time.strftime("%Y%m%d%H%M%S", localtime)
    return capturetime


def read_barcode():

    vc = cv2.VideoCapture(0)

    if not vc.isOpened(): 
        return 
    
    threadn = 1 # cv2.getNumberOfCPUs()
    pool = ThreadPool(processes = threadn)
    barcodeTasks = deque()

    windowName = "Barcode Reader"

    while True:
        rval, frame = vc.read()
        while len(barcodeTasks) > 0 and barcodeTasks[0].ready():
            results, elapsed_time = barcodeTasks.popleft().get()
            if results != None:
                cv2.putText(frame, 'Elapsed time: ' + str(elapsed_time) + 'ms', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                for result in results:
                    print("Type: " + result.format)
                    print("Value: " + result.text + "\n")
                    x1 = result.x1
                    y1 = result.y1
                    x2 = result.x2
                    y2 = result.y2
                    x3 = result.x3
                    y3 = result.y3
                    x4 = result.x4
                    y4 = result.y4
                    cv2.putText(frame, result.text, (x1 + 10, y1 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))
                    cv2.drawContours(frame, [np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)

        if len(barcodeTasks) < threadn:
            task = pool.apply_async(process_frame, (frame.copy(), ))
            barcodeTasks.append(task)

        cv2.imshow(windowName, frame)
        # 'ESC' for quit
        key = cv2.waitKey(1)
        if key == 27:
            break

    cv2.destroyWindow(windowName)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    read_barcode()