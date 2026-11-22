import sys
import os
import json
import numpy as np
import cv2
import zxingcpp

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QGraphicsView, QGraphicsScene, QGraphicsPolygonItem,
    QGraphicsEllipseItem, QGraphicsLineItem,
    QMessageBox, QLabel, QProgressBar, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox, QGroupBox, QComboBox,
    QAbstractItemView, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QPointF, QRectF, QThread, Signal
from PySide6.QtGui import (
    QImage, QPixmap, QPolygonF, QPen, QColor, QFont, QPainter, QBrush
)

from dynamsoft_barcode_reader_bundle import (
    LicenseManager, CaptureVisionRouter, EnumPresetTemplate, EnumErrorCode
)

# ---------------------------------------------------------------------------
# License
# ---------------------------------------------------------------------------
LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="

err, msg = LicenseManager.init_license(LICENSE_KEY)
if err not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_CACHE_USED):
    print(f"[DBR] License warning: {msg}")


# ---------------------------------------------------------------------------
# Single-popup barcode edit dialog
# ---------------------------------------------------------------------------
class BarcodeEditDialog(QDialog):
    FORMATS = [
        "QRCode", "Code128", "Code39", "EAN13", "EAN8", "UPCA", "UPCE",
        "DataMatrix", "PDF417", "Aztec", "ITF", "Codabar", "Code93",
        "GS1_128", "GS1_DataBar", "MaxiCode", "Unknown",
    ]

    def __init__(self, text="", fmt="Unknown", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Barcode Annotation")
        self.setMinimumWidth(420)
        layout = QFormLayout(self)

        self.text_edit = QLineEdit(text)
        layout.addRow("Text:", self.text_edit)

        self.fmt_combo = QComboBox()
        self.fmt_combo.setEditable(True)
        self.fmt_combo.addItems(self.FORMATS)
        idx = self.fmt_combo.findText(fmt, Qt.MatchFixedString)
        if idx >= 0:
            self.fmt_combo.setCurrentIndex(idx)
        else:
            self.fmt_combo.setCurrentText(fmt)
        layout.addRow("Format:", self.fmt_combo)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)


# ---------------------------------------------------------------------------
# EXIF-aware image loading via OpenCV
# ---------------------------------------------------------------------------
def load_image_cv(path):
    """Load image with cv2.IMREAD_COLOR and auto-orient via EXIF.
    cv2.imread with IMREAD_COLOR + IMREAD_IGNORE_ORIENTATION ignores EXIF,
    so we use IMREAD_COLOR_RGB | IMREAD_UNCHANGED first, then manually rotate.
    Actually, OpenCV's imread by default ignores EXIF orientation.
    We use cv2.IMREAD_UNCHANGED and handle orientation from EXIF ourselves.
    The simplest robust approach: use IMREAD_COLOR which ignores EXIF, then
    re-read with IMREAD_ANYCOLOR | IMREAD_ANYDEPTH via a workaround.
    Best approach: use cv2.VideoCapture or PIL for EXIF, but to keep deps
    minimal we read EXIF orientation tag manually.
    """
    # Read raw bytes to preserve EXIF, then decode
    raw = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if img is None:
        return None

    # Try to read EXIF orientation
    orientation = _get_exif_orientation(raw)
    if orientation == 3:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif orientation == 6:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif orientation == 8:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


def _get_exif_orientation(data):
    """Extract EXIF orientation tag from raw JPEG/TIFF bytes.
    Returns orientation int (1-8) or 1 if not found.
    """
    try:
        # JPEG: starts with FF D8, EXIF APP1 marker FF E1
        if len(data) < 12:
            return 1
        if data[0] == 0xFF and data[1] == 0xD8:
            idx = 2
            while idx < len(data) - 1:
                if data[idx] != 0xFF:
                    break
                marker = data[idx + 1]
                if marker == 0xE1:  # APP1 (EXIF)
                    # Length of this segment
                    seg_len = int(data[idx + 2]) << 8 | int(data[idx + 3])
                    exif_data = data[idx + 4 : idx + 2 + seg_len]
                    return _parse_exif_orientation(exif_data)
                else:
                    seg_len = int(data[idx + 2]) << 8 | int(data[idx + 3])
                    idx += 2 + seg_len
    except Exception:
        pass
    return 1


def _parse_exif_orientation(exif_data):
    """Parse orientation from EXIF APP1 payload."""
    try:
        if len(exif_data) < 14:
            return 1
        # Check for 'Exif\x00\x00'
        if exif_data[:4] != b'Exif' or exif_data[4:6] != b'\x00\x00':
            return 1
        tiff = exif_data[6:]
        if len(tiff) < 8:
            return 1
        # Byte order
        if tiff[0:2] == b'MM':
            big_endian = True
        elif tiff[0:2] == b'II':
            big_endian = False
        else:
            return 1

        def read_u16(d, off):
            if big_endian:
                return (d[off] << 8) | d[off + 1]
            return d[off] | (d[off + 1] << 8)

        def read_u32(d, off):
            if big_endian:
                return (d[off] << 24) | (d[off+1] << 16) | (d[off+2] << 8) | d[off+3]
            return d[off] | (d[off+1] << 8) | (d[off+2] << 16) | (d[off+3] << 24)

        ifd_offset = read_u32(tiff, 4)
        if ifd_offset + 2 > len(tiff):
            return 1
        num_entries = read_u16(tiff, ifd_offset)
        for i in range(num_entries):
            entry_off = ifd_offset + 2 + i * 12
            if entry_off + 12 > len(tiff):
                break
            tag = read_u16(tiff, entry_off)
            if tag == 0x0112:  # Orientation
                return read_u16(tiff, entry_off + 8)
    except Exception:
        pass
    return 1


def cv_to_qpixmap(cv_img):
    """Convert a BGR OpenCV image to QPixmap."""
    h, w = cv_img.shape[:2]
    if len(cv_img.shape) == 2:
        qimg = QImage(cv_img.data, w, h, w, QImage.Format_Grayscale8)
    else:
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


# ---------------------------------------------------------------------------
# Draggable vertex handle for quad corners
# ---------------------------------------------------------------------------
HANDLE_RADIUS = 6


class DraggableVertex(QGraphicsEllipseItem):
    """Small circle handle the user can drag to adjust a quad corner."""

    def __init__(self, annotation, point_index, redraw_cb, parent=None):
        r = HANDLE_RADIUS
        super().__init__(-r, -r, 2 * r, 2 * r, parent)
        self.annotation = annotation
        self._idx = point_index
        self._redraw = redraw_cb
        self.setBrush(QBrush(QColor(255, 255, 0, 180)))
        self.setPen(QPen(QColor(0, 0, 0), 1))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.SizeAllCursor)
        self.setZValue(50)
        x, y = annotation["points"][point_index]
        self.setPos(x, y)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionHasChanged:
            pos = value
            self.annotation["points"][self._idx] = (pos.x(), pos.y())
            self._redraw()
        return super().itemChange(change, value)


# ---------------------------------------------------------------------------
# Clickable polygon overlay
# ---------------------------------------------------------------------------
class SelectablePolygon(QGraphicsPolygonItem):
    def __init__(self, annotation, redraw_cb, delete_cb, parent=None):
        super().__init__(parent)
        self.annotation = annotation
        self._redraw = redraw_cb
        self._delete = delete_cb
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            dlg = BarcodeEditDialog(
                text=self.annotation["text"],
                fmt=self.annotation["format"],
            )
            if dlg.exec() == QDialog.Accepted:
                self.annotation["text"] = dlg.text_edit.text()
                self.annotation["format"] = dlg.fmt_combo.currentText()
                self._redraw()
        elif event.button() == Qt.RightButton:
            reply = QMessageBox.question(
                None, "Delete Annotation",
                f'Delete barcode "{self.annotation["text"]}"?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._delete(self.annotation)
        else:
            super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Graphics view with interactive quad draw mode, crop mode, scroll-wheel zoom, D&D
# ---------------------------------------------------------------------------
CLOSE_THRESHOLD = 12  # pixels – click within this distance of P1 to close


class DrawableGraphicsView(QGraphicsView):
    quad_drawn = Signal(list)          # list of (x,y) tuples
    crop_drawn = Signal(QRectF)        # bounding rect from drag
    files_dropped = Signal(list)       # list of file paths

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._draw_mode = False
        self._crop_mode = False
        self._click_pts = []           # settled scene-coord QPointFs
        self._preview_items = []       # temp graphics items (dots, lines)
        self._rubber_line = None       # the dynamic line following cursor
        self._crop_start = None        # start point for crop rect drag
        self._crop_rect_item = None    # live rubber-band rect item
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

    # -- mode toggles --
    def set_draw_mode(self, enabled):
        self._draw_mode = enabled
        self._clear_preview()
        self._click_pts.clear()
        if enabled:
            if self._crop_mode:
                self._crop_mode = False
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        else:
            if not self._crop_mode:
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                self.unsetCursor()

    def set_crop_mode(self, enabled):
        self._crop_mode = enabled
        self._crop_start = None
        if self._crop_rect_item and self._crop_rect_item.scene():
            self.scene().removeItem(self._crop_rect_item)
        self._crop_rect_item = None
        if enabled:
            if self._draw_mode:
                self._draw_mode = False
                self._clear_preview()
                self._click_pts.clear()
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        else:
            if not self._draw_mode:
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                self.unsetCursor()

    # -- draw-mode preview helpers --
    def _clear_preview(self):
        for item in self._preview_items:
            if item.scene():
                self.scene().removeItem(item)
        self._preview_items.clear()
        if self._rubber_line and self._rubber_line.scene():
            self.scene().removeItem(self._rubber_line)
        self._rubber_line = None

    def _redraw_settled(self):
        """Redraw settled dots and lines between confirmed points."""
        self._clear_preview()
        pen = QPen(QColor(255, 165, 0), 2, Qt.SolidLine)
        dot_pen = QPen(QColor(255, 165, 0), 1)
        dot_brush = QBrush(QColor(255, 165, 0, 180))
        close_pen = QPen(QColor(0, 255, 0), 1)
        close_brush = QBrush(QColor(0, 255, 0, 120))
        r = 4
        cr = CLOSE_THRESHOLD
        for i, pt in enumerate(self._click_pts):
            if i == 0 and len(self._click_pts) >= 3:
                ring = self.scene().addEllipse(
                    pt.x() - cr, pt.y() - cr, 2 * cr, 2 * cr,
                    close_pen, close_brush
                )
                ring.setZValue(99)
                self._preview_items.append(ring)
            dot = self.scene().addEllipse(
                pt.x() - r, pt.y() - r, 2 * r, 2 * r,
                dot_pen, dot_brush
            )
            dot.setZValue(100)
            self._preview_items.append(dot)
            if i > 0:
                line = self.scene().addLine(
                    self._click_pts[i - 1].x(), self._click_pts[i - 1].y(),
                    pt.x(), pt.y(), pen
                )
                line.setZValue(100)
                self._preview_items.append(line)

    def _update_rubber_line(self, scene_pos):
        """Draw/update the dynamic dashed line from last point to cursor."""
        if self._rubber_line and self._rubber_line.scene():
            self.scene().removeItem(self._rubber_line)
            self._rubber_line = None
        if not self._click_pts:
            return
        last = self._click_pts[-1]
        pen = QPen(QColor(255, 165, 0), 2, Qt.DashLine)
        self._rubber_line = self.scene().addLine(
            last.x(), last.y(), scene_pos.x(), scene_pos.y(), pen
        )
        self._rubber_line.setZValue(100)

    def _is_near_first(self, pt):
        if len(self._click_pts) < 3:
            return False
        first = self._click_pts[0]
        vp = self.mapFromScene(pt)
        vf = self.mapFromScene(first)
        dx = vp.x() - vf.x()
        dy = vp.y() - vf.y()
        return (dx * dx + dy * dy) <= CLOSE_THRESHOLD * CLOSE_THRESHOLD

    # -- mouse events --
    def mousePressEvent(self, event):
        if self._draw_mode and event.button() == Qt.LeftButton:
            pt = self.mapToScene(event.pos())
            if self._is_near_first(pt):
                quad = [(p.x(), p.y()) for p in self._click_pts]
                self._clear_preview()
                self._click_pts.clear()
                self.quad_drawn.emit(quad)
                return
            self._click_pts.append(pt)
            self._redraw_settled()
        elif self._draw_mode and event.button() == Qt.RightButton:
            self._clear_preview()
            self._click_pts.clear()
        elif self._crop_mode and event.button() == Qt.LeftButton:
            self._crop_start = self.mapToScene(event.pos())
            pen = QPen(QColor(0, 180, 255), 2, Qt.DashLine)
            self._crop_rect_item = self.scene().addRect(
                QRectF(self._crop_start, self._crop_start), pen
            )
            self._crop_rect_item.setZValue(100)
        elif self._crop_mode and event.button() == Qt.RightButton:
            # cancel current crop drag
            if self._crop_rect_item and self._crop_rect_item.scene():
                self.scene().removeItem(self._crop_rect_item)
            self._crop_rect_item = None
            self._crop_start = None
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._draw_mode and self._click_pts:
            self._update_rubber_line(self.mapToScene(event.pos()))
        elif self._crop_mode and self._crop_start is not None and self._crop_rect_item:
            cur = self.mapToScene(event.pos())
            self._crop_rect_item.setRect(
                QRectF(self._crop_start, cur).normalized()
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._crop_mode and event.button() == Qt.LeftButton and self._crop_start is not None:
            end = self.mapToScene(event.pos())
            rect = QRectF(self._crop_start, end).normalized()
            if self._crop_rect_item and self._crop_rect_item.scene():
                self.scene().removeItem(self._crop_rect_item)
            self._crop_rect_item = None
            self._crop_start = None
            if rect.width() > 4 and rect.height() > 4:
                self.crop_drawn.emit(rect)
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        self.scale(factor, factor)

    # -- drag & drop into view --
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                local = url.toLocalFile()
                if os.path.isdir(local):
                    for root_dir, _, files in os.walk(local):
                        for f in files:
                            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")):
                                paths.append(os.path.join(root_dir, f))
                elif local.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")):
                    paths.append(local)
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# ---------------------------------------------------------------------------
# Background detection worker
# ---------------------------------------------------------------------------
class DetectionWorker(QThread):
    progress = Signal(int, int)        # done, total
    file_done = Signal(str, list)      # abs_path, annotations

    def __init__(self, file_paths, template_path=None, template_name=None, parent=None):
        super().__init__(parent)
        self._files = list(file_paths)
        self._template_path = template_path
        self._template_name = template_name or EnumPresetTemplate.PT_READ_BARCODES.value

    def run(self):
        router = CaptureVisionRouter()
        if self._template_path:
            err, msg = router.init_settings_from_file(self._template_path)
            if err != 0:
                print(f"[DBR] Template load failed ({err}): {msg}")
        total = len(self._files)
        for i, path in enumerate(self._files):
            anns = self._detect(router, path)
            self.file_done.emit(path, anns)
            self.progress.emit(i + 1, total)

    def _detect(self, router, path):
        dbr_items = []
        try:
            result = router.capture(path, self._template_name)
            if result:
                dbr_r = result.get_decoded_barcodes_result()
                if dbr_r:
                    for item in (dbr_r.get_items() or []):
                        pts = item.get_location().points
                        dbr_items.append({
                            "text":   item.get_text(),
                            "format": item.get_format_string(),
                            "points": [(p.x, p.y) for p in pts],
                        })
        except Exception as exc:
            print(f"[DBR] {exc}")

        zxing_items = []
        try:
            img = cv2.imread(path)
            if img is not None:
                for zx in zxingcpp.read_barcodes(img):
                    pos = zx.position
                    zxing_items.append({
                        "text":   zx.text,
                        "format": zx.format.name,
                        "points": [
                            (pos.top_left.x,     pos.top_left.y),
                            (pos.top_right.x,    pos.top_right.y),
                            (pos.bottom_right.x, pos.bottom_right.y),
                            (pos.bottom_left.x,  pos.bottom_left.y),
                        ],
                    })
        except Exception as exc:
            print(f"[ZXing] {exc}")

        # Build merged annotation list, keeping per-engine results
        zxing_text_set = {r["text"] for r in zxing_items}
        dbr_text_set = {r["text"] for r in dbr_items}

        # Map zxing items by text for pairing
        zxing_by_text = {}
        for r in zxing_items:
            zxing_by_text.setdefault(r["text"], []).append(r)

        anns = []
        used_zxing_texts = set()
        for r in dbr_items:
            match = r["text"] in zxing_text_set
            zxing_pair = None
            if match and r["text"] in zxing_by_text and zxing_by_text[r["text"]]:
                zxing_pair = zxing_by_text[r["text"]].pop(0)
                used_zxing_texts.add(r["text"])
            anns.append({
                **r,
                "match":  match,
                "source": "dbr",
                "dbr":    {"text": r["text"], "format": r["format"], "points": r["points"]},
                "zxing":  {"text": zxing_pair["text"], "format": zxing_pair["format"],
                           "points": zxing_pair["points"]} if zxing_pair else None,
            })
        for r in zxing_items:
            if r["text"] not in dbr_text_set:
                anns.append({
                    **r,
                    "match":  False,
                    "source": "zxing",
                    "dbr":    None,
                    "zxing":  {"text": r["text"], "format": r["format"], "points": r["points"]},
                })
        return anns


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class AnnotationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Barcode Annotation Tool")
        self.resize(1440, 860)
        self.setAcceptDrops(True)

        self._files = {}           # abs_path -> {"annotations": list|None}
        self._all_paths = []       # insertion-ordered list of abs paths
        self._current_path = None
        self._poly_items = {}      # ann_index -> SelectablePolygon
        self._handle_items = []    # DraggableVertex list
        self._worker = None
        self._pending_paths = []   # paths queued while worker is busy

        # DBR template – None means use the SDK default template
        self._active_template_path = None
        self._active_template_name = EnumPresetTemplate.PT_READ_BARCODES.value

        # Workers for per-image re-detection (No Result list)
        self._redetect_workers = []

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # ---- Toolbar row ------------------------------------------------
        tb = QHBoxLayout()
        self._btn_files = QPushButton("Load Files...")
        self._btn_files.clicked.connect(self._load_files)
        self._btn_folder = QPushButton("Load Folder...")
        self._btn_folder.clicked.connect(self._load_folder)
        self._btn_import = QPushButton("Import JSON")
        self._btn_import.setToolTip(
            "Load a barcode-benchmark/1.0 JSON file and apply its annotations "
            "to already-loaded images (matched by filename)."
        )
        self._btn_import.clicked.connect(self._import_json)

        self._btn_export = QPushButton("Export JSON")
        self._btn_export.clicked.connect(self._export_json)

        self._prog_label = QLabel("")
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)
        self._progress.setFixedHeight(18)

        self._btn_delete = QPushButton("Delete Image")
        self._btn_delete.clicked.connect(self._delete_current)
        self._btn_delete_all = QPushButton("Delete All")
        self._btn_delete_all.clicked.connect(self._delete_all)

        self._btn_verify = QPushButton("✔ Verify")
        self._btn_verify.setToolTip(
            "Mark the current image as Verified and move it to the Verified list."
        )
        self._btn_verify.clicked.connect(self._verify_current)

        self._btn_save_verified = QPushButton("Save Verified Dataset")
        self._btn_save_verified.setToolTip(
            "Copy all Verified images and their annotations to a target folder."
        )
        self._btn_save_verified.clicked.connect(self._save_verified_dataset)

        self._btn_tmpl_export = QPushButton("Export DBR Template")
        self._btn_tmpl_export.setToolTip(
            "Export the current DBR template to a JSON file for editing."
        )
        self._btn_tmpl_export.clicked.connect(self._export_dbr_template)

        self._btn_tmpl_import = QPushButton("Import DBR Template")
        self._btn_tmpl_import.setToolTip(
            "Load a custom DBR template JSON file — "
            "all subsequent captures will use it."
        )
        self._btn_tmpl_import.clicked.connect(self._import_dbr_template)

        self._btn_tmpl_reset = QPushButton("Reset Template")
        self._btn_tmpl_reset.setToolTip("Revert to the built-in default DBR template.")
        self._btn_tmpl_reset.clicked.connect(self._reset_dbr_template)
        self._btn_tmpl_reset.setVisible(False)   # shown only when a custom template is loaded

        tb.addWidget(self._btn_files)
        tb.addWidget(self._btn_folder)
        tb.addWidget(self._btn_import)
        tb.addWidget(self._btn_export)
        tb.addWidget(self._btn_delete)
        tb.addWidget(self._btn_delete_all)
        tb.addWidget(self._btn_verify)
        tb.addWidget(self._btn_save_verified)
        tb.addSpacing(10)
        tb.addWidget(self._btn_tmpl_export)
        tb.addWidget(self._btn_tmpl_import)
        tb.addWidget(self._btn_tmpl_reset)
        tb.addSpacing(10)
        tb.addWidget(self._prog_label)
        tb.addWidget(self._progress, 1)
        root.addLayout(tb)

        # ---- Three-column splitter --------------------------------------
        splitter = QSplitter(Qt.Horizontal)

        # -- Left: file zone lists ----------------------------------------
        left = QWidget()
        left.setMinimumWidth(200)
        left.setMaximumWidth(300)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 4, 0)
        lv.setSpacing(6)

        self._grp_verified = QGroupBox("Verified (0)")
        gv = QVBoxLayout(self._grp_verified)
        gv.setContentsMargins(4, 4, 4, 4)
        self._list_verified = QListWidget()
        self._list_verified.itemClicked.connect(
            lambda item: self._select_file(item.data(Qt.UserRole))
        )
        gv.addWidget(self._list_verified)

        self._grp_review = QGroupBox("Needs Review (0)")
        gr = QVBoxLayout(self._grp_review)
        gr.setContentsMargins(4, 4, 4, 4)
        self._list_review = QListWidget()
        self._list_review.itemClicked.connect(
            lambda item: self._select_file(item.data(Qt.UserRole))
        )
        gr.addWidget(self._list_review)

        self._grp_noresult = QGroupBox("No Result (0)")
        gn = QVBoxLayout(self._grp_noresult)
        gn.setContentsMargins(4, 4, 4, 4)
        self._list_noresult = QListWidget()
        self._list_noresult.itemClicked.connect(self._on_noresult_item_clicked)
        gn.addWidget(self._list_noresult)

        lv.addWidget(self._grp_verified, 1)
        lv.addWidget(self._grp_review, 1)
        lv.addWidget(self._grp_noresult, 1)

        # status / drop hint
        self._status_lbl = QLabel("Drop images or folders anywhere, or use the buttons above.")
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setStyleSheet("color:gray;font-size:11px;")
        lv.addWidget(self._status_lbl)

        # -- Center: image view + nav bar ---------------------------------
        center = QWidget()
        cv = QVBoxLayout(center)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(2)

        self._scene = QGraphicsScene()
        self._view = DrawableGraphicsView(self._scene)
        self._view.quad_drawn.connect(self._on_quad_drawn)
        self._view.crop_drawn.connect(self._on_crop_drawn)
        self._view.files_dropped.connect(self._add_paths)
        cv.addWidget(self._view, 1)

        nav = QHBoxLayout()
        self._btn_prev = QPushButton("< Prev")
        self._btn_prev.setFixedWidth(70)
        self._btn_prev.clicked.connect(self._prev_image)
        self._btn_next = QPushButton("Next >")
        self._btn_next.setFixedWidth(70)
        self._btn_next.clicked.connect(self._next_image)
        self._nav_label = QLabel("0 / 0")
        self._nav_label.setAlignment(Qt.AlignCenter)

        self._btn_crop = QPushButton("Crop Mode  [C]")
        self._btn_crop.setCheckable(True)
        self._btn_crop.setFixedWidth(130)
        self._btn_crop.toggled.connect(self._on_crop_mode_toggled)

        self._btn_draw = QPushButton("Draw Mode  [D]")
        self._btn_draw.setCheckable(True)
        self._btn_draw.setFixedWidth(130)
        self._btn_draw.toggled.connect(self._on_draw_mode_toggled)

        nav.addWidget(self._btn_prev)
        nav.addStretch(1)
        nav.addWidget(self._nav_label)
        nav.addStretch(1)
        nav.addWidget(self._btn_next)
        nav.addSpacing(16)
        nav.addWidget(self._btn_crop)
        nav.addWidget(self._btn_draw)
        cv.addLayout(nav)

        # -- Right: barcode results panel ---------------------------------
        right = QWidget()
        right.setMinimumWidth(320)
        right.setMaximumWidth(480)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 0, 0, 0)

        grp_b = QGroupBox("Detected Barcodes")
        gb = QVBoxLayout(grp_b)
        gb.setContentsMargins(4, 4, 4, 4)

        legend = QLabel(
            "<span style='color:green'>Green</span> = both SDKs agree &nbsp;"
            "<span style='color:red'>Red</span> = mismatch / single SDK / manual"
        )
        legend.setWordWrap(True)
        legend.setStyleSheet("font-size:11px;")
        gb.addWidget(legend)

        self._tree_barcodes = QTreeWidget()
        self._tree_barcodes.setHeaderLabels(["Property", "Value"])
        self._tree_barcodes.header().setStretchLastSection(True)
        self._tree_barcodes.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._tree_barcodes.setIndentation(16)
        self._tree_barcodes.setStyleSheet("font-size:11px;")
        self._tree_barcodes.itemClicked.connect(self._on_barcode_tree_clicked)
        gb.addWidget(self._tree_barcodes)

        rv.addWidget(grp_b, 1)

        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        root.addWidget(splitter, 1)
        self.statusBar().showMessage("Ready. Drop images/folders or use Load buttons.")

    # ------------------------------------------------------------------
    # Drag-and-drop (main window level)
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if os.path.isdir(local):
                for root, _, files in os.walk(local):
                    for f in files:
                        if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")):
                            paths.append(os.path.join(root, f))
            elif local.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")):
                paths.append(local)
        self._add_paths(paths)
        event.acceptProposedAction()

    # ------------------------------------------------------------------
    # File loading
    # ------------------------------------------------------------------
    def _load_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp)"
        )
        self._add_paths(paths)

    def _load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        paths = []
        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")):
                    paths.append(os.path.join(root, f))
        self._add_paths(paths)

    def _add_paths(self, paths):
        existing = set(self._files.keys())
        new = [p for p in paths if p not in existing]
        if not new:
            return
        for p in new:
            self._files[p] = {"annotations": None}
            self._all_paths.append(p)
        self._status_lbl.setText(f"{len(self._all_paths)} image(s) loaded.")
        self._run_detection(new)

    # ------------------------------------------------------------------
    # Background detection
    # ------------------------------------------------------------------
    def _run_detection(self, paths):
        if self._worker and self._worker.isRunning():
            self._pending_paths.extend(paths)
            return

        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._progress.setMaximum(len(paths))
        self._prog_label.setText("Detecting...")
        self._btn_files.setEnabled(False)
        self._btn_folder.setEnabled(False)

        self._worker = DetectionWorker(
            paths,
            template_path=self._active_template_path,
            template_name=self._active_template_name,
        )
        self._worker.file_done.connect(self._on_file_detected)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_detection_done)
        self._worker.start()

    def _on_file_detected(self, path, annotations):
        self._files[path]["annotations"] = annotations
        filename = os.path.basename(path)

        item = QListWidgetItem(filename)
        item.setData(Qt.UserRole, path)
        if len(annotations) == 0:
            item.setForeground(QColor(120, 120, 120))
            self._list_noresult.addItem(item)
        elif all(a.get("match") for a in annotations):
            item.setForeground(QColor(0, 130, 0))
            self._list_verified.addItem(item)
        else:
            item.setForeground(QColor(180, 0, 0))
            self._list_review.addItem(item)

        self._grp_verified.setTitle(f"Verified ({self._list_verified.count()})")
        self._grp_review.setTitle(f"Needs Review ({self._list_review.count()})")
        self._grp_noresult.setTitle(f"No Result ({self._list_noresult.count()})")

        # Auto-show first image as soon as it arrives
        if self._current_path is None:
            self._select_file(path)

    def _on_progress(self, done, total):
        self._progress.setMaximum(total)
        self._progress.setValue(done)
        self._prog_label.setText(f"Detecting... {done}/{total}")

    def _on_detection_done(self):
        self._progress.setVisible(False)
        self._prog_label.setText("")
        self._btn_files.setEnabled(True)
        self._btn_folder.setEnabled(True)
        self.statusBar().showMessage(
            f"Detection complete. "
            f"Verified: {self._list_verified.count()}  |  "
            f"Needs Review: {self._list_review.count()}  |  "
            f"No Result: {self._list_noresult.count()}"
        )

        if self._pending_paths:
            batch = list(self._pending_paths)
            self._pending_paths.clear()
            self._run_detection(batch)

    # ------------------------------------------------------------------
    # No-Result re-detection on click
    # ------------------------------------------------------------------
    def _on_noresult_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        self._select_file(path)
        # Re-run detection with the active template every time this image is selected
        self._redetect_single(path)

    def _redetect_single(self, path):
        """Run detection on one file in the background; move it out of No Result if found."""
        worker = DetectionWorker(
            [path],
            template_path=self._active_template_path,
            template_name=self._active_template_name,
        )
        worker.file_done.connect(self._on_redetect_file_done)
        worker.finished.connect(lambda w=worker: self._redetect_workers.remove(w))
        self._redetect_workers.append(worker)
        worker.start()

    def _on_redetect_file_done(self, path, annotations):
        if not annotations:
            self.statusBar().showMessage(
                "Re-detection: still no barcodes found.  "
                "Try a different template or draw manually.", 5000
            )
            return

        # Update stored annotations
        self._files[path]["annotations"] = annotations

        # Remove from No Result list
        for i in range(self._list_noresult.count()):
            if self._list_noresult.item(i).data(Qt.UserRole) == path:
                self._list_noresult.takeItem(i)
                break

        # Add to Verified or Needs Review
        filename = os.path.basename(path)
        item = QListWidgetItem(filename)
        item.setData(Qt.UserRole, path)
        if all(a.get("match") for a in annotations):
            item.setForeground(QColor(0, 130, 0))
            self._list_verified.addItem(item)
            dest = "Verified"
        else:
            item.setForeground(QColor(180, 0, 0))
            self._list_review.addItem(item)
            dest = "Needs Review"

        self._grp_verified.setTitle(f"Verified ({self._list_verified.count()})")
        self._grp_review.setTitle(f"Needs Review ({self._list_review.count()})")
        self._grp_noresult.setTitle(f"No Result ({self._list_noresult.count()})")

        # Refresh the highlighted item so the new list row is selected
        self._highlight_list_item(path)

        # If the re-detected image is currently displayed, redraw annotations
        if path == self._current_path:
            self._redraw(path)

        self.statusBar().showMessage(
            f"Re-detection found {len(annotations)} barcode(s) — moved to {dest}.", 5000
        )

    # ------------------------------------------------------------------
    # Image selection & display
    # ------------------------------------------------------------------
    def _select_file(self, path):
        self._current_path = path
        self._show_image(path)
        self._update_nav()
        self._highlight_list_item(path)

    def _show_image(self, path):
        self._scene.clear()
        self._poly_items = {}
        self._handle_items = []
        cv_img = load_image_cv(path)
        if cv_img is None:
            self._status_lbl.setText(f"Cannot load: {os.path.basename(path)}")
            return
        pxmap = cv_to_qpixmap(cv_img)
        self._scene.addPixmap(pxmap)
        self._scene.setSceneRect(QRectF(pxmap.rect()))

        anns = (self._files.get(path) or {}).get("annotations") or []
        self._draw_annotations(path, anns)
        self._refresh_barcode_tree(anns)

        # Fit image to fill view at a comfortable size, centered
        self._view.resetTransform()
        self._view.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)
        # Scale up a bit so the image actually fills more of the viewport
        self._view.scale(0.95, 0.95)

    def _draw_annotations(self, path, annotations):
        self._poly_items = {}
        self._handle_items = []
        for i, ann in enumerate(annotations):
            if not ann.get("points"):
                continue
            poly = QPolygonF([QPointF(x, y) for x, y in ann["points"]])
            color = QColor(0, 200, 0) if ann.get("match") else QColor(220, 50, 50)

            poly_item = SelectablePolygon(
                ann,
                lambda p=path: self._redraw(p),
                lambda a=ann, p=path: self._delete_annotation(p, a)
            )
            poly_item.setPolygon(poly)
            poly_item.setPen(QPen(color, 2))
            self._scene.addItem(poly_item)
            self._poly_items[i] = poly_item

            # Draggable vertex handles for each corner
            for pt_idx in range(len(ann["points"])):
                handle = DraggableVertex(
                    ann, pt_idx,
                    lambda p=path: self._soft_redraw(p)
                )
                self._scene.addItem(handle)
                self._handle_items.append(handle)

            tx, ty = ann["points"][0]
            source_tag = " [D+Z]" if ann.get("match") else (
                " [D]" if ann.get("source") == "dbr" else (
                    " [Z]" if ann.get("source") == "zxing" else " [M]"
                )
            )
            label = f'[{ann["format"]}] {ann["text"]}{source_tag}'
            ti = self._scene.addText(label, QFont("Arial", 9, QFont.Bold))
            ti.setDefaultTextColor(color)
            ti.setPos(tx, max(0.0, ty - 16))

    def _refresh_barcode_tree(self, annotations):
        self._tree_barcodes.clear()
        for i, ann in enumerate(annotations):
            source_tag = "[D+Z]" if ann.get("match") else (
                "[D]" if ann.get("source") == "dbr" else (
                    "[Z]" if ann.get("source") == "zxing" else "[manual]"
                )
            )
            color = QColor(0, 130, 0) if ann.get("match") else QColor(180, 0, 0)

            root_item = QTreeWidgetItem([
                f"#{i+1} {source_tag}",
                f'{ann["text"]}  ({ann["format"]})'
            ])
            root_item.setData(0, Qt.UserRole, i)
            root_item.setForeground(0, color)
            root_item.setForeground(1, color)

            # Coordinates
            pts = ann.get("points", [])
            coord_item = QTreeWidgetItem(["Quad Points", ""])
            for pi, pt in enumerate(pts):
                QTreeWidgetItem(coord_item, [f"  P{pi+1}", f"({pt[0]:.1f}, {pt[1]:.1f})"])
            root_item.addChild(coord_item)

            # Dynamsoft result
            dbr_data = ann.get("dbr")
            if dbr_data:
                dbr_node = QTreeWidgetItem(["Dynamsoft (DBR)", ""])
                dbr_node.setForeground(0, QColor(0, 100, 180))
                QTreeWidgetItem(dbr_node, ["  Text", dbr_data["text"]])
                QTreeWidgetItem(dbr_node, ["  Format", dbr_data["format"]])
                dbr_pts = dbr_data.get("points", [])
                for pi, pt in enumerate(dbr_pts):
                    QTreeWidgetItem(dbr_node, [f"  P{pi+1}", f"({pt[0]:.1f}, {pt[1]:.1f})"])
                root_item.addChild(dbr_node)

            # ZXing result
            zxing_data = ann.get("zxing")
            if zxing_data:
                zx_node = QTreeWidgetItem(["ZXing", ""])
                zx_node.setForeground(0, QColor(180, 100, 0))
                QTreeWidgetItem(zx_node, ["  Text", zxing_data["text"]])
                QTreeWidgetItem(zx_node, ["  Format", zxing_data["format"]])
                zx_pts = zxing_data.get("points", [])
                for pi, pt in enumerate(zx_pts):
                    QTreeWidgetItem(zx_node, [f"  P{pi+1}", f"({pt[0]:.1f}, {pt[1]:.1f})"])
                root_item.addChild(zx_node)

            # Highlight differences between DBR and ZXing
            if dbr_data and zxing_data:
                diff_node = QTreeWidgetItem(["Differences", ""])
                diff_node.setForeground(0, QColor(200, 0, 200))
                has_diff = False
                if dbr_data["text"] != zxing_data["text"]:
                    QTreeWidgetItem(diff_node, ["  Text", f'DBR="{dbr_data["text"]}" vs ZX="{zxing_data["text"]}"'])
                    has_diff = True
                if dbr_data["format"] != zxing_data["format"]:
                    QTreeWidgetItem(diff_node, ["  Format", f'DBR={dbr_data["format"]} vs ZX={zxing_data["format"]}'])
                    has_diff = True
                if not has_diff:
                    QTreeWidgetItem(diff_node, ["", "All fields match"])
                root_item.addChild(diff_node)

            if not dbr_data and not zxing_data:
                # manual annotation
                manual_node = QTreeWidgetItem(["Source", "Manual"])
                root_item.addChild(manual_node)

            self._tree_barcodes.addTopLevelItem(root_item)
            root_item.setExpanded(True)

    def _redraw(self, path):
        self._scene.clear()
        self._poly_items = {}
        self._handle_items = []
        cv_img = load_image_cv(path)
        if cv_img is not None:
            pxmap = cv_to_qpixmap(cv_img)
            self._scene.addPixmap(pxmap)
            self._scene.setSceneRect(QRectF(pxmap.rect()))
        anns = (self._files.get(path) or {}).get("annotations") or []
        self._draw_annotations(path, anns)
        self._refresh_barcode_tree(anns)

    def _soft_redraw(self, path):
        """Lightweight redraw: update polygon shapes + tree without clearing scene."""
        anns = (self._files.get(path) or {}).get("annotations") or []
        for i, poly_item in self._poly_items.items():
            if i < len(anns):
                pts = anns[i].get("points", [])
                poly_item.setPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))
        self._refresh_barcode_tree(anns)

    # ------------------------------------------------------------------
    # Navigator
    # ------------------------------------------------------------------
    def _update_nav(self):
        total = len(self._all_paths)
        if self._current_path in self._all_paths:
            idx = self._all_paths.index(self._current_path)
            self._nav_label.setText(f"{idx + 1} / {total}")
        else:
            self._nav_label.setText(f"- / {total}")

    def _prev_image(self):
        if not self._all_paths or self._current_path is None:
            return
        idx = self._all_paths.index(self._current_path)
        if idx > 0:
            self._select_file(self._all_paths[idx - 1])

    def _next_image(self):
        if not self._all_paths or self._current_path is None:
            return
        idx = self._all_paths.index(self._current_path)
        if idx < len(self._all_paths) - 1:
            self._select_file(self._all_paths[idx + 1])

    def _highlight_list_item(self, path):
        for lst in (self._list_verified, self._list_review, self._list_noresult):
            lst.clearSelection()
            for i in range(lst.count()):
                item = lst.item(i)
                if item.data(Qt.UserRole) == path:
                    lst.setCurrentItem(item)
                    break

    # ------------------------------------------------------------------
    # Delete image(s)
    # ------------------------------------------------------------------
    def _delete_current(self):
        if not self._current_path:
            return
        path = self._current_path
        # Determine next image to show
        idx = self._all_paths.index(path)
        next_path = None
        if idx + 1 < len(self._all_paths):
            next_path = self._all_paths[idx + 1]
        elif idx - 1 >= 0:
            next_path = self._all_paths[idx - 1]

        # Remove from data
        self._all_paths.remove(path)
        del self._files[path]

        # Remove from list widgets
        self._remove_from_lists(path)

        # Show next or clear
        if next_path:
            self._select_file(next_path)
        else:
            self._current_path = None
            self._scene.clear()
            self._poly_items = {}
            self._handle_items = []
            self._tree_barcodes.clear()
            self._nav_label.setText("0 / 0")

        self._status_lbl.setText(f"{len(self._all_paths)} image(s) loaded.")

    def _delete_all(self):
        if not self._files:
            return
        reply = QMessageBox.question(
            self, "Delete All",
            f"Remove all {len(self._all_paths)} images and their annotations?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self._files.clear()
        self._all_paths.clear()
        self._current_path = None
        self._list_verified.clear()
        self._list_review.clear()
        self._list_noresult.clear()
        self._grp_verified.setTitle("Verified (0)")
        self._grp_review.setTitle("Needs Review (0)")
        self._grp_noresult.setTitle("No Result (0)")
        self._scene.clear()
        self._poly_items = {}
        self._handle_items = []
        self._tree_barcodes.clear()
        self._nav_label.setText("0 / 0")
        self._status_lbl.setText("All images removed.")

    def _remove_from_lists(self, path):
        for lst in (self._list_verified, self._list_review, self._list_noresult):
            for i in range(lst.count()):
                if lst.item(i).data(Qt.UserRole) == path:
                    lst.takeItem(i)
                    break
        self._grp_verified.setTitle(f"Verified ({self._list_verified.count()})")
        self._grp_review.setTitle(f"Needs Review ({self._list_review.count()})")
        self._grp_noresult.setTitle(f"No Result ({self._list_noresult.count()})")

    def _delete_annotation(self, path, annotation):
        """Remove a single annotation object from the image's annotation list and redraw."""
        anns = (self._files.get(path) or {}).get("annotations")
        if anns is None:
            return
        try:
            anns.remove(annotation)
        except ValueError:
            return
        self._redraw(path)

    # ------------------------------------------------------------------
    # Mode toggle helpers (mutually exclusive)
    # ------------------------------------------------------------------
    def _on_draw_mode_toggled(self, enabled):
        if enabled and self._btn_crop.isChecked():
            self._btn_crop.setChecked(False)
        self._view.set_draw_mode(enabled)

    def _on_crop_mode_toggled(self, enabled):
        if enabled and self._btn_draw.isChecked():
            self._btn_draw.setChecked(False)
        self._view.set_crop_mode(enabled)

    # ------------------------------------------------------------------
    # Crop mode: drag rect → auto-detect barcodes, no dialog fallback
    # ------------------------------------------------------------------
    def _on_crop_drawn(self, rect):
        if not self._current_path:
            return
        path = self._current_path
        quad_points = [
            (rect.left(),  rect.top()),
            (rect.right(), rect.top()),
            (rect.right(), rect.bottom()),
            (rect.left(),  rect.bottom()),
        ]
        anns = self._decode_quad_region(path, quad_points)
        if anns:
            if self._files[path]["annotations"] is None:
                self._files[path]["annotations"] = []
            self._files[path]["annotations"].extend(anns)
            self._redraw(path)
        else:
            self.statusBar().showMessage(
                "Crop mode: no barcodes detected in selected area. "
                "Try Draw Mode to annotate manually.", 5000
            )

    # ------------------------------------------------------------------
    # Draw mode: polygon → always show dialog for manual annotation
    # ------------------------------------------------------------------
    def _on_quad_drawn(self, quad_points):
        if not self._current_path:
            return
        dlg = BarcodeEditDialog(text="", fmt="Unknown")
        if dlg.exec() != QDialog.Accepted:
            return
        ann = {
            "text":   dlg.text_edit.text(),
            "format": dlg.fmt_combo.currentText(),
            "points": quad_points,
            "match":  False,
            "source": "manual",
            "dbr":    None,
            "zxing":  None,
        }
        path = self._current_path
        if self._files[path]["annotations"] is None:
            self._files[path]["annotations"] = []
        self._files[path]["annotations"].append(ann)
        self._redraw(path)

    def _decode_quad_region(self, path, quad_points):
        """Crop the bounding rect of quad_points, run DBR + ZXing, return annotations.
        Coordinates are adjusted back to the original image space.
        """
        cv_img = load_image_cv(path)
        if cv_img is None:
            return []

        h, w = cv_img.shape[:2]
        xs = [p[0] for p in quad_points]
        ys = [p[1] for p in quad_points]
        x1 = max(0, int(min(xs)))
        y1 = max(0, int(min(ys)))
        x2 = min(w, int(max(xs)) + 1)
        y2 = min(h, int(max(ys)) + 1)

        if x2 <= x1 or y2 <= y1:
            return []

        crop = cv_img[y1:y2, x1:x2]

        # --- Dynamsoft ---
        dbr_items = []
        try:
            router = CaptureVisionRouter()
            if self._active_template_path:
                err, msg = router.init_settings_from_file(self._active_template_path)
                if err != 0:
                    print(f"[DBR crop] Template load failed ({err}): {msg}")
            # Encode crop to temp PNG in memory and pass as numpy array path
            import tempfile, os as _os
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            cv2.imwrite(tmp_path, crop)
            result = router.capture(tmp_path, self._active_template_name)
            _os.unlink(tmp_path)
            if result:
                dbr_r = result.get_decoded_barcodes_result()
                if dbr_r:
                    for item in (dbr_r.get_items() or []):
                        pts = item.get_location().points
                        dbr_items.append({
                            "text":   item.get_text(),
                            "format": item.get_format_string(),
                            "points": [(p.x + x1, p.y + y1) for p in pts],
                        })
        except Exception as exc:
            print(f"[DBR crop] {exc}")

        # --- ZXing ---
        zxing_items = []
        try:
            for zx in zxingcpp.read_barcodes(crop):
                pos = zx.position
                zxing_items.append({
                    "text":   zx.text,
                    "format": zx.format.name,
                    "points": [
                        (pos.top_left.x + x1,     pos.top_left.y + y1),
                        (pos.top_right.x + x1,    pos.top_right.y + y1),
                        (pos.bottom_right.x + x1, pos.bottom_right.y + y1),
                        (pos.bottom_left.x + x1,  pos.bottom_left.y + y1),
                    ],
                })
        except Exception as exc:
            print(f"[ZXing crop] {exc}")

        if not dbr_items and not zxing_items:
            return []

        # Merge results, same logic as DetectionWorker._detect
        zxing_text_set = {r["text"] for r in zxing_items}
        dbr_text_set   = {r["text"] for r in dbr_items}
        zxing_by_text  = {}
        for r in zxing_items:
            zxing_by_text.setdefault(r["text"], []).append(r)

        anns = []
        for r in dbr_items:
            match = r["text"] in zxing_text_set
            zxing_pair = None
            if match and zxing_by_text.get(r["text"]):
                zxing_pair = zxing_by_text[r["text"]].pop(0)
            # Use the engine's detected quad points as the display polygon
            display_pts = r["points"]
            anns.append({
                "text":   r["text"],
                "format": r["format"],
                "points": display_pts,
                "match":  match,
                "source": "dbr",
                "dbr":    {"text": r["text"], "format": r["format"], "points": r["points"]},
                "zxing":  {"text": zxing_pair["text"], "format": zxing_pair["format"],
                           "points": zxing_pair["points"]} if zxing_pair else None,
            })
        for r in zxing_items:
            if r["text"] not in dbr_text_set:
                anns.append({
                    "text":   r["text"],
                    "format": r["format"],
                    "points": r["points"],
                    "match":  False,
                    "source": "zxing",
                    "dbr":    None,
                    "zxing":  {"text": r["text"], "format": r["format"], "points": r["points"]},
                })
        return anns

    # ------------------------------------------------------------------
    # Verify current image / Save verified dataset
    # ------------------------------------------------------------------
    def _verify_current(self):
        """Force the current image into the Verified list regardless of match state."""
        path = self._current_path
        if not path:
            return
        anns = (self._files.get(path) or {}).get("annotations") or []

        # Already in Verified list? — do nothing
        for i in range(self._list_verified.count()):
            if self._list_verified.item(i).data(Qt.UserRole) == path:
                self.statusBar().showMessage("Image is already in the Verified list.", 3000)
                return

        # Remove from whichever list it currently lives in
        self._remove_from_lists(path)

        # Mark every annotation as verified (match=True) so it shows green
        for ann in anns:
            ann["match"] = True

        # Add to Verified list
        filename = os.path.basename(path)
        item = QListWidgetItem(filename)
        item.setData(Qt.UserRole, path)
        item.setForeground(QColor(0, 130, 0))
        self._list_verified.addItem(item)
        self._grp_verified.setTitle(f"Verified ({self._list_verified.count()})")
        self._grp_review.setTitle(f"Needs Review ({self._list_review.count()})")
        self._grp_noresult.setTitle(f"No Result ({self._list_noresult.count()})")

        self._highlight_list_item(path)
        # Redraw so polygon colours update to green
        self._redraw(path)
        self.statusBar().showMessage(f"'{filename}' moved to Verified.", 4000)

    def _save_verified_dataset(self):
        """Copy all Verified images + write annotations JSON to a chosen folder."""
        if self._list_verified.count() == 0:
            QMessageBox.warning(self, "No Verified Images",
                                "There are no images in the Verified list yet.")
            return

        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder for Verified Dataset"
        )
        if not folder:
            return

        import shutil
        images_out = []
        errors = []
        total_barcodes = 0

        for i in range(self._list_verified.count()):
            path = self._list_verified.item(i).data(Qt.UserRole)
            filename = os.path.basename(path)
            dest = os.path.join(folder, filename)

            # Copy image file
            try:
                if os.path.abspath(path) != os.path.abspath(dest):
                    shutil.copy2(path, dest)
            except Exception as exc:
                errors.append(f"{filename}: {exc}")
                continue

            anns = (self._files.get(path) or {}).get("annotations") or []
            barcodes = [
                {"text": a["text"], "format": a["format"], "points": a["points"]}
                for a in anns
            ]
            total_barcodes += len(barcodes)
            images_out.append({"file": filename, "barcodes": barcodes})

        # Write JSON
        out = {
            "format":        "barcode-benchmark/1.0",
            "dataset":       "Verified Collection",
            "total_images":  len(images_out),
            "total_barcodes": total_barcodes,
            "images":        images_out,
        }
        json_path = os.path.join(folder, "annotations.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            errors.append(f"annotations.json: {exc}")

        msg = (
            f"Saved {len(images_out)} image(s) and annotations.json to:\n{folder}"
        )
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Saved with Errors", msg)
        else:
            QMessageBox.information(self, "Verified Dataset Saved", msg)

    # ------------------------------------------------------------------
    # DBR template import / export / reset
    # ------------------------------------------------------------------
    def _export_dbr_template(self):
        """Export the active (or default) DBR template to a JSON file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export DBR Template",
            "dbr_template.json",
            "JSON files (*.json)"
        )
        if not path:
            return
        try:
            router = CaptureVisionRouter()
            # If a custom template is loaded, init the router with it first
            # so we export its full definition rather than the bare default.
            if self._active_template_path:
                router.init_settings_from_file(self._active_template_path)
            # Export '*' → all templates (includes the one we'll be using)
            err, msg = router.output_settings_to_file("*", path,
                                                       include_default_values=True)
            if err != 0:
                QMessageBox.warning(self, "Export Failed",
                                    f"DBR error [{err}]: {msg}")
            else:
                self.statusBar().showMessage(
                    f"Template exported → {path}  "
                    "(edit it, then use 'Import DBR Template' to load it back)", 8000
                )
        except Exception as exc:
            QMessageBox.warning(self, "Export Failed", str(exc))

    def _import_dbr_template(self):
        """Load a custom DBR template JSON file for all subsequent captures."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Import DBR Template",
            self._active_template_path or "",
            "JSON files (*.json)"
        )
        if not path:
            return
        try:
            # Validate by trying to load into a temporary router
            router = CaptureVisionRouter()
            err, msg = router.init_settings_from_file(path)
            if err != 0:
                QMessageBox.warning(self, "Import Failed",
                                    f"DBR error [{err}]: {msg}")
                return

            # Find the first template name inside the JSON so we use the right one
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            templates = data.get("CaptureVisionTemplates", [])
            if templates:
                template_name = templates[0]["Name"]
            else:
                # Fallback: keep the default name
                template_name = EnumPresetTemplate.PT_READ_BARCODES.value

            self._active_template_path = path
            self._active_template_name = template_name

            basename = os.path.basename(path)
            self._btn_tmpl_import.setText(f"Template: {basename}")
            self._btn_tmpl_reset.setVisible(True)
            self.statusBar().showMessage(
                f"DBR template loaded: {basename}  "
                f"(template name: '{template_name}')", 8000
            )
        except Exception as exc:
            QMessageBox.warning(self, "Import Failed", str(exc))

    def _reset_dbr_template(self):
        """Revert to the built-in default DBR template."""
        self._active_template_path = None
        self._active_template_name = EnumPresetTemplate.PT_READ_BARCODES.value
        self._btn_tmpl_import.setText("Import DBR Template")
        self._btn_tmpl_reset.setVisible(False)
        self.statusBar().showMessage("DBR template reset to default.", 5000)

    # ------------------------------------------------------------------
    # Barcode tree interaction
    # ------------------------------------------------------------------
    def _on_barcode_tree_clicked(self, item, column):
        # Walk up to find the top-level item that has the annotation index
        node = item
        while node.parent():
            node = node.parent()
        idx = node.data(0, Qt.UserRole)
        if idx is None:
            return
        # Highlight selected polygon, dim others
        for i, poly in self._poly_items.items():
            is_match = poly.annotation.get("match")
            base_color = QColor(0, 200, 0) if is_match else QColor(220, 50, 50)
            width = 4 if i == idx else 2
            poly.setPen(QPen(base_color, width))

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self._prev_image()
        elif event.key() == Qt.Key_Right:
            self._next_image()
        elif event.key() == Qt.Key_D:
            self._btn_draw.toggle()
        elif event.key() == Qt.Key_C:
            self._btn_crop.toggle()
        elif event.key() == Qt.Key_Delete:
            self._delete_current()
        elif event.key() == Qt.Key_Escape:
            if self._btn_draw.isChecked():
                self._btn_draw.setChecked(False)
            if self._btn_crop.isChecked():
                self._btn_crop.setChecked(False)
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_path and self._scene.sceneRect().width() > 0:
            self._view.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)
            self._view.scale(0.95, 0.95)

    # ------------------------------------------------------------------
    # Import annotations from a barcode-benchmark/1.0 JSON file
    # ------------------------------------------------------------------
    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Annotations", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            QMessageBox.warning(self, "Import Error", str(exc))
            return

        fmt = data.get("format", "")
        if "barcode-benchmark" not in fmt:
            reply = QMessageBox.question(
                self, "Unrecognised Format",
                f"Expected 'barcode-benchmark/1.0', got '{fmt}'.\n"
                "Try to import anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Build lookup: basename -> list of barcode dicts
        json_map = {}
        for entry in data.get("images", []):
            file_field = entry.get("file", "")
            basename = os.path.basename(file_field) if file_field else ""
            if basename:
                json_map[basename] = entry.get("barcodes", [])

        applied = 0
        skipped = 0
        for img_path in self._all_paths:
            basename = os.path.basename(img_path)
            if basename not in json_map:
                skipped += 1
                continue

            # Convert to internal annotation format (imported = verified)
            raw_barcodes = json_map[basename]
            annotations = [
                {
                    "text":   bc.get("text", ""),
                    "format": bc.get("format", "Unknown"),
                    "points": [tuple(p) for p in bc.get("points", [])],
                    "match":  True,
                    "source": "imported",
                    "dbr":    None,
                    "zxing":  None,
                }
                for bc in raw_barcodes
            ]

            # Update stored data
            self._files[img_path]["annotations"] = annotations

            # Move item to the correct list
            self._remove_from_lists(img_path)
            item = QListWidgetItem(basename)
            item.setData(Qt.UserRole, img_path)
            if annotations:
                item.setForeground(QColor(0, 130, 0))
                self._list_verified.addItem(item)
            else:
                item.setForeground(QColor(120, 120, 120))
                self._list_noresult.addItem(item)

            applied += 1

        self._grp_verified.setTitle(f"Verified ({self._list_verified.count()})")
        self._grp_review.setTitle(f"Needs Review ({self._list_review.count()})")
        self._grp_noresult.setTitle(f"No Result ({self._list_noresult.count()})")

        # Refresh display if the current image was updated
        if self._current_path:
            basename = os.path.basename(self._current_path)
            if basename in json_map:
                self._redraw(self._current_path)
                self._highlight_list_item(self._current_path)

        self.statusBar().showMessage(
            f"Import complete — {applied} image(s) updated, "
            f"{skipped} image(s) not found in JSON.",
            8000
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _export_json(self):
        if not self._files:
            QMessageBox.warning(self, "No Files", "No images loaded.")
            return

        images_out = []
        total_barcodes = 0
        for path in self._all_paths:
            filename = os.path.basename(path)
            anns = (self._files.get(path) or {}).get("annotations") or []
            barcodes = [
                {"text": a["text"], "format": a["format"], "points": a["points"]}
                for a in anns
            ]
            total_barcodes += len(barcodes)
            images_out.append({"file": filename, "barcodes": barcodes})

        out = {
            "format":  "barcode-benchmark/1.0",
            "dataset": "Annotated Collection",
            "total_images": len(images_out),
            "total_barcodes": total_barcodes,
            "images":  images_out,
        }

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotations", "annotations.json", "JSON (*.json)"
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Saved", f"Annotations saved to:\n{save_path}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnnotationApp()
    window.show()
    sys.exit(app.exec())
