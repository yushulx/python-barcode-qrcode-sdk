# Refer to https://github.com/harupy/snipping-tool
import numpy as np
import cv2
from PIL import ImageGrab
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt


class SnippingWidget(QtWidgets.QWidget):
    is_snipping = False

    def __init__(self, parent=None, app=None):
        super(SnippingWidget, self).__init__()
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.screen = app.primaryScreen()
        self.setGeometry(0, 0, self.screen.size().width(),
                         self.screen.size().height())
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.onSnippingCompleted = None

    def fullscreen(self):
        img = ImageGrab.grab(
            bbox=(0, 0, self.screen.size().width(), self.screen.size().height()))

        try:
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except:
            img = None

        if self.onSnippingCompleted is not None:
            self.onSnippingCompleted(img)

    def start(self):
        SnippingWidget.is_snipping = True
        self.setWindowOpacity(0.3)
        QtWidgets.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.show()

    def paintEvent(self, event):
        if SnippingWidget.is_snipping:
            brush_color = (128, 128, 255, 100)
            lw = 3
            opacity = 0.3
        else:
            self.begin = QtCore.QPoint()
            self.end = QtCore.QPoint()
            brush_color = (0, 0, 0, 0)
            lw = 0
            opacity = 0

        self.setWindowOpacity(opacity)
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('black'), lw))
        qp.setBrush(QtGui.QColor(*brush_color))
        rect = QtCore.QRectF(self.begin, self.end)
        qp.drawRect(rect)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        SnippingWidget.is_snipping = False
        QtWidgets.QApplication.restoreOverrideCursor()
        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        self.repaint()
        QtWidgets.QApplication.processEvents()
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

        try:
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except:
            img = None

        if self.onSnippingCompleted is not None:
            self.onSnippingCompleted(img)

        self.close()
