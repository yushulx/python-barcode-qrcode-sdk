import cv2 as cv
from simplesocket import SimpleSocket, DataType
import json
import barcodeQrSDK
import time
import numpy as np

g_local_results = None
g_remote_results = None
isLocalAvailable = True
isDisconnected = False
msgQueue = []

cap = cv.VideoCapture(0)
if cap.isOpened() == False:
    print("Unable to read camera feed")
    exit()

def callback(results, elapsed_time):
    global g_local_results, isLocalAvailable
    g_local_results = (results, elapsed_time)
    isLocalAvailable = True

# Initialize Dynamsoft Barcode Reader
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
reader = barcodeQrSDK.createInstance()
print(barcodeQrSDK.__version__)
reader.addAsyncListener(callback)
    
def readCb(data_type, data):
    global isDisconnected, g_remote_results
    if data == b'':
        isDisconnected = True

    if data_type == DataType.TEXT:
        text = data.decode('utf-8')
        print(text)
        
    if data_type == DataType.JSON:
        obj = json.loads(data)
        g_remote_results = (obj['results'], obj['time'])
    
# Data for sending
def writeCb():
    global isDisconnected, g_local_results, isLocalAvailable, g_remote_results
    if cap.isOpened():
        rval, frame = cap.read()
        webp = cv.imencode('.webp', frame, [cv.IMWRITE_WEBP_QUALITY, 90])[1]
        
        if frame is not None:
            if isLocalAvailable:
                isLocalAvailable = False
                reader.decodeMatAsync(frame)
                
        if g_local_results != None:
            for result in g_local_results[0]:
                text = result.text
                x1 = result.x1
                y1 = result.y1
                x2 = result.x2
                y2 = result.y2
                x3 = result.x3
                y3 = result.y3
                x4 = result.x4
                y4 = result.y4
                cv.putText(frame, text, (x1, y1), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv.drawContours(frame, [np.int0([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)
            
            cv.putText(frame, "Elapsed time: " + str(g_local_results[1]) + " ms", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        if g_remote_results != None:
            for result in g_remote_results[0]:
                text = result['text']
                x1 = result['x1']
                y1 = result['y1']
                x2 = result['x2']
                y2 = result['y2']
                x3 = result['x3']
                y3 = result['y3']
                x4 = result['x4']
                y4 = result['y4']
                cv.putText(frame, text, (x1, y1), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv.drawContours(frame, [np.int0([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)
            
            cv.putText(frame, "Remote Elapsed time: " + str(int(g_remote_results[1])) + " ms", (10, 60), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
        cv.imshow('client', frame)
        if cv.waitKey(10) == 27:
            isDisconnected = True
        
        frametime = int(time.time()).to_bytes(4, 'big')
                
        return DataType.WEBP, frametime + webp.tobytes()
    
    return None, None
    
def run():
    global isDisconnected
    
    client = SimpleSocket()
    client.registerEventCb((readCb, writeCb))
    client.startClient('localhost', 80)
    
    while True:
        client.monitorEvents()
        if (isDisconnected):
                break
    
    client.shutdown()
       
if __name__ == '__main__':
    run()
        