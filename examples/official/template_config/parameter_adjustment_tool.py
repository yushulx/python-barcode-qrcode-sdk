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
    QTreeWidgetItem, QHeaderView, QListWidget, QDialog, QDialogButtonBox
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

class CustomIterationsDialog(QDialog):
    """Dialog for setting custom auto-adjustment iterations"""
    
    def __init__(self, current_value=40, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Auto-Adjustment Iterations")
        self.setModal(True)
        self.setFixedSize(350, 180)
        
        layout = QVBoxLayout()
        
        # Description
        description = QLabel(
            "Specify the number of parameter combinations to test during auto-adjustment.\n"
            "Higher values provide more thorough testing but take longer to complete."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Input section
        input_layout = QFormLayout()
        
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 500)
        self.iterations_spin.setValue(current_value)
        self.iterations_spin.setSuffix(" combinations")
        self.iterations_spin.setMinimumWidth(150)
        
        input_layout.addRow("Iterations:", self.iterations_spin)
        layout.addLayout(input_layout)
        
        # Recommendation label
        self.recommendation_label = QLabel()
        self.update_recommendation()
        self.recommendation_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.recommendation_label)
        
        # Connect value change to update recommendation
        self.iterations_spin.valueChanged.connect(self.update_recommendation)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def update_recommendation(self):
        """Update the recommendation text based on selected value"""
        value = self.iterations_spin.value()
        if value <= 20:
            text = "Quick scan - basic parameter testing"
        elif value <= 40:
            text = "Standard scan - balanced thoroughness"
        elif value <= 60:
            text = "Comprehensive scan - detailed testing"
        elif value <= 100:
            text = "Deep scan - extensive parameter coverage"
        else:
            text = "Ultra-deep scan - maximum thoroughness (slow)"
        
        self.recommendation_label.setText(text)
    
    def get_iterations(self):
        """Get the selected number of iterations"""
        return self.iterations_spin.value()

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
        
        # Auto adjustment mode selection
        self.auto_adjust_mode = QComboBox()
        self.auto_adjust_mode.addItems(["Quick (20 tests)", "Standard (40 tests)", "Comprehensive (60 tests)", "Deep Scan (100 tests)", "Custom..."])
        self.auto_adjust_mode.setCurrentIndex(1)  # Default to Standard
        self.auto_adjust_mode.setToolTip("Select auto adjustment thoroughness")
        self.auto_adjust_mode.setMinimumWidth(140)
        button_layout.addWidget(self.auto_adjust_mode)
        
        # Store custom iterations value (no UI widget needed now)
        self.custom_iterations_value = 40
        
        # Connect mode change to handle custom selection
        self.auto_adjust_mode.currentTextChanged.connect(self.on_auto_adjust_mode_changed)
        
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
        self.create_global_parameter_tab()
        self.create_target_roi_tab()
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
                
                # AllModuleDeviation
                if 'AllModuleDeviation' in spec:
                    deviation_spin = QSpinBox()
                    deviation_spin.setRange(0, 100)
                    deviation_spin.setValue(spec['AllModuleDeviation'])
                    deviation_spin.setMinimumWidth(120)
                    deviation_spin.valueChanged.connect(partial(self.on_all_module_deviation_changed, spec))
                    advanced_layout.addRow("All Module Deviation:", deviation_spin)
                    
                    control_key = f"all_module_deviation_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (deviation_spin, 'value', spec['AllModuleDeviation'])
                
                # AustralianPostEncodingTable
                if 'AustralianPostEncodingTable' in spec:
                    aus_post_combo = QComboBox()
                    aus_post_combo.addItems(['C', 'N'])
                    aus_post_combo.setCurrentText(spec['AustralianPostEncodingTable'])
                    aus_post_combo.setMinimumWidth(120)
                    aus_post_combo.currentTextChanged.connect(partial(self.on_aus_post_encoding_changed, spec))
                    advanced_layout.addRow("Australian Post Encoding:", aus_post_combo)
                    
                    control_key = f"aus_post_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (aus_post_combo, 'text', spec['AustralianPostEncodingTable'])
                
                # BarcodeTextRegExPattern
                if 'BarcodeTextRegExPattern' in spec:
                    regex_edit = QLineEdit()
                    regex_edit.setText(spec['BarcodeTextRegExPattern'])
                    regex_edit.setMinimumWidth(120)
                    regex_edit.textChanged.connect(partial(self.on_barcode_regex_changed, spec))
                    advanced_layout.addRow("Barcode Text Regex Pattern:", regex_edit)
                    
                    control_key = f"regex_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (regex_edit, 'text', spec['BarcodeTextRegExPattern'])
                
                # BarcodeZoneMinDistanceToImageBorders
                if 'BarcodeZoneMinDistanceToImageBorders' in spec:
                    border_distance_spin = QSpinBox()
                    border_distance_spin.setRange(0, 100)
                    border_distance_spin.setValue(spec['BarcodeZoneMinDistanceToImageBorders'])
                    border_distance_spin.setMinimumWidth(120)
                    border_distance_spin.valueChanged.connect(partial(self.on_border_distance_changed, spec))
                    advanced_layout.addRow("Min Distance to Borders:", border_distance_spin)
                    
                    control_key = f"border_dist_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (border_distance_spin, 'value', spec['BarcodeZoneMinDistanceToImageBorders'])
                
                # Code128Subset
                if 'Code128Subset' in spec:
                    code128_edit = QLineEdit()
                    code128_edit.setText(spec['Code128Subset'])
                    code128_edit.setMinimumWidth(120)
                    code128_edit.textChanged.connect(partial(self.on_code128_subset_changed, spec))
                    advanced_layout.addRow("Code 128 Subset:", code128_edit)
                    
                    control_key = f"code128_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (code128_edit, 'text', spec['Code128Subset'])
                
                # DataMatrixModuleIsotropic
                if 'DataMatrixModuleIsotropic' in spec:
                    dm_isotropic_checkbox = QCheckBox("DataMatrix Module Isotropic")
                    dm_isotropic_checkbox.setChecked(bool(spec['DataMatrixModuleIsotropic']))
                    dm_isotropic_checkbox.stateChanged.connect(partial(self.on_dm_isotropic_changed, spec))
                    advanced_layout.addRow(dm_isotropic_checkbox)
                    
                    control_key = f"dm_isotropic_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (dm_isotropic_checkbox, 'checked', bool(spec['DataMatrixModuleIsotropic']))
                
                # EnableAddOnCode
                if 'EnableAddOnCode' in spec:
                    addon_checkbox = QCheckBox("Enable Add-On Code")
                    addon_checkbox.setChecked(bool(spec['EnableAddOnCode']))
                    addon_checkbox.stateChanged.connect(partial(self.on_addon_code_changed, spec))
                    advanced_layout.addRow(addon_checkbox)
                    
                    control_key = f"addon_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (addon_checkbox, 'checked', bool(spec['EnableAddOnCode']))
                
                # EnableDataMatrixECC000-140
                if 'EnableDataMatrixECC000-140' in spec:
                    ecc_checkbox = QCheckBox("Enable DataMatrix ECC000-140")
                    ecc_checkbox.setChecked(bool(spec['EnableDataMatrixECC000-140']))
                    ecc_checkbox.stateChanged.connect(partial(self.on_dm_ecc_changed, spec))
                    advanced_layout.addRow(ecc_checkbox)
                    
                    control_key = f"dm_ecc_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (ecc_checkbox, 'checked', bool(spec['EnableDataMatrixECC000-140']))
                
                # EnableQRCodeModel1
                if 'EnableQRCodeModel1' in spec:
                    qr_model1_checkbox = QCheckBox("Enable QR Code Model 1")
                    qr_model1_checkbox.setChecked(bool(spec['EnableQRCodeModel1']))
                    qr_model1_checkbox.stateChanged.connect(partial(self.on_qr_model1_changed, spec))
                    advanced_layout.addRow(qr_model1_checkbox)
                    
                    control_key = f"qr_model1_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (qr_model1_checkbox, 'checked', bool(spec['EnableQRCodeModel1']))
                
                # HeadModuleRatio
                if 'HeadModuleRatio' in spec:
                    head_ratio_edit = QLineEdit()
                    head_ratio_edit.setText(spec['HeadModuleRatio'])
                    head_ratio_edit.setMinimumWidth(120)
                    head_ratio_edit.textChanged.connect(partial(self.on_head_ratio_changed, spec))
                    advanced_layout.addRow("Head Module Ratio:", head_ratio_edit)
                    
                    control_key = f"head_ratio_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (head_ratio_edit, 'text', spec['HeadModuleRatio'])
                
                # TailModuleRatio
                if 'TailModuleRatio' in spec:
                    tail_ratio_edit = QLineEdit()
                    tail_ratio_edit.setText(spec['TailModuleRatio'])
                    tail_ratio_edit.setMinimumWidth(120)
                    tail_ratio_edit.textChanged.connect(partial(self.on_tail_ratio_changed, spec))
                    advanced_layout.addRow("Tail Module Ratio:", tail_ratio_edit)
                    
                    control_key = f"tail_ratio_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (tail_ratio_edit, 'text', spec['TailModuleRatio'])
                
                # IncludeImpliedAI01
                if 'IncludeImpliedAI01' in spec:
                    ai01_checkbox = QCheckBox("Include Implied AI 01")
                    ai01_checkbox.setChecked(bool(spec['IncludeImpliedAI01']))
                    ai01_checkbox.stateChanged.connect(partial(self.on_ai01_changed, spec))
                    advanced_layout.addRow(ai01_checkbox)
                    
                    control_key = f"ai01_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (ai01_checkbox, 'checked', bool(spec['IncludeImpliedAI01']))
                
                # IncludeTrailingCheckDigit
                if 'IncludeTrailingCheckDigit' in spec:
                    check_digit_checkbox = QCheckBox("Include Trailing Check Digit")
                    check_digit_checkbox.setChecked(bool(spec['IncludeTrailingCheckDigit']))
                    check_digit_checkbox.stateChanged.connect(partial(self.on_check_digit_changed, spec))
                    advanced_layout.addRow(check_digit_checkbox)
                    
                    control_key = f"check_digit_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (check_digit_checkbox, 'checked', bool(spec['IncludeTrailingCheckDigit']))
                
                # MSICodeCheckDigitCalculation
                if 'MSICodeCheckDigitCalculation' in spec:
                    msi_calc_combo = QComboBox()
                    msi_calc_combo.addItems(['MSICCDC_MOD_10', 'MSICCDC_MOD_11', 'MSICCDC_MOD_1010', 'MSICCDC_MOD_1110', 'MSICCDC_MOD_11_IBM', 'MSICCDC_MOD_1011_IBM', 'MSICCDC_SKIP', 'MSICCDC_NO_CALCULATION'])
                    msi_calc_combo.setCurrentText(spec['MSICodeCheckDigitCalculation'])
                    msi_calc_combo.setMinimumWidth(120)
                    msi_calc_combo.currentTextChanged.connect(partial(self.on_msi_calc_changed, spec))
                    advanced_layout.addRow("MSI Check Digit Calculation:", msi_calc_combo)
                    
                    control_key = f"msi_calc_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (msi_calc_combo, 'text', spec['MSICodeCheckDigitCalculation'])
                
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
                
                # MinRatioOfBarcodeZoneWidthToHeight
                if 'MinRatioOfBarcodeZoneWidthToHeight' in spec:
                    ratio_spin = QDoubleSpinBox()
                    ratio_spin.setRange(0.0, 10.0)
                    ratio_spin.setDecimals(2)
                    ratio_spin.setSingleStep(0.1)
                    ratio_spin.setValue(spec['MinRatioOfBarcodeZoneWidthToHeight'])
                    ratio_spin.setMinimumWidth(120)
                    ratio_spin.valueChanged.connect(partial(self.on_width_height_ratio_changed, spec))
                    advanced_layout.addRow("Min Width/Height Ratio:", ratio_spin)
                    
                    control_key = f"wh_ratio_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (ratio_spin, 'value', spec['MinRatioOfBarcodeZoneWidthToHeight'])
                
                # RequireStartStopChars
                if 'RequireStartStopChars' in spec:
                    startstop_checkbox = QCheckBox("Require Start/Stop Characters")
                    startstop_checkbox.setChecked(bool(spec['RequireStartStopChars']))
                    startstop_checkbox.stateChanged.connect(partial(self.on_startstop_changed, spec))
                    advanced_layout.addRow(startstop_checkbox)
                    
                    control_key = f"startstop_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (startstop_checkbox, 'checked', bool(spec['RequireStartStopChars']))
                
                # ReturnPartialBarcodeValue
                if 'ReturnPartialBarcodeValue' in spec:
                    partial_checkbox = QCheckBox("Return Partial Barcode Value")
                    partial_checkbox.setChecked(bool(spec['ReturnPartialBarcodeValue']))
                    partial_checkbox.stateChanged.connect(partial(self.on_partial_value_changed, spec))
                    advanced_layout.addRow(partial_checkbox)
                    
                    control_key = f"partial_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (partial_checkbox, 'checked', bool(spec['ReturnPartialBarcodeValue']))
                
                # StandardFormat
                if 'StandardFormat' in spec:
                    std_format_edit = QLineEdit()
                    std_format_edit.setText(spec['StandardFormat'])
                    std_format_edit.setMinimumWidth(120)
                    std_format_edit.textChanged.connect(partial(self.on_std_format_changed, spec))
                    advanced_layout.addRow("Standard Format:", std_format_edit)
                    
                    control_key = f"std_format_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (std_format_edit, 'text', spec['StandardFormat'])
                
                # VerifyCheckDigit
                if 'VerifyCheckDigit' in spec:
                    verify_checkbox = QCheckBox("Verify Check Digit")
                    verify_checkbox.setChecked(bool(spec['VerifyCheckDigit']))
                    verify_checkbox.stateChanged.connect(partial(self.on_verify_digit_changed, spec))
                    advanced_layout.addRow(verify_checkbox)
                    
                    control_key = f"verify_{spec.get('Name', f'spec_{i}')}"
                    self.ui_controls[control_key] = (verify_checkbox, 'checked', bool(spec['VerifyCheckDigit']))
                
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
                
                # DPM Code Reading Modes
                if 'DPMCodeReadingModes' in task:
                    dpm_group = QGroupBox("DPM Code Reading Modes")
                    dpm_layout = QVBoxLayout()
                    
                    for j, dpm_mode in enumerate(task['DPMCodeReadingModes']):
                        dpm_widget = QWidget()
                        dpm_widget_layout = QHBoxLayout()
                        dpm_widget_layout.setContentsMargins(0, 0, 0, 0)
                        
                        # Barcode Format
                        format_label = QLabel("Barcode Format:")
                        format_combo = QComboBox()
                        format_combo.addItems(['BF_DATAMATRIX', 'BF_QR_CODE', 'BF_PDF417', 'BF_AZTEC', 'BF_ALL'])
                        format_combo.setCurrentText(dpm_mode.get('BarcodeFormat', 'BF_DATAMATRIX'))
                        format_combo.setMinimumWidth(120)
                        format_combo.currentTextChanged.connect(partial(self.on_dpm_format_changed, task, j))
                        
                        # Mode
                        mode_label = QLabel("Mode:")
                        mode_combo = QComboBox()
                        mode_combo.addItems(['DPMCRM_SKIP', 'DPMCRM_GENERAL', 'DPMCRM_ADVANCED'])
                        mode_combo.setCurrentText(dpm_mode.get('Mode', 'DPMCRM_SKIP'))
                        mode_combo.setMinimumWidth(120)
                        mode_combo.currentTextChanged.connect(partial(self.on_dpm_mode_changed, task, j))
                        
                        dpm_widget_layout.addWidget(format_label)
                        dpm_widget_layout.addWidget(format_combo)
                        dpm_widget_layout.addWidget(mode_label)
                        dpm_widget_layout.addWidget(mode_combo)
                        dpm_widget_layout.addStretch()
                        
                        dpm_widget.setLayout(dpm_widget_layout)
                        dpm_layout.addWidget(dpm_widget)
                        
                        # Store references for resetting
                        control_key = f"dpm_format_{task.get('Name', f'task_{i}')}_{j}"
                        self.ui_controls[control_key] = (format_combo, 'text', dpm_mode.get('BarcodeFormat', 'BF_DATAMATRIX'))
                        
                        control_key = f"dpm_mode_{task.get('Name', f'task_{i}')}_{j}"
                        self.ui_controls[control_key] = (mode_combo, 'text', dpm_mode.get('Mode', 'DPMCRM_SKIP'))
                    
                    dpm_group.setLayout(dpm_layout)
                    group_layout.addWidget(dpm_group)
                
                # Text Result Order Modes
                if 'TextResultOrderModes' in task:
                    order_group = QGroupBox("Text Result Order Modes")
                    order_layout = QVBoxLayout()
                    
                    for j, order_mode in enumerate(task['TextResultOrderModes']):
                        order_widget = QWidget()
                        order_widget_layout = QHBoxLayout()
                        order_widget_layout.setContentsMargins(0, 0, 0, 0)
                        
                        order_label = QLabel(f"Order {j+1}:")
                        order_combo = QComboBox()
                        order_combo.addItems(['TROM_CONFIDENCE', 'TROM_POSITION', 'TROM_FORMAT', 'TROM_SKIP'])
                        order_combo.setCurrentText(order_mode.get('Mode', 'TROM_CONFIDENCE'))
                        order_combo.setMinimumWidth(120)
                        order_combo.currentTextChanged.connect(partial(self.on_text_order_changed, task, j))
                        
                        order_widget_layout.addWidget(order_label)
                        order_widget_layout.addWidget(order_combo)
                        order_widget_layout.addStretch()
                        
                        order_widget.setLayout(order_widget_layout)
                        order_layout.addWidget(order_widget)
                        
                        # Store reference for resetting
                        control_key = f"text_order_{task.get('Name', f'task_{i}')}_{j}"
                        self.ui_controls[control_key] = (order_combo, 'text', order_mode.get('Mode', 'TROM_CONFIDENCE'))
                    
                    order_group.setLayout(order_layout)
                    group_layout.addWidget(order_group)
                
                # Region Predetection Modes (from sections)
                if 'SectionArray' in task:
                    for section in task['SectionArray']:
                        if section.get('Section') == 'ST_REGION_PREDETECTION':
                            for stage in section.get('StageArray', []):
                                if 'RegionPredetectionModes' in stage:
                                    region_group = QGroupBox("Region Predetection Modes")
                                    region_layout = QVBoxLayout()
                                    
                                    for j, mode in enumerate(stage['RegionPredetectionModes']):
                                        mode_widget = QWidget()
                                        mode_layout = QFormLayout()
                                        mode_layout.setContentsMargins(0, 0, 0, 0)
                                        
                                        # Mode
                                        mode_combo = QComboBox()
                                        mode_combo.addItems(['RPM_GENERAL', 'RPM_GENERAL_RGB_CONTRAST', 'RPM_GENERAL_GRAY_CONTRAST', 'RPM_SKIP'])
                                        mode_combo.setCurrentText(mode.get('Mode', 'RPM_GENERAL'))
                                        mode_combo.setMinimumWidth(120)
                                        mode_combo.currentTextChanged.connect(partial(self.on_region_mode_changed, task, j))
                                        mode_layout.addRow("Mode:", mode_combo)
                                        
                                        # Sensitivity
                                        if 'Sensitivity' in mode:
                                            sensitivity_spin = QSpinBox()
                                            sensitivity_spin.setRange(1, 9)
                                            sensitivity_spin.setValue(mode['Sensitivity'])
                                            sensitivity_spin.setMinimumWidth(120)
                                            sensitivity_spin.valueChanged.connect(partial(self.on_region_sensitivity_changed, task, j))
                                            mode_layout.addRow("Sensitivity:", sensitivity_spin)
                                            
                                            control_key = f"region_sensitivity_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (sensitivity_spin, 'value', mode['Sensitivity'])
                                        
                                        # MinImageDimension
                                        if 'MinImageDimension' in mode:
                                            min_dim_spin = QSpinBox()
                                            min_dim_spin.setRange(1, 1000000)
                                            min_dim_spin.setValue(mode['MinImageDimension'])
                                            min_dim_spin.setMinimumWidth(120)
                                            min_dim_spin.valueChanged.connect(partial(self.on_region_min_dim_changed, task, j))
                                            mode_layout.addRow("Min Image Dimension:", min_dim_spin)
                                            
                                            control_key = f"region_min_dim_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (min_dim_spin, 'value', mode['MinImageDimension'])
                                        
                                        # SpatialIndexBlockSize
                                        if 'SpatialIndexBlockSize' in mode:
                                            block_size_spin = QSpinBox()
                                            block_size_spin.setRange(1, 32)
                                            block_size_spin.setValue(mode['SpatialIndexBlockSize'])
                                            block_size_spin.setMinimumWidth(120)
                                            block_size_spin.valueChanged.connect(partial(self.on_region_block_size_changed, task, j))
                                            mode_layout.addRow("Spatial Index Block Size:", block_size_spin)
                                            
                                            control_key = f"region_block_size_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (block_size_spin, 'value', mode['SpatialIndexBlockSize'])
                                        
                                        # FindAccurateBoundary
                                        if 'FindAccurateBoundary' in mode:
                                            accurate_checkbox = QCheckBox("Find Accurate Boundary")
                                            accurate_checkbox.setChecked(bool(mode['FindAccurateBoundary']))
                                            accurate_checkbox.stateChanged.connect(partial(self.on_region_accurate_changed, task, j))
                                            mode_layout.addRow(accurate_checkbox)
                                            
                                            control_key = f"region_accurate_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (accurate_checkbox, 'checked', bool(mode['FindAccurateBoundary']))
                                        
                                        # MeasuredByPercentage
                                        if 'MeasuredByPercentage' in mode:
                                            percentage_checkbox = QCheckBox("Measured By Percentage")
                                            percentage_checkbox.setChecked(bool(mode['MeasuredByPercentage']))
                                            percentage_checkbox.stateChanged.connect(partial(self.on_region_percentage_changed, task, j))
                                            mode_layout.addRow(percentage_checkbox)
                                            
                                            control_key = f"region_percentage_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (percentage_checkbox, 'checked', bool(mode['MeasuredByPercentage']))
                                        
                                        # DetectionModelName
                                        if 'DetectionModelName' in mode:
                                            model_edit = QLineEdit()
                                            model_edit.setText(mode['DetectionModelName'])
                                            model_edit.setMinimumWidth(120)
                                            model_edit.textChanged.connect(partial(self.on_region_model_changed, task, j))
                                            mode_layout.addRow("Detection Model Name:", model_edit)
                                            
                                            control_key = f"region_model_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (model_edit, 'text', mode['DetectionModelName'])
                                        
                                        mode_widget.setLayout(mode_layout)
                                        region_layout.addWidget(mode_widget)
                                        
                                        # Store main mode control
                                        control_key = f"region_mode_{task.get('Name', f'task_{i}')}_{j}"
                                        self.ui_controls[control_key] = (mode_combo, 'text', mode.get('Mode', 'RPM_GENERAL'))
                                    
                                    region_group.setLayout(region_layout)
                                    group_layout.addWidget(region_group)
                                    break
                
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
                                        mode_main_layout = QVBoxLayout()
                                        mode_main_layout.setContentsMargins(5, 5, 5, 5)
                                        
                                        # Mode header with checkbox
                                        header_layout = QHBoxLayout()
                                        checkbox = QCheckBox(mode_text.replace('LM_', ''))
                                        checkbox.setChecked(True)
                                        checkbox.stateChanged.connect(
                                            partial(self.on_localization_mode_changed, task, mode_text)
                                        )
                                        header_layout.addWidget(checkbox)
                                        loc_checkboxes.append(checkbox)
                                        header_layout.addStretch()
                                        mode_main_layout.addLayout(header_layout)
                                        
                                        # Parameters grid layout
                                        params_layout = QGridLayout()
                                        row = 0
                                        
                                        # Confidence Threshold
                                        if 'ConfidenceThreshold' in mode:
                                            confidence_label = QLabel("Confidence:")
                                            confidence_spin = QSpinBox()
                                            confidence_spin.setRange(0, 100)
                                            confidence_spin.setValue(mode['ConfidenceThreshold'])
                                            confidence_spin.setMinimumWidth(80)
                                            confidence_spin.valueChanged.connect(
                                                partial(self.on_localization_confidence_changed, task, j, mode_text)
                                            )
                                            params_layout.addWidget(confidence_label, row, 0)
                                            params_layout.addWidget(confidence_spin, row, 1)
                                            
                                            control_key = f"loc_conf_{task.get('Name', f'task_{i}')}_{j}_{mode_text}"
                                            self.ui_controls[control_key] = (confidence_spin, 'value', mode['ConfidenceThreshold'])
                                            row += 1
                                        
                                        # IsOneDStacked
                                        if 'IsOneDStacked' in mode:
                                            stacked_checkbox = QCheckBox("Is One-D Stacked")
                                            stacked_checkbox.setChecked(bool(mode['IsOneDStacked']))
                                            stacked_checkbox.stateChanged.connect(
                                                partial(self.on_localization_stacked_changed, task, j, mode_text)
                                            )
                                            params_layout.addWidget(stacked_checkbox, row, 0, 1, 2)
                                            
                                            control_key = f"loc_stacked_{task.get('Name', f'task_{i}')}_{j}_{mode_text}"
                                            self.ui_controls[control_key] = (stacked_checkbox, 'checked', bool(mode['IsOneDStacked']))
                                            row += 1
                                        
                                        # ModuleSize
                                        if 'ModuleSize' in mode:
                                            module_label = QLabel("Module Size:")
                                            module_spin = QSpinBox()
                                            module_spin.setRange(0, 100)
                                            module_spin.setValue(mode['ModuleSize'])
                                            module_spin.setMinimumWidth(80)
                                            module_spin.valueChanged.connect(
                                                partial(self.on_localization_module_size_changed, task, j, mode_text)
                                            )
                                            params_layout.addWidget(module_label, row, 0)
                                            params_layout.addWidget(module_spin, row, 1)
                                            
                                            control_key = f"loc_module_size_{task.get('Name', f'task_{i}')}_{j}_{mode_text}"
                                            self.ui_controls[control_key] = (module_spin, 'value', mode['ModuleSize'])
                                            row += 1
                                        
                                        # ScanDirection
                                        if 'ScanDirection' in mode:
                                            direction_label = QLabel("Scan Direction:")
                                            direction_spin = QSpinBox()
                                            direction_spin.setRange(0, 360)
                                            direction_spin.setValue(mode['ScanDirection'])
                                            direction_spin.setMinimumWidth(80)
                                            direction_spin.valueChanged.connect(
                                                partial(self.on_localization_scan_direction_changed, task, j, mode_text)
                                            )
                                            params_layout.addWidget(direction_label, row, 0)
                                            params_layout.addWidget(direction_spin, row, 1)
                                            
                                            control_key = f"loc_direction_{task.get('Name', f'task_{i}')}_{j}_{mode_text}"
                                            self.ui_controls[control_key] = (direction_spin, 'value', mode['ScanDirection'])
                                            row += 1
                                        
                                        # ScanStride
                                        if 'ScanStride' in mode:
                                            stride_label = QLabel("Scan Stride:")
                                            stride_spin = QSpinBox()
                                            stride_spin.setRange(0, 50)
                                            stride_spin.setValue(mode['ScanStride'])
                                            stride_spin.setMinimumWidth(80)
                                            stride_spin.valueChanged.connect(
                                                partial(self.on_localization_scan_stride_changed, task, j, mode_text)
                                            )
                                            params_layout.addWidget(stride_label, row, 0)
                                            params_layout.addWidget(stride_spin, row, 1)
                                            
                                            control_key = f"loc_stride_{task.get('Name', f'task_{i}')}_{j}_{mode_text}"
                                            self.ui_controls[control_key] = (stride_spin, 'value', mode['ScanStride'])
                                            row += 1
                                        
                                        if row > 0:
                                            mode_main_layout.addLayout(params_layout)
                                        
                                        mode_widget.setLayout(mode_main_layout)
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
                
                # Deformation Resisting Modes (from sections)
                if 'SectionArray' in task:
                    for section in task['SectionArray']:
                        if section.get('Section') == 'ST_BARCODE_DECODING':
                            for stage in section.get('StageArray', []):
                                if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                    deform_group = QGroupBox("Deformation Resisting Modes")
                                    deform_layout = QVBoxLayout()
                                    
                                    for j, deform_mode in enumerate(stage['DeformationResistingModes']):
                                        deform_widget = QWidget()
                                        deform_widget_layout = QFormLayout()
                                        
                                        # Mode
                                        mode_combo = QComboBox()
                                        mode_combo.addItems(['DRM_SKIP', 'DRM_AUTO', 'DRM_GENERAL', 'DRM_DEWRAPPING'])
                                        mode_combo.setCurrentText(deform_mode.get('Mode', 'DRM_SKIP'))
                                        mode_combo.setMinimumWidth(120)
                                        mode_combo.currentTextChanged.connect(partial(self.on_deform_mode_changed, task, j))
                                        deform_widget_layout.addRow("Mode:", mode_combo)
                                        
                                        # Level
                                        if 'Level' in deform_mode:
                                            level_spin = QSpinBox()
                                            level_spin.setRange(1, 9)
                                            level_spin.setValue(deform_mode['Level'])
                                            level_spin.setMinimumWidth(120)
                                            level_spin.valueChanged.connect(partial(self.on_deform_level_changed, task, j))
                                            deform_widget_layout.addRow("Level:", level_spin)
                                            
                                            control_key = f"deform_level_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (level_spin, 'value', deform_mode['Level'])
                                        
                                        # Binarization Mode (nested)
                                        if 'BinarizationMode' in deform_mode:
                                            bin_mode = deform_mode['BinarizationMode']
                                            bin_group = QGroupBox("Binarization Mode")
                                            bin_layout = QFormLayout()
                                            
                                            # Mode
                                            bin_mode_combo = QComboBox()
                                            bin_mode_combo.addItems(['BM_LOCAL_BLOCK', 'BM_THRESHOLD', 'BM_AUTO', 'BM_SKIP'])
                                            bin_mode_combo.setCurrentText(bin_mode.get('Mode', 'BM_LOCAL_BLOCK'))
                                            bin_mode_combo.setMinimumWidth(120)
                                            bin_mode_combo.currentTextChanged.connect(partial(self.on_deform_bin_mode_changed, task, j))
                                            bin_layout.addRow("Bin Mode:", bin_mode_combo)
                                            
                                            # BinarizationThreshold
                                            if 'BinarizationThreshold' in bin_mode:
                                                threshold_spin = QSpinBox()
                                                threshold_spin.setRange(-1, 255)
                                                threshold_spin.setValue(bin_mode['BinarizationThreshold'])
                                                threshold_spin.setMinimumWidth(120)
                                                threshold_spin.valueChanged.connect(partial(self.on_deform_bin_threshold_changed, task, j))
                                                bin_layout.addRow("Binarization Threshold:", threshold_spin)
                                                
                                                control_key = f"deform_bin_threshold_{task.get('Name', f'task_{i}')}_{j}"
                                                self.ui_controls[control_key] = (threshold_spin, 'value', bin_mode['BinarizationThreshold'])
                                            
                                            # BlockSizeX
                                            if 'BlockSizeX' in bin_mode:
                                                block_x_spin = QSpinBox()
                                                block_x_spin.setRange(0, 1000)
                                                block_x_spin.setValue(bin_mode['BlockSizeX'])
                                                block_x_spin.setMinimumWidth(120)
                                                block_x_spin.valueChanged.connect(partial(self.on_deform_bin_block_x_changed, task, j))
                                                bin_layout.addRow("Block Size X:", block_x_spin)
                                                
                                                control_key = f"deform_bin_block_x_{task.get('Name', f'task_{i}')}_{j}"
                                                self.ui_controls[control_key] = (block_x_spin, 'value', bin_mode['BlockSizeX'])
                                            
                                            # BlockSizeY
                                            if 'BlockSizeY' in bin_mode:
                                                block_y_spin = QSpinBox()
                                                block_y_spin.setRange(0, 1000)
                                                block_y_spin.setValue(bin_mode['BlockSizeY'])
                                                block_y_spin.setMinimumWidth(120)
                                                block_y_spin.valueChanged.connect(partial(self.on_deform_bin_block_y_changed, task, j))
                                                bin_layout.addRow("Block Size Y:", block_y_spin)
                                                
                                                control_key = f"deform_bin_block_y_{task.get('Name', f'task_{i}')}_{j}"
                                                self.ui_controls[control_key] = (block_y_spin, 'value', bin_mode['BlockSizeY'])
                                            
                                            # EnableFillBinaryVacancy
                                            if 'EnableFillBinaryVacancy' in bin_mode:
                                                fill_checkbox = QCheckBox("Enable Fill Binary Vacancy")
                                                fill_checkbox.setChecked(bool(bin_mode['EnableFillBinaryVacancy']))
                                                fill_checkbox.stateChanged.connect(partial(self.on_deform_bin_fill_changed, task, j))
                                                bin_layout.addRow(fill_checkbox)
                                                
                                                control_key = f"deform_bin_fill_{task.get('Name', f'task_{i}')}_{j}"
                                                self.ui_controls[control_key] = (fill_checkbox, 'checked', bool(bin_mode['EnableFillBinaryVacancy']))
                                            
                                            # ThresholdCompensation
                                            if 'ThresholdCompensation' in bin_mode:
                                                compensation_spin = QSpinBox()
                                                compensation_spin.setRange(0, 255)
                                                compensation_spin.setValue(bin_mode['ThresholdCompensation'])
                                                compensation_spin.setMinimumWidth(120)
                                                compensation_spin.valueChanged.connect(partial(self.on_deform_bin_compensation_changed, task, j))
                                                bin_layout.addRow("Threshold Compensation:", compensation_spin)
                                                
                                                control_key = f"deform_bin_compensation_{task.get('Name', f'task_{i}')}_{j}"
                                                self.ui_controls[control_key] = (compensation_spin, 'value', bin_mode['ThresholdCompensation'])
                                            
                                            bin_group.setLayout(bin_layout)
                                            deform_widget_layout.addRow(bin_group)
                                            
                                            # Store bin mode combo control
                                            control_key = f"deform_bin_mode_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (bin_mode_combo, 'text', bin_mode.get('Mode', 'BM_LOCAL_BLOCK'))
                                        
                                        # Grayscale Enhancement Mode (nested)
                                        if 'GrayscaleEnhancementMode' in deform_mode:
                                            gray_mode = deform_mode['GrayscaleEnhancementMode']
                                            gray_group = QGroupBox("Grayscale Enhancement Mode")
                                            gray_layout = QFormLayout()
                                            
                                            # Mode
                                            gray_mode_combo = QComboBox()
                                            gray_mode_combo.addItems(['GEM_GENERAL', 'GEM_GRAY_EQUALIZE', 'GEM_GRAY_SMOOTH', 'GEM_GRAY_SHARPEN', 'GEM_SKIP'])
                                            gray_mode_combo.setCurrentText(gray_mode.get('Mode', 'GEM_GENERAL'))
                                            gray_mode_combo.setMinimumWidth(120)
                                            gray_mode_combo.currentTextChanged.connect(partial(self.on_deform_gray_mode_changed, task, j))
                                            gray_layout.addRow("Gray Mode:", gray_mode_combo)
                                            
                                            # Sensitivity
                                            if 'Sensitivity' in gray_mode:
                                                gray_sensitivity_spin = QSpinBox()
                                                gray_sensitivity_spin.setRange(1, 9)
                                                gray_sensitivity_spin.setValue(gray_mode['Sensitivity'])
                                                gray_sensitivity_spin.setMinimumWidth(120)
                                                gray_sensitivity_spin.valueChanged.connect(partial(self.on_deform_gray_sensitivity_changed, task, j))
                                                gray_layout.addRow("Sensitivity:", gray_sensitivity_spin)
                                                
                                                control_key = f"deform_gray_sensitivity_{task.get('Name', f'task_{i}')}_{j}"
                                                self.ui_controls[control_key] = (gray_sensitivity_spin, 'value', gray_mode['Sensitivity'])
                                            
                                            gray_group.setLayout(gray_layout)
                                            deform_widget_layout.addRow(gray_group)
                                            
                                            # Store gray mode combo control
                                            control_key = f"deform_gray_mode_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (gray_mode_combo, 'text', gray_mode.get('Mode', 'GEM_GENERAL'))
                                        
                                        deform_widget.setLayout(deform_widget_layout)
                                        deform_layout.addWidget(deform_widget)
                                        
                                        # Store main deform mode control
                                        control_key = f"deform_mode_{task.get('Name', f'task_{i}')}_{j}"
                                        self.ui_controls[control_key] = (mode_combo, 'text', deform_mode.get('Mode', 'DRM_SKIP'))
                                    
                                    deform_group.setLayout(deform_layout)
                                    group_layout.addWidget(deform_group)
                                    break
                
                # Barcode Complement Modes (from sections)
                if 'SectionArray' in task:
                    for section in task['SectionArray']:
                        if section.get('Section') == 'ST_BARCODE_DECODING':
                            for stage in section.get('StageArray', []):
                                if stage.get('Stage') == 'SST_COMPLEMENT_BARCODE' and 'BarcodeComplementModes' in stage:
                                    complement_group = QGroupBox("Barcode Complement Modes")
                                    complement_layout = QVBoxLayout()
                                    
                                    for j, complement_mode in enumerate(stage['BarcodeComplementModes']):
                                        complement_widget = QWidget()
                                        complement_widget_layout = QFormLayout()
                                        
                                        # Mode
                                        complement_mode_combo = QComboBox()
                                        complement_mode_combo.addItems(['BCM_SKIP', 'BCM_AUTO', 'BCM_GENERAL'])
                                        complement_mode_combo.setCurrentText(complement_mode.get('Mode', 'BCM_SKIP'))
                                        complement_mode_combo.setMinimumWidth(120)
                                        complement_mode_combo.currentTextChanged.connect(partial(self.on_complement_mode_changed, task, j))
                                        complement_widget_layout.addRow("Mode:", complement_mode_combo)
                                        
                                        complement_widget.setLayout(complement_widget_layout)
                                        complement_layout.addWidget(complement_widget)
                                        
                                        # Store control
                                        control_key = f"complement_mode_{task.get('Name', f'task_{i}')}_{j}"
                                        self.ui_controls[control_key] = (complement_mode_combo, 'text', complement_mode.get('Mode', 'BCM_SKIP'))
                                    
                                    complement_group.setLayout(complement_layout)
                                    group_layout.addWidget(complement_group)
                                    break
                
                # Barcode Scale Modes (from sections)
                if 'SectionArray' in task:
                    for section in task['SectionArray']:
                        if section.get('Section') == 'ST_BARCODE_DECODING':
                            for stage in section.get('StageArray', []):
                                if stage.get('Stage') == 'SST_SCALE_BARCODE_IMAGE' and 'BarcodeScaleModes' in stage:
                                    scale_group = QGroupBox("Barcode Scale Modes")
                                    scale_layout = QVBoxLayout()
                                    
                                    for j, scale_mode in enumerate(stage['BarcodeScaleModes']):
                                        scale_widget = QWidget()
                                        scale_widget_layout = QFormLayout()
                                        
                                        # Mode
                                        scale_mode_combo = QComboBox()
                                        scale_mode_combo.addItems(['BSM_SKIP', 'BSM_AUTO', 'BSM_MANUAL'])
                                        scale_mode_combo.setCurrentText(scale_mode.get('Mode', 'BSM_AUTO'))
                                        scale_mode_combo.setMinimumWidth(120)
                                        scale_mode_combo.currentTextChanged.connect(partial(self.on_scale_mode_changed, task, j))
                                        scale_widget_layout.addRow("Mode:", scale_mode_combo)
                                        
                                        # AcuteAngleWithXThreshold
                                        if 'AcuteAngleWithXThreshold' in scale_mode:
                                            angle_spin = QSpinBox()
                                            angle_spin.setRange(-1, 90)
                                            angle_spin.setValue(scale_mode['AcuteAngleWithXThreshold'])
                                            angle_spin.setMinimumWidth(120)
                                            angle_spin.valueChanged.connect(partial(self.on_scale_angle_changed, task, j))
                                            scale_widget_layout.addRow("Acute Angle Threshold:", angle_spin)
                                            
                                            control_key = f"scale_angle_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (angle_spin, 'value', scale_mode['AcuteAngleWithXThreshold'])
                                        
                                        # ModuleSizeThreshold
                                        if 'ModuleSizeThreshold' in scale_mode:
                                            module_threshold_spin = QSpinBox()
                                            module_threshold_spin.setRange(0, 100)
                                            module_threshold_spin.setValue(scale_mode['ModuleSizeThreshold'])
                                            module_threshold_spin.setMinimumWidth(120)
                                            module_threshold_spin.valueChanged.connect(partial(self.on_scale_module_threshold_changed, task, j))
                                            scale_widget_layout.addRow("Module Size Threshold:", module_threshold_spin)
                                            
                                            control_key = f"scale_module_threshold_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (module_threshold_spin, 'value', scale_mode['ModuleSizeThreshold'])
                                        
                                        # TargetModuleSize
                                        if 'TargetModuleSize' in scale_mode:
                                            target_size_spin = QSpinBox()
                                            target_size_spin.setRange(0, 100)
                                            target_size_spin.setValue(scale_mode['TargetModuleSize'])
                                            target_size_spin.setMinimumWidth(120)
                                            target_size_spin.valueChanged.connect(partial(self.on_scale_target_size_changed, task, j))
                                            scale_widget_layout.addRow("Target Module Size:", target_size_spin)
                                            
                                            control_key = f"scale_target_size_{task.get('Name', f'task_{i}')}_{j}"
                                            self.ui_controls[control_key] = (target_size_spin, 'value', scale_mode['TargetModuleSize'])
                                        
                                        scale_widget.setLayout(scale_widget_layout)
                                        scale_layout.addWidget(scale_widget)
                                        
                                        # Store main scale mode control
                                        control_key = f"scale_mode_{task.get('Name', f'task_{i}')}_{j}"
                                        self.ui_controls[control_key] = (scale_mode_combo, 'text', scale_mode.get('Mode', 'BSM_AUTO'))
                                    
                                    scale_group.setLayout(scale_layout)
                                    group_layout.addWidget(scale_group)
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
                        
                        # Colour Conversion Modes
                        if 'ColourConversionModes' in stage:
                            color_group = QGroupBox("Colour Conversion")
                            color_layout = QFormLayout()
                            
                            for color_mode in stage['ColourConversionModes']:
                                mode_text = color_mode.get('Mode', 'Unknown')
                                color_layout.addRow(QLabel(f"Mode: {mode_text.replace('CICM_', '')}"))
                                
                                # Red Channel Weight
                                if 'RedChannelWeight' in color_mode:
                                    red_spin = QSpinBox()
                                    red_spin.setRange(-1, 1000)
                                    red_spin.setValue(color_mode['RedChannelWeight'])
                                    red_spin.setMinimumWidth(120)
                                    red_spin.valueChanged.connect(
                                        partial(self.on_color_weight_changed, color_mode, 'RedChannelWeight')
                                    )
                                    color_layout.addRow("Red Weight:", red_spin)
                                    
                                    control_key = f"red_weight_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (red_spin, 'value', color_mode['RedChannelWeight'])
                                
                                # Green Channel Weight  
                                if 'GreenChannelWeight' in color_mode:
                                    green_spin = QSpinBox()
                                    green_spin.setRange(-1, 1000)
                                    green_spin.setValue(color_mode['GreenChannelWeight'])
                                    green_spin.setMinimumWidth(120)
                                    green_spin.valueChanged.connect(
                                        partial(self.on_color_weight_changed, color_mode, 'GreenChannelWeight')
                                    )
                                    color_layout.addRow("Green Weight:", green_spin)
                                    
                                    control_key = f"green_weight_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (green_spin, 'value', color_mode['GreenChannelWeight'])
                                
                                # Blue Channel Weight
                                if 'BlueChannelWeight' in color_mode:
                                    blue_spin = QSpinBox()
                                    blue_spin.setRange(-1, 1000)
                                    blue_spin.setValue(color_mode['BlueChannelWeight'])
                                    blue_spin.setMinimumWidth(120)
                                    blue_spin.valueChanged.connect(
                                        partial(self.on_color_weight_changed, color_mode, 'BlueChannelWeight')
                                    )
                                    color_layout.addRow("Blue Weight:", blue_spin)
                                    
                                    control_key = f"blue_weight_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (blue_spin, 'value', color_mode['BlueChannelWeight'])
                                
                                # Reference Channel
                                if 'ReferChannel' in color_mode:
                                    ref_combo = QComboBox()
                                    ref_combo.addItems(['H_CHANNEL', 'S_CHANNEL', 'V_CHANNEL'])
                                    ref_combo.setCurrentText(color_mode['ReferChannel'])
                                    ref_combo.setMinimumWidth(120)
                                    ref_combo.currentTextChanged.connect(
                                        partial(self.on_color_ref_changed, color_mode)
                                    )
                                    color_layout.addRow("Reference Channel:", ref_combo)
                                    
                                    control_key = f"ref_channel_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (ref_combo, 'text', color_mode['ReferChannel'])
                            
                            color_group.setLayout(color_layout)
                            stage_layout.addWidget(color_group)
                        
                        # Grayscale Enhancement Modes
                        if 'GrayscaleEnhancementModes' in stage:
                            enhance_group = QGroupBox("Grayscale Enhancement")
                            enhance_layout = QFormLayout()
                            
                            for enhance_mode in stage['GrayscaleEnhancementModes']:
                                mode_text = enhance_mode.get('Mode', 'Unknown')
                                enhance_layout.addRow(QLabel(f"Mode: {mode_text.replace('GEM_', '')}"))
                                
                                # Sensitivity
                                if 'Sensitivity' in enhance_mode:
                                    sens_spin = QSpinBox()
                                    sens_spin.setRange(1, 9)
                                    sens_spin.setValue(enhance_mode['Sensitivity'])
                                    sens_spin.setMinimumWidth(120)
                                    sens_spin.valueChanged.connect(
                                        partial(self.on_enhance_sensitivity_changed, enhance_mode)
                                    )
                                    enhance_layout.addRow("Sensitivity:", sens_spin)
                                    
                                    control_key = f"enhance_sens_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (sens_spin, 'value', enhance_mode['Sensitivity'])
                                
                                # Sharpen Block Size X
                                if 'SharpenBlockSizeX' in enhance_mode:
                                    sharpen_x_spin = QSpinBox()
                                    sharpen_x_spin.setRange(3, 1000)
                                    sharpen_x_spin.setValue(enhance_mode['SharpenBlockSizeX'])
                                    sharpen_x_spin.setMinimumWidth(120)
                                    sharpen_x_spin.valueChanged.connect(
                                        partial(self.on_enhance_block_changed, enhance_mode, 'SharpenBlockSizeX')
                                    )
                                    enhance_layout.addRow("Sharpen Block X:", sharpen_x_spin)
                                    
                                    control_key = f"sharpen_x_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (sharpen_x_spin, 'value', enhance_mode['SharpenBlockSizeX'])
                                
                                # Sharpen Block Size Y
                                if 'SharpenBlockSizeY' in enhance_mode:
                                    sharpen_y_spin = QSpinBox()
                                    sharpen_y_spin.setRange(3, 1000)
                                    sharpen_y_spin.setValue(enhance_mode['SharpenBlockSizeY'])
                                    sharpen_y_spin.setMinimumWidth(120)
                                    sharpen_y_spin.valueChanged.connect(
                                        partial(self.on_enhance_block_changed, enhance_mode, 'SharpenBlockSizeY')
                                    )
                                    enhance_layout.addRow("Sharpen Block Y:", sharpen_y_spin)
                                    
                                    control_key = f"sharpen_y_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (sharpen_y_spin, 'value', enhance_mode['SharpenBlockSizeY'])
                            
                            enhance_group.setLayout(enhance_layout)
                            stage_layout.addWidget(enhance_group)
                        
                        # Texture Detection Modes
                        if 'TextureDetectionModes' in stage:
                            texture_group = QGroupBox("Texture Detection")
                            texture_layout = QFormLayout()
                            
                            for texture_mode in stage['TextureDetectionModes']:
                                mode_text = texture_mode.get('Mode', 'Unknown')
                                texture_layout.addRow(QLabel(f"Mode: {mode_text.replace('TDM_', '')}"))
                                
                                if 'Sensitivity' in texture_mode:
                                    sens_spin = QSpinBox()
                                    sens_spin.setRange(1, 9)
                                    sens_spin.setValue(texture_mode['Sensitivity'])
                                    sens_spin.setMinimumWidth(120)
                                    sens_spin.valueChanged.connect(
                                        partial(self.on_texture_sensitivity_changed, texture_mode)
                                    )
                                    texture_layout.addRow("Sensitivity:", sens_spin)
                                    
                                    control_key = f"texture_sens_{param.get('Name', f'param_{i}')}_{stage_name}"
                                    self.ui_controls[control_key] = (sens_spin, 'value', texture_mode['Sensitivity'])
                            
                            texture_group.setLayout(texture_layout)
                            stage_layout.addWidget(texture_group)
                        
                        # Shortline Detection Mode
                        if 'ShortlineDetectionMode' in stage:
                            shortline_group = QGroupBox("Shortline Detection")
                            shortline_layout = QFormLayout()
                            
                            shortline_mode = stage['ShortlineDetectionMode']
                            mode_text = shortline_mode.get('Mode', 'Unknown')
                            shortline_layout.addRow(QLabel(f"Mode: {mode_text.replace('SDM_', '')}"))
                            
                            if 'Sensitivity' in shortline_mode:
                                sens_spin = QSpinBox()
                                sens_spin.setRange(1, 9)
                                sens_spin.setValue(shortline_mode['Sensitivity'])
                                sens_spin.setMinimumWidth(120)
                                sens_spin.valueChanged.connect(
                                    partial(self.on_shortline_sensitivity_changed, shortline_mode)
                                )
                                shortline_layout.addRow("Sensitivity:", sens_spin)
                                
                                control_key = f"shortline_sens_{param.get('Name', f'param_{i}')}_{stage_name}"
                                self.ui_controls[control_key] = (sens_spin, 'value', shortline_mode['Sensitivity'])
                            
                            shortline_group.setLayout(shortline_layout)
                            stage_layout.addWidget(shortline_group)
                        
                        # Line Assembly Mode
                        if 'LineAssemblyMode' in stage:
                            assembly_group = QGroupBox("Line Assembly")
                            assembly_layout = QFormLayout()
                            
                            assembly_mode = stage['LineAssemblyMode']
                            mode_text = assembly_mode.get('Mode', 'Unknown')
                            assembly_layout.addRow(QLabel(f"Mode: {mode_text.replace('LAM_', '')}"))
                            
                            if 'Sensitivity' in assembly_mode:
                                sens_spin = QSpinBox()
                                sens_spin.setRange(1, 9)
                                sens_spin.setValue(assembly_mode['Sensitivity'])
                                sens_spin.setMinimumWidth(120)
                                sens_spin.valueChanged.connect(
                                    partial(self.on_assembly_sensitivity_changed, assembly_mode)
                                )
                                assembly_layout.addRow("Sensitivity:", sens_spin)
                                
                                control_key = f"assembly_sens_{param.get('Name', f'param_{i}')}_{stage_name}"
                                self.ui_controls[control_key] = (sens_spin, 'value', assembly_mode['Sensitivity'])
                            
                            assembly_group.setLayout(assembly_layout)
                            stage_layout.addWidget(assembly_group)
                        
                        # Image Scale Setting
                        if 'ImageScaleSetting' in stage:
                            scale_group = QGroupBox("Image Scale Setting")
                            scale_layout = QFormLayout()
                            
                            scale_setting = stage['ImageScaleSetting']
                            
                            # Edge Length Threshold
                            if 'EdgeLengthThreshold' in scale_setting:
                                edge_spin = QSpinBox()
                                edge_spin.setRange(1, 10000)
                                edge_spin.setValue(scale_setting['EdgeLengthThreshold'])
                                edge_spin.setMinimumWidth(120)
                                edge_spin.valueChanged.connect(
                                    partial(self.on_edge_threshold_changed, scale_setting)
                                )
                                scale_layout.addRow("Edge Length Threshold:", edge_spin)
                                
                                control_key = f"edge_threshold_{param.get('Name', f'param_{i}')}_{stage_name}"
                                self.ui_controls[control_key] = (edge_spin, 'value', scale_setting['EdgeLengthThreshold'])
                            
                            # Reference Edge
                            if 'ReferenceEdge' in scale_setting:
                                ref_combo = QComboBox()
                                ref_combo.addItems(['RE_SHORTER_EDGE', 'RE_LONGER_EDGE'])
                                ref_combo.setCurrentText(scale_setting['ReferenceEdge'])
                                ref_combo.setMinimumWidth(120)
                                ref_combo.currentTextChanged.connect(
                                    partial(self.on_ref_edge_changed, scale_setting)
                                )
                                scale_layout.addRow("Reference Edge:", ref_combo)
                                
                                control_key = f"ref_edge_{param.get('Name', f'param_{i}')}_{stage_name}"
                                self.ui_controls[control_key] = (ref_combo, 'text', scale_setting['ReferenceEdge'])
                            
                            # Scale Type
                            if 'ScaleType' in scale_setting:
                                type_combo = QComboBox()
                                type_combo.addItems(['ST_SCALE_DOWN', 'ST_SCALE_UP'])
                                type_combo.setCurrentText(scale_setting['ScaleType'])
                                type_combo.setMinimumWidth(120)
                                type_combo.currentTextChanged.connect(
                                    partial(self.on_scale_type_changed, scale_setting)
                                )
                                scale_layout.addRow("Scale Type:", type_combo)
                                
                                control_key = f"scale_type_{param.get('Name', f'param_{i}')}_{stage_name}"
                                self.ui_controls[control_key] = (type_combo, 'text', scale_setting['ScaleType'])
                            
                            scale_group.setLayout(scale_layout)
                            stage_layout.addWidget(scale_group)
                        
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
        
    def create_global_parameter_tab(self):
        """Create global parameter controls"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Global Parameters")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title)
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Get global parameters
        global_params = self.default_settings.get('GlobalParameter', {})
        if global_params:
            # Max Total Image Dimension
            param_layout = QFormLayout()
            
            max_dimension = global_params.get('MaxTotalImageDimension', 0)
            max_dimension_spinbox = QSpinBox()
            max_dimension_spinbox.setRange(0, 999999999)
            max_dimension_spinbox.setValue(max_dimension)
            max_dimension_spinbox.setSuffix(" pixels")
            max_dimension_spinbox.setToolTip("Maximum total image dimension (0 = no limit)")
            max_dimension_spinbox.valueChanged.connect(partial(self.on_max_dimension_changed))
            param_layout.addRow("Max Total Image Dimension:", max_dimension_spinbox)
            
            # Store control reference
            self.ui_controls[f"max_dimension"] = (max_dimension_spinbox, 'value', max_dimension)
            
            scroll_layout.addLayout(param_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        self.param_tabs.addTab(tab, "Global Parameters")
        
    def create_target_roi_tab(self):
        """Create target ROI definition controls"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Target ROI Definition Options")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title)
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Get target ROI options
        target_roi_options = self.default_settings.get('TargetROIDefOptions', [])
        
        for i, roi_option in enumerate(target_roi_options):
            roi_group = QGroupBox(f"ROI: {roi_option.get('Name', f'ROI {i+1}')}")
            roi_layout = QFormLayout()
            
            # Enable Results Deduplication
            if 'EnableResultsDeduplication' in roi_option:
                dedup_checkbox = QCheckBox()
                dedup_checkbox.setChecked(bool(roi_option['EnableResultsDeduplication']))
                dedup_checkbox.stateChanged.connect(
                    partial(self.on_roi_deduplication_changed, roi_option)
                )
                roi_layout.addRow("Enable Results Deduplication:", dedup_checkbox)
                
                control_key = f"roi_dedup_{roi_option.get('Name', f'roi_{i}')}"
                self.ui_controls[control_key] = (dedup_checkbox, 'checked', bool(roi_option['EnableResultsDeduplication']))
            
            # Pause Flag
            if 'PauseFlag' in roi_option:
                pause_checkbox = QCheckBox()
                pause_checkbox.setChecked(bool(roi_option['PauseFlag']))
                pause_checkbox.stateChanged.connect(
                    partial(self.on_roi_pause_changed, roi_option)
                )
                roi_layout.addRow("Pause Flag:", pause_checkbox)
                
                control_key = f"roi_pause_{roi_option.get('Name', f'roi_{i}')}"
                self.ui_controls[control_key] = (pause_checkbox, 'checked', bool(roi_option['PauseFlag']))
            
            # Task Setting Name Array
            if 'TaskSettingNameArray' in roi_option:
                task_list = QListWidget()
                task_list.addItems(roi_option['TaskSettingNameArray'])
                task_list.setMaximumHeight(100)
                roi_layout.addRow("Task Settings:", task_list)
                
                control_key = f"roi_tasks_{roi_option.get('Name', f'roi_{i}')}"
                self.ui_controls[control_key] = (task_list, 'items', roi_option['TaskSettingNameArray'])
            
            # Location settings (simplified - these are complex nested objects)
            if 'Location' in roi_option:
                location = roi_option['Location']
                location_group = QGroupBox("Location Settings")
                location_layout = QFormLayout()
                
                # Reference Object Type
                if 'ReferenceObjectType' in location:
                    ref_obj_combo = QComboBox()
                    ref_obj_combo.addItems(['ROT_ATOMIC_OBJECT', 'ROT_LOCALIZED_TEXT_LINE', 'ROT_BARCODE', 'ROT_TEXT_ZONE'])
                    ref_obj_combo.setCurrentText(location['ReferenceObjectType'])
                    ref_obj_combo.currentTextChanged.connect(
                        partial(self.on_roi_ref_object_changed, location)
                    )
                    location_layout.addRow("Reference Object Type:", ref_obj_combo)
                    
                    control_key = f"roi_ref_obj_{roi_option.get('Name', f'roi_{i}')}"
                    self.ui_controls[control_key] = (ref_obj_combo, 'text', location['ReferenceObjectType'])
                
                # Measured By Percentage (in Offset)
                if 'Offset' in location and 'MeasuredByPercentage' in location['Offset']:
                    offset = location['Offset']
                    measured_checkbox = QCheckBox()
                    measured_checkbox.setChecked(bool(offset['MeasuredByPercentage']))
                    measured_checkbox.stateChanged.connect(
                        partial(self.on_roi_measured_changed, offset)
                    )
                    location_layout.addRow("Measured By Percentage:", measured_checkbox)
                    
                    control_key = f"roi_measured_{roi_option.get('Name', f'roi_{i}')}"
                    self.ui_controls[control_key] = (measured_checkbox, 'checked', bool(offset['MeasuredByPercentage']))
                
                location_group.setLayout(location_layout)
                roi_layout.addRow(location_group)
            
            roi_group.setLayout(roi_layout)
            scroll_layout.addWidget(roi_group)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        self.param_tabs.addTab(tab, "Target ROI")
        
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
        
    # New parameter callback methods
    def on_all_module_deviation_changed(self, spec: Dict, value: int):
        """Handle all module deviation changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['AllModuleDeviation'] = value
                    break
        self.update_settings()
        
    def on_aus_post_encoding_changed(self, spec: Dict, value: str):
        """Handle Australian Post encoding table changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['AustralianPostEncodingTable'] = value
                    break
        self.update_settings()
        
    def on_barcode_regex_changed(self, spec: Dict, value: str):
        """Handle barcode text regex pattern changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['BarcodeTextRegExPattern'] = value
                    break
        self.update_settings()
        
    def on_border_distance_changed(self, spec: Dict, value: int):
        """Handle barcode zone min distance to borders changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['BarcodeZoneMinDistanceToImageBorders'] = value
                    break
        self.update_settings()
        
    def on_code128_subset_changed(self, spec: Dict, value: str):
        """Handle Code 128 subset changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['Code128Subset'] = value
                    break
        self.update_settings()
        
    def on_dm_isotropic_changed(self, spec: Dict, state: int):
        """Handle DataMatrix module isotropic changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['DataMatrixModuleIsotropic'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_addon_code_changed(self, spec: Dict, state: int):
        """Handle enable add-on code changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['EnableAddOnCode'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_dm_ecc_changed(self, spec: Dict, state: int):
        """Handle DataMatrix ECC000-140 changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['EnableDataMatrixECC000-140'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_qr_model1_changed(self, spec: Dict, state: int):
        """Handle QR Code Model 1 changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['EnableQRCodeModel1'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_head_ratio_changed(self, spec: Dict, value: str):
        """Handle head module ratio changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['HeadModuleRatio'] = value
                    break
        self.update_settings()
        
    def on_tail_ratio_changed(self, spec: Dict, value: str):
        """Handle tail module ratio changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['TailModuleRatio'] = value
                    break
        self.update_settings()
        
    def on_ai01_changed(self, spec: Dict, state: int):
        """Handle include implied AI 01 changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['IncludeImpliedAI01'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_check_digit_changed(self, spec: Dict, state: int):
        """Handle include trailing check digit changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['IncludeTrailingCheckDigit'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_msi_calc_changed(self, spec: Dict, value: str):
        """Handle MSI check digit calculation changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['MSICodeCheckDigitCalculation'] = value
                    break
        self.update_settings()
        
    def on_width_height_ratio_changed(self, spec: Dict, value: float):
        """Handle min ratio of barcode zone width to height changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['MinRatioOfBarcodeZoneWidthToHeight'] = value
                    break
        self.update_settings()
        
    def on_startstop_changed(self, spec: Dict, state: int):
        """Handle require start/stop characters changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['RequireStartStopChars'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_partial_value_changed(self, spec: Dict, state: int):
        """Handle return partial barcode value changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['ReturnPartialBarcodeValue'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_std_format_changed(self, spec: Dict, value: str):
        """Handle standard format changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['StandardFormat'] = value
                    break
        self.update_settings()
        
    def on_verify_digit_changed(self, spec: Dict, state: int):
        """Handle verify check digit changes"""
        if 'BarcodeFormatSpecificationOptions' in self.current_settings:
            for current_spec in self.current_settings['BarcodeFormatSpecificationOptions']:
                if current_spec.get('Name') == spec.get('Name'):
                    current_spec['VerifyCheckDigit'] = 1 if state == Qt.CheckState.Checked.value else 0
                    break
        self.update_settings()
        
    def on_dpm_format_changed(self, task: Dict, mode_index: int, value: str):
        """Handle DPM code reading mode barcode format changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'DPMCodeReadingModes' in current_task and mode_index < len(current_task['DPMCodeReadingModes']):
                        current_task['DPMCodeReadingModes'][mode_index]['BarcodeFormat'] = value
                    break
        self.update_settings()
        
    def on_dpm_mode_changed(self, task: Dict, mode_index: int, value: str):
        """Handle DPM code reading mode changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'DPMCodeReadingModes' in current_task and mode_index < len(current_task['DPMCodeReadingModes']):
                        current_task['DPMCodeReadingModes'][mode_index]['Mode'] = value
                    break
        self.update_settings()
        
    def on_text_order_changed(self, task: Dict, order_index: int, value: str):
        """Handle text result order mode changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'TextResultOrderModes' in current_task and order_index < len(current_task['TextResultOrderModes']):
                        current_task['TextResultOrderModes'][order_index]['Mode'] = value
                    break
        self.update_settings()
        
    def on_region_mode_changed(self, task: Dict, mode_index: int, value: str):
        """Handle region predetection mode changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_REGION_PREDETECTION':
                                for stage in section.get('StageArray', []):
                                    if 'RegionPredetectionModes' in stage and mode_index < len(stage['RegionPredetectionModes']):
                                        stage['RegionPredetectionModes'][mode_index]['Mode'] = value
                                        break
                    break
        self.update_settings()
        
    def on_region_sensitivity_changed(self, task: Dict, mode_index: int, value: int):
        """Handle region predetection sensitivity changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_REGION_PREDETECTION':
                                for stage in section.get('StageArray', []):
                                    if 'RegionPredetectionModes' in stage and mode_index < len(stage['RegionPredetectionModes']):
                                        stage['RegionPredetectionModes'][mode_index]['Sensitivity'] = value
                                        break
                    break
        self.update_settings()
        
    def on_region_min_dim_changed(self, task: Dict, mode_index: int, value: int):
        """Handle region predetection min image dimension changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_REGION_PREDETECTION':
                                for stage in section.get('StageArray', []):
                                    if 'RegionPredetectionModes' in stage and mode_index < len(stage['RegionPredetectionModes']):
                                        stage['RegionPredetectionModes'][mode_index]['MinImageDimension'] = value
                                        break
                    break
        self.update_settings()
        
    def on_region_block_size_changed(self, task: Dict, mode_index: int, value: int):
        """Handle region predetection spatial index block size changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_REGION_PREDETECTION':
                                for stage in section.get('StageArray', []):
                                    if 'RegionPredetectionModes' in stage and mode_index < len(stage['RegionPredetectionModes']):
                                        stage['RegionPredetectionModes'][mode_index]['SpatialIndexBlockSize'] = value
                                        break
                    break
        self.update_settings()
        
    def on_region_accurate_changed(self, task: Dict, mode_index: int, state: int):
        """Handle region predetection find accurate boundary changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_REGION_PREDETECTION':
                                for stage in section.get('StageArray', []):
                                    if 'RegionPredetectionModes' in stage and mode_index < len(stage['RegionPredetectionModes']):
                                        stage['RegionPredetectionModes'][mode_index]['FindAccurateBoundary'] = 1 if state == Qt.CheckState.Checked.value else 0
                                        break
                    break
        self.update_settings()
        
    def on_region_percentage_changed(self, task: Dict, mode_index: int, state: int):
        """Handle region predetection measured by percentage changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_REGION_PREDETECTION':
                                for stage in section.get('StageArray', []):
                                    if 'RegionPredetectionModes' in stage and mode_index < len(stage['RegionPredetectionModes']):
                                        stage['RegionPredetectionModes'][mode_index]['MeasuredByPercentage'] = 1 if state == Qt.CheckState.Checked.value else 0
                                        break
                    break
        self.update_settings()
        
    def on_region_model_changed(self, task: Dict, mode_index: int, value: str):
        """Handle region predetection model name changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_REGION_PREDETECTION':
                                for stage in section.get('StageArray', []):
                                    if 'RegionPredetectionModes' in stage and mode_index < len(stage['RegionPredetectionModes']):
                                        stage['RegionPredetectionModes'][mode_index]['DetectionModelName'] = value
                                        break
                    break
        self.update_settings()
        
    def on_localization_stacked_changed(self, task: Dict, mode_index: int, mode_text: str, state: int):
        """Handle localization mode IsOneDStacked changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_LOCALIZATION':
                                for stage in section.get('StageArray', []):
                                    if 'LocalizationModes' in stage:
                                        for mode in stage['LocalizationModes']:
                                            if mode.get('Mode') == mode_text:
                                                mode['IsOneDStacked'] = 1 if state == Qt.CheckState.Checked.value else 0
                                                break
                    break
        self.update_settings()
        
    def on_localization_module_size_changed(self, task: Dict, mode_index: int, mode_text: str, value: int):
        """Handle localization mode module size changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_LOCALIZATION':
                                for stage in section.get('StageArray', []):
                                    if 'LocalizationModes' in stage:
                                        for mode in stage['LocalizationModes']:
                                            if mode.get('Mode') == mode_text:
                                                mode['ModuleSize'] = value
                                                break
                    break
        self.update_settings()
        
    def on_localization_scan_direction_changed(self, task: Dict, mode_index: int, mode_text: str, value: int):
        """Handle localization mode scan direction changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_LOCALIZATION':
                                for stage in section.get('StageArray', []):
                                    if 'LocalizationModes' in stage:
                                        for mode in stage['LocalizationModes']:
                                            if mode.get('Mode') == mode_text:
                                                mode['ScanDirection'] = value
                                                break
                    break
        self.update_settings()
        
    def on_localization_scan_stride_changed(self, task: Dict, mode_index: int, mode_text: str, value: int):
        """Handle localization mode scan stride changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_LOCALIZATION':
                                for stage in section.get('StageArray', []):
                                    if 'LocalizationModes' in stage:
                                        for mode in stage['LocalizationModes']:
                                            if mode.get('Mode') == mode_text:
                                                mode['ScanStride'] = value
                                                break
                    break
        self.update_settings()
        
    def on_deform_mode_changed(self, task: Dict, mode_index: int, value: str):
        """Handle deformation resisting mode changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']):
                                            stage['DeformationResistingModes'][mode_index]['Mode'] = value
                                            break
                    break
        self.update_settings()
        
    def on_deform_level_changed(self, task: Dict, mode_index: int, value: int):
        """Handle deformation resisting level changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']):
                                            stage['DeformationResistingModes'][mode_index]['Level'] = value
                                            break
                    break
        self.update_settings()
        
    def on_deform_bin_mode_changed(self, task: Dict, mode_index: int, value: str):
        """Handle deformation resisting binarization mode changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']) and 'BinarizationMode' in stage['DeformationResistingModes'][mode_index]:
                                            stage['DeformationResistingModes'][mode_index]['BinarizationMode']['Mode'] = value
                                            break
                    break
        self.update_settings()
        
    def on_deform_bin_threshold_changed(self, task: Dict, mode_index: int, value: int):
        """Handle deformation resisting binarization threshold changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']) and 'BinarizationMode' in stage['DeformationResistingModes'][mode_index]:
                                            stage['DeformationResistingModes'][mode_index]['BinarizationMode']['BinarizationThreshold'] = value
                                            break
                    break
        self.update_settings()
        
    def on_deform_bin_block_x_changed(self, task: Dict, mode_index: int, value: int):
        """Handle deformation resisting binarization block X changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']) and 'BinarizationMode' in stage['DeformationResistingModes'][mode_index]:
                                            stage['DeformationResistingModes'][mode_index]['BinarizationMode']['BlockSizeX'] = value
                                            break
                    break
        self.update_settings()
        
    def on_deform_bin_block_y_changed(self, task: Dict, mode_index: int, value: int):
        """Handle deformation resisting binarization block Y changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']) and 'BinarizationMode' in stage['DeformationResistingModes'][mode_index]:
                                            stage['DeformationResistingModes'][mode_index]['BinarizationMode']['BlockSizeY'] = value
                                            break
                    break
        self.update_settings()
        
    def on_deform_bin_fill_changed(self, task: Dict, mode_index: int, state: int):
        """Handle deformation resisting binarization fill vacancy changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']) and 'BinarizationMode' in stage['DeformationResistingModes'][mode_index]:
                                            stage['DeformationResistingModes'][mode_index]['BinarizationMode']['EnableFillBinaryVacancy'] = 1 if state == Qt.CheckState.Checked.value else 0
                                            break
                    break
        self.update_settings()
        
    def on_deform_bin_compensation_changed(self, task: Dict, mode_index: int, value: int):
        """Handle deformation resisting binarization threshold compensation changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']) and 'BinarizationMode' in stage['DeformationResistingModes'][mode_index]:
                                            stage['DeformationResistingModes'][mode_index]['BinarizationMode']['ThresholdCompensation'] = value
                                            break
                    break
        self.update_settings()
        
    def on_deform_gray_mode_changed(self, task: Dict, mode_index: int, value: str):
        """Handle deformation resisting grayscale enhancement mode changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']) and 'GrayscaleEnhancementMode' in stage['DeformationResistingModes'][mode_index]:
                                            stage['DeformationResistingModes'][mode_index]['GrayscaleEnhancementMode']['Mode'] = value
                                            break
                    break
        self.update_settings()
        
    def on_deform_gray_sensitivity_changed(self, task: Dict, mode_index: int, value: int):
        """Handle deformation resisting grayscale enhancement sensitivity changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_RESIST_DEFORMATION' and 'DeformationResistingModes' in stage:
                                        if mode_index < len(stage['DeformationResistingModes']) and 'GrayscaleEnhancementMode' in stage['DeformationResistingModes'][mode_index]:
                                            stage['DeformationResistingModes'][mode_index]['GrayscaleEnhancementMode']['Sensitivity'] = value
                                            break
                    break
        self.update_settings()
        
    def on_complement_mode_changed(self, task: Dict, mode_index: int, value: str):
        """Handle barcode complement mode changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_COMPLEMENT_BARCODE' and 'BarcodeComplementModes' in stage:
                                        if mode_index < len(stage['BarcodeComplementModes']):
                                            stage['BarcodeComplementModes'][mode_index]['Mode'] = value
                                            break
                    break
        self.update_settings()
        
    def on_scale_mode_changed(self, task: Dict, mode_index: int, value: str):
        """Handle barcode scale mode changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_SCALE_BARCODE_IMAGE' and 'BarcodeScaleModes' in stage:
                                        if mode_index < len(stage['BarcodeScaleModes']):
                                            stage['BarcodeScaleModes'][mode_index]['Mode'] = value
                                            break
                    break
        self.update_settings()
        
    def on_scale_angle_changed(self, task: Dict, mode_index: int, value: int):
        """Handle barcode scale acute angle threshold changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_SCALE_BARCODE_IMAGE' and 'BarcodeScaleModes' in stage:
                                        if mode_index < len(stage['BarcodeScaleModes']):
                                            stage['BarcodeScaleModes'][mode_index]['AcuteAngleWithXThreshold'] = value
                                            break
                    break
        self.update_settings()
        
    def on_scale_module_threshold_changed(self, task: Dict, mode_index: int, value: int):
        """Handle barcode scale module size threshold changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_SCALE_BARCODE_IMAGE' and 'BarcodeScaleModes' in stage:
                                        if mode_index < len(stage['BarcodeScaleModes']):
                                            stage['BarcodeScaleModes'][mode_index]['ModuleSizeThreshold'] = value
                                            break
                    break
        self.update_settings()
        
    def on_scale_target_size_changed(self, task: Dict, mode_index: int, value: int):
        """Handle barcode scale target module size changes"""
        if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
            for current_task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                if current_task.get('Name') == task.get('Name'):
                    if 'SectionArray' in current_task:
                        for section in current_task['SectionArray']:
                            if section.get('Section') == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_SCALE_BARCODE_IMAGE' and 'BarcodeScaleModes' in stage:
                                        if mode_index < len(stage['BarcodeScaleModes']):
                                            stage['BarcodeScaleModes'][mode_index]['TargetModuleSize'] = value
                                            break
                    break
        self.update_settings()
        
    def on_max_dimension_changed(self, value: int):
        """Handle global parameter MaxTotalImageDimension changes"""
        if 'GlobalParameter' not in self.current_settings:
            self.current_settings['GlobalParameter'] = {}
        self.current_settings['GlobalParameter']['MaxTotalImageDimension'] = value
        self.update_settings()
        
    def on_color_weight_changed(self, mode_dict: Dict, weight_key: str, value: int):
        """Handle colour conversion weight changes"""
        mode_dict[weight_key] = value
        self.update_settings()
        
    def on_color_ref_changed(self, mode_dict: Dict, value: str):
        """Handle colour conversion reference channel changes"""
        mode_dict['ReferChannel'] = value
        self.update_settings()
        
    def on_enhance_sensitivity_changed(self, mode_dict: Dict, value: int):
        """Handle grayscale enhancement sensitivity changes"""
        mode_dict['Sensitivity'] = value
        self.update_settings()
        
    def on_enhance_block_changed(self, mode_dict: Dict, block_key: str, value: int):
        """Handle grayscale enhancement block size changes"""
        mode_dict[block_key] = value
        self.update_settings()
        
    def on_texture_sensitivity_changed(self, mode_dict: Dict, value: int):
        """Handle texture detection sensitivity changes"""
        mode_dict['Sensitivity'] = value
        self.update_settings()
        
    def on_shortline_sensitivity_changed(self, mode_dict: Dict, value: int):
        """Handle shortline detection sensitivity changes"""
        mode_dict['Sensitivity'] = value
        self.update_settings()
        
    def on_assembly_sensitivity_changed(self, mode_dict: Dict, value: int):
        """Handle line assembly sensitivity changes"""
        mode_dict['Sensitivity'] = value
        self.update_settings()
        
    def on_edge_threshold_changed(self, setting_dict: Dict, value: int):
        """Handle edge length threshold changes"""
        setting_dict['EdgeLengthThreshold'] = value
        self.update_settings()
        
    def on_ref_edge_changed(self, setting_dict: Dict, value: str):
        """Handle reference edge changes"""
        setting_dict['ReferenceEdge'] = value
        self.update_settings()
        
    def on_scale_type_changed(self, setting_dict: Dict, value: str):
        """Handle scale type changes"""
        setting_dict['ScaleType'] = value
        self.update_settings()
        
    def on_roi_deduplication_changed(self, roi_option: Dict, state: int):
        """Handle ROI results deduplication changes"""
        roi_option['EnableResultsDeduplication'] = bool(state == Qt.CheckState.Checked.value)
        self.update_settings()
        
    def on_roi_pause_changed(self, roi_option: Dict, state: int):
        """Handle ROI pause flag changes"""
        roi_option['PauseFlag'] = bool(state == Qt.CheckState.Checked.value)
        self.update_settings()
        
    def on_roi_ref_object_changed(self, location_dict: Dict, value: str):
        """Handle ROI reference object type changes"""
        location_dict['ReferenceObjectType'] = value
        self.update_settings()
        
    def on_roi_measured_changed(self, offset_dict: Dict, state: int):
        """Handle ROI measured by percentage changes"""
        offset_dict['MeasuredByPercentage'] = bool(state == Qt.CheckState.Checked.value)
        self.update_settings()
        
    def update_settings(self):
        """Update current settings and notify about changes"""
        # Settings are updated in-place through the parameter controls
        # This method can be used to perform additional validation or processing
        print("Updating settings and UI controls...")
        
        # Validate current settings structure
        self.validate_settings_structure()
        
        # Update UI and display
        self.update_ui_from_settings()
        self.update_parameters_display()
        
    def validate_settings_structure(self):
        """Validate and fix any issues with the current settings structure"""
        try:
            # Ensure all top-level sections exist
            required_sections = [
                'BarcodeFormatSpecificationOptions',
                'BarcodeReaderTaskSettingOptions', 
                'ImageParameterOptions',
                'CaptureVisionTemplates',
                'TargetROIDefOptions'
            ]
            
            for section in required_sections:
                if section not in self.current_settings:
                    print(f"Warning: Missing section {section} in current settings")
                    # Initialize with empty array or object as appropriate
                    if section in ['BarcodeFormatSpecificationOptions', 'BarcodeReaderTaskSettingOptions', 
                                   'ImageParameterOptions', 'CaptureVisionTemplates', 'TargetROIDefOptions']:
                        self.current_settings[section] = []
                    else:
                        self.current_settings[section] = {}
            
            # Ensure GlobalParameter exists
            if 'GlobalParameter' not in self.current_settings:
                self.current_settings['GlobalParameter'] = {'MaxTotalImageDimension': 0}
            
            # Validate JSON serializability
            json_test = json.dumps(self.current_settings)
            print(f"Settings validation passed - JSON size: {len(json_test)} characters")
            
        except Exception as e:
            print(f"Settings validation error: {e}")
            # If validation fails, reset to default settings
            self.current_settings = copy.deepcopy(self.default_settings)
        
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
                test_number = getattr(self, 'auto_adjustment_index', 0)
                total_tests = len(getattr(self, 'auto_adjustment_params', []))
                self.toggle_auto_adjustment()
                self.status_bar.showMessage(f"Success! Test {test_number}/{total_tests} found {len(results)} barcode(s) - auto-adjustment stopped")
            else:
                self.status_bar.showMessage(f"Detection complete - found {len(results)} barcode(s)")
        else:
            self.result_text.setPlainText("No barcodes detected")
            if not self.auto_adjusting:
                self.status_bar.showMessage("Detection complete - no barcodes found")
            
        # Update image overlay
        self.image_panel.set_barcode_results(results)
        
    def on_progress_update(self, message: str):
        """Handle progress updates from worker thread"""
        if self.auto_adjusting and hasattr(self, 'auto_adjustment_index') and hasattr(self, 'auto_adjustment_params'):
            # During auto-adjustment, preserve the progress information
            progress_info = f"Test {self.auto_adjustment_index}/{len(self.auto_adjustment_params)}"
            if "Detecting barcodes" in message:
                self.status_bar.showMessage(f"{progress_info}: Detecting barcodes...")
            elif "Applying settings" in message:
                self.status_bar.showMessage(f"{progress_info}: Applying parameter settings...")
            else:
                self.status_bar.showMessage(f"{progress_info}: {message}")
        else:
            # Normal operation, show message as-is
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
    
    def on_auto_adjust_mode_changed(self):
        """Handle auto adjustment mode change"""
        mode_text = self.auto_adjust_mode.currentText()
        is_custom = "Custom" in mode_text
        
        if is_custom:
            # Show custom iterations dialog
            dialog = CustomIterationsDialog(self.custom_iterations_value, self)
            if dialog.exec() == 1:  # QDialog.Accepted value is 1
                self.custom_iterations_value = dialog.get_iterations()
                self.status_bar.showMessage(f"Custom mode selected - will test {self.custom_iterations_value} parameter combinations")
            else:
                # User cancelled, revert to previous selection
                self.auto_adjust_mode.setCurrentIndex(1)  # Back to Standard
                self.status_bar.showMessage("Custom mode cancelled - reverted to Standard mode")
        else:
            iterations = 20 if "Quick" in mode_text else 40 if "Standard" in mode_text else 60 if "Comprehensive" in mode_text else 100
            self.status_bar.showMessage(f"{mode_text} selected - will test {iterations} parameter combinations")
            
    def prepare_auto_adjustment_params(self):
        """Prepare different parameter combinations for auto-adjustment based on selected mode"""
        
        # Get the selected mode
        mode_text = self.auto_adjust_mode.currentText()
        if "Quick" in mode_text:
            max_combinations = 20
            mode_name = "Quick"
        elif "Standard" in mode_text:
            max_combinations = 40  
            mode_name = "Standard"
        elif "Comprehensive" in mode_text:
            max_combinations = 60
            mode_name = "Comprehensive"
        elif "Deep" in mode_text:
            max_combinations = 100
            mode_name = "Deep Scan"
        elif "Custom" in mode_text:
            max_combinations = self.custom_iterations_value
            mode_name = f"Custom ({max_combinations})"
        else:
            max_combinations = 40
            mode_name = "Standard"
        
        print(f"Preparing {mode_name} auto-adjustment parameters (max {max_combinations} combinations)...")
        self.auto_adjustment_params = []
        
        # Different localization mode combinations (ordered by effectiveness)
        localization_modes = [
            # Single modes first
            [{"Mode": "LM_CONNECTED_BLOCKS", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}],
            [{"Mode": "LM_SCAN_DIRECTLY", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}],
            [{"Mode": "LM_STATISTICS", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}],
            [{"Mode": "LM_LINES", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}],
            
            # Effective combinations with enhanced parameters
            [{"Mode": "LM_CONNECTED_BLOCKS", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}, 
             {"Mode": "LM_SCAN_DIRECTLY", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}],
            [{"Mode": "LM_CONNECTED_BLOCKS", "ConfidenceThreshold": 60, "ModuleSize": 3, "ScanStride": 0}, 
             {"Mode": "LM_STATISTICS", "ConfidenceThreshold": 50, "ModuleSize": 0, "ScanStride": 0}],
            [{"Mode": "LM_SCAN_DIRECTLY", "ConfidenceThreshold": 40, "ModuleSize": 0, "ScanStride": 4}, 
             {"Mode": "LM_LINES", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}],
             
            # More comprehensive combinations
            [{"Mode": "LM_CONNECTED_BLOCKS", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}, 
             {"Mode": "LM_SCAN_DIRECTLY", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0},
             {"Mode": "LM_STATISTICS", "ConfidenceThreshold": 60, "ModuleSize": 0, "ScanStride": 0}],
        ]
        
        # Enhanced binarization configurations
        binarization_configs = [
            {"BlockSizeX": 0, "BlockSizeY": 0, "Mode": "BM_LOCAL_BLOCK", "ThresholdCompensation": 10},  # Auto - best first
            {"BlockSizeX": 71, "BlockSizeY": 71, "Mode": "BM_LOCAL_BLOCK", "ThresholdCompensation": 10},  # Default
            {"BlockSizeX": 51, "BlockSizeY": 51, "Mode": "BM_LOCAL_BLOCK", "ThresholdCompensation": 15},  # Enhanced
            {"BlockSizeX": 31, "BlockSizeY": 31, "Mode": "BM_LOCAL_BLOCK", "ThresholdCompensation": 20},  # Fine detail
            {"BlockSizeX": 0, "BlockSizeY": 0, "Mode": "BM_AUTO", "ThresholdCompensation": 10},  # Auto mode
            {"BlockSizeX": 101, "BlockSizeY": 101, "Mode": "BM_LOCAL_BLOCK", "ThresholdCompensation": 5},  # Large blocks
        ]
        
        # Region predetection configurations for difficult cases
        region_predetection_configs = [
            {"Mode": "RPM_GENERAL", "Sensitivity": 1, "MinImageDimension": 262144},  # Default
            {"Mode": "RPM_GENERAL", "Sensitivity": 3, "MinImageDimension": 131072},  # More sensitive
            {"Mode": "RPM_GENERAL", "Sensitivity": 5, "MinImageDimension": 65536},   # High sensitivity
            {"Mode": "RPM_GENERAL", "Sensitivity": 7, "MinImageDimension": 32768},   # Very high sensitivity
        ]
        
        # Deformation resisting configurations for damaged barcodes
        deformation_configs = [
            {"Level": 1, "Mode": "DRM_SKIP"},  # Disabled
            {"Level": 3, "Mode": "DRM_AUTO"},  # Light correction
            {"Level": 5, "Mode": "DRM_AUTO"},  # Medium correction
            {"Level": 7, "Mode": "DRM_AUTO"},  # Strong correction
        ]
        
        # Scale configurations for small/large barcodes
        scale_configs = [
            {"Mode": "BSM_SKIP"},  # Disabled
            {"Mode": "BSM_AUTO", "AcuteAngleWithXThreshold": -1, "ModuleSizeThreshold": 0, "TargetModuleSize": 0},
            {"Mode": "BSM_AUTO", "AcuteAngleWithXThreshold": 20, "ModuleSizeThreshold": 2, "TargetModuleSize": 6},
            {"Mode": "BSM_AUTO", "AcuteAngleWithXThreshold": 45, "ModuleSizeThreshold": 4, "TargetModuleSize": 8},
        ]
        
        # Text result ordering for multiple barcodes
        text_order_configs = [
            [{"Mode": "TROM_CONFIDENCE"}],  # By confidence only
            [{"Mode": "TROM_CONFIDENCE"}, {"Mode": "TROM_POSITION"}],  # Confidence then position
            [{"Mode": "TROM_POSITION"}, {"Mode": "TROM_CONFIDENCE"}],  # Position then confidence
        ]
        
        # Expected barcode counts with intelligent defaults
        expected_counts = [0, 1, 3, 5]  # Extended range
        
        # Create intelligent combinations based on mode - prioritize most effective
        combination_count = 0
        
        # Phase 1: Essential combinations (always included in all modes)
        essential_combinations = []
        for expected_count in [0, 1]:  # Most common cases
            for loc_modes in localization_modes[:2]:  # Best single modes
                for bin_config in binarization_configs[:2]:  # Auto and default
                    essential_combinations.append({
                        'expected_count': expected_count,
                        'localization_modes': loc_modes,
                        'binarization_config': bin_config,
                        'region_predetection': region_predetection_configs[0],
                        'deformation_config': deformation_configs[0],
                        'scale_config': scale_configs[0],
                        'text_order': text_order_configs[0]
                    })
        
        # Add essential combinations
        for combo in essential_combinations:
            if combination_count >= max_combinations:
                break
            self.auto_adjustment_params.append(combo)
            combination_count += 1
        
        # Phase 2: Enhanced combinations (for Standard mode and above)
        if combination_count < max_combinations and max_combinations >= 40:
            for expected_count in expected_counts:
                for loc_modes in localization_modes[2:]:  # Additional localization modes
                    for region_config in region_predetection_configs[1:2]:  # Enhanced sensitivity
                        if combination_count >= max_combinations:
                            break
                            
                        self.auto_adjustment_params.append({
                            'expected_count': expected_count,
                            'localization_modes': loc_modes,
                            'binarization_config': binarization_configs[1],
                            'region_predetection': region_config,
                            'deformation_config': deformation_configs[1],
                            'scale_config': scale_configs[1],
                            'text_order': text_order_configs[1]
                        })
                        combination_count += 1
                        
        # Phase 3: Comprehensive combinations (for Comprehensive mode and above)
        if combination_count < max_combinations and max_combinations >= 60:
            for expected_count in [0, 3, 5]:
                for bin_config in binarization_configs[2:]:  # Fine tuning
                    for region_config in region_predetection_configs[2:]:  # High sensitivity
                        if combination_count >= max_combinations:
                            break
                            
                        self.auto_adjustment_params.append({
                            'expected_count': expected_count,
                            'localization_modes': localization_modes[1],  # Scan directly
                            'binarization_config': bin_config,
                            'region_predetection': region_config,
                            'deformation_config': deformation_configs[2],  # Medium correction
                            'scale_config': scale_configs[2],  # Enhanced scaling
                            'text_order': text_order_configs[2]
                        })
                        combination_count += 1
                        
        # Phase 4: Deep scan combinations (for Deep mode only)
        if combination_count < max_combinations and max_combinations >= 100:
            # Advanced deformation and scaling combinations
            for expected_count in expected_counts:
                for deform_config in deformation_configs[2:]:  # Strong correction
                    for scale_config in scale_configs[2:]:  # Advanced scaling
                        for loc_modes in localization_modes[4:]:  # Multi-mode combinations
                            if combination_count >= max_combinations:
                                break
                                
                            self.auto_adjustment_params.append({
                                'expected_count': expected_count,
                                'localization_modes': loc_modes,
                                'binarization_config': binarization_configs[3],  # Fine detail
                                'region_predetection': region_predetection_configs[3],  # Very high sensitivity
                                'deformation_config': deform_config,
                                'scale_config': scale_config,
                                'text_order': text_order_configs[2]
                            })
                                
        print(f"*** Prepared {len(self.auto_adjustment_params)} {mode_name.lower()} parameter combinations")
        if len(self.auto_adjustment_params) > 0:
            print(f"*** Mode coverage: {mode_name}")
            print(f"*** First combination preview: {self.auto_adjustment_params[0]['localization_modes'][0]['Mode']}")
            
            # Show mode-specific features
            if max_combinations >= 40:
                print("*** Includes enhanced region predetection and deformation resistance")
            if max_combinations >= 60:
                print("*** Includes comprehensive binarization fine-tuning")
            if max_combinations >= 100:
                print("🚀 Includes deep scan with advanced scaling and multi-mode localization")
                
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
            total_tests = len(self.auto_adjustment_params)
            self.status_bar.showMessage(f"Auto-adjustment completed - tested {total_tests} parameter combinations, no barcodes found")
            self.result_text.setPlainText(f"Auto-adjustment completed. Tested {total_tests} parameter combinations. No barcodes were detected with any combination.")
            print("Auto-adjustment completed - no combinations left")
            return
            
        if self.detection_worker.isRunning():
            print("Detection worker still running, waiting...")
            return  # Wait for current detection to finish
            
        # Get current parameter combination
        params = self.auto_adjustment_params[self.auto_adjustment_index]
        
        # Create comprehensive descriptive status message
        loc_modes = [mode['Mode'].replace('LM_', '') for mode in params['localization_modes']]
        status_components = []
        
        # Add localization info
        status_components.append(f"Loc: {','.join(loc_modes)}")
        
        # Add binarization info
        if 'binarization_config' in params:
            bin_config = params['binarization_config']
            if bin_config['BlockSizeX'] == 0:
                status_components.append(f"Bin: {bin_config['Mode'][:3]}(Auto)")
            else:
                status_components.append(f"Bin: {bin_config['Mode'][:3]}({bin_config['BlockSizeX']})")
        
        # Add special processing info
        special_features = []
        if 'region_predetection' in params and params['region_predetection']['Sensitivity'] > 1:
            special_features.append(f"RegSens:{params['region_predetection']['Sensitivity']}")
        if 'deformation_config' in params and params['deformation_config']['Mode'] != 'DRM_SKIP':
            special_features.append(f"DefRes:{params['deformation_config']['Level']}")
        if 'scale_config' in params and params['scale_config']['Mode'] != 'BSM_SKIP':
            special_features.append("Scale")
        
        if special_features:
            status_components.append(f"[{','.join(special_features)}]")
        
        status_msg = f"Test {self.auto_adjustment_index + 1}/{len(self.auto_adjustment_params)}: {' | '.join(status_components)}"
        self.status_bar.showMessage(status_msg)
        print(f"Testing enhanced parameters: {params}")
        
        # Apply parameter combination to settings
        self.apply_auto_adjustment_params(params)
        
        # Test with current parameters
        print("Calling test_parameters()...")
        self.test_parameters()
        
        self.auto_adjustment_index += 1
        
    def apply_auto_adjustment_params(self, params):
        """Apply comprehensive parameter combination to current settings"""
        print(f"Applying enhanced auto-adjustment params: {params}")
        try:
            # Update expected barcode count in all tasks
            if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
                for task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                    task['ExpectedBarcodesCount'] = params['expected_count']
                    
                    # Update text result order modes
                    if 'text_order' in params:
                        task['TextResultOrderModes'] = params['text_order']
            
            # Update parameters in task sections
            if 'BarcodeReaderTaskSettingOptions' in self.current_settings:
                for task in self.current_settings['BarcodeReaderTaskSettingOptions']:
                    if 'SectionArray' in task:
                        for section in task['SectionArray']:
                            section_type = section.get('Section')
                            
                            # Update Region Predetection parameters
                            if section_type == 'ST_REGION_PREDETECTION':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_PREDETECT_REGIONS' and 'RegionPredetectionModes' in stage:
                                        if 'region_predetection' in params:
                                            # Update existing or create new mode
                                            if stage['RegionPredetectionModes']:
                                                stage['RegionPredetectionModes'][0].update(params['region_predetection'])
                                            else:
                                                stage['RegionPredetectionModes'] = [params['region_predetection']]
                            
                            # Update Localization parameters
                            elif section_type == 'ST_BARCODE_LOCALIZATION':
                                for stage in section.get('StageArray', []):
                                    if stage.get('Stage') == 'SST_LOCALIZE_CANDIDATE_BARCODES':
                                        stage['LocalizationModes'] = params['localization_modes']
                            
                            # Update Decoding parameters
                            elif section_type == 'ST_BARCODE_DECODING':
                                for stage in section.get('StageArray', []):
                                    stage_type = stage.get('Stage')
                                    
                                    # Update Deformation Resisting
                                    if stage_type == 'SST_RESIST_DEFORMATION' and 'deformation_config' in params:
                                        if 'DeformationResistingModes' in stage:
                                            if stage['DeformationResistingModes']:
                                                stage['DeformationResistingModes'][0]['Level'] = params['deformation_config']['Level']
                                                stage['DeformationResistingModes'][0]['Mode'] = params['deformation_config']['Mode']
                                    
                                    # Update Barcode Scaling
                                    elif stage_type == 'SST_SCALE_BARCODE_IMAGE' and 'scale_config' in params:
                                        if 'BarcodeScaleModes' in stage:
                                            if stage['BarcodeScaleModes']:
                                                stage['BarcodeScaleModes'][0].update(params['scale_config'])
                                            else:
                                                stage['BarcodeScaleModes'] = [params['scale_config']]
            
            # Update Binarization in Image Parameters
            if 'ImageParameterOptions' in self.current_settings and 'binarization_config' in params:
                for param in self.current_settings['ImageParameterOptions']:
                    if 'ApplicableStages' in param:
                        for stage in param['ApplicableStages']:
                            if 'BinarizationModes' in stage:
                                for bin_mode in stage['BinarizationModes']:
                                    bin_mode.update(params['binarization_config'])
            
            # Update settings and refresh display
            self.update_settings()
            self.update_parameters_display()
            
            # Create comprehensive parameter information display
            param_info = f"🔬 Testing Enhanced Parameters (Combination {self.auto_adjustment_index + 1}/{len(self.auto_adjustment_params)}):\n\n"
            
            param_info += f"� Expected Count: {params['expected_count']} barcode(s)\n"
            
            loc_modes = [mode['Mode'].replace('LM_', '') for mode in params['localization_modes']]
            param_info += f"🎯 Localization: {', '.join(loc_modes)}\n"
            
            if 'binarization_config' in params:
                bin_config = params['binarization_config']
                if bin_config['BlockSizeX'] == 0:
                    param_info += f"🔲 Binarization: {bin_config['Mode']} (Auto Size)\n"
                else:
                    param_info += f"🔲 Binarization: {bin_config['Mode']} ({bin_config['BlockSizeX']}×{bin_config['BlockSizeY']})\n"
            
            if 'region_predetection' in params:
                pred_config = params['region_predetection']
                param_info += f"� Region Detection: {pred_config['Mode']} (Sensitivity: {pred_config['Sensitivity']})\n"
            
            if 'deformation_config' in params:
                deform_config = params['deformation_config']
                if deform_config['Mode'] != 'DRM_SKIP':
                    param_info += f"� Deformation Resist: Level {deform_config['Level']}\n"
            
            if 'scale_config' in params:
                scale_config = params['scale_config']
                if scale_config['Mode'] != 'BSM_SKIP':
                    param_info += f"📏 Barcode Scaling: {scale_config['Mode']}\n"
            
            if 'text_order' in params:
                order_modes = [mode['Mode'].replace('TROM_', '') for mode in params['text_order']]
                param_info += f"*** Result Ordering: {', '.join(order_modes)}\n"
            
            param_info += f"\n⏱️ Running detection...\n"
            
            self.result_text.setPlainText(param_info)
                                        
        except Exception as e:
            print(f"Error applying enhanced auto-adjustment parameters: {e}")
            error_msg = f"❌ Error in combination {self.auto_adjustment_index + 1}: {str(e)}\n"
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
                    # Handle different control types for text property
                    if hasattr(control, 'setCurrentText'):
                        # QComboBox and similar controls
                        control.setCurrentText(default_value)
                    elif hasattr(control, 'setText'):
                        # QLineEdit and similar controls
                        control.setText(str(default_value))
                    else:
                        # Fallback - try both methods
                        try:
                            control.setCurrentText(default_value)
                        except:
                            control.setText(str(default_value))
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