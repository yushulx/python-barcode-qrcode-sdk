import numpy as np
import cv2 as cv

from multiprocessing.pool import ThreadPool
from collections import deque

import dbr
from dbr import *

import time

BarcodeReader.init_license("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
reader = BarcodeReader()
reader.init_runtime_settings_with_string("{\"ImageParameter\":{\"Name\":\"BestCoverage\",\"DeblurLevel\":9,\"ExpectedBarcodesCount\":512,\"ScaleDownThreshold\":100000,\"LocalizationModes\":[{\"Mode\":\"LM_CONNECTED_BLOCKS\"},{\"Mode\":\"LM_SCAN_DIRECTLY\"},{\"Mode\":\"LM_STATISTICS\"},{\"Mode\":\"LM_LINES\"},{\"Mode\":\"LM_STATISTICS_MARKS\"}],\"GrayscaleTransformationModes\":[{\"Mode\":\"GTM_ORIGINAL\"},{\"Mode\":\"GTM_INVERTED\"}]}}")

def main():
    import sys
    try:
        filename = sys.argv[1]
    except:
        filename = ''

    if filename == '':
        print('Usage: python3 barcode-reader.py <filename>')
        exit(1)

    frame = cv.imread(filename)
    results = reader.decode_buffer(frame)
    for result in results:
        points = result.localization_result.localization_points
        cv.line(frame, points[0], points[1], (0,255,0), 2)
        cv.line(frame, points[1], points[2], (0,255,0), 2)
        cv.line(frame, points[2], points[3], (0,255,0), 2)
        cv.line(frame, points[3], points[0], (0,255,0), 2)
        cv.putText(frame, result.barcode_text, points[0], cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))
    
    cv.imshow('Barcode & QR Code Reader', frame)
    cv.waitKey(0)

    cv.imwrite('output.png', frame)
    print('Saved to output.png')
    

if __name__ == '__main__':
    main()
    cv.destroyAllWindows()