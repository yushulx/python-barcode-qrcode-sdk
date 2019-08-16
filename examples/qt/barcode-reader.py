import sys
from PySide2.QtGui import QPixmap, QImage

from PySide2.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QFileDialog, QTextEdit, QSizePolicy, QMessageBox, QHBoxLayout
from PySide2.QtCore import Slot, Qt, QStringListModel, QSize, QTimer

from dbr import DynamsoftBarcodeReader
dbr = DynamsoftBarcodeReader()
import os
import cv2

class UI_Window(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        # The default barcode image.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dir_path, 'image.tif')

        # Create a timer.
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)

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
        self.label.setFixedSize(640, 640)
        pixmap = self.resizeImage(filename)
        self.label.setPixmap(pixmap)
        layout.addWidget(self.label)

        # Add a text area
        self.results = QTextEdit()
        self.readBarcode(filename)
        layout.addWidget(self.results)

        # Set the layout
        self.setLayout(layout)
        self.setWindowTitle("Dynamsoft Barcode Reader")
        self.setFixedSize(800, 800)

    # https://stackoverflow.com/questions/1414781/prompt-on-exit-in-pyqt-application
    def closeEvent(self, event):
    
        msg = "Close the app?"
        reply = QMessageBox.question(self, 'Message', 
                        msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            self.stopCamera()
        else:
            event.ignore()

    def readBarcode(self, filename):
        dbr.initLicense("Your License")
        results = dbr.decodeFile(filename, 0x3FF | 0x2000000 | 0x4000000 | 0x8000000 | 0x10000000)

        out = ''
        index = 0
        for result in results:
            out += "Index: " + str(index) + "\n"
            out += "Barcode format: " + result[0] + '\n'
            out += "Barcode value: " + result[1] + '\n'
            out += '-----------------------------------\n'
            index += 1

        self.results.setText(out)

    def resizeImage(self, filename):
        pixmap = QPixmap(filename)
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

    def pickFile(self):
        self.stopCamera()
        # Load an image file.
        filename = QFileDialog.getOpenFileName(self, 'Open file',
                                               'E:\\Program Files (x86)\\Dynamsoft\\Barcode Reader 7.1\\Images', "Barcode images (*)")
        # Show barcode images
        pixmap = self.resizeImage(filename[0])
        self.label.setPixmap(pixmap)

        # Read barcodes
        self.readBarcode(filename[0])

    def openCamera(self):
        self.vc = cv2.VideoCapture(0)
        # vc.set(5, 30)  #set FPS
        self.vc.set(3, 640) #set width
        self.vc.set(4, 480) #set height

        if not self.vc.isOpened(): 
            msgBox = QMessageBox()
            msgBox.setText("Failed to open camera.")
            msgBox.exec_()
            return

        self.timer.start(1000./24)
    
    def stopCamera(self):
        self.timer.stop()

    # https://stackoverflow.com/questions/41103148/capture-webcam-video-using-pyqt
    def nextFrameSlot(self):
        rval, frame = self.vc.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)

        results = dbr.decodeBuffer(frame, 0x3FF | 0x2000000 | 0x4000000 | 0x8000000 | 0x10000000)
        out = ''
        index = 0
        for result in results:
            out += "Index: " + str(index) + "\n"
            out += "Barcode format: " + result[0] + '\n'
            out += "Barcode value: " + result[1] + '\n'
            out += '-----------------------------------\n'
            index += 1

        self.results.setText(out)
            
def main():
    app = QApplication(sys.argv)
    ex = UI_Window()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
