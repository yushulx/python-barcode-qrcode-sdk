#!/usr/bin/env python3

'''
Usage:
   app.py <license.txt>
'''

import sys
from PySide6.QtGui import QPixmap, QImage

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QFileDialog, QTextEdit, QMessageBox, QHBoxLayout
from PySide6.QtCore import QTimer

from barcode_manager import *
import os
import cv2
import numpy as np


class UI_Window(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        self.FRAME_WIDTH = 640
        self.FRAME_HEIGHT = 480
        self.WINDOW_WIDTH = 1280
        self.WINDOW_HEIGHT = 1000
        self._results = None
        # Initialize Dynamsoft Barcode Reader
        self._barcodeManager = BarcodeManager()

        # Initialize OpenCV camera
        self._cap = cv2.VideoCapture(0)
        # cap.set(5, 30)  #set FPS
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)

        # The current path.
        self._path = os.path.dirname(os.path.realpath(__file__))

        # Create a timer.
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameUpdate)

        # Create a layout.
        layout = QVBoxLayout()

        # Add a button
        self.btn = QPushButton("Load an image")
        self.btn.clicked.connect(self.pickFile)
        layout.addWidget(self.btn)

        # Add a button
        button_layout = QHBoxLayout()

        btnCamera = QPushButton("Open camera")
        btnCamera.clicked.connect(self.openCamera)
        button_layout.addWidget(btnCamera)

        btnCamera = QPushButton("Stop camera")
        btnCamera.clicked.connect(self.stopCamera)
        button_layout.addWidget(btnCamera)

        layout.addLayout(button_layout)

        # Add a label
        self.label = QLabel()
        self.label.setFixedSize(self.WINDOW_WIDTH - 30,
                                self.WINDOW_HEIGHT - 160)
        layout.addWidget(self.label)

        # Add a text area
        self.results = QTextEdit()
        layout.addWidget(self.results)

        # Set the layout
        self.setLayout(layout)
        self.setWindowTitle("Dynamsoft Barcode Reader")
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

    def closeEvent(self, event):

        msg = "Close the app?"
        reply = QMessageBox.question(self, 'Message',
                                     msg, QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.stopCamera()
            event.accept()
        else:
            event.ignore()

    def resizeImage(self, pixmap):
        lwidth = self.label.maximumWidth()
        pwidth = pixmap.width()
        lheight = self.label.maximumHeight()
        pheight = pixmap.height()

        wratio = pwidth * 1.0 / lwidth
        hratio = pheight * 1.0 / lheight

        if pwidth > lwidth or pheight > lheight:
            if wratio > hratio:
                lheight = pheight / wratio
            else:
                lwidth = pwidth / hratio

            scaled_pixmap = pixmap.scaled(lwidth, lheight)
            return scaled_pixmap
        else:
            return pixmap

    def showMessageBox(self, text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()

    def pickFile(self):
        self.stopCamera()
        # Load an image file.
        filename = QFileDialog.getOpenFileName(self, 'Open file',
                                               self._path, "Barcode images (*)")
        if filename is None or filename[0] == '':
            self.showMessageBox("No file selected")
            return

        # Read barcodes
        frame, results = self._barcodeManager.decode_file(filename[0])
        if frame is None:
            self.showMessageBox("Cannot decode " + filename[0])
            return

        self.showResults(frame, results)

    def openCamera(self):

        if not self._cap.isOpened():
            self.showMessageBox("Failed to open camera.")
            return

        self._barcodeManager.create_barcode_process()
        self.timer.start(int(1000./24))

    def stopCamera(self):
        self._barcodeManager.destroy_barcode_process()
        self.timer.stop()

    def showResults(self, frame, results):
        out = ''
        index = 0

        if results is not None:
            thickness = 2
            color = (0, 255, 0)
            out = 'Elapsed time: ' + "{:.2f}".format(results[1]) + 'ms\n\n'
            
            if results[0] is not None:
                items_data = results[0]
                
                if isinstance(items_data, list):
                    for item_data in items_data:
                        out += "Index: " + str(index) + "\n"
                        out += "Barcode format: " + item_data['format_string'] + '\n'
                        out += "Barcode value: " + item_data['text'] + '\n'
                        out += '-----------------------------------\n'
                        index += 1

                        points = item_data['points']
                        pts = np.array(points, np.int32).reshape((-1, 1, 2))
                        cv2.drawContours(frame, [pts], 0, (0, 255, 0), 2)
                        cv2.putText(frame, item_data['text'], (points[0][0], points[0][1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
                else:
                    result = results[0]
                    items = result.get_items()
                    for item in items:
                        location = item.get_location()
                        x1 = location.points[0].x
                        y1 = location.points[0].y
                        x2 = location.points[1].x
                        y2 = location.points[1].y
                        x3 = location.points[2].x
                        y3 = location.points[2].y
                        x4 = location.points[3].x
                        y4 = location.points[3].y

                        out += "Index: " + str(index) + "\n"
                        out += "Barcode format: " + item.get_format_string() + '\n'
                        out += "Barcode value: " + item.get_text() + '\n'
                        out += '-----------------------------------\n'
                        index += 1

                        pts = np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], np.int32).reshape((-1, 1, 2))
                        cv2.drawContours(frame, [pts], 0, (0, 255, 0), 2)
                        cv2.putText(frame, item.get_text(), (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
            else:
                out += "No barcodes detected\n"
        else:
            out = "Waiting for scanner results...\n"

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(
            frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        pixmap = self.resizeImage(pixmap)
        self.label.setPixmap(pixmap)
        self.results.setText(out)

    def nextFrameUpdate(self):
        ret, frame = self._cap.read()

        if not ret:
            self.showMessageBox('Failed to get camera frame!')
            return

        self._barcodeManager.append_frame(frame)
        self._results = self._barcodeManager.peek_results()

        self.showResults(frame, self._results)


def main():
    try:
        with open(sys.argv[1]) as f:
            license = f.read()
            LicenseManager.init_license(
                license)
    except:
        LicenseManager.init_license(
            "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

    app = QApplication(sys.argv)
    ex = UI_Window()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    print(__doc__)
    main()
