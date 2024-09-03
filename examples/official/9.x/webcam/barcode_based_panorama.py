from __future__ import print_function
import re

import numpy as np
import cv2 as cv

from multiprocessing.pool import ThreadPool
from collections import deque

import dbr
from dbr import *

import time
from util import *

BarcodeReader.init_license("DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

class ScanManager:
    MODE_AUTO_STITCH = 0
    MODE_MANUAL_STITCH = 1
    MODE_CAMERA_ONLY = 2

    def __init__(self):
        modes = (cv.Stitcher_PANORAMA, cv.Stitcher_SCANS)
        self.stitcher = cv.Stitcher.create(modes[1])
        self.stitcher.setPanoConfidenceThresh(0.1)
        self.panorama = []
        self.isPanoramaDone = False
        self.reader = BarcodeReader()

    def count_barcodes(self, frame):
        try:
            results = self.reader.decode_buffer(frame)
            return len(results)
        except BarcodeReaderError as e:
            print(e)
        
        return 0

    def save_frame(self, frame):
        # frame = self.frame_overlay(frame)
        filename = str(time.time()) + "_panorama.jpg"
        cv.imwrite(filename, frame)
        print("Saved to " + filename)

    def frame_overlay(self, frame):
        frame_cp = frame.copy()
        try:
            results = self.reader.decode_buffer(frame_cp)
            if results != None:
                for result in results:
                    points = result.localization_result.localization_points
                    cv.line(frame_cp, points[0], points[1], (0,255,0), 2)
                    cv.line(frame_cp, points[1], points[2], (0,255,0), 2)
                    cv.line(frame_cp, points[2], points[3], (0,255,0), 2)
                    cv.line(frame_cp, points[3], points[0], (0,255,0), 2)
                    cv.putText(frame_cp, result.barcode_text, points[0], cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))
                    
            return frame_cp
        except BarcodeReaderError as e:
            print(e)
            return None

    def stitch_frame(self, frame):
        try:
            results = self.reader.decode_buffer(frame)
            if results != None:
                # Draw results on the copy of the frame. Keep original frame clean.
                frame_cp = frame.copy()
                for result in results:
                    points = result.localization_result.localization_points
                    cv.line(frame_cp, points[0], points[1], (0,255,0), 2)
                    cv.line(frame_cp, points[1], points[2], (0,255,0), 2)
                    cv.line(frame_cp, points[2], points[3], (0,255,0), 2)
                    cv.line(frame_cp, points[3], points[0], (0,255,0), 2)
                    cv.putText(frame_cp, result.barcode_text, points[0], cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))

                # Save frame and barcode info if panorama is empty
                if len(self.panorama) == 0:
                    self.panorama.append((frame, results, frame_cp))
                else:
                    # Compare results. If there is an intersection, transform and stitch. Otherwise, discard.
                    preFrame = self.panorama[0][0]
                    preResults = self.panorama[0][1]
                    preFrameCp = self.panorama[0][2]

                    while len(results) > 0:
                        result = results.pop()
                        for preResult in preResults:
                            if preResult.barcode_text == result.barcode_text and preResult.barcode_format == result.barcode_format:
                                prePoints = preResult.localization_result.localization_points
                                # preContour = np.array([prePoints[0], prePoints[1], prePoints[2], prePoints[3]])
                                # preArea = cv.minAreaRect(preContour)
                                # preAreaSize = preArea[1][0] * preArea[1][1]
                                # preBounding = cv.boxPoints(preArea)

                                points = result.localization_result.localization_points

                                # # Crop image based on min area rect
                                preFrame = preFrame[0: preFrame.shape[0], 0: max(prePoints[0][0], prePoints[1][0], prePoints[2][0], prePoints[3][0]) + 10]
                                frame = frame[0: frame.shape[0], max(points[0][0], points[1][0], points[2][0], points[3][0]): frame.shape[1] + 10]

                                preFrameCp = preFrameCp[0: preFrameCp.shape[0], 0: max(prePoints[0][0], prePoints[1][0], prePoints[2][0], prePoints[3][0]) + 10]
                                frame_cp = frame_cp[0: frame_cp.shape[0], max(points[0][0], points[1][0], points[2][0], points[3][0]): frame_cp.shape[1] + 10]

                                # # Stitch images
                                frame = concat_images([preFrame, frame])
                                frame_cp = concat_images([preFrameCp, frame_cp])

                                # Re-detect barcodes from the new image
                                results = self.reader.decode_buffer(frame)

                                # Save results
                                self.panorama = [(frame, results, frame_cp)]
                                return frame, frame_cp

                return self.panorama[0][0], self.panorama[0][2]
                    
        except BarcodeReaderError as e:
            print(e)
            return None, None

        return None, None


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
        cap = cv.VideoCapture(fn)

        threadn = 1 # cv.getNumberOfCPUs()
        barcodePool = ThreadPool(processes = threadn)
        panoramaPool = ThreadPool(processes = threadn)
        cameraTasks = deque()
        panoramaTask = deque()
        mode = self.MODE_CAMERA_ONLY
        image = None
        imageCp = None
        panoramaImage = None
        panoramaImageCp = None

        while True:
            ret, frame = cap.read()
            frame_cp = frame.copy()
            cv.putText(frame, 'A: auto pano, M: manual pano, C: capture, O: camera, S: stop', (10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))
            cv.putText(frame, 'Barcode & QR Code Scanning ...', (10, 50), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0))

            # Scan and show barcode & QR code results
            while len(cameraTasks) > 0 and cameraTasks[0].ready():
                results = cameraTasks.popleft().get()
                if results != None:
                    for result in results:
                        points = result.localization_result.localization_points
                        cv.line(frame, points[0], points[1], (0,255,0), 2)
                        cv.line(frame, points[1], points[2], (0,255,0), 2)
                        cv.line(frame, points[2], points[3], (0,255,0), 2)
                        cv.line(frame, points[3], points[0], (0,255,0), 2)
                        cv.putText(frame, result.barcode_text, points[0], cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))
                
            if len(cameraTasks) < threadn:
                task = barcodePool.apply_async(self.process_frame, (frame_cp, ))
                cameraTasks.append(task)

            # Stitch images for panorama
            if mode == self.MODE_MANUAL_STITCH:
                cv.putText(frame, 'Manual Panorama ...', (10, 70), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0))
            elif mode == self.MODE_AUTO_STITCH:
                cv.putText(frame, 'Auto Panorama ...', (10, 70), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0))
                if not self.isPanoramaDone and len(panoramaTask) < threadn:
                    task = panoramaPool.apply_async(self.stitch_frame, (frame_cp, ))
                    panoramaTask.append(task)

            if mode == self.MODE_MANUAL_STITCH or mode == self.MODE_AUTO_STITCH:
                while len(panoramaTask) > 0 and panoramaTask[0].ready():
                    image, imageCp = panoramaTask.popleft().get()
                    if image is not None:
                        panoramaImage = image.copy()
                        panoramaImageCp = imageCp.copy()
                        cv.imshow('panorama', panoramaImageCp)
            
            # Key events
            ch = cv.waitKey(1)
            if ch == 27:
                break
            if ord('o') == ch:
                self.close_window('panorama')
                self.isPanoramaDone = True
                mode = self.MODE_CAMERA_ONLY
                self.clean_deque(panoramaTask)
            elif ord('a') == ch:
                self.close_window('panorama')
                self.isPanoramaDone = False
                mode = self.MODE_AUTO_STITCH
                self.clean_deque(panoramaTask)
                self.panorama = []
            elif ord('m') == ch:
                self.close_window('panorama')
                self.isPanoramaDone = False
                mode = self.MODE_MANUAL_STITCH
                self.clean_deque(panoramaTask)
                self.panorama = []
            elif ord('c') == ch and mode == self.MODE_MANUAL_STITCH and not self.isPanoramaDone:
                if len(panoramaTask) < threadn:
                    task = panoramaPool.apply_async(self.stitch_frame, (frame_cp, ))
                    panoramaTask.append(task)
            ################################################### Test image operations
            elif ord('x') == ch:
                if panoramaImageCp is not None:
                    panoramaImageCp = shiftX(panoramaImageCp, 5)
                    cv.imshow('panorama', panoramaImageCp)
            elif ord('t') == ch:
                if panoramaImageCp is not None:
                    panoramaImageCp = concat_images([panoramaImageCp, frame])
                    cv.imshow('panorama', panoramaImageCp)
            elif ord('y') == ch:
                if panoramaImageCp is not None:
                    panoramaImageCp = shiftY(panoramaImageCp, 5)
                    cv.imshow('panorama', panoramaImageCp)
            elif ord('z') == ch:
                if panoramaImageCp is not None:
                    panoramaImageCp = zoom_image(panoramaImageCp, 2)
                    cv.imshow('panorama', panoramaImageCp)
            elif ord('r') == ch:
                if panoramaImageCp is not None:
                    panoramaImageCp = rotate_image(panoramaImageCp, 1)
                    cv.imshow('panorama', panoramaImageCp)
            ###################################################

            # Quit panorama mode
            if self.isPanoramaDone:
                self.close_window('panorama')
                mode = self.MODE_CAMERA_ONLY
                self.clean_deque(panoramaTask)
                self.isPanoramaDone = False
                if panoramaImage is not None:
                    self.save_frame(panoramaImage)
                    panoramaImage = None

            cv.imshow('Barcode & QR Code Scanner', frame)

        cv.destroyAllWindows()
        print('Done')


if __name__ == '__main__':
    ScanManager().run()
    
