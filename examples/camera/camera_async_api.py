import barcodeQrSDK
import numpy as np

# set license
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

# initialize barcode scanner
scanner = barcodeQrSDK.createInstance()

g_results = None

def callback(results):
    global g_results 
    g_results = results
    
import cv2
scanner.addAsyncListener(callback)

cap = cv2.VideoCapture(0)
while True:
    ret, image = cap.read()
    if image is not None:
        scanner.decodeMatAsync(image)
    
    if g_results != None:
        for result in g_results:
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
            
            cv2.drawContours(image, [np.int0([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)
        

    cv2.imshow('Barcode QR Code Scanner', image)
    ch = cv2.waitKey(1)
    if ch == 27:
        break



