import os
import json
from dbr import DynamsoftBarcodeReader
dbr = DynamsoftBarcodeReader()
# print(dir(dbr))

import cv2

import sys
sys.path.append('../')
import config

def initLicense(license):
    dbr.initLicense(license)


def decodeFile(fileName, templateName = ""):
    try:
        results = dbr.decodeFile(fileName, dbr.BF_ONED | dbr.BF_PDF417 | dbr.BF_QR_CODE | dbr.BF_DATAMATRIX | dbr.BF_AZTEC, templateName, "utf8")
        for result in results:
            print("barcode format: " + result[0])
            print("barcode value: " + result[1])
    except Exception as err:
        print(err)


def decodeBuffer(image, templateName = ""):
    results = dbr.decodeBuffer(image, dbr.BF_ALL, templateName)

    thickness = 2
    color = (0,255,0)
    for result in results:
        print("barcode format: " + result[0])
        print("barcode value: " + result[1])
        x1 = result[2]
        y1 = result[3]
        x2 = result[4]
        y2 = result[5]
        x3 = result[6]
        y3 = result[7]
        x4 = result[8]
        y4 = result[9]

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
        initLicense(config.license)        
        # Get default barcode params
        params = dbr.getParameters()
        # Convert string to JSON object
        json_obj = json.loads(params)
        # Update JSON object
        templateName = json_obj['ImageParameter']['Name']
        # DPM
        json_obj['ImageParameter']['DPMCodeReadingModes'][0]['Mode'] = 'DPMCRM_GENERAL'
        json_obj['ImageParameter']['LocalizationModes'][0]['Mode'] = 'LM_STATISTICS_MARKS'
        # Convert JSON object to string
        params = json.dumps(json_obj)
        # Set parameters
        ret = dbr.setParameters(params)
        
        ##### Set dbr parameters
        # with open('template.json', 'r') as file:
        #     params = file.read().replace('\n', '')
        # templateName = "dbr"
        # settings = {"ImageParameter": {"name": templateName,"IntermediateResultSavingMode":{"Mode":"IRSM_BOTH","FolderPath":"d:\\"}, "TerminatePhase" : "TP_BARCODE_RECOGNIZED", "IntermediateResultTypes": ["IRT_ORIGINAL_IMAGE", "IRT_COLOUR_CLUSTERED_IMAGE", "IRT_COLOUR_CONVERTED_GRAYSCALE_IMAGE", "IRT_BINARIZED_IMAGE"]}}
        # params = json.dumps(settings)
        # ret = dbr.setParameters(params)
        # dbr.setFurtherModes(dbr.GRAY_SCALE_TRANSFORMATION_MODE, [dbr.GTM_INVERTED, dbr.GTM_ORIGINAL])
        decodeFile(barcode_image, templateName)
        image = cv2.imread(barcode_image, 1)
        decodeBuffer(image, templateName)

    
    
