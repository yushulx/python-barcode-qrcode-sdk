from PIL import Image # pip install Pillow
im = Image.open('qr.jpg')
# im.show()

import numpy
import dbr
import cv2

dbr.initLicense('LICENSE-LEY')

opencvImage = cv2.cvtColor(numpy.array(im), cv2.COLOR_RGB2BGR)

results = dbr.decodeBuffer(opencvImage, 0x3FF | 0x2000000 | 0x4000000 | 0x8000000 | 0x10000000) # 1D, PDF417, QRCODE, DataMatrix, Aztec Code

for result in results:

    print('barcode format: ' + result[0])
    print('barcode value: ' + result[1])
