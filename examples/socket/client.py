import cv2 as cv
from simplesocket import SimpleSocket, DataType
import json
import barcodeQrSDK
import numpy as np

g_local_results = None
g_remote_results = None
isDisconnected = False
msgQueue = []
isReady = True

cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

if cap.isOpened() == False:
    print("Unable to read camera feed")
    exit()

def callback(results, elapsed_time):
    global g_local_results
    print("Local decoding time: " + str(elapsed_time) + " ms")
    g_local_results = (results, elapsed_time)

# Initialize Dynamsoft Barcode Reader
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
reader = barcodeQrSDK.createInstance()
print(barcodeQrSDK.__version__)
reader.addAsyncListener(callback)
    
def readCb(data_type, data):
    global isDisconnected, g_remote_results, isReady
    if data == b'':
        isDisconnected = True

    if data_type == DataType.TEXT:
        text = data.decode('utf-8')
        print(text)
        
    if data_type == DataType.JSON:
        obj = json.loads(data)
        g_remote_results = (obj['results'], obj['time'])
        isReady = True
    
# Data for sending
def writeCb():
    if len(msgQueue) > 0:
        data_type, data =  msgQueue.pop(0)
        return data_type, data
    
    return None, None
    
def run():
    global isDisconnected, g_local_results, g_remote_results, isReady
    
    client = SimpleSocket()
    client.registerEventCb((readCb, writeCb))
    client.startClient('192.168.8.72', 8080)
    
    while True:
        client.monitorEvents()
        if (isDisconnected):
                break
            
        rval, frame = cap.read()
        
        
        if frame is not None:
            # Decode the frame
            reader.decodeMatAsync(frame)
                
        # Send data to server
        if isReady:
            isReady = False
            webp = cv.imencode('.webp', frame, [cv.IMWRITE_WEBP_QUALITY, 90])[1]
            msgQueue.append((DataType.WEBP, webp.tobytes()))
                
        # Show local and remote results
        # if g_local_results != None:
        #     for result in g_local_results[0]:
        #         text = result.text
        #         x1 = result.x1
        #         y1 = result.y1
        #         x2 = result.x2
        #         y2 = result.y2
        #         x3 = result.x3
        #         y3 = result.y3
        #         x4 = result.x4
        #         y4 = result.y4
        #         cv.putText(frame, text, (x1, y1), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        #         cv.drawContours(frame, [np.int0([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)
            
        #     cv.putText(frame, "Local decoding time: " + str(g_local_results[1]) + " ms", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        if g_remote_results != None:
            print("Remote decoding time: " + str(int(g_remote_results[1])) + " ms")
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
            
            cv.putText(frame, "Remote decoding time: " + str(int(g_remote_results[1])) + " ms", (10, 60), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            
        cv.imshow('client', frame)
        if cv.waitKey(10) == 27:
            break
        
    client.shutdown()
       
if __name__ == '__main__':
    run()
        