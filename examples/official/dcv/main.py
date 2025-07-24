import sys
import os
import json
import csv
import threading
import datetime
import queue
import time
import os
import queue
import datetime
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, List

import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QScrollArea, QFrame, QSplitter, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QProgressBar, QStatusBar, QFileDialog,
    QMessageBox, QDialog, QRadioButton, QButtonGroup, QDialogButtonBox,
    QTabWidget, QSlider, QLineEdit, QInputDialog
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QSize, QRect, QPoint, QMutex, QMutexLocker, QUrl
)
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QPen, QBrush, QColor, QFont, QAction, 
    QDragEnterEvent, QDropEvent, QClipboard, QIcon, QDesktopServices
)
from PySide6.QtMultimedia import QCamera, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget
from dynamsoft_capture_vision_bundle import (
    LicenseManager, CaptureVisionRouter, EnumPresetTemplate, EnumErrorCode,
    IntermediateResultReceiver, IntermediateResultManager, CapturedResultReceiver,
    EnumCapturedResultItemType, ImageSourceAdapter, ParsedResultItem,
    EnumValidationStatus, LocalizedBarcodesUnit, IntermediateResultExtraInfo,
    ImageIO
)
from utils import convertMat2ImageData

# Try to import memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Constants
LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="

# Detection modes
DETECTION_MODES = {
    "Barcode": {
        "template": EnumPresetTemplate.PT_READ_BARCODES.value,
        "description": "Detect barcodes and QR codes"
    },
    "Document": {
        "template": EnumPresetTemplate.PT_DETECT_AND_NORMALIZE_DOCUMENT.value,
        "description": "Detect and normalize documents"
    },
    "MRZ": {
        "template": "ReadPassportAndId",
        "description": "Read passport and ID cards (MRZ)"
    }
}

# Global license initialization - called once at startup
_LICENSE_INITIALIZED = False

def initialize_license_once():
    """Initialize Dynamsoft license globally, only once."""
    global _LICENSE_INITIALIZED
    if not _LICENSE_INITIALIZED:
        try:
            error_code, error_message = LicenseManager.init_license(LICENSE_KEY)
            if error_code == EnumErrorCode.EC_OK or error_code == EnumErrorCode.EC_LICENSE_CACHE_USED:
                _LICENSE_INITIALIZED = True
                print("✅ Dynamsoft license initialized successfully!")
                return True
            else:
                print(f"❌ License initialization failed: {error_code}, {error_message}")
                return False
        except Exception as e:
            print(f"❌ Error initializing license: {e}")
            return False
    return True
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

# Fixed color assignment for consistent barcode detection visualization
BARCODE_COLORS = {}  # Will store {barcode_text: color_index} for consistent colors
BARCODE_LAST_SEEN = {}  # Track when each barcode was last detected

def cleanup_old_barcode_colors():
    """Remove barcode colors for barcodes not seen recently."""
    import time
    current_time = time.time()
    expired_barcodes = []
    
    for barcode_text, last_seen in BARCODE_LAST_SEEN.items():
        if current_time - last_seen > 10:  # Remove after 10 seconds
            expired_barcodes.append(barcode_text)
    
    for barcode_text in expired_barcodes:
        BARCODE_COLORS.pop(barcode_text, None)
        BARCODE_LAST_SEEN.pop(barcode_text, None)

class FrameFetcher(ImageSourceAdapter):
    """Frame fetcher for camera input using Dynamsoft SDK."""
    
    def __init__(self):
        super().__init__()
        
    def has_next_image_to_fetch(self) -> bool:
        return True

    def add_frame(self, imageData):
        """Add frame to the buffer for processing."""
        self.add_image_to_buffer(imageData)


class CameraCapturedResultReceiver(CapturedResultReceiver):
    """Result receiver for camera barcode detection."""
    
    def __init__(self, result_queue):
        super().__init__()
        self.result_queue = result_queue

    def on_captured_result_received(self, result):
        """Handle captured barcode results from camera."""
        try:
            self.result_queue.put(result)
        except Exception as e:
            print(f"Error handling camera result: {e}")


class CameraWidget(QWidget):
    """Widget for camera display and real-time barcode detection."""
    
    # Signals
    barcodes_detected = Signal(list)  # List of detected barcodes
    frame_processed = Signal(object)  # Processed frame with annotations
    error_occurred = Signal(str)     # Error message
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        
        # Camera variables
        self.camera = None
        self.current_camera_device = None
        self.camera_running = False
        self.opencv_capture = None
        
        # Dynamsoft SDK variables
        self.cvr_instance = None
        self.frame_fetcher = None
        self.camera_receiver = None
        self.result_queue = queue.Queue()
        
        # Frame processing
        self.current_frame = None
        self.annotated_frame = None
        self.frame_mutex = QMutex()
        self.detection_enabled = True
        self._current_barcode_items = []  # Store current detection results for live overlay
        
        import time
        self._last_detection_time = time.time()  # Initialize with current time to prevent issues
        
        # Detection mode
        self.current_detection_mode = "Barcode"  # Default to barcode detection
        
        # UI Setup
        self.setup_ui()
        
        # Timer for frame updates
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self.update_frame)
        
        # Timer for processing results
        self.result_timer = QTimer()
        self.result_timer.timeout.connect(self.process_detection_results)
        
        # Initialize available cameras
        self.update_camera_list()
    
    def setup_ui(self):
        """Setup camera widget UI."""
        layout = QVBoxLayout(self)
        
        # Camera display
        self.camera_label = QLabel("📷 Camera View")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                background-color: #f0f0f0;
                color: #666;
                font-size: 16px;
            }
        """)
        layout.addWidget(self.camera_label)
        
        # Camera controls
        controls_layout = QHBoxLayout()
        
        # Camera selection
        controls_layout.addWidget(QLabel("Camera:"))
        self.camera_combo = QComboBox()
        self.camera_combo.currentIndexChanged.connect(self.change_camera)
        controls_layout.addWidget(self.camera_combo)
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("📷 Start Camera")
        self.start_stop_btn.clicked.connect(self.toggle_camera)
        controls_layout.addWidget(self.start_stop_btn)
        
        # Detection toggle
        self.detection_check = QCheckBox("Real-time Detection")
        self.detection_check.setChecked(True)
        self.detection_check.toggled.connect(self.toggle_detection)
        controls_layout.addWidget(self.detection_check)
        
        # Capture button
        self.capture_btn = QPushButton("📸 Capture")
        self.capture_btn.setEnabled(False)
        self.capture_btn.clicked.connect(self.capture_frame)
        controls_layout.addWidget(self.capture_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Status
        self.camera_status = QLabel("Camera: Stopped")
        self.camera_status.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.camera_status)
    
    def update_camera_list(self):
        """Update the list of available cameras."""
        self.camera_combo.clear()
        
        # Get available cameras
        cameras = QMediaDevices.videoInputs()
        if cameras:
            for i, camera in enumerate(cameras):
                self.camera_combo.addItem(f"Camera {i}: {camera.description()}")
        else:
            self.camera_combo.addItem("No cameras found")
    
    def initialize_dynamsoft_camera(self, cvr_instance):
        """Initialize Dynamsoft SDK for camera processing (non-blocking)."""
        # Start initialization in background to avoid UI freeze
        QTimer.singleShot(50, self._init_camera_background)
        return True
    
    def _init_camera_background(self):
        """Background initialization to prevent UI freezing."""
        try:
            # Stop any existing capture first
            if self.cvr_instance:
                try:
                    self.cvr_instance.stop_capturing()
                    if self.camera_receiver:
                        self.cvr_instance.remove_result_receiver(self.camera_receiver)
                except:
                    pass
            
            # Create a new CVR instance for camera mode to avoid conflicts
            self.cvr_instance = CaptureVisionRouter()
            
            # License is already initialized globally - no need to reinitialize
            
            self.frame_fetcher = FrameFetcher()
            self.cvr_instance.set_input(self.frame_fetcher)
            
            # Create result receiver
            self.camera_receiver = CameraCapturedResultReceiver(self.result_queue)
            self.cvr_instance.add_result_receiver(self.camera_receiver)
            
            # Start capturing with current detection mode
            template = DETECTION_MODES[self.current_detection_mode]["template"]
            error_code, error_msg = self.cvr_instance.start_capturing(template)
            
            if error_code != EnumErrorCode.EC_OK:
                print(f"Barcode detection start warning: {error_msg}")
                
        except Exception as e:
            print(f"Camera initialization warning: {e}")
    
    def toggle_camera(self):
        """Start or stop the camera."""
        if self.camera_running:
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        """Start camera capture (non-blocking)."""
        try:
            camera_index = self.camera_combo.currentIndex()
            if camera_index < 0:
                self.error_occurred.emit("No camera selected")
                return
            
            # Update UI immediately to show responsiveness
            self.start_stop_btn.setText("⏳ Starting...")
            self.start_stop_btn.setEnabled(False)
            self.camera_status.setText("Camera: Initializing...")
            self.camera_status.setStyleSheet("color: orange; font-size: 10px;")
            
            # Start camera in background to avoid UI freeze
            QTimer.singleShot(100, lambda: self._start_camera_background(camera_index))
            
        except Exception as e:
            self.error_occurred.emit(f"Error starting camera: {e}")
    
    def _start_camera_background(self, camera_index):
        """Background camera startup to prevent UI freezing."""
        try:
            # Use OpenCV for camera capture (more reliable than Qt camera for frame access)
            self.opencv_capture = cv2.VideoCapture(camera_index)
            if not self.opencv_capture.isOpened():
                self.error_occurred.emit("Failed to open camera")
                self._reset_camera_ui()
                return
            
            # Set camera properties (this can be slow)
            self.opencv_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.opencv_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.opencv_capture.set(cv2.CAP_PROP_FPS, 30)
            
            # Test camera by reading one frame
            ret, test_frame = self.opencv_capture.read()
            if not ret:
                self.error_occurred.emit("Camera opened but can't read frames")
                self._reset_camera_ui()
                return
            
            # Success - update UI on main thread
            self.camera_running = True
            self.start_stop_btn.setText("⏹️ Stop Camera")
            self.start_stop_btn.setEnabled(True)
            self.capture_btn.setEnabled(True)
            self.camera_status.setText("Camera: Running")
            self.camera_status.setStyleSheet("color: green; font-size: 10px;")
            
            # Start timers
            self.frame_timer.start(33)  # ~30 FPS
            self.result_timer.start(100)  # Check results every 100ms
            
        except Exception as e:
            self.error_occurred.emit(f"Error in camera background startup: {e}")
            self._reset_camera_ui()
    
    def _reset_camera_ui(self):
        """Reset camera UI to initial state."""
        self.start_stop_btn.setText("📷 Start Camera")
        self.start_stop_btn.setEnabled(True)
        self.capture_btn.setEnabled(False)
        self.camera_status.setText("Camera: Stopped")
        self.camera_status.setStyleSheet("color: gray; font-size: 10px;")
    
    def stop_camera(self):
        """Stop camera capture."""
        try:
            self.camera_running = False
            self.frame_timer.stop()
            self.result_timer.stop()
            
            if self.opencv_capture:
                self.opencv_capture.release()
                self.opencv_capture = None
            
            # Clear all annotation data to prevent overlay issues
            self.annotated_frame = None
            self._current_barcode_items = []
            
            self.start_stop_btn.setText("📷 Start Camera")
            self.capture_btn.setEnabled(False)
            self.camera_status.setText("Camera: Stopped")
            self.camera_status.setStyleSheet("color: gray; font-size: 10px;")
            
            # Clear display
            self.camera_label.setText("📷 Camera View")
            self.camera_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #ccc;
                    background-color: #f0f0f0;
                    color: #666;
                    font-size: 16px;
                }
            """)
            
        except Exception as e:
            self.error_occurred.emit(f"Error stopping camera: {e}")
    
    def change_camera(self, index):
        """Change camera device."""
        if self.camera_running:
            self.stop_camera()
    
    def set_detection_mode(self, mode):
        """Set the detection mode."""
        self.current_detection_mode = mode
        # Restart detection with new mode if camera is running
        if self.camera_running and self.cvr_instance:
            try:
                # Stop current detection
                self.cvr_instance.stop_capturing()
                
                # Start with new template
                template = DETECTION_MODES[mode]["template"]
                error_code, error_msg = self.cvr_instance.start_capturing(template)
                
                if error_code != EnumErrorCode.EC_OK:
                    print(f"Detection mode change warning: {error_msg}")
                    
            except Exception as e:
                print(f"Error changing detection mode: {e}")
    
    def toggle_detection(self, enabled):
        """Toggle real-time barcode detection."""
        self.detection_enabled = enabled
        if not enabled:
            # Clear annotations immediately when detection is disabled
            self._current_barcode_items = []
    
    def update_frame(self):
        """Update camera frame display with proper synchronization."""
        if not self.camera_running or not self.opencv_capture:
            return
        
        try:
            ret, frame = self.opencv_capture.read()
            if not ret:
                return
            
            # Store the raw frame for detection processing
            with QMutexLocker(self.frame_mutex):
                self.current_frame = frame.copy()
            
            # Send frame for barcode detection if enabled
            if self.detection_enabled and self.frame_fetcher:
                try:
                    image_data = convertMat2ImageData(frame)
                    self.frame_fetcher.add_frame(image_data)
                except Exception as e:
                    pass  # Silently ignore frame processing errors
            
            # Always start with a fresh frame copy
            display_frame = frame.copy()
            
            # Only add annotations if we have VERY recent detections to prevent ghosting
            if (self.detection_enabled and 
                hasattr(self, '_current_barcode_items') and 
                self._current_barcode_items and
                hasattr(self, '_last_detection_time')):
                
                import time
                current_time = time.time()
                
                # Only show annotations if they're very recent (less than 0.3 seconds old)
                if current_time - self._last_detection_time < 0.3:
                    try:
                        display_frame = self.draw_detection_annotations(display_frame, self._current_barcode_items)
                    except Exception as e:
                        pass  # Fall back to clean frame if annotation fails
                else:
                    # Clear old annotations if they're stale
                    self._current_barcode_items = []
            
            # Convert to Qt format and display
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Scale to fit the label
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.camera_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.camera_label.setPixmap(scaled_pixmap)
            self.camera_label.setStyleSheet("border: 2px solid #007acc;")
            
        except Exception as e:
            pass  # Silently ignore frame update errors
    
    def process_detection_results(self):
        """Process detection results and update live annotations."""
        import time
        
        if not self.detection_enabled:
            # Clear current results when detection is disabled
            self._current_barcode_items = []
            return
        
        current_time = time.time()
        detected_items = []
        
        # Process all available results
        while not self.result_queue.empty():
            try:
                captured_result = self.result_queue.get_nowait()
                
                # Handle different detection modes
                if self.current_detection_mode == "Barcode":
                    items = captured_result.get_items()
                    for item in items:
                        if item.get_type() == EnumCapturedResultItemType.CRIT_BARCODE:
                            detected_items.append(item)
                
                elif self.current_detection_mode == "Document":
                    # Handle document detection results
                    processed_doc_result = captured_result.get_processed_document_result()
                    if processed_doc_result:
                        items = processed_doc_result.get_deskewed_image_result_items()
                        detected_items.extend(items)
                
                elif self.current_detection_mode == "MRZ":
                    # Handle MRZ detection results
                    parsed_result = captured_result.get_parsed_result()
                    if parsed_result:
                        items = parsed_result.get_items()
                        detected_items.extend(items)
                        
            except queue.Empty:
                break
            except Exception as e:
                continue
        
        # ALWAYS clear previous annotations first to prevent ghosting
        self._current_barcode_items = []
        
        # Update with new detections if any
        if detected_items:
            self._current_barcode_items = detected_items
            self._last_detection_time = current_time
            # Emit signal with detected items for results panel
            self.barcodes_detected.emit(detected_items)
        else:
            # Clear old annotations more aggressively (0.5 seconds instead of 1)
            if current_time - self._last_detection_time > 0.5:
                self._current_barcode_items = []
    
    def draw_detection_annotations(self, frame, detection_items):
        """Draw detection annotations on the frame with consistent colors."""
        if not detection_items:
            return frame
        
        import time
        current_time = time.time()
        
        # Clean up old barcode colors periodically
        if len(BARCODE_COLORS) > 20:  # Prevent dictionary from growing too large
            cleanup_old_barcode_colors()
        
        annotated_frame = frame.copy()
        
        for i, item in enumerate(detection_items):
            try:
                if self.current_detection_mode == "Barcode":
                    self._draw_barcode_item(annotated_frame, item, current_time)
                elif self.current_detection_mode == "Document":
                    self._draw_document_item(annotated_frame, item, i)
                elif self.current_detection_mode == "MRZ":
                    self._draw_mrz_item(annotated_frame, item, i)
                           
            except Exception as e:
                continue  # Skip problematic annotations
        
        return annotated_frame
    
    def _draw_barcode_item(self, frame, item, current_time):
        """Draw barcode detection annotation."""
        # Get barcode location
        location = item.get_location()
        points = [(int(point.x), int(point.y)) for point in location.points]
        
        # Get barcode text for consistent color assignment
        text = item.get_text()
        
        # Update last seen timestamp
        BARCODE_LAST_SEEN[text] = current_time
        
        # Use consistent color based on barcode content (not index)
        if text not in BARCODE_COLORS:
            BARCODE_COLORS[text] = len(BARCODE_COLORS) % len(CONTOUR_COLORS)
        
        color = CONTOUR_COLORS[BARCODE_COLORS[text]]
        
        # Draw contour
        cv2.drawContours(frame, [np.array(points)], 0, color, 2)
        
        # Truncate text for display
        display_text = text
        if len(display_text) > 15:
            display_text = display_text[:12] + "..."
        
        # Add text label
        x1, y1 = points[0]
        cv2.putText(frame, display_text, (x1, y1 - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Add barcode number (use consistent index based on color)
        cv2.putText(frame, f"#{BARCODE_COLORS[text]+1}", (x1 - 30, y1),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    def _draw_document_item(self, frame, item, index):
        """Draw document detection annotation."""
        try:
            # For DeskewedImageResultItem, get the source deskew quad
            if hasattr(item, 'get_source_deskew_quad'):
                location = item.get_source_deskew_quad()
                points = [(int(point.x), int(point.y)) for point in location.points]
            elif hasattr(item, 'get_location'):
                location = item.get_location()
                points = [(int(point.x), int(point.y)) for point in location.points]
            else:
                return  # Can't draw without location data
            
            # Use blue color for documents
            color = (255, 0, 0)  # Blue in BGR
            
            # Draw document boundary
            cv2.drawContours(frame, [np.array(points)], 0, color, 3)
            
            # Add label
            if points:
                x1, y1 = points[0]
                cv2.putText(frame, f"Document #{index+1}", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        except Exception as e:
            print(f"Debug: Camera document annotation error: {e}")
            pass
    
    def _draw_mrz_item(self, frame, item, index):
        """Draw MRZ detection annotation."""
        # MRZ items contain parsed text data
        try:
            # Draw a simple rectangle for MRZ detection
            h, w = frame.shape[:2]
            
            # MRZ is typically in the bottom portion of documents
            rect_y = int(h * 0.7)
            rect_height = int(h * 0.2)
            
            color = (0, 255, 255)  # Yellow in BGR
            
            # Draw MRZ region rectangle
            cv2.rectangle(frame, (10, rect_y), (w-10, rect_y + rect_height), color, 3)
            
            # Add label
            cv2.putText(frame, f"MRZ #{index+1}", (20, rect_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        except:
            pass
    
    def capture_frame(self):
        """Capture current frame."""
        if self.current_frame is not None:
            with QMutexLocker(self.frame_mutex):
                captured_frame = self.current_frame.copy()
            
            # Emit signal with captured frame
            self.frame_processed.emit(captured_frame)
    
    def cleanup(self):
        """Cleanup camera resources."""
        self.stop_camera()
        
        if self.cvr_instance and self.camera_receiver:
            try:
                self.cvr_instance.stop_capturing()
                self.cvr_instance.remove_result_receiver(self.camera_receiver)
            except:
                pass
        
        # Clear the CVR instance for camera
        self.cvr_instance = None
        self.camera_receiver = None


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
    """Worker thread for detection processing to keep UI responsive."""
    
    # Define signals
    finished = Signal(object)  # Processing results
    error = Signal(str)        # Error message
    progress = Signal(str)     # Progress message
    
    def __init__(self, cvr_instance, file_path, detection_mode="Barcode"):
        super().__init__()
        self.cvr_instance = cvr_instance
        self.file_path = file_path
        self.detection_mode = detection_mode
    
    def run(self):
        """Run detection in background thread."""
        try:
            mode_name = self.detection_mode.split(" - ")[0] if " - " in self.detection_mode else self.detection_mode
            self.progress.emit(f"🔍 Starting {mode_name} detection...")
            
            # Get the appropriate template for the detection mode
            template = DETECTION_MODES[mode_name]["template"]
            
            results = self.cvr_instance.capture_multi_pages(self.file_path, template)
            
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
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            display_image = self.draw_detection_annotations(display_image, self.barcode_items)
        
        # Convert to QPixmap
        height, width, channel = display_image.shape
        bytes_per_line = 3 * width
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        
        q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # Apply zoom
        if self.zoom_factor == 1.0 and hasattr(self, 'parent') and self.parent():
            # Calculate fit zoom based on parent widget size
            parent = self.parent()
            if hasattr(parent, 'size') and callable(getattr(parent, 'size', None)):
                try:
                    parent_size = parent.size()
                    if parent_size.width() > 50 and parent_size.height() > 50:  # Valid size
                        scale_x = (parent_size.width() - 50) / width
                        scale_y = (parent_size.height() - 50) / height
                        scale = min(scale_x, scale_y, 1.0)  # Don't upscale beyond 100%
                        if scale > 0.1:  # Valid scale
                            scaled_size = pixmap.size() * scale
                            pixmap = pixmap.scaled(scaled_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                except:
                    pass  # Ignore if parent doesn't support size()
        elif self.zoom_factor != 1.0:
            scaled_size = pixmap.size() * self.zoom_factor
            pixmap = pixmap.scaled(scaled_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.current_pixmap = pixmap
        self.setPixmap(pixmap)
        self.resize(pixmap.size())
        self.setStyleSheet("border: 2px solid #ccc; background-color: white;")
    
    def draw_detection_annotations(self, cv_image, items):
        """Draw detection results on the image based on item type."""
        if not items:
            return cv_image
        
        annotated_image = cv_image.copy()
        
        # Adjust annotation parameters based on image size
        height, width = annotated_image.shape[:2]
        font_scale = max(0.3, min(1.0, (width + height) / 2000))
        thickness = max(1, int(2 * (width + height) / 2000))
        
        for i, item in enumerate(items):
            try:
                # Check item type and handle accordingly
                if hasattr(item, 'get_text'):  # Barcode item
                    self._draw_barcode_annotation(annotated_image, item, font_scale, thickness)
                elif hasattr(item, 'get_source_deskew_quad') or (hasattr(item, 'get_location') and not hasattr(item, 'get_text')):  # Document item
                    self._draw_document_annotation(annotated_image, item, i, font_scale, thickness)
                elif hasattr(item, 'get_code_type'):  # MRZ/ParsedResultItem
                    self._draw_mrz_annotation(annotated_image, item, i, font_scale, thickness)
            except Exception as e:
                continue  # Skip problematic items
        
        return annotated_image
    
    def _draw_barcode_annotation(self, annotated_image, item, font_scale, thickness):
        """Draw barcode annotation."""
        # Use consistent color based on barcode content (not index)
        text = item.get_text()
        
        # Update last seen timestamp for picture mode too
        import time
        BARCODE_LAST_SEEN[text] = time.time()
        
        if text not in BARCODE_COLORS:
            BARCODE_COLORS[text] = len(BARCODE_COLORS) % len(CONTOUR_COLORS)
        
        color = CONTOUR_COLORS[BARCODE_COLORS[text]]
        location = item.get_location()
        points = [(int(point.x), int(point.y)) for point in location.points]
        
        # Draw contour
        cv2.drawContours(annotated_image, [np.array(points)], 0, color, thickness)
        
        # Add text label with background
        display_text = text
        if len(display_text) > 20:  # Truncate long text
            display_text = display_text[:17] + "..."
        
        x1, y1 = points[0]
        
        # Calculate text size for background rectangle
        (text_width, text_height), baseline = cv2.getTextSize(
            display_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
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
        cv2.putText(annotated_image, display_text, (x1, y1 - TEXT_OFFSET_Y),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
        
        # Add barcode number
        cv2.putText(annotated_image, f"#{BARCODE_COLORS[text]+1}", 
                   (x1 - 30, y1),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.8, color, thickness)
    
    def _draw_document_annotation(self, annotated_image, item, index, font_scale, thickness):
        """Draw document annotation."""
        try:
            # For DeskewedImageResultItem, get the source deskew quad
            if hasattr(item, 'get_source_deskew_quad'):
                location = item.get_source_deskew_quad()
                points = [(int(point.x), int(point.y)) for point in location.points]
            elif hasattr(item, 'get_location'):
                location = item.get_location()
                points = [(int(point.x), int(point.y)) for point in location.points]
            else:
                return  # Can't draw without location data
            
            # Use blue color for documents
            color = (255, 0, 0)  # Blue in BGR
            
            # Draw document boundary
            cv2.drawContours(annotated_image, [np.array(points)], 0, color, thickness + 1)
            
            # Add label
            if points:
                x1, y1 = points[0]
                label = f"Document #{index+1}"
                
                # Draw background for text
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
                )
                
                cv2.rectangle(annotated_image, 
                             (x1 - 2, y1 - text_height - 15),
                             (x1 + text_width + 2, y1 - 5),
                             (255, 255, 255), -1)
                cv2.rectangle(annotated_image, 
                             (x1 - 2, y1 - text_height - 15),
                             (x1 + text_width + 2, y1 - 5),
                             color, 1)
                
                cv2.putText(annotated_image, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        except Exception as e:
            print(f"Debug: Document annotation error: {e}")
            pass
    
    def _draw_mrz_annotation(self, annotated_image, item, index, font_scale, thickness):
        """Draw MRZ annotation."""
        try:
            # For MRZ, draw a simple rectangle as MRZ items don't have location points
            h, w = annotated_image.shape[:2]
            
            # MRZ is typically in the bottom portion of documents
            rect_y = int(h * 0.7)
            rect_height = int(h * 0.2)
            
            color = (0, 255, 255)  # Yellow in BGR
            
            # Draw MRZ region rectangle
            cv2.rectangle(annotated_image, (10, rect_y), (w-10, rect_y + rect_height), color, thickness + 1)
            
            # Add label
            label = f"MRZ #{index+1}"
            cv2.putText(annotated_image, label, (20, rect_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        except:
            pass
        
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
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
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
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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

class LicenseDialog(QDialog):
    """Custom dialog for license key entry with trial license option."""
    
    def __init__(self, current_license_key, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Management")
        self.setFixedSize(500, 300)
        self.license_key = ""
        self.result_type = None  # 'license', 'trial', or None
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔑 Dynamsoft License Management")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current license info
        current_key_display = current_license_key[:20] + "..." if len(current_license_key) > 20 else current_license_key
        current_info = QLabel(f"Current license: {current_key_display}")
        current_info.setStyleSheet("color: gray; font-size: 10px; padding: 10px;")
        layout.addWidget(current_info)
        
        # License key input
        input_group = QGroupBox("Enter New License Key")
        input_layout = QVBoxLayout(input_group)
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Paste your Dynamsoft license key here...")
        input_layout.addWidget(self.license_input)
        
        layout.addWidget(input_group)
        
        # Trial license section
        trial_group = QGroupBox("Need a License?")
        trial_layout = QVBoxLayout(trial_group)
        
        trial_info = QLabel("Get a 30-day free trial license from Dynamsoft:")
        trial_layout.addWidget(trial_info)
        
        self.trial_button = QPushButton("🌐 Get 30-Day Trial License")
        self.trial_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.trial_button.clicked.connect(self.open_trial_page)
        trial_layout.addWidget(self.trial_button)
        
        layout.addWidget(trial_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply License")
        self.apply_button.setDefault(True)
        self.apply_button.clicked.connect(self.apply_license)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def open_trial_page(self):
        """Open the trial license page in the default browser."""
        trial_url = "https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform"
        QDesktopServices.openUrl(QUrl(trial_url))
        
        # Show info message
        QMessageBox.information(
            self,
            "Trial License",
            "🌐 The trial license page has been opened in your browser.\n\n"
            "Steps to get your trial license:\n"
            "1. Fill out the form on the opened page\n"
            "2. Submit to receive your license key via email\n"
            "3. Copy the license key and paste it here\n"
            "4. Click 'Apply License' to activate"
        )
    
    def apply_license(self):
        """Apply the entered license key."""
        self.license_key = self.license_input.text().strip()
        if self.license_key:
            self.result_type = 'license'
            self.accept()
        else:
            QMessageBox.warning(self, "Missing License", "Please enter a license key.")
    
    def get_license_key(self):
        """Get the entered license key."""
        return self.license_key

class BarcodeReaderMainWindow(QMainWindow):
    """Main window for the PySide6 barcode reader application with camera support."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamsoft Capture Vision - Multi-Mode Scanner")
        self.setGeometry(100, 100, 1600, 1000)
        self.setAcceptDrops(True)  # Enable drag-and-drop for main window
        
        # Initialize variables
        self.cvr_instance = None
        self.custom_receiver = None
        self.current_file_path = None
        self.current_pages = {}  # Store page data {page_index: cv_image}
        self.page_hash_mapping = {}  # Map page_index to hash_id
        self.current_page_index = 0
        self.page_results = {}  # Store detection results for each page
        self.is_processing = False
        self.process_start_time = None
        self.current_detection_mode = "Barcode"  # Default detection mode
        
        # Camera mode variables
        self.camera_results = []  # Store recent camera detection results
        self.camera_history = []  # Store detection history
        
        # Setup UI
        self.setup_ui()
        self.setup_status_bar()
        self.setup_menu_bar()
        
        # Initialize Dynamsoft
        self.initialize_license()
    
    def setup_ui(self):
        """Setup the main user interface with tabbed layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Picture Mode Tab
        self.picture_tab = self.create_picture_mode_tab()
        self.tab_widget.addTab(self.picture_tab, "📁 Picture Mode")
        
        # Camera Mode Tab
        self.camera_tab = self.create_camera_mode_tab()
        self.tab_widget.addTab(self.camera_tab, "📷 Camera Mode")
        
        # Connect tab change event
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def create_picture_mode_tab(self):
        """Create the picture mode tab (original functionality)."""
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
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
        splitter.setSizes([300, 700, 400])
        
        return tab_widget
    
    def create_camera_mode_tab(self):
        """Create the camera mode tab for real-time scanning."""
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        
        # Create splitter for camera layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Camera controls panel (left)
        self.camera_control_panel = self.create_camera_control_panel()
        splitter.addWidget(self.camera_control_panel)
        
        # Camera display (center)
        self.camera_widget = CameraWidget()
        
        # Set initial detection mode from combo box
        initial_mode = list(DETECTION_MODES.keys())[0]  # Default to first mode (Barcode)
        self.camera_widget.set_detection_mode(initial_mode)
        
        splitter.addWidget(self.camera_widget)
        
        # Camera results panel (right)
        self.camera_results_panel = self.create_camera_results_panel()
        splitter.addWidget(self.camera_results_panel)
        
        # Set initial sizes
        splitter.setSizes([300, 800, 400])
        
        # Connect camera signals
        self.camera_widget.barcodes_detected.connect(self.on_camera_barcodes_detected)
        self.camera_widget.frame_processed.connect(self.on_camera_frame_captured)
        self.camera_widget.error_occurred.connect(self.on_camera_error)
        
        return tab_widget
    
    def create_camera_control_panel(self):
        """Create camera control panel."""
        panel = QWidget()
        panel.setMaximumWidth(320)
        layout = QVBoxLayout(panel)
        
        # Camera Settings Group
        camera_group = QGroupBox("📷 Camera Settings")
        camera_layout = QVBoxLayout(camera_group)
        
        # Detection mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Detection Mode:"))
        self.detection_mode_combo = QComboBox()
        for mode, config in DETECTION_MODES.items():
            self.detection_mode_combo.addItem(f"{mode} - {config['description']}")
        self.detection_mode_combo.setCurrentIndex(0)  # Default to Barcode
        self.detection_mode_combo.currentTextChanged.connect(self.on_detection_mode_changed)
        mode_layout.addWidget(self.detection_mode_combo)
        camera_layout.addLayout(mode_layout)
        
        # Instructions
        instructions = QLabel("""
        <b>Camera Mode Instructions:</b><br>
        1. Select detection mode above<br>
        2. Select camera from dropdown<br>
        3. Click 'Start Camera'<br>
        4. Enable 'Real-time Detection'<br>
        5. Point camera at target objects<br>
        6. View results in real-time
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 11px; color: #444; background-color: #f0f8ff; padding: 10px; border: 1px solid #ccc;")
        camera_layout.addWidget(instructions)
        
        layout.addWidget(camera_group)
        
        # Detection Settings Group
        detection_group = QGroupBox("🔍 Detection Settings")
        detection_layout = QVBoxLayout(detection_group)
        
        self.camera_auto_clear_check = QCheckBox("Auto-clear old results")
        self.camera_auto_clear_check.setChecked(True)
        detection_layout.addWidget(self.camera_auto_clear_check)
        
        self.camera_show_confidence_check = QCheckBox("Show confidence")
        detection_layout.addWidget(self.camera_show_confidence_check)
        
        self.camera_beep_check = QCheckBox("Beep on detection")
        detection_layout.addWidget(self.camera_beep_check)
        
        # Detection frequency
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Detection frequency:"))
        self.detection_freq_combo = QComboBox()
        self.detection_freq_combo.addItems(["High (30Hz)", "Medium (10Hz)", "Low (5Hz)"])
        self.detection_freq_combo.setCurrentIndex(1)  # Default to Medium
        freq_layout.addWidget(self.detection_freq_combo)
        detection_layout.addLayout(freq_layout)
        
        layout.addWidget(detection_group)
        
        # Camera Actions Group
        actions_group = QGroupBox("⚡ Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.camera_capture_btn = QPushButton("📸 Capture Current Frame")
        self.camera_capture_btn.clicked.connect(self.capture_camera_frame)
        actions_layout.addWidget(self.camera_capture_btn)
        
        self.camera_export_btn = QPushButton("💾 Export Camera Results")
        self.camera_export_btn.setEnabled(False)
        self.camera_export_btn.clicked.connect(self.export_camera_results)
        actions_layout.addWidget(self.camera_export_btn)
        
        self.camera_clear_btn = QPushButton("🗑️ Clear Results")
        self.camera_clear_btn.clicked.connect(self.clear_camera_results)
        actions_layout.addWidget(self.camera_clear_btn)
        
        layout.addWidget(actions_group)
        
        # Statistics Group
        stats_group = QGroupBox("📊 Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.camera_stats_label = QLabel("Unique barcodes: 0\nTotal detections: 0\nLast detection: Never")
        self.camera_stats_label.setStyleSheet("font-size: 11px; color: #666;")
        stats_layout.addWidget(self.camera_stats_label)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        return panel
    
    def create_camera_results_panel(self):
        """Create camera results panel."""
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        
        # Results header
        header_layout = QHBoxLayout()
        self.camera_results_summary = QLabel("Live Detections: 0")
        self.camera_results_summary.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.camera_results_summary)
        
        # Clear button in header
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(60)
        clear_btn.clicked.connect(self.clear_camera_results)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Results display
        self.camera_results_text = QTextEdit()
        self.camera_results_text.setReadOnly(True)
        self.camera_results_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.camera_results_text)
        
        return panel
    
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
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        process_group = QGroupBox("🔍 Detection Controls")
        process_layout = QVBoxLayout(process_group)
        
        # Detection mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Detection Mode:"))
        self.picture_detection_mode_combo = QComboBox()
        for mode, config in DETECTION_MODES.items():
            self.picture_detection_mode_combo.addItem(f"{mode} - {config['description']}")
        self.picture_detection_mode_combo.setCurrentIndex(0)  # Default to Barcode
        mode_layout.addWidget(self.picture_detection_mode_combo)
        process_layout.addLayout(mode_layout)
        
        self.process_button = QPushButton("🔍 Start Detection")
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
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_label = QLabel(f"Memory: {memory_mb:.1f} MB")
                self.memory_label.setStyleSheet("color: gray; font-size: 10px;")
                self.status_bar.addPermanentWidget(self.memory_label)
            except:
                pass  # Ignore if psutil is not available
    
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
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        license_action = QAction("Enter License Key...", self)
        license_action.triggered.connect(self.enter_license_key)
        settings_menu.addAction(license_action)
        
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
        """Initialize the Dynamsoft license using global function."""
        try:
            # Use global license initialization
            if initialize_license_once():
                self.cvr_instance = CaptureVisionRouter()
                intermediate_result_manager = self.cvr_instance.get_intermediate_result_manager()
                self.custom_receiver = MyIntermediateResultReceiver(intermediate_result_manager)
                intermediate_result_manager.add_result_receiver(self.custom_receiver)
                
                self.log_message("✅ License initialized successfully!")
                
                # Initialize camera widget with CVR instance after a delay to avoid conflicts
                QTimer.singleShot(500, self.delayed_camera_init)
                
            else:
                self.log_message(f"❌ License initialization failed")
                QMessageBox.critical(self, "License Error", f"Failed to initialize license")
        except Exception as e:
            self.log_message(f"❌ Error initializing license: {e}")
            QMessageBox.critical(self, "Error", f"Failed to initialize: {e}")
    
    def delayed_camera_init(self):
        """Initialize camera with delay to avoid conflicts."""
        if hasattr(self, 'camera_widget'):
            self.camera_widget.initialize_dynamsoft_camera(self.cvr_instance)
    
    def on_detection_mode_changed(self, mode_text):
        """Handle detection mode change in camera."""
        mode_name = mode_text.split(" - ")[0]  # Extract mode name from combo text
        if hasattr(self, 'camera_widget'):
            self.camera_widget.set_detection_mode(mode_name)
        
        # Update window title to reflect current mode
        current_mode = mode_name
        self.setWindowTitle(f"Dynamsoft Capture Vision - {current_mode} Scanner")
        self.log_message(f"🔄 Switched to {current_mode} detection mode")
    
    def on_tab_changed(self, index):
        """Handle tab change events."""
        if index == 0:  # Picture mode
            self.log_message("📁 Switched to Picture Mode")
            # Stop camera if running
            if hasattr(self, 'camera_widget') and self.camera_widget.camera_running:
                self.camera_widget.stop_camera()
        elif index == 1:  # Camera mode
            self.log_message("📷 Switched to Camera Mode")
            # Initialize camera widget if not already done
            if hasattr(self, 'camera_widget') and self.cvr_instance:
                # Delay camera initialization to avoid conflicts
                QTimer.singleShot(100, lambda: self.camera_widget.initialize_dynamsoft_camera(self.cvr_instance))
    
    def on_camera_barcodes_detected(self, detection_items):
        """Handle detection results from camera (barcodes, documents, MRZ)."""
        if not detection_items:
            return
        
        current_time = datetime.datetime.now()
        new_detections = 0
        
        # Get current detection mode
        current_mode_text = self.detection_mode_combo.currentText()
        mode_name = current_mode_text.split(" - ")[0]
        
        for item in detection_items:
            try:
                detection_data = {
                    'timestamp': current_time,
                    'mode': mode_name
                }
                is_new = False  # Initialize to False
                
                if mode_name == "Barcode":
                    # Handle barcode detection
                    barcode_text = item.get_text()
                    barcode_format = item.get_format_string()
                    
                    detection_data.update({
                        'text': barcode_text,
                        'format': barcode_format,
                        'confidence': getattr(item, 'get_confidence', lambda: None)()
                    })
                    
                    # Check if this is a new detection (not detected in last 2 seconds)
                    is_new = True
                    for existing in self.camera_history:
                        if (existing.get('text') == barcode_text and 
                            (current_time - existing['timestamp']).total_seconds() < 2):
                            is_new = False
                            break
                
                elif mode_name == "Document":
                    # Handle document detection
                    detection_data.update({
                        'type': 'Document',
                        'status': 'Detected'
                    })
                    is_new = True  # Always show document detections
                
                elif mode_name == "MRZ":
                    # Handle MRZ detection with parsed data
                    from utils import MRZResult
                    mrz_result = MRZResult(item)
                    
                    detection_data.update({
                        'type': 'MRZ',
                        'doc_type': mrz_result.doc_type,
                        'doc_id': mrz_result.doc_id,
                        'surname': mrz_result.surname,
                        'given_name': mrz_result.given_name,
                        'nationality': mrz_result.nationality,
                        'issuer': mrz_result.issuer,
                        'gender': mrz_result.gender,
                        'date_of_birth': mrz_result.date_of_birth,
                        'date_of_expiry': mrz_result.date_of_expiry,
                        'raw_text': mrz_result.raw_text
                    })
                    
                    # Check for new MRZ detection based on document ID
                    is_new = True
                    for existing in self.camera_history:
                        if (existing.get('doc_id') == mrz_result.doc_id and 
                            existing.get('mode') == 'MRZ' and
                            (current_time - existing['timestamp']).total_seconds() < 5):  # 5 seconds for MRZ
                            is_new = False
                            break
                
                if is_new:
                    self.camera_history.append(detection_data)
                    new_detections += 1
                    
                    # Limit history size
                    if len(self.camera_history) > 100:
                        self.camera_history = self.camera_history[-50:]  # Keep last 50
            
            except Exception as e:
                print(f"Error processing camera detection: {e}")
                continue
        
        if new_detections > 0:
            self.update_camera_results_display()
            self.update_camera_statistics()
            
            # Beep if enabled
            if self.camera_beep_check.isChecked():
                QApplication.beep()
    
    def on_camera_frame_captured(self, frame):
        """Handle captured frame from camera."""
        try:
            # Process the captured frame like a regular image
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create a temporary file name
            temp_filename = f"camera_capture_{timestamp}.jpg"
            
            # You could save the frame or process it directly
            self.log_message(f"📸 Frame captured at {timestamp}")
            
            # Optionally switch to picture mode and load the captured frame
            # For now, just show a message
            QMessageBox.information(self, "Frame Captured", 
                                  f"Frame captured successfully!\nTimestamp: {timestamp}")
            
        except Exception as e:
            self.log_message(f"❌ Error handling captured frame: {e}")
    
    def on_camera_error(self, error_message):
        """Handle camera errors."""
        self.log_message(f"📷 Camera error: {error_message}")
        QMessageBox.warning(self, "Camera Error", error_message)
    
    def capture_camera_frame(self):
        """Trigger camera frame capture."""
        if hasattr(self, 'camera_widget'):
            self.camera_widget.capture_frame()
    
    def export_camera_results(self):
        """Export camera detection results."""
        if not self.camera_history:
            QMessageBox.warning(self, "No Results", "No camera detection results to export.")
            return
        
        try:
            # Show export format dialog
            dialog = ExportFormatDialog(self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            format_index = dialog.get_selected_format()
            if format_index is None:
                return
                
            extensions = [".txt", ".csv", ".json"]
            format_names = ["Text", "CSV", "JSON"]
            
            ext = extensions[format_index]
            format_name = format_names[format_index]
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Camera Results",
                f"camera_detections{ext}",
                f"{format_name} files (*{ext});;All files (*.*)"
            )
            
            if file_path:
                if ext == ".txt":
                    self.export_camera_to_text(file_path)
                elif ext == ".csv":
                    self.export_camera_to_csv(file_path)
                elif ext == ".json":
                    self.export_camera_to_json(file_path)
                
                self.log_message(f"💾 Camera results exported to: {os.path.basename(file_path)}")
                QMessageBox.information(self, "Export Complete", 
                                      f"Camera results exported successfully to:\n{file_path}")
                
        except Exception as e:
            self.log_message(f"❌ Export error: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export results: {e}")
    
    def export_camera_to_text(self, file_path):
        """Export camera results to text file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Dynamsoft Barcode Reader - Camera Detection Results\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total Detections: {len(self.camera_history)}\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, detection in enumerate(self.camera_history, 1):
                f.write(f"Detection {i}:\n")
                f.write(f"  Format: {detection['format']}\n")
                f.write(f"  Text: {detection['text']}\n")
                f.write(f"  Timestamp: {detection['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                if detection['confidence']:
                    f.write(f"  Confidence: {detection['confidence']}\n")
                f.write("\n")
                f.write(f"  Format: {detection['format']}\n")
                f.write(f"  Text: {detection['text']}\n")
                f.write(f"  Timestamp: {detection['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                if detection['confidence']:
                    f.write(f"  Confidence: {detection['confidence']}\n")
                f.write("\n")
    
    def export_camera_to_csv(self, file_path):
        """Export camera results to CSV file."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Detection_Number', 'Format', 'Text', 'Timestamp', 'Confidence'])
            
            for i, detection in enumerate(self.camera_history, 1):
                row = [
                    i,
                    detection['format'],
                    detection['text'],
                    detection['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    detection['confidence'] or ''
                ]
                writer.writerow(row)
    
    def export_camera_to_json(self, file_path):
        """Export camera results to JSON file."""
        export_data = {
            "source": "camera_detection",
            "export_time": datetime.datetime.now().isoformat(),
            "total_detections": len(self.camera_history),
            "detections": []
        }
        
        for i, detection in enumerate(self.camera_history, 1):
            detection_data = {
                "detection_number": i,
                "format": detection['format'],
                "text": detection['text'],
                "timestamp": detection['timestamp'].isoformat(),
                "confidence": detection['confidence']
            }
            export_data["detections"].append(detection_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def clear_camera_results(self):
        """Clear camera detection results."""
        reply = QMessageBox.question(self, "Clear Results", 
                                   "Are you sure you want to clear all camera detection results?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.camera_history.clear()
            self.camera_results.clear()
            self.update_camera_results_display()
            self.update_camera_statistics()
            self.camera_export_btn.setEnabled(False)
            self.log_message("🗑️ Camera results cleared")
    
    def update_camera_results_display(self):
        """Update camera results display."""
        if not self.camera_history:
            self.camera_results_text.clear()
            self.camera_results_text.append("No detections yet. Point camera at targets.")
            return
        
        # Get recent detections (last 20)
        recent_detections = self.camera_history[-20:] if len(self.camera_history) > 20 else self.camera_history
        
        html_content = '<h3 style="color: #1E3A8A;">📷 LIVE CAMERA DETECTIONS</h3>'
        html_content += '<hr style="border: 1px solid #ccc;">'
        
        for i, detection in enumerate(reversed(recent_detections), 1):
            time_str = detection['timestamp'].strftime('%H:%M:%S')
            mode = detection.get('mode', 'Unknown')
            
            html_content += f'<div style="margin: 8px 0; padding: 8px; background-color: #f0f8ff; border-left: 3px solid #007acc;">'
            html_content += f'<div style="font-weight: bold; color: #DC2626;">#{len(self.camera_history) - i + 1} - {time_str} ({mode})</div>'
            
            if mode == "Barcode":
                html_content += f'<div><b>Format:</b> <span style="color: #7C2D12;">{detection.get("format", "Unknown")}</span></div>'
                html_content += f'<div><b>Content:</b> <span style="color: #15803D; font-family: monospace;">"{detection.get("text", "")}"</span></div>'
                
                if detection.get('confidence') and self.camera_show_confidence_check.isChecked():
                    html_content += f'<div><b>Confidence:</b> <span style="color: #7C2D12;">{detection["confidence"]}</span></div>'
            
            elif mode == "Document":
                html_content += f'<div><b>Type:</b> <span style="color: #7C2D12;">Document</span></div>'
                html_content += f'<div><b>Status:</b> <span style="color: #15803D;">Detected & Normalized</span></div>'
            
            elif mode == "MRZ":
                # Display MRZ parsed data
                html_content += f'<div><b>Type:</b> <span style="color: #7C2D12;">MRZ - {detection.get("doc_type", "Unknown")}</span></div>'
                
                if detection.get('doc_id'):
                    html_content += f'<div><b>Document ID:</b> <span style="color: #15803D; font-family: monospace;">{detection["doc_id"]}</span></div>'
                
                if detection.get('surname') and detection.get('given_name'):
                    full_name = f"{detection['given_name']} {detection['surname']}"
                    html_content += f'<div><b>Name:</b> <span style="color: #15803D;">{full_name}</span></div>'
                
                if detection.get('nationality'):
                    html_content += f'<div><b>Nationality:</b> <span style="color: #15803D;">{detection["nationality"]}</span></div>'
                
                if detection.get('date_of_birth'):
                    html_content += f'<div><b>Birth Date:</b> <span style="color: #15803D; font-family: monospace;">{detection["date_of_birth"]}</span></div>'
                
                if detection.get('date_of_expiry'):
                    html_content += f'<div><b>Expiry:</b> <span style="color: #15803D; font-family: monospace;">{detection["date_of_expiry"]}</span></div>'
                
                # Show raw MRZ lines in compact format
                if detection.get('raw_text'):
                    raw_lines = detection['raw_text'][:2]  # Show first 2 lines only in camera view
                    html_content += f'<div style="margin-top: 5px;"><b>MRZ Lines:</b></div>'
                    for line_num, line in enumerate(raw_lines, 1):
                        # Limit line length for camera display
                        display_line = line[:30] + "..." if len(line) > 30 else line
                        html_content += f'<div style="font-family: monospace; font-size: 10px; color: #666;">L{line_num}: {display_line}</div>'
            
            html_content += '</div>'
        
        if len(self.camera_history) > 20:
            html_content += f'<div style="text-align: center; color: #666; font-style: italic;">... and {len(self.camera_history) - 20} more detections</div>'
        
        self.camera_results_text.setHtml(html_content)
        
        # Enable export if we have results
        self.camera_export_btn.setEnabled(len(self.camera_history) > 0)
    
    def update_camera_statistics(self):
        """Update camera statistics display."""
        # Count different types of detections
        barcode_count = len([d for d in self.camera_history if d.get('mode') == 'Barcode'])
        document_count = len([d for d in self.camera_history if d.get('mode') == 'Document'])
        mrz_count = len([d for d in self.camera_history if d.get('mode') == 'MRZ'])
        
        total_detections = len(self.camera_history)
        
        last_detection = "Never"
        if self.camera_history:
            last_detection = self.camera_history[-1]['timestamp'].strftime('%H:%M:%S')
        
        # Get current mode for better statistics
        current_mode_text = self.detection_mode_combo.currentText()
        mode_name = current_mode_text.split(" - ")[0]
        
        if mode_name == "Barcode":
            unique_items = len(set(d.get('text', '') for d in self.camera_history if d.get('mode') == 'Barcode'))
            stats_text = f"Unique barcodes: {unique_items}\nTotal detections: {total_detections}\nLast detection: {last_detection}"
        elif mode_name == "MRZ":
            unique_items = len(set(d.get('doc_id', '') for d in self.camera_history if d.get('mode') == 'MRZ' and d.get('doc_id')))
            stats_text = f"Unique documents: {unique_items}\nMRZ detections: {mrz_count}\nLast detection: {last_detection}"
        else:
            stats_text = f"Barcodes: {barcode_count} | Docs: {document_count} | MRZ: {mrz_count}\nTotal: {total_detections}\nLast: {last_detection}"
        
        self.camera_stats_label.setText(stats_text)
        
        # Update summary
        self.camera_results_summary.setText(f"Live Detections: {total_detections}")
    
    def closeEvent(self, event):
        """Handle application close event."""
        reply = QMessageBox.question(self, "Quit", "Do you want to quit the Barcode Reader?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Stop any running worker threads
            if hasattr(self, 'worker') and self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait()
            
            # Cleanup camera resources
            if hasattr(self, 'camera_widget'):
                self.camera_widget.cleanup()
            
            event.accept()
        else:
            event.ignore()
    
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
        """Process the current file for detection."""
        if not self.current_file_path or self.is_processing:
            return
        
        # Get current detection mode from the combo box
        current_mode_text = self.picture_detection_mode_combo.currentText()
        mode_name = current_mode_text.split(" - ")[0]
        
        self.is_processing = True
        self.process_button.setEnabled(False)
        self.process_button.setText(f"🔄 Processing {mode_name}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Clear previous results
        self.page_results = {}
        self.page_hash_mapping = {}
        if self.custom_receiver:
            self.custom_receiver.images.clear()
        
        # Record start time
        self.process_start_time = datetime.datetime.now()
        
        self.log_message(f"🔍 Starting {mode_name} detection...")
        
        # Create and start worker thread with detection mode
        self.worker = ProcessingWorker(self.cvr_instance, self.current_file_path, current_mode_text)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.progress.connect(self.log_message)
        self.worker.start()
    
    def on_processing_finished(self, results):
        """Handle completion of detection processing."""
        try:
            self.page_results = {}
            self.page_hash_mapping = {}
            total_items = 0
            
            # Get current detection mode
            current_mode_text = self.picture_detection_mode_combo.currentText()
            mode_name = current_mode_text.split(" - ")[0]
            
            result_list = results.get_results()
            
            # Build the page mapping from results to maintain correct order
            for i, result in enumerate(result_list):
                if result.get_error_code() == EnumErrorCode.EC_OK:
                    hash_id = result.get_original_image_hash_id()
                    
                    # Extract items based on detection mode
                    items = []
                    if mode_name == "Barcode":
                        items = result.get_items()
                    elif mode_name == "Document":
                        # Handle document detection results
                        processed_doc_result = result.get_processed_document_result()
                        if processed_doc_result:
                            items = processed_doc_result.get_deskewed_image_result_items()
                    elif mode_name == "MRZ":
                        # Handle MRZ detection results
                        parsed_result = result.get_parsed_result()
                        if parsed_result:
                            items = parsed_result.get_items()
                    
                    # Map page index to hash_id and store results
                    page_index = i
                    self.page_hash_mapping[page_index] = hash_id
                    self.page_results[page_index] = items
                    total_items += len(items)
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
            if self.process_start_time is not None:
                process_time = (datetime.datetime.now() - self.process_start_time).total_seconds()
            else:
                process_time = 0.0
            
            # Get current detection mode for UI updates
            current_mode_text = self.picture_detection_mode_combo.currentText()
            mode_name = current_mode_text.split(" - ")[0]
            
            # Update UI
            self.results_summary.setText(f"Total {mode_name}s: {total_items}")
            self.display_current_page()
            self.display_page_results()
            
            # Enable export buttons if items found
            has_results = total_items > 0
            self.export_button.setEnabled(has_results)
            self.copy_button.setEnabled(has_results)
            
            # Update time display
            self.time_label.setText(f"Processing time: {process_time:.2f}s")
            
            self.log_message(f"✅ Processing complete! Found {total_items} {mode_name.lower()}(s) in {process_time:.2f}s")
            
        except Exception as e:
            self.on_processing_error(str(e))
        finally:
            self.is_processing = False
            current_mode_text = self.picture_detection_mode_combo.currentText()
            mode_name = current_mode_text.split(" - ")[0]
            self.process_button.setText(f"🔍 Detect {mode_name}s")
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
        detection_items = self.page_results.get(self.current_page_index, [])
        
        # Get current detection mode
        current_mode_text = self.picture_detection_mode_combo.currentText()
        mode_name = current_mode_text.split(" - ")[0]
        
        # Special handling for document detection - show normalized documents if available
        if mode_name == "Document" and detection_items:
            self.display_document_results(cv_image, detection_items)
        else:
            # Standard display for barcodes and MRZ
            self.image_widget.set_image(cv_image, detection_items)
        
        self.display_page_results()
    
    def display_document_results(self, original_image, document_items):
        """Special display for document detection showing both original with boundaries and normalized documents."""
        from utils import convertImageData2Mat
        
        # Create a combined display showing original with annotations and normalized documents
        try:
            if not document_items:
                self.image_widget.set_image(original_image, [])
                return
            
            # Create annotated original image
            annotated_original = original_image.copy()
            
            # Draw document boundaries on original
            for i, item in enumerate(document_items):
                try:
                    if hasattr(item, 'get_source_deskew_quad'):
                        location = item.get_source_deskew_quad()
                        points = [(int(point.x), int(point.y)) for point in location.points]
                        
                        # Draw detected document boundary
                        color = (0, 255, 0)  # Green for detected boundaries
                        cv2.drawContours(annotated_original, [np.array(points)], 0, color, 3)
                        
                        # Add label
                        if points:
                            x1, y1 = points[0]
                            cv2.putText(annotated_original, f"Detected Document #{i+1}", 
                                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                except Exception as e:
                    print(f"Error drawing document boundary: {e}")
                    continue
            
            # Get the first normalized document for display (if multiple, show the first one)
            first_item = document_items[0]
            if hasattr(first_item, 'get_image_data'):
                try:
                    normalized_image_data = first_item.get_image_data()
                    if normalized_image_data:
                        normalized_image = convertImageData2Mat(normalized_image_data)
                        
                        # Create side-by-side display
                        combined_image = self.create_side_by_side_display(annotated_original, normalized_image)
                        self.image_widget.set_image(combined_image, [])  # No additional annotations needed
                        return
                except Exception as e:
                    print(f"Error processing normalized document: {e}")
            
            # Fallback: just show original with boundaries if normalized image extraction fails
            self.image_widget.set_image(annotated_original, [])
            
        except Exception as e:
            print(f"Error in document display: {e}")
            # Fallback to standard display
            self.image_widget.set_image(original_image, document_items)
    
    def create_side_by_side_display(self, original_image, normalized_image):
        """Create a side-by-side display of original and normalized images."""
        try:
            # Resize images to same height for better comparison
            orig_h, orig_w = original_image.shape[:2]
            norm_h, norm_w = normalized_image.shape[:2]
            
            # Use the smaller height to fit both images nicely
            target_height = min(orig_h, norm_h, 600)  # Cap at 600px height
            
            # Calculate aspect ratios and resize
            orig_aspect = orig_w / orig_h
            norm_aspect = norm_w / norm_h
            
            orig_new_width = int(target_height * orig_aspect)
            norm_new_width = int(target_height * norm_aspect)
            
            resized_original = cv2.resize(original_image, (orig_new_width, target_height))
            resized_normalized = cv2.resize(normalized_image, (norm_new_width, target_height))
            
            # Add text labels
            label_height = 30
            total_height = target_height + label_height
            
            # Create labeled images
            orig_with_label = np.zeros((total_height, orig_new_width, 3), dtype=np.uint8)
            orig_with_label[:label_height] = (50, 50, 50)  # Dark gray header
            orig_with_label[label_height:] = resized_original
            
            norm_with_label = np.zeros((total_height, norm_new_width, 3), dtype=np.uint8)
            norm_with_label[:label_height] = (50, 50, 50)  # Dark gray header
            norm_with_label[label_height:] = resized_normalized
            
            # Add text labels
            cv2.putText(orig_with_label, "Original with Detected Boundaries", 
                       (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(norm_with_label, "Normalized Document", 
                       (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Combine side by side with a separator
            separator_width = 10
            separator = np.zeros((total_height, separator_width, 3), dtype=np.uint8)
            separator[:] = (200, 200, 200)  # Light gray separator
            
            combined = np.hstack([orig_with_label, separator, norm_with_label])
            return combined
            
        except Exception as e:
            print(f"Error creating side-by-side display: {e}")
            return original_image
    
    def display_page_results(self):
        """Display detection results for the current page."""
        self.results_text.clear()
        
        if self.current_page_index not in self.page_results:
            self.results_text.append("No detection results for this page.")
            self.page_summary.setText("")
            return
        
        items = self.page_results[self.current_page_index]
        
        if not items:
            # Get current detection mode
            current_mode_text = self.picture_detection_mode_combo.currentText()
            mode_name = current_mode_text.split(" - ")[0]
            self.results_text.append(f"No {mode_name.lower()}s found on this page.")
            self.page_summary.setText("")
            return
        
        # Get current detection mode
        current_mode_text = self.picture_detection_mode_combo.currentText()
        mode_name = current_mode_text.split(" - ")[0]
        
        # Update page summary
        self.page_summary.setText(f"Page {self.current_page_index + 1}: {len(items)} {mode_name.lower()}(s)")
        
        # Format results with HTML based on detection mode
        html_content = f'<h3 style="color: #1E3A8A; background-color: #F0F8FF;">📄 PAGE {self.current_page_index + 1} RESULTS</h3>'
        html_content += '<hr style="border: 1px solid #ccc;">'
        
        if mode_name == "Barcode":
            html_content += self._format_barcode_results(items)
        elif mode_name == "Document":
            html_content += self._format_document_results(items)
        elif mode_name == "MRZ":
            html_content += self._format_mrz_results(items)
        
        self.results_text.setHtml(html_content)
    
    def _format_barcode_results(self, items):
        """Format barcode detection results."""
        html_content = ""
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
            html_content += '</div>'
        
        return html_content
    
    def _format_document_results(self, items):
        """Format document detection results."""
        html_content = ""
        for i, item in enumerate(items, 1):
            html_content += f'<div style="margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #00cc66;">'
            html_content += f'<h4 style="color: #DC2626; margin: 0;">📄 DOCUMENT #{i:02d}</h4>'
            html_content += f'<p style="margin: 5px 0;"><b>📋 Type:</b> <span style="color: #7C2D12;">Detected Document</span></p>'
            html_content += f'<p style="margin: 5px 0;"><b>📊 Status:</b> <span style="color: #15803D;">Normalized</span></p>'
            
            # Location if available
            try:
                location = item.get_location()
                points = location.points
                if len(points) >= 4:
                    point_labels = ["TL", "TR", "BR", "BL"]
                    points_text = " → ".join([f"{label}({int(p.x)},{int(p.y)})" for p, label in zip(points[:4], point_labels)])
                    html_content += f'<p style="margin: 5px 0;"><b>📍 Corners:</b> <span style="color: #1E40AF; font-family: monospace; font-size: 10px;">{points_text}</span></p>'
            except:
                pass
                
            html_content += '</div>'
        
        return html_content
    
    def _format_mrz_results(self, items):
        """Format MRZ detection results."""
        from utils import MRZResult
        
        html_content = ""
        for i, item in enumerate(items, 1):
            html_content += f'<div style="margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #ffcc00;">'
            html_content += f'<h4 style="color: #DC2626; margin: 0;">🆔 MRZ #{i:02d}</h4>'
            
            try:
                # Use MRZResult class to parse the MRZ data
                mrz_result = MRZResult(item)
                
                # Display document type
                if mrz_result.doc_type:
                    html_content += f'<p style="margin: 5px 0;"><b>📋 Document Type:</b> <span style="color: #7C2D12;">{mrz_result.doc_type}</span></p>'
                
                # Display document ID (passport number, etc.)
                if mrz_result.doc_id:
                    html_content += f'<p style="margin: 5px 0;"><b>🆔 Document ID:</b> <span style="color: #15803D; font-family: monospace;">{mrz_result.doc_id}</span></p>'
                
                # Display personal information
                if mrz_result.surname:
                    html_content += f'<p style="margin: 5px 0;"><b>👤 Surname:</b> <span style="color: #15803D;">{mrz_result.surname}</span></p>'
                
                if mrz_result.given_name:
                    html_content += f'<p style="margin: 5px 0;"><b>👤 Given Name:</b> <span style="color: #15803D;">{mrz_result.given_name}</span></p>'
                
                if mrz_result.nationality:
                    html_content += f'<p style="margin: 5px 0;"><b>🌍 Nationality:</b> <span style="color: #15803D;">{mrz_result.nationality}</span></p>'
                
                if mrz_result.issuer:
                    html_content += f'<p style="margin: 5px 0;"><b>🏢 Issuing Country:</b> <span style="color: #15803D;">{mrz_result.issuer}</span></p>'
                
                if mrz_result.gender:
                    html_content += f'<p style="margin: 5px 0;"><b>⚥ Gender:</b> <span style="color: #15803D;">{mrz_result.gender}</span></p>'
                
                if mrz_result.date_of_birth:
                    html_content += f'<p style="margin: 5px 0;"><b>🎂 Date of Birth:</b> <span style="color: #15803D; font-family: monospace;">{mrz_result.date_of_birth}</span></p>'
                
                if mrz_result.date_of_expiry:
                    html_content += f'<p style="margin: 5px 0;"><b>⏰ Expiry Date:</b> <span style="color: #15803D; font-family: monospace;">{mrz_result.date_of_expiry}</span></p>'
                
                # Display raw MRZ text lines
                if mrz_result.raw_text:
                    html_content += f'<div style="margin: 10px 0; padding: 8px; background-color: #f0f0f0; border: 1px solid #ddd;">'
                    html_content += f'<p style="margin: 0; font-weight: bold; color: #666;">📝 Raw MRZ Text:</p>'
                    for line_num, line in enumerate(mrz_result.raw_text, 1):
                        # Escape HTML and preserve spacing
                        escaped_line = line.replace('<', '&lt;').replace('>', '&gt;')
                        html_content += f'<p style="margin: 2px 0; font-family: monospace; font-size: 12px; color: #444;">Line {line_num}: <span style="background-color: #fff; padding: 2px;">{escaped_line}</span></p>'
                    html_content += f'</div>'
                
                # Show validation status if any issues
                validation_issues = []
                for line in mrz_result.raw_text:
                    if "Validation Failed" in line:
                        validation_issues.append(line)
                
                if validation_issues:
                    html_content += f'<div style="margin: 5px 0; padding: 5px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 3px;">'
                    html_content += f'<p style="margin: 0; color: #856404;"><b>⚠️ Validation Issues:</b></p>'
                    for issue in validation_issues:
                        html_content += f'<p style="margin: 2px 0; font-size: 11px; color: #856404;">{issue}</p>'
                    html_content += f'</div>'
                
            except Exception as e:
                # Fallback if MRZ parsing fails
                html_content += f'<p style="margin: 5px 0;"><b>📋 Type:</b> <span style="color: #7C2D12;">MRZ Data</span></p>'
                html_content += f'<p style="margin: 5px 0;"><b>📊 Status:</b> <span style="color: #15803D;">Detected</span></p>'
                html_content += f'<p style="margin: 5px 0;"><b>❗ Parse Error:</b> <span style="color: #dc3545; font-size: 11px;">{str(e)}</span></p>'
                
            html_content += '</div>'
        
        return html_content
    
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
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        format_index = dialog.get_selected_format()
        if format_index is None:
            return
            
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
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
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
                         "Dynamsoft Barcode Reader - Picture & Camera Scanner\n\n"
                         "A modern Qt-based interface for barcode detection\n"
                         "using the Dynamsoft Capture Vision SDK.\n\n"
                         "Features:\n"
                         "• Picture Mode: Images & PDF support\n"
                         "• Camera Mode: Real-time scanning\n"
                         "• Multi-format barcode detection\n"
                         "• Export capabilities (TXT, CSV, JSON)\n"
                         "• Professional user interface\n\n"
                         "Supports both file-based and live camera scanning.")
    
    def enter_license_key(self):
        """Show dialog to enter a new license key."""
        global LICENSE_KEY, _LICENSE_INITIALIZED
        
        # Show custom license dialog
        dialog = LicenseDialog(LICENSE_KEY, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            license_key = dialog.get_license_key()
            
            if license_key:
                # Show confirmation dialog
                reply = QMessageBox.question(
                    self, 
                    "Update License", 
                    f"Update license key to:\n{license_key[:20]}...\n\nThe license will be tested and applied.\n\nContinue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        # Test the new license
                        test_error_code, test_error_message = LicenseManager.init_license(license_key)
                        
                        if test_error_code == EnumErrorCode.EC_OK or test_error_code == EnumErrorCode.EC_LICENSE_CACHE_USED:
                            # License is valid, update the global LICENSE_KEY
                            LICENSE_KEY = license_key
                            
                            # Reinitialize the license system
                            _LICENSE_INITIALIZED = False
                            
                            if initialize_license_once():
                                # Reinitialize the CVR instance
                                if self.cvr_instance:
                                    self.cvr_instance = None
                                
                                self.cvr_instance = CaptureVisionRouter()
                                intermediate_result_manager = self.cvr_instance.get_intermediate_result_manager()
                                self.custom_receiver = MyIntermediateResultReceiver(intermediate_result_manager)
                                intermediate_result_manager.add_result_receiver(self.custom_receiver)
                                
                                # Update camera widget if it exists
                                if hasattr(self, 'camera_widget'):
                                    self.camera_widget.initialize_dynamsoft_camera(self.cvr_instance)
                                
                                QMessageBox.information(
                                    self, 
                                    "License Updated", 
                                    "✅ License key updated successfully!\n\nThe new license is now active."
                                )
                                
                                self.log_message("✅ License key updated successfully")
                            else:
                                QMessageBox.critical(
                                    self, 
                                    "License Error", 
                                    "❌ Failed to reinitialize with new license key.\n\nPlease restart the application."
                                )
                        else:
                            QMessageBox.critical(
                                self, 
                                "Invalid License", 
                                f"❌ License validation failed:\n\nError Code: {test_error_code}\nError Message: {test_error_message}\n\nPlease check your license key and try again."
                            )
                            
                    except Exception as e:
                        QMessageBox.critical(
                            self, 
                            "License Error", 
                            f"❌ Error updating license:\n\n{str(e)}\n\nPlease try again or restart the application."
                        )

def main():
    """Main application entry point."""
    # Initialize license ONCE at startup before creating any UI
    print("🔑 Initializing Dynamsoft license...")
    if not initialize_license_once():
        print("❌ Failed to initialize license. Exiting.")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Dynamsoft Barcode Reader - Picture & Camera Scanner")
    app.setApplicationVersion("2.1")
    app.setOrganizationName("Dynamsoft")
    
    # Set application style
    app.setStyle('Fusion')  # Modern look
    
    # Create and show main window
    window = BarcodeReaderMainWindow()
    window.show()
    
    print("🚀 Starting Dynamsoft Capture Vision - Multi-Mode Scanner...")
    print("📁 Picture Mode: JPG, PNG, BMP, TIFF, WEBP, PDF")
    print("📷 Camera Mode: Real-time detection")
    print("🔍 Detection Modes: Barcode, Document, MRZ")
    print("✨ Modern Qt interface with tabbed layout")
    
    # Start the application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
