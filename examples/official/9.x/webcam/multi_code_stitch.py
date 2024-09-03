import numpy as np
import cv2 as cv

from multiprocessing.pool import ThreadPool
from collections import deque

import dbr
from dbr import *

import time
# from util import *

BarcodeReader.init_license(
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

def transform_point(points, matrix):
    """Transforms the point using the given matrix."""
    all = []
    for point in points:
        x, y = point
        transformed = np.dot(matrix, [x, y, 1])
        
        all.append((int(transformed[0] / transformed[2]), int(transformed[1] / transformed[2])))
    
    return all

def perspective_correction(img, pts):
    # Define the 4 points where the image will be warped to.
    # For a typical use-case, this would be a rectangle.
    # We'll use the dimensions of the input image, but you can adjust this
    # as needed to set the dimensions of the output image.
    rect = np.array([
        [0, 0],
        [img.shape[1] - 1, 0],
        [img.shape[1] - 1, img.shape[0] - 1],
        [0, img.shape[0] - 1]
    ], dtype="float32")

    # Compute the perspective transform matrix
    matrix = cv.getPerspectiveTransform(pts, rect)

    # Perform the perspective warp
    warped = cv.warpPerspective(img, matrix, (img.shape[1], img.shape[0]))

    return warped

class ScanManager:
    def __init__(self):
        self.multicode = []
        self.ismulticodeDone = False
        self.reader = BarcodeReader()

    def count_barcodes(self, frame):
        try:
            results = self.reader.decode_buffer(frame)
            return len(results)
        except BarcodeReaderError as e:
            print(e)

        return 0

    def save_frame(self, frame):
        filename = str(time.time()) + "_multicode.jpg"
        cv.imwrite(filename, frame)
        print("Saved to " + filename)

    def stitch_frame(self, frame):
        try:
            results = self.reader.decode_buffer(frame)
            if results != None:
                if len(self.multicode) == 0:
                    self.multicode = [frame, results, frame.copy()]
                else:
                    preResults = self.multicode[1]
                    matrix = None
                    newResults = []
                    isFirstTime = True
                    while len(results) > 0:
                        result = results.pop()
                        isExisted = False
                        for preResult in preResults:
                            if preResult.barcode_text == result.barcode_text and preResult.barcode_format == result.barcode_format:
                                isExisted = True
                                prePoints = preResult.localization_result.localization_points
                                points = result.localization_result.localization_points
                                if isFirstTime:
                                    isFirstTime = False
                                    matrix = cv.getPerspectiveTransform(np.array([
                                        points[0],
                                        points[1],
                                        points[2],
                                        points[3]
                                    ], dtype="float32"), np.array([
                                        prePoints[0],
                                        prePoints[1],
                                        prePoints[2],
                                        prePoints[3]
                                    ], dtype="float32"))
                                break

                        if not isExisted:
                            newResults.append(result)

                    if len(newResults) > 0:
                        try:
                            for newResult in newResults:
                                points = newResult.localization_result.localization_points
                                points = transform_point(points, matrix)
                                newResult.localization_result.localization_points = points
                                preResults.extend([newResult])

                            self.multicode = [self.multicode[0],
                                            preResults, self.multicode[2]]
                        except Exception as e:
                            return None

                for result in self.multicode[1]:
                    points = result.localization_result.localization_points
                    cv.line(self.multicode[2], points[0],
                            points[1], (0, 255, 0), 2)
                    cv.line(self.multicode[2], points[1],
                            points[2], (0, 255, 0), 2)
                    cv.line(self.multicode[2], points[2],
                            points[3], (0, 255, 0), 2)
                    cv.line(self.multicode[2], points[3],
                            points[0], (0, 255, 0), 2)
                    cv.putText(self.multicode[2], result.barcode_text,
                               points[0], cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))

                return self.multicode[2]

        except BarcodeReaderError as e:
            print(e)

        return None

    def process_frame(self, frame):
        results = None
        try:
            results = self.reader.decode_buffer(frame)
        except BarcodeReaderError as bre:
            print(bre)

        return results

    def clean_deque(self, tasks):
        while len(tasks) > 0:
            tasks.popleft()

    def close_window(self, window_name):
        try:
            cv.destroyWindow(window_name)
        except:
            pass

    def run(self):
        import sys
        try:
            fn = sys.argv[1]
        except:
            fn = 0
        cap = cv.VideoCapture(0)

        threadn = 1  # cv.getNumberOfCPUs()
        barcodePool = ThreadPool(processes=threadn)
        stitchingPool = ThreadPool(processes=threadn)
        cameraTasks = deque()
        codeStitchingTask = deque()
        stitching = False
        save = False

        while True:
            ret, frame = cap.read()
            frame_cp = frame.copy()
            cv.putText(frame, 's: save / r: reset / c: capture / ESC: stop', (10, 20),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
            cv.putText(frame, 'Multi Code Scanning ...',
                       (10, 50), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

            # Scan and show Multi Code results
            while len(cameraTasks) > 0 and cameraTasks[0].ready():
                results = cameraTasks.popleft().get()
                if results != None:
                    for result in results:
                        points = result.localization_result.localization_points
                        cv.line(frame, points[0], points[1], (0, 255, 0), 2)
                        cv.line(frame, points[1], points[2], (0, 255, 0), 2)
                        cv.line(frame, points[2], points[3], (0, 255, 0), 2)
                        cv.line(frame, points[3], points[0], (0, 255, 0), 2)
                        cv.putText(
                            frame, result.barcode_text, points[0], cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))

            while len(codeStitchingTask) > 0 and codeStitchingTask[0].ready():
                stitchedImage = codeStitchingTask.popleft().get()
                if stitchedImage is not None:
                    cv.imshow('Multi Code', stitchedImage)
                    if save:
                        save = False
                        self.save_frame(stitchedImage)

            if len(cameraTasks) < threadn:
                task = barcodePool.apply_async(
                    self.process_frame, (frame_cp, ))
                cameraTasks.append(task)

            # Key events
            ch = cv.waitKey(10)
            if ch == 27:
                break
            elif ord('s') == ch:
                save = True
            elif ord('r') == ch:
                stitching = False
                cv.destroyWindow('Multi Code')
                self.multicode = []
            elif ord('c') == ch or stitching:
                stitching = True
                if len(codeStitchingTask) < threadn:
                    task = stitchingPool.apply_async(
                        self.stitch_frame, (frame_cp, ))
                    codeStitchingTask.append(task)

            cv.imshow('Multi Code Scanner', frame)

        cv.destroyAllWindows()
        print('Done')


if __name__ == '__main__':
    ScanManager().run()
