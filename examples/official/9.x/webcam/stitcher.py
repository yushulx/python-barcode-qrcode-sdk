from __future__ import print_function

import numpy as np
import cv2 as cv

from multiprocessing.pool import ThreadPool
from collections import deque

import dbr
from dbr import *

import time

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
                for result in results:
                    points = result.localization_result.localization_points
                    cv.line(frame, points[0], points[1], (0,255,0), 2)
                    cv.line(frame, points[1], points[2], (0,255,0), 2)
                    cv.line(frame, points[2], points[3], (0,255,0), 2)
                    cv.line(frame, points[3], points[0], (0,255,0), 2)
                    cv.putText(frame, result.barcode_text, points[0], cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))

                self.panorama.append((frame, len(results)))
                print('Stitching .............')
                try:
                    all_images = [frame for frame, count in self.panorama]
                    status, image = self.stitcher.stitch(all_images)

                    if status != cv.Stitcher_OK:
                        print("Can't stitch images, error code = %d" % status)
                        return self.panorama[0][0]
                    else:
                        # Stop stitching if the output image is out of control
                        if image.shape[0] >= frame.shape[0] * 1.5:
                            self.isPanoramaDone = True
                            self.save_frame(all_images[0])
                            print('Stitching is done.............')
                            return None

                        # Drop the stitched image if its quality is not good enough
                        total = 0
                        for frame, count in self.panorama:
                            total += count

                        count_stitch = self.count_barcodes(image)
                        if count_stitch > total or count_stitch < self.panorama[0][1]:
                            return self.panorama[0][0]

                        # Wait for the next stitching and return the current stitched image
                        self.panorama = [(image, count_stitch)]
                        return image
                except Exception as e:
                    print(e)
                    return None
                    
        except BarcodeReaderError as e:
            print(e)
            return None

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
        cap = cv.VideoCapture(fn)

        threadn = 1 # cv.getNumberOfCPUs()
        barcodePool = ThreadPool(processes = threadn)
        panoramaPool = ThreadPool(processes = threadn)
        cameraTasks = deque()
        panoramaTask = deque()
        mode = self.MODE_CAMERA_ONLY
        image = None

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
                    image = panoramaTask.popleft().get()
                    if image is not None:
                        cv.imshow('panorama', image)
            
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
            elif ord('s') == ch:
                print('Stitching is done.............')
                self.isPanoramaDone = True

            # Quit panorama mode
            if self.isPanoramaDone:
                self.close_window('panorama')
                mode = self.MODE_CAMERA_ONLY
                self.clean_deque(panoramaTask)
                self.isPanoramaDone = False
                if image is not None:
                    self.save_frame(image)
                    image = None

            cv.imshow('Barcode & QR Code Scanner', frame)

        cv.destroyAllWindows()
        print('Done')


if __name__ == '__main__':
    ScanManager().run()
    
