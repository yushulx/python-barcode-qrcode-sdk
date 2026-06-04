"""
Dynamsoft Barcode Reader - PySide6 GUI

Reads barcodes from image files (PNG/JPG/BMP/TIFF/WebP) and PDF files using
CaptureVisionRouter.capture_multi_pages. Supports drag-and-drop for files and
folders, draws overlay quadrilaterals on detected barcodes, and provides a
page navigator for multi-page documents (PDFs, TIFFs).
"""

import os
import sys
import time
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
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHeaderView,
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

from dynamsoft_barcode_reader_bundle import (
    CaptureVisionRouter,
    EnumCapturedResultItemType,
    EnumErrorCode,
    EnumImagePixelFormat,
    EnumPresetTemplate,
    FileImageTag,
    LicenseManager,
    Quadrilateral,
)

try:
    from dynamsoft_barcode_reader_bundle import (
        EnumLayoutElementSource,
        EnumLayoutPattern,
        LayoutAnalysisParameter,
        LayoutAnalyzer,
    )
except ImportError:
    EnumLayoutElementSource = None
    EnumLayoutPattern = None
    LayoutAnalysisParameter = None
    LayoutAnalyzer = None

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
BASE_DIR = Path(__file__).resolve().parent
LAYOUT_FAST_TEMPLATE_PATH = str(BASE_DIR / "GridFastScan.json")
LAYOUT_FAST_TEMPLATE_NAME = "GridFastScan"
LAYOUT_DEEP_TEMPLATE_PATH = str(BASE_DIR / "GridDeepDecode.json")
LAYOUT_DEEP_TEMPLATE_NAME = "GridDeepDecode"
LAYOUT_ROI_SCALE_FACTOR = 2.0
LAYOUT_ANALYSIS_AVAILABLE = all(
    symbol is not None
    for symbol in (
        EnumLayoutElementSource,
        EnumLayoutPattern,
        LayoutAnalysisParameter,
        LayoutAnalyzer,
    )
)
LAYOUT_ANALYSIS_UNAVAILABLE_REASON = (
    ""
    if LAYOUT_ANALYSIS_AVAILABLE
    else "Layout analysis is unavailable in the installed Dynamsoft Barcode Reader Bundle version."
)

TEMPLATES: List[Tuple[str, str]] = [
    ("Read Barcodes (default)", EnumPresetTemplate.PT_READ_BARCODES.value),
    ("Speed First", EnumPresetTemplate.PT_READ_BARCODES_SPEED_FIRST.value),
    ("Read Rate First", EnumPresetTemplate.PT_READ_BARCODES_READ_RATE_FIRST.value),
    ("Single Barcode", EnumPresetTemplate.PT_READ_SINGLE_BARCODE.value),
]
DEFAULT_TEMPLATE_INDEX = 0  # Read Barcodes (default)

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
    decode_elapsed_ms: Optional[int] = None


@dataclass
class FileScanMetrics:
    barcode_count: int = 0
    decode_elapsed_ms: Optional[int] = None
    used_layout_analysis: bool = False
    template: Optional[str] = None


@dataclass
class LayoutCommonDecodeResult:
    locations: List[Quadrilateral] = field(default_factory=list)
    hits: List[BarcodeHit] = field(default_factory=list)

    def prepare_for_layout_analysis(self) -> None:
        for location_index, location in enumerate(self.locations):
            location.id = location_index


def _points_from_quad(quad: Quadrilateral) -> List[Tuple[float, float]]:
    return [(point.x, point.y) for point in quad.points]


def _barcode_hit_from_item(item) -> BarcodeHit:
    location = item.get_location()
    return BarcodeHit(
        text=item.get_text(),
        format=item.get_format_string(),
        confidence=item.get_confidence(),
        points=_points_from_quad(location),
    )


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------

def _qimage_from_bgr(mat: np.ndarray) -> QImage:
    rgb = cv2.cvtColor(mat, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    return QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888).copy()


def _qimage_to_bgr(image: QImage) -> np.ndarray:
    rgb_image = image.convertToFormat(QImage.Format.Format_RGB888)
    width = rgb_image.width()
    height = rgb_image.height()
    stride = rgb_image.bytesPerLine()
    data = np.frombuffer(rgb_image.bits(), dtype=np.uint8).reshape((height, stride))
    rgb = data[:, : width * 3].reshape((height, width, 3)).copy()
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _compute_center(quad: Quadrilateral) -> Tuple[float, float]:
    center_x = sum(point.x for point in quad.points) / 4
    center_y = sum(point.y for point in quad.points) / 4
    return center_x, center_y


def _expand_quad(quad: Quadrilateral, scale: float) -> Quadrilateral:
    center_x, center_y = _compute_center(quad)
    result = Quadrilateral()
    for point_index, point in enumerate(quad.points):
        result.points[point_index].x = int(center_x + (point.x - center_x) * scale)
        result.points[point_index].y = int(center_y + (point.y - center_y) * scale)
    return result


def _capture_layout_fast_scan(image: np.ndarray) -> Tuple[LayoutCommonDecodeResult, Optional[str]]:
    cvr = CaptureVisionRouter()
    err_code, err_msg = cvr.init_settings_from_file(LAYOUT_FAST_TEMPLATE_PATH)
    if err_code != EnumErrorCode.EC_OK:
        return LayoutCommonDecodeResult(), f"Failed to load layout fast-scan template: {err_msg}"

    result = cvr.capture(
        np.ascontiguousarray(image),
        EnumImagePixelFormat.IPF_BGR_888,
        LAYOUT_FAST_TEMPLATE_NAME,
    )
    result_error = result.get_error_code()
    if result_error not in (
        EnumErrorCode.EC_OK,
        EnumErrorCode.EC_TIMEOUT,
        EnumErrorCode.EC_UNSUPPORTED_JSON_KEY_WARNING,
    ):
        return LayoutCommonDecodeResult(), result.get_error_string()

    common_result = LayoutCommonDecodeResult()
    for item in result.get_items() or []:
        if item.get_type() == EnumCapturedResultItemType.CRIT_BARCODE:
            common_result.locations.append(item.get_location())
            common_result.hits.append(_barcode_hit_from_item(item))
    return common_result, None


class LayoutDeepDecoder:
    def __init__(self) -> None:
        self._cvr = CaptureVisionRouter()
        self._error: Optional[str] = None
        err_code, err_msg = self._cvr.init_settings_from_file(LAYOUT_DEEP_TEMPLATE_PATH)
        if err_code != EnumErrorCode.EC_OK:
            self._error = f"Failed to load layout deep-decode template: {err_msg}"

    @property
    def error(self) -> Optional[str]:
        return self._error

    def decode(self, image: np.ndarray, quad: Quadrilateral) -> Optional[BarcodeHit]:
        if self._error:
            return None

        err_code, _err_msg, settings = self._cvr.get_simplified_settings(
            LAYOUT_DEEP_TEMPLATE_NAME
        )
        if err_code != EnumErrorCode.EC_OK:
            return None

        settings.roi = _expand_quad(quad, LAYOUT_ROI_SCALE_FACTOR)
        settings.roi_measured_in_percentage = 0
        err_code, _err_msg = self._cvr.update_settings(
            LAYOUT_DEEP_TEMPLATE_NAME, settings
        )
        if err_code != EnumErrorCode.EC_OK:
            return None

        result = self._cvr.capture(
            np.ascontiguousarray(image),
            EnumImagePixelFormat.IPF_BGR_888,
            LAYOUT_DEEP_TEMPLATE_NAME,
        )
        if result.get_error_code() not in (
            EnumErrorCode.EC_OK,
            EnumErrorCode.EC_UNSUPPORTED_JSON_KEY_WARNING,
        ):
            return None

        for item in result.get_items() or []:
            if item.get_type() == EnumCapturedResultItemType.CRIT_BARCODE and item.get_text():
                return _barcode_hit_from_item(item)
        return None


def decode_with_layout_analysis(image: np.ndarray) -> Tuple[List[BarcodeHit], Optional[str]]:
    if not LAYOUT_ANALYSIS_AVAILABLE:
        return [], LAYOUT_ANALYSIS_UNAVAILABLE_REASON

    common_result, error = _capture_layout_fast_scan(image)
    if error:
        return [], error
    if not common_result.locations:
        return [], None

    common_result.prepare_for_layout_analysis()

    param = LayoutAnalysisParameter()
    param.pattern = EnumLayoutPattern.LP_MATRIX
    param.input_image_height = image.shape[0]
    param.input_image_width = image.shape[1]

    layout_result = LayoutAnalyzer.analyze(common_result.locations, param)
    if layout_result is None or layout_result.error_code != EnumErrorCode.EC_OK:
        error_code = layout_result.error_code if layout_result else -1
        return common_result.hits, f"Layout analysis failed: ErrorCode: {error_code}"

    hits: List[BarcodeHit] = []
    used_location_ids: set[int] = set()
    deep_decoder: Optional[LayoutDeepDecoder] = None
    deep_decode_error: Optional[str] = None

    for row_elements in layout_result.elements:
        for element in row_elements:
            if element.source == EnumLayoutElementSource.LES_INPUT:
                location_id = getattr(element.quad, "id", -1)
                if 0 <= location_id < len(common_result.hits):
                    base_hit = common_result.hits[location_id]
                    hits.append(
                        BarcodeHit(
                            text=base_hit.text,
                            format=base_hit.format,
                            confidence=base_hit.confidence,
                            points=_points_from_quad(element.quad),
                        )
                    )
                    used_location_ids.add(location_id)
            elif element.source == EnumLayoutElementSource.LES_INFERRED:
                if deep_decoder is None:
                    deep_decoder = LayoutDeepDecoder()
                    deep_decode_error = deep_decoder.error
                decoded_hit = deep_decoder.decode(image, element.quad)
                if decoded_hit is not None:
                    hits.append(decoded_hit)

    for location_id, hit in enumerate(common_result.hits):
        if location_id not in used_location_ids:
            hits.append(hit)

    return hits, deep_decode_error


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


def render_detection_mats(file_path: str, page_records: List[PageData]) -> List[np.ndarray]:
    ext = Path(file_path).suffix.lower()

    if ext in PDF_EXTS:
        mats: List[np.ndarray] = []
        with fitz.open(file_path) as doc:
            for page in doc:
                pix = page.get_pixmap(dpi=PDF_DETECT_DPI, alpha=False)
                samples = np.frombuffer(pix.samples, dtype=np.uint8)
                if pix.n == 1:
                    pixels = samples.reshape((pix.height, pix.width))
                    mat = cv2.cvtColor(pixels, cv2.COLOR_GRAY2BGR)
                else:
                    pixels = samples.reshape((pix.height, pix.width, pix.n))
                    mat = cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR)
                mats.append(np.ascontiguousarray(mat))
        return mats

    if ext in TIFF_EXTS:
        ok, mats = cv2.imreadmulti(file_path, [], cv2.IMREAD_COLOR)
        if ok and mats:
            return [np.ascontiguousarray(mat) for mat in mats if mat is not None]

    mat = cv2.imread(file_path, cv2.IMREAD_COLOR)
    if mat is not None:
        return [np.ascontiguousarray(mat)]

    return [
        _qimage_to_bgr(page.image)
        for page in page_records
        if page.image is not None and not page.image.isNull()
    ]


# ---------------------------------------------------------------------------
# Scanner thread
# ---------------------------------------------------------------------------

class ScannerSignals(QObject):
    fileStarted = Signal(str, int)
    pageReady = Signal(object)
    fileMetricsReady = Signal(str, int, int, bool, str)
    fileFinished = Signal(str)
    allFinished = Signal()
    error = Signal(str, str)


class ScannerThread(QThread):
    def __init__(
        self,
        files: List[str],
        template: str,
        cached_pages: Optional[dict] = None,
        use_layout_analysis: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.files = list(files)
        self.template = template
        self.use_layout_analysis = use_layout_analysis and LAYOUT_ANALYSIS_AVAILABLE
        # {(file_path, page_idx) -> PageData} - rendered pages we can reuse
        # so a template-switch re-decode does not re-render PDFs/TIFFs.
        self.cached_pages = cached_pages or {}
        self.signals = ScannerSignals()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def _prepare_pages(self, file_path: str) -> List[PageData]:
        """Render pages or reuse cached renders. Emits fileStarted (only when
        the file was not previously loaded) and a placeholder pageReady for
        every page. Returns the list of PageData."""
        cached_keys = sorted(k for k in self.cached_pages if k[0] == file_path)
        if cached_keys:
            n_total = cached_keys[-1][1] + 1
            if all((file_path, i) in self.cached_pages for i in range(n_total)):
                records: List[PageData] = []
                for i in range(n_total):
                    old = self.cached_pages[(file_path, i)]
                    records.append(
                        PageData(
                            file_path=file_path,
                            page_index=i,
                            total_pages=n_total,
                            image=old.image,
                            detect_width=old.detect_width,
                            detect_height=old.detect_height,
                            barcodes=[],
                            error=None,
                        )
                    )
                # No fileStarted - the tree item already exists.
                for rec in records:
                    self.signals.pageReady.emit(rec)
                return records

        try:
            rendered = render_pages(file_path)
        except Exception as exc:
            self.signals.error.emit(
                file_path, f"Failed to render: {exc}\n{traceback.format_exc()}"
            )
            return []

        total_pages = len(rendered)
        if total_pages == 0:
            self.signals.error.emit(file_path, "No pages rendered.")
            return []

        self.signals.fileStarted.emit(file_path, total_pages)

        records = []
        for idx, (img, dw, dh) in enumerate(rendered):
            rec = PageData(
                file_path=file_path,
                page_index=idx,
                total_pages=total_pages,
                image=img,
                detect_width=dw,
                detect_height=dh,
            )
            records.append(rec)
            self.signals.pageReady.emit(rec)
        return records

    def _scan_with_layout_analysis(
        self, file_path: str, page_records: List[PageData]
    ) -> None:
        try:
            detection_images = render_detection_mats(file_path, page_records)
        except Exception as exc:
            self.signals.error.emit(
                file_path,
                f"Failed to render detection images: {exc}\n{traceback.format_exc()}",
            )
            return

        if not detection_images:
            self.signals.error.emit(file_path, "No detection images rendered.")
            return

        for page_index, page_record in enumerate(page_records):
            if self._stop:
                break
            if page_index >= len(detection_images):
                page_record.error = "No detection image rendered for this page."
                self.signals.pageReady.emit(page_record)
                continue

            detection_image = detection_images[page_index]
            page_start = time.perf_counter()
            try:
                hits, error = decode_with_layout_analysis(detection_image)
            except Exception as exc:
                page_record.error = f"Layout analysis failed: {exc}"
                page_record.decode_elapsed_ms = int(
                    (time.perf_counter() - page_start) * 1000
                )
                self.signals.pageReady.emit(page_record)
                continue

            page_record.detect_width = detection_image.shape[1]
            page_record.detect_height = detection_image.shape[0]
            page_record.barcodes = hits
            page_record.error = error
            page_record.decode_elapsed_ms = int((time.perf_counter() - page_start) * 1000)
            self.signals.pageReady.emit(page_record)

    def run(self) -> None:
        cvr: Optional[CaptureVisionRouter] = None
        if not self.use_layout_analysis:
            try:
                cvr = CaptureVisionRouter()
            except Exception as exc:
                self.signals.error.emit("", f"Failed to init CVR: {exc}")
                self.signals.allFinished.emit()
                return

        template = self.template

        for file_path in self.files:
            if self._stop:
                break

            page_records = self._prepare_pages(file_path)
            if not page_records:
                continue
            total_pages = len(page_records)

            if self._stop:
                break

            if self.use_layout_analysis:
                file_start = time.perf_counter()
                self._scan_with_layout_analysis(file_path, page_records)
                file_elapsed_ms = int((time.perf_counter() - file_start) * 1000)
                total_barcodes = sum(len(page_record.barcodes) for page_record in page_records)
                self.signals.fileMetricsReady.emit(
                    file_path, total_barcodes, file_elapsed_ms, True, self.template
                )
                self.signals.fileFinished.emit(file_path)
                continue

            file_start = time.perf_counter()
            try:
                if cvr is None:
                    raise RuntimeError("CaptureVisionRouter was not initialized.")
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
                file_elapsed_ms = int((time.perf_counter() - file_start) * 1000)
                self.signals.fileMetricsReady.emit(
                    file_path, 0, file_elapsed_ms, False, self.template
                )
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
                for item in page_result.get_items() or []:
                    if item.get_type() == EnumCapturedResultItemType.CRIT_BARCODE:
                        hits.append(_barcode_hit_from_item(item))
                page_records[page_idx].barcodes = hits
                self.signals.pageReady.emit(page_records[page_idx])

            file_elapsed_ms = int((time.perf_counter() - file_start) * 1000)
            total_barcodes = sum(len(page_record.barcodes) for page_record in page_records)
            if total_pages == 1 and page_records:
                page_records[0].decode_elapsed_ms = file_elapsed_ms
                self.signals.pageReady.emit(page_records[0])
            self.signals.fileMetricsReady.emit(
                file_path, total_barcodes, file_elapsed_ms, False, self.template
            )
            self.signals.fileFinished.emit(file_path)

        self.signals.allFinished.emit()


# ---------------------------------------------------------------------------
# Image viewer with overlays
# ---------------------------------------------------------------------------

class ImageViewer(QGraphicsView):
    filesDropped = Signal(list)

    _BG_NORMAL = QColor("#1e1f23")
    _BG_HOVER = QColor("#2d3a2a")

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
        self.setBackgroundBrush(QBrush(self._BG_NORMAL))
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._zoom = 0
        self._has_page = False
        self._show_drop_hint()

    def _show_drop_hint(self) -> None:
        hint = self._scene.addText("Drop images, PDFs, or a folder here")
        font = QFont()
        font.setPointSize(14)
        hint.setFont(font)
        hint.setDefaultTextColor(QColor("#8a8a8a"))
        self._scene.setSceneRect(hint.boundingRect().adjusted(-40, -40, 40, 40))

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
        # Reset any accumulated pan/zoom before fitting the current page again.
        self.resetTransform()
        target_rect = self._pixmap_item.sceneBoundingRect()
        self.centerOn(self._pixmap_item)
        self.fitInView(target_rect, Qt.AspectRatioMode.KeepAspectRatio)
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

    # ----- drag and drop ----------------------------------------------------

    @staticmethod
    def _urls_to_paths(mime) -> List[str]:
        paths: List[str] = []
        if mime.hasUrls():
            for url in mime.urls():
                local = url.toLocalFile()
                if local:
                    paths.append(local)
        return paths

    def dragEnterEvent(self, event) -> None:
        if self._urls_to_paths(event.mimeData()):
            event.acceptProposedAction()
            self.setBackgroundBrush(QBrush(self._BG_HOVER))
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if self._urls_to_paths(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event) -> None:
        self.setBackgroundBrush(QBrush(self._BG_NORMAL))
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        paths = self._urls_to_paths(event.mimeData())
        self.setBackgroundBrush(QBrush(self._BG_NORMAL))
        if paths:
            event.acceptProposedAction()
            self.filesDropped.emit(paths)
            return
        super().dropEvent(event)


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
        self._file_metrics: dict[str, FileScanMetrics] = {}
        self._file_items: dict[str, QTreeWidgetItem] = {}
        self._scanner: Optional[ScannerThread] = None
        self._license_ok = False
        self._barcode_total = 0
        self._auto_select_target: Optional[str] = None
        self._current_template: str = TEMPLATES[DEFAULT_TEMPLATE_INDEX][1]
        self._layout_analysis_enabled = False

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
        self._fit_act.triggered.connect(self._on_fit_to_window)
        toolbar.addAction(self._fit_act)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel(" Template: "))
        self._template_combo = QComboBox()
        for label, _value in TEMPLATES:
            self._template_combo.addItem(label)
        self._template_combo.setCurrentIndex(DEFAULT_TEMPLATE_INDEX)
        self._template_combo.setMinimumWidth(180)
        self._template_combo.setToolTip(
            "Capture Vision preset template. Changing it re-decodes the "
            "currently selected file."
        )
        self._template_combo.currentIndexChanged.connect(self._on_template_changed)
        toolbar.addWidget(self._template_combo)

        self._layout_analysis_checkbox = QCheckBox("Layout Analysis")
        self._layout_analysis_checkbox.setToolTip(
            "Use matrix layout analysis and deep decode for grid barcode images."
        )
        self._layout_analysis_checkbox.toggled.connect(
            self._on_layout_analysis_toggled
        )
        if not LAYOUT_ANALYSIS_AVAILABLE:
            self._layout_analysis_checkbox.setEnabled(False)
            self._layout_analysis_checkbox.setToolTip(
                LAYOUT_ANALYSIS_UNAVAILABLE_REASON
            )
        toolbar.addWidget(self._layout_analysis_checkbox)

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
        self.tree.setHeaderLabels(["File / Page", "Barcodes", "Time (ms)"])
        self.tree.setMinimumWidth(340)
        tree_header = self.tree.header()
        tree_header.setStretchLastSection(False)
        tree_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tree_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tree_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.currentItemChanged.connect(self._on_tree_changed)

        tree_panel = QWidget()
        tree_panel.setMinimumWidth(340)
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
        self.viewer.filesDropped.connect(self._enqueue_paths)

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
        splitter.setSizes([360, 640, 280])
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
            if LAYOUT_ANALYSIS_AVAILABLE:
                self._status_label.setText(
                    "License OK. Drop files/folders to scan. Check 'Layout Analysis' to enable grid analysis."
                )
            else:
                self._status_label.setText(
                    "License OK. Layout analysis is unavailable in this bundle version; standard decoding only."
                )
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

    def _on_template_changed(self, index: int) -> None:
        if index < 0 or index >= len(TEMPLATES):
            return
        label, value = TEMPLATES[index]
        self._current_template = value

        file_path = self._current_file_path()
        if not file_path:
            self._status_label.setText(f"Template -> {label}")
            return

        mode_label = "layout analysis" if self._layout_analysis_enabled else f"'{label}'"
        self._restart_current_file_decode(
            f"Re-decoding {os.path.basename(file_path)} with {mode_label}..."
        )

    def _on_fit_to_window(self) -> None:
        self.viewer.fit_to_window()
        if self.viewer._pixmap_item is not None:
            self._status_label.setText("Fitted current page to window.")

    def _on_layout_analysis_toggled(self, checked: bool) -> None:
        if checked and not LAYOUT_ANALYSIS_AVAILABLE:
            self._layout_analysis_checkbox.blockSignals(True)
            self._layout_analysis_checkbox.setChecked(False)
            self._layout_analysis_checkbox.blockSignals(False)
            self._layout_analysis_enabled = False
            self._status_label.setText(LAYOUT_ANALYSIS_UNAVAILABLE_REASON)
            return

        self._layout_analysis_enabled = checked
        file_path = self._current_file_path()
        mode_label = "layout analysis" if checked else "standard decoding"
        if not file_path:
            self._status_label.setText(f"Selected {mode_label}.")
            return

        self._restart_current_file_decode(
            f"Re-decoding {os.path.basename(file_path)} with {mode_label}..."
        )

    def _connect_scanner(self) -> None:
        if self._scanner is None:
            return
        self._scanner.signals.fileStarted.connect(self._on_file_started)
        self._scanner.signals.pageReady.connect(self._on_page_ready)
        self._scanner.signals.fileMetricsReady.connect(self._on_file_metrics_ready)
        self._scanner.signals.fileFinished.connect(self._on_file_finished)
        self._scanner.signals.allFinished.connect(self._on_all_finished)
        self._scanner.signals.error.connect(self._on_scan_error)

    def _restart_current_file_decode(self, status_text: str) -> None:
        file_path = self._current_file_path()
        if not file_path:
            self._status_label.setText(status_text)
            return

        cached = {
            key: page for key, page in self._pages.items() if key[0] == file_path
        }
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()
            self._scanner.wait(2000)

        self._auto_select_target = None  # keep the current selection
        self._progress.setVisible(True)
        self._status_label.setText(status_text)

        self._scanner = ScannerThread(
            [file_path],
            self._current_template,
            cached_pages=cached,
            use_layout_analysis=self._layout_analysis_enabled,
            parent=self,
        )
        self._connect_scanner()
        self._scanner.start()

    def _current_file_path(self) -> Optional[str]:
        item = self.tree.currentItem()
        if item is None:
            return None
        path = item.data(0, self.FILE_ROLE)
        return path if path else None

    def _on_clear(self) -> None:
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()
            self._scanner.wait(2000)
        self.tree.clear()
        self.results.clear()
        self.viewer.clear_view()
        self._pages.clear()
        self._file_metrics.clear()
        self._file_items.clear()
        self._barcode_total = 0
        self._auto_select_target = None
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

        # Auto-select the first page of the first newly dropped file as
        # soon as its placeholder render becomes available.
        self._auto_select_target = new_files[0]

        self._progress.setVisible(True)
        mode_text = " with layout analysis" if self._layout_analysis_enabled else ""
        self._status_label.setText(f"Scanning {len(new_files)} file(s){mode_text}...")

        self._scanner = ScannerThread(
            new_files,
            self._current_template,
            use_layout_analysis=self._layout_analysis_enabled,
            parent=self,
        )
        self._connect_scanner()
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
        item = QTreeWidgetItem([os.path.basename(file_path), "...", "..."])
        item.setToolTip(0, file_path)
        item.setData(0, self.FILE_ROLE, file_path)
        self.tree.addTopLevelItem(item)
        self._file_items[file_path] = item
        if total_pages > 1:
            item.setExpanded(True)

    def _on_file_metrics_ready(
        self,
        file_path: str,
        barcode_count: int,
        decode_elapsed_ms: int,
        used_layout_analysis: bool,
        template: str,
    ) -> None:
        self._file_metrics[file_path] = FileScanMetrics(
            barcode_count=barcode_count,
            decode_elapsed_ms=decode_elapsed_ms,
            used_layout_analysis=used_layout_analysis,
            template=template,
        )

        item = self._file_items.get(file_path)
        if item is not None:
            item.setText(1, str(barcode_count))
            item.setText(2, str(decode_elapsed_ms))

        current = self.tree.currentItem()
        if current is not None:
            page = self._page_from_item(current)
            if page is not None and page.file_path == file_path:
                self._show_page(page)

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
        decode_text = (
            str(page.decode_elapsed_ms) if page.decode_elapsed_ms is not None else ""
        )
        if page.total_pages == 1:
            parent.setText(1, str(n_bc))
            parent.setText(2, decode_text)
            parent.setData(0, self.PAGE_ROLE, 0)
            target_item = parent
        else:
            if existing_child is None:
                child = QTreeWidgetItem(
                    [f"Page {page.page_index + 1}", str(n_bc), decode_text]
                )
                child.setData(0, self.PAGE_ROLE, page.page_index)
                child.setData(0, self.FILE_ROLE, page.file_path)
                parent.addChild(child)
                target_item = child
            else:
                existing_child.setText(1, str(n_bc))
                existing_child.setText(2, decode_text)
                target_item = existing_child
            # roll up total count
            total = sum(
                len(self._pages.get((page.file_path, i), PageData(page.file_path, i, 0)).barcodes)
                for i in range(page.total_pages)
            )
            parent.setText(1, str(total))

        metrics = self._file_metrics.get(page.file_path)
        if metrics is not None and metrics.decode_elapsed_ms is not None:
            parent.setText(2, str(metrics.decode_elapsed_ms))

        # Auto-select the first page of the most recently dropped batch as
        # soon as its placeholder render appears, so the user sees the file
        # immediately. Falls back to picking up the first page that arrives
        # if nothing is selected yet.
        if (
            self._auto_select_target == page.file_path
            and page.page_index == 0
        ):
            self._auto_select_target = None
            if self.tree.currentItem() is not target_item:
                self.tree.setCurrentItem(target_item)
            else:
                self._show_page(page)
        elif self.tree.currentItem() is None:
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
        total_elapsed_ms = sum(
            metrics.decode_elapsed_ms or 0 for metrics in self._file_metrics.values()
        )
        self._barcode_total = total_bc
        self._status_label.setText(
            f"Done. {total_pages} page(s), {total_bc} barcode(s), {total_elapsed_ms} ms total."
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

        file_path = current.data(0, self.FILE_ROLE)
        if file_path:
            if self._file_needs_redecode(file_path):
                mode_label = (
                    "layout analysis" if self._layout_analysis_enabled else "standard decoding"
                )
                self._restart_selected_file_decode(
                    file_path,
                    f"Re-decoding {os.path.basename(file_path)} with {mode_label}...",
                )
                return

        page = self._page_from_item(current)
        if page is not None:
            self._show_page(page)
        else:
            self.viewer.clear_view()
            self.results.clear()
            self._page_label.setText(os.path.basename(current.data(0, self.FILE_ROLE) or ""))
            self._update_nav_state()

    def _restart_selected_file_decode(self, file_path: str, status_text: str) -> None:
        if not file_path:
            self._status_label.setText(status_text)
            return

        cached = {
            key: page for key, page in self._pages.items() if key[0] == file_path
        }
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()
            self._scanner.wait(2000)

        self._auto_select_target = None
        self._progress.setVisible(True)
        self._status_label.setText(status_text)

        self._scanner = ScannerThread(
            [file_path],
            self._current_template,
            cached_pages=cached,
            use_layout_analysis=self._layout_analysis_enabled,
            parent=self,
        )
        self._connect_scanner()
        self._scanner.start()

    def _page_from_item(self, item: QTreeWidgetItem) -> Optional[PageData]:
        page_idx = item.data(0, self.PAGE_ROLE)
        file_path = item.data(0, self.FILE_ROLE)
        if file_path is None or page_idx is None:
            return None
        return self._pages.get((file_path, int(page_idx)))

    def _decode_mode_label(self, file_path: str) -> str:
        metrics = self._file_metrics.get(file_path)
        if metrics is not None and metrics.used_layout_analysis:
            return "Layout analysis"
        return "Standard decoding"

    def _file_needs_redecode(self, file_path: str) -> bool:
        metrics = self._file_metrics.get(file_path)
        if metrics is None:
            return False
        if self._layout_analysis_enabled:
            return not metrics.used_layout_analysis
        return metrics.used_layout_analysis or metrics.template != self._current_template

    def _show_page(self, page: PageData) -> None:
        self.viewer.set_page(page)
        self.results.clear()

        metrics = self._file_metrics.get(page.file_path)
        mode_label = self._decode_mode_label(page.file_path)
        decode_elapsed_ms = page.decode_elapsed_ms
        decode_scope = "Decode"
        if decode_elapsed_ms is None and metrics is not None:
            decode_elapsed_ms = metrics.decode_elapsed_ms
            decode_scope = "File decode"

        info_text = f"[info] Mode: {mode_label} | Count: {len(page.barcodes)} barcode(s)"
        if decode_elapsed_ms is not None:
            info_text += f" | {decode_scope} time: {decode_elapsed_ms} ms"
        info_item = QListWidgetItem(info_text)
        info_item.setForeground(QBrush(QColor("#1c7ed6")))
        self.results.addItem(info_item)

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
        page_text = (
            f"{os.path.basename(page.file_path)}    "
            f"Page {page.page_index + 1} / {page.total_pages}    "
            f"{len(page.barcodes)} barcode(s)    "
            f"Mode: {mode_label}"
        )
        if decode_elapsed_ms is not None:
            page_text += f"    {decode_scope}: {decode_elapsed_ms} ms"
        self._page_label.setText(page_text)
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
