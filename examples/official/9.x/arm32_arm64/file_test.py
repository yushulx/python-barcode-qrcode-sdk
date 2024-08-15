#!/usr/bin/env python3
import os
from dbr import *
import dbr
import time


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

    if os.path.exists(target_dir):
        filelist = os.listdir(target_dir)

        index = 0
        while index < 5:
            file = filelist[index]
            filapath = os.path.join(target_dir, file)

            if os.path.isfile(filapath):
                start_time = time.time()
                results = reader.decode_file(filapath)
                elapsed_time = time.time() - start_time

                print(filelist[0] + ", elapsed time: " +
                      str(round(elapsed_time * 1000)) + "ms, ")
                if results != None:
                    for result in results:
                        print(result.barcode_format_string +
                              ': ' + result.barcode_text)
                else:
                    print(' results: 0')

            index += 1


if __name__ == '__main__':
    main()
