import os
import json
import sys
import barcodeQrSDK

# set license
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

# initialize barcode reader
reader = barcodeQrSDK.createInstance()

def decodeFile(fileName):
    try:
        results, elapsed_time = reader.decodeFile(fileName)
        for result in results:
            print("barcode format: " + result.format)
            print("barcode value: " + result.text)
    except Exception as err:
        print(err)


if __name__ == "__main__":
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
