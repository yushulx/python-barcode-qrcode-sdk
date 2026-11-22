#!/usr/bin/env python3
"""
YOLO Dataset Visualizer - GUI Application with PySide6

A comprehensive image viewer to visualize YOLO segmentation datasets with annotation overlays.
Features:
- Browse through all training/validation images
- Overlay segmentation polygons
- Show annotation details
- Navigate with keyboard shortcuts
- Zoom and pan functionality
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QPushButton, QLabel, QSlider, QComboBox,
                               QScrollArea, QTextEdit, QSplitter, QGroupBox,
                               QCheckBox, QSpinBox, QColorDialog, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QKeySequence, QShortcut, QMouseEvent

class ImageLabel(QLabel):
    """Custom QLabel with zoom and pan functionality."""
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("border: 1px solid gray;")
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False
        self.last_pos = None
        self.original_pixmap = None
        
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        zoom_in = delta > 0
        
        if zoom_in:
            self.zoom_factor = min(self.zoom_factor * 1.2, 5.0)
        else:
            self.zoom_factor = max(self.zoom_factor / 1.2, 0.1)
        
        self.update_display()
        
    def mousePressEvent(self, ev):
        """Start panning."""
        if ev.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_pos = ev.position()
            
    def mouseMoveEvent(self, ev):
        """Handle panning."""
        if self.dragging and self.last_pos:
            delta = ev.position() - self.last_pos
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_pos = ev.position()
            self.update_display()
            
    def mouseReleaseEvent(self, ev):
        """Stop panning."""
        if ev.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            
    def reset_view(self):
        """Reset zoom and pan."""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.update_display()
        
    def update_display(self):
        """Update the displayed image with current zoom and pan."""
        if self.original_pixmap:
            self.setPixmap(self.original_pixmap)

class YOLODatasetVisualizer(QMainWindow):
    """Main application window for YOLO dataset visualization."""
    
    def __init__(self):
        super().__init__()
        self.dataset_path = Path("dataset")
        self.current_split = "train"  # train or val
        self.current_index = 0
        self.image_paths = []
        self.show_annotations = True
        self.polygon_color = QColor(0, 255, 0)
        self.point_color = QColor(255, 0, 0)
        self.line_thickness = 2
        
        self.init_ui()
        self.load_dataset()
        self.setup_shortcuts()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("YOLO Dataset Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Image display
        right_panel = self.create_image_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
    def create_control_panel(self):
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Dataset selection
        dataset_group = QGroupBox("Dataset Selection")
        dataset_layout = QVBoxLayout(dataset_group)
        
        self.split_combo = QComboBox()
        self.split_combo.addItems(["train", "val"])
        self.split_combo.currentTextChanged.connect(self.on_split_changed)
        dataset_layout.addWidget(QLabel("Split:"))
        dataset_layout.addWidget(self.split_combo)
        
        layout.addWidget(dataset_group)
        
        # Navigation
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(nav_group)
        
        # Image counter
        self.image_counter = QLabel("0 / 0")
        nav_layout.addWidget(self.image_counter)
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.prev_btn.clicked.connect(self.prev_image)
        self.next_btn.clicked.connect(self.next_image)
        nav_buttons.addWidget(self.prev_btn)
        nav_buttons.addWidget(self.next_btn)
        nav_layout.addLayout(nav_buttons)
        
        # Image slider
        self.image_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_slider.valueChanged.connect(self.on_slider_changed)
        nav_layout.addWidget(self.image_slider)
        
        layout.addWidget(nav_group)
        
        # Display options
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout(display_group)
        
        self.show_annotations_cb = QCheckBox("Show Annotations")
        self.show_annotations_cb.setChecked(True)
        self.show_annotations_cb.toggled.connect(self.on_annotations_toggled)
        display_layout.addWidget(self.show_annotations_cb)
        
        # Line thickness
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel("Line Thickness:"))
        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(1, 10)
        self.thickness_spin.setValue(2)
        self.thickness_spin.valueChanged.connect(self.on_thickness_changed)
        thickness_layout.addWidget(self.thickness_spin)
        display_layout.addLayout(thickness_layout)
        
        # Color buttons
        color_layout = QHBoxLayout()
        self.polygon_color_btn = QPushButton("Polygon Color")
        self.polygon_color_btn.clicked.connect(self.choose_polygon_color)
        self.point_color_btn = QPushButton("Point Color")
        self.point_color_btn.clicked.connect(self.choose_point_color)
        color_layout.addWidget(self.polygon_color_btn)
        color_layout.addWidget(self.point_color_btn)
        display_layout.addLayout(color_layout)
        
        # Reset view button
        self.reset_view_btn = QPushButton("Reset View")
        self.reset_view_btn.clicked.connect(self.reset_view)
        display_layout.addWidget(self.reset_view_btn)
        
        layout.addWidget(display_group)
        
        # Image info
        info_group = QGroupBox("Image Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(200)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
        
    def create_image_panel(self):
        """Create the right image display panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Image display
        self.image_scroll = QScrollArea()
        self.image_label = ImageLabel()
        self.image_scroll.setWidget(self.image_label)
        self.image_scroll.setWidgetResizable(True)
        layout.addWidget(self.image_scroll)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        return panel
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Navigation shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.prev_image)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.next_image)
        QShortcut(QKeySequence(Qt.Key.Key_Home), self, self.first_image)
        QShortcut(QKeySequence(Qt.Key.Key_End), self, self.last_image)
        
        # Display shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.toggle_annotations)
        QShortcut(QKeySequence(Qt.Key.Key_R), self, self.reset_view)
        
    def load_dataset(self):
        """Load the dataset images."""
        if not self.dataset_path.exists():
            QMessageBox.warning(self, "Error", "Dataset folder not found!")
            return
            
        images_path = self.dataset_path / "images" / self.current_split
        if not images_path.exists():
            QMessageBox.warning(self, "Error", f"Images folder not found: {images_path}")
            return
            
        # Get all image files
        self.image_paths = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            self.image_paths.extend(list(images_path.glob(ext)))
        
        self.image_paths.sort()
        
        if not self.image_paths:
            QMessageBox.warning(self, "Error", "No images found in dataset!")
            return
            
        # Setup slider
        self.image_slider.setRange(0, len(self.image_paths) - 1)
        self.image_slider.setValue(0)
        
        # Load first image
        self.current_index = 0
        self.load_current_image()
        
    def load_current_image(self):
        """Load and display the current image with annotations."""
        if not self.image_paths or self.current_index >= len(self.image_paths):
            return
            
        img_path = self.image_paths[self.current_index]
        
        # Load image
        img = cv2.imread(str(img_path))
        if img is None:
            self.status_label.setText(f"Failed to load: {img_path.name}")
            return
            
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Draw annotations if enabled
        if self.show_annotations:
            img = self.draw_annotations(img, img_path)
            
        # Convert to QPixmap
        height, width, channel = img.shape
        bytes_per_line = 3 * width
        q_image = QImage(img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # Scale to fit while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.original_pixmap = scaled_pixmap
        self.image_label.setPixmap(scaled_pixmap)
        
        # Update UI
        self.update_image_info(img_path)
        self.update_navigation()
        
    def draw_annotations(self, img, img_path):
        """Draw segmentation annotations on the image."""
        # Find corresponding label file
        label_path = (self.dataset_path / "labels" / self.current_split / 
                     (img_path.stem + ".txt"))
        
        if not label_path.exists():
            return img
            
        h, w = img.shape[:2]
        
        try:
            with open(label_path, 'r') as f:
                line = f.readline().strip()
                if not line:
                    return img
                
                parts = line.split()
                if len(parts) < 9:  # class_id + 4 points (x,y each)
                    return img
                
                # Parse normalized coordinates
                coords = list(map(float, parts[1:]))  # Skip class_id
                
                # Convert normalized coords to pixel coords
                points = []
                for i in range(0, len(coords), 2):
                    x = int(coords[i] * w)
                    y = int(coords[i+1] * h)
                    points.append([x, y])
                
                # Draw polygon
                points = np.array(points, dtype=np.int32)
                cv2.polylines(img, [points], True, 
                            (self.polygon_color.red(), self.polygon_color.green(), self.polygon_color.blue()), 
                            self.line_thickness)
                
                # Draw corner points
                for point in points:
                    cv2.circle(img, tuple(point), 5, 
                             (self.point_color.red(), self.point_color.green(), self.point_color.blue()), 
                             -1)
                    
        except Exception as e:
            print(f"Error drawing annotations: {e}")
            
        return img
        
    def update_image_info(self, img_path):
        """Update the image information display."""
        # Get image info
        img = cv2.imread(str(img_path))
        h, w = img.shape[:2] if img is not None else (0, 0)
        
        # Get label info
        label_path = (self.dataset_path / "labels" / self.current_split / 
                     (img_path.stem + ".txt"))
        
        label_info = "No annotation file"
        if label_path.exists():
            try:
                with open(label_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        parts = content.split()
                        if len(parts) >= 9:
                            class_id = parts[0]
                            coords = [float(x) for x in parts[1:]]
                            label_info = f"Class: {class_id}\\nCoordinates: {len(coords)//2} points"
                        else:
                            label_info = "Invalid annotation format"
                    else:
                        label_info = "Empty annotation file"
            except Exception as e:
                label_info = f"Error reading annotation: {e}"
        
        info_text = f"""
File: {img_path.name}
Path: {img_path}
Image Size: {w} x {h}
Split: {self.current_split}
Index: {self.current_index + 1} / {len(self.image_paths)}

Annotation: {label_info}
        """.strip()
        
        self.info_text.setText(info_text)
        
    def update_navigation(self):
        """Update navigation controls."""
        total = len(self.image_paths)
        current = self.current_index + 1
        
        self.image_counter.setText(f"{current} / {total}")
        self.image_slider.blockSignals(True)
        self.image_slider.setValue(self.current_index)
        self.image_slider.blockSignals(False)
        
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < total - 1)
        
        self.status_label.setText(f"Loaded: {self.image_paths[self.current_index].name}")
        
    # Navigation methods
    def prev_image(self):
        """Go to previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
            
    def next_image(self):
        """Go to next image."""
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_current_image()
            
    def first_image(self):
        """Go to first image."""
        self.current_index = 0
        self.load_current_image()
        
    def last_image(self):
        """Go to last image."""
        self.current_index = len(self.image_paths) - 1
        self.load_current_image()
        
    def on_slider_changed(self, value):
        """Handle slider value change."""
        self.current_index = value
        self.load_current_image()
        
    def on_split_changed(self, split):
        """Handle split selection change."""
        self.current_split = split
        self.load_dataset()
        
    def on_annotations_toggled(self, checked):
        """Handle annotation display toggle."""
        self.show_annotations = checked
        self.load_current_image()
        
    def toggle_annotations(self):
        """Toggle annotation display."""
        self.show_annotations = not self.show_annotations
        self.show_annotations_cb.setChecked(self.show_annotations)
        self.load_current_image()
        
    def on_thickness_changed(self, value):
        """Handle line thickness change."""
        self.line_thickness = value
        self.load_current_image()
        
    def choose_polygon_color(self):
        """Choose polygon color."""
        color = QColorDialog.getColor(self.polygon_color, self)
        if color.isValid():
            self.polygon_color = color
            self.load_current_image()
            
    def choose_point_color(self):
        """Choose point color."""
        color = QColorDialog.getColor(self.point_color, self)
        if color.isValid():
            self.point_color = color
            self.load_current_image()
            
    def reset_view(self):
        """Reset image view."""
        self.image_label.reset_view()

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Check if PySide6 is available
    try:
        window = YOLODatasetVisualizer()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting application: {e}")
        print("Make sure PySide6 is installed: pip install PySide6")
        sys.exit(1)

if __name__ == "__main__":
    main()
