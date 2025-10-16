import os
import json
import sys
package_path = os.path.dirname(__file__) + '/../../'
print(package_path)
sys.path.append(package_path)
import barcodeQrSDK
from barcodeQrSDK import *
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
        results = reader.decodeBytes(im.tobytes(), im.width, im.height, im.width * 3, EnumImagePixelFormat.IPF_BGR_888)
        for result in results:
            print("barcode format: " + result.format)
            print("barcode value: " + result.text)
    except Exception as err:
        print(err)
    