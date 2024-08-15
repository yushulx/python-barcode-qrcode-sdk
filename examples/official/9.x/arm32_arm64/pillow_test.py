#!/usr/bin/env python3
import os
from dbr import *
import dbr
import time
from PIL import Image


def main():
    print('version: ' + dbr.__version__)
    BarcodeReader.init_license(
        "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

    reader = BarcodeReader()
    reader.init_runtime_settings_with_file(
        'faster.json', conflict_mode=EnumConflictMode.CM_OVERWRITE)

    # read file list
    folder = '../../../../images'
    target_dir = os.path.join(os.getcwd(), folder)
    print(target_dir)
    if os.path.exists(target_dir):
        filelist = os.listdir(target_dir)

        index = 0
        while index < len(filelist):
            file = filelist[index]
            filapath = os.path.join(target_dir, file)

            index += 1

            if os.path.isfile(filapath):

                with Image.open(filapath) as im:
                    try:
                        start_time = time.time()
                        results = reader.decode_buffer_manually(
                            im.tobytes(), im.width, im.height, im.width * 3, EnumImagePixelFormat.IPF_RGB_888)
                        elapsed_time = time.time() - start_time
                        print(file + ", elapsed time: " + str(round(elapsed_time *
                                                                    1000)) + "ms, " + ' results: ' + str(len(results)))

                        if results != None:
                            for result in results:
                                print(result.barcode_format_string +
                                      ': ' + result.barcode_text)
                        else:
                            print(' results: 0')

                    except Exception as err:
                        print(err)

                print('-------------------------------------')


if __name__ == '__main__':
    main()
