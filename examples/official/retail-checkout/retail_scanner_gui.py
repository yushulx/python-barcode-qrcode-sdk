"""
retail_scanner_gui.py
---------------------
A professional point-of-sale style barcode scanner built with PySide6 and the
Dynamsoft Barcode Reader Bundle. It mirrors a real self-checkout station:

  * Scan from a live camera feed (overhead/handheld scanner simulation), or
  * Scan from an image file (e.g. a saved checkout-belt frame).

Decoded items accumulate into a "receipt" table, deduplicated, while live
bounding boxes are drawn over every barcode in the frame.

Run:  python retail_scanner_gui.py
"""

import os
import sys
import time

import cv2
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMainWindow,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from dynamsoft_barcode_reader_bundle import (
    CaptureVisionRouter, EnumBarcodeFormat, EnumErrorCode, EnumImagePixelFormat,
    EnumPresetTemplate, ImageData, LicenseManager,
)

# Public trial license. Request your own 30-day license at:
# https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform
LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="

# Symbologies that dominate retail checkout: the EAN/UPC family for products,
# GS1 DataBar for produce/coupons, Code 128 / GS1-128 for logistics, QR for loyalty.
RETAIL_FORMATS = (
    EnumBarcodeFormat.BF_ONED
    | EnumBarcodeFormat.BF_GS1_DATABAR
    | EnumBarcodeFormat.BF_QR_CODE
)


class RetailBarcodeEngine:
    """Wraps a CaptureVisionRouter configured for retail symbologies."""

    def __init__(self, license_key):
        err_code, err_str = LicenseManager.init_license(license_key)
        if err_code != EnumErrorCode.EC_OK and err_code != EnumErrorCode.EC_LICENSE_WARNING:
            raise RuntimeError(f"License initialization failed: {err_str}")
        self.cvr = CaptureVisionRouter()
        err_code, err_str, settings = self.cvr.get_simplified_settings(
            EnumPresetTemplate.PT_READ_BARCODES)
        settings.barcode_settings.barcode_format_ids = RETAIL_FORMATS
        settings.barcode_settings.expected_barcodes_count = 0
        self.cvr.update_settings(EnumPresetTemplate.PT_READ_BARCODES, settings)

    def decode_bgr(self, frame):
        """Decode a BGR numpy frame; return a list of {format, text, points}."""
        frame = np.ascontiguousarray(frame)
        image_data = ImageData(
            frame.tobytes(), frame.shape[1], frame.shape[0],
            frame.strides[0], EnumImagePixelFormat.IPF_RGB_888,
        )
        result = self.cvr.capture(image_data, EnumPresetTemplate.PT_READ_BARCODES)
        barcode_result = result.get_decoded_barcodes_result()
        items = []
        if barcode_result is not None:
            for item in barcode_result.get_items():
                location = item.get_location()
                points = [(p.x, p.y) for p in location.points]
                items.append({
                    "format": item.get_format_string(),
                    "text": item.get_text(),
                    "points": points,
                })
        return items


def draw_overlays(frame, items):
    """Draw green quadrilaterals and labels over each decoded barcode."""
    annotated = frame.copy()
    for item in items:
        pts = np.array(item["points"], dtype=np.int32)
        cv2.polylines(annotated, [pts], True, (0, 200, 0), 3)
        x, y = pts[0]
        label = item["format"]
        cv2.putText(annotated, label, (int(x), int(y) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
    return annotated


def bgr_to_qimage(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    return QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()


class CameraWorker(QThread):
    """Grabs camera frames, decodes each one, and emits annotated results."""

    frame_ready = Signal(QImage, list)

    def __init__(self, engine, cam_index=0):
        super().__init__()
        self.engine = engine
        self.cam_index = cam_index
        self._running = False

    def run(self):
        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            return
        self._running = True
        while self._running:
            ok, frame = cap.read()
            if not ok:
                break
            items = self.engine.decode_bgr(frame)
            annotated = draw_overlays(frame, items)
            self.frame_ready.emit(bgr_to_qimage(annotated), items)
        cap.release()

    def stop(self):
        self._running = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.camera = None
        self.seen = set()

        self.setWindowTitle("Dynamsoft Retail Checkout Scanner")
        self.resize(1180, 720)

        # --- Left: live preview ---
        self.preview = QLabel("Open an image or start the camera to scan")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumWidth(740)
        self.preview.setStyleSheet(
            "background:#1b1f27; color:#9aa4b2; border-radius:8px; font-size:15px;")

        self.open_btn = QPushButton("Open Image")
        self.camera_btn = QPushButton("Start Camera")
        self.clear_btn = QPushButton("Clear Receipt")
        for b in (self.open_btn, self.camera_btn, self.clear_btn):
            b.setMinimumHeight(40)
            b.setCursor(Qt.PointingHandCursor)
        self.open_btn.clicked.connect(self.open_image)
        self.camera_btn.clicked.connect(self.toggle_camera)
        self.clear_btn.clicked.connect(self.clear_receipt)

        controls = QHBoxLayout()
        controls.addWidget(self.open_btn)
        controls.addWidget(self.camera_btn)
        controls.addWidget(self.clear_btn)

        left = QVBoxLayout()
        left.addWidget(self.preview, 1)
        left.addLayout(controls)

        # --- Right: receipt ---
        header = QLabel("Scanned Items")
        header.setStyleSheet("font-size:18px; font-weight:600; padding:6px 0;")
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Symbology", "Content"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.count_label = QLabel("0 unique items")
        self.count_label.setStyleSheet("color:#5b6472; padding-top:6px;")

        right = QVBoxLayout()
        right.addWidget(header)
        right.addWidget(self.table, 1)
        right.addWidget(self.count_label)

        root = QHBoxLayout()
        root.addLayout(left, 3)
        root.addLayout(right, 2)
        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open checkout image", "images",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not path:
            return
        frame = cv2.imread(path)
        if frame is None:
            return
        items = self.engine.decode_bgr(frame)
        annotated = draw_overlays(frame, items)
        self.show_frame(bgr_to_qimage(annotated))
        for item in items:
            self.add_to_receipt(item)

    def toggle_camera(self):
        if self.camera is None:
            self.camera = CameraWorker(self.engine)
            self.camera.frame_ready.connect(self.on_frame)
            self.camera.start()
            self.camera_btn.setText("Stop Camera")
        else:
            self.camera.stop()
            self.camera = None
            self.camera_btn.setText("Start Camera")

    def on_frame(self, qimage, items):
        self.show_frame(qimage)
        for item in items:
            self.add_to_receipt(item)

    def show_frame(self, qimage):
        pixmap = QPixmap.fromImage(qimage).scaled(
            self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview.setPixmap(pixmap)

    def add_to_receipt(self, item):
        key = (item["format"], item["text"])
        if key in self.seen:
            return
        self.seen.add(key)
        row = self.table.rowCount()
        self.table.insertRow(row)
        fmt_item = QTableWidgetItem(item["format"])
        fmt_item.setForeground(QColor("#1d8a4a"))
        self.table.setItem(row, 0, fmt_item)
        self.table.setItem(row, 1, QTableWidgetItem(item["text"]))
        self.count_label.setText(f"{len(self.seen)} unique items")

    def clear_receipt(self):
        self.seen.clear()
        self.table.setRowCount(0)
        self.count_label.setText("0 unique items")

    def closeEvent(self, event):
        if self.camera is not None:
            self.camera.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    try:
        engine = RetailBarcodeEngine(LICENSE_KEY)
    except RuntimeError as exc:
        QLabel(str(exc)).show()
        print(exc)
        return
    window = MainWindow(engine)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
