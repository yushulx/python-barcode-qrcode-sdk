import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QImage, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from dynamsoft_capture_vision_bundle import (
    CaptureVisionRouter,
    EnumImagePixelFormat,
    LicenseManager,
)


LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="

TEMPLATE_NAME_PREFERENCES = (
    "U22288",
    "ReadPageQrAndNumber_OneShot",
    "ReadPageQrAndNumber_ByBarcodeRef",
)

SUPPORTED_IMAGE_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
)


BarcodeResultCallback = Callable[[List["BarcodeHit"]], None]
TextResultCallback = Callable[[List["TextHit"]], None]


@dataclass
class BarcodeHit:
    text: str
    fmt: str
    confidence: int
    points: List[Tuple[float, float]]
    variant: str


@dataclass
class TextHit:
    text: str
    confidence: int
    points: List[Tuple[float, float]]
    variant: str


@dataclass
class ScanResult:
    barcodes: List[BarcodeHit]
    text_lines: List[TextHit]
    page_number: Optional[str]
    logs: List[str]


def _is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES


def _expand_image_paths(paths: Sequence[Path]) -> List[Path]:
    expanded: List[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(
                child
                for child in sorted(path.rglob("*"))
                if child.is_file() and _is_supported_image(child)
            )
        elif path.is_file() and _is_supported_image(path):
            expanded.append(path)
    return expanded


def _extract_drop_image_paths(urls) -> List[Path]:
    local_paths = [Path(url.toLocalFile()) for url in urls if url.isLocalFile()]
    return _expand_image_paths(local_paths)


class CaptureVisionPageScanner:
    def __init__(self, template_path: Path) -> None:
        self._template_path = template_path
        self._init_license()
        self._template_name = self._resolve_template_name(template_path)

        self._template_router = CaptureVisionRouter()
        err, msg = self._template_router.init_settings_from_file(str(template_path))
        if err != 0:
            raise RuntimeError(f"Failed to load template file: {msg}")

    @staticmethod
    def _init_license() -> None:
        err, msg = LicenseManager.init_license(LICENSE_KEY)
        if err != 0:
            print(f"[DCV] License warning ({err}): {msg}")

    @staticmethod
    def _resolve_template_name(template_path: Path) -> str:
        try:
            data = json.loads(template_path.read_text(encoding="utf-8"))
        except Exception:
            return TEMPLATE_NAME_PREFERENCES[0]

        names = [
            item.get("Name", "")
            for item in (data.get("CaptureVisionTemplates") or [])
            if isinstance(item, dict)
        ]
        for preferred in TEMPLATE_NAME_PREFERENCES:
            if preferred in names:
                return preferred
        return names[0] if names else TEMPLATE_NAME_PREFERENCES[0]

    @staticmethod
    def _rescale_points(
        points: Sequence[Tuple[float, float]],
        scale: float,
        offset: Tuple[float, float] = (0.0, 0.0),
    ) -> List[Tuple[float, float]]:
        ox, oy = offset
        return [((x / scale) + ox, (y / scale) + oy) for x, y in points]

    @staticmethod
    def _extract_barcodes(captured_result, variant: str) -> List[BarcodeHit]:
        hits: List[BarcodeHit] = []
        barcode_result = captured_result.get_decoded_barcodes_result() if captured_result else None
        if barcode_result is None:
            return hits

        items = barcode_result.get_items() or []
        for item in items:
            loc = item.get_location()
            points = []
            if loc and getattr(loc, "points", None):
                points = [(float(p.x), float(p.y)) for p in loc.points]
            hits.append(
                BarcodeHit(
                    text=item.get_text() or "",
                    fmt=item.get_format_string() or "UNKNOWN",
                    confidence=int(item.get_confidence() or 0),
                    points=points,
                    variant=variant,
                )
            )
        return hits

    @staticmethod
    def _extract_text_lines(captured_result, variant: str) -> List[TextHit]:
        hits: List[TextHit] = []
        text_result = (
            captured_result.get_recognized_text_lines_result() if captured_result else None
        )
        if text_result is None:
            return hits

        items = text_result.get_items() or []
        for item in items:
            raw_text = (item.get_text() or "").strip()
            if not raw_text:
                continue

            loc = item.get_location()
            points = []
            if loc and getattr(loc, "points", None):
                points = [(float(p.x), float(p.y)) for p in loc.points]
            hits.append(
                TextHit(
                    text=raw_text,
                    confidence=int(item.get_confidence() or 0),
                    points=points,
                    variant=variant,
                )
            )
        return hits

    @staticmethod
    def _dedupe_barcodes(hits: Sequence[BarcodeHit]) -> List[BarcodeHit]:
        deduped: List[BarcodeHit] = []
        seen = set()
        for hit in hits:
            rounded = tuple((round(x, 1), round(y, 1)) for x, y in hit.points)
            key = (hit.text, hit.fmt, rounded)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(hit)
        return deduped

    @staticmethod
    def _dedupe_text_lines(hits: Sequence[TextHit]) -> List[TextHit]:
        deduped: List[TextHit] = []
        seen = set()
        for hit in hits:
            rounded = tuple((round(x, 1), round(y, 1)) for x, y in hit.points)
            key = (hit.text, rounded)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(hit)
        return deduped

    def _capture_with_template(self, image: np.ndarray, template_name: str):
        return self._template_router.capture(
            image,
            EnumImagePixelFormat.IPF_BGR_888,
            template_name,
        )

    def _capture_with_template_file(self, image_path: Path, template_name: str):
        results = self._template_router.capture_multi_pages(str(image_path), template_name)
        if results is None:
            return None
        items = results.get_results() or []
        return items[0] if items else None

    @staticmethod
    def _pick_page_number(
        text_hits: Sequence[TextHit],
        barcode_hits: Sequence[BarcodeHit],
    ) -> Optional[str]:
        anchor: Optional[Tuple[float, float, float, float]] = None
        if barcode_hits:
            primary = max(barcode_hits, key=lambda hit: hit.confidence)
            if primary.points:
                xs = [p[0] for p in primary.points]
                ys = [p[1] for p in primary.points]
                cx = (min(xs) + max(xs)) * 0.5
                cy = (min(ys) + max(ys)) * 0.5
                bw = max(max(xs) - min(xs), 1.0)
                bh = max(max(ys) - min(ys), 1.0)
                anchor = (cx, cy, bw, bh)

        candidates: List[Tuple[float, str]] = []
        for hit in text_hits:
            raw = hit.text.strip()
            if not raw:
                continue

            if hit.points:
                xs = [p[0] for p in hit.points]
                ys = [p[1] for p in hit.points]
                box_w = max(xs) - min(xs)
                box_h = max(ys) - min(ys)
                # Ignore tiny noise-like OCR boxes that commonly become 111/1114.
                if box_w < 6.0 or box_h < 6.0:
                    continue

            score = float(hit.confidence) * 10.0

            if anchor and hit.points:
                ax, ay, aw, ah = anchor
                hx = (min(xs) + max(xs)) * 0.5
                hy = (min(ys) + max(ys)) * 0.5
                dx = ax - hx
                dy = ay - hy

                # For this fixed page layout, page number tends to be left/above QR.
                expected_dx = 2.0 * aw
                expected_dy = 1.0 * ah
                score -= (abs(dx - expected_dx) / aw) * 8.0
                score -= (abs(dy - expected_dy) / ah) * 4.0

                if dx <= 0:
                    score -= 25.0

            candidates.append((score, raw))

        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def detect(
        self,
        image_bgr: np.ndarray,
        image_path: Optional[Path] = None,
        on_barcodes: Optional[BarcodeResultCallback] = None,
        on_text_lines: Optional[TextResultCallback] = None,
    ) -> ScanResult:
        logs: List[str] = []

        captured = None
        scale = 1.0

        if image_path is not None and image_path.exists():
            logs.append(
                f"[CAPTURE] template={self._template_name}, source=file"
            )
            captured = self._capture_with_template_file(image_path, self._template_name)
        else:
            logs.append(
                f"[CAPTURE] template={self._template_name}, source=array"
            )
            captured = self._capture_with_template(image_bgr, self._template_name)

        if captured is None:
            logs.append("[CAPTURE] file/array capture returned no result, fallback=array")
            captured = self._capture_with_template(image_bgr, self._template_name)

        err_code = int(captured.get_error_code())
        err_msg = captured.get_error_string() or ""
        logs.append(f"[CAPTURE] err={err_code}, msg={err_msg}")

        variant = "oneshot/file" if image_path is not None and image_path.exists() else "oneshot/array"

        barcodes = self._extract_barcodes(captured, variant)
        for hit in barcodes:
            hit.points = self._rescale_points(hit.points, scale)
        barcodes = self._dedupe_barcodes(barcodes)

        text_lines = self._extract_text_lines(captured, variant)
        for hit in text_lines:
            hit.points = self._rescale_points(hit.points, scale)
        text_lines = self._dedupe_text_lines(text_lines)

        if on_barcodes is not None:
            on_barcodes(barcodes)
            logs.append(f"[CALLBACK] on_barcodes: {len(barcodes)}")
        if on_text_lines is not None:
            on_text_lines(text_lines)
            logs.append(f"[CALLBACK] on_text_lines: {len(text_lines)}")

        page_number = self._pick_page_number(text_lines, barcodes)
        logs.append(
            f"[SUMMARY] barcodes={len(barcodes)}, text_lines={len(text_lines)}, page_number={page_number}"
        )
        return ScanResult(barcodes=barcodes, text_lines=text_lines, page_number=page_number, logs=logs)


class ImageView(QGraphicsView):
    files_dropped = Signal(list)

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(
            self.renderHints() | QPainter.Antialiasing | QPainter.TextAntialiasing
        )
        self.setBackgroundBrush(Qt.black)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setAcceptDrops(True)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(1.2, 1.2)
        else:
            self.scale(1 / 1.2, 1 / 1.2)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = _extract_drop_image_paths(event.mimeData().urls())
            if paths:
                self.files_dropped.emit([str(path) for path in paths])
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class FileListWidget(QListWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = _extract_drop_image_paths(event.mimeData().urls())
            if paths:
                self.files_dropped.emit([str(path) for path in paths])
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class PageQrOcrWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Page QR + OCR Scanner (Dynamsoft Capture Vision)")
        self.resize(1320, 840)

        self._file_paths: List[Path] = []
        self._current_index: int = -1
        self._image_bgr: Optional[np.ndarray] = None
        self._image_path: Optional[Path] = None
        self._scan_result: Optional[ScanResult] = None
        self._image_rect: Optional[QRectF] = None
        self._main_splitter: Optional[QSplitter] = None

        template_path = Path(__file__).with_name("page_qr_ocr_template.json")
        self._scanner = CaptureVisionPageScanner(template_path)

        self._scene = QGraphicsScene(self)
        self._view = ImageView(self._scene, self)
        self._view.files_dropped.connect(self._add_paths)

        self._file_list = FileListWidget(self)
        self._file_list.setAlternatingRowColors(True)
        self._file_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._file_list.currentRowChanged.connect(self._on_file_selected)
        self._file_list.files_dropped.connect(self._add_paths)

        self._status_label = QLabel("Load images to start.")
        self._barcode_label = QLabel("Barcodes: 0")
        self._page_number_label = QLabel("Page number: -")
        self._nav_label = QLabel("0 / 0")
        self._nav_label.setAlignment(Qt.AlignCenter)
        self._log_box = QPlainTextEdit()
        self._log_box.setReadOnly(True)
        self._log_box.setMaximumHeight(180)

        self._toggle_log_btn = QPushButton("Hide Log")
        self._toggle_log_btn.setCheckable(True)
        self._toggle_log_btn.toggled.connect(self._on_toggle_log)

        self._prev_btn = QPushButton("< Prev")
        self._prev_btn.clicked.connect(self._prev_image)
        self._next_btn = QPushButton("Next >")
        self._next_btn.clicked.connect(self._next_image)

        self._build_ui()
        self._update_navigation()

    def _build_ui(self) -> None:
        load_btn = QPushButton("Load Images...")
        load_btn.clicked.connect(self._on_load_images)

        clear_btn = QPushButton("Clear Images")
        clear_btn.clicked.connect(self._clear_images)

        top_bar = QHBoxLayout()
        top_bar.addWidget(load_btn)
        top_bar.addWidget(clear_btn)
        top_bar.addSpacing(12)
        top_bar.addWidget(self._prev_btn)
        top_bar.addWidget(self._nav_label)
        top_bar.addWidget(self._next_btn)
        top_bar.addSpacing(12)
        top_bar.addWidget(self._toggle_log_btn)
        top_bar.addStretch(1)

        stats_bar = QHBoxLayout()
        stats_bar.addWidget(self._status_label, 4)
        stats_bar.addWidget(self._barcode_label, 1)
        stats_bar.addWidget(self._page_number_label, 1)

        log_panel = QWidget()
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addWidget(QLabel("Run Log"))
        log_layout.addWidget(self._log_box, 1)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._view)
        splitter.addWidget(log_panel)
        splitter.setStretchFactor(0, 8)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([700, 140])
        self._main_splitter = splitter

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Files"))
        left_layout.addWidget(self._file_list, 1)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addLayout(stats_bar)
        right_layout.addWidget(splitter, 1)

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setSizes([260, 1000])

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.addLayout(top_bar)
        root_layout.addWidget(content_splitter, 1)
        self.setCentralWidget(root)

    def _on_toggle_log(self, hidden: bool) -> None:
        self._log_box.parentWidget().setVisible(not hidden)
        self._toggle_log_btn.setText("Show Log" if hidden else "Hide Log")
        if self._main_splitter is not None:
            if hidden:
                self._main_splitter.setSizes([1, 0])
            else:
                self._main_splitter.setSizes([700, 140])

    def _on_load_images(self) -> None:
        path_strs, _ = QFileDialog.getOpenFileNames(
            self,
            "Load Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)",
        )
        if not path_strs:
            return

        self._add_paths(path_strs)

    def _add_paths(self, raw_paths: Sequence[str]) -> None:
        candidate_paths = _expand_image_paths([Path(path) for path in raw_paths])
        if not candidate_paths:
            self._status_label.setText("No supported images found in dropped or selected items.")
            return

        existing = {str(path.resolve()): index for index, path in enumerate(self._file_paths)}
        added = 0
        for path in candidate_paths:
            key = str(path.resolve())
            if key in existing:
                continue
            existing[key] = len(self._file_paths)
            self._file_paths.append(path)

            item = QListWidgetItem(path.name)
            item.setData(Qt.UserRole, str(path))
            item.setToolTip(str(path))
            self._file_list.addItem(item)
            added += 1

        if added == 0:
            self._status_label.setText(f"No new files added. Total images: {len(self._file_paths)}")
            self._update_navigation()
            return

        self._status_label.setText(f"Added {added} image(s). Total images: {len(self._file_paths)}")
        if self._current_index < 0 and self._file_paths:
            self._select_index(0)
        self._update_navigation()

    def _on_file_selected(self, row: int) -> None:
        if row < 0 or row >= len(self._file_paths):
            return
        self._load_image_at_index(row)

    def _select_index(self, index: int) -> None:
        if not self._file_paths:
            return
        bounded = max(0, min(index, len(self._file_paths) - 1))
        if self._file_list.currentRow() != bounded:
            self._file_list.setCurrentRow(bounded)
        else:
            self._load_image_at_index(bounded)

    def _load_image_at_index(self, index: int) -> None:
        if index < 0 or index >= len(self._file_paths):
            return

        image_path = self._file_paths[index]
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            QMessageBox.warning(self, "Load Failed", f"Cannot open image: {image_path}")
            return

        self._current_index = index

        self._image_bgr = image_bgr
        self._image_path = image_path
        self._scan_result = None
        self._image_rect = None

        self._status_label.setText(f"Image {index + 1}/{len(self._file_paths)}: {image_path}")
        self._barcode_label.setText("Barcodes: 0")
        self._page_number_label.setText("Page number: -")
        self._log_box.setPlainText("")

        self._redraw_scene()
        self._update_navigation()
        self._on_detect()

    def _update_navigation(self) -> None:
        total = len(self._file_paths)
        current = self._current_index + 1 if self._current_index >= 0 else 0
        self._nav_label.setText(f"{current} / {total}")

        has_items = total > 0
        self._prev_btn.setEnabled(has_items and self._current_index > 0)
        self._next_btn.setEnabled(has_items and 0 <= self._current_index < total - 1)

    def _prev_image(self) -> None:
        if self._current_index <= 0:
            return
        self._select_index(self._current_index - 1)

    def _next_image(self) -> None:
        if self._current_index < 0 and self._file_paths:
            self._select_index(0)
            return
        if self._current_index >= len(self._file_paths) - 1:
            return
        self._select_index(self._current_index + 1)

    def _on_detect(self) -> None:
        if self._image_bgr is None:
            QMessageBox.information(self, "No Image", "Load an image first.")
            return

        callback_barcodes: List[BarcodeHit] = []
        callback_text_lines: List[TextHit] = []

        def on_barcodes_received(hits: List[BarcodeHit]) -> None:
            callback_barcodes.clear()
            callback_barcodes.extend(hits)

        def on_text_lines_received(hits: List[TextHit]) -> None:
            callback_text_lines.clear()
            callback_text_lines.extend(hits)

        try:
            result = self._scanner.detect(
                self._image_bgr,
                image_path=self._image_path,
                on_barcodes=on_barcodes_received,
                on_text_lines=on_text_lines_received,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Detection Error", str(exc))
            return

        self._scan_result = result
        self._barcode_label.setText(f"Barcodes: {len(callback_barcodes)}")
        self._page_number_label.setText(f"Page number: {result.page_number or '-'}")
        self._log_box.setPlainText("\n".join(result.logs))

        self._redraw_scene()

    def _clear_images(self) -> None:
        self._file_paths.clear()
        self._current_index = -1
        self._image_bgr = None
        self._image_path = None
        self._scan_result = None
        self._image_rect = None

        self._file_list.clear()
        self._scene.clear()
        self._scene.setSceneRect(QRectF())
        self._view.resetTransform()

        self._status_label.setText("Load images to start.")
        self._barcode_label.setText("Barcodes: 0")
        self._page_number_label.setText("Page number: -")
        self._log_box.setPlainText("")
        self._update_navigation()

    @staticmethod
    def _to_qpixmap(image_bgr: np.ndarray) -> QPixmap:
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())

    def _add_polygon(
        self,
        points: Sequence[Tuple[float, float]],
        color: Qt.GlobalColor,
        text: Optional[str] = None,
        dashed: bool = False,
    ) -> None:
        if len(points) < 4:
            return

        polygon = QPolygonF([QPointF(x, y) for x, y in points])
        item = QGraphicsPolygonItem(polygon)
        pen = QPen(color)
        pen.setWidth(3)
        if dashed:
            pen.setStyle(Qt.DashLine)
        item.setPen(pen)
        self._scene.addItem(item)

        if text:
            tx, ty = points[0]
            label_item = QGraphicsTextItem(text)
            label_item.setDefaultTextColor(color)
            label_item.setPos(tx + 4, ty - 22)
            self._scene.addItem(label_item)

    def _redraw_scene(self) -> None:
        self._scene.clear()
        self._image_rect = None
        if self._image_bgr is None:
            return

        pixmap = self._to_qpixmap(self._image_bgr)
        pixmap_item = self._scene.addPixmap(pixmap)
        self._image_rect = pixmap_item.boundingRect()
        self._scene.setSceneRect(self._image_rect)

        if self._scan_result is not None:
            for hit in self._scan_result.barcodes:
                label = f"{hit.fmt}: {hit.text}"
                self._add_polygon(hit.points, Qt.blue, label)

            for hit in self._scan_result.text_lines:
                if not hit.text:
                    continue
                label = f"OCR: {hit.text}"
                self._add_polygon(hit.points, Qt.red, label)

        self._view.resetTransform()
        if self._image_rect is not None and not self._image_rect.isNull():
            self._view.fitInView(self._image_rect, Qt.KeepAspectRatio)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Left:
            self._prev_image()
            return
        if event.key() == Qt.Key_Right:
            self._next_image()
            return
        super().keyPressEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    win = PageQrOcrWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())