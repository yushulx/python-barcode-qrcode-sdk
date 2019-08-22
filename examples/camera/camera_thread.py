import cv2
from dbr import DynamsoftBarcodeReader
dbr = DynamsoftBarcodeReader()
import time
import threading
import sys
import os

import sys
sys.path.append('../')
import config

if sys.version_info < (3, 0):
    import Queue
    q = Queue.Queue(1)
else:
    import queue
    q = queue.Queue(1)


class BarcodeReaderThread (threading.Thread):
    def __init__(self, name, isRunning):
        threading.Thread.__init__(self)
        self.name = name
        self.isRunning = isRunning

    def run(self):
        global q

        while self.isRunning:
            # Get a frame
            frame = q.get(True)
            results = dbr.decodeBuffer(frame, config.barcodeTypes)
            q.task_done()

            if (len(results) > 0):
                print(get_time())
                print("Total count: " + str(len(results)))
                for result in results:
                    print("Type: " + result[0])
                    print("Value: " + result[1] + "\n")

        print("Quit thread")


def get_time():
    localtime = time.localtime()
    capturetime = time.strftime("%Y%m%d%H%M%S", localtime)
    return capturetime


def read_barcode():
    vc = cv2.VideoCapture(0)

    if vc.isOpened():  # try to get the first frame
        dbr.initLicense(config.license)
        rval, frame = vc.read()
    else:
        return

    windowName = "Barcode Reader"

    # Create a thread for barcode detection
    barcodeReaderThread = BarcodeReaderThread("Barcode Reader Thread", True)
    barcodeReaderThread.start()

    global q
    while True:
        cv2.imshow(windowName, frame)  # Render a frame on Window
        rval, frame = vc.read()  # Get a frame

        try:
            q.put_nowait(frame)
        except Queue.Full:
            try:
                q.get_nowait()
            except Queue.Empty:
                None

        # 'ESC' for quit
        key = cv2.waitKey(20)
        if key == 27:
            barcodeReaderThread.isRunning = False
            barcodeReaderThread.join()
            break

    cv2.destroyWindow(windowName)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    read_barcode()
