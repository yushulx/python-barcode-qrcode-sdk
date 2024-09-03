from time import sleep
import cv2 as cv
import numpy as np
import time
from threading import Thread
import queue
from dbr import *

license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
BarcodeReader.init_license(license_key)
reader = BarcodeReader()
color = (0, 0, 255)
thickness = 2


def decodeframe(frame):

    try:
        outs = reader.decode_buffer(frame)
        if outs != None:
            return outs
    except BarcodeReaderError as bre:
        print(bre)

    return None


winName = 'QR Detection'


def postprocess(frame, outs):
    if outs == None:
        return

    for out in outs:
        points = out.localization_result.localization_points

        cv.line(frame, points[0], points[1], color, thickness)
        cv.line(frame, points[1], points[2], color, thickness)
        cv.line(frame, points[2], points[3], color, thickness)
        cv.line(frame, points[3], points[0], color, thickness)
        cv.putText(frame, out.barcode_text, (min([point[0] for point in points]), min(
            [point[1] for point in points])), cv.FONT_HERSHEY_SIMPLEX, 1, color, thickness)


cap = cv.VideoCapture(0)


class QueueFPS(queue.Queue):
    def __init__(self):
        queue.Queue.__init__(self)
        self.startTime = 0
        self.counter = 0

    def put(self, v):
        queue.Queue.put(self, v)
        self.counter += 1
        if self.counter == 1:
            self.startTime = time.time()

    def getFPS(self):
        return self.counter / (time.time() - self.startTime)


process = True

#
# Frames capturing thread
#
framesQueue = QueueFPS()


def framesThreadBody():
    global framesQueue, process

    while process:
        hasFrame, frame = cap.read()
        if not hasFrame:
            break
        framesQueue.put(frame)


#
# Frames processing thread
#
decodingQueue = QueueFPS()


def processingThreadBody():
    global decodingQueue, process

    while process:
        # Get a next frame
        frame = None
        try:
            frame = framesQueue.get_nowait()
            framesQueue.queue.clear()
        except queue.Empty:
            pass

        if not frame is None:
            outs = decodeframe(frame)
            decodingQueue.put((frame, outs))
            sleep(0.03)


framesThread = Thread(target=framesThreadBody)
framesThread.start()

processingThread = Thread(target=processingThreadBody)
processingThread.start()

#
# Postprocessing and rendering loop
#
while cv.waitKey(1) < 0:
    try:
        # Request prediction first because they put after frames
        outs = decodingQueue.get_nowait()
        frame = outs[0]
        postprocess(frame, outs[1])

        # Put efficiency information.
        if decodingQueue.counter > 1:
            label = 'Camera: %.2f FPS' % (framesQueue.getFPS())
            cv.putText(frame, label, (0, 15),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

            label = 'DBR SDK: %.2f FPS' % (decodingQueue.getFPS())
            cv.putText(frame, label, (0, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

            label = 'Skipped frames: %d' % (
                framesQueue.counter - decodingQueue.counter)
            cv.putText(frame, label, (0, 45),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

        cv.imshow(winName, frame)
    except queue.Empty:
        pass


process = False
framesThread.join()
processingThread.join()
