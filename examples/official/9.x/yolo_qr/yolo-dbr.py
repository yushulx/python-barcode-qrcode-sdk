import cv2 as cv
import numpy as np
import time
from dbr import *

license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
BarcodeReader.init_license(license_key)
reader = BarcodeReader()


def decodeframe(frame, left, top, right, bottom):
    settings = reader.reset_runtime_settings()
    settings = reader.get_runtime_settings()
    settings.region_bottom = bottom
    settings.region_left = left
    settings.region_right = right
    settings.region_top = top
    settings.barcode_format_ids = EnumBarcodeFormat.BF_QR_CODE
    settings.expected_barcodes_count = 1
    reader.update_runtime_settings(settings)

    try:
        text_results = reader.decode_buffer(frame)

        if text_results != None:
            return text_results[0]
            # for text_result in text_results:
            #     print("Barcode Format :")
            #     print(text_result.barcode_format_string)
            #     print("Barcode Text :")
            #     print(text_result.barcode_text)
            #     print("Localization Points : ")
            #     print(text_result.localization_result.localization_points)
            #     print("-------------")
    except BarcodeReaderError as bre:
        print(bre)

    return None


# Load an image
frame = cv.imread("416x416.jpg")

threshold = 0.6

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
            cv.putText(frame, label, (left, top - 15),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0))

            result = decodeframe(frame, left, top, left + width, top + height)
            # Draw barcode results
            if not result is None:
                label = '%s' % (result.barcode_text)
                cv.putText(frame, label, (left, top - 5),
                           cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0))


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

cv.imshow('QR Detection', frame)
cv.waitKey()
