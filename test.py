import barcodeQrSDK

barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

reader = barcodeQrSDK.DynamsoftBarcodeReader()
results = reader.decodeFile("test.png")
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