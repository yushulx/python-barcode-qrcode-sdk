"""
Main window for Document Detection Application
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QFileDialog, QLabel, QComboBox,
                                QMessageBox, QSplitter, QGroupBox, QStatusBar)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
import cv2
import numpy as np
from pathlib import Path

import config
from model_loader import load_model, get_model_info
from inference import DocumentDetector
from image_viewer import ImageViewer
from metrics_widget import MetricsWidget
from utils import get_logger, load_image, save_image
from post_processing import crop_document

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.current_image = None
        self.current_image_path = None
        self.image_paths = []
        self.current_image_index = -1
        self.current_result = None
        self.detector = None
        self.device = None
        
        # Webcam
        self.webcam = None
        self.webcam_timer = None
        self.is_webcam_active = False
        
        self.init_ui()
        self.load_model_async()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(config.WINDOW_CONFIG['title'])
        self.setGeometry(100, 100, 
                        config.WINDOW_CONFIG['width'], 
                        config.WINDOW_CONFIG['height'])
        self.setMinimumSize(config.WINDOW_CONFIG['min_width'],
                           config.WINDOW_CONFIG['min_height'])
        self.setAcceptDrops(True)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Image display
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Controls and metrics
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes (70% left, 30% right)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def create_left_panel(self) -> QWidget:
        """Create left panel with image viewers"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Image viewers
        self.image_viewer = ImageViewer()
        self.image_viewer.filesDropped.connect(self.load_image_paths)
        layout.addWidget(self.image_viewer)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        
        zoom_in_btn = QPushButton("Zoom In (+)")
        zoom_in_btn.clicked.connect(self.image_viewer.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out (-)")
        zoom_out_btn.clicked.connect(self.image_viewer.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        
        fit_btn = QPushButton("Fit to Window")
        fit_btn.clicked.connect(self.image_viewer.fit_in_view)
        zoom_layout.addWidget(fit_btn)
        
        zoom_layout.addStretch()
        
        layout.addLayout(zoom_layout)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with controls and metrics"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Control buttons group
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout()
        
        self.load_image_btn = QPushButton("📁 Load Images")
        self.load_image_btn.clicked.connect(self.load_images)
        self.load_image_btn.setMinimumHeight(40)
        control_layout.addWidget(self.load_image_btn)

        navigation_layout = QHBoxLayout()
        self.prev_image_btn = QPushButton("◀ Prev")
        self.prev_image_btn.clicked.connect(self.show_previous_image)
        self.prev_image_btn.setEnabled(False)
        navigation_layout.addWidget(self.prev_image_btn)

        self.image_counter_label = QLabel("0 / 0")
        self.image_counter_label.setAlignment(Qt.AlignCenter)
        navigation_layout.addWidget(self.image_counter_label)

        self.next_image_btn = QPushButton("Next ▶")
        self.next_image_btn.clicked.connect(self.show_next_image)
        self.next_image_btn.setEnabled(False)
        navigation_layout.addWidget(self.next_image_btn)

        control_layout.addLayout(navigation_layout)
        
        self.webcam_btn = QPushButton("📷 Start Webcam")
        self.webcam_btn.clicked.connect(self.toggle_webcam)
        self.webcam_btn.setMinimumHeight(40)
        control_layout.addWidget(self.webcam_btn)
        
        self.process_btn = QPushButton("🔍 Process Image")
        self.process_btn.clicked.connect(self.process_image)
        self.process_btn.setEnabled(False)
        self.process_btn.setMinimumHeight(40)
        control_layout.addWidget(self.process_btn)
        
        self.export_btn = QPushButton("💾 Export Results")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumHeight(40)
        control_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_all)
        self.clear_btn.setMinimumHeight(40)
        control_layout.addWidget(self.clear_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Metrics widget
        self.metrics_widget = MetricsWidget()
        layout.addWidget(self.metrics_widget)
        
        return panel
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Images", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.load_images)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def load_model_async(self):
        """Load model asynchronously"""
        try:
            model_name = config.DEFAULT_MODEL
            self.statusBar.showMessage(f"Loading model: {model_name}...")
            logger.info(f"Loading model: {model_name}...")
            
            # Load model
            model, device = load_model(model_name)
            self.detector = DocumentDetector(model, device)
            self.device = device
            
            # Update metrics widget
            model_info = get_model_info(model, model_name)
            self.metrics_widget.set_model_info(model_info)
            self.metrics_widget.set_device(device)
            
            self.statusBar.showMessage(f"Model {model_name} loaded successfully", 3000)
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load model:\n{str(e)}")
            self.statusBar.showMessage("Failed to load model")
    
    def load_images(self):
        """Load one or more images from disk."""
        file_filter = "Images (" + " ".join(config.SUPPORTED_FORMATS) + ")"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Image", "", file_filter
        )

        if file_paths:
            self.load_image_paths(file_paths)

    def load_image_paths(self, file_paths: list):
        """Load a new image collection from file paths."""
        valid_paths = [path for path in file_paths if self.is_supported_image_path(path)]
        if not valid_paths:
            self.statusBar.showMessage("No supported images selected", 3000)
            return

        if self.is_webcam_active:
            self.stop_webcam()

        self.image_paths = valid_paths
        self.current_image_index = 0
        self.show_image_at_index(0)

    def is_supported_image_path(self, file_path: str) -> bool:
        """Return True when the file extension is supported."""
        suffix = Path(file_path).suffix.lower()
        supported_suffixes = {
            pattern.replace('*', '').lower()
            for pattern in config.SUPPORTED_FORMATS
        }
        return suffix in supported_suffixes

    def show_image_at_index(self, index: int):
        """Display and process the image at the given collection index."""
        if index < 0 or index >= len(self.image_paths):
            return

        file_path = self.image_paths[index]

        try:
            self.current_image = load_image(file_path)
            self.current_image_path = file_path
            self.current_image_index = index
            self.current_result = None

            self.image_viewer.set_image(self.current_image)
            self.process_btn.setEnabled(True)
            self.export_btn.setEnabled(False)
            self.update_image_navigation()
            self.statusBar.showMessage(f"Loaded: {Path(file_path).name}")

            self.process_image()

        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load image:\n{str(e)}")

    def show_previous_image(self):
        """Display the previous image in the loaded collection."""
        if self.current_image_index > 0:
            self.show_image_at_index(self.current_image_index - 1)

    def show_next_image(self):
        """Display the next image in the loaded collection."""
        if self.current_image_index + 1 < len(self.image_paths):
            self.show_image_at_index(self.current_image_index + 1)

    def update_image_navigation(self):
        """Update navigator controls for the current image collection."""
        has_images = len(self.image_paths) > 0 and not self.is_webcam_active
        self.prev_image_btn.setEnabled(has_images and self.current_image_index > 0)
        self.next_image_btn.setEnabled(
            has_images and self.current_image_index < len(self.image_paths) - 1
        )

        if has_images:
            self.image_counter_label.setText(
                f"{self.current_image_index + 1} / {len(self.image_paths)}"
            )
        else:
            self.image_counter_label.setText("0 / 0")
    
    def toggle_webcam(self):
        """Toggle webcam on/off"""
        if not self.is_webcam_active:
            self.start_webcam()
        else:
            self.stop_webcam()
    
    def start_webcam(self):
        """Start webcam capture"""
        try:
            self.webcam = cv2.VideoCapture(0)
            if not self.webcam.isOpened():
                raise RuntimeError("Failed to open webcam")
            
            self.is_webcam_active = True
            self.webcam_btn.setText("⏹️ Stop Webcam")
            self.load_image_btn.setEnabled(False)
            self.process_btn.setEnabled(False)
            self.prev_image_btn.setEnabled(False)
            self.next_image_btn.setEnabled(False)
            
            # Start timer for frame capture
            self.webcam_timer = QTimer()
            self.webcam_timer.timeout.connect(self.capture_webcam_frame)
            self.webcam_timer.start(33)  # ~30 FPS
            
            self.statusBar.showMessage("Webcam started")
            
        except Exception as e:
            logger.error(f"Failed to start webcam: {e}")
            QMessageBox.warning(self, "Error", f"Failed to start webcam:\n{str(e)}")
    
    def stop_webcam(self):
        """Stop webcam capture"""
        if self.webcam_timer:
            self.webcam_timer.stop()
            self.webcam_timer = None
        
        if self.webcam:
            self.webcam.release()
            self.webcam = None
        
        self.is_webcam_active = False
        self.webcam_btn.setText("📷 Start Webcam")
        self.load_image_btn.setEnabled(True)
        self.process_btn.setEnabled(self.current_image is not None)
        self.update_image_navigation()

        if self.image_paths and 0 <= self.current_image_index < len(self.image_paths):
            self.show_image_at_index(self.current_image_index)
            return
        
        self.statusBar.showMessage("Webcam stopped")
    
    def capture_webcam_frame(self):
        """Capture and process webcam frame"""
        if not self.webcam:
            return
        
        ret, frame = self.webcam.read()
        if not ret:
            return
        
        self.current_image = frame
        
        # Process frame
        if self.detector:
            self.current_result = self.detector.detect(frame)
            self.update_visualization()
            
            # Update metrics
            self.metrics_widget.update_metrics(
                self.current_result['metrics'],
                frame.shape,
                self.current_result['corners'] is not None
            )
    
    def process_image(self):
        """Process current image"""
        if self.current_image is None or self.detector is None:
            return
        
        try:
            self.statusBar.showMessage("Processing...")
            
            # Run detection
            self.current_result = self.detector.detect(self.current_image)
            
            # Update visualization
            self.update_visualization()
            
            # Update metrics
            self.metrics_widget.update_metrics(
                self.current_result['metrics'],
                self.current_image.shape,
                self.current_result['corners'] is not None
            )
            
            # Enable export
            self.export_btn.setEnabled(True)
            
            self.statusBar.showMessage("Processing complete", 2000)
            
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            QMessageBox.warning(self, "Error", f"Failed to process image:\n{str(e)}")
            self.statusBar.showMessage("Processing failed")
    
    def update_visualization(self):
        """Update image visualization (Overlay only)"""
        if self.current_result is None:
            return
        
        # Always show overlay
        self.image_viewer.set_image(self.current_result['overlay'])
    
    def export_results(self):
        """Export detection results"""
        if self.current_result is None:
            return
        
        # Ask user what to export
        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not export_dir:
            return
        
        export_path = Path(export_dir)
        timestamp = Path(config.OUTPUT_DIR).name
        
        try:
            # Export overlay
            overlay_path = export_path / f"overlay_{timestamp}.png"
            save_image(self.current_result['overlay'], str(overlay_path))
            
            # Export mask
            mask_path = export_path / f"mask_{timestamp}.png"
            save_image(self.current_result['mask_colored'], str(mask_path))
            
            # Export cropped document if corners detected
            if self.current_result['corners'] is not None:
                cropped = crop_document(self.current_image, self.current_result['corners'])
                cropped_path = export_path / f"document_{timestamp}.png"
                save_image(cropped, str(cropped_path))
            
            QMessageBox.information(self, "Success", 
                                   f"Results exported to:\n{export_dir}")
            self.statusBar.showMessage(f"Exported to {export_dir}", 3000)
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            QMessageBox.warning(self, "Error", f"Failed to export results:\n{str(e)}")
    
    def clear_all(self):
        """Clear all data"""
        self.current_image = None
        self.current_image_path = None
        self.image_paths = []
        self.current_image_index = -1
        self.current_result = None
        self.image_viewer.clear()
        self.process_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.update_image_navigation()
        self.metrics_widget.reset_statistics()
        self.statusBar.showMessage("Cleared")

    def dragEnterEvent(self, event):
        """Accept supported image files dragged onto the window."""
        file_paths = self._extract_dropped_image_paths(event)
        if file_paths:
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        """Load dropped image files."""
        file_paths = self._extract_dropped_image_paths(event)
        if file_paths:
            event.acceptProposedAction()
            self.load_image_paths(file_paths)
            return
        super().dropEvent(event)

    def _extract_dropped_image_paths(self, event) -> list:
        """Collect supported local image paths from a drop event."""
        mime_data = event.mimeData()
        if mime_data is None or not mime_data.hasUrls():
            return []

        file_paths = []
        for url in mime_data.urls():
            if not url.isLocalFile():
                continue

            local_path = url.toLocalFile()
            if self.is_supported_image_path(local_path):
                file_paths.append(local_path)

        return file_paths
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Document Detection Application</h2>
        <p>Deep learning-based document boundary detection using DeepLabV3 semantic segmentation.</p>
        <p><b>Model:</b> DeepLabV3-MobileNetV3-Large</p>
        <p><b>Framework:</b> PyTorch + PySide6</p>
        <p><b>Reference:</b> <a href='https://learnopencv.com/deep-learning-based-document-segmentation-using-semantic-segmentation-deeplabv3-on-custom-dataset/'>
        LearnOpenCV Article</a></p>
        """
        QMessageBox.about(self, "About", about_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop webcam if active
        if self.is_webcam_active:
            self.stop_webcam()
        
        event.accept()
