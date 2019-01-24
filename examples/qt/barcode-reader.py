import sys
from PySide2.QtGui import QPixmap

from PySide2.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QFileDialog, QTextEdit, QSizePolicy
from PySide2.QtCore import Slot, Qt, QStringListModel, QSize

import dbr
import os

class UI_Window(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        # The default barcode image.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dir_path, 'image.tif')

        # Create a layout.
        layout = QVBoxLayout()

        # Add a button
        self.btn = QPushButton("Load an image")
        self.btn.clicked.connect(self.pickFile)
        layout.addWidget(self.btn)

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
        # Load an image file.
        filename = QFileDialog.getOpenFileName(self, 'Open file',
                                               'E:\\Program Files (x86)\\Dynamsoft\\Barcode Reader 6.4.1\\Images', "Barcode images (*)")
        # Show barcode images
        pixmap = self.resizeImage(filename[0])
        self.label.setPixmap(pixmap)

        # Read barcodes
        self.readBarcode(filename[0])

def main():
    app = QApplication(sys.argv)
    ex = UI_Window()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
