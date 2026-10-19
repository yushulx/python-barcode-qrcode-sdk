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
import numpy as np

from PySide6.QtCore import QObject, QThread, Signal, Qt
import SnippingTool

class Worker(QObject):
    finished = Signal()
    progress = Signal(object)

    def __init__(self, manager, capture):
        super(Worker, self).__init__()
        self._barcodeManager = manager
        self._cap = capture
        self.isRunning = True

    def run(self):
        print('Running worker thread...')
        while self.isRunning:
            try:
                results = self._barcodeManager.decodeLatestFrame()

                if  results != None:
                    self.progress.emit(results)
            except Exception as e:
                print(e)
                break

        print('Quit worker thread...')
        self.finished.emit()


class MainWindow(QMainWindow):
    useQThread = True
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

        # Screenshot button
        self.snippingWidget = SnippingTool.SnippingWidget(app=QApplication.instance())
        self.snippingWidget.onSnippingCompleted = self.onSnippingCompleted
        self.ui.pushButton_area.clicked.connect(self.snipArea)
        self.ui.pushButton_full.clicked.connect(self.snipFull)
        
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
        self.mouse_x = 0
        self.mouse_y = 0
        self.endx = 0
        self.endy = 0
        self.clicked = False

        self.worker = None

    def onSnippingCompleted(self, frame):
        self.setWindowState(Qt.WindowState.WindowMaximized)
        if frame is None:
            return 

        frame, self._results = self._barcodeManager.decode_frame(frame)
        self.showResults(frame, self._results)

    def snipArea(self):
        self.setWindowState(Qt.WindowState.WindowMinimized)
        self.snippingWidget.start()    

    def snipFull(self):
        self.setWindowState(Qt.WindowState.WindowMinimized)
        self.snippingWidget.fullscreen()    

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        filename = urls[0].toLocalFile()
        self.loadFile(filename)
        self.decodeFile(filename)
        event.acceptProposedAction()
            
    def reportProgress(self, results):
        self._results = results

    # https://realpython.com/python-pyqt-qthread/
    def runLongTask(self):
        # Step 2: Create a QThread object
        self._thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker(self._barcodeManager, self._cap)
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self._thread)
        # Step 5: Connect signals and slots
        self._thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self.worker.progress.connect(self.reportProgress)
        # Step 6: Start the thread
        self._thread.start()

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

    def labelMouseReleaseEvent(self, ev):
        self.clicked = False

    def labelMousePressEvent(self, ev):
        self.clicked = True
        self.mouse_x = ev.position().x()
        self.mouse_y = ev.position().y()
        self.endx = self.mouse_x
        self.endy = self.mouse_y

    def labelMouseMoveEvent(self, ev):
        if self.clicked:
            self.endx = ev.position().x()
            self.endy = ev.position().y()

    def resetCoordinates(self):
        self.endx = self.mouse_x
        self.endy = self.mouse_y

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
            if not self.useQThread:
                self._barcodeManager.create_barcode_process()
            else:
                self._barcodeManager.initQueue()
                self.runLongTask()

        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameUpdate)
        self.timer.start(int(1000./24))

    def stopCamera(self):

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        if not self.ui.checkBox_syncdisplay.isChecked():
            if self.timer is not None:
                self.timer.stop()
                self.timer = None

            self._barcodeManager.destroy_barcode_process()
            if self.worker is not None:
                self.worker.isRunning = False
        else:
            if self.timer is not None:
                self.timer.stop()
                self.timer = None

        self._results = None

    def nextFrameUpdate(self):
        if self._cap is None:
            return
            
        ret, frame = self._cap.read()

        if not ret:
            self.showMessageBox('Error', 'Failed to get camera frame!')
            return

        if not self.ui.checkBox_syncdisplay.isChecked():
            self._barcodeManager.append_frame(frame)
            if not self.useQThread:
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

    def loadFile(self, filename):
        item = QListWidgetItem()
        item.setText(filename)
        self.ui.listWidget.addItem(item)
        self._all_data[filename] = None

    def appendFile(self, filename):
       
        if filename not in self._all_data:
            self.loadFile(filename)

    def currentItemChanged(self, current, previous):
        filename = current.text()
        self.decodeFile(filename)

    def setParameters(self):
        # Get template
        template = self.ui.textEdit_template.toPlainText()
        self._barcodeManager.set_template(template)

        # Get barcode types
        types = 0
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
            types |= EnumBarcodeFormat.BF_DOTCODE
        if (self.ui.checkBox_postalcode.isChecked()):
            types |= EnumBarcodeFormat.BF_POSTALCODE

        self._barcodeManager.set_barcode_types(types)

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
                                               self._path, QFileDialog.Option.ShowDirsOnly)
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
            if error[0] != EnumErrorCode.EC_OK:
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
        template_result = self._barcodeManager.get_template()
        with open(filename, 'w') as f:
            if isinstance(template_result, tuple) and len(template_result) >= 3:
                f.write(template_result[1])  # Assuming the JSON is in the second element
            else:
                f.write(str(template_result))

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
        thickness = 2
        color = (0, 255, 0)
        out = ''
        index = 0

        if results is not None and results[0] is not None:
            items_data = results[0]
            hasResults = False
            if isinstance(items_data, list):
                
                for item_data in items_data:
                    hasResults = True
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
                    hasResults = True
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
            
            if hasResults and self.ui.checkBox_autostop.isChecked():
                self.stopCamera()

        else:
            out = 'No barcode found'
            
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(
            frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_RGB888)
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
                                     msg, QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # self._painter.end()
            self.stopCamera()

            event.accept()
        else:
            event.ignore()


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

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    print(__doc__)
    main()
