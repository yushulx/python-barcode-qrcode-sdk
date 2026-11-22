# https://opencv-tutorial.readthedocs.io/en/latest/yolo/yolo.html
# https://docs.opencv.org/master/d6/d0f/group__dnn.html
# https://docs.opencv.org/3.4/db/d30/classcv_1_1dnn_1_1Net.html
# https://github.com/opencv/opencv/blob/master/samples/dnn/object_detection.py
import cv2 as cv
import numpy as np
import time

# Load an image
frame = cv.imread("416x416.jpg")
# frame = cv.imread("test.jpg")

threshold = 0.6
maxWidth = 1280
maxHeight = 720
imgHeight, imgWidth = frame.shape[:2]
hScale = 1
wScale = 1
thickness = 1

if imgHeight > maxHeight:
    hScale = imgHeight / maxHeight
    thickness = 6

if imgWidth > maxWidth:
    wScale = imgWidth / maxWidth
    thickness = 6

# Load class names and YOLOv3-tiny model
classes = open('qrcode.names').read().strip().split('\n')
net = cv.dnn.readNetFromDarknet(
    'qrcode-yolov3-tiny.cfg', 'qrcode-yolov3-tiny.weights')
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
# net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU) # DNN_TARGET_OPENCL DNN_TARGET_CPU DNN_TARGET_CUDA

start_time = time.monotonic()
# Convert frame to blob
blob = cv.dnn.blobFromImage(frame, 1/255, (416, 416), swapRB=True, crop=False)
elapsed_ms = (time.monotonic() - start_time) * 1000
print('blobFromImage in %.1fms' % (elapsed_ms))


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
        for i in indices.flatten():  # Flatten the indices if they are in nested format
            box = boxes[i]
            left = box[0]
            top = box[1]
            width = box[2]
            height = box[3]

            # Crop the detected object from the frame
            cropped_image = frame[top:top + height, left:left + width]
            cv.imshow('cropped', cropped_image)
            cv.imwrite('cropped.jpg', cropped_image)

            # Draw bounding box around the detected object
            cv.rectangle(frame, (left, top), (left + width,
                                              top + height), (0, 0, 255), thickness)

            # Draw class name and confidence on the bounding box
            label = '%s:%.2f' % (classes[classIds[i]], confidences[i])
            cv.putText(frame, label, (left, top),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))


# Determine the output layer
ln = net.getLayerNames()
ln = [ln[i - 1] for i in net.getUnconnectedOutLayers().flatten()]

net.setInput(blob)
start_time = time.monotonic()
# Compute
outs = net.forward(ln)
elapsed_ms = (time.monotonic() - start_time) * 1000
print('forward in %.1fms' % (elapsed_ms))

start_time = time.monotonic()
postprocess(frame, outs)
elapsed_ms = (time.monotonic() - start_time) * 1000
print('postprocess in %.1fms' % (elapsed_ms))

if hScale > wScale:
    frame = cv.resize(frame, (int(imgWidth / hScale), maxHeight))
elif hScale < wScale:
    frame = cv.resize(frame, (maxWidth, int(imgHeight / wScale)))

cv.imshow('QR Detection', frame)
cv.waitKey()
