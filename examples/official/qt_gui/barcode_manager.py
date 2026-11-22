
from dynamsoft_capture_vision_bundle import *
import cv2
from multiprocessing import Process, Queue
import time
import numpy as np


def process_barcode_frame(frameQueue, resultQueue, template=None, types=0):
    # Create Dynamsoft Barcode Reader
    LicenseManager.init_license(
            "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
    cvr_instance = CaptureVisionRouter()
    if template != None and template != '':
        cvr_instance.init_settings(template)

    if types != 0:
        error_code, error_message, settings = cvr_instance.get_simplified_settings(EnumPresetTemplate.PT_READ_BARCODES.value)
        settings.barcode_settings.barcode_format_ids = types
        error_code, error_message = cvr_instance.update_settings(EnumPresetTemplate.PT_READ_BARCODES.value, settings)
        if error_code != EnumErrorCode.EC_OK:
            print(error_message)

    while True:
        results = None

        try:
            frame = frameQueue.get(False, 10)
            if type(frame) is str:
                break
        except:
            time.sleep(0.01)
            continue

        start, end = 0, 0
        start = time.time()
        results = cvr_instance.capture(frame, EnumPresetTemplate.PT_READ_BARCODES.value)
        end = time.time()

        # Extract serializable data from results before putting in queue
        serializable_results = None
        if results is not None and results.get_items() is not None and len(results.get_items()) > 0:
            items_data = []
            for item in results.get_items():
                location = item.get_location()
                item_data = {
                    'text': item.get_text(),
                    'format_string': item.get_format_string(),
                    'points': [(point.x, point.y) for point in location.points]
                }
                items_data.append(item_data)
            serializable_results = items_data

        try:
            resultQueue.put([serializable_results, (end - start) * 1000], False, 10)
        except:
            pass


class BarcodeManager():
    def __init__(self):
        self.cvr_instance = CaptureVisionRouter()
        self._template = None
        self._types = 0
        self.barcodeScanning = None
        size = 1
        self.frameQueue = Queue(size)
        self.resultQueue = Queue(size)

    def __init_params(self):
        if self._template != None and self._template != '':
            self.cvr_instance.init_settings(self._template)

        if self._types != 0:
            error_code, error_message, settings = self.cvr_instance.get_simplified_settings(EnumPresetTemplate.PT_READ_BARCODES.value)
            settings.barcode_settings.barcode_format_ids = self._types
            error_code, error_message = self.cvr_instance.update_settings(EnumPresetTemplate.PT_READ_BARCODES.value, settings)
            if error_code != EnumErrorCode.EC_OK:
                print(error_message)

    def __decode_file(self, filename):
        self.__init_params()

        frame = cv2.imread(filename)
        start = time.time()
        results = self.cvr_instance.capture(frame, EnumPresetTemplate.PT_READ_BARCODES.value)
        end = time.time()

        return frame, [results, (end - start) * 1000]

    def __decode_buffer(self, frame):
        if frame is None:
            return None, None

        self.__init_params()

        start = time.time()
        results = self.cvr_instance.capture(frame, EnumPresetTemplate.PT_READ_BARCODES.value)
        end = time.time()
        return frame, [results, (end - start) * 1000]

    def decode_frame(self, frame):
        return self.__decode_buffer(frame)

    def decode_file(self, filename):
        if filename.endswith('.gif') or filename.endswith('.pdf'):
            return self.__decode_file(filename)
        else:
            frame = cv2.imread(filename)
            return self.__decode_buffer(frame)

    def set_template(self, template):
        self._template = template

    def set_barcode_types(self, types):
        self._types = types

    def initQueue(self):
        size = 5  # Increased from 1 to allow better buffering
        self.frameQueue = Queue(size)
        self.resultQueue = Queue(size)

    def create_barcode_process(self):
        self.destroy_barcode_process()
        self.initQueue()
        self.barcodeScanning = Process(target=process_barcode_frame, args=(
            self.frameQueue, self.resultQueue, self._template, self._types))
        self.barcodeScanning.start()

    def destroy_barcode_process(self):
        if self.frameQueue != None:
            self.frameQueue.put("")
            self.frameQueue = None

        if self.barcodeScanning != None:
            self.barcodeScanning.join()
            self.barcodeScanning = None

        if self.frameQueue != None:
            self.frameQueue.close()
            self.frameQueue = None

        if self.resultQueue != None:
            while not self.resultQueue.empty():
                try:
                    self.resultQueue.get(timeout=0.001)
                except:
                    pass
            self.resultQueue.close()
            self.resultQueue = None

    def append_frame(self, frame):
        try:
            if self.frameQueue != None:
                # Try to clear any old frames first to avoid queue being full
                try:
                    while not self.frameQueue.empty():
                        self.frameQueue.get(False)
                except:
                    pass
                # Add the new frame
                self.frameQueue.put(frame.copy(), False, 10)
        except:
            pass

    def peek_results(self):
        try:
            if self.resultQueue is not None:
                return self.resultQueue.get(False, 10)
        except:
            return None
        return None

    def get_template(self):
        return self.cvr_instance.output_settings(EnumPresetTemplate.PT_READ_BARCODES.value)

    def set_license(self, key):
        return LicenseManager.init_license(key)

    def decodeLatestFrame(self):
        try:
            if self.frameQueue is not None:
                frame = self.frameQueue.get(False, 10)
                if type(frame) is str:
                    return None

                start = time.time()
                results = self.cvr_instance.capture(frame, EnumPresetTemplate.PT_READ_BARCODES.value)
                end = time.time()
                return [results, (end - start) * 1000]
        except Exception as e:
            time.sleep(0.01)
            return None
        return None
