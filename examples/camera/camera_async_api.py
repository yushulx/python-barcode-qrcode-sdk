import barcodeQrSDK
import numpy as np
import cv2
import json

g_results = None

def callback(results, elapsed_time):
    global g_results
    g_results = (results, elapsed_time)

def run():
    # set license
    barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

    # initialize barcode scanner
    scanner = barcodeQrSDK.createInstance()
    params = scanner.getParameters()
    # Convert string to JSON object
    json_obj = json.loads(params)
    # json_obj['ImageParameter']['ExpectedBarcodesCount'] = 999
    params = json.dumps(json_obj)
    ret = scanner.setParameters(params)
    
    scanner.addAsyncListener(callback)

    cap = cv2.VideoCapture(0)
    while True:
        ret, image = cap.read()
        if image is not None:
            # scanner.decodeMatAsync(image)
            
            scanner.decodeBytesAsync(image.tobytes(), image.shape[1], image.shape[0], image.strides[0], barcodeQrSDK.ImagePixelFormat.IPF_BGR_888)
            
            # results, elapsed_time = scanner.decodeBytes(image.tobytes(), image.shape[1], image.shape[0], image.strides[0], barcodeQrSDK.ImagePixelFormat.IPF_BGR_888)
            # g_results = (results, elapsed_time)
            
        if g_results != None:
            print('Elapsed time: ' + str(g_results[1]) + 'ms')
            cv2.putText(image, 'Elapsed time: ' + str(g_results[1]) + 'ms', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            for result in g_results[0]:
                x1 = result.x1
                y1 = result.y1
                x2 = result.x2
                y2 = result.y2
                x3 = result.x3
                y3 = result.y3
                x4 = result.x4
                y4 = result.y4
                
                cv2.drawContours(image, [np.int0([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)
                cv2.putText(image, result.text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Barcode QR Code Scanner', image)
        ch = cv2.waitKey(1)
        if ch == 27:
            break
    
    scanner.clearAsyncListener()

if __name__ == '__main__':
    run()