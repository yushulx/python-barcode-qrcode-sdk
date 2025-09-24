#!/usr/bin/env python3
"""
Dynamsoft Barcode Reader Parameter Adjustment Tool
A GUI tool for adjusting barcode detection parameters with real-time testing.
"""

import sys
import os
import json
import cv2
import numpy as np
import copy
import threading
import time
from functools import partial
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QScrollArea, QFrame, QSplitter, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QLineEdit, QFileDialog, QMessageBox,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QTabWidget, QSlider,
    QButtonGroup, QRadioButton, QFormLayout, QDoubleSpinBox, QTreeWidget,
    QTreeWidgetItem, QHeaderView
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QSize, QRect, QPoint, QMimeData, QUrl
)
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QPen, QBrush, QColor, QFont, QAction,
    QDragEnterEvent, QDropEvent, QPalette, QIcon
)

from dynamsoft_barcode_reader_bundle import (
    LicenseManager, CaptureVisionRouter, EnumErrorCode, BarcodeResultItem, EnumPresetTemplate
)

class BarcodeDetectionWorker(QThread):
    """Worker thread for barcode detection to avoid UI freezing"""
    result_ready = Signal(list, str)  # results, error_message
    progress_update = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.settings_json = None
        self.running = False
        
    def set_parameters(self, image_path: str, settings_json: str):
        self.image_path = image_path
        self.settings_json = settings_json
        
    def run(self):
        if not self.image_path or not self.settings_json:
            self.result_ready.emit([], "No image or settings provided")
            return
            
        try:
            self.progress_update.emit("Initializing barcode reader...")
            
            # Initialize CaptureVisionRouter
            cvr_instance = CaptureVisionRouter()
            
            # Apply settings - use correct method signature
            self.progress_update.emit("Applying settings...")
            error_code, error_str = cvr_instance.init_settings(self.settings_json)
            # print("License initialization result:", error_code, error_str)
            if error_code != EnumErrorCode.EC_OK:
                self.result_ready.emit([], f"Failed to initialize settings: {error_str}")
                return
            
            # Capture from image - use current template from settings
            self.progress_update.emit("Detecting barcodes...")
            # Extract template name from settings if available
            template_name = "ReadBarcodes_Default"  # Default template
            try:
                import json
                settings_dict = json.loads(self.settings_json)
                if 'CaptureVisionTemplates' in settings_dict and settings_dict['CaptureVisionTemplates']:
                    # Use the first template name found
                    template_name = settings_dict['CaptureVisionTemplates'][0].get('Name', 'ReadBarcodes_Default')
            except:
                pass  # Use default if parsing fails
                
            result = cvr_instance.capture(self.image_path, template_name)
            
            barcode_results = []
            if result.get_error_code() == EnumErrorCode.EC_OK:
                barcode_result_items = result.get_items()
                if barcode_result_items:
                    for item in barcode_result_items:
                        location = item.get_location()
                        x1 = location.points[0].x
                        y1 = location.points[0].y
                        x2 = location.points[1].x
                        y2 = location.points[1].y
                        x3 = location.points[2].x
                        y3 = location.points[2].y
                        x4 = location.points[3].x
                        y4 = location.points[3].y
                        barcode_results.append({
                            'text': item.get_text(),
                            'format': item.get_format_string(),
                            'confidence': item.get_confidence(),
                            'location': [
                                (x1, y1),
                                (x2, y2),
                                (x3, y3),
                                (x4, y4)
                            ]
                        })
                        
            self.result_ready.emit(barcode_results, "")
            
        except Exception as e:
            self.result_ready.emit([], str(e))

class ImagePanel(QLabel):
    """Image display panel with drag-drop support and overlay drawing"""
    
    image_loaded = Signal(str)  # Signal emitted when image is loaded
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("border: 2px dashed #aaa;")
        self.setText("Drag and drop an image here\nor use File menu to load")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        
        self.original_image = None
        self.barcode_results = []
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if self.is_image_file(file_path):
                    event.accept()
                    return
        event.ignore()
        
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            if self.is_image_file(file_path):
                self.load_image(file_path)
                
    def is_image_file(self, file_path: str) -> bool:
        """Check if file is a supported image format"""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif']
        return Path(file_path).suffix.lower() in valid_extensions
        
    def load_image(self, file_path: str):
        """Load and display an image"""
        try:
            # Load with OpenCV to get original image data
            self.original_image = cv2.imread(file_path)
            if self.original_image is None:
                QMessageBox.warning(self, "Error", f"Cannot load image: {file_path}")
                return
            
            # Clear previous barcode results
            self.barcode_results = []
            
            # Update display
            self.update_display()
            
            # Emit signal when image is loaded
            self.image_loaded.emit(file_path)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
            
    def update_display(self):
        """Update the display with current pixmap and overlays"""
        if self.original_image is not None:
            # Create a copy of the original image for drawing overlays
            display_image = self.original_image.copy()
            
            # Draw barcode overlays if available
            if self.barcode_results:
                display_image = self.draw_barcode_overlays_opencv(display_image)
            
            # Convert OpenCV image to QImage
            height, width, channel = display_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(display_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
            
            # Create pixmap and scale to fit widget
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            
            self.setPixmap(scaled_pixmap)
            self.setStyleSheet("")  # Remove border when image is loaded
        else:
            self.setPixmap(QPixmap())
            
    def draw_barcode_overlays(self, pixmap: QPixmap) -> QPixmap:
        """Draw bounding boxes and text overlays for detected barcodes"""
        if not self.barcode_results or not self.original_image:
            return pixmap
            
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate scaling factors
        scale_x = pixmap.width() / self.original_image.shape[1]
        scale_y = pixmap.height() / self.original_image.shape[0]
        
        # Draw each barcode result
        for i, result in enumerate(self.barcode_results):
            # Set color based on barcode index
            colors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255), 
                     QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)]
            color = colors[i % len(colors)]
            
            pen = QPen(color, 3)
            painter.setPen(pen)
            
            # Draw bounding box
            points = result['location']
            if len(points) >= 4:
                for j in range(len(points)):
                    start_point = QPoint(int(points[j][0] * scale_x), int(points[j][1] * scale_y))
                    end_point = QPoint(int(points[(j + 1) % len(points)][0] * scale_x), 
                                     int(points[(j + 1) % len(points)][1] * scale_y))
                    painter.drawLine(start_point, end_point)
            
            # Draw text label
            if points:
                text_x = int(min(p[0] for p in points) * scale_x)
                text_y = int(min(p[1] for p in points) * scale_y) - 10
                if text_y < 20:
                    text_y = int(max(p[1] for p in points) * scale_y) + 20
                    
                painter.fillRect(text_x - 2, text_y - 15, len(result['text']) * 8 + 4, 20, QBrush(color))
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.drawText(text_x, text_y, f"{result['format']}: {result['text']}")
                
        painter.end()
        return pixmap
        
    def draw_barcode_overlays_opencv(self, image):
        """Draw bounding boxes and text overlays using OpenCV"""
        if not self.barcode_results:
            return image
            
        # Create a copy to avoid modifying the original
        overlay_image = image.copy()
        
        # Define colors for different barcodes (BGR format for OpenCV)
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), 
                 (0, 255, 255), (255, 0, 255), (255, 255, 0)]
        
        for i, result in enumerate(self.barcode_results):
            color = colors[i % len(colors)]
            
            # Draw bounding box
            points = result['location']
            if len(points) >= 4:
                # Convert points to numpy array for OpenCV
                pts = np.array([(int(p[0]), int(p[1])) for p in points], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(overlay_image, [pts], True, color, 3)
            
            # Draw text label
            if points:
                # Find top-left corner for text placement
                min_x = int(min(p[0] for p in points))
                min_y = int(min(p[1] for p in points))
                
                # Prepare text
                text = f"{result['format']}: {result['text']}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                
                # Get text size
                (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
                
                # Adjust text position if too close to top
                text_y = min_y - 10 if min_y > 30 else min_y + text_height + 10
                text_x = min_x
                
                # Draw text background rectangle
                cv2.rectangle(overlay_image, 
                            (text_x - 5, text_y - text_height - 5),
                            (text_x + text_width + 5, text_y + baseline + 5),
                            color, -1)
                
                # Draw text
                cv2.putText(overlay_image, text, (text_x, text_y), 
                          font, font_scale, (255, 255, 255), thickness)
        
        return overlay_image
        
    def set_barcode_results(self, results: List[Dict]):
        """Set barcode detection results for overlay drawing"""
        self.barcode_results = results
        self.update_display()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()

class ParameterAdjustmentTool(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamsoft Barcode Reader - Parameter Adjustment Tool")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize SDK
        self.init_license()
        
        # Load default settings
        self.default_settings = self.get_default_settings()
        self.current_settings = copy.deepcopy(self.default_settings)
        self.current_image_path = None
        
        # Worker thread for barcode detection
        self.detection_worker = BarcodeDetectionWorker()
        self.detection_worker.result_ready.connect(self.on_detection_result)
        self.detection_worker.progress_update.connect(self.on_progress_update)
        
        # Auto-adjustment state
        self.auto_adjusting = False
        self.auto_adjustment_timer = QTimer()
        self.auto_adjustment_timer.timeout.connect(self.auto_adjust_step)
        self.auto_adjustment_params = []  # List of parameter combinations to try
        self.auto_adjustment_index = 0    # Current parameter combination index
        
        # Store references to UI controls for resetting
        self.ui_controls = {}
        
        self.setup_ui()
        self.setup_menu()
        
    def init_license(self):
        """Initialize Dynamsoft license"""
        try:
            error_code, error_message = LicenseManager.init_license(
                "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
            )
            if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
                print(f"License initialization failed: ErrorCode: {error_code}, ErrorString: {error_message}")
            else:
                print("License initialized successfully")
        except Exception as e:
            print(f"Failed to initialize license: {e}")
            
    def get_default_settings(self) -> Dict:
        """Get default settings from SDK"""
        try:
            cvr_instance = CaptureVisionRouter()
            error_code, settings, error_str = cvr_instance.output_settings(EnumPresetTemplate.PT_READ_BARCODES.value, True)
            if error_code == EnumErrorCode.EC_OK and settings:
                actual_settings = json.loads(settings)
                print("*** Using actual SDK settings ***")
                # Debug: Check what BarcodeFormatIds are in the actual settings
                if 'BarcodeReaderTaskSettingOptions' in actual_settings:
                    for i, task in enumerate(actual_settings['BarcodeReaderTaskSettingOptions']):
                        if 'BarcodeFormatIds' in task:
                            print(f"Task {i} original BarcodeFormatIds: {task['BarcodeFormatIds']}")
                            # Ensure BF_ALL is available in the task settings for UI display
                            if 'BF_ALL' not in task['BarcodeFormatIds']:
                                task['BarcodeFormatIds'].append('BF_ALL')
                                print(f"Task {i} updated BarcodeFormatIds: {task['BarcodeFormatIds']}")
                return actual_settings
            else:
                print(f"Failed to get default settings: {error_str}")
                # Return a basic fallback configuration
                print("*** Using fallback settings ***")
                return self.get_fallback_settings()
        except Exception as e:
            print(f"Error getting default settings: {e}")
            print("*** Using fallback settings ***")
            return self.get_fallback_settings()
            
    def get_fallback_settings(self) -> Dict:
        """Get fallback settings when SDK settings are not available"""
        return {
            "BarcodeFormatSpecificationOptions": [
                {
                    "BarcodeFormatIds": ["BF_ALL"],
                    "MirrorMode": "MM_NORMAL",
                    "Name": "default_format_spec"
                }
            ],
            "BarcodeReaderTaskSettingOptions": [
                {
                    "BarcodeFormatIds": ["BF_DEFAULT"],
                    "BarcodeFormatSpecificationNameArray": ["default_format_spec"],
                    "ExpectedBarcodesCount": 0,
                    "Name": "default_task",
                    "SectionArray": [
                        {
                            "ImageParameterName": "default_image_param",
                            "Section": "ST_BARCODE_LOCALIZATION",
                            "StageArray": [
                                {
                                    "LocalizationModes": [
                                        {"Mode": "LM_CONNECTED_BLOCKS"},
                                        {"Mode": "LM_LINES"}
                                    ],
                                    "Stage": "SST_LOCALIZE_CANDIDATE_BARCODES"
                                }
                            ]
                        }
                    ]
                }
            ],
            "CaptureVisionTemplates": [
                {
                    "ImageROIProcessingNameArray": ["default_roi"],
                    "Name": "ReadBarcodes_Default"
                }
            ],
            "ImageParameterOptions": [
                {
                    "Name": "default_image_param",
                    "ApplicableStages": [
                        {
                            "Stage": "SST_BINARIZE_IMAGE",
                            "BinarizationModes": [
                                {
                                    "Mode": "BM_LOCAL_BLOCK",
                                    "BlockSizeX": 71,
                                    "BlockSizeY": 71,
                                    "EnableFillBinaryVacancy": 0
                                }
                            ]
                        }
                    ]
                }
            ],
            "TargetROIDefOptions": [
                {
                    "Name": "default_roi",
                    "TaskSettingNameArray": ["default_task"]
                }
            ]
        }
            
    def setup_ui(self):
        """Setup the main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Parameter panel (left)
        self.parameter_panel = self.create_parameter_panel()
        main_splitter.addWidget(self.parameter_panel)
        
        # Right side vertical splitter for image and results
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Image panel (top right)
        image_group = QGroupBox("Image")
        image_layout = QVBoxLayout()
        self.image_panel = ImagePanel()
        self.image_panel.image_loaded.connect(self.on_image_loaded)  # Connect signal
        image_layout.addWidget(self.image_panel)
        image_group.setLayout(image_layout)
        right_splitter.addWidget(image_group)
        
        # Result panel (bottom right)
        self.result_panel = self.create_result_panel()
        right_splitter.addWidget(self.result_panel)
        
        main_splitter.addWidget(right_splitter)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 800])
        right_splitter.setSizes([500, 300])
        
        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        central_widget.setLayout(layout)
        
    def create_parameter_panel(self) -> QWidget:
        """Create the parameter adjustment panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Parameter Configuration")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("Test Parameters")
        self.test_btn.clicked.connect(self.test_parameters)
        button_layout.addWidget(self.test_btn)
        
        self.auto_adjust_btn = QPushButton("Auto Adjust")
        self.auto_adjust_btn.clicked.connect(self.toggle_auto_adjustment)
        button_layout.addWidget(self.auto_adjust_btn)
        
        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.clicked.connect(self.reset_parameters)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        
        # Parameter tabs
        self.param_tabs = QTabWidget()
        
        # Create parameter controls based on JSON structure
        self.create_parameter_controls()
        
        layout.addWidget(self.param_tabs)
        
        panel.setLayout(layout)
        panel.setMaximumWidth(400)
        return panel
        
    def create_parameter_controls(self):
        """Create parameter control widgets based on JSON structure"""
        if not self.default_settings:
            placeholder = QLabel("No parameter settings available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.param_tabs.addTab(placeholder, "Parameters")
            return
            
        # Create tabs for different parameter categories
        self.create_barcode_format_tab()
        self.create_barcode_reader_task_tab()
        self.create_image_parameter_tab()
        self.create_capture_vision_template_tab()
        
    def create_barcode_format_tab(self):
        """Create barcode format specification controls"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # BarcodeFormatSpecificationOptions
        if 'BarcodeFormatSpecificationOptions' in self.default_settings:
            format_specs = self.default_settings['BarcodeFormatSpecificationOptions']
            
            for i, spec in enumerate(format_specs):
                group = QGroupBox(f"Format Spec: {spec.get('Name', f'Spec {i+1}')}")
                group_layout = QVBoxLayout()
                
                # Barcode Format IDs
                if 'BarcodeFormatIds' in spec:
                    formats_group = QGroupBox("Barcode Formats")
                    formats_main_layout = QVBoxLayout()
                    
                    # Add Select All/Unselect All buttons
                    button_layout = QHBoxLayout()
                    select_all_btn = QPushButton("Select All")
                    unselect_all_btn = QPushButton("Unselect All")
                    
                    button_layout.addWidget(select_all_btn)
                    button_layout.addWidget(unselect_all_btn)
                    button_layout.addStretch()
                    formats_main_layout.addLayout(button_layout)
                    
                    formats_layout = QGridLayout()
                    
                    # Common barcode formats with checkboxes
                    common_formats = [
                        'BF_ALL', 'BF_CODE_128', 'BF_CODE_39', 'BF_CODE_93',
                        'BF_CODABAR', 'BF_EAN_13', 'BF_EAN_8', 'BF_UPC_A',
                        'BF_UPC_E', 'BF_QR_CODE', 'BF_DATAMATRIX', 'BF_PDF417',
                        'BF_AZTEC', 'BF_MICRO_QR', 'BF_MICRO_PDF417', 'BF_DOTCODE'
                    ]
                    
                    format_checkboxes = []  # Store checkboxes for bulk operations
                    row, col = 0, 0
                    for fmt in common_formats:
                        checkbox = QCheckBox(fmt.replace('BF_', ''))
                        checkbox.setChecked(fmt in spec['BarcodeFormatIds'] or 'BF_ALL' in spec['BarcodeFormatIds'])
                        checkbox.stateChanged.connect(partial(self.on_format_changed, fmt, spec))
                        
                        format_checkboxes.append(checkbox)
                        
                        # Store reference for resetting
                        control_key = f"format_{spec.get('Name', f'spec_{i}')}_{fmt}"
                        self.ui_controls[control_key] = (checkbox, 'checked', fmt in spec['BarcodeFormatIds'] or 'BF_ALL' in spec['BarcodeFormatIds'])
                        
                        formats_layout.addWidget(checkbox, row, col)
                        col += 1
                        if col > 2:  # 3 columns
                            col = 0
                            row += 1
                    
                    # Connect bulk operation buttons
                    select_all_btn.clicked.connect(partial(self.select_all_checkboxes, format_checkboxes, True))
                    unselect_all_btn.clicked.connect(partial(self.select_all_checkboxes, format_checkboxes, False))
                    
                    formats_main_layout.addLayout(formats_layout)
                    formats_group.setLayout(formats_main_layout)
                    group_layout.addWidget(formats_group)
                
                # Mirror Mode
                if 'MirrorMode' in spec:
                    mirror_group = QGroupBox("Mirror Mode")
                    mirror_layout = QHBoxLayout()
                    
                    mirror_combo = QComboBox()
                    mirror_combo.addItems(['MM_NORMAL', 'MM_MIRROR', 'MM_BOTH'])
                    mirror_combo.setCurrentText(spec['MirrorMode'])
                    mirror_combo.currentTextChanged.connect(partial(self.on_mirror_mode_changed, spec))
                    
                    # Store reference for resetting
                    control_key = f"mirror_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (mirror_combo, 'text', spec['MirrorMode'])
                    
                    mirror_layout.addWidget(mirror_combo)
                    
                    mirror_group.setLayout(mirror_layout)
                    group_layout.addWidget(mirror_group)
                
                # Advanced Settings Group
                advanced_group = QGroupBox("Advanced Settings")
                advanced_layout = QFormLayout()
                
                # MinResultConfidence
                if 'MinResultConfidence' in spec:
                    confidence_spin = QSpinBox()
                    confidence_spin.setRange(0, 100)
                    confidence_spin.setValue(spec['MinResultConfidence'])
                    confidence_spin.setMinimumWidth(120)
                    confidence_spin.valueChanged.connect(partial(self.on_min_confidence_changed, spec))
                    advanced_layout.addRow("Min Result Confidence:", confidence_spin)
                    
                    control_key = f"confidence_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (confidence_spin, 'value', spec['MinResultConfidence'])
                
                # MinQuietZoneWidth  
                if 'MinQuietZoneWidth' in spec:
                    quiet_zone_spin = QSpinBox()
                    quiet_zone_spin.setRange(0, 20)
                    quiet_zone_spin.setValue(spec['MinQuietZoneWidth'])
                    quiet_zone_spin.setMinimumWidth(120)
                    quiet_zone_spin.valueChanged.connect(partial(self.on_quiet_zone_changed, spec))
                    advanced_layout.addRow("Min Quiet Zone Width:", quiet_zone_spin)
                    
                    control_key = f"quiet_zone_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (quiet_zone_spin, 'value', spec['MinQuietZoneWidth'])
                
                # FindUnevenModuleBarcode checkbox
                if 'FindUnevenModuleBarcode' in spec:
                    uneven_checkbox = QCheckBox("Find Uneven Module Barcode")
                    uneven_checkbox.setChecked(bool(spec['FindUnevenModuleBarcode']))
                    uneven_checkbox.stateChanged.connect(partial(self.on_uneven_module_changed, spec))
                    advanced_layout.addRow(uneven_checkbox)
                    
                    control_key = f"uneven_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (uneven_checkbox, 'checked', bool(spec['FindUnevenModuleBarcode']))
                
                if advanced_layout.rowCount() > 0:
                    advanced_group.setLayout(advanced_layout)
                    group_layout.addWidget(advanced_group)
                
                group.setLayout(group_layout)
                scroll_layout.addWidget(group)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        self.param_tabs.addTab(tab, "Barcode Formats")
        
    def create_barcode_reader_task_tab(self):
        """Create barcode reader task controls"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # BarcodeReaderTaskSettingOptions
        if 'BarcodeReaderTaskSettingOptions' in self.default_settings:
            task_settings = self.default_settings['BarcodeReaderTaskSettingOptions']
            
            for i, task in enumerate(task_settings):
                group = QGroupBox(f"Task: {task.get('Name', f'Task {i+1}')}")
                group_layout = QVBoxLayout()
                
                # BarcodeFormatIds for Reader Task
                if 'BarcodeFormatIds' in task:
                    formats_group = QGroupBox("Barcode Format IDs")
                    formats_layout = QVBoxLayout()
                    
                    # Define all supported barcode formats with descriptions
                    # Use ordered list to ensure BF_DEFAULT and BF_ALL appear at top
                    barcode_formats_ordered = [
                        ('BF_DEFAULT', 'Default commonly used formats ⭐'),
                        ('BF_ALL', 'All supported formats ⭐'),
                        ('BF_ONED', 'All one-dimensional formats'),
                        ('BF_CODE_39', 'Code 39'),
                        ('BF_CODE_128', 'Code 128'), 
                        ('BF_CODE_93', 'Code 93'),
                        ('BF_CODABAR', 'Codabar'),
                        ('BF_ITF', 'Interleaved 2 of 5'),
                        ('BF_EAN_13', 'EAN-13'),
                        ('BF_EAN_8', 'EAN-8'),
                        ('BF_UPC_A', 'UPC-A'),
                        ('BF_UPC_E', 'UPC-E'),
                        ('BF_INDUSTRIAL_25', 'Industrial 2 of 5'),
                        ('BF_CODE_39_EXTENDED', 'Extended Code 39'),
                        ('BF_QR_CODE', 'QR Code'),
                        ('BF_DATAMATRIX', 'DataMatrix'),
                        ('BF_PDF417', 'PDF417'),
                        ('BF_AZTEC', 'Aztec'),
                        ('BF_MICRO_QR', 'Micro QR'),
                        ('BF_MICRO_PDF417', 'Micro PDF417'),
                        ('BF_DOTCODE', 'DotCode'),
                        ('BF_MAXICODE', 'MaxiCode'),
                        ('BF_GS1_DATABAR', 'GS1 DataBar (All)'),
                        ('BF_GS1_DATABAR_OMNIDIRECTIONAL', 'GS1 DataBar Omnidirectional'),
                        ('BF_GS1_DATABAR_TRUNCATED', 'GS1 DataBar Truncated'),
                        ('BF_GS1_DATABAR_STACKED', 'GS1 DataBar Stacked'),
                        ('BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL', 'GS1 DataBar Stacked Omnidirectional'),
                        ('BF_GS1_DATABAR_EXPANDED', 'GS1 DataBar Expanded'),
                        ('BF_GS1_DATABAR_EXPANDED_STACKED', 'GS1 DataBar Expanded Stacked'),
                        ('BF_GS1_DATABAR_LIMITED', 'GS1 DataBar Limited'),
                        ('BF_PATCHCODE', 'Patch Code'),
                        ('BF_MSI_CODE', 'MSI Code'),
                        ('BF_CODE_11', 'Code 11'),
                        ('BF_TWO_DIGIT_ADD_ON', 'Two-Digit Add-On'),
                        ('BF_FIVE_DIGIT_ADD_ON', 'Five-Digit Add-On'),
                        ('BF_CODE_32', 'Code 32 (Italian PharmaCode)'),
                        ('BF_GS1_COMPOSITE', 'GS1 Composite'),
                        ('BF_NONSTANDARD_BARCODE', 'Nonstandard Barcode'),
                        ('BF_PHARMACODE', 'PharmaCode (All)'),
                        ('BF_PHARMACODE_ONE_TRACK', 'PharmaCode One Track'),
                        ('BF_PHARMACODE_TWO_TRACK', 'PharmaCode Two Track'), 
                        ('BF_MATRIX_25', 'Matrix 2 of 5'),
                        ('BF_POSTALCODE', 'Postal Code (All)'),
                        ('BF_USPSINTELLIGENTMAIL', 'USPS Intelligent Mail'),
                        ('BF_POSTNET', 'Postnet'),
                        ('BF_PLANET', 'Planet'),
                        ('BF_AUSTRALIANPOST', 'Australian Post'),
                        ('BF_RM4SCC', 'RM4SCC (Royal Mail)'),
                        ('BF_KIX', 'KIX (Dutch Postal)')
                    ]
                    
                    # Create a 3-column layout for checkboxes
                    checkbox_layout = QGridLayout()
                    row = 0
                    col = 0
                    
                    task_format_checkboxes = {}
                    for format_id, description in barcode_formats_ordered:
                        checkbox = QCheckBox(f"{format_id} - {description}")
                        # Check the checkbox if the format is in the task's BarcodeFormatIds
                        checkbox.setChecked(format_id in task['BarcodeFormatIds'])
                        checkbox.stateChanged.connect(partial(self.on_task_format_changed, task, format_id))
                        
                        checkbox_layout.addWidget(checkbox, row, col)
                        task_format_checkboxes[format_id] = checkbox
                        
                        # Store reference for resetting
                        control_key = f"task_format_{format_id}_{task.get('Name', f'task_{i}')}"
                        self.ui_controls[control_key] = (checkbox, 'checked', format_id in task['BarcodeFormatIds'])
                        
                        col += 1
                        if col >= 2:  # 2 columns
                            col = 0
                            row += 1
                    
                    # Add bulk operations
                    bulk_layout = QHBoxLayout()
                    select_all_btn = QPushButton("Select All")
                    unselect_all_btn = QPushButton("Unselect All")
                    
                    select_all_btn.clicked.connect(partial(self.select_all_task_formats, task_format_checkboxes, task))
                    unselect_all_btn.clicked.connect(partial(self.unselect_all_task_formats, task_format_checkboxes, task))
                    
                    bulk_layout.addWidget(select_all_btn)
                    bulk_layout.addWidget(unselect_all_btn)
                    bulk_layout.addStretch()
                    
                    formats_layout.addLayout(checkbox_layout)
                    formats_layout.addLayout(bulk_layout)
                    formats_group.setLayout(formats_layout)
                    group_layout.addWidget(formats_group)
                
                # Expected Barcodes Count
                if 'ExpectedBarcodesCount' in task:
                    count_layout = QHBoxLayout()
                    count_layout.addWidget(QLabel("Expected Barcodes Count:"))
                    count_spin = QSpinBox()
                    count_spin.setRange(0, 999)
                    count_spin.setValue(task['ExpectedBarcodesCount'])
                    count_spin.setMinimumWidth(120)  # Make wider
                    count_spin.valueChanged.connect(partial(self.on_expected_count_changed, task))
                    
                    # Store reference for resetting
                    control_key = f"count_{task.get('Name', f'task_{i}')}"
                    self.ui_controls[control_key] = (count_spin, 'value', task['ExpectedBarcodesCount'])
                    
                    count_layout.addWidget(count_spin)
                    count_layout.addStretch()
                    group_layout.addLayout(count_layout)
                
                # Max Threads In One Task
                if 'MaxThreadsInOneTask' in task:
                    threads_layout = QHBoxLayout()
                    threads_layout.addWidget(QLabel("Max Threads In One Task:"))
                    threads_spin = QSpinBox()
                    threads_spin.setRange(1, 16)
                    threads_spin.setValue(task['MaxThreadsInOneTask'])
                    threads_spin.setMinimumWidth(120)
                    threads_spin.valueChanged.connect(partial(self.on_max_threads_changed, task))
                    
                    # Store reference for resetting
                    control_key = f"threads_{task.get('Name', f'task_{i}')}"
                    self.ui_controls[control_key] = (threads_spin, 'value', task['MaxThreadsInOneTask'])
                    
                    threads_layout.addWidget(threads_spin)
                    threads_layout.addStretch()
                    group_layout.addLayout(threads_layout)
                
                # Localization Modes (from sections)
                if 'SectionArray' in task:
                    for section in task['SectionArray']:
                        if section.get('Section') == 'ST_BARCODE_LOCALIZATION':
                            for stage in section.get('StageArray', []):
                                if 'LocalizationModes' in stage:
                                    loc_group = QGroupBox("Localization Modes")
                                    loc_main_layout = QVBoxLayout()
                                    
                                    # Add Select All/Unselect All buttons
                                    loc_button_layout = QHBoxLayout()
                                    loc_select_all_btn = QPushButton("Select All")
                                    loc_unselect_all_btn = QPushButton("Unselect All")
                                    
                                    loc_button_layout.addWidget(loc_select_all_btn)
                                    loc_button_layout.addWidget(loc_unselect_all_btn)
                                    loc_button_layout.addStretch()
                                    loc_main_layout.addLayout(loc_button_layout)
                                    
                                    loc_layout = QVBoxLayout()
                                    loc_checkboxes = []  # Store checkboxes for bulk operations
                                    
                                    for j, mode in enumerate(stage['LocalizationModes']):
                                        mode_text = mode.get('Mode', 'Unknown')
                                        mode_widget = QWidget()
                                        mode_layout = QHBoxLayout()
                                        mode_layout.setContentsMargins(0, 0, 0, 0)
                                        
                                        checkbox = QCheckBox(mode_text.replace('LM_', ''))
                                        checkbox.setChecked(True)
                                        checkbox.stateChanged.connect(
                                            partial(self.on_localization_mode_changed, task, mode_text)
                                        )
                                        mode_layout.addWidget(checkbox)
                                        loc_checkboxes.append(checkbox)
                                        
                                        # Add confidence threshold control if available
                                        if 'ConfidenceThreshold' in mode:
                                            confidence_label = QLabel("Confidence:")
                                            confidence_spin = QSpinBox()
                                            confidence_spin.setRange(0, 100)
                                            confidence_spin.setValue(mode['ConfidenceThreshold'])
                                            confidence_spin.setMinimumWidth(60)
                                            confidence_spin.valueChanged.connect(
                                                partial(self.on_localization_confidence_changed, task, j, mode_text)
                                            )
                                            mode_layout.addWidget(confidence_label)
                                            mode_layout.addWidget(confidence_spin)
                                            
                                            # Store UI control for reset functionality
                                            control_key = f"loc_conf_{task.get('Name', f'task_{i}')}_{j}_{mode_text}"
                                            self.ui_controls[control_key] = (confidence_spin, 'value', mode['ConfidenceThreshold'])
                                        
                                        mode_layout.addStretch()
                                        mode_widget.setLayout(mode_layout)
                                        loc_layout.addWidget(mode_widget)
                                        
                                        # Store UI control for reset functionality
                                        control_key = f"localization_{task.get('Name', f'task_{i}')}_{j}_{mode_text}"
                                        self.ui_controls[control_key] = (checkbox, 'checked', True)
                                    
                                    # Connect bulk operation buttons
                                    loc_select_all_btn.clicked.connect(partial(self.select_all_checkboxes, loc_checkboxes, True))
                                    loc_unselect_all_btn.clicked.connect(partial(self.select_all_checkboxes, loc_checkboxes, False))
                                    
                                    loc_main_layout.addLayout(loc_layout)
                                    loc_group.setLayout(loc_main_layout)
                                    group_layout.addWidget(loc_group)
                                    break
                
                group.setLayout(group_layout)
                scroll_layout.addWidget(group)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        self.param_tabs.addTab(tab, "Reader Tasks")
        
    def create_image_parameter_tab(self):
        """Create image parameter controls"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # ImageParameterOptions
        if 'ImageParameterOptions' in self.default_settings:
            image_params = self.default_settings['ImageParameterOptions']
            
            for i, param in enumerate(image_params):
                group = QGroupBox(f"Image Param: {param.get('Name', f'Param {i+1}')}")
                group_layout = QVBoxLayout()
                
                if 'ApplicableStages' in param:
                    for stage in param['ApplicableStages']:
                        stage_name = stage.get('Stage', 'Unknown Stage')
                        stage_group = QGroupBox(stage_name.replace('SST_', ''))
                        stage_layout = QVBoxLayout()
                        
                        # Binarization Modes
                        if 'BinarizationModes' in stage:
                            bin_group = QGroupBox("Binarization")
                            bin_layout = QFormLayout()
                            
                            for bin_mode in stage['BinarizationModes']:
                                mode_text = bin_mode.get('Mode', 'Unknown')
                                bin_layout.addRow(QLabel(f"Mode: {mode_text.replace('BM_', '')}"))
                                
                                if 'BlockSizeX' in bin_mode:
                                    block_x_spin = QSpinBox()
                                    block_x_spin.setRange(0, 200)
                                    block_x_spin.setValue(bin_mode['BlockSizeX'])
                                    block_x_spin.setMinimumWidth(120)  # Make wider
                                    block_x_spin.valueChanged.connect(
                                        partial(self.on_block_size_changed, bin_mode, 'BlockSizeX')
                                    )
                                    bin_layout.addRow("Block Size X:", block_x_spin)
                                    
                                    # Store UI control for reset functionality
                                    control_key = f"block_size_x_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (block_x_spin, 'value', bin_mode['BlockSizeX'])
                                
                                if 'BlockSizeY' in bin_mode:
                                    block_y_spin = QSpinBox()
                                    block_y_spin.setRange(0, 200)
                                    block_y_spin.setValue(bin_mode['BlockSizeY'])
                                    block_y_spin.setMinimumWidth(120)  # Make wider
                                    block_y_spin.valueChanged.connect(
                                        partial(self.on_block_size_changed, bin_mode, 'BlockSizeY')
                                    )
                                    bin_layout.addRow("Block Size Y:", block_y_spin)
                                    
                                    # Store UI control for reset functionality
                                    control_key = f"block_size_y_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (block_y_spin, 'value', bin_mode['BlockSizeY'])
                            
                            bin_group.setLayout(bin_layout)
                            stage_layout.addWidget(bin_group)
                        
                        # Grayscale Transformation Modes
                        if 'GrayscaleTransformationModes' in stage:
                            gray_group = QGroupBox("Grayscale Transformation")
                            gray_main_layout = QVBoxLayout()
                            
                            # Add Select All/Unselect All buttons
                            gray_button_layout = QHBoxLayout()
                            gray_select_all_btn = QPushButton("Select All")
                            gray_unselect_all_btn = QPushButton("Unselect All")
                            
                            gray_button_layout.addWidget(gray_select_all_btn)
                            gray_button_layout.addWidget(gray_unselect_all_btn)
                            gray_button_layout.addStretch()
                            gray_main_layout.addLayout(gray_button_layout)
                            
                            gray_layout = QVBoxLayout()
                            gray_checkboxes = []  # Store checkboxes for bulk operations
                            
                            for j, gray_mode in enumerate(stage['GrayscaleTransformationModes']):
                                mode_text = gray_mode.get('Mode', 'Unknown')
                                checkbox = QCheckBox(mode_text.replace('GTM_', ''))
                                checkbox.setChecked(True)
                                checkbox.stateChanged.connect(
                                    partial(self.on_grayscale_mode_changed, param, stage_name, gray_mode)
                                )
                                gray_layout.addWidget(checkbox)
                                gray_checkboxes.append(checkbox)
                                
                                # Store UI control for reset functionality
                                control_key = f"grayscale_{param.get('Name', f'param_{i}')}_{stage_name}_{j}_{mode_text}"
                                self.ui_controls[control_key] = (checkbox, 'checked', True)
                            
                            # Connect bulk operation buttons
                            gray_select_all_btn.clicked.connect(partial(self.select_all_checkboxes, gray_checkboxes, True))
                            gray_unselect_all_btn.clicked.connect(partial(self.select_all_checkboxes, gray_checkboxes, False))
                            
                            gray_main_layout.addLayout(gray_layout)
                            gray_group.setLayout(gray_main_layout)
                            stage_layout.addWidget(gray_group)
                        
                        # Text Detection Mode
                        if 'TextDetectionMode' in stage:
                            text_group = QGroupBox("Text Detection")
                            text_layout = QFormLayout()
                            
                            text_mode = stage['TextDetectionMode']
                            if 'Sensitivity' in text_mode:
                                sens_spin = QSpinBox()
                                sens_spin.setRange(1, 9)
                                sens_spin.setValue(text_mode['Sensitivity'])
                                sens_spin.setMinimumWidth(120)  # Make wider
                                sens_spin.valueChanged.connect(
                                    partial(self.on_text_sensitivity_changed, text_mode)
                                )
                                text_layout.addRow("Sensitivity:", sens_spin)
                                
                                # Store UI control for reset functionality
                                control_key = f"text_sensitivity_{param.get('Name', f'param_{i}')}_{stage_name}"
                                self.ui_controls[control_key] = (sens_spin, 'value', text_mode['Sensitivity'])
                            
                            text_group.setLayout(text_layout)
                            stage_layout.addWidget(text_group)
                        
                        stage_group.setLayout(stage_layout)
                        group_layout.addWidget(stage_group)
                
                group.setLayout(group_layout)
                scroll_layout.addWidget(group)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        self.param_tabs.addTab(tab, "Image Processing")
        
    def create_capture_vision_template_tab(self):
        """Create capture vision template controls"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Template selection
        template_group = QGroupBox("Template Selection")
        template_layout = QVBoxLayout()
        
        self.template_combo = QComboBox()
        if 'CaptureVisionTemplates' in self.default_settings:
            templates = self.default_settings['CaptureVisionTemplates']
            for template in templates:
                self.template_combo.addItem(template.get('Name', 'Unknown Template'))
        
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        template_layout.addWidget(QLabel("Active Template:"))
        template_layout.addWidget(self.template_combo)
        
        # Store UI control for reset functionality
        default_template = self.default_settings.get('CaptureVisionTemplates', [{}])[0].get('Name', 'ReadBarcodes_Default') if self.default_settings.get('CaptureVisionTemplates') else 'ReadBarcodes_Default'
        self.ui_controls['template'] = (self.template_combo, 'text', default_template)
        
        # Timeout setting
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout (ms):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1000, 300000)
        self.timeout_spin.setValue(10000)
        self.timeout_spin.setMinimumWidth(120)  # Make wider
        self.timeout_spin.valueChanged.connect(self.on_timeout_changed)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        template_layout.addLayout(timeout_layout)
        
        # Store UI control for reset functionality
        self.ui_controls['timeout'] = (self.timeout_spin, 'value', 10000)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.param_tabs.addTab(tab, "Templates")
        
    # Parameter change event handlers
    def on_format_changed(self, format_id: str, spec: Dict, state: int):
        """Handle barcode format checkbox changes"""
        # Find the spec in current_settings and update it
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    if 'BarcodeFormatIds' not in current_spec:
                        current_spec['BarcodeFormatIds'] = []
                    
                    # Make a copy to avoid modifying while iterating
                    current_formats = current_spec['BarcodeFormatIds'][:]
                    
                    if state == Qt.CheckState.Checked.value:
                        if format_id not in current_formats:
                            current_spec['BarcodeFormatIds'].append(format_id)
                    else:
                        if format_id in current_formats:
                            current_spec['BarcodeFormatIds'].remove(format_id)
                    
                    # Allow empty array - don't force BF_ALL
                    
                    break
                        
        self.update_settings()
        
    def on_mirror_mode_changed(self, spec: Dict, mode: str):
        """Handle mirror mode changes"""
        # Find the spec in current_settings and update it
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['MirrorMode'] = mode
                    break
        self.update_settings()
        
    def on_min_confidence_changed(self, spec: Dict, value: int):
        """Handle minimum result confidence changes"""
        # Find the spec in current_settings and update it
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['MinResultConfidence'] = value
                    break
        self.update_settings()
        
    def on_quiet_zone_changed(self, spec: Dict, value: int):
        """Handle minimum quiet zone width changes"""
        # Find the spec in current_settings and update it
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['MinQuietZoneWidth'] = value
                    break
        self.update_settings()
        
    def on_uneven_module_changed(self, spec: Dict, state: int):
        """Handle find uneven module barcode checkbox changes"""
        # Find the spec in current_settings and update it
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['FindUnevenModuleBarcode'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_expected_count_changed(self, task: Dict, count: int):
        """Handle expected barcode count changes"""
        # Find the task in current_settings and update it
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    current_task['ExpectedBarcodesCount'] = count
                    break
        self.update_settings()
        
    def on_max_threads_changed(self, task: Dict, threads: int):
        """Handle max threads in one task changes"""
        # Find the task in current_settings and update it
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    current_task['MaxThreadsInOneTask'] = threads
                    break
        self.update_settings()
        
    def on_task_format_changed(self, task: Dict, format_id: str, state: int):
        """Handle task barcode format changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if state == 2:  # Checked
                        if format_id not in current_task['BarcodeFormatIds']:
                            current_task['BarcodeFormatIds'].append(format_id)
                    else:  # Unchecked
                        if format_id in current_task['BarcodeFormatIds']:
                            current_task['BarcodeFormatIds'].remove(format_id)
                    break
        self.update_settings()
    
    def select_all_task_formats(self, checkboxes: Dict, task: Dict):
        """Select all task barcode formats"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    current_task['BarcodeFormatIds'] = list(checkboxes.keys())
                    break
        
        # Update all checkboxes to checked state
        for checkbox in checkboxes.values():
            checkbox.setChecked(True)
            
        self.update_settings()
    
    def unselect_all_task_formats(self, checkboxes: Dict, task: Dict):
        """Unselect all task barcode formats"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    current_task['BarcodeFormatIds'] = []
                    break
        
        # Update all checkboxes to unchecked state
        for checkbox in checkboxes.values():
            checkbox.setChecked(False)
            
        self.update_settings()
        
    def on_localization_mode_changed(self, task: Dict, mode: str, state: int):
        """Handle localization mode changes"""
        # Find and update localization modes in the current_settings
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_LOCALIZATION':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_LOCALIZE_CANDIDATE_BARCODES' and 'LocalizationModes' in stage:
                                        modes = stage['LocalizationModes']
                                        mode_found = False
                                        
                                        # Check if mode already exists
                                        for i, existing_mode in enumerate(modes):
                                            if existing_mode.get('Mode') == mode:
                                                if state != Qt.CheckState.Checked.value:
                                                    # Remove mode if unchecked
                                                    modes.pop(i)
                                                mode_found = True
                                                break
                                        
                                        # Add mode if checked and not found
                                        if state == Qt.CheckState.Checked.value and not mode_found:
                                            modes.append({'Mode': mode})
                                        
                                        # Ensure at least one mode is present
                                        if not modes:
                                            modes.append({'Mode': 'LM_CONNECTED_BLOCKS'})  # Default mode
                                    break
                            break
                    break
                                
        self.update_settings()
        
    def on_localization_confidence_changed(self, task: Dict, mode_index: int, mode_text: str, value: int):
        """Handle localization mode confidence threshold changes"""
        # Find and update confidence threshold in the current_settings
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_LOCALIZATION':
                                for stage in section.get('StageArray', []):
                                    if 'LocalizationModes' in stage:
                                        if mode_index < len(stage['LocalizationModes']):
                                            if stage['LocalizationModes'][mode_index].get('Mode') == mode_text:
                                                stage['LocalizationModes'][mode_index]['ConfidenceThreshold'] = value
                                                self.update_settings()
                                                return
                    break
        self.update_settings()
        
    def on_block_size_changed(self, bin_mode: Dict, param: str, value: int):
        """Handle block size changes"""
        # Find and update block size in current_settings
        if 'ImageParameterOptions' in self.current_settings:
            for current_param in self.current_settings['ImageParameterOptions']:
                if 'ApplicableStages' in current_param:
                    for stage in current_param['ApplicableStages']:
                        if 'BinarizationModes' in stage:
                            for current_bin_mode in stage['BinarizationModes']:
                                # Match by Mode type - this is a simplified approach
                                if (current_bin_mode.get('Mode') == bin_mode.get('Mode') and 
                                    param in current_bin_mode):
                                    current_bin_mode[param] = value
                                    self.update_settings()
                                    return
        self.update_settings()
        
    def on_text_sensitivity_changed(self, text_mode: Dict, value: int):
        """Handle text detection sensitivity changes"""
        # Find and update sensitivity in current_settings
        if 'ImageParameterOptions' in self.current_settings:
            for current_param in self.current_settings['ImageParameterOptions']:
                if 'ApplicableStages' in current_param:
                    for stage in current_param['ApplicableStages']:
                        if 'TextDetectionMode' in stage and 'Sensitivity' in stage['TextDetectionMode']:
                            stage['TextDetectionMode']['Sensitivity'] = value
                            self.update_settings()
                            return
        self.update_settings()
        
    def on_grayscale_mode_changed(self, param: Dict, stage_name: str, gray_mode: Dict, state: int):
        """Handle grayscale transformation mode changes"""
        # This is a complex update that would require finding the right stage
        self.update_settings()
        
    def on_template_changed(self, template_name: str):
        """Handle template selection changes"""
        # Update current template selection in settings
        if 'CaptureVisionTemplates' in self.current_settings:
            # Move the selected template to the front
            templates = self.current_settings['CaptureVisionTemplates']
            selected_template = None
            for template in templates:
                if template.get('Name') == template_name:
                    selected_template = template
                    break
            
            if selected_template:
                # Remove from current position and add to front
                templates.remove(selected_template)
                templates.insert(0, selected_template)
        
        self.update_settings()
        
    def on_timeout_changed(self, timeout: int):
        """Handle timeout changes"""
        # Update timeout in current template
        if 'CaptureVisionTemplates' in self.current_settings:
            for template in self.current_settings['CaptureVisionTemplates']:
                if template.get('Name') == self.template_combo.currentText():
                    template['Timeout'] = timeout
                    break
        self.update_settings()
        
    def update_settings(self):
        """Update current settings and notify about changes"""
        # Settings are updated in-place through the parameter controls
        # This method can be used to perform additional validation or processing
        print("Updating settings and UI controls...")
        self.update_ui_from_settings()
        self.update_parameters_display()
        
    def update_ui_from_settings(self):
        """Update UI controls to reflect current settings values"""
        print("Updating UI controls from current settings...")
        try:
            # Update expected barcode count controls
            if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
                for i, task in enumerate(self.current_settings['BarcodeReaderTaskSettingOptions']):
                    if 'ExpectedBarcodesCount' in task:
                        control_key = f'expected_count_task_{i}'
                        if control_key in self.ui_controls:
                            control, prop_type, _ = self.ui_controls[control_key]
                            expected_count = task['ExpectedBarcodesCount']
                            print(f"Setting {control_key} to {expected_count}")
                            control.setValue(expected_count)
            
            # Update block size controls
            if 'ImageParameterOptions' in self.current_settings:
                for i, param in enumerate(self.current_settings['ImageParameterOptions']):
                    if 'ApplicableStages' in param:
                        for j, stage in enumerate(param['ApplicableStages']):
                            if 'BinarizationModes' in stage:
                                for k, bin_mode in enumerate(stage['BinarizationModes']):
                                    if 'Mode' in bin_mode and bin_mode['Mode'] == 'BM_LOCAL_BLOCK':
                                        # Update block size X
                                        if 'BlockSizeX' in bin_mode:
                                            control_key = f'block_size_x_param_{i}_stage_{j}_mode_{k}'
                                            if control_key in self.ui_controls:
                                                control, prop_type, _ = self.ui_controls[control_key]
                                                block_x = bin_mode['BlockSizeX']
                                                print(f"Setting {control_key} to {block_x}")
                                                control.setValue(block_x)
                                        
                                        # Update block size Y
                                        if 'BlockSizeY' in bin_mode:
                                            control_key = f'block_size_y_param_{i}_stage_{j}_mode_{k}'
                                            if control_key in self.ui_controls:
                                                control, prop_type, _ = self.ui_controls[control_key]
                                                block_y = bin_mode['BlockSizeY']
                                                print(f"Setting {control_key} to {block_y}")
                                                control.setValue(block_y)
                                                
            print("UI controls updated successfully")
                                                
        except Exception as e:
            print(f"Error updating UI controls from settings: {e}")
        
    def update_parameters_display(self):
        """Update the parameters display text area"""
        if hasattr(self, 'params_text'):
            try:
                # Format the current settings as JSON for display
                params_json = json.dumps(self.current_settings, indent=2)
                self.params_text.setPlainText(params_json)
            except Exception as e:
                self.params_text.setPlainText(f"Error displaying parameters: {e}")
        
    def select_all_checkboxes(self, checkboxes: List, checked: bool):
        """Select or unselect all checkboxes in the given list"""
        for checkbox in checkboxes:
            checkbox.setChecked(checked)
        
    def create_result_panel(self) -> QWidget:
        """Create the result display panel"""
        group = QGroupBox("Detection Results & Parameters")
        layout = QVBoxLayout()
        
        # Create horizontal splitter for results and parameters
        results_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Detection Results (left side)
        results_widget = QWidget()
        results_layout = QVBoxLayout()
        results_layout.addWidget(QLabel("Detection Results:"))
        
        self.result_text = QTextEdit()
        self.result_text.setMinimumHeight(100)
        self.result_text.setReadOnly(True)
        results_layout.addWidget(self.result_text)
        results_widget.setLayout(results_layout)
        
        # Current Parameters (right side)
        params_widget = QWidget()
        params_layout = QVBoxLayout()
        params_layout.addWidget(QLabel("Current Parameters:"))
        
        self.params_text = QTextEdit()
        self.params_text.setMinimumHeight(100)
        self.params_text.setReadOnly(True)
        self.params_text.setFont(QFont("Courier", 8))  # Monospace font for JSON
        params_layout.addWidget(self.params_text)
        params_widget.setLayout(params_layout)
        
        # Add to splitter
        results_splitter.addWidget(results_widget)
        results_splitter.addWidget(params_widget)
        results_splitter.setSizes([300, 300])  # Equal sizes initially
        
        layout.addWidget(results_splitter)
        
        # Export button
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export Working Parameters")
        self.export_btn.clicked.connect(self.export_parameters)
        self.export_btn.setEnabled(True)  # Always enable export
        export_layout.addWidget(self.export_btn)
        export_layout.addStretch()
        
        layout.addLayout(export_layout)
        group.setLayout(layout)
        
        # Initialize parameters display
        self.update_parameters_display()
        
        return group
        
    def setup_menu(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        load_image_action = QAction("Load Image", self)
        load_image_action.setShortcut("Ctrl+O")
        load_image_action.triggered.connect(self.load_image)
        file_menu.addAction(load_image_action)
        
        file_menu.addSeparator()
        
        load_settings_action = QAction("Load Settings", self)
        load_settings_action.triggered.connect(self.load_settings)
        file_menu.addAction(load_settings_action)
        
        save_settings_action = QAction("Save Settings", self)
        save_settings_action.triggered.connect(self.save_settings)
        file_menu.addAction(save_settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def load_image(self):
        """Load an image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.gif)"
        )
        if file_path:
            self.image_panel.load_image(file_path)
            self.current_image_path = file_path
            
    def on_image_loaded(self, file_path: str):
        """Callback when image is loaded"""
        self.current_image_path = file_path
        self.status_bar.showMessage(f"Loaded: {Path(file_path).name}")
        
        # Automatically trigger barcode detection
        QTimer.singleShot(500, self.test_parameters)  # Small delay to ensure UI is updated
        
    def test_parameters(self):
        """Test current parameters with loaded image"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please load an image first")
            return
        
        # Clear previous results
        self.result_text.setPlainText("Testing parameters...")
        self.image_panel.set_barcode_results([])
            
        self.test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Convert current settings to JSON
        settings_json = json.dumps(self.current_settings, indent=2)
        
        # Start detection in worker thread
        self.detection_worker.set_parameters(self.current_image_path, settings_json)
        self.detection_worker.start()
        
    def on_detection_result(self, results: List[Dict], error_message: str):
        """Handle barcode detection results"""
        self.test_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if error_message:
            self.result_text.setPlainText(f"Error: {error_message}")
            self.image_panel.set_barcode_results([])
            return
            
        # Display results
        if results:
            result_text = f"Found {len(results)} barcode(s):\n\n"
            for i, result in enumerate(results, 1):
                result_text += f"{i}. Format: {result['format']}\n"
                result_text += f"   Text: {result['text']}\n"
                result_text += f"   Confidence: {result['confidence']}\n\n"
            
            self.result_text.setPlainText(result_text)
            
            # Stop auto-adjustment if barcodes found
            if self.auto_adjusting:
                self.toggle_auto_adjustment()
                self.status_bar.showMessage(f"Auto-adjustment stopped - {len(results)} barcode(s) found!")
        else:
            self.result_text.setPlainText("No barcodes detected")
            
        # Update image overlay
        self.image_panel.set_barcode_results(results)
        
    def on_progress_update(self, message: str):
        """Handle progress updates from worker thread"""
        self.status_bar.showMessage(message)
        
    def toggle_auto_adjustment(self):
        """Toggle automatic parameter adjustment"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please load an image first")
            return
            
        if not self.auto_adjusting:
            # Clear previous results when starting auto adjustment
            self.result_text.setPlainText("Starting auto-adjustment...")
            self.image_panel.set_barcode_results([])
            
            # Initialize auto-adjustment parameters
            self.prepare_auto_adjustment_params()
            self.auto_adjustment_index = 0
            
            if not self.auto_adjustment_params:
                QMessageBox.warning(self, "Warning", "No parameter combinations prepared for auto-adjustment!")
                return
            
            self.auto_adjusting = True
            self.auto_adjust_btn.setText("Stop Auto Adjust")
            self.auto_adjustment_timer.start(2000)  # 2 second intervals for better visibility
            self.status_bar.showMessage(f"Auto-adjustment started... (0/{len(self.auto_adjustment_params)} combinations)")
            print(f"Auto-adjustment started with {len(self.auto_adjustment_params)} combinations")
        else:
            self.auto_adjusting = False
            self.auto_adjust_btn.setText("Auto Adjust")
            self.auto_adjustment_timer.stop()
            self.status_bar.showMessage("Auto-adjustment stopped")
            
    def prepare_auto_adjustment_params(self):
        """Prepare different parameter combinations for auto-adjustment"""
        print("Preparing auto-adjustment parameters...")
        self.auto_adjustment_params = []
        
        # Different localization mode combinations (ordered by effectiveness)
        localization_modes = [
            # Single modes first
            [{"Mode": "LM_CONNECTED_BLOCKS", "ConfidenceThreshold": 60}],
            [{"Mode": "LM_SCAN_DIRECTLY", "ConfidenceThreshold": 60}],
            [{"Mode": "LM_STATISTICS", "ConfidenceThreshold": 60}],
            [{"Mode": "LM_LINES", "ConfidenceThreshold": 60}],
            
            # Effective combinations
            [{"Mode": "LM_CONNECTED_BLOCKS", "ConfidenceThreshold": 60}, 
             {"Mode": "LM_SCAN_DIRECTLY", "ConfidenceThreshold": 60}],
            [{"Mode": "LM_CONNECTED_BLOCKS", "ConfidenceThreshold": 60}, 
             {"Mode": "LM_STATISTICS", "ConfidenceThreshold": 60}],
            [{"Mode": "LM_SCAN_DIRECTLY", "ConfidenceThreshold": 60}, 
             {"Mode": "LM_LINES", "ConfidenceThreshold": 60}],
             
            # More comprehensive combinations
            [{"Mode": "LM_CONNECTED_BLOCKS", "ConfidenceThreshold": 60}, 
             {"Mode": "LM_SCAN_DIRECTLY", "ConfidenceThreshold": 60},
             {"Mode": "LM_STATISTICS", "ConfidenceThreshold": 60}],
        ]
        
        # Different binarization block sizes (ordered by common effectiveness)
        block_sizes = [
            {"BlockSizeX": 0, "BlockSizeY": 0},  # Auto block size - try first
            {"BlockSizeX": 71, "BlockSizeY": 71},  # Default
            {"BlockSizeX": 51, "BlockSizeY": 51},  # Smaller blocks
            {"BlockSizeX": 31, "BlockSizeY": 31},  # Even smaller
            {"BlockSizeX": 21, "BlockSizeY": 21},  # Fine detail
            {"BlockSizeX": 15, "BlockSizeY": 15},  # Very fine
            {"BlockSizeX": 101, "BlockSizeY": 101}, # Larger blocks
            {"BlockSizeX": 151, "BlockSizeY": 151}, # Very large
        ]
        
        # Different expected barcode counts
        expected_counts = [0, 1, 5]  # Most common scenarios
        
        # Different confidence thresholds for localization
        confidence_levels = [60, 40, 80, 30]
        
        # Create combinations - prioritize most likely to succeed
        combination_count = 0
        max_combinations = 40  # Restore original limit
        
        for expected_count in expected_counts:
            for loc_modes in localization_modes:
                for block_size in block_sizes:
                    for confidence in confidence_levels:
                        if combination_count >= max_combinations:
                            break
                            
                        # Update confidence in localization modes
                        updated_loc_modes = []
                        for mode in loc_modes:
                            updated_mode = mode.copy()
                            updated_mode['ConfidenceThreshold'] = confidence
                            updated_loc_modes.append(updated_mode)
                        
                        param_combination = {
                            'expected_count': expected_count,
                            'localization_modes': updated_loc_modes,
                            'block_size': block_size,
                            'confidence': confidence
                        }
                        self.auto_adjustment_params.append(param_combination)
                        combination_count += 1
                    
                    if combination_count >= max_combinations:
                        break
                if combination_count >= max_combinations:
                    break
            if combination_count >= max_combinations:
                break
                
        print(f"Prepared {len(self.auto_adjustment_params)} parameter combinations for auto-adjustment")
        if len(self.auto_adjustment_params) > 0:
            print(f"First combination: {self.auto_adjustment_params[0]}")
            
    def auto_adjust_step(self):
        """Perform one step of auto adjustment"""
        print(f"Auto-adjust step called. Index: {self.auto_adjustment_index}, Total: {len(self.auto_adjustment_params)}")
        
        if self.auto_adjustment_index >= len(self.auto_adjustment_params):
            # No more combinations to try
            self.auto_adjusting = False
            self.auto_adjust_btn.setText("Auto Adjust")
            self.auto_adjustment_timer.stop()
            self.status_bar.showMessage("Auto-adjustment completed - no barcodes found with any combination")
            self.result_text.setPlainText("Auto-adjustment completed. No barcodes were detected with any parameter combination.")
            print("Auto-adjustment completed - no combinations left")
            return
            
        if self.detection_worker.isRunning():
            print("Detection worker still running, waiting...")
            return  # Wait for current detection to finish
            
        # Get current parameter combination
        params = self.auto_adjustment_params[self.auto_adjustment_index]
        
        # Create descriptive status message
        loc_modes = [mode['Mode'].replace('LM_', '') for mode in params['localization_modes']]
        status_msg = f"Testing combination {self.auto_adjustment_index + 1}/{len(self.auto_adjustment_params)}: {', '.join(loc_modes)}"
        self.status_bar.showMessage(status_msg)
        print(f"Testing parameters: {params}")
        
        # Apply parameter combination to settings
        self.apply_auto_adjustment_params(params)
        
        # Test with current parameters
        print("Calling test_parameters()...")
        self.test_parameters()
        
        self.auto_adjustment_index += 1
        
    def apply_auto_adjustment_params(self, params):
        """Apply parameter combination to current settings"""
        print(f"Applying auto-adjustment params: {params}")
        try:
            # Update expected barcode count in all tasks
            if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
                for task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                    task['ExpectedBarcodesCount'] = params['expected_count']
            
            # Update localization modes in all applicable sections
            if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
                for task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                    if 'SectionArray' in task:
                        for section in task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_LOCALIZATION':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_LOCALIZE_CANDIDATE_BARCODES':
                                        # Update localization modes with confidence thresholds
                                        stage['LocalizationModes'] = params['localization_modes']
            
            # Update block sizes in image parameters
            if 'ImageParameterOptions' in self.current_settings:
                for param in self.current_settings['ImageParameterOptions']:
                    if 'ApplicableStages' in param:
                        for stage in param['ApplicableStages']:
                            if 'BinarizationModes' in stage:
                                for bin_mode in stage['BinarizationModes']:
                                    if 'Mode' in bin_mode and bin_mode['Mode'] == 'BM_LOCAL_BLOCK':
                                        bin_mode.update(params['block_size'])
            
            # Update settings and refresh display
            self.update_settings()
            self.update_parameters_display()
            
            # Show current parameter combination in the result text
            param_info = f"Testing parameters (Combination {self.auto_adjustment_index + 1}/{len(self.auto_adjustment_params)}):\n\n"
            param_info += f"🔍 Expected Count: {params['expected_count']} barcode(s)\n"
            param_info += f"📍 Localization Modes: {[mode['Mode'].replace('LM_', '') for mode in params['localization_modes']]}\n"
            param_info += f"🎯 Confidence Threshold: {params['confidence']}%\n"
            
            if params['block_size']['BlockSizeX'] == 0:
                param_info += f"📦 Block Size: Auto\n"
            else:
                param_info += f"📦 Block Size: {params['block_size']['BlockSizeX']}×{params['block_size']['BlockSizeY']}\n"
            
            param_info += f"\n⏱️ Running detection...\n"
            
            self.result_text.setPlainText(param_info)
                                        
        except Exception as e:
            print(f"Error applying auto-adjustment parameters: {e}")
            error_msg = f"Error in parameter combination {self.auto_adjustment_index + 1}: {str(e)}\n"
            error_msg += "Skipping to next combination..."
            self.result_text.setPlainText(error_msg)
            
    def reset_parameters(self):
        """Reset parameters to default values"""
        self.current_settings = copy.deepcopy(self.default_settings)
        
        # Update all UI controls to default values
        for control_key, (control, prop_type, default_value) in self.ui_controls.items():
            try:
                if prop_type == 'checked':
                    control.setChecked(default_value)
                elif prop_type == 'text':
                    control.setCurrentText(default_value)
                elif prop_type == 'value':
                    control.setValue(default_value)
            except Exception as e:
                print(f"Failed to reset control {control_key}: {e}")
        
        # Clear results and overlay
        self.result_text.setPlainText("")
        if hasattr(self, 'image_panel'):
            self.image_panel.set_barcode_results([])
        
        self.status_bar.showMessage("Parameters reset to default")
        
    def export_parameters(self):
        """Export current working parameters to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Parameters", "barcode_parameters.json",
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.current_settings, f, indent=2)
                QMessageBox.information(self, "Success", f"Parameters exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export parameters:\n{str(e)}")
                
    def load_settings(self):
        """Load parameter settings from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.current_settings = json.load(f)
                # TODO: Update parameter controls
                self.status_bar.showMessage(f"Settings loaded from {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load settings:\n{str(e)}")
                
    def save_settings(self):
        """Save current parameter settings to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Settings", "settings.json", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.current_settings, f, indent=2)
                self.status_bar.showMessage(f"Settings saved to {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save settings:\n{str(e)}")
                
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About",
            "Dynamsoft Barcode Reader Parameter Adjustment Tool\n\n"
            "This tool helps developers find appropriate parameters "
            "for barcode detection by providing a visual interface "
            "for parameter adjustment and real-time testing.\n\n"
            "Features:\n"
            "• Visual parameter adjustment\n"
            "• Real-time barcode detection\n"
            "• Auto parameter adjustment\n"
            "• Parameter export/import\n"
            "• Drag-and-drop image loading"
        )

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Barcode Parameter Tool")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Dynamsoft")
    
    # Create and show main window
    window = ParameterAdjustmentTool()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()