import sys
import os
import json
import csv
import threading
import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, List

import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QScrollArea, QFrame, QSplitter, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QProgressBar, QStatusBar, QFileDialog,
    QMessageBox, QDialog, QRadioButton, QButtonGroup, QDialogButtonBox,
    QTabWidget, QSlider, QLineEdit
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QSize, QRect, QPoint
)
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QPen, QBrush, QColor, QFont, QAction, 
    QDragEnterEvent, QDropEvent, QClipboard, QIcon
)
from dynamsoft_capture_vision_bundle import *

# Try to import memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Constants
LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
CONTOUR_COLORS = [
    (0, 255, 0),    # Green
    (255, 0, 0),    # Blue (BGR format)
    (0, 0, 255),    # Red
    (255, 255, 0),  # Cyan
    (255, 0, 255),  # Magenta
    (0, 255, 255)   # Yellow
]
TEXT_COLOR = (0, 0, 255)     # Red
CONTOUR_THICKNESS = 2
TEXT_THICKNESS = 2
FONT_SCALE = 0.5
TEXT_OFFSET_Y = 10

class MyIntermediateResultReceiver(IntermediateResultReceiver):
    """Enhanced intermediate result receiver for capturing page images."""
    
    def __init__(self, im: IntermediateResultManager):
        self.images = {}
        self.im = im
        super().__init__()

    def on_localized_barcodes_received(self, result: "LocalizedBarcodesUnit", info: IntermediateResultExtraInfo) -> None:
        """Handle localized barcode results and capture images."""
        try:
            hash_id = result.get_original_image_hash_id()
            if hash_id and self.im:
                image = self.im.get_original_image(hash_id)
                
                if image is not None and self.images.get(hash_id) is None:
                    try:
                        image_io = ImageIO()
                        saved = image_io.save_to_numpy(image)
                        if saved is not None:
                            # Handle different return formats
                            if isinstance(saved, tuple) and len(saved) == 3:
                                error_code, error_message, numpy_array = saved
                                if error_code == 0 and numpy_array is not None:
                                    self.images[hash_id] = numpy_array
                            elif isinstance(saved, tuple) and len(saved) == 2:
                                success, numpy_array = saved
                                if success and numpy_array is not None:
                                    self.images[hash_id] = numpy_array
                            else:
                                # Direct numpy array return
                                self.images[hash_id] = saved
                    except Exception:
                        # Silently ignore intermediate result processing errors
                        pass
        except Exception:
            # Silently handle any unexpected errors in the receiver
            pass

class ProcessingWorker(QThread):
    """Worker thread for barcode processing to keep UI responsive."""
    
    # Define signals
    finished = Signal(object)  # Processing results
    error = Signal(str)        # Error message
    progress = Signal(str)     # Progress message
    
    def __init__(self, cvr_instance, file_path):
        super().__init__()
        self.cvr_instance = cvr_instance
        self.file_path = file_path
    
    def run(self):
        """Run barcode detection in background thread."""
        try:
            self.progress.emit("🔍 Starting barcode detection...")
            
            results = self.cvr_instance.capture_multi_pages(
                self.file_path, 
                EnumPresetTemplate.PT_READ_BARCODES.value
            )
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

class ImageDisplayWidget(QLabel):
    """Custom widget for displaying and zooming images with barcode annotations."""
    
    # Define signal for file drop
    file_dropped = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setStyleSheet("border: 2px solid #ccc; background-color: white;")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        
        # Image data
        self.original_image = None
        self.current_pixmap = None
        self.zoom_factor = 1.0
        self.show_annotations = True
        self.barcode_items = []
        
        # Display placeholder
        self.show_placeholder()
    
    def show_placeholder(self):
        """Show placeholder text when no image is loaded."""
        self.setText("🖼️ Drag and drop files here\n\n📁 Supported formats:\n• Images: JPG, PNG, BMP, TIFF, WEBP\n• PDF files (native support)\n\n🖱️ Or click 'Load File' button")
        self.setStyleSheet("border: 2px dashed #ccc; background-color: #f9f9f9; color: #666; font-size: 14px;")
    
    def set_image(self, cv_image, barcode_items=None):
        """Set the image to display with optional barcode annotations."""
        if cv_image is None:
            self.show_placeholder()
            return
        
        self.original_image = cv_image.copy()
        self.barcode_items = barcode_items if barcode_items else []
        self.update_display()
    
    def update_display(self):
        """Update the display with current zoom and annotations."""
        if self.original_image is None:
            return
        
        # Create annotated image if needed
        display_image = self.original_image.copy()
        if self.show_annotations and self.barcode_items:
            display_image = self.draw_barcode_annotations(display_image, self.barcode_items)
        
        # Convert to QPixmap
        height, width, channel = display_image.shape
        bytes_per_line = 3 * width
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        
        q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # Apply zoom
        if self.zoom_factor == 1.0 and hasattr(self, 'parent') and self.parent():
            # Calculate fit zoom based on parent widget size
            parent_size = self.parent().size()
            if parent_size.width() > 50 and parent_size.height() > 50:  # Valid size
                scale_x = (parent_size.width() - 50) / width
                scale_y = (parent_size.height() - 50) / height
                scale = min(scale_x, scale_y, 1.0)  # Don't upscale beyond 100%
                if scale > 0.1:  # Valid scale
                    scaled_size = pixmap.size() * scale
                    pixmap = pixmap.scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif self.zoom_factor != 1.0:
            scaled_size = pixmap.size() * self.zoom_factor
            pixmap = pixmap.scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.current_pixmap = pixmap
        self.setPixmap(pixmap)
        self.resize(pixmap.size())
        self.setStyleSheet("border: 2px solid #ccc; background-color: white;")
    
    def draw_barcode_annotations(self, cv_image, items):
        """Draw barcode detection results on the image."""
        if not items:
            return cv_image
        
        annotated_image = cv_image.copy()
        
        # Adjust annotation parameters based on image size
        height, width = annotated_image.shape[:2]
        font_scale = max(0.3, min(1.0, (width + height) / 2000))
        thickness = max(1, int(2 * (width + height) / 2000))
        
        for i, item in enumerate(items):
            color = CONTOUR_COLORS[i % len(CONTOUR_COLORS)]
            location = item.get_location()
            points = [(int(point.x), int(point.y)) for point in location.points]
            
            # Draw contour
            cv2.drawContours(annotated_image, [np.array(points)], 0, color, thickness)
            
            # Add text label with background
            text = item.get_text()
            if len(text) > 20:  # Truncate long text
                text = text[:17] + "..."
            
            x1, y1 = points[0]
            
            # Calculate text size for background rectangle
            (text_width, text_height), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )
            
            # Draw background rectangle
            cv2.rectangle(annotated_image, 
                         (x1 - 2, y1 - text_height - TEXT_OFFSET_Y - 2),
                         (x1 + text_width + 2, y1 - TEXT_OFFSET_Y + baseline + 2),
                         (255, 255, 255), -1)
            
            # Draw border around background
            cv2.rectangle(annotated_image, 
                         (x1 - 2, y1 - text_height - TEXT_OFFSET_Y - 2),
                         (x1 + text_width + 2, y1 - TEXT_OFFSET_Y + baseline + 2),
                         color, 1)
            
            # Draw text
            cv2.putText(annotated_image, text, (x1, y1 - TEXT_OFFSET_Y),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, TEXT_COLOR, thickness)
            
            # Add barcode number
            cv2.putText(annotated_image, f"#{i+1}", (x1 - 20, y1),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, color, max(1, thickness - 1))
        
        return annotated_image
    
    def set_zoom(self, zoom_factor):
        """Set zoom factor and update display."""
        self.zoom_factor = zoom_factor
        self.update_display()
        
        # Adjust widget size for proper scrolling
        if self.current_pixmap:
            self.resize(self.current_pixmap.size())
    
    def toggle_annotations(self, show):
        """Toggle barcode annotations on/off."""
        self.show_annotations = show
        self.update_display()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any of the URLs are valid file types
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path:
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.pdf']:
                        event.acceptProposedAction()
                        # Change border to indicate drop zone is active
                        self.setStyleSheet("border: 2px dashed #007acc; background-color: #e6f3ff; color: #666; font-size: 14px;")
                        return
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        # Restore normal styling when drag leaves
        if self.original_image is None:
            self.setStyleSheet("border: 2px dashed #ccc; background-color: #f9f9f9; color: #666; font-size: 14px;")
        else:
            self.setStyleSheet("border: 2px solid #ccc; background-color: white;")
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop events."""
        # Restore normal styling
        if self.original_image is None:
            self.setStyleSheet("border: 2px dashed #ccc; background-color: #f9f9f9; color: #666; font-size: 14px;")
        else:
            self.setStyleSheet("border: 2px solid #ccc; background-color: white;")
        
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            # Emit signal with the first dropped file
            self.file_dropped.emit(files[0])
        event.acceptProposedAction()

class ExportFormatDialog(QDialog):
    """Dialog for selecting export format."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Export Format")
        self.setFixedSize(300, 200)
        self.selected_format = None
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Select export format:")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Radio buttons
        self.button_group = QButtonGroup()
        formats = ["Text (.txt)", "CSV (.csv)", "JSON (.json)"]
        
        for i, format_name in enumerate(formats):
            radio = QRadioButton(format_name)
            if i == 0:  # Default to first option
                radio.setChecked(True)
                self.selected_format = i
            self.button_group.addButton(radio, i)
            layout.addWidget(radio)
        
        # Connect button group
        self.button_group.buttonClicked.connect(self.on_format_selected)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def on_format_selected(self, button):
        """Handle format selection."""
        self.selected_format = self.button_group.id(button)
    
    def get_selected_format(self):
        """Get the selected format index."""
        return self.selected_format

class BarcodeReaderMainWindow(QMainWindow):
    """Main window for the PySide6 barcode reader application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamsoft Barcode Reader - PySide6 GUI")
        self.setGeometry(100, 100, 1400, 900)
        self.setAcceptDrops(True)  # Enable drag-and-drop for main window
        
        # Initialize variables
        self.cvr_instance = None
        self.custom_receiver = None
        self.current_file_path = None
        self.current_pages = {}  # Store page data {page_index: cv_image}
        self.page_hash_mapping = {}  # Map page_index to hash_id
        self.current_page_index = 0
        self.page_results = {}  # Store barcode results for each page
        self.is_processing = False
        self.process_start_time = None
        
        # Setup UI
        self.setup_ui()
        self.setup_status_bar()
        self.setup_menu_bar()
        
        # Initialize Dynamsoft
        self.initialize_license()
    
    def setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Control panel (left)
        self.control_panel = self.create_control_panel()
        splitter.addWidget(self.control_panel)
        
        # Image display (center)
        self.image_display = self.create_image_display_panel()
        splitter.addWidget(self.image_display)
        
        # Results panel (right)
        self.results_panel = self.create_results_panel()
        splitter.addWidget(self.results_panel)
        
        # Set initial sizes
        splitter.setSizes([300, 600, 400])
    
    def create_control_panel(self):
        """Create the control panel with file operations and settings."""
        panel = QWidget()
        panel.setMaximumWidth(320)
        layout = QVBoxLayout(panel)
        
        # File Controls Group
        file_group = QGroupBox("📁 File Controls")
        file_layout = QVBoxLayout(file_group)
        
        # Load file button
        self.load_button = QPushButton("📂 Load File")
        self.load_button.setMinimumHeight(35)
        self.load_button.clicked.connect(self.load_file)
        file_layout.addWidget(self.load_button)
        
        # File info
        info_group = QGroupBox("File Information")
        info_layout = QVBoxLayout(info_group)
        
        self.file_info_label = QLabel("No file loaded")
        self.file_info_label.setWordWrap(True)
        self.file_info_label.setStyleSheet("font-size: 11px;")
        info_layout.addWidget(self.file_info_label)
        
        self.file_size_label = QLabel("")
        self.file_size_label.setStyleSheet("font-size: 10px; color: gray;")
        info_layout.addWidget(self.file_size_label)
        
        file_layout.addWidget(info_group)
        layout.addWidget(file_group)
        
        # Page Navigation Group
        self.nav_group = QGroupBox("📄 Page Navigation")
        nav_layout = QVBoxLayout(self.nav_group)
        
        # Navigation buttons
        nav_buttons_layout = QHBoxLayout()
        self.prev_button = QPushButton("◀ Prev")
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.prev_page)
        nav_buttons_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next ▶")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.next_page)
        nav_buttons_layout.addWidget(self.next_button)
        
        nav_layout.addLayout(nav_buttons_layout)
        
        # Page label
        self.page_label = QLabel("Page: 0/0")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        nav_layout.addWidget(self.page_label)
        
        # Page jump
        jump_layout = QHBoxLayout()
        jump_layout.addWidget(QLabel("Go to page:"))
        self.page_entry = QSpinBox()
        self.page_entry.setMinimum(1)
        self.page_entry.valueChanged.connect(self.jump_to_page)
        jump_layout.addWidget(self.page_entry)
        nav_layout.addLayout(jump_layout)
        
        self.nav_group.hide()  # Hidden initially
        layout.addWidget(self.nav_group)
        
        # Processing Controls Group
        process_group = QGroupBox("🔍 Barcode Detection")
        process_layout = QVBoxLayout(process_group)
        
        self.process_button = QPushButton("🔍 Detect Barcodes")
        self.process_button.setMinimumHeight(35)
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_current_file)
        process_layout.addWidget(self.process_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        process_layout.addWidget(self.progress_bar)
        
        # Processing options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.auto_process_check = QCheckBox("Auto-process on load")
        self.auto_process_check.setChecked(True)
        options_layout.addWidget(self.auto_process_check)
        
        self.show_confidence_check = QCheckBox("Show confidence")
        self.show_confidence_check.setChecked(False)
        options_layout.addWidget(self.show_confidence_check)
        
        self.show_annotations_check = QCheckBox("Show annotations")
        self.show_annotations_check.setChecked(True)
        self.show_annotations_check.toggled.connect(self.toggle_annotations)
        options_layout.addWidget(self.show_annotations_check)
        
        process_layout.addWidget(options_group)
        layout.addWidget(process_group)
        
        # Actions Group
        actions_group = QGroupBox("⚡ Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.export_button = QPushButton("💾 Export Results")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_results)
        actions_layout.addWidget(self.export_button)
        
        self.copy_button = QPushButton("📋 Copy to Clipboard")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        actions_layout.addWidget(self.copy_button)
        
        clear_button = QPushButton("🗑️ Clear All")
        clear_button.clicked.connect(self.clear_all)
        actions_layout.addWidget(clear_button)
        
        layout.addWidget(actions_group)
        
        # PDF Support info
        pdf_info = QLabel("✅ Native PDF support enabled\nvia Dynamsoft SDK")
        pdf_info.setStyleSheet("color: green; font-size: 10px;")
        pdf_info.setWordWrap(True)
        layout.addWidget(pdf_info)
        
        layout.addStretch()
        return panel
    
    def create_image_display_panel(self):
        """Create the image display panel with zoom controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Zoom controls
        toolbar_layout.addWidget(QLabel("Zoom:"))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["25%", "50%", "75%", "100%", "125%", "150%", "200%", "Fit"])
        self.zoom_combo.setCurrentText("Fit")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_change)
        toolbar_layout.addWidget(self.zoom_combo)
        
        zoom_in_btn = QPushButton("🔍+")
        zoom_in_btn.setMaximumWidth(40)
        zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("🔍-")
        zoom_out_btn.setMaximumWidth(40)
        zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar_layout.addWidget(zoom_out_btn)
        
        reset_btn = QPushButton("↻")
        reset_btn.setMaximumWidth(40)
        reset_btn.clicked.connect(self.reset_view)
        toolbar_layout.addWidget(reset_btn)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Image display area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)  # Don't auto-resize widget
        scroll_area.setAlignment(Qt.AlignCenter)
        scroll_area.setMinimumSize(400, 300)
        
        self.image_widget = ImageDisplayWidget()
        self.image_widget.setMinimumSize(400, 300)
        # Connect drag-and-drop signal
        self.image_widget.file_dropped.connect(self.load_file_path)
        scroll_area.setWidget(self.image_widget)
        
        layout.addWidget(scroll_area)
        
        return panel
    
    def create_results_panel(self):
        """Create the results panel for displaying barcode detection results."""
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        
        # Results header
        header_layout = QHBoxLayout()
        self.results_summary = QLabel("Total Barcodes: 0")
        self.results_summary.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.results_summary)
        
        self.page_summary = QLabel("")
        self.page_summary.setStyleSheet("font-size: 10px; color: gray;")
        header_layout.addWidget(self.page_summary)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.results_text)
        
        return panel
    
    def setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Main status message
        self.status_bar.showMessage("Ready")
        
        # Processing time label
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: gray; font-size: 10px;")
        self.status_bar.addPermanentWidget(self.time_label)
        
        # Memory usage (if available)
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label = QLabel(f"Memory: {memory_mb:.1f} MB")
            self.memory_label.setStyleSheet("color: gray; font-size: 10px;")
            self.status_bar.addPermanentWidget(self.memory_label)
    
    def setup_menu_bar(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        zoom_fit_action = QAction("Zoom to Fit", self)
        zoom_fit_action.setShortcut("Ctrl+0")
        zoom_fit_action.triggered.connect(self.reset_view)
        view_menu.addAction(zoom_fit_action)
        
        zoom_actual_action = QAction("Actual Size", self)
        zoom_actual_action.setShortcut("Ctrl+1")
        zoom_actual_action.triggered.connect(lambda: self.set_zoom("100%"))
        view_menu.addAction(zoom_actual_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def initialize_license(self):
        """Initialize the Dynamsoft license."""
        try:
            error_code, error_message = LicenseManager.init_license(LICENSE_KEY)
            
            if error_code == EnumErrorCode.EC_OK or error_code == EnumErrorCode.EC_LICENSE_CACHE_USED:
                self.cvr_instance = CaptureVisionRouter()
                intermediate_result_manager = self.cvr_instance.get_intermediate_result_manager()
                self.custom_receiver = MyIntermediateResultReceiver(intermediate_result_manager)
                intermediate_result_manager.add_result_receiver(self.custom_receiver)
                self.log_message("✅ License initialized successfully!")
            else:
                self.log_message(f"❌ License initialization failed: {error_code}, {error_message}")
                QMessageBox.critical(self, "License Error", f"Failed to initialize license: {error_message}")
        except Exception as e:
            self.log_message(f"❌ Error initializing license: {e}")
            QMessageBox.critical(self, "Error", f"Failed to initialize: {e}")
    
    def log_message(self, message):
        """Log a message to status bar and results panel."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Update status bar
        self.status_bar.showMessage(message)
        
        # Add to results panel with HTML formatting
        self.results_text.append(f'<span style="color: gray; font-size: 10px;">{formatted_message}</span>')
    
    def load_file(self):
        """Open file dialog to load an image or PDF."""
        file_types = "All Supported (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp *.pdf);;Image files (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp);;PDF files (*.pdf);;All files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image or PDF file",
            "",
            file_types
        )
        
        if file_path:
            self.load_file_path(file_path)
    
    def load_file_path(self, file_path):
        """Load a file from the given path."""
        try:
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "Error", f"File not found: {file_path}")
                return
            
            self.log_message(f"📂 Loading file: {os.path.basename(file_path)}")
            
            self.current_file_path = file_path
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            file_size = os.path.getsize(file_path)
            
            # Update file info
            self.file_info_label.setText(f"📄 {file_name}")
            size_text = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
            self.file_size_label.setText(f"Size: {size_text}")
            
            # Clear previous data
            self.current_pages = {}
            self.page_hash_mapping = {}
            self.page_results = {}
            self.current_page_index = 0
            
            # Clear custom receiver images
            if self.custom_receiver:
                self.custom_receiver.images.clear()
            
            if file_ext == '.pdf':
                self.load_pdf_file(file_path)
            else:
                self.load_single_image(file_path)
            
            self.process_button.setEnabled(True)
            
            # Auto-process if enabled
            if self.auto_process_check.isChecked():
                QTimer.singleShot(100, self.process_current_file)  # Small delay
            
        except Exception as e:
            self.log_message(f"❌ Error loading file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
    
    def load_single_image(self, file_path):
        """Load a single image file."""
        try:
            # Load image
            cv_image = cv2.imread(file_path)
            if cv_image is None:
                raise ValueError("Could not load image - invalid format or corrupted file")
            
            self.current_pages = {0: cv_image}
            self.image_widget.set_image(cv_image)
            
            # Hide navigation for single images
            self.nav_group.hide()
            
            self.log_message(f"✅ Loaded image: {cv_image.shape[1]}x{cv_image.shape[0]} pixels")
            
        except Exception as e:
            raise Exception(f"Failed to load image: {e}")
    
    def load_pdf_file(self, file_path):
        """Load PDF file using Dynamsoft SDK."""
        try:
            self.log_message("📄 Loading PDF file...")
            
            # Clear previous intermediate result images
            if self.custom_receiver:
                self.custom_receiver.images.clear()
            
            # Set the PDF file path
            self.current_pages = {}  # Will be populated after processing
            self.current_page_index = 0
            
            # Show placeholder message
            self.image_widget.setText("📄 PDF File Loaded\n\n🔍 Click 'Detect Barcodes' to process\nand view PDF pages\n\nDynamsoft SDK will automatically\nconvert PDF pages during processing")
            self.image_widget.setStyleSheet("border: 2px solid #ccc; background-color: #f9f9f9; color: #666; font-size: 14px;")
            
            self.log_message("✅ PDF file loaded - process to view pages")
            
        except Exception as e:
            raise Exception(f"Failed to load PDF: {e}")
    
    def process_current_file(self):
        """Process the current file for barcode detection."""
        if not self.current_file_path or self.is_processing:
            return
        
        self.is_processing = True
        self.process_button.setEnabled(False)
        self.process_button.setText("🔄 Processing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Clear previous results
        self.page_results = {}
        self.page_hash_mapping = {}
        if self.custom_receiver:
            self.custom_receiver.images.clear()
        
        # Record start time
        self.process_start_time = datetime.datetime.now()
        
        self.log_message("🔍 Starting barcode detection...")
        
        # Create and start worker thread
        self.worker = ProcessingWorker(self.cvr_instance, self.current_file_path)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.progress.connect(self.log_message)
        self.worker.start()
    
    def on_processing_finished(self, results):
        """Handle completion of barcode processing."""
        try:
            self.page_results = {}
            self.page_hash_mapping = {}
            total_barcodes = 0
            
            result_list = results.get_results()
            
            # Build the page mapping from results to maintain correct order
            for i, result in enumerate(result_list):
                if result.get_error_code() == EnumErrorCode.EC_OK:
                    hash_id = result.get_original_image_hash_id()
                    items = result.get_items()
                    
                    # Map page index to hash_id and store results
                    page_index = i
                    self.page_hash_mapping[page_index] = hash_id
                    self.page_results[page_index] = items
                    total_barcodes += len(items)
                else:
                    self.log_message(f"⚠️ Error on page {i+1}: {result.get_error_string()}")
            
            # Extract pages from intermediate receiver for PDF files
            if self.current_file_path and self.current_file_path.lower().endswith('.pdf'):
                self.extract_pdf_pages_from_receiver()
            
            # Setup navigation for multi-page PDFs
            if len(self.current_pages) > 1:
                self.nav_group.show()
                self.update_navigation_state()
            else:
                self.nav_group.hide()
            
            # Calculate processing time
            process_time = (datetime.datetime.now() - self.process_start_time).total_seconds()
            
            # Update UI
            self.results_summary.setText(f"Total Barcodes: {total_barcodes}")
            self.display_current_page()
            self.display_page_results()
            
            # Enable export buttons if barcodes found
            has_results = total_barcodes > 0
            self.export_button.setEnabled(has_results)
            self.copy_button.setEnabled(has_results)
            
            # Update time display
            self.time_label.setText(f"Processing time: {process_time:.2f}s")
            
            self.log_message(f"✅ Processing complete! Found {total_barcodes} barcode(s) in {process_time:.2f}s")
            
        except Exception as e:
            self.on_processing_error(str(e))
        finally:
            self.is_processing = False
            self.process_button.setEnabled(True)
            self.process_button.setText("🔍 Detect Barcodes")
            self.progress_bar.setVisible(False)
    
    def on_processing_error(self, error_message):
        """Handle processing errors."""
        self.log_message(f"❌ Processing error: {error_message}")
        QMessageBox.critical(self, "Processing Error", f"Failed to process file: {error_message}")
        
        self.is_processing = False
        self.process_button.setEnabled(True)
        self.process_button.setText("🔍 Detect Barcodes")
        self.progress_bar.setVisible(False)
    
    def extract_pdf_pages_from_receiver(self):
        """Extract PDF pages from the intermediate result receiver."""
        if not self.custom_receiver or not self.custom_receiver.images:
            return
        
        # Clear current pages
        self.current_pages = {}
        
        # Extract pages using the correct hash_id order from page_hash_mapping
        for page_index in sorted(self.page_hash_mapping.keys()):
            hash_id = self.page_hash_mapping[page_index]
            if hash_id in self.custom_receiver.images:
                numpy_image = self.custom_receiver.images[hash_id]
                if numpy_image is not None:
                    try:
                        # Convert from numpy array to OpenCV format if needed
                        if hasattr(numpy_image, 'shape') and len(numpy_image.shape) == 3:
                            self.current_pages[page_index] = numpy_image
                        elif hasattr(numpy_image, 'shape'):
                            self.current_pages[page_index] = numpy_image
                        else:
                            self.log_message(f"⚠️ Unexpected image format for page {page_index}")
                    except Exception as e:
                        self.log_message(f"⚠️ Error processing page {page_index}: {e}")
                        continue
        
        # Set the first page as current
        if self.current_pages:
            self.current_page_index = 0
            self.log_message(f"✅ Extracted {len(self.current_pages)} page(s) from PDF in correct order")
        else:
            self.log_message("⚠️ No pages extracted from PDF")
    
    def display_current_page(self):
        """Display the current page with annotations."""
        if self.current_page_index not in self.current_pages:
            return
        
        cv_image = self.current_pages[self.current_page_index]
        barcode_items = self.page_results.get(self.current_page_index, [])
        
        self.image_widget.set_image(cv_image, barcode_items)
        self.display_page_results()
    
    def display_page_results(self):
        """Display barcode results for the current page."""
        self.results_text.clear()
        
        if self.current_page_index not in self.page_results:
            self.results_text.append("No barcode results for this page.")
            self.page_summary.setText("")
            return
        
        items = self.page_results[self.current_page_index]
        
        if not items:
            self.results_text.append("No barcodes found on this page.")
            self.page_summary.setText("")
            return
        
        # Update page summary
        self.page_summary.setText(f"Page {self.current_page_index + 1}: {len(items)} barcode(s)")
        
        # Format results with HTML
        html_content = f'<h3 style="color: #1E3A8A; background-color: #F0F8FF;">📄 PAGE {self.current_page_index + 1} RESULTS</h3>'
        html_content += '<hr style="border: 1px solid #ccc;">'
        
        for i, item in enumerate(items, 1):
            format_type = item.get_format_string()
            text = item.get_text()
            
            html_content += f'<div style="margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #007acc;">'
            html_content += f'<h4 style="color: #DC2626; margin: 0;">📊 BARCODE #{i:02d}</h4>'
            html_content += f'<p style="margin: 5px 0;"><b>📋 Format:</b> <span style="color: #7C2D12;">{format_type}</span></p>'
            html_content += f'<p style="margin: 5px 0;"><b>💬 Content:</b> <span style="color: #15803D; font-family: monospace;">"{text}"</span></p>'
            
            # Confidence if available and enabled
            if self.show_confidence_check.isChecked():
                try:
                    confidence = item.get_confidence()
                    if confidence is not None:
                        html_content += f'<p style="margin: 5px 0;"><b>📊 Confidence:</b> <span style="color: #7C2D12;">{confidence}/100</span></p>'
                except:
                    pass
            
            # Location points
            location = item.get_location()
            points = location.points
            if len(points) >= 4:
                point_labels = ["TL", "TR", "BR", "BL"]
                points_text = " → ".join([f"{label}({int(p.x)},{int(p.y)})" for p, label in zip(points[:4], point_labels)])
            else:
                points_text = " → ".join([f"({int(p.x)},{int(p.y)})" for p in points])
            
            html_content += f'<p style="margin: 5px 0;"><b>📍 Location:</b> <span style="color: #1E40AF; font-family: monospace; font-size: 10px;">{points_text}</span></p>'
            
            # Area calculation
            try:
                points_coords = [(p.x, p.y) for p in location.points]
                area = self.calculate_polygon_area(points_coords)
                if area > 10000:
                    area_text = f"{area:,.0f} px² ({area/10000:.1f}k px²)"
                else:
                    area_text = f"{area:.0f} px²"
                html_content += f'<p style="margin: 5px 0;"><b>📐 Area:</b> <span style="color: #1E40AF; font-family: monospace;">{area_text}</span></p>'
            except:
                pass
            
            html_content += '</div>'
        
        html_content += f'<div style="margin-top: 15px; text-align: center; color: #059669; font-weight: bold;">✨ Found {len(items)} barcode(s) on this page</div>'
        
        self.results_text.setHtml(html_content)
    
    def calculate_polygon_area(self, points):
        """Calculate the area of a polygon using the shoelace formula."""
        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return abs(area) / 2.0
    
    def prev_page(self):
        """Navigate to previous page."""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_current_page()
            self.update_navigation_state()
    
    def next_page(self):
        """Navigate to next page."""
        if self.current_page_index < len(self.current_pages) - 1:
            self.current_page_index += 1
            self.display_current_page()
            self.update_navigation_state()
    
    def jump_to_page(self, page_num):
        """Jump to a specific page number."""
        if 1 <= page_num <= len(self.current_pages):
            self.current_page_index = page_num - 1
            self.display_current_page()
            self.update_navigation_state()
    
    def update_navigation_state(self):
        """Update navigation button states and page label."""
        total_pages = len(self.current_pages)
        current = self.current_page_index + 1
        
        self.page_label.setText(f"Page: {current}/{total_pages}")
        self.page_entry.setMaximum(total_pages)
        self.page_entry.setValue(current)
        
        self.prev_button.setEnabled(self.current_page_index > 0)
        self.next_button.setEnabled(self.current_page_index < total_pages - 1)
    
    def on_zoom_change(self, zoom_text):
        """Handle zoom level change."""
        if zoom_text == "Fit":
            # Let the image widget calculate fit zoom
            zoom_factor = 1.0  # Will be calculated in ImageDisplayWidget
        else:
            zoom_factor = int(zoom_text.rstrip('%')) / 100.0
        
        self.image_widget.set_zoom(zoom_factor)
    
    def zoom_in(self):
        """Zoom in by 25%."""
        current_text = self.zoom_combo.currentText()
        if current_text == "Fit":
            self.zoom_combo.setCurrentText("100%")
        else:
            current_zoom = int(current_text.rstrip('%'))
            new_zoom = min(current_zoom + 25, 500)  # Max 500%
            self.zoom_combo.setCurrentText(f"{new_zoom}%")
    
    def zoom_out(self):
        """Zoom out by 25%."""
        current_text = self.zoom_combo.currentText()
        if current_text == "Fit":
            self.zoom_combo.setCurrentText("75%")
        else:
            current_zoom = int(current_text.rstrip('%'))
            new_zoom = max(current_zoom - 25, 10)  # Min 10%
            self.zoom_combo.setCurrentText(f"{new_zoom}%")
    
    def reset_view(self):
        """Reset zoom to fit."""
        self.zoom_combo.setCurrentText("Fit")
    
    def set_zoom(self, zoom_text):
        """Set specific zoom level."""
        self.zoom_combo.setCurrentText(zoom_text)
    
    def toggle_annotations(self, show):
        """Toggle barcode annotations on/off."""
        self.image_widget.toggle_annotations(show)
    
    def export_results(self):
        """Export barcode results to a file."""
        if not self.page_results:
            QMessageBox.warning(self, "No Results", "No barcode results to export.")
            return
        
        # Show export format dialog
        dialog = ExportFormatDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        
        format_index = dialog.get_selected_format()
        extensions = [".txt", ".csv", ".json"]
        format_names = ["Text", "CSV", "JSON"]
        
        ext = extensions[format_index]
        format_name = format_names[format_index]
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            f"barcode_results{ext}",
            f"{format_name} files (*{ext});;All files (*.*)"
        )
        
        if file_path:
            try:
                if ext == ".txt":
                    self.export_to_text(file_path)
                elif ext == ".csv":
                    self.export_to_csv(file_path)
                elif ext == ".json":
                    self.export_to_json(file_path)
                
                self.log_message(f"💾 Results exported to: {os.path.basename(file_path)}")
                QMessageBox.information(self, "Export Complete", f"Results exported successfully to:\n{file_path}")
                
            except Exception as e:
                self.log_message(f"❌ Export error: {e}")
                QMessageBox.critical(self, "Export Error", f"Failed to export results: {e}")
    
    def export_to_text(self, file_path):
        """Export results to text file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Dynamsoft Barcode Reader - Detection Results\n")
            f.write("=" * 60 + "\n")
            f.write(f"Source File: {self.current_file_path}\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            total_barcodes = 0
            for page_index in sorted(self.page_results.keys()):
                items = self.page_results[page_index]
                f.write(f"Page {page_index + 1}:\n")
                f.write("-" * 20 + "\n")
                
                if not items:
                    f.write("No barcodes found.\n\n")
                    continue
                
                for i, item in enumerate(items, 1):
                    format_type = item.get_format_string()
                    text = item.get_text()
                    
                    f.write(f"Barcode {i}:\n")
                    f.write(f"  Format: {format_type}\n")
                    f.write(f"  Text: {text}\n")
                    
                    location = item.get_location()
                    f.write("  Location Points:\n")
                    for j, point in enumerate(location.points):
                        f.write(f"    Point {j+1}: ({int(point.x)}, {int(point.y)})\n")
                    f.write("\n")
                    
                    total_barcodes += 1
                
                f.write("\n")
            
            f.write(f"Total Barcodes Found: {total_barcodes}\n")
    
    def export_to_csv(self, file_path):
        """Export results to CSV file."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Page', 'Barcode_Number', 'Format', 'Text', 'X1', 'Y1', 'X2', 'Y2', 'X3', 'Y3', 'X4', 'Y4'])
            
            for page_index in sorted(self.page_results.keys()):
                items = self.page_results[page_index]
                
                for i, item in enumerate(items, 1):
                    format_type = item.get_format_string()
                    text = item.get_text()
                    location = item.get_location()
                    
                    points = [int(p.x) for p in location.points] + [int(p.y) for p in location.points]
                    row = [page_index + 1, i, format_type, text] + points[:8]  # Limit to 4 points
                    writer.writerow(row)
    
    def export_to_json(self, file_path):
        """Export results to JSON file."""
        export_data = {
            "source_file": self.current_file_path,
            "export_time": datetime.datetime.now().isoformat(),
            "total_pages": len(self.current_pages),
            "pages": []
        }
        
        for page_index in sorted(self.page_results.keys()):
            items = self.page_results[page_index]
            
            page_data = {
                "page_number": page_index + 1,
                "barcode_count": len(items),
                "barcodes": []
            }
            
            for i, item in enumerate(items, 1):
                format_type = item.get_format_string()
                text = item.get_text()
                location = item.get_location()
                
                barcode_data = {
                    "barcode_number": i,
                    "format": format_type,
                    "text": text,
                    "location": {
                        "points": [{"x": int(p.x), "y": int(p.y)} for p in location.points]
                    }
                }
                
                page_data["barcodes"].append(barcode_data)
            
            export_data["pages"].append(page_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def copy_to_clipboard(self):
        """Copy barcode results to clipboard."""
        if not self.page_results:
            QMessageBox.warning(self, "No Results", "No barcode results to copy.")
            return
        
        try:
            # Generate text summary
            text_content = []
            for page_index in sorted(self.page_results.keys()):
                items = self.page_results[page_index]
                if items:
                    text_content.append(f"Page {page_index + 1}:")
                    for i, item in enumerate(items, 1):
                        text_content.append(f"  {i}. [{item.get_format_string()}] {item.get_text()}")
                    text_content.append("")
            
            clipboard_text = "\n".join(text_content)
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text)
            
            self.log_message("📋 Results copied to clipboard")
            QMessageBox.information(self, "Copied", "Barcode results copied to clipboard!")
            
        except Exception as e:
            self.log_message(f"❌ Clipboard error: {e}")
            QMessageBox.critical(self, "Clipboard Error", f"Failed to copy to clipboard: {e}")
    
    def clear_all(self):
        """Clear all data and reset the application."""
        reply = QMessageBox.question(self, "Clear All", "Are you sure you want to clear all data?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.current_file_path = None
            self.current_pages = {}
            self.page_hash_mapping = {}
            self.page_results = {}
            self.current_page_index = 0
            
            # Clear custom receiver
            if self.custom_receiver:
                self.custom_receiver.images.clear()
            
            # Clear UI
            self.image_widget.show_placeholder()
            self.results_text.clear()
            self.results_summary.setText("Total Barcodes: 0")
            self.page_summary.setText("")
            self.file_info_label.setText("No file loaded")
            self.file_size_label.setText("")
            self.time_label.setText("")
            
            # Reset buttons
            self.process_button.setEnabled(False)
            self.export_button.setEnabled(False)
            self.copy_button.setEnabled(False)
            
            # Hide navigation
            self.nav_group.hide()
            
            # Reset zoom
            self.zoom_combo.setCurrentText("Fit")
            
            self.log_message("🗑️ Application reset")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About", 
                         "Dynamsoft Barcode Reader - PySide6 GUI\n\n"
                         "A modern Qt-based interface for barcode detection\n"
                         "using the Dynamsoft Capture Vision SDK.\n\n"
                         "Features:\n"
                         "• Multi-format support (Images & PDF)\n"
                         "• Real-time visual annotations\n"
                         "• Export capabilities (TXT, CSV, JSON)\n"
                         "• Professional user interface")
    
    def closeEvent(self, event):
        """Handle application close event."""
        reply = QMessageBox.question(self, "Quit", "Do you want to quit the Barcode Reader?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Stop any running worker threads
            if hasattr(self, 'worker') and self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait()
            event.accept()
        else:
            event.ignore()

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Dynamsoft Barcode Reader")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Dynamsoft")
    
    # Set application style
    app.setStyle('Fusion')  # Modern look
    
    # Create and show main window
    window = BarcodeReaderMainWindow()
    window.show()
    
    print("🚀 Starting Dynamsoft Barcode Reader PySide6 GUI...")
    print("📁 Supported formats: JPG, PNG, BMP, TIFF, WEBP, PDF")
    print("✨ Modern Qt interface with advanced features")
    
    # Start the application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
