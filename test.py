import cv2
import barcodeQrSDK
from barcodeQrSDK import *
from time import sleep

file_path = "images/test.png"
# set license
ret = barcodeQrSDK.initLicense(
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
print('initLicense: {}'.format(ret))

# initialize barcode reader
reader = barcodeQrSDK.createInstance()

# Get runtime settings
settings = reader.getParameters()
print(reader.getParameters())

# Set runtime settings
ret = reader.setParameters(settings)
print(ret)

# decodeFile()
print('decodeFile()....')
results = reader.decodeFile(file_path)
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

# decodeBytes()
print('decodeBytes()....')
image = cv2.imread(file_path)
results = reader.decodeBytes(image.tobytes(), image.shape[1], image.shape[0], image.shape[2] * image.shape[1], EnumImagePixelFormat.IPF_BGR_888)
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
print('decodeMat()....')
image = cv2.imread(file_path)
results = reader.decodeMat(image)
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
print('Test decodeMatAsync()....')

def callback(results):
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


image = cv2.imread(file_path)
reader.addAsyncListener(callback)

for i in range(2):
    print('decodeMatAsync: {}'.format(i))
    reader.decodeMatAsync(image)

    sleep(1)

reader.clearAsyncListener()

# asyncio test
import asyncio

async def async_decode_mat():
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, reader.decodeMat, image)
    print('Asyncio results:')
    for result in results:
        print(result.text)
        print(result.format)

asyncio.run(async_decode_mat())
