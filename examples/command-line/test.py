import os
import json
import cv2
import sys
sys.path.append('../../')
import barcodeQrSDK

# set license
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

# initialize barcode reader
reader = barcodeQrSDK.DynamsoftBarcodeReader()

def decodeFile(fileName):
    try:
        results = reader.decodeFile(fileName)
        for result in results:
            print("barcode format: " + result.format)
            print("barcode value: " + result.text)
    except Exception as err:
        print(err)


def decodeBuffer(image):
    results = reader.decodeMat(image)

    thickness = 2
    color = (0,255,0)
    for result in results:
        print("barcode format: " + result.format)
        print("barcode value: " + result.text)
        x1 = result.x1
        y1 = result.y1
        x2 = result.x2
        y2 = result.y2
        x3 = result.x3
        y3 = result.y3
        x4 = result.x4
        y4 = result.y4

        cv2.line(image, (x1, y1), (x2, y2), color, thickness)
        cv2.line(image, (x2, y2), (x3, y3), color, thickness)
        cv2.line(image, (x3, y3), (x4, y4), color, thickness)
        cv2.line(image, (x4, y4), (x1, y1), color, thickness)

    cv2.imshow("Localization", image)
    cv2.waitKey(0)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    import sys
    barcode_image = ""
    if sys.version_info < (3, 0):
        barcode_image = raw_input("Enter the barcode file: ")
    else:
        barcode_image = input("Enter the barcode file: ")

    if not os.path.isfile(barcode_image):
        print("It is not a valid file.")
    else:
        # Get default barcode params
        params = reader.getParameters()
        # Convert string to JSON object
        json_obj = json.loads(params)
        # Update JSON object
        # DPM
        json_obj['ImageParameter']['DPMCodeReadingModes'][0]['Mode'] = 'DPMCRM_GENERAL'
        json_obj['ImageParameter']['LocalizationModes'][0]['Mode'] = 'LM_STATISTICS_MARKS'
        # Convert JSON object to string
        params = json.dumps(json_obj)
        # Set parameters
        ret = reader.setParameters(params)
        decodeFile(barcode_image)
        image = cv2.imread(barcode_image, 1)
        decodeBuffer(image)