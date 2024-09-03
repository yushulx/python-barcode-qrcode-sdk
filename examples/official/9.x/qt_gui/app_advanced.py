#!/usr/bin/env python3

'''
Usage:
   app.py <license.txt>
'''

import sys
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PySide6.QtWidgets import QApplication, QMainWindow, QInputDialog
from PySide6.QtCore import QFile, QTimer, QEvent
from PySide6.QtWidgets import *
from design import Ui_MainWindow

from barcode_manager import *
import os
import cv2
from dbr import EnumBarcodeFormat, EnumBarcodeFormat_2


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialization
        self._all_data = {}
        self._results = None
        self._painter = None

        # Dynamsoft Barcode Reader
        self._barcodeManager = BarcodeManager()

        # Create a timer.
        self.timer = None

        # Open camera
        self._cap = None
        # self.openCamera()

        # Resolution list
        self.ui.comboBox.currentTextChanged.connect(self.onComboBoxChanged)

        # The current path.
        self._path = os.path.dirname(os.path.realpath(__file__))

        # Camera button
        self.ui.pushButton_open.clicked.connect(self.openCamera)
        self.ui.pushButton_stop.clicked.connect(self.stopCamera)

        # Load file
        self.ui.actionOpen_File.triggered.connect(self.openFile)

        # Load directory
        self.ui.actionOpen_Folder.triggered.connect(self.openFolder)

        # Export template
        self.ui.actionExport_template.triggered.connect(self.exportTemplate)

        # About
        self.ui.actionAbout.triggered.connect(self.about)

        # Set license
        self.ui.actionEnter_License_Key.triggered.connect(self.setLicense)

        # List widget
        self.ui.listWidget.currentItemChanged.connect(self.currentItemChanged)

        # Template load button
        self.ui.pushButton_template.clicked.connect(self.loadTemplate)

        # Template export button
        self.ui.pushButton_export_template.clicked.connect(self.exportTemplate)

        self.ui.label.mouseMoveEvent = self.labelMouseMoveEvent
        self.ui.label.mousePressEvent = self.labelMousePressEvent
        self.ui.label.mouseReleaseEvent = self.labelMouseReleaseEvent
        self._pixmap = None
        self.x = 0
        self.y = 0
        self.endx = 0
        self.endy = 0
        self.clicked = False

    def paintEvent(self, event):
        if self._pixmap is not None:
            self.ui.label.setPixmap(self._pixmap)
            # painter = QPainter(self.ui.label.pixmap())
            # xshift = self.ui.label.width() - self._pixmap.width()
            # yshift = self.ui.label.height() - self._pixmap.height()
            # pen = QPen()
            # pen.setWidth(10)
            # pen.setColor(QColor('red'))
            # painter.setPen(pen)
            # painter.drawRect(self.x, self.y - yshift / 2, self.endx - self.x, self.endy - self.y)
            # painter.end()

    def labelMouseReleaseEvent(self, event):
        self.clicked = False

    def labelMousePressEvent(self, event):
        self.clicked = True
        self.x = event.position().x()
        self.y = event.position().y()
        self.endx = self.x
        self.endy = self.y

    def labelMouseMoveEvent(self, event):
        if self.clicked:
            self.endx = event.position().x()
            self.endy = event.position().y()

    def resetCoordinates(self):
        self.endx = self.x
        self.endy = self.y

    def openCamera(self):
        self.resetCoordinates()

        self.stopCamera()
        self.setParameters()

        width = 640
        height = 480
        resolution = self.ui.comboBox.currentText()
        if resolution == '640 x 480':
            width = 640
            height = 480
        elif resolution == '320 x 240':
            width = 320
            height = 240

        self._cap = cv2.VideoCapture(0)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        width = self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        if not self._cap.isOpened():
            self.showMessageBox('Error', "Failed to open camera.")
            return

        if not self.ui.checkBox_syncdisplay.isChecked():
            self._barcodeManager.create_barcode_process()

        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameUpdate)
        self.timer.start(1000./24)

    def stopCamera(self):

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        if not self.ui.checkBox_syncdisplay.isChecked():
            if self.timer is not None:
                self.timer.stop()
                self.timer = None

            self._barcodeManager.destroy_barcode_process()
        else:
            if self.timer is not None:
                self.timer.stop()
                self.timer = None

        self._results = None

    def nextFrameUpdate(self):
        ret, frame = self._cap.read()

        if not ret:
            self.showMessageBox('Error', 'Failed to get camera frame!')
            return

        if not self.ui.checkBox_syncdisplay.isChecked():
            self._barcodeManager.append_frame(frame)
            self._results = self._barcodeManager.peek_results()
        else:
            frame, self._results = self._barcodeManager.decode_frame(frame)

        self.showResults(frame, self._results)

    def onComboBoxChanged(self):
        self.openCamera()

    def loadTemplate(self):
        filename = QFileDialog.getOpenFileName(self, 'Open template',
                                               self._path, "*.json")
        if filename is None or filename[0] == '':
            # self.showMessageBox('Open File...', "No file selected")
            return

        with open(filename[0]) as f:
            template = f.read()
            self.ui.textEdit_template.setText(template)

    def appendFile(self, filename):

        if filename not in self._all_data:
            item = QListWidgetItem()
            item.setText(filename)
            self.ui.listWidget.addItem(item)
            self._all_data[filename] = None

    def currentItemChanged(self, current, previous):
        filename = current.text()
        self.decodeFile(filename)

    def setParameters(self):
        # Get template
        template = self.ui.textEdit_template.toPlainText()
        self._barcodeManager.set_template(template)

        # Get barcode types
        types = 0
        types2 = 0
        if (self.ui.checkBox_code39.isChecked()):
            types |= EnumBarcodeFormat.BF_CODE_39
        if (self.ui.checkBox_code93.isChecked()):
            types |= EnumBarcodeFormat.BF_CODE_93
        if (self.ui.checkBox_code128.isChecked()):
            types |= EnumBarcodeFormat.BF_CODE_128
        if (self.ui.checkBox_codabar.isChecked()):
            types |= EnumBarcodeFormat.BF_CODABAR
        if (self.ui.checkBox_itf.isChecked()):
            types |= EnumBarcodeFormat.BF_ITF
        if (self.ui.checkBox_ean13.isChecked()):
            types |= EnumBarcodeFormat.BF_EAN_13
        if (self.ui.checkBox_ean8.isChecked()):
            types |= EnumBarcodeFormat.BF_EAN_8
        if (self.ui.checkBox_upca.isChecked()):
            types |= EnumBarcodeFormat.BF_UPC_A
        if (self.ui.checkBox_upce.isChecked()):
            types |= EnumBarcodeFormat.BF_UPC_E
        if (self.ui.checkBox_industrial25.isChecked()):
            types |= EnumBarcodeFormat.BF_INDUSTRIAL_25
        if (self.ui.checkBox_qrcode.isChecked()):
            types |= EnumBarcodeFormat.BF_QR_CODE
        if (self.ui.checkBox_pdf417.isChecked()):
            types |= EnumBarcodeFormat.BF_PDF417
        if (self.ui.checkBox_aztec.isChecked()):
            types |= EnumBarcodeFormat.BF_AZTEC
        if (self.ui.checkBox_maxicode.isChecked()):
            types |= EnumBarcodeFormat.BF_MAXICODE
        if (self.ui.checkBox_datamatrix.isChecked()):
            types |= EnumBarcodeFormat.BF_DATAMATRIX
        if (self.ui.checkBox_gs1.isChecked()):
            types |= EnumBarcodeFormat.BF_GS1_COMPOSITE
        if (self.ui.checkBox_patchcode.isChecked()):
            types |= EnumBarcodeFormat.BF_PATCHCODE
        if (self.ui.checkBox_dotcode.isChecked()):
            types2 |= EnumBarcodeFormat_2.BF2_DOTCODE
        if (self.ui.checkBox_postalcode.isChecked()):
            types2 |= EnumBarcodeFormat_2.BF2_POSTALCODE

        self._barcodeManager.set_barcode_types(types)
        self._barcodeManager.set_barcode_types_2(types2)

    def decodeFile(self, filename):
        self.resetCoordinates()
        self.ui.statusbar.showMessage(filename)

        self.stopCamera()
        self.setParameters()

        # Read barcodes
        frame, results = self._barcodeManager.decode_file(filename)
        if frame is None:
            self.showMessageBox('Error', 'Cannot decode ' + filename)
            return

        self._all_data[filename] = results

        self.showResults(frame, results)

    def openFile(self):
        filename = QFileDialog.getOpenFileName(self, 'Open File',
                                               self._path, "Barcode images (*)")
        if filename is None or filename[0] == '':
            # self.showMessageBox('Open File...', "No file selected")
            return

        filename = filename[0]
        self.appendFile(filename)
        self.decodeFile(filename)

    def openFolder(self):
        dir = QFileDialog.getExistingDirectory(self, 'Open Folder',
                                               self._path, QFileDialog.ShowDirsOnly)
        if dir == '':
            # self.showMessageBox('Open Folder...', "No folder selected")
            return

        files = [os.path.join(dir, f) for f in os.listdir(
            dir) if os.path.isfile(os.path.join(dir, f))]
        if len(files) == 0:
            return

        for filename in files:
            self.appendFile(filename)

        self.decodeFile(files[0])

    def setLicense(self):
        key = QInputDialog.getText(self, 'License', 'Enter license key')
        if key[1]:
            error = self._barcodeManager.set_license(key[0])
            if error[0] != EnumErrorCode.DBR_OK:
                self.showMessageBox('Error', error[1])
            else:
                self.ui.statusbar.showMessage(
                    'Dynamsoft Barcode Reader is activated successfully!')

    def exportTemplate(self):
        filename = QFileDialog.getSaveFileName(self, 'Save File',
                                               self._path, "Barcode Template (*.json)")
        if filename is None or filename[0] == '':
            # self.showMessageBox('Open File...', "No file selected")
            return

        filename = filename[0]
        json = self._barcodeManager.get_template()
        with open(filename, 'w') as f:
            f.write(json)

        self.ui.statusbar.showMessage('File saved to ' + filename)

    def resizeImage(self, pixmap):
        lwidth = self.ui.label.width()
        pwidth = pixmap.width()
        lheight = self.ui.label.height()
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

    def showResults(self, frame, results):
        out = ''
        index = 0

        if results is not None and results[0] is not None:
            if self.ui.checkBox_autostop.isChecked():
                self.stopCamera()

            thickness = 2
            color = (0, 255, 0)
            out = 'Elapsed time: ' + "{:.2f}".format(results[1]) + 'ms\n\n'
            for result in results[0]:
                points = result.localization_result.localization_points
                out += "Index: " + str(index) + "\n"
                out += "Barcode format: " + result.barcode_format_string + '\n'
                out += "Barcode value: " + result.barcode_text + '\n'
                out += "Bounding box: " + \
                    str(points[0]) + ' ' + str(points[1]) + ' ' + \
                    str(points[2]) + ' ' + str(points[3]) + '\n'
                out += '-----------------------------------\n'
                index += 1

                cv2.line(frame, points[0], points[1], color, thickness)
                cv2.line(frame, points[1], points[2], color, thickness)
                cv2.line(frame, points[2], points[3], color, thickness)
                cv2.line(frame, points[3], points[0], color, thickness)
                cv2.putText(frame, result.barcode_text,
                            points[0], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(
            frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self._pixmap = self.resizeImage(pixmap)
        self.ui.label.setPixmap(self._pixmap)
        self.ui.textEdit_results.setText(out)

    def about(self):
        self.showMessageBox(
            "About", "<a href='https://www.dynamsoft.com/barcode-reader/overview/'>About Dynamsoft Barcode Reader</a>")

    def showMessageBox(self, title, content):
        msgBox = QMessageBox()
        msgBox.setWindowTitle(title)
        msgBox.setText(content)
        msgBox.exec()

    def closeEvent(self, event):

        msg = "Close the app?"
        reply = QMessageBox.question(self, 'Message',
                                     msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # self._painter.end()
            self.stopCamera()

            event.accept()
        else:
            event.ignore()


def main():
    try:
        with open(sys.argv[1]) as f:
            license = f.read()
            BarcodeReader.init_license(
                license)
    except:
        BarcodeReader.init_license(
            "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    print(__doc__)
    main()
