from dynamsoft_barcode_reader_bundle import *
import cv2
import numpy as np
import queue
from utils import *


class FrameFetcher(ImageSourceAdapter):
    def has_next_image_to_fetch(self) -> bool:
        return True

    def add_frame(self, imageData):
        self.add_image_to_buffer(imageData)


class MyCapturedResultReceiver(CapturedResultReceiver):
    def __init__(self, result_queue):
        super().__init__()
        self.result_queue = result_queue

    def on_captured_result_received(self, captured_result):
        self.result_queue.put(captured_result)


if __name__ == '__main__':
    errorCode, errorMsg = LicenseManager.init_license(
        "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
    if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print("License initialization failed: ErrorCode:",
              errorCode, ", ErrorString:", errorMsg)
    else:
        vc = cv2.VideoCapture(0)
        if not vc.isOpened():
            print("Error: Camera is not opened!")
            exit(1)

        cvr = CaptureVisionRouter()
        fetcher = FrameFetcher()
        cvr.set_input(fetcher)

        # Create a thread-safe queue to store captured items
        result_queue = queue.Queue()

        receiver = MyCapturedResultReceiver(result_queue)
        cvr.add_result_receiver(receiver)

        errorCode, errorMsg = cvr.start_capturing(
            EnumPresetTemplate.PT_READ_BARCODES.value)

        if errorCode != EnumErrorCode.EC_OK:
            print("error:", errorMsg)

        while True:
            ret, frame = vc.read()
            if not ret:
                print("Error: Cannot read frame!")
                break

            fetcher.add_frame(convertMat2ImageData(frame))

            if not result_queue.empty():
                captured_result = result_queue.get_nowait()

                items = captured_result.get_items()
                for item in items:

                    if item.get_type() == EnumCapturedResultItemType.CRIT_BARCODE:
                        text = item.get_text()
                        location = item.get_location()
                        x1 = location.points[0].x
                        y1 = location.points[0].y
                        x2 = location.points[1].x
                        y2 = location.points[1].y
                        x3 = location.points[2].x
                        y3 = location.points[2].y
                        x4 = location.points[3].x
                        y4 = location.points[3].y
                        pts = np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], np.int32).reshape((-1, 1, 2))
                        cv2.drawContours(
                            frame, [pts], 0, (0, 255, 0), 2)

                        cv2.putText(frame, text, (x1, y1),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                        del location

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            elif  cv2.waitKey(1) & 0xFF == ord('c'):
                cv2.imshow('Captured Image', frame)

            cv2.imshow('frame', frame)

        cvr.stop_capturing()
        vc.release()
        cv2.destroyAllWindows()
