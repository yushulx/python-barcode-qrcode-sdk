import os
import json
import sys
import barcodeQrSDK
import io
from PIL import Image

# set license
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

# initialize barcode reader
reader = barcodeQrSDK.createInstance()

with Image.open("test.png") as im:
    # im.show()
    # print(dir(im))

    try:
        results, elapsed_time = reader.decodeBytes(im.tobytes(), im.width, im.height, im.width * 3, barcodeQrSDK.ImagePixelFormat.IPF_RGB_888)
        for result in results:
            print("barcode format: " + result.format)
            print("barcode value: " + result.text)
    except Exception as err:
        print(err)
    