"""
Document Detection GUI Application
A PySide6-based GUI for document detection with drag-and-drop support,
dual image views (original with overlay and rectified), and export functionality.
"""

import sys
import os
import warnings
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QSplitter, QFileDialog, 
    QMessageBox, QProgressBar, QScrollArea, QFrame, QGroupBox,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, QObject, Signal, QMimeData, QSize, QTimer
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QFont, QIcon

from ultralytics import YOLO

# Suppress warnings
os.environ['ORT_LOGGING_LEVEL'] = '4'
warnings.filterwarnings('ignore')

class DocumentDetector:
    """Core document detection functionality"""
    
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model (PyTorch first, then ONNX fallback)"""
        model_paths = [
            ("runs/segment/train/weights/best.pt", "PyTorch"),
            ("runs/segment/train/weights/best.onnx", "ONNX"),
            ("yolo11s-seg.pt", "Pre-trained")
        ]
        
        for model_path, model_type in model_paths:
            if os.path.exists(model_path):
                try:
                    self.model = YOLO(model_path)
                    print(f"✅ {model_type} model loaded: {model_path}")
                    return
                except Exception as e:
                    print(f"❌ Failed to load {model_type} model: {e}")
                    continue
        
        raise RuntimeError("No working model found!")
    
    @staticmethod
    def order_points(pts):
        """Order points in clockwise order starting from top-left"""
        s = pts.sum(1)
        d = np.diff(pts, axis=1).ravel()
        return np.array([
            pts[np.argmin(s)],      # top-left
            pts[np.argmin(d)],      # top-right
            pts[np.argmax(s)],      # bottom-right
            pts[np.argmax(d)]       # bottom-left
        ], dtype="float32")
    
    @staticmethod
    def polygon_to_quad(poly_xy: np.ndarray) -> np.ndarray:
        """
        Convert polygon to quadrilateral using approxPolyDP with multiple tolerances.
        poly_xy: (K,2) float32 in original image coordinates.
        Returns ordered 4x2 quad (float32). Uses approxPolyDP, with minAreaRect fallback.
        """
        cnt = poly_xy.reshape(-1, 1, 2).astype(np.float32)
        peri = cv2.arcLength(cnt, True)

        # Try several epsilons, coarse to fine for better boundary coverage
        for eps in (0.03, 0.025, 0.02, 0.015, 0.01):
            approx = cv2.approxPolyDP(cnt, eps * peri, True)
            if len(approx) == 4:
                return DocumentDetector.order_points(approx.reshape(-1, 2).astype(np.float32))

        # Fallback: min area rectangle
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect).astype(np.float32)  # (4,2)
        return DocumentDetector.order_points(box)
    
    def detect_document(self, image: np.ndarray, conf: float = 0.25) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Detect document in image and return overlay, rectified image, and coordinates
        Uses res.masks.xy for direct coordinate extraction (no scaling needed)
        
        Returns:
            Tuple of (overlay_image, rectified_image, quad_coordinates) or None if no detection
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        # Get original dimensions
        orig_h, orig_w = image.shape[:2]
        print(f"Debug - Image size: {orig_w}x{orig_h}")
        
        # Run inference - YOLO will handle sizing automatically
        try:
            results = self.model(image, imgsz=640, conf=conf, device='cpu')[0]
        except Exception as e:
            raise RuntimeError(f"Inference failed: {e}")
        
        if results.masks is None or len(results.masks.data) == 0:
            return None
        
        # Use res.masks.xy for coordinates directly in original image space
        # This eliminates the need for complex scaling calculations!
        polys = results.masks.xy  # list of N (K,2) arrays in original image coords
        if not polys:
            return None
        
        # Pick the largest polygon by area
        areas = [cv2.contourArea(p.astype(np.float32)) for p in polys]
        idx = int(np.argmax(areas))
        poly = polys[idx].astype(np.float32)
        
        print(f"Debug - Selected polygon has {len(poly)} points, area: {areas[idx]:.0f}")
        
        # Convert polygon to quadrilateral using improved method
        quad = self.polygon_to_quad(poly)
        if quad is None:
            return None
        
        # Create overlay image
        overlay = image.copy()
        cv2.polylines(overlay, [quad.astype(int)], True, (0, 255, 0), 3)
        
        # Add corner points with better precision
        for i, point in enumerate(quad):
            x, y = int(round(point[0])), int(round(point[1]))
            cv2.circle(overlay, (x, y), 8, (255, 0, 0), -1)
            cv2.putText(overlay, str(i), (x + 10, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Calculate rectified dimensions
        h, w = image.shape[:2]
        w_out = int(max(np.linalg.norm(quad[1] - quad[0]), np.linalg.norm(quad[2] - quad[3])))
        h_out = int(max(np.linalg.norm(quad[2] - quad[1]), np.linalg.norm(quad[3] - quad[0])))
        
        # Perspective transform
        dst = np.array([[0, 0], [w_out - 1, 0], [w_out - 1, h_out - 1], [0, h_out - 1]], dtype="float32")
        M = cv2.getPerspectiveTransform(quad, dst)
        rectified = cv2.warpPerspective(image, M, (w_out, h_out))
        
        return overlay, rectified, quad


class DropLabel(QLabel):
    """QLabel that supports drag and drop"""
    
    file_dropped = Signal(str)
    
    def __init__(self, text="Drop image here"):
        super().__init__(text)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                min-height: 200px;
                font-size: 14px;
                color: #666;
            }
            QLabel:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)
        self.original_text = text
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self.is_image_file(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self.setStyleSheet(self.styleSheet().replace("#f0f8ff", "#e6f3ff"))
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("#e6f3ff", "#f0f8ff"))
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self.is_image_file(file_path):
                self.file_dropped.emit(file_path)
                event.acceptProposedAction()
        self.setStyleSheet(self.styleSheet().replace("#e6f3ff", "#f0f8ff"))
    
    @staticmethod
    def is_image_file(file_path):
        """Check if file is a supported image format"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        return Path(file_path).suffix.lower() in valid_extensions
    
    def set_pixmap_scaled(self, pixmap: QPixmap):
        """Set pixmap with scaling to fit label"""
        if pixmap.isNull():
            self.setText(self.original_text)
            return
        
        scaled_pixmap = pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)


class DetectionWorker(QObject):
    """Worker thread for document detection"""
    
    finished = Signal(object)  # (overlay, rectified, quad) or None
    error = Signal(str)
    
    def __init__(self, detector: DocumentDetector, image: np.ndarray, conf: float):
        super().__init__()
        self.detector = detector
        self.image = image
        self.conf = conf
    
    def run(self):
        try:
            print("DetectionWorker: Starting detection...")
            result = self.detector.detect_document(self.image, self.conf)
            print("DetectionWorker: Detection completed successfully")
            self.finished.emit(result)
        except Exception as e:
            print(f"DetectionWorker: Error occurred - {e}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class DocumentDetectorGUI(QMainWindow):
    """Main GUI application"""
    
    def __init__(self):
        super().__init__()
        self.detector = None
        self.current_image = None
        self.current_overlay = None
        self.current_rectified = None
        self.current_quad = None
        
        # Thread management
        self.detection_thread = None
        self.detection_worker = None
        
        self.init_ui()
        self.init_detector()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Document Detection GUI")
        self.setGeometry(100, 100, 1400, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel for controls
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel)
        
        # Right panel for images
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, stretch=3)
        
        # Status bar
        self.statusBar().showMessage("Ready - Drop an image or click Browse to start")
    
    def create_left_panel(self):
        """Create the left control panel"""
        panel = QFrame()
        panel.setMaximumWidth(300)
        panel.setFrameStyle(QFrame.Shape.Box)
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Document Detection")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Browse button
        self.browse_btn = QPushButton("📁 Browse Image")
        self.browse_btn.clicked.connect(self.browse_image)
        layout.addWidget(self.browse_btn)
        
        # Detection button
        self.detect_btn = QPushButton("🔍 Detect Document")
        self.detect_btn.clicked.connect(self.detect_document)
        self.detect_btn.setEnabled(False)
        layout.addWidget(self.detect_btn)
        
        # Save button
        self.save_btn = QPushButton("💾 Save Rectified")
        self.save_btn.clicked.connect(self.save_rectified)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        layout.addWidget(QLabel())  # Spacer
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Info display
        info_group = QGroupBox("Detection Info")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(200)
        self.info_text.setFont(QFont("Consolas", 9))
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        return panel
    
    def create_right_panel(self):
        """Create the right image panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Image splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Original image with overlay
        original_group = QGroupBox("Original with Overlay")
        original_layout = QVBoxLayout(original_group)
        
        self.original_scroll = QScrollArea()
        self.original_label = DropLabel("Drop image here or click Browse")
        self.original_label.file_dropped.connect(self.load_image)
        self.original_scroll.setWidget(self.original_label)
        self.original_scroll.setWidgetResizable(True)
        original_layout.addWidget(self.original_scroll)
        
        splitter.addWidget(original_group)
        
        # Rectified image
        rectified_group = QGroupBox("Rectified Document")
        rectified_layout = QVBoxLayout(rectified_group)
        
        self.rectified_scroll = QScrollArea()
        self.rectified_label = QLabel("Rectified document will appear here")
        self.rectified_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rectified_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                background-color: #f5f5f5;
                min-height: 200px;
                color: #888;
            }
        """)
        self.rectified_scroll.setWidget(self.rectified_label)
        self.rectified_scroll.setWidgetResizable(True)
        rectified_layout.addWidget(self.rectified_scroll)
        
        splitter.addWidget(rectified_group)
        splitter.setSizes([1, 1])  # Equal sizes
        
        layout.addWidget(splitter)
        
        return panel
    
    def init_detector(self):
        """Initialize the document detector"""
        try:
            self.detector = DocumentDetector()
            self.statusBar().showMessage("Model loaded successfully - Ready for detection")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load model: {e}")
            self.statusBar().showMessage("Error loading model")
    
    def browse_image(self):
        """Browse for an image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp *.tiff *.tif)"
        )
        
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path: str):
        """Load an image from file path"""
        try:
            # Load image
            self.current_image = cv2.imread(file_path)
            if self.current_image is None:
                raise ValueError("Failed to load image")
            
            # Convert to Qt format and display
            height, width, channel = self.current_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(
                cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB).data,
                width, height, bytes_per_line, QImage.Format.Format_RGB888
            )
            
            pixmap = QPixmap.fromImage(q_image)
            self.original_label.set_pixmap_scaled(pixmap)
            
            # Update UI
            self.detect_btn.setEnabled(True)
            self.save_btn.setEnabled(False)
            self.rectified_label.setText("Rectified document will appear here")
            self.rectified_label.setPixmap(QPixmap())
            
            # Update info
            file_name = Path(file_path).name
            self.info_text.setText(f"Loaded: {file_name}\nDimensions: {width}x{height}\nReady for detection")
            self.statusBar().showMessage(f"Loaded: {file_name}")
            
            # Reset detection results
            self.current_overlay = None
            self.current_rectified = None
            self.current_quad = None

            self.detect_document()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
    
    def detect_document(self):
        """Run document detection"""
        if self.current_image is None or self.detector is None:
            print("Detection skipped: No image or detector")
            return
        
        try:
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.detect_btn.setEnabled(False)
            self.statusBar().showMessage("Detecting document...")
            
            # Clean up any existing worker/thread
            self.cleanup_detection_thread()
            
            # Create worker thread
            self.detection_worker = DetectionWorker(self.detector, self.current_image, 0.25)
            self.detection_thread = QThread()
            self.detection_worker.moveToThread(self.detection_thread)
            
            # Connect signals
            self.detection_thread.started.connect(self.detection_worker.run)
            self.detection_worker.finished.connect(self.on_detection_finished)
            self.detection_worker.error.connect(self.on_detection_error)
            self.detection_worker.finished.connect(self.cleanup_detection_thread)
            
            # Start detection
            print("Starting detection thread...")
            self.detection_thread.start()
            
        except Exception as e:
            print(f"Error in detect_document: {e}")
            import traceback
            traceback.print_exc()
            self.progress_bar.setVisible(False)
            self.detect_btn.setEnabled(True)
            QMessageBox.critical(self, "Detection Error", f"Failed to start detection: {e}")
    
    def cleanup_detection_thread(self):
        """Safely cleanup detection thread and worker"""
        try:
            # Clean up worker
            if self.detection_worker is not None:
                self.detection_worker.deleteLater()
                self.detection_worker = None
            
            # Clean up thread
            if self.detection_thread is not None:
                if self.detection_thread.isRunning():
                    print("Stopping running detection thread...")
                    self.detection_thread.quit()
                    if not self.detection_thread.wait(3000):  # Wait up to 3 seconds
                        print("Force terminating detection thread...")
                        self.detection_thread.terminate()
                        self.detection_thread.wait()
                
                self.detection_thread.deleteLater()
                self.detection_thread = None
                print("Detection thread cleaned up")
                
        except RuntimeError as e:
            # Handle "Internal C++ object already deleted" gracefully
            print(f"Thread cleanup warning (expected): {e}")
            self.detection_thread = None
            self.detection_worker = None
        except Exception as e:
            print(f"Error during thread cleanup: {e}")
            self.detection_thread = None
            self.detection_worker = None
    
    def on_detection_finished(self, result):
        """Handle detection completion"""
        try:
            self.progress_bar.setVisible(False)
            self.detect_btn.setEnabled(True)
            
            if result is None:
                QMessageBox.information(self, "No Detection", "No document detected in the image.")
                self.statusBar().showMessage("No document detected")
                self.info_text.append("\n❌ No document detected")
                return
            
            overlay, rectified, quad = result
            self.current_overlay = overlay
            self.current_rectified = rectified
            self.current_quad = quad
            
            # Display overlay - with error handling
            try:
                height, width, channel = overlay.shape
                bytes_per_line = 3 * width
                overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
                q_image = QImage(
                    overlay_rgb.data,
                    width, height, bytes_per_line, QImage.Format.Format_RGB888
                )
                pixmap = QPixmap.fromImage(q_image)
                self.original_label.set_pixmap_scaled(pixmap)
            except Exception as e:
                print(f"Error displaying overlay: {e}")
                QMessageBox.warning(self, "Display Error", f"Failed to display overlay: {e}")
            
            # Display rectified - with error handling
            try:
                rect_height, rect_width, _ = rectified.shape
                rect_bytes_per_line = 3 * rect_width
                rectified_rgb = cv2.cvtColor(rectified, cv2.COLOR_BGR2RGB)
                rect_q_image = QImage(
                    rectified_rgb.data,
                    rect_width, rect_height, rect_bytes_per_line, QImage.Format.Format_RGB888
                )
                rect_pixmap = QPixmap.fromImage(rect_q_image)
                
                # Scale to fit
                scaled_rect_pixmap = rect_pixmap.scaled(
                    self.rectified_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.rectified_label.setPixmap(scaled_rect_pixmap)
            except Exception as e:
                print(f"Error displaying rectified image: {e}")
                QMessageBox.warning(self, "Display Error", f"Failed to display rectified image: {e}")
            
            # Update info - with error handling
            try:
                height, width = overlay.shape[:2]
                rect_height, rect_width = rectified.shape[:2]
                
                info_text = f"✅ Document detected!\n"
                info_text += f"Original: {width}x{height}\n"
                info_text += f"Rectified: {rect_width}x{rect_height}\n\n"
                info_text += "Corner coordinates:\n"
                for i, point in enumerate(quad):
                    info_text += f"  {i}: ({point[0]:.1f}, {point[1]:.1f})\n"
                
                self.info_text.setText(info_text)
                self.save_btn.setEnabled(True)
                self.statusBar().showMessage("Document detected successfully")
            except Exception as e:
                print(f"Error updating info: {e}")
                
        except Exception as e:
            print(f"Critical error in on_detection_finished: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Critical Error", f"Unexpected error: {e}")
            self.progress_bar.setVisible(False)
            self.detect_btn.setEnabled(True)
    
    def on_detection_error(self, error_msg):
        """Handle detection error"""
        try:
            print(f"Detection error: {error_msg}")
            self.progress_bar.setVisible(False)
            self.detect_btn.setEnabled(True)
            QMessageBox.critical(self, "Detection Error", f"Error during detection: {error_msg}")
            self.statusBar().showMessage("Detection failed")
            self.info_text.append(f"\n❌ Detection failed: {error_msg}")
        except Exception as e:
            print(f"Error in error handler: {e}")
            # Don't show another error dialog as it might cause recursion
    
    def save_rectified(self):
        """Save the rectified document"""
        if self.current_rectified is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Rectified Document",
            "rectified_document.jpg",
            "JPEG Files (*.jpg);;PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            try:
                cv2.imwrite(file_path, self.current_rectified)
                QMessageBox.information(self, "Success", f"Rectified document saved to:\n{file_path}")
                self.statusBar().showMessage(f"Saved: {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image: {e}")
    
    def resizeEvent(self, event):
        """Handle window resize to update image scaling"""
        super().resizeEvent(event)
        # Use timer to avoid excessive updates during resize
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        
        self._resize_timer = QTimer()
        self._resize_timer.timeout.connect(self._update_image_scaling)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.start(100)  # 100ms delay
    
    def _update_image_scaling(self):
        """Update image scaling after resize"""
        # Update original image
        if self.current_overlay is not None:
            height, width, channel = self.current_overlay.shape
            bytes_per_line = 3 * width
            q_image = QImage(
                cv2.cvtColor(self.current_overlay, cv2.COLOR_BGR2RGB).data,
                width, height, bytes_per_line, QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(q_image)
            self.original_label.set_pixmap_scaled(pixmap)
        
        # Update rectified image
        if self.current_rectified is not None:
            height, width, channel = self.current_rectified.shape
            bytes_per_line = 3 * width
            q_image = QImage(
                cv2.cvtColor(self.current_rectified, cv2.COLOR_BGR2RGB).data,
                width, height, bytes_per_line, QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(q_image)
            
            scaled_pixmap = pixmap.scaled(
                self.rectified_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.rectified_label.setPixmap(scaled_pixmap)
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
            print("Application closing, cleaning up threads...")
            self.cleanup_detection_thread()
            print("Application closing...")
            event.accept()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            event.accept()


def main():
    """Main entry point"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Document Detection GUI")
        app.setOrganizationName("Document Detection")
        
        # Set application style
        app.setStyle("Fusion")
        
        # Create and show main window
        window = DocumentDetectorGUI()
        window.show()
        
        print("Starting GUI application...")
        return app.exec()
        
    except Exception as e:
        print(f"Critical error starting application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
