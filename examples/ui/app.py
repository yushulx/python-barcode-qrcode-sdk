from tkinter import *
import os
import json
import sys
import barcodeQrSDK

# set license
barcodeQrSDK.initLicense("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

# initialize barcode reader
reader = barcodeQrSDK.createInstance()

def showResults(results, barcode_image):
    ws = Tk()
    ws.title('Barcode Reader')


    bg = PhotoImage(file = barcode_image)
    ws.geometry('{}x{}'.format(bg.width(), bg.height()))
    canvas = Canvas(
            ws, 
            width = bg.width(),
            height = bg.height()
            )
    
    canvas.pack(fill='both', expand = True)

    canvas.create_image(
        0, 
        0, 
        image=bg,
        anchor = "nw"
        )
        
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
        
        canvas.create_text(x1 + 10, y1 + 10, text = result.text, font=('Arial', 18), fill='red')
        
        canvas.create_line(x1, y1, x2, y2, fill='red', width=2)
        canvas.create_line(x2, y2, x3, y3, fill='red', width=2)
        canvas.create_line(x3, y3, x4, y4, fill='red', width=2)
        canvas.create_line(x4, y4, x1, y1, fill='red', width=2)


    ws.mainloop()

def decodeFile(fileName):
    try:
        results, elapsed_time = reader.decodeFile(fileName)
        return results
    except Exception as err:
        print(err)
        return None

if __name__ == "__main__":
    import sys
    barcode_image = "test.png"
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
    results = decodeFile(barcode_image)
    if results is not None:
        showResults(results, barcode_image)
        


