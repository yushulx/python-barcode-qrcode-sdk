"""
Dynamsoft Barcode Reader - PySide6 GUI

Reads barcodes from image files (PNG/JPG/BMP/TIFF/WebP) and PDF files using
CaptureVisionRouter.capture_multi_pages. Supports drag-and-drop for files and
folders, draws overlay quadrilaterals on detected barcodes, and provides a
page navigator for multi-page documents (PDFs, TIFFs).
"""

import os
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import fitz
import numpy as np
from PySide6.QtCore import QObject, QPointF, QRectF, QSize, Qt, QThread, Signal
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QImage,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QStyle,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dynamsoft_capture_vision_bundle import (
    CaptureVisionRouter,
    EnumErrorCode,
    EnumPresetTemplate,
    FileImageTag,
    LicenseManager,
)

LICENSE_KEY = (
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6"
    "YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5"
    "YUoifQ=="
)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
TIFF_EXTS = {".tif", ".tiff"}
PDF_EXTS = {".pdf"}
SUPPORTED_EXTS = IMAGE_EXTS | TIFF_EXTS | PDF_EXTS

PDF_DETECT_DPI = 300
PDF_DISPLAY_DPI = 150

OVERLAY_COLOR = QColor(0, 200, 80)
OVERLAY_FILL = QColor(0, 200, 80, 60)
OVERLAY_TEXT_BG = QColor(0, 0, 0, 180)
OVERLAY_TEXT_FG = QColor(255, 255, 255)


@dataclass
class BarcodeHit:
    text: str
    format: str
    confidence: int
    points: List[Tuple[float, float]]


@dataclass
class PageData:
    file_path: str
    page_index: int
    total_pages: int
    image: Optional[QImage] = None
    detect_width: int = 0
    detect_height: int = 0
    barcodes: List[BarcodeHit] = field(default_factory=list)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------

def _qimage_from_bgr(mat: np.ndarray) -> QImage:
    rgb = cv2.cvtColor(mat, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    return QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888).copy()


def render_pages(file_path: str) -> List[Tuple[QImage, int, int]]:
    """Render every page of *file_path* and also return the dimensions
    Dynamsoft uses when decoding so overlay coordinates can be scaled.

    Returns a list of ``(qimage, detect_w, detect_h)`` tuples.
    """
    ext = Path(file_path).suffix.lower()

    if ext in PDF_EXTS:
        pages: List[Tuple[QImage, int, int]] = []
        with fitz.open(file_path) as doc:
            for page in doc:
                pix = page.get_pixmap(dpi=PDF_DISPLAY_DPI, alpha=False)
                fmt = (
                    QImage.Format.Format_RGB888
                    if pix.n == 3
                    else QImage.Format.Format_Grayscale8
                )
                img = QImage(
                    pix.samples, pix.width, pix.height, pix.stride, fmt
                ).copy()
                detect_w = max(1, int(round(page.rect.width * PDF_DETECT_DPI / 72)))
                detect_h = max(1, int(round(page.rect.height * PDF_DETECT_DPI / 72)))
                pages.append((img, detect_w, detect_h))
        return pages

    if ext in TIFF_EXTS:
        ok, mats = cv2.imreadmulti(file_path, [], cv2.IMREAD_COLOR)
        pages = []
        if ok and mats:
            for mat in mats:
                if mat is None:
                    continue
                img = _qimage_from_bgr(mat)
                pages.append((img, img.width(), img.height()))
        return pages

    img = QImage(file_path)
    if img.isNull():
        mat = cv2.imread(file_path, cv2.IMREAD_COLOR)
        if mat is None:
            return []
        img = _qimage_from_bgr(mat)
    return [(img, img.width(), img.height())]


# ---------------------------------------------------------------------------
# Scanner thread
# ---------------------------------------------------------------------------

class ScannerSignals(QObject):
    fileStarted = Signal(str, int)
    pageReady = Signal(object)
    fileFinished = Signal(str)
    allFinished = Signal()
    error = Signal(str, str)


class ScannerThread(QThread):
    def __init__(self, files: List[str], parent=None) -> None:
        super().__init__(parent)
        self.files = list(files)
        self.signals = ScannerSignals()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            cvr = CaptureVisionRouter()
        except Exception as exc:
            self.signals.error.emit("", f"Failed to init CVR: {exc}")
            self.signals.allFinished.emit()
            return

        template = EnumPresetTemplate.PT_READ_BARCODES_READ_RATE_FIRST.value

        for file_path in self.files:
            if self._stop:
                break
            try:
                rendered = render_pages(file_path)
            except Exception as exc:
                self.signals.error.emit(
                    file_path, f"Failed to render: {exc}\n{traceback.format_exc()}"
                )
                continue

            total_pages = len(rendered)
            if total_pages == 0:
                self.signals.error.emit(file_path, "No pages rendered.")
                continue

            self.signals.fileStarted.emit(file_path, total_pages)

            # Emit placeholder pages first so the UI is responsive while the
            # scan runs; barcodes will be filled in after decode finishes.
            page_records: List[PageData] = []
            for idx, (img, dw, dh) in enumerate(rendered):
                rec = PageData(
                    file_path=file_path,
                    page_index=idx,
                    total_pages=total_pages,
                    image=img,
                    detect_width=dw,
                    detect_height=dh,
                )
                page_records.append(rec)
                self.signals.pageReady.emit(rec)

            if self._stop:
                break

            try:
                result_array = cvr.capture_multi_pages(file_path, template)
            except Exception as exc:
                self.signals.error.emit(
                    file_path,
                    f"capture_multi_pages failed: {exc}\n{traceback.format_exc()}",
                )
                self.signals.fileFinished.emit(file_path)
                continue

            results = result_array.get_results() if result_array else None
            if not results:
                self.signals.fileFinished.emit(file_path)
                continue

            for page_result in results:
                page_idx = 0
                tag = page_result.get_original_image_tag()
                if isinstance(tag, FileImageTag):
                    page_idx = tag.get_page_number()
                if page_idx < 0 or page_idx >= total_pages:
                    continue

                err = page_result.get_error_code()
                if err not in (
                    EnumErrorCode.EC_OK,
                    EnumErrorCode.EC_UNSUPPORTED_JSON_KEY_WARNING,
                ):
                    page_records[page_idx].error = page_result.get_error_string()
                    self.signals.pageReady.emit(page_records[page_idx])
                    continue

                hits: List[BarcodeHit] = []
                for item in page_result.get_items():
                    loc = item.get_location()
                    pts = [(p.x, p.y) for p in loc.points]
                    hits.append(
                        BarcodeHit(
                            text=item.get_text(),
                            format=item.get_format_string(),
                            confidence=item.get_confidence(),
                            points=pts,
                        )
                    )
                page_records[page_idx].barcodes = hits
                self.signals.pageReady.emit(page_records[page_idx])

            self.signals.fileFinished.emit(file_path)

        self.signals.allFinished.emit()


# ---------------------------------------------------------------------------
# Image viewer with overlays
# ---------------------------------------------------------------------------

class ImageViewer(QGraphicsView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#1e1f23")))
        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._zoom = 0
        self._has_page = False

    def clear_view(self) -> None:
        self._scene.clear()
        self._pixmap_item = None
        self._has_page = False
        self._zoom = 0
        self.resetTransform()

    def set_page(self, page: PageData) -> None:
        self._scene.clear()
        self._pixmap_item = None
        self._zoom = 0
        self.resetTransform()

        if page.image is None or page.image.isNull():
            placeholder = self._scene.addText("No preview available")
            placeholder.setDefaultTextColor(QColor("#bbbbbb"))
            self._has_page = False
            return

        pix = QPixmap.fromImage(page.image)
        self._pixmap_item = self._scene.addPixmap(pix)
        self._pixmap_item.setZValue(0)
        self._scene.setSceneRect(QRectF(pix.rect()))
        self._has_page = True

        sx = pix.width() / max(1, page.detect_width)
        sy = pix.height() / max(1, page.detect_height)

        pen = QPen(OVERLAY_COLOR)
        pen.setCosmetic(True)
        pen.setWidth(3)
        brush = QBrush(OVERLAY_FILL)

        font = QFont()
        font.setBold(True)
        font.setPointSize(11)

        for idx, hit in enumerate(page.barcodes, start=1):
            polygon = QPolygonF([QPointF(x * sx, y * sy) for x, y in hit.points])
            poly_item = QGraphicsPolygonItem(polygon)
            poly_item.setPen(pen)
            poly_item.setBrush(brush)
            poly_item.setZValue(1)
            self._scene.addItem(poly_item)

            anchor = polygon.boundingRect().topLeft()
            label_text = f"#{idx} {hit.format}"
            text_item = QGraphicsSimpleTextItem(label_text)
            text_item.setFont(font)
            text_item.setBrush(QBrush(OVERLAY_TEXT_FG))
            text_item.setZValue(2)
            text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)

            br = text_item.boundingRect()
            pad = 4
            bg = self._scene.addRect(
                QRectF(0, 0, br.width() + 2 * pad, br.height() + 2 * pad),
                QPen(Qt.PenStyle.NoPen),
                QBrush(OVERLAY_TEXT_BG),
            )
            bg.setZValue(2)
            bg.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
            bg.setPos(anchor)
            text_item.setParentItem(bg)
            text_item.setPos(pad, pad)

        self.fit_to_window()

    def fit_to_window(self) -> None:
        if self._pixmap_item is None:
            return
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = 0

    def wheelEvent(self, event) -> None:
        if not self._has_page or not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            super().wheelEvent(event)
            return
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.2 if delta > 0 else 1 / 1.2
        new_zoom = self._zoom + (1 if delta > 0 else -1)
        if -15 <= new_zoom <= 25:
            self.scale(factor, factor)
            self._zoom = new_zoom

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._zoom == 0 and self._pixmap_item is not None:
            self.fit_to_window()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    PAGE_ROLE = Qt.ItemDataRole.UserRole + 1
    FILE_ROLE = Qt.ItemDataRole.UserRole + 2

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Dynamsoft Barcode Reader - GUI")
        self.resize(1280, 820)
        self.setAcceptDrops(True)

        # data
        self._pages: dict[Tuple[str, int], PageData] = {}
        self._file_items: dict[str, QTreeWidgetItem] = {}
        self._scanner: Optional[ScannerThread] = None
        self._license_ok = False
        self._barcode_total = 0

        self._build_ui()
        self._init_license()

    # ----- UI construction -------------------------------------------------

    def _build_ui(self) -> None:
        style = self.style()

        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        open_files_act = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
            "Open Files",
            self,
        )
        open_files_act.triggered.connect(self._on_open_files)
        toolbar.addAction(open_files_act)

        open_dir_act = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon),
            "Open Folder",
            self,
        )
        open_dir_act.triggered.connect(self._on_open_folder)
        toolbar.addAction(open_dir_act)

        toolbar.addSeparator()

        self._clear_act = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon),
            "Clear",
            self,
        )
        self._clear_act.triggered.connect(self._on_clear)
        toolbar.addAction(self._clear_act)

        self._fit_act = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView),
            "Fit to Window",
            self,
        )
        self._fit_act.triggered.connect(lambda: self.viewer.fit_to_window())
        toolbar.addAction(self._fit_act)

        toolbar.addSeparator()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setFixedWidth(180)
        toolbar.addWidget(self._progress)

        # tree (file list)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File / Page", "Barcodes"])
        self.tree.setColumnWidth(0, 220)
        self.tree.setMinimumWidth(260)
        self.tree.currentItemChanged.connect(self._on_tree_changed)

        tree_panel = QWidget()
        tree_layout = QVBoxLayout(tree_panel)
        tree_layout.setContentsMargins(6, 6, 6, 6)
        tree_layout.setSpacing(4)
        tree_hint = QLabel("Drop files or folders here")
        tree_hint.setStyleSheet("color: #8a8a8a; font-style: italic;")
        tree_layout.addWidget(tree_hint)
        tree_layout.addWidget(self.tree)

        # viewer + navigator
        self.viewer = ImageViewer()
        self.viewer.setMinimumSize(480, 360)

        nav_bar = QFrame()
        nav_bar.setFrameShape(QFrame.Shape.StyledPanel)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(8, 6, 8, 6)
        self._prev_btn = QPushButton("\u2039 Prev")
        self._prev_btn.clicked.connect(self._on_prev_page)
        self._next_btn = QPushButton("Next \u203a")
        self._next_btn.clicked.connect(self._on_next_page)
        self._page_label = QLabel("No page selected")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setStyleSheet("font-weight: 600;")
        nav_layout.addWidget(self._prev_btn)
        nav_layout.addWidget(self._page_label, 1)
        nav_layout.addWidget(self._next_btn)

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.addWidget(self.viewer, 1)
        center_layout.addWidget(nav_bar)

        # results panel
        self.results = QListWidget()
        self.results.setWordWrap(True)
        self.results.setAlternatingRowColors(True)
        self.results.itemDoubleClicked.connect(self._on_result_double_clicked)

        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(6, 6, 6, 6)
        results_layout.setSpacing(4)
        results_layout.addWidget(QLabel("Detected barcodes"))
        results_layout.addWidget(self.results)

        # splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(tree_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(results_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([280, 720, 280])
        self.setCentralWidget(splitter)

        # status bar
        self._status_label = QLabel("Drop files/folders, or use the toolbar.")
        sb = QStatusBar()
        sb.addWidget(self._status_label, 1)
        self.setStatusBar(sb)

        self._update_nav_state()

    # ----- license ---------------------------------------------------------

    def _init_license(self) -> None:
        try:
            code, msg = LicenseManager.init_license(LICENSE_KEY)
        except Exception as exc:
            self._license_ok = False
            QMessageBox.critical(self, "License", f"License init failed: {exc}")
            return
        if code in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_CACHE_USED):
            self._license_ok = True
            self._status_label.setText("License OK. Drop files/folders to scan.")
        else:
            self._license_ok = False
            QMessageBox.warning(
                self, "License", f"License initialization failed ({code}): {msg}"
            )
            self._status_label.setText(f"License failed: {msg}")

    # ----- drag and drop ---------------------------------------------------

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths: List[str] = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local:
                paths.append(local)
        if paths:
            event.acceptProposedAction()
            self._enqueue_paths(paths)
        else:
            event.ignore()

    # ----- toolbar handlers ------------------------------------------------

    def _on_open_files(self) -> None:
        patterns = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select images or PDFs",
            "",
            f"Supported ({patterns});;All files (*)",
        )
        if files:
            self._enqueue_paths(files)

    def _on_open_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder:
            self._enqueue_paths([folder])

    def _on_clear(self) -> None:
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()
            self._scanner.wait(2000)
        self.tree.clear()
        self.results.clear()
        self.viewer.clear_view()
        self._pages.clear()
        self._file_items.clear()
        self._barcode_total = 0
        self._page_label.setText("No page selected")
        self._status_label.setText("Cleared.")
        self._update_nav_state()

    # ----- queueing --------------------------------------------------------

    def _enqueue_paths(self, paths: List[str]) -> None:
        if not self._license_ok:
            QMessageBox.warning(self, "License", "License not initialized.")
            return

        expanded = self._expand_paths(paths)
        if not expanded:
            self._status_label.setText("No supported files found.")
            return

        # de-dupe against already-loaded files
        new_files = [p for p in expanded if p not in self._file_items]
        if not new_files:
            self._status_label.setText("All dropped files are already loaded.")
            return

        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()
            self._scanner.wait(2000)

        self._progress.setVisible(True)
        self._status_label.setText(f"Scanning {len(new_files)} file(s)...")

        self._scanner = ScannerThread(new_files, self)
        self._scanner.signals.fileStarted.connect(self._on_file_started)
        self._scanner.signals.pageReady.connect(self._on_page_ready)
        self._scanner.signals.fileFinished.connect(self._on_file_finished)
        self._scanner.signals.allFinished.connect(self._on_all_finished)
        self._scanner.signals.error.connect(self._on_scan_error)
        self._scanner.start()

    @staticmethod
    def _expand_paths(paths: List[str]) -> List[str]:
        out: List[str] = []
        seen: set = set()
        for p in paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for name in sorted(files):
                        ext = Path(name).suffix.lower()
                        if ext in SUPPORTED_EXTS:
                            full = os.path.abspath(os.path.join(root, name))
                            if full not in seen:
                                seen.add(full)
                                out.append(full)
            elif os.path.isfile(p):
                ext = Path(p).suffix.lower()
                if ext in SUPPORTED_EXTS:
                    full = os.path.abspath(p)
                    if full not in seen:
                        seen.add(full)
                        out.append(full)
        return out

    # ----- scanner signals -------------------------------------------------

    def _on_file_started(self, file_path: str, total_pages: int) -> None:
        item = QTreeWidgetItem([os.path.basename(file_path), "..."])
        item.setToolTip(0, file_path)
        item.setData(0, self.FILE_ROLE, file_path)
        self.tree.addTopLevelItem(item)
        self._file_items[file_path] = item
        if total_pages > 1:
            item.setExpanded(True)

    def _on_page_ready(self, page: PageData) -> None:
        key = (page.file_path, page.page_index)
        self._pages[key] = page

        parent = self._file_items.get(page.file_path)
        if parent is None:
            return

        # First time we see this page -> add it under the parent (only if
        # multi-page document); for single-page files the parent represents
        # the page directly.
        existing_child = None
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, self.PAGE_ROLE) == page.page_index:
                existing_child = child
                break

        n_bc = len(page.barcodes)
        if page.total_pages == 1:
            parent.setText(1, str(n_bc))
            parent.setData(0, self.PAGE_ROLE, 0)
            target_item = parent
        else:
            if existing_child is None:
                child = QTreeWidgetItem([f"Page {page.page_index + 1}", str(n_bc)])
                child.setData(0, self.PAGE_ROLE, page.page_index)
                child.setData(0, self.FILE_ROLE, page.file_path)
                parent.addChild(child)
                target_item = child
            else:
                existing_child.setText(1, str(n_bc))
                target_item = existing_child
            # roll up total count
            total = sum(
                len(self._pages.get((page.file_path, i), PageData(page.file_path, i, 0)).barcodes)
                for i in range(page.total_pages)
            )
            parent.setText(1, str(total))

        # If the user has not selected anything yet, auto-select the very
        # first item we know about.
        if self.tree.currentItem() is None:
            self.tree.setCurrentItem(target_item)
        elif self.tree.currentItem() is target_item:
            # currently viewed page just got new results -> refresh
            self._show_page(page)

    def _on_file_finished(self, file_path: str) -> None:
        item = self._file_items.get(file_path)
        if item is not None:
            item.setForeground(0, QBrush(QColor("#2f9e44")))

    def _on_all_finished(self) -> None:
        self._progress.setVisible(False)
        total_pages = len(self._pages)
        total_bc = sum(len(p.barcodes) for p in self._pages.values())
        self._barcode_total = total_bc
        self._status_label.setText(
            f"Done. {total_pages} page(s), {total_bc} barcode(s) detected."
        )

    def _on_scan_error(self, file_path: str, message: str) -> None:
        if file_path:
            self._status_label.setText(f"Error: {os.path.basename(file_path)} - {message.splitlines()[0]}")
        else:
            self._status_label.setText(f"Error: {message.splitlines()[0]}")

    # ----- navigation ------------------------------------------------------

    def _on_tree_changed(self, current: Optional[QTreeWidgetItem], _prev) -> None:
        if current is None:
            self.viewer.clear_view()
            self.results.clear()
            self._page_label.setText("No page selected")
            self._update_nav_state()
            return
        page = self._page_from_item(current)
        if page is not None:
            self._show_page(page)
        else:
            self.viewer.clear_view()
            self.results.clear()
            self._page_label.setText(os.path.basename(current.data(0, self.FILE_ROLE) or ""))
            self._update_nav_state()

    def _page_from_item(self, item: QTreeWidgetItem) -> Optional[PageData]:
        page_idx = item.data(0, self.PAGE_ROLE)
        file_path = item.data(0, self.FILE_ROLE)
        if file_path is None or page_idx is None:
            return None
        return self._pages.get((file_path, int(page_idx)))

    def _show_page(self, page: PageData) -> None:
        self.viewer.set_page(page)
        self.results.clear()
        if page.error:
            err_item = QListWidgetItem(f"[error] {page.error}")
            err_item.setForeground(QBrush(QColor("#c92a2a")))
            self.results.addItem(err_item)
        for idx, hit in enumerate(page.barcodes, start=1):
            text = (
                f"#{idx}  [{hit.format}]  conf={hit.confidence}\n"
                f"    {hit.text}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, hit.text)
            self.results.addItem(item)
        self._page_label.setText(
            f"{os.path.basename(page.file_path)}    "
            f"Page {page.page_index + 1} / {page.total_pages}    "
            f"{len(page.barcodes)} barcode(s)"
        )
        self._update_nav_state()

    def _flat_page_items(self) -> List[QTreeWidgetItem]:
        items: List[QTreeWidgetItem] = []
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            if top.childCount() == 0 and top.data(0, self.PAGE_ROLE) is not None:
                items.append(top)
            else:
                for j in range(top.childCount()):
                    items.append(top.child(j))
        return items

    def _on_prev_page(self) -> None:
        self._step_page(-1)

    def _on_next_page(self) -> None:
        self._step_page(1)

    def _step_page(self, delta: int) -> None:
        items = self._flat_page_items()
        if not items:
            return
        current = self.tree.currentItem()
        if current is None or current not in items:
            target = items[0]
        else:
            idx = items.index(current) + delta
            if idx < 0 or idx >= len(items):
                return
            target = items[idx]
        self.tree.setCurrentItem(target)

    def _update_nav_state(self) -> None:
        items = self._flat_page_items()
        current = self.tree.currentItem()
        has_items = bool(items)
        idx = items.index(current) if current in items else -1
        self._prev_btn.setEnabled(has_items and idx > 0)
        self._next_btn.setEnabled(has_items and idx >= 0 and idx < len(items) - 1)

    # ----- results panel ---------------------------------------------------

    def _on_result_double_clicked(self, item: QListWidgetItem) -> None:
        text = item.data(Qt.ItemDataRole.UserRole)
        if text:
            QApplication.clipboard().setText(text)
            self._status_label.setText(f"Copied to clipboard: {text[:60]}")

    # ----- cleanup ---------------------------------------------------------

    def closeEvent(self, event) -> None:
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()
            self._scanner.wait(2000)
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Dynamsoft Barcode Reader GUI")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
