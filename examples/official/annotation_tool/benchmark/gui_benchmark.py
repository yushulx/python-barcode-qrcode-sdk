#!/usr/bin/env python3
"""
GUI Benchmark Application for Barcode Readers
PySide6-based application with drag-and-drop support, SDK configuration, and HTML report export.
"""

import sys
import os
import json
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QProgressDialog, QGroupBox, QCheckBox,
    QLineEdit, QDialog, QDialogButtonBox, QFormLayout, QTextEdit,
    QTabWidget, QProgressBar, QComboBox, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QImage, QPixmap

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.barcode_readers import create_reader
from src.benchmark_framework import BenchmarkResult, TestCase


@dataclass
class BenchmarkTask:
    """Represents a single benchmark task."""
    file_path: str
    file_type: str  # 'image' or 'video'
    expected_barcodes: Optional[List[str]] = None  # Expected barcode values for this file


@dataclass
class FrameResult:
    """Result for a single frame/image."""
    file_path: str
    library_name: str
    barcodes_detected: int
    detected_data: List[Dict[str, str]]  # [{'data': ..., 'type': ...}]
    detection_time_ms: float
    expected_barcodes: List[str] = None
    is_correct: Optional[bool] = None  # None means no annotation for validation


class VideoFrameExtractor:
    """Extract frames from video files using OpenCV."""

    @staticmethod
    def extract_frames(video_path: str, output_dir: str, max_frames: int = 10) -> List[str]:
        """Extract frames from video file."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames <= max_frames:
            frame_indices = list(range(total_frames))
        else:
            frame_indices = [int(i * total_frames / max_frames) for i in range(max_frames)]

        extracted_frames = []
        video_name = Path(video_path).stem

        for idx, frame_idx in enumerate(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frame_path = os.path.join(output_dir, f"{video_name}_frame_{idx:03d}.jpg")
                cv2.imwrite(frame_path, frame)
                extracted_frames.append(frame_path)

        cap.release()
        return extracted_frames


class AnnotationConverter:
    """Convert between different annotation formats."""

    @staticmethod
    def from_dynamsoft_format(dynamsoft_json: Dict[str, Any], image_dir: Optional[str] = None) -> Dict[str, Any]:
        """Convert from Dynamsoft annotation format to benchmark format.
        
        Input format:
        {
            "images": [
                {"file_name": "IMG_8743", "barcodes": [{"value": "..."}]}
            ]
        }
        
        Output format:
        {
            "format": "barcode-benchmark/1.0",
            "images": [
                {"file": "IMG_8743.JPG", "barcodes": ["...", "..."]}
            ]
        }
        """
        images = []
        for entry in dynamsoft_json.get('images', []):
            filename = entry.get('file_name', '')
            barcodes = [bc['value'] for bc in entry.get('barcodes', []) if 'value' in bc]
            
            if barcodes:
                # Try to find actual file with extension
                if image_dir:
                    img_path = Path(image_dir)
                    if img_path.exists():
                        for f in img_path.iterdir():
                            if f.stem == filename:
                                filename = f.name
                                break
                
                images.append({
                    'file': filename,
                    'barcodes': barcodes
                })
        
        return {
            'format': 'barcode-benchmark/1.0',
            'images': images
        }

    @staticmethod
    def load_and_convert(file_path: str) -> Dict[str, List[str]]:
        """Load annotation file and return as filename->barcodes mapping.
        
        Supports:
        1. Benchmark format: {"format": "barcode-benchmark/1.0", "images": [...]}
        2. Dynamsoft format: {"images": [{"file_name": "...", "barcodes": [...]}]}
        3. Simple format: {"filename.jpg": ["barcode1", "barcode2"]}
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Benchmark format (annotation_app: barcodes are {"text": ..., "format": ..., "points": ...})
        if 'format' in data and data['format'].startswith('barcode-benchmark'):
            result = {}
            for img in data.get('images', []):
                barcodes = img.get('barcodes', [])
                texts = []
                for bc in barcodes:
                    if isinstance(bc, str):
                        texts.append(bc)
                    elif isinstance(bc, dict):
                        text = bc.get('text', '')
                        if text:
                            texts.append(text)
                result[img['file']] = texts
            return result
        
        # Dynamsoft format
        if 'images' in data:
            result = {}
            for img in data['images']:
                filename = img.get('file_name', '')
                barcodes = [bc['value'] for bc in img.get('barcodes', []) if 'value' in bc]
                if barcodes:
                    result[filename] = barcodes
            return result
        
        # Simple format: direct mapping
        if 'annotations' in data:
            return data['annotations']
        return data


class AnnotationValidator:
    """Validate detected barcodes against expected values."""

    _CONTROL_TOKEN_MAP = {
        '<NUL>': '\x00',
        '␀': '\x00',
        '<EOT>': '\x04',
        '␄': '\x04',
        '<GS>': '\x1d',
        '[GS]': '\x1d',
        '␝': '\x1d',
        '<RS>': '\x1e',
        '␞': '\x1e',
    }

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize line endings and control-character placeholders."""
        normalized = value.replace('\r\n', '\n').replace('\r', '\n').strip()
        for token, replacement in AnnotationValidator._CONTROL_TOKEN_MAP.items():
            normalized = normalized.replace(token, replacement)
        return normalized

    @staticmethod
    def _normalize_gs1_text(value: str) -> str:
        """Normalize GS1 text so human-friendly AI formatting still matches raw content."""
        normalized = AnnotationValidator._normalize_text(value)
        for token in ('(', ')', '\x1d', '\x1e', '\x04'):
            normalized = normalized.replace(token, '')
        return normalized

    @staticmethod
    def _match_texts(detected: str, expected: str) -> bool:
        """Flexible barcode text matching with UPC/EAN equivalence."""
        detected = AnnotationValidator._normalize_text(detected)
        expected = AnnotationValidator._normalize_text(expected)

        if detected == expected:
            return True

        # ZXing may return human-friendly GS1 text like (01)900... while GT stores 01900...
        normalized_detected = AnnotationValidator._normalize_gs1_text(detected)
        normalized_expected = AnnotationValidator._normalize_gs1_text(expected)
        if normalized_detected == normalized_expected:
            return True

        detected = normalized_detected
        expected = normalized_expected

        # EAN/UPC add-on extensions may be present in GT but omitted by decoders.
        if detected.isdigit() and expected.isdigit() and abs(len(detected) - len(expected)) in (2, 5):
            if detected.startswith(expected) or expected.startswith(detected):
                return True

        # UPC-A (12 digits) <-> EAN-13 (13 digits with leading 0)
        if len(detected) == 12 and len(expected) == 13 and expected == '0' + detected:
            return True
        if len(detected) == 13 and len(expected) == 12 and detected == '0' + expected:
            return True
        # Detected may have appended check digit (up to 2 extra chars)
        if detected.startswith(expected) and len(detected) <= len(expected) + 2:
            return True
        return False

    @staticmethod
    def validate(detected: List[Dict[str, str]], expected: List[str]) -> Dict[str, Any]:
        """Validate detected barcodes against expected values.
        
        Uses list-based matching to correctly handle duplicate barcodes in same image.
        Returns barcode-level TP/FP/FN counts.
        """
        if not expected:
            return {
                'is_correct': None,  # No annotation to validate against
                'expected_count': 0,
                'found_count': len(detected),
                'matched': 0,
                'tp': 0,
                'fp': len(detected),
                'fn': 0,
                'missing': [],
                'extra': [bc.get('data', '') for bc in detected]
            }

        detected_texts = [bc.get('data', '').strip() for bc in detected]
        expected_texts = [v.strip() for v in expected]

        # Greedy 1-to-1 matching: each expected matched to at most one detected
        matched_detected_indices = set()
        matched_expected_indices = set()
        missing = []

        for i, exp in enumerate(expected_texts):
            for j, det in enumerate(detected_texts):
                if j not in matched_detected_indices and AnnotationValidator._match_texts(det, exp):
                    matched_expected_indices.add(i)
                    matched_detected_indices.add(j)
                    break
            else:
                missing.append(exp)

        tp = len(matched_expected_indices)
        fp = len(detected_texts) - len(matched_detected_indices)
        fn = len(expected_texts) - tp
        extra = [detected_texts[j] for j in range(len(detected_texts)) if j not in matched_detected_indices]

        exact_match = (fn == 0 and fp == 0 and tp == len(expected_texts))

        return {
            'is_correct': exact_match,
            'exact_match': exact_match,
            'expected_count': len(expected_texts),
            'found_count': len(detected_texts),
            'matched': tp,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'missing': missing,
            'extra': extra
        }

    @staticmethod
    def classify_validation(validation: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Return a display-friendly validation bucket for grouping benchmark results."""
        if not validation:
            return {
                'group': 'No Annotation',
                'order': 2,
                'status': 'No Annotation',
            }

        if validation.get('exact_match') or validation.get('is_correct'):
            return {
                'group': 'Exact Match',
                'order': 1,
                'status': '✓ Exact Match',
            }

        parts = []
        missing_count = len(validation.get('missing', []))
        extra_count = len(validation.get('extra', []))
        if missing_count:
            parts.append(f'Missing {missing_count}')
        if extra_count:
            parts.append(f'Extra {extra_count}')

        return {
            'group': 'Needs Review',
            'order': 0,
            'status': '✗ ' + (' / '.join(parts) if parts else 'Mismatch'),
        }


class AnnotationLoaderWorker(QThread):
    """Worker thread for loading annotation JSON files without blocking the UI."""

    finished = Signal(dict, dict)  # annotation_data, annotation_full_data
    error = Signal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            annotation_data = AnnotationConverter.load_and_convert(self.file_path)

            annotation_full_data = {}
            with open(self.file_path, 'r', encoding='utf-8') as _f:
                _raw = json.load(_f)
            if 'format' in _raw and str(_raw.get('format', '')).startswith('barcode-benchmark'):
                for _img in _raw.get('images', []):
                    _fname = _img.get('file', '')
                    annotation_full_data[_fname] = [
                        {'text': _bc.get('text', ''), 'points': _bc.get('points', [])}
                        for _bc in _img.get('barcodes', [])
                        if isinstance(_bc, dict)
                    ]

            self.finished.emit(annotation_data, annotation_full_data)
        except Exception as e:
            self.error.emit(str(e))


class BenchmarkWorker(QThread):
    """Worker thread for running benchmarks without blocking UI."""
    
    progress = Signal(int, int, str)  # current, total, message
    file_complete = Signal(str, str, dict)  # file_path, library_name, result
    finished = Signal(dict)  # final_results
    error = Signal(str)

    def __init__(self, tasks: List[BenchmarkTask], readers: Dict[str, Any],
                 template_path=None, template_name=None, parent=None):
        super().__init__(parent)
        self.tasks = tasks
        self.readers = readers
        self._template_path = template_path
        self._template_name = template_name
        self._running = True

    def run(self):
        """Run benchmark tests."""
        results = {}
        total_files = len(self.tasks)

        try:
            for file_idx, task in enumerate(self.tasks):
                if not self._running:
                    break

                file_path = task.file_path
                file_type = task.file_type

                self.progress.emit(file_idx, total_files, f"Processing: {Path(file_path).name}")

                # Handle video files
                frames_to_process = [file_path]
                temp_dir = None
                if file_type == 'video':
                    temp_dir = tempfile.mkdtemp()
                    frames = VideoFrameExtractor.extract_frames(file_path, temp_dir)
                    if frames:
                        frames_to_process = frames
                    else:
                        self.error.emit(f"Failed to extract frames from {file_path}")
                        continue

                # Process each frame/image with each reader
                for frame_path in frames_to_process:
                    for lib_name, reader in self.readers.items():
                        try:
                            # Initialize reader if needed
                            if not hasattr(reader, '_gui_initialized') or not reader._gui_initialized:
                                reader.initialize()
                                reader._gui_initialized = True
                                # Apply DBR template to Dynamsoft reader if provided
                                if self._template_path and hasattr(reader, 'cvr_instance') and reader.cvr_instance:
                                    reader.cvr_instance.init_settings_from_file(self._template_path)
                                    if self._template_name:
                                        reader._template_name = self._template_name

                            # Decode barcodes
                            start_time = time.perf_counter()
                            detected_barcodes, _ = reader.decode_barcodes(frame_path)
                            end_time = time.perf_counter()
                            detection_time_ms = (end_time - start_time) * 1000

                            # Extract barcode data with type info
                            detected_data = [
                                {'data': bc.get('data', ''), 'type': bc.get('type', '')}
                                for bc in detected_barcodes
                            ]
                            barcode_count = len(detected_barcodes)

                            # Validate against expected if available
                            validation = None
                            if task.expected_barcodes:
                                validation = AnnotationValidator.validate(
                                    detected_barcodes, task.expected_barcodes
                                )

                            # Store result
                            result = {
                                'file_path': frame_path,
                                'original_file': file_path,
                                'library_name': lib_name,
                                'success': True,
                                'barcodes_detected': barcode_count,
                                'barcodes_expected': len(task.expected_barcodes) if task.expected_barcodes else 0,
                                'expected_values': list(task.expected_barcodes) if task.expected_barcodes else [],
                                'detection_time_ms': detection_time_ms,
                                'detected_data': detected_data,
                                'validation': validation
                            }

                            key = f"{lib_name}_{file_path}"
                            if key not in results:
                                results[key] = []
                            results[key].append(result)

                            # Emit signal for UI update
                            self.file_complete.emit(file_path, lib_name, result)

                        except Exception as e:
                            self.error.emit(f"Error processing {file_path} with {lib_name}: {str(e)}")

                # Cleanup temp files for video
                if temp_dir:
                    import shutil
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    except:
                        pass

            self.finished.emit(results)

        except Exception as e:
            self.error.emit(f"Benchmark failed: {str(e)}")

    def stop(self):
        """Stop the worker."""
        self._running = False


class HTMLReportExporter:
    """Export benchmark results as an HTML report matching the web app layout."""

    _CSS = """
    *, *::before, *::after { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           background: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }
    .report-header { background: #fff; border-radius: 12px; padding: 24px 28px;
                     margin-bottom: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
    .report-header h1 { margin: 0 0 6px; font-size: 1.6rem; color: #0f172a; }
    .report-header p  { margin: 2px 0; font-size: 0.88rem; color: #64748b; }
    .benchmark-table-wrap { overflow-x: auto; margin-bottom: 16px; }
    .benchmark-table { width: 100%; border-collapse: collapse; background: #fff;
                       border-radius: 8px; overflow: hidden;
                       box-shadow: 0 1px 4px rgba(0,0,0,.07); font-size: 0.9rem; }
    .benchmark-table th { background: #f1f5f9; color: #475569; font-weight: 600;
                          text-align: left; padding: 10px 14px;
                          border-bottom: 1px solid #e2e8f0; }
    .benchmark-table td { padding: 9px 14px; border-bottom: 1px solid #f1f5f9;
                          vertical-align: top; }
    .benchmark-table tr:last-child td { border-bottom: none; }
    .benchmark-table tr:hover td { background: #f8fafc; }
    .sdk-col   { font-weight: 600; white-space: nowrap; }
    .count-col { text-align: center; font-weight: 700; font-size: 1.05em; }
    .best-count { color: #16a34a; }
    .time-col  { white-space: nowrap; color: #64748b; }
    .rate-col  { text-align: center; white-space: nowrap; font-weight: 600; }
    .gt-good { color: #16a34a; }
    .gt-ok   { color: #d97706; }
    .gt-poor { color: #dc2626; }
    .barcodes-list { margin: 0; padding-left: 16px; }
    .barcodes-list li { margin-bottom: 2px; font-size: 0.85em; font-family: monospace; }
    .benchmark-summary { background: #fff; border-radius: 8px; padding: 16px 20px;
                         box-shadow: 0 1px 4px rgba(0,0,0,.07); margin-bottom: 24px; }
    .benchmark-summary h4 { margin: 0 0 10px; font-size: 1rem; color: #334155; }
    .benchmark-summary ul { margin: 8px 0 0; padding-left: 20px;
                             font-size: 0.9rem; line-height: 1.8; }
    .benchmark-group { background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.07);
                       margin-bottom: 20px; overflow: hidden; }
    .benchmark-group summary { cursor: pointer; list-style: none; font-size: 1rem; font-weight: 700;
                               color: #334155; padding: 16px 20px; background: #f8fafc;
                               border-bottom: 1px solid #e2e8f0; }
    .benchmark-group summary::-webkit-details-marker { display: none; }
    .benchmark-group summary::before { content: '▸'; display: inline-block; margin-right: 8px;
                                       color: #64748b; transition: transform 0.15s ease; }
    .benchmark-group[open] summary::before { transform: rotate(90deg); }
    .benchmark-group-body { padding: 16px 20px 8px; }
    .benchmark-image-title { font-size: 0.95rem; font-weight: 600; color: #475569;
                              margin: 18px 0 6px; padding-bottom: 4px;
                              border-bottom: 1px solid #e2e8f0; }
    .expected-values { margin: 0 0 10px; padding: 8px 10px; border-radius: 8px;
                       background: #fff7ed; color: #9a3412; font-size: 0.86rem; }
    .expected-values strong { color: #7c2d12; }
    """

    @staticmethod
    def _esc(s: str) -> str:
        from html import escape
        return escape(str(s))

    @staticmethod
    def _display_text(s: str) -> str:
        """Convert control characters to visible markers and preserve line breaks in HTML."""
        from html import escape

        normalized = AnnotationValidator._normalize_text(str(s))
        visible = (
            normalized
            .replace('\x00', '<NUL>')
            .replace('\x04', '<EOT>')
            .replace('\x1d', '<GS>')
            .replace('\x1e', '<RS>')
        )
        return escape(visible).replace('\n', '<br>')

    @staticmethod
    def _gt_cls(rate_pct: float) -> str:
        return 'gt-good' if rate_pct >= 90 else ('gt-ok' if rate_pct >= 70 else 'gt-poor')

    @staticmethod
    def export(results: Dict[str, List[Dict]], output_path: str, has_annotation: bool = False):
        """Generate HTML report identical in layout to the web-app benchmark export."""
        esc = HTMLReportExporter._esc
        gt_cls = HTMLReportExporter._gt_cls
        display_text = HTMLReportExporter._display_text

        # ── Reorganise results: file_path → lib_name → result dict ─────────
        file_results: Dict[str, Dict[str, dict]] = {}
        all_libs: List[str] = []
        lib_seen: set = set()
        for result_list in results.values():
            for r in result_list:
                fp, lib = r['file_path'], r['library_name']
                file_results.setdefault(fp, {})[lib] = r
                if lib not in lib_seen:
                    lib_seen.add(lib)
                    all_libs.append(lib)
        file_paths = list(file_results.keys())
        img_count = len(file_paths)

        # ── Aggregate per library ────────────────────────────────────────────
        agg: Dict[str, dict] = {
            lib: {'files': 0, 'total_barcodes': 0, 'total_time': 0.0,
                  'all_texts': set(), 'tp': 0, 'fp': 0, 'expected': 0}
            for lib in all_libs
        }
        for fp, lib_map in file_results.items():
            for lib, r in lib_map.items():
                a = agg[lib]
                a['files'] += 1
                a['total_barcodes'] += r.get('barcodes_detected', 0)
                a['total_time'] += r.get('detection_time_ms', 0.0)
                for bc in r.get('detected_data', []):
                    a['all_texts'].add(bc.get('data', ''))
                v = r.get('validation')
                if v:
                    a['tp'] += v.get('tp', v.get('matched', 0))
                    a['fp'] += v.get('fp', 0)
                    a['expected'] += v.get('expected_count', 0)

        for a in agg.values():
            a['unique_barcodes'] = len(a['all_texts'])
            a['avg_time'] = a['total_time'] / max(a['files'], 1)
            if has_annotation and a['expected'] > 0:
                a['detection_rate'] = a['tp'] / a['expected'] * 100
                pd = a['tp'] + a['fp']
                a['precision'] = a['tp'] / pd * 100 if pd > 0 else 0.0
            else:
                a['detection_rate'] = None
                a['precision'] = None

        max_barcodes = max((a['total_barcodes'] for a in agg.values()), default=0)
        max_unique   = max((a['unique_barcodes'] for a in agg.values()), default=0)
        max_rate     = max((a['detection_rate']  for a in agg.values()
                            if a['detection_rate'] is not None), default=0)
        all_unique   = len(set(t for a in agg.values() for t in a['all_texts']))
        most_lib     = max(agg, key=lambda l: agg[l]['total_barcodes'], default='')
        fastest_lib  = min(agg, key=lambda l: agg[l]['total_time'],     default='')
        most_uniq_lib = max(agg, key=lambda l: agg[l]['unique_barcodes'], default='')
        best_rate_lib = (max((l for l in agg if agg[l]['detection_rate'] is not None),
                             key=lambda l: agg[l]['detection_rate'], default='')
                         if has_annotation else '')

        # ── Header ───────────────────────────────────────────────────────────
        sdk_list = ', '.join(all_libs)
        mode_str = 'With Ground Truth Validation' if has_annotation else 'Barcode Count Only'
        html = (
            f'<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            f'<meta charset="UTF-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'<title>Barcode Benchmark Report</title>\n'
            f'<style>{HTMLReportExporter._CSS}</style>\n</head>\n<body>\n'
            f'<div class="report-header">\n'
            f'  <h1>&#128202; Barcode Benchmark Report</h1>\n'
            f'  <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>\n'
            f'  <p><strong>Images tested:</strong> {img_count}</p>\n'
            f'  <p><strong>SDKs compared:</strong> {esc(sdk_list)}</p>\n'
            f'  <p><strong>Mode:</strong> {mode_str}</p>\n'
            f'</div>\n'
        )

        # ── Aggregate summary block ───────────────────────────────────────────
        html += f'<div class="benchmark-summary">\n'
        html += f'  <h4>Aggregate Summary ({img_count} image{"s" if img_count != 1 else ""})</h4>\n'
        html += '  <div class="benchmark-table-wrap"><table class="benchmark-table">\n    <thead><tr>'
        html += '<th>SDK</th><th>Total Found</th><th>Unique Barcodes</th>'
        if has_annotation:
            html += '<th>GT Expected</th><th>GT Detected</th><th>Detection Rate</th><th>Precision</th>'
        html += '<th>Total Time</th><th>Avg Time/Image</th></tr></thead>\n    <tbody>\n'

        for lib in all_libs:
            a = agg[lib]
            tc = 'count-col best-count' if (a['total_barcodes'] == max_barcodes and max_barcodes > 0) else 'count-col'
            uc = 'count-col best-count' if (a['unique_barcodes'] == max_unique  and max_unique  > 0) else 'count-col'
            html += f'    <tr><td class="sdk-col">{esc(lib)}</td>'
            html += f'<td class="{tc}">{a["total_barcodes"]}</td>'
            html += f'<td class="{uc}">{a["unique_barcodes"]}</td>'
            if has_annotation:
                dr, pr = a['detection_rate'], a['precision']
                rc = 'count-col best-count' if (dr is not None and dr == max_rate and max_rate > 0) else 'count-col'
                dr_h = f'<span class="{gt_cls(dr)}">{dr:.1f}%</span>' if dr is not None else '<em>N/A</em>'
                pr_h = f'<span class="{gt_cls(pr)}">{pr:.1f}%</span>' if pr is not None else '<em>N/A</em>'
                html += f'<td class="count-col">{a["expected"]}</td>'
                html += f'<td class="count-col">{a["tp"]}</td>'
                html += f'<td class="{rc} rate-col">{dr_h}</td>'
                html += f'<td class="rate-col">{pr_h}</td>'
            html += f'<td class="time-col">{a["total_time"]:.0f} ms</td>'
            html += f'<td class="time-col">{a["avg_time"]:.0f} ms</td></tr>\n'

        html += '    </tbody>\n  </table></div>\n  <ul>\n'
        html += f'    <li><strong>{all_unique}</strong> unique barcode(s) found across all SDKs and images</li>\n'
        if most_lib:
            html += f'    <li>Most barcodes: <strong>{esc(most_lib)}</strong> ({agg[most_lib]["total_barcodes"]})</li>\n'
        if img_count > 1 and most_uniq_lib:
            html += f'    <li>Most unique barcodes: <strong>{esc(most_uniq_lib)}</strong> ({agg[most_uniq_lib]["unique_barcodes"]})</li>\n'
        if has_annotation and best_rate_lib:
            dr = agg[best_rate_lib]['detection_rate']
            html += f'    <li>Best detection rate: <strong>{esc(best_rate_lib)}</strong> ({dr:.1f}%)</li>\n'
        if fastest_lib:
            html += f'    <li>Fastest: <strong>{esc(fastest_lib)}</strong> ({agg[fastest_lib]["total_time"]:.0f} ms total)</li>\n'
        html += '  </ul>\n</div>\n'

        def render_image_section(fp: str, show_expected_values: bool = False) -> str:
            lib_map = file_results[fp]
            fname = Path(fp).name
            has_gt = any(r.get('validation') for r in lib_map.values())
            expected_values = []
            for result in lib_map.values():
                expected_values = result.get('expected_values') or []
                if expected_values:
                    break
            gt_badge = (
                ' <span style="font-size:0.78rem;font-weight:500;color:#16a34a;'
                'background:#d1fae5;padding:1px 7px;border-radius:10px;margin-left:4px;">GT</span>'
                if has_gt else ''
            )
            section_html = f'<h4 class="benchmark-image-title">{esc(fname)}{gt_badge}</h4>\n'
            if show_expected_values and expected_values:
                expected_html = '<br>'.join(display_text(value) for value in expected_values)
                section_html += (
                    '<div class="expected-values">'
                    f'<strong>Expected:</strong> {expected_html}'
                    '</div>\n'
                )
            section_html += '<div class="benchmark-table-wrap"><table class="benchmark-table">\n  <thead><tr>'
            if has_gt:
                section_html += '<th>SDK</th><th>Found</th><th>Expected</th><th>Detected &#10003;</th><th>Rate</th><th>Precision</th><th>Time</th><th>Details</th>'
            else:
                section_html += '<th>SDK</th><th>Barcodes Found</th><th>Time</th><th>Details</th>'
            section_html += '</tr></thead>\n  <tbody>\n'

            counts = [lib_map[l].get('barcodes_detected', 0) for l in all_libs if l in lib_map]
            max_count = max(counts, default=0)

            for lib in all_libs:
                if lib not in lib_map:
                    continue
                r = lib_map[lib]
                count = r.get('barcodes_detected', 0)
                cnt_cls = 'count-col best-count' if (count == max_count and max_count > 0) else 'count-col'
                t_ms = r.get('detection_time_ms', 0.0)
                barcodes = r.get('detected_data', [])
                if barcodes:
                    detail = '<ul class="barcodes-list">' + ''.join(
                        f'<li>[{esc(b.get("type",""))}] {display_text(b.get("data",""))}</li>'
                        for b in barcodes
                    ) + '</ul>'
                else:
                    detail = '<em>Nothing found</em>'

                section_html += f'  <tr><td class="sdk-col">{esc(lib)}</td>'
                if has_gt:
                    v = r.get('validation') or {}
                    tp_v  = v.get('tp', v.get('matched', 0))
                    exp_v = v.get('expected_count', 0)
                    fp_v  = v.get('fp', 0)
                    dr_p  = (tp_v / exp_v * 100) if exp_v > 0 else None
                    pr_p  = (tp_v / (tp_v + fp_v) * 100) if (tp_v + fp_v) > 0 else None
                    dr_h  = f'<span class="{gt_cls(dr_p)}">{dr_p:.1f}%</span>' if dr_p is not None else '<em>N/A</em>'
                    pr_h  = f'<span class="{gt_cls(pr_p)}">{pr_p:.1f}%</span>' if pr_p is not None else '<em>N/A</em>'
                    section_html += (
                        f'<td class="{cnt_cls}">{count}</td>'
                        f'<td class="count-col">{exp_v}</td>'
                        f'<td class="count-col">{tp_v}</td>'
                        f'<td class="rate-col">{dr_h}</td>'
                        f'<td class="rate-col">{pr_h}</td>'
                        f'<td class="time-col">{t_ms:.0f} ms</td>'
                        f'<td>{detail}</td></tr>\n'
                    )
                else:
                    section_html += (
                        f'<td class="{cnt_cls}">{count}</td>'
                        f'<td class="time-col">{t_ms:.0f} ms</td>'
                        f'<td>{detail}</td></tr>\n'
                    )

            section_html += '  </tbody>\n</table></div>\n'
            return section_html

        # ── Grouped per-image sections ───────────────────────────────────────
        grouped_file_paths = {
            'Needs Review': [],
            'Exact Match': [],
            'No Annotation': [],
        }
        for fp in file_paths:
            lib_map = file_results[fp]
            statuses = [
                AnnotationValidator.classify_validation(r.get('validation'))['group']
                for r in lib_map.values()
            ]
            if 'Needs Review' in statuses:
                grouped_file_paths['Needs Review'].append(fp)
            elif 'Exact Match' in statuses:
                grouped_file_paths['Exact Match'].append(fp)
            else:
                grouped_file_paths['No Annotation'].append(fp)

        for group_name in ('Needs Review', 'Exact Match', 'No Annotation'):
            group_files = grouped_file_paths[group_name]
            if not group_files:
                continue

            html += f'<details class="benchmark-group">\n'
            html += f'  <summary>{esc(group_name)} ({len(group_files)})</summary>\n'
            html += '  <div class="benchmark-group-body">\n'
            for fp in group_files:
                html += render_image_section(fp, show_expected_values=(group_name == 'Needs Review'))
            html += '  </div>\n'
            html += '</details>\n'

        html += '</body>\n</html>\n'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


class SettingsDialog(QDialog):
    """Dialog for configuring SDK license keys."""

    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("SDK Settings")
        self.setMinimumWidth(600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Dynamsoft License
        dynamsoft_group = QGroupBox("Dynamsoft License")
        dynamsoft_layout = QFormLayout()
        self.dynamsoft_license = QLineEdit()
        self.dynamsoft_license.setText(
            self.config.get('libraries', {}).get('dynamsoft', {}).get('license', '')
        )
        self.dynamsoft_license.setPlaceholderText("Enter Dynamsoft license key...")
        dynamsoft_layout.addRow("License Key:", self.dynamsoft_license)
        dynamsoft_group.setLayout(dynamsoft_layout)
        layout.addWidget(dynamsoft_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> Dict[str, Any]:
        """Get updated configuration."""
        config = self.config.copy()
        if 'libraries' not in config:
            config['libraries'] = {}

        if 'dynamsoft' not in config['libraries']:
            config['libraries']['dynamsoft'] = {'enabled': True, 'options': {}}
        config['libraries']['dynamsoft']['license'] = self.dynamsoft_license.text()

        return config


class DropZoneWidget(QWidget):
    """Custom widget that accepts drag-and-drop files and folders."""

    files_dropped = Signal(list)  # List of file paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel("📁")
        self.icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Drag & Drop Images/Videos/Folders Here\nor Click to Browse")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("""
            color: #666;
            font-size: 16px;
            padding: 20px;
        """)
        layout.addWidget(self.text_label)

        self.setStyleSheet("""
            DropZoneWidget {
                background: #f8f9fa;
                border: 3px dashed #667eea;
                border-radius: 10px;
            }
            DropZoneWidget:hover {
                background: #e9ecef;
                border-color: #764ba2;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
            elif os.path.isdir(file_path):
                for root, dirs, filenames in os.walk(file_path):
                    for filename in filenames:
                        fp = os.path.join(root, filename)
                        ext = Path(fp).suffix.lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp',
                                  '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']:
                            files.append(fp)

        if files:
            self.files_dropped.emit(files)

    def mousePressEvent(self, event):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images/Videos",
            "",
            "Images/Videos (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp *.mp4 *.avi *.mov *.mkv *.wmv *.flv)"
        )
        if files:
            self.files_dropped.emit(files)


class _DropImageLabel(QLabel):
    """Large image-viewer label that also acts as a drag-and-drop target."""

    files_dropped = Signal(list)

    _STYLE_IDLE = (
        "background: #0d1117; border: 2px dashed #30363d; border-radius: 8px;"
        " color: #8b949e; font-size: 15px;"
    )
    _STYLE_HOVER = (
        "background: #161b22; border: 2px dashed #388bfd; border-radius: 8px;"
        " color: #388bfd; font-size: 15px;"
    )
    _PROMPT = "📁   Drag & drop images / folders here\nor use  Browse Files  above"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(480, 360)
        self.setText(self._PROMPT)
        self.setStyleSheet(self._STYLE_IDLE)
        self.setWordWrap(True)

    def clear_to_prompt(self):
        self.setPixmap(QPixmap())
        self.setText(self._PROMPT)
        self.setStyleSheet(self._STYLE_IDLE)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setStyleSheet(self._STYLE_HOVER)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._STYLE_IDLE)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.setStyleSheet(self._STYLE_IDLE)
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
            elif os.path.isdir(file_path):
                for root, _dirs, filenames in os.walk(file_path):
                    for filename in filenames:
                        fp = os.path.join(root, filename)
                        if Path(fp).suffix.lower() in {
                            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',
                            '.webp', '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'
                        }:
                            files.append(fp)
        if files:
            self.files_dropped.emit(files)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Barcode Benchmark Tool")
        self.setMinimumSize(1200, 800)

        # State
        self.config = self._load_config()
        self.selected_files = []
        self.annotation_data = None       # Dict: filename -> List[str] (text values)
        self.annotation_full_data: Dict[str, List[dict]] = {}  # filename -> [{text, points}]
        self.annotation_file = None
        self._template_path = None   # DBR template file path
        self._template_name = None   # DBR template name extracted from file
        self.results = {}
        self.readers = {}
        self._image_list: List[str] = []
        self._current_image_idx: int = 0

        self.init_ui()

    def _load_config(self) -> Dict[str, Any]:
        """Load benchmark configuration."""
        config_path = Path(__file__).parent / "config" / "benchmark_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {'libraries': {}}

    def _save_config(self):
        """Save configuration."""
        config_path = Path(__file__).parent / "config" / "benchmark_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    @staticmethod
    def _normalize_annotation_key(path_value: str) -> str:
        """Normalize file paths so absolute paths can match relative annotation keys."""
        return str(path_value).replace('\\', '/').strip().lower().lstrip('./')

    def _lookup_annotation_mapping(self, mapping: Optional[Dict[str, Any]], file_path: str):
        """Find annotation data using exact, basename, stem, or relative-suffix matching."""
        if not mapping:
            return None

        normalized_path = self._normalize_annotation_key(file_path)
        filename = Path(normalized_path).name
        filename_no_ext = Path(normalized_path).stem

        for candidate in (normalized_path, filename, filename_no_ext):
            if candidate in mapping:
                return mapping[candidate]

        suffix_matches = []
        for key, value in mapping.items():
            normalized_key = self._normalize_annotation_key(key)
            if normalized_path == normalized_key or normalized_path.endswith('/' + normalized_key):
                suffix_matches.append(value)

        if len(suffix_matches) == 1:
            return suffix_matches[0]
        if suffix_matches:
            return suffix_matches[0]

        return None

    def _match_annotation(self, file_path: str) -> Optional[List[str]]:
        """Find expected barcodes for a file based on annotation.
        """
        return self._lookup_annotation_mapping(self.annotation_data, file_path)

    def init_ui(self):
        """Initialize user interface."""
        # ── Global stylesheet ──────────────────────────────────────────────
        self.setStyleSheet("""
            QMainWindow { background: #0d1117; }
            QWidget      { font-family: 'Segoe UI', Arial, sans-serif; background: transparent; }
            QGroupBox {
                font-weight: 700;
                font-size: 11px;
                letter-spacing: 0.5px;
                border: 1px solid #30363d;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 6px;
                background: #161b22;
                color: #e6edf3;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                background: #161b22;
                color: #8b949e;
                text-transform: uppercase;
            }
            QPushButton {
                padding: 5px 13px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                border: 1px solid #30363d;
                background: #21262d;
                color: #c9d1d9;
            }
            QPushButton:hover   { background: #30363d; border-color: #8b949e; }
            QPushButton:pressed { background: #161b22; }
            QPushButton:disabled { color: #484f58; background: #161b22; border-color: #21262d; }
            QTableWidget {
                border: none;
                font-size: 12px;
                gridline-color: #21262d;
                background: #0d1117;
                color: #c9d1d9;
                alternate-background-color: #161b22;
            }
            QTableWidget::item { padding: 3px 6px; }
            QTableWidget::item:selected { background: #1f6feb; color: #ffffff; }
            QHeaderView::section {
                background: #161b22;
                border: none;
                border-bottom: 2px solid #30363d;
                border-right: 1px solid #21262d;
                padding: 6px 8px;
                font-weight: 700;
                font-size: 11px;
                color: #8b949e;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 4px;
                text-align: center;
                height: 16px;
                font-size: 11px;
                background: #161b22;
                color: #c9d1d9;
            }
            QProgressBar::chunk { background: #1f6feb; border-radius: 3px; }
            QCheckBox { font-size: 12px; spacing: 6px; color: #c9d1d9; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border-radius: 4px;
                border: 1px solid #30363d;
                background: #161b22;
            }
            QCheckBox::indicator:checked { background: #1f6feb; border-color: #1f6feb; }
            QTextEdit {
                font-size: 11px;
                border: 1px solid #30363d;
                border-radius: 4px;
                background: #0d1117;
                color: #c9d1d9;
            }
            QLabel { color: #c9d1d9; }
            QSplitter::handle { background: #30363d; width: 4px; height: 4px; }
            QScrollBar:vertical { background: #0d1117; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #30363d; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        central_widget = QWidget()
        central_widget.setStyleSheet("background: #0d1117;")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ── Top row: Image viewer (left)  +  Controls (right) ─────────────
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        # ── LEFT: Image Viewer (doubles as drop zone) ──────────────────────
        viewer_group = QGroupBox("📷  Image Viewer")
        viewer_layout = QVBoxLayout(viewer_group)
        viewer_layout.setSpacing(6)

        # Action bar
        action_row = QHBoxLayout()
        btn_browse = QPushButton("📁  Browse Files")
        btn_browse.setStyleSheet(
            "QPushButton { background: #1f6feb; color: #ffffff; border: none; font-weight: 600; }"
            "QPushButton:hover { background: #388bfd; border: none; }"
        )
        btn_browse.clicked.connect(self._browse_files)
        action_row.addWidget(btn_browse)

        btn_clear_files = QPushButton("🗑  Clear")
        btn_clear_files.clicked.connect(self.clear_files)
        action_row.addWidget(btn_clear_files)

        btn_load_annotation = QPushButton("📋  Load Annotations")
        btn_load_annotation.clicked.connect(self.load_annotation)
        action_row.addWidget(btn_load_annotation)

        action_row.addStretch()

        self._annotation_status_label = QLabel("")
        self._annotation_status_label.setStyleSheet("color: #3fb950; font-size: 11px;")
        action_row.addWidget(self._annotation_status_label)

        viewer_layout.addLayout(action_row)

        # Navigation bar
        nav_row = QHBoxLayout()
        self._btn_prev = QPushButton("◀  Prev")
        self._btn_prev.clicked.connect(self._on_prev_image)
        self._btn_prev.setEnabled(False)
        self._btn_prev.setFixedWidth(90)
        nav_row.addWidget(self._btn_prev)

        self._nav_label = QLabel("No image loaded")
        self._nav_label.setAlignment(Qt.AlignCenter)
        self._nav_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 500;")
        nav_row.addWidget(self._nav_label, 1)

        self._btn_next = QPushButton("Next  ▶")
        self._btn_next.clicked.connect(self._on_next_image)
        self._btn_next.setEnabled(False)
        self._btn_next.setFixedWidth(90)
        nav_row.addWidget(self._btn_next)
        viewer_layout.addLayout(nav_row)

        # Main canvas — accepts drag & drop and shows images
        self._viewer_canvas = _DropImageLabel()
        self._viewer_canvas.files_dropped.connect(self.on_files_dropped)
        self._image_label = self._viewer_canvas   # alias used by _show_image_at
        viewer_layout.addWidget(self._viewer_canvas, 1)

        # Per-image result info
        self._image_info = QTextEdit()
        self._image_info.setReadOnly(True)
        self._image_info.setFixedHeight(75)
        viewer_layout.addWidget(self._image_info)

        top_layout.addWidget(viewer_group, 2)

        # ── RIGHT: Controls panel ──────────────────────────────────────────
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        # SDK selection
        sdk_group = QGroupBox("🔬  Select SDKs")
        sdk_layout = QVBoxLayout(sdk_group)
        self.sdk_checkboxes = {}
        libraries = self.config.get('libraries', {})
        for lib_name in ['zxing_cpp', 'dynamsoft']:
            if lib_name in libraries:
                cb = QCheckBox(lib_name.replace('_', ' ').title())
                cb.setChecked(libraries[lib_name].get('enabled', False))
                cb.stateChanged.connect(self.on_sdk_changed)
                self.sdk_checkboxes[lib_name] = cb
                sdk_layout.addWidget(cb)
        btn_settings = QPushButton("⚙  SDK Settings")
        btn_settings.clicked.connect(self.open_settings)
        sdk_layout.addWidget(btn_settings)
        right_panel.addWidget(sdk_group)

        # DBR template
        template_group = QGroupBox("📄  Dynamsoft Template")
        template_layout = QVBoxLayout(template_group)
        tmpl_btn_row = QHBoxLayout()
        self._btn_load_template = QPushButton("Load JSON")
        self._btn_load_template.clicked.connect(self.load_template)
        tmpl_btn_row.addWidget(self._btn_load_template)
        self._btn_clear_template = QPushButton("Reset")
        self._btn_clear_template.clicked.connect(self.clear_template)
        self._btn_clear_template.setEnabled(False)
        tmpl_btn_row.addWidget(self._btn_clear_template)
        template_layout.addLayout(tmpl_btn_row)
        self._template_label = QLabel("No template loaded (using default)")
        self._template_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        self._template_label.setWordWrap(True)
        template_layout.addWidget(self._template_label)
        right_panel.addWidget(template_group)

        # Benchmark controls
        control_group = QGroupBox("🚀  Benchmark")
        control_layout = QVBoxLayout(control_group)
        self.btn_run = QPushButton("▶   Run Benchmark")
        self.btn_run.setEnabled(False)
        self.btn_run.setMinimumHeight(38)
        self.btn_run.clicked.connect(self.run_benchmark)
        self.btn_run.setStyleSheet("""
            QPushButton          { background: #238636; color: #ffffff; border: none;
                                   font-size: 13px; font-weight: 700; }
            QPushButton:hover    { background: #2ea043; border: none; }
            QPushButton:disabled { background: #21262d; color: #484f58; border: none; }
        """)
        control_layout.addWidget(self.btn_run)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        control_layout.addWidget(self.status_label)
        right_panel.addWidget(control_group)

        # Results summary
        results_group = QGroupBox("📊  Results Summary")
        results_layout = QVBoxLayout(results_group)
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            'Library', 'Files', 'Found', 'GT Expected', 'GT Detected', 'Detection Rate', 'Avg ms'
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        results_layout.addWidget(self.results_table)
        self.btn_export = QPushButton("📄  Export HTML Report")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)
        results_layout.addWidget(self.btn_export)
        right_panel.addWidget(results_group, 1)

        top_layout.addLayout(right_panel, 1)
        main_layout.addLayout(top_layout, 2)

        # ── Bottom splitter: detail table  |  file list ───────────────────
        bottom_splitter = QSplitter(Qt.Horizontal)

        # Detailed results table
        detail_group = QGroupBox("📋  Detailed Results")
        detail_layout = QVBoxLayout(detail_group)
        self.detail_table = QTableWidget()
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setColumnCount(7)
        self.detail_table.setHorizontalHeaderLabels([
            'File', 'Library', 'Found', 'Expected', 'Matched', 'Time (ms)', 'Status'
        ])
        self.detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.detail_table.itemClicked.connect(self._on_detail_row_clicked)
        detail_layout.addWidget(self.detail_table)
        bottom_splitter.addWidget(detail_group)

        # Selected files list (moved from top-left)
        file_list_group = QGroupBox("📁  Selected Files")
        file_list_layout = QVBoxLayout(file_list_group)
        self.file_list_table = QTableWidget()
        self.file_list_table.setAlternatingRowColors(True)
        self.file_list_table.setColumnCount(4)
        self.file_list_table.setHorizontalHeaderLabels(['File', 'Type', 'Expected', 'Annotation'])
        self.file_list_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        file_list_layout.addWidget(self.file_list_table)
        bottom_splitter.addWidget(file_list_group)

        bottom_splitter.setSizes([680, 320])
        main_layout.addWidget(bottom_splitter, 1)

    def on_files_dropped(self, files: List[str]):
        """Handle files being dropped or selected."""
        self.selected_files.extend(files)
        self.update_file_list()
        self.update_run_button()

    def _browse_files(self):
        """Open file dialog for manual file selection."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images / Videos",
            "",
            "Images / Videos (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"
            " *.mp4 *.avi *.mov *.mkv *.wmv *.flv)"
        )
        if files:
            self.on_files_dropped(files)

    def update_file_list(self):
        """Update the file list table."""
        self.file_list_table.setUpdatesEnabled(False)
        self.file_list_table.setSortingEnabled(False)
        self.file_list_table.setRowCount(len(self.selected_files))

        for idx, file_path in enumerate(self.selected_files):
            # File name
            name_item = QTableWidgetItem(Path(file_path).name)
            name_item.setToolTip(file_path)
            self.file_list_table.setItem(idx, 0, name_item)

            # File type
            ext = Path(file_path).suffix.lower()
            file_type = "Video" if ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'] else "Image"
            type_item = QTableWidgetItem(file_type)
            self.file_list_table.setItem(idx, 1, type_item)

            # Expected barcodes from annotation
            expected = self._match_annotation(file_path)
            expected_text = str(len(expected)) if expected else "-"
            expected_item = QTableWidgetItem(expected_text)
            if expected:
                expected_item.setToolTip("\n".join(expected))
            self.file_list_table.setItem(idx, 2, expected_item)

            # Annotation status
            annotation_status = "✓" if expected else "-"
            annotation_item = QTableWidgetItem(annotation_status)
            self.file_list_table.setItem(idx, 3, annotation_item)

        self.file_list_table.setUpdatesEnabled(True)

    def clear_files(self):
        """Clear all selected files, results and reset the viewer."""
        self.selected_files = []
        self.results = {}
        self.file_list_table.setRowCount(0)
        self.detail_table.setRowCount(0)
        self.results_table.setRowCount(0)
        self._image_list = []
        self._current_image_idx = 0
        self._viewer_canvas.clear_to_prompt()
        self._nav_label.setText("No image loaded")
        self._btn_prev.setEnabled(False)
        self._btn_next.setEnabled(False)
        self._image_info.clear()
        self.btn_export.setEnabled(False)
        self.status_label.setText("Ready")
        self.update_run_button()

    def load_annotation(self):
        """Load annotation JSON file in a background thread with a progress dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Annotation File",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        # Show indeterminate progress dialog while loading
        self._annot_progress = QProgressDialog(
            "Loading annotation file…", None, 0, 0, self
        )
        self._annot_progress.setWindowTitle("Loading")
        self._annot_progress.setWindowModality(Qt.WindowModal)
        self._annot_progress.setMinimumDuration(0)
        self._annot_progress.setValue(0)
        self._annot_progress.show()

        self._annot_loader_path = file_path
        self._annot_worker = AnnotationLoaderWorker(file_path, self)
        self._annot_worker.finished.connect(self._on_annotation_loaded)
        self._annot_worker.error.connect(self._on_annotation_error)
        self._annot_worker.start()

    def _on_annotation_loaded(self, annotation_data: dict, annotation_full_data: dict):
        """Called on the main thread when annotation loading finishes."""
        self._annot_progress.close()

        self.annotation_data = annotation_data
        self.annotation_full_data = annotation_full_data
        self.annotation_file = self._annot_loader_path

        self.update_file_list()
        self.update_run_button()

        file_count = len(self.annotation_data)
        barcode_count = sum(len(v) for v in self.annotation_data.values())
        self._annotation_status_label.setText(
            f"✓ {file_count} images, {barcode_count} barcodes"
        )
        QMessageBox.information(
            self,
            "Annotation Loaded",
            f"{file_count} images, {barcode_count} barcodes loaded."
        )

    def _on_annotation_error(self, error_message: str):
        """Called on the main thread when annotation loading fails."""
        self._annot_progress.close()
        QMessageBox.critical(self, "Error", f"Failed to load annotation:\n{error_message}")

    def on_sdk_changed(self):
        """Update config when SDK checkbox state changes."""
        for lib_name, cb in self.sdk_checkboxes.items():
            if lib_name in self.config.get('libraries', {}):
                self.config['libraries'][lib_name]['enabled'] = cb.isChecked()

    def open_settings(self):
        """Open SDK settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.get_config()
            self._save_config()
            QMessageBox.information(self, "Settings Saved", "SDK settings have been saved.")

    def load_template(self):
        """Load a Dynamsoft Barcode Reader template JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load DBR Template", self._template_path or "", "JSON Files (*.json)"
        )
        if not file_path:
            return
        try:
            # Validate and extract template name from the JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            templates = data.get("CaptureVisionTemplates", [])
            template_name = templates[0]["Name"] if templates else None

            self._template_path = file_path
            self._template_name = template_name
            fname = Path(file_path).name
            name_hint = f" (template: '{template_name}')" if template_name else ""
            self._template_label.setText(f"{fname}{name_hint}")
            self._template_label.setStyleSheet("color: #155724; font-size: 11px;")
            self._btn_clear_template.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Template Error", f"Failed to load template:\n{str(e)}")

    def clear_template(self):
        """Clear the loaded DBR template and revert to default."""
        self._template_path = None
        self._template_name = None
        self._template_label.setText("No template loaded (using default)")
        self._template_label.setStyleSheet("color: #666; font-size: 11px;")
        self._btn_clear_template.setEnabled(False)

    def update_run_button(self):
        """Enable/disable run button based on valid selection."""
        has_files = len(self.selected_files) > 0
        has_sdk = any(cb.isChecked() for cb in self.sdk_checkboxes.values())
        self.btn_run.setEnabled(has_files and has_sdk)

    def run_benchmark(self):
        """Run benchmark tests."""
        enabled_sdks = [lib for lib, cb in self.sdk_checkboxes.items() if cb.isChecked()]
        if not enabled_sdks:
            QMessageBox.warning(self, "No SDK Selected", "Please select at least one SDK to benchmark.")
            return

        # Create readers
        self.readers = {}
        for lib_name in enabled_sdks:
            try:
                lib_config = self.config['libraries'][lib_name]
                reader = create_reader(lib_name, lib_config)
                reader._gui_initialized = False  # Reset initialization state
                self.readers[lib_name] = reader
            except Exception as e:
                QMessageBox.warning(self, "SDK Error", f"Failed to initialize {lib_name}:\n{str(e)}")

        if not self.readers:
            return

        # Create benchmark tasks
        tasks = []
        for file_path in self.selected_files:
            ext = Path(file_path).suffix.lower()
            file_type = "video" if ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'] else "image"

            # Get expected barcodes from annotation
            expected = self._match_annotation(file_path)

            tasks.append(BenchmarkTask(
                file_path=file_path,
                file_type=file_type,
                expected_barcodes=expected
            ))

        # Setup UI for running
        self.btn_run.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)
        self.status_label.setText("Running benchmark...")

        # Clear previous results
        self.results = {}
        self.detail_table.setRowCount(0)

        # Create and start worker
        self.worker = BenchmarkWorker(tasks, self.readers,
                                      template_path=self._template_path,
                                      template_name=self._template_name)
        self.worker.progress.connect(self.on_progress)
        self.worker.file_complete.connect(self.on_file_complete)
        self.worker.finished.connect(self.on_benchmark_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_progress(self, current: int, total: int, message: str):
        """Update progress."""
        self.status_label.setText(message)
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)

    def on_file_complete(self, file_path: str, library_name: str, result: dict):
        """Update UI when a file is processed."""
        row = self.detail_table.rowCount()
        self.detail_table.insertRow(row)

        self._populate_detail_row(row, result)

    def _populate_detail_row(self, row: int, result: dict):
        """Fill one row in the detail table from a benchmark result."""
        validation = result.get('validation')
        status_info = AnnotationValidator.classify_validation(validation)

        self.detail_table.setItem(row, 0, QTableWidgetItem(Path(result['file_path']).name))
        self.detail_table.setItem(row, 1, QTableWidgetItem(result['library_name']))
        self.detail_table.setItem(row, 2, QTableWidgetItem(str(result['barcodes_detected'])))
        self.detail_table.setItem(row, 3, QTableWidgetItem(str(result['barcodes_expected'])))

        matched = validation.get('matched', 0) if validation else '-'
        self.detail_table.setItem(row, 4, QTableWidgetItem(str(matched)))
        self.detail_table.setItem(row, 5, QTableWidgetItem(f"{result['detection_time_ms']:.2f}"))

        status_item = QTableWidgetItem(status_info['status'])
        status_item.setData(Qt.UserRole, status_info['order'])
        status_item.setToolTip(status_info['group'])
        if status_info['group'] == 'Needs Review':
            status_item.setForeground(Qt.red)
        elif status_info['group'] == 'Exact Match':
            status_item.setForeground(Qt.darkGreen)
        self.detail_table.setItem(row, 6, status_item)

    def _rebuild_detail_table_grouped(self):
        """Rebuild the detail table grouped by review status for easier inspection."""
        ordered_results = []
        for result_list in self.results.values():
            ordered_results.extend(result_list)

        ordered_results.sort(
            key=lambda result: (
                AnnotationValidator.classify_validation(result.get('validation'))['order'],
                Path(result['file_path']).name.lower(),
                result['library_name'].lower(),
            )
        )

        self.detail_table.setUpdatesEnabled(False)
        self.detail_table.setRowCount(0)
        for result in ordered_results:
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)
            self._populate_detail_row(row, result)
        self.detail_table.setUpdatesEnabled(True)

    def on_benchmark_finished(self, results: dict):
        """Handle benchmark completion."""
        self.results = results
        self._rebuild_detail_table_grouped()
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Benchmark completed! Processed {len(self.selected_files)} files.")
        self.btn_export.setEnabled(True)

        # Build ordered image list for viewer
        seen: set = set()
        self._image_list = []
        for fp in self.selected_files:
            if fp not in seen:
                seen.add(fp)
                self._image_list.append(fp)
        if self._image_list:
            self._show_image_at(0)

        # Update summary table
        self.update_results_summary()

    def on_error(self, error_message: str):
        """Handle errors."""
        QMessageBox.critical(self, "Error", error_message)
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Benchmark failed.")

    def update_results_summary(self):
        """Update the results summary table."""
        self.results_table.setRowCount(0)

        # Aggregate by library — track barcode-level TP/FP/FN
        library_stats = {}
        for key, result_list in self.results.items():
            for result in result_list:
                lib_name = result['library_name']
                if lib_name not in library_stats:
                    library_stats[lib_name] = {
                        'files': 0,
                        'barcodes': 0,
                        'times': [],
                        'tp': 0,
                        'fp': 0,
                        'total_expected': 0,
                    }
                library_stats[lib_name]['files'] += 1
                library_stats[lib_name]['barcodes'] += result['barcodes_detected']
                library_stats[lib_name]['times'].append(result['detection_time_ms'])

                validation = result.get('validation')
                if validation:
                    library_stats[lib_name]['tp'] += validation.get('tp', validation.get('matched', 0))
                    library_stats[lib_name]['fp'] += validation.get('fp', 0)
                    library_stats[lib_name]['total_expected'] += validation.get('expected_count', 0)

        has_annotation = self.annotation_data is not None

        # Populate table
        for lib_name, stats in library_stats.items():
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            avg_time = sum(stats['times']) / len(stats['times']) if stats['times'] else 0
            tp = stats['tp']
            total_exp = stats['total_expected']
            detection_rate = f"{tp / total_exp * 100:.1f}%" if (has_annotation and total_exp > 0) else "N/A"
            gt_expected = str(total_exp) if has_annotation else "N/A"
            gt_detected = str(tp) if has_annotation else "N/A"

            self.results_table.setItem(row, 0, QTableWidgetItem(lib_name))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(stats['files'])))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(stats['barcodes'])))
            self.results_table.setItem(row, 3, QTableWidgetItem(gt_expected))
            self.results_table.setItem(row, 4, QTableWidgetItem(gt_detected))
            self.results_table.setItem(row, 5, QTableWidgetItem(detection_rate))
            self.results_table.setItem(row, 6, QTableWidgetItem(f"{avg_time:.2f}"))

    def _on_detail_row_clicked(self, item):
        """Navigate viewer to the image of the clicked detail table row."""
        row = item.row()
        name_item = self.detail_table.item(row, 0)
        if name_item:
            file_name = name_item.text()
            for idx, path in enumerate(self._image_list):
                if Path(path).name == file_name:
                    self._show_image_at(idx)
                    break

    def _on_prev_image(self):
        """Navigate to previous image."""
        if self._current_image_idx > 0:
            self._show_image_at(self._current_image_idx - 1)

    def _on_next_image(self):
        """Navigate to next image."""
        if self._current_image_idx < len(self._image_list) - 1:
            self._show_image_at(self._current_image_idx + 1)

    def _show_image_at(self, idx: int):
        """Display the image at the given index with per-library benchmark results."""
        if not self._image_list or idx < 0 or idx >= len(self._image_list):
            return
        self._current_image_idx = idx
        file_path = self._image_list[idx]

        self._nav_label.setText(f"{idx + 1} / {len(self._image_list)}  —  {Path(file_path).name}")
        self._btn_prev.setEnabled(idx > 0)
        self._btn_next.setEnabled(idx < len(self._image_list) - 1)

        # ── Load and display image with overlays ──────────────────────────
        img = cv2.imread(file_path)
        if img is not None:
            lw = max(self._image_label.width(), 480)
            lh = max(self._image_label.height(), 360)
            h, w = img.shape[:2]
            scale = min(lw / w, lh / h) * 0.95
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            display = cv2.resize(img, (nw, nh)).copy()

            # Colour palette per library (BGR)
            _LIB_COLORS = [(0, 120, 255), (255, 100, 0), (220, 0, 220), (0, 200, 200)]
            _lib_color_map: Dict[str, tuple] = {}
            _color_idx = 0

            # Draw detected barcodes first (so GT overlays on top)
            for _key, _result_list in self.results.items():
                for _r in _result_list:
                    if _r.get('file_path') != file_path:
                        continue
                    _lib = _r['library_name']
                    if _lib not in _lib_color_map:
                        _lib_color_map[_lib] = _LIB_COLORS[_color_idx % len(_LIB_COLORS)]
                        _color_idx += 1
                    _color = _lib_color_map[_lib]
                    for _bc in _r.get('detected_data', []):
                        _pos = _bc.get('position', {})
                        _x = int(_pos.get('x', 0) * scale)
                        _y = int(_pos.get('y', 0) * scale)
                        _bw = int(_pos.get('width', 0) * scale)
                        _bh = int(_pos.get('height', 0) * scale)
                        if _bw > 0 and _bh > 0:
                            cv2.rectangle(display, (_x, _y), (_x + _bw, _y + _bh), _color, 2)
                            _label = f"[{_lib}] {_bc.get('data','')[:24]}"
                            cv2.putText(display, _label, (_x, max(_y - 4, 10)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, _color, 1, cv2.LINE_AA)

            # Draw GT annotation polygons (green) on top
            _gt_entries = self._lookup_annotation_mapping(self.annotation_full_data, file_path) or []
            for _bc in _gt_entries:
                _pts = _bc.get('points', [])
                if len(_pts) >= 2:
                    _scaled_pts = np.array(
                        [[int(_p[0] * scale), int(_p[1] * scale)] for _p in _pts],
                        dtype=np.int32
                    )
                    cv2.polylines(display, [_scaled_pts], True, (0, 220, 0), 2)
                    _ox, _oy = _scaled_pts[0][0], _scaled_pts[0][1]
                    _text = _bc.get('text', '')[:24]
                    cv2.putText(display, _text, (_ox, max(_oy - 4, 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 0), 1, cv2.LINE_AA)

            img_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            qimg = QImage(img_rgb.data, nw, nh, nw * 3, QImage.Format_RGB888)
            self._image_label.setPixmap(QPixmap.fromImage(qimg.copy()))
        else:
            self._image_label.setText(f"Cannot load:\n{Path(file_path).name}")

        # ── Detail info text area below image ─────────────────────────────
        expected = self._match_annotation(file_path)
        lines = [f'<b>{Path(file_path).name}</b>']
        if expected:
            lines.append(
                f"<span style='color:#155724'><b>GT ({len(expected)}):</b> "
                f"{', '.join(expected)}</span>"
            )
        for _key, _result_list in self.results.items():
            for _r in _result_list:
                if _r.get('file_path') == file_path:
                    _lib = _r['library_name']
                    _detected = [bc['data'] for bc in _r.get('detected_data', [])]
                    _validation = _r.get('validation')
                    if _validation:
                        _ok = _validation.get('is_correct')
                        _mark = (
                            "<span style='color:green'>&#10003;</span>"
                            if _ok else
                            "<span style='color:red'>&#10007;</span>"
                        )
                    else:
                        _mark = ''
                    _dtext = ', '.join(_detected) if _detected else '<i>none</i>'
                    lines.append(f'<b>{_lib}:</b> {_mark} {_dtext}')
        self._image_info.setHtml('<br>'.join(lines))

    def export_report(self):
        """Export benchmark results as HTML report."""
        if not self.results:
            QMessageBox.warning(self, "No Results", "No results to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export HTML Report",
            "benchmark_report.html",
            "HTML Files (*.html)"
        )

        if file_path:
            try:
                HTMLReportExporter.export(
                    self.results,
                    file_path,
                    has_annotation=self.annotation_data is not None
                )
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Report saved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export report:\n{str(e)}")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
