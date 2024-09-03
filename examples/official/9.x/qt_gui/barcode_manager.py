
from dbr import *
import cv2
from multiprocessing import Process, Queue
import time
import numpy as np


def process_barcode_frame(frameQueue, resultQueue, template=None, types=0, types2=0):
    # Create Dynamsoft Barcode Reader
    reader = BarcodeReader()
    if template != None and template != '':
        error = reader.init_runtime_settings_with_string(template)
        if error[0] != EnumErrorCode.DBR_OK:
            print(error[1])

    if types != 0:
        settings = reader.get_runtime_settings()
        settings.barcode_format_ids = types
        ret = reader.update_runtime_settings(settings)

    if types2 != 0:
        settings = reader.get_runtime_settings()
        settings.barcode_format_ids_2 = types2
        ret = reader.update_runtime_settings(settings)

    settings = reader.get_runtime_settings()
    settings.max_algorithm_thread_count = 1
    reader.update_runtime_settings(settings)

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
        try:
            frameHeight, frameWidth, channel = frame.shape[:3]
            start = time.time()
            # results = reader.decode_buffer(frame)
            results = reader.decode_buffer_manually(np.array(frame).tobytes(
            ), frameWidth, frameHeight, frame.strides[0], EnumImagePixelFormat.IPF_RGB_888)
            end = time.time()
        except BarcodeReaderError as error:
            print(error)

        try:
            resultQueue.put([results, (end - start) * 1000], False, 10)
        except:
            pass


class BarcodeManager():
    def __init__(self):
        self._reader = BarcodeReader()
        settings = self._reader.get_runtime_settings()
        settings.max_algorithm_thread_count = 1
        self._reader.update_runtime_settings(settings)
        self._template = None
        self._types = 0
        self._types2 = 0

        self.frameQueue, self.resultQueue, self.barcodeScanning = None, None, None

    def __init_params(self):
        if self._template != None and self._template != '':
            error = self._reader.init_runtime_settings_with_string(
                self._template)
            if error[0] != EnumErrorCode.DBR_OK:
                print(error[1])

        if self._types != 0:
            settings = self._reader.get_runtime_settings()
            settings.barcode_format_ids = self._types
            ret = self._reader.update_runtime_settings(settings)

        if self._types2 != 0:
            settings = self._reader.get_runtime_settings()
            settings.barcode_format_ids_2 = self._types2
            ret = self._reader.update_runtime_settings(settings)

    def __decode_file(self, filename):
        self.__init_params()

        settings = self._reader.get_runtime_settings()
        settings.intermediate_result_types = EnumIntermediateResultType.IRT_ORIGINAL_IMAGE
        settings.intermediate_result_saving_mode = EnumIntermediateResultSavingMode.IRSM_MEMORY
        error = self._reader.update_runtime_settings(settings)

        start = time.time()
        results = self._reader.decode_file(filename)
        end = time.time()

        intermediate_results = self._reader.get_all_intermediate_results()

        imageData = intermediate_results[0].results[0]
        buffer = imageData.bytes
        width = imageData.width
        height = imageData.height
        stride = imageData.stride
        format = imageData.image_pixel_format
        channel = 3
        if format == EnumImagePixelFormat.IPF_RGB_888:
            channel = 3
        elif format == EnumImagePixelFormat.IPF_BINARY or format == EnumImagePixelFormat.IPF_GRAYSCALED or format == EnumImagePixelFormat.IPF_BINARYINVERTED:
            channel = 1

        if format == EnumImagePixelFormat.IPF_BINARY or format == EnumImagePixelFormat.IPF_BINARYINVERTED:
            whiteValue = 1
            if format == EnumImagePixelFormat.IPF_BINARYINVERTED:
                whiteValue = 0

            binData = bytearray(len(buffer) << 3)
            count = 0
            for pos in range(len(buffer)):
                for bit in range(7, -1, -1):
                    if (buffer[pos] >> bit) & 0x01 == whiteValue:
                        binData[count] = 255
                    else:
                        binData[count] = 0

                    count += 1

            frame = np.ndarray((height, width, channel),
                               np.uint8, binData, 0, (stride << 3, channel, 1))
        else:

            frame = np.ndarray((height, width, channel),
                               np.uint8, buffer, 0, (stride, channel, 1))
        return frame, [results, (end - start) * 1000]

    def __decode_buffer(self, frame):
        if frame is None:
            return None, None

        self.__init_params()

        start = time.time()
        results = self._reader.decode_buffer(frame)
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

    def set_barcode_types_2(self, types):
        self._types2 = types

    def create_barcode_process(self):
        self.destroy_barcode_process()

        size = 1
        self.frameQueue = Queue(size)
        self.resultQueue = Queue(size)
        self.barcodeScanning = Process(target=process_barcode_frame, args=(
            self.frameQueue, self.resultQueue, self._template, self._types, self._types2))
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
            self.resultQueue.close()
            self.resultQueue = None

    def append_frame(self, frame):
        try:
            self.frameQueue.put(frame.copy(), False, 10)
        except:
            pass

    def peek_results(self):
        try:
            return self.resultQueue.get(False, 10)
        except:
            return None

    def get_template(self):
        return self._reader.output_settings_to_json_string()

    def set_license(self, key):
        BarcodeReader.init_license(key)
