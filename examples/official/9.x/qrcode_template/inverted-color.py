import cv2
import numpy as np
import time
from dbr import *

license = ""
with open("license.txt", "r") as f:
    license = f.read()

BarcodeReader.init_license(license)

reader = BarcodeReader()
error = reader.init_runtime_settings_with_file('inverted-color.json')
print(error)
print(reader.get_runtime_settings().__dict__)
image = cv2.imread('images/inverted-color.jpg')


def detect(windowName, image, pixel_format):
    try:
        buffer = image.tobytes()
        height = image.shape[0]
        width = image.shape[1]
        stride = image.strides[0]
        start = time.time()
        results = reader.decode_buffer_manually(
            buffer, width, height, stride, pixel_format, "")
        end = time.time()
        print("Time taken: {:.4f}".format(end - start) + " seconds")

        cv2.putText(image, "Time taken: {:.4f}".format(
            end - start) + " seconds", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        if results != None:
            for result in results:
                print("Barcode Format : ")
                print(result.barcode_format_string)
                print("Barcode Text : ")
                print(result.barcode_text)

                points = result.localization_result.localization_points
                data = np.array([[points[0][0], points[0][1]], [points[1][0], points[1][1]], [
                                points[2][0], points[2][1]], [points[3][0], points[3][1]]])
                cv2.drawContours(image=image, contours=[
                                 data], contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)

                x = min(points[0][0], points[1][0], points[2][0], points[3][0])
                y = min(points[0][1], points[1][1], points[2][1], points[3][1])
                cv2.putText(image, result.barcode_text, (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.imshow(windowName, image)
    except BarcodeReaderError as bre:
        print(bre)


image_copy = image.copy()
detect('Color', image_copy, EnumImagePixelFormat.IPF_RGB_888)

cv2.waitKey(0)
