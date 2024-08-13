import argparse
import pyzbar.pyzbar as zbar
from PIL import Image
import zxingcpp
from dbr import *
import time
import os
import data
import cv2


def zxing_decode(filename):
    start = time.time()
    img = cv2.imread(filename)
    zxing_results = zxingcpp.read_barcodes(img)
    elapsed_time = time.time() - start
    if zxing_results != None:
        for result in zxing_results:
            print('ZXing: {}. Elapsed time: {}ms'.format(
                result.text, int(elapsed_time * 1000)))
        return zxing_results
    else:
        print('ZXing failed to decode {}'.format(filename))

    return None


def zbar_decode(zbar_reader, filename):
    start = time.time()
    zbar_results = zbar.decode(Image.open(filename))
    elapsed_time = time.time() - start
    if len(zbar_results) > 0:
        for zbar_result in zbar_results:
            print('ZBar: {}. Elapsed time: {}ms'.format(
                zbar_result.data.decode("utf-8"), int(elapsed_time * 1000)))

        return zbar_results
    else:
        print('ZBar failed to decode {}'.format(filename))

    return None


def dbr_decode(dbr_reader, filename):
    try:
        start = time.time()
        dbr_results = dbr_reader.decode_file(filename)
        elapsed_time = time.time() - start

        if dbr_results != None:
            for text_result in dbr_results:
                # print(textResult["BarcodeFormatString"])
                print('Dynamsoft Barcode Reader: {}. Elapsed time: {}ms'.format(
                    text_result.barcode_text, int(elapsed_time * 1000)))

            return dbr_results
        else:
            print("DBR failed to decode {}".format(filename))
    except Exception as err:
        print("DBR failed to decode {}".format(filename))

    return None


def dataset(directory=None, zbar_reader=None, dbr_reader=None):
    if directory != None:
        print(directory)
        files = os.listdir(directory)
        files = [f for f in files if f.endswith('.jpg') or f.endswith('.png')]
        total_count = len(files)
        if total_count == 0:
            print('No image files')
            return

        # Create a .xlsx file
        datafile = 'benchmark.xlsx'
        wb = data.get_workbook(datafile)
        index = 2

        print('Total count of barcode image files: {}'.format(total_count))
        zbar_count = 0
        dbr_count = 0
        zxing_count = 0

        for filename in files:
            file_path = os.path.join(directory, filename)
            expected_result = filename.split('_')[0]

            r1 = ''
            r2 = ''
            r3 = ''

            # ZBar
            if zbar_reader != None:
                zbar_results = zbar_decode(zbar_reader, file_path)
                if zbar_results != None:
                    for zbar_result in zbar_results:
                        zbar_text = zbar_result.data.decode("utf-8")
                        r1 = zbar_text
                        if r1 == expected_result:
                            zbar_count += 1
                            break
                else:
                    print('Fail to decode {}'.format(filename))

            # DBR
            if dbr_reader != None:
                textResults = dbr_decode(dbr_reader, file_path)
                if textResults != None:
                    for textResult in textResults:
                        r2 = textResult.barcode_text
                        if r2 == expected_result:
                            dbr_count += 1
                            break
                else:
                    print("DBR failed to decode {}".format(filename))

            # ZXing
            print('ZXing decoding {}'.format(filename))
            zxing_results = zxing_decode(file_path)
            if zxing_results != None:
                for result in zxing_results:
                    r3 = result.text
                    if r3 == expected_result:
                        zxing_count += 1
            else:
                print('ZXing failed to decode {}'.format(filename))

            # Add results to .xlsx file
            data.update_row(wb, index, filename, expected_result, r1, r2, r3)
            index += 1

            # Test
            # if index == 9:
            #     break

        r1 = 0
        r2 = 0
        r3 = 0
        if zbar_reader != None:
            zbar_rate = zbar_count * 100 / total_count
            r1 = '{0:.2f}%'.format(zbar_rate)
            print('ZBar recognition rate: {0:.2f}%'.format(zbar_rate))

        if dbr_reader != None:
            dbr_rate = dbr_count * 100 / total_count
            r2 = '{0:.2f}%'.format(dbr_rate)
            print('DBR recognition rate: {0:.2f}%'.format(dbr_rate))

        zxing_rate = zxing_count * 100 / total_count
        r3 = '{0:.2f}%'.format(zxing_rate)
        print('ZXing recognition rate: {0:.2f}%'.format(zxing_rate))

        data.set_recognition_rate(wb, index, r1, r2, r3)
        # Save data to .xlsx file
        data.save_workbook(wb, datafile)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", type=str,
                    help="path to input image")
    ap.add_argument("-d", "--directory", type=str,
                    help="directory of image folder")
    args = vars(ap.parse_args())

    image = args["image"]
    directory = args["directory"]
    if image == None and directory == None:
        print('''
        Usage: 
            python app.py -i <image_file> 
            python app.py -d <folder_directory> 
        ''')
        return

    # Initialize barcode reader
    BarcodeReader.init_license(
        'DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==')
    dbr_reader = BarcodeReader()

    if image != None:
        # ZXing
        zxing_decode(image)

        # ZBar
        zbar_decode(zbar, image)

        # Dynamsoft Barcode Reader
        dbr_decode(dbr_reader, image)

    if directory != None:
        dataset(directory,
                zbar_reader=zbar, dbr_reader=dbr_reader)


if __name__ == "__main__":
    main()
