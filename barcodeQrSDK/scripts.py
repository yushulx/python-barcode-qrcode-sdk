import argparse
import barcodeQrSDK
import sys
import numpy as np

def scanbarcode():
    """
    Command-line script for reading barcode and QR code from a given image
    """
    parser = argparse.ArgumentParser(description='Read barcode and QR code from a given image')
    parser.add_argument('filename')
    parser.add_argument('-u', '--ui', default=False, type=bool, help='Whether to show the image')
    parser.add_argument('-l', '--license', default='', type=str, help='Set a valid license key')
    args = parser.parse_args()
    # print(args)
    try:
        filename = args.filename
        license = args.license
        ui = args.ui
        
        # set license
        if  license == '':
            barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
        else:
            barcodeQrSDK.initLicense(license)
            
        # initialize barcode reader
        reader = barcodeQrSDK.createInstance()
        
        if ui:
            import cv2
            image = cv2.imread(filename)
            results = reader.decodeMat(image)
            for result in results:
                print("Format: " + result.format)
                print("Text: " + result.text)
                
                x1 = result.x1
                y1 = result.y1
                x2 = result.x2
                y2 = result.y2
                x3 = result.x3
                y3 = result.y3
                x4 = result.x4
                y4 = result.y4
                
                cv2.drawContours(image, [np.int0([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])], 0, (0, 255, 0), 2)
                cv2.putText(image, result.text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 2)
            
            cv2.imshow("Scan Barcode & QR Code", image)
            cv2.waitKey(0)
        else:
            results = reader.decodeFile(filename)
            for result in results:
                print("Format:" + result.format)
                print("Text: " + result.text)
                
            
    except Exception as err:
        print(err)
        sys.exit(1)
