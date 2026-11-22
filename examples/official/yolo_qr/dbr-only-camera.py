from time import sleep
import cv2 as cv
import numpy as np
import time
from threading import Thread
import queue
from dynamsoft_capture_vision_bundle import *

errorCode, errorMsg = LicenseManager.init_license(
        "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
    print("License initialization failed: ErrorCode:",
            errorCode, ", ErrorString:", errorMsg)

cvr_instance = CaptureVisionRouter()    

color = (0, 0, 255)
thickness = 2


def decodeframe(frame):

    result = cvr_instance.capture(frame, EnumPresetTemplate.PT_READ_BARCODES.value)
    return result


winName = 'QR Detection'


def postprocess(frame, result):
    items = result.get_items()
    for item in items:
        location = item.get_location()
        x1 = location.points[0].x
        y1 = location.points[0].y
        x2 = location.points[1].x
        y2 = location.points[1].y
        x3 = location.points[2].x
        y3 = location.points[2].y
        x4 = location.points[3].x
        y4 = location.points[3].y

        pts = np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], np.int32).reshape((-1, 1, 2))
        cv.drawContours(
            frame, [pts], 0, (0, 255, 0), 2)

        cv.putText(frame, item.get_text(), (x1, y1 - 10),
                    cv.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)


cap = cv.VideoCapture(0)


class QueueFPS(queue.Queue):
    def __init__(self):
        queue.Queue.__init__(self)
        self.startTime = 0
        self.counter = 0

    def put(self, item, block=True, timeout=None):
        queue.Queue.put(self, item, block=block, timeout=timeout)
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
