import cv2 as cv
import numpy as np
from simplesocket import SimpleSocket, DataType
import json
import os
import sys

package_path = os.path.join(os.path.dirname(__file__), '../../')
sys.path.append(package_path)
import barcodeQrSDK

g_results = None
isDisconnected = False
msgQueue = []

# def callback(results, elpased_time):
#     global g_results
#     g_results = (results, elpased_time)
    
# Initialize Dynamsoft Barcode Reader
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
reader = barcodeQrSDK.createInstance()
print(barcodeQrSDK.__version__)
# reader.addAsyncListener(callback)
   
# Process received data     
def readCb(data_type, data):
    global isDisconnected, g_results
    
    if data == b'':
        isDisconnected = True

    if data_type == DataType.TEXT:
        text = data.decode('utf-8')
        print(text)
        
    if data_type == DataType.JSON:
        obj = json.loads(data)
        print(obj)
            

    if data_type == DataType.WEBP:
        try:
            frame = cv.imdecode(np.frombuffer(data, np.uint8), cv.IMREAD_COLOR)
            
            if frame is not None:
                results = reader.decodeMat(frame)
                g_results = results
                
            if g_results != None:
                jsonData = {'results': []}
                for result in g_results:
                    format = result.format
                    text = result.text
                    x1 = result.x1
                    y1 = result.y1
                    x2 = result.x2
                    y2 = result.y2
                    x3 = result.x3
                    y3 = result.y3
                    x4 = result.x4
                    y4 = result.y4
                    data = {'format': format, 'text': text, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'x3': x3, 'y3': y3, 'x4': x4, 'y4': y4}
                    jsonData['results'].append(data)
                    
                    # cv.putText(frame, text, (x1, y1), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    # cv.drawContours(frame, [np.int0([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)
                
                msgQueue.append((DataType.JSON, json.dumps(jsonData).encode('utf-8')))
                    
            # cv.imshow('server', frame)
            # if cv.waitKey(10) == 27:
            #     isDisconnected = True
        except Exception as e:
            isDisconnected = True
            print(e)
    
# Data for sending
def writeCb():
    if len(msgQueue) > 0:
        data_type, data =  msgQueue.pop(0)
        return data_type, data
    
    return None, None
    
def run():
    global g_results, startTime, isAvailable, isDisconnected
    
    server = SimpleSocket()
    server.registerEventCb((readCb, writeCb))
    server.startServer(8080, 1)
    
    try:
        while True:
            server.monitorEvents()
            if (isDisconnected):
                break
    
    except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
    finally:
        server.shutdown()
    
if __name__ == '__main__':
    run()
    
    
    