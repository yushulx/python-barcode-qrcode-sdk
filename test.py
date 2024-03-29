import barcodeQrSDK
from time import sleep

# set license
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

# initialize barcode reader
reader = barcodeQrSDK.createInstance()

# Get runtime settings
settings = reader.getParameters()
print(reader.getParameters())

# Set runtime settings
ret = reader.setParameters(settings)
print(ret)

# decodeFile()
results, elapsed_time = reader.decodeFile("test.png")
print('Elapsed time: ' + str(elapsed_time) + 'ms')
for result in results:
    print(result.format)
    print(result.text)
    print(result.x1)
    print(result.y1)
    print(result.x2)
    print(result.y2)
    print(result.x3)
    print(result.y3)
    print(result.x4)
    print(result.y4)

# decodeMat()
import cv2
image = cv2.imread("test.png")
results, elapsed_time = reader.decodeMat(image)
print('Elapsed time: ' + str(elapsed_time) + 'ms')
for result in results:
    print(result.format)
    print(result.text)
    print(result.x1)
    print(result.y1)
    print(result.x2)
    print(result.y2)
    print(result.x3)
    print(result.y3)
    print(result.x4)
    print(result.y4)

# decodeMatAsync()
print('')
print('Test decodeMatAsync()')
def callback(results, elapsed_time):
    print('Elapsed time: ' + str(elapsed_time) + 'ms')
    for result in results:
        print(result.format)
        print(result.text)
        print(result.x1)
        print(result.y1)
        print(result.x2)
        print(result.y2)
        print(result.x3)
        print(result.y3)
        print(result.x4)
        print(result.y4)
    
import cv2
image = cv2.imread("test.png")
reader.addAsyncListener(callback)
reader.decodeMatAsync(image)
sleep(1)