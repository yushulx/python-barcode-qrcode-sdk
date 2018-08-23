import cv2
import dbr
import time
import os
from multiprocessing import Process, Queue

import sys
sys.path.append('../')
import config


def clear_queue(queue):
    try:
        while queue.qsize() > 0:
            queue.get()
        queue.close()
        queue.join_thread()
    except:
        pass


def dbr_run(frame_queue, status_queue, finish_queue):
    dbr.initLicense(config.license)
    while finish_queue.qsize() == 0:
        if frame_queue.empty():
            continue

        inputframe = frame_queue.get()
        results = dbr.decodeBuffer(inputframe, config.barcodeTypes)
        if (len(results) > 0):
            print(get_time())
            print("Total count: " + str(len(results)))
            for result in results:
                print("Type: " + result[0])
                print("Value: " + result[1] + "\n")

        status_queue.put("main")

    dbr.destroy()
    print("Detection is done.")
    clear_queue(frame_queue)
    clear_queue(status_queue)
    clear_queue(finish_queue)


def get_time():
    localtime = time.localtime()
    capturetime = time.strftime("%Y%m%d%H%M%S", localtime)
    return capturetime


def read_barcode():
    frame_queue = Queue()
    status_queue = Queue()
    finish_queue = Queue()

    vc = cv2.VideoCapture(0)

    if vc.isOpened():  # try to get the first frame
        rval, frame = vc.read()
    else:
        return

    windowName = "Barcode Reader"
    is_started = False

    while True:
        cv2.imshow(windowName, frame)
        rval, frame = vc.read()

        if frame_queue.qsize() == 0:
            frame_queue.put(frame)

            if is_started == False:
                is_started = True
                dbr_proc = Process(target=dbr_run, args=(
                    frame_queue, status_queue, finish_queue))
                dbr_proc.start()
        else:
            status = status_queue.get()
            if status == "main":
                frame_queue.put(frame)

        # 'ESC' for quit
        key = cv2.waitKey(20)
        if key == 27:
            finish_queue.put(True)
            dbr_proc.join()
            break

    cv2.destroyWindow(windowName)


if __name__ == "__main__":
    print("OpenCV version: " + cv2.__version__)
    read_barcode()
