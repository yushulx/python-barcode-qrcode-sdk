import os
import sys
package_path = os.path.dirname(__file__) + '/../../'
print(package_path)
sys.path.append(package_path)
import barcodeQrSDK
from barcodeQrSDK import *
import numpy as np
import cv2
import json

g_results = None

def callback(results):
    global g_results
    g_results = results

def run():
    # set license
    barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

    # initialize barcode scanner
    scanner = barcodeQrSDK.createInstance()
    
    scanner.addAsyncListener(callback)

    cap = cv2.VideoCapture(0)
    while True:
        ret, image = cap.read()
        if image is not None:
            # scanner.decodeMatAsync(image)
            
            scanner.decodeBytesAsync(image.tobytes(), image.shape[1], image.shape[0], image.strides[0], EnumImagePixelFormat.IPF_BGR_888)
        
            
        if g_results != None:
            for result in g_results:
                x1 = result.x1
                y1 = result.y1
                x2 = result.x2
                y2 = result.y2
                x3 = result.x3
                y3 = result.y3
                x4 = result.x4
                y4 = result.y4
                
                cv2.drawContours(image, [np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], dtype=np.int32)], 0, (0, 255, 0), 2)
                cv2.putText(image, result.text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Barcode QR Code Scanner', image)
        ch = cv2.waitKey(1)
        if ch == 27:
            break
    
    scanner.clearAsyncListener()

if __name__ == '__main__':
    run()