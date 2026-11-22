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


def decodeframe(frame, left, top, right, bottom):
    error_code, error_msg, settings = cvr_instance.get_simplified_settings(EnumPresetTemplate.PT_READ_BARCODES.value)
    quad = Quadrilateral()
    quad.points = [Point(left, top), Point(right, top), Point(right, bottom), Point(left, bottom)]
    settings.roi = quad
    settings.roi_measured_in_percentage = False
    cvr_instance.update_settings(EnumPresetTemplate.PT_READ_BARCODES.value, settings)
    result = cvr_instance.capture(frame, EnumPresetTemplate.PT_READ_BARCODES.value)
    return result


winName = 'QR Detection'
threshold = 0.6

# Load class names and YOLOv3-tiny model
classes = open('qrcode.names').read().strip().split('\n')
net = cv.dnn.readNetFromDarknet(
    'qrcode-yolov3-tiny.cfg', 'qrcode-yolov3-tiny.weights')
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)


def processframe(frame, outs):
    results = []
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
            left, top, width, height = box

            # Decode barcode
            result = decodeframe(frame, left, top, left + width, top + height)
            items = result.get_items()

            if len(items) == 0:
                results.append((classes[classIds[i]], confidences[i], left,
                                top, left + width, top + height, "Decoding Failed"))
            else:
                results.append((classes[classIds[i]], confidences[i], left,
                                top, left + width, top + height, items[0].get_text()))

    return results


def postprocess(frame, outs):
    for out in outs:
        # Draw bounding box for objects
        cv.rectangle(frame, (out[2], out[3]), (out[4], out[5]), (0, 0, 255))

        # Draw class name and confidence
        label = '%s:%.2f' % (out[0], out[1])
        cv.putText(frame, label, (out[2], out[3] - 15),
                   cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))

        # Draw barcode results
        barcode_label = '%s' % (out[6])
        cv.putText(frame, barcode_label,
                   (out[2], out[3] - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0))


# Determine the output layer
ln = net.getLayerNames()
ln = [ln[i - 1] for i in net.getUnconnectedOutLayers().flatten()]

cap = cv.VideoCapture(0)


class QueueFPS(queue.Queue):
    def __init__(self):
        super().__init__()
        self.startTime = 0
        self.counter = 0

    def put(self, v):
        super().put(v)
        self.counter += 1
        if self.counter == 1:
            self.startTime = time.time()

    def getFPS(self):
        return self.counter / (time.time() - self.startTime) if self.counter > 1 else 0


process = True

# Frames capturing thread
framesQueue = QueueFPS()


def framesThreadBody():
    global framesQueue, process

    while process:
        hasFrame, frame = cap.read()
        if not hasFrame:
            break
        framesQueue.put(frame)


# Frames processing thread
processedFramesQueue = queue.Queue()
predictionsQueue = QueueFPS()


def processingThreadBody():
    global processedFramesQueue, predictionsQueue, process

    while process:
        # Get the next frame
        try:
            frame = framesQueue.get_nowait()
            framesQueue.queue.clear()  # Clear older frames to avoid lag
        except queue.Empty:
            continue

        if frame is not None:
            blob = cv.dnn.blobFromImage(
                frame, 1/255, (416, 416), swapRB=True, crop=False)
            processedFramesQueue.put(frame)

            # Run the model
            net.setInput(blob)
            outs = net.forward(ln)

            # Process frame and put results into the predictions queue
            results = processframe(frame, outs)
            predictionsQueue.put(results)


framesThread = Thread(target=framesThreadBody)
framesThread.start()

processingThread = Thread(target=processingThreadBody)
processingThread.start()

# Postprocessing and rendering loop
while cv.waitKey(1) < 0:
    try:
        # Retrieve the predictions and processed frame
        outs = predictionsQueue.get_nowait()
        frame = processedFramesQueue.get_nowait()

        # Process and display the results
        postprocess(frame, outs)

        # Display FPS info
        if predictionsQueue.counter > 1:
            label = 'Camera: %.2f FPS' % framesQueue.getFPS()
            cv.putText(frame, label, (0, 15),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

            label = 'Network: %.2f FPS' % predictionsQueue.getFPS()
            cv.putText(frame, label, (0, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

            label = 'Skipped frames: %d' % (
                framesQueue.counter - predictionsQueue.counter)
            cv.putText(frame, label, (0, 45),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

        cv.imshow(winName, frame)
    except queue.Empty:
        continue

# Cleanup
process = False
framesThread.join()
processingThread.join()
cap.release()
cv.destroyAllWindows()
