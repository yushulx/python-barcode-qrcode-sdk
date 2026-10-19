# https://opencv-tutorial.readthedocs.io/en/latest/yolo/yolo.html
# https://docs.opencv.org/master/d6/d0f/group__dnn.html
# https://docs.opencv.org/3.4/db/d30/classcv_1_1dnn_1_1Net.html
# https://github.com/opencv/opencv/blob/master/samples/dnn/object_detection.py
import cv2 as cv
import numpy as np
import time
from threading import Thread
import queue

winName = 'QR Detection'

threshold = 0.6

# Load class names and YOLOv3-tiny model
classes = open('qrcode.names').read().strip().split('\n')
net = cv.dnn.readNetFromDarknet(
    'qrcode-yolov3-tiny.cfg', 'qrcode-yolov3-tiny.weights')
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
# net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU) # DNN_TARGET_OPENCL DNN_TARGET_CPU


def postprocess(frame, outs):
    frameHeight, frameWidth = frame.shape[:2]

    classIds = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > threshold:
                x, y, width, height = detection[:4] * np.array(
                    [frameWidth, frameHeight, frameWidth, frameHeight])
                left = int(x - width / 2)
                top = int(y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, int(width), int(height)])

    indices = cv.dnn.NMSBoxes(boxes, confidences, threshold, threshold - 0.1)
    if not isinstance(indices, tuple):
        for i in indices.flatten():
            box = boxes[i]
            left = box[0]
            top = box[1]
            width = box[2]
            height = box[3]

            # Draw bounding box for objects
            cv.rectangle(frame, (left, top),
                         (left + width, top + height), (0, 0, 255))

            # Draw class name and confidence
            label = '%s:%.2f' % (classes[classIds[i]], confidences[i])
            cv.putText(frame, label, (left, top),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))


# Determine the output layer
ln = net.getLayerNames()
ln = [ln[i - 1] for i in net.getUnconnectedOutLayers().flatten()]


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
processedFramesQueue = queue.Queue()
predictionsQueue = QueueFPS()


def processingThreadBody():
    global processedFramesQueue, predictionsQueue, process

    while process:
        # Get a next frame
        frame = None
        try:
            frame = framesQueue.get_nowait()
            framesQueue.queue.clear()
        except queue.Empty:
            continue

        if frame is not None:
            blob = cv.dnn.blobFromImage(
                frame, 1/255, (416, 416), swapRB=True, crop=False)
            processedFramesQueue.put(frame)

            # Run a model
            net.setInput(blob)
            # Compute
            outs = net.forward(ln)
            predictionsQueue.put(outs)


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
        outs = predictionsQueue.get_nowait()
        frame = processedFramesQueue.get_nowait()

        postprocess(frame, outs)

        # Put efficiency information.
        if predictionsQueue.counter > 1:
            label = 'Camera: %.2f FPS' % (framesQueue.getFPS())
            cv.putText(frame, label, (0, 15),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

            label = 'Network: %.2f FPS' % (predictionsQueue.getFPS())
            cv.putText(frame, label, (0, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

            label = 'Skipped frames: %d' % (
                framesQueue.counter - predictionsQueue.counter)
            cv.putText(frame, label, (0, 45),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

        cv.imshow(winName, frame)
    except queue.Empty:
        pass


process = False
framesThread.join()
processingThread.join()
