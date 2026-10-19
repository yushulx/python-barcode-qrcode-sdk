"""
Performance metrics display widget
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QGroupBox, QGridLayout, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from collections import deque
from typing import Dict
from utils import format_time, format_size

class MetricsWidget(QWidget):
    """Widget to display performance metrics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.metrics_history = deque(maxlen=50)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Model Information Group
        model_group = QGroupBox("Model Information")
        model_layout = QGridLayout()
        
        self.model_arch_label = QLabel("Architecture: -")
        self.model_params_label = QLabel("Parameters: -")
        self.model_device_label = QLabel("Device: -")
        self.model_input_size_label = QLabel("Input Size: -")
        
        model_layout.addWidget(QLabel("<b>Architecture:</b>"), 0, 0)
        model_layout.addWidget(self.model_arch_label, 0, 1)
        model_layout.addWidget(QLabel("<b>Parameters:</b>"), 1, 0)
        model_layout.addWidget(self.model_params_label, 1, 1)
        model_layout.addWidget(QLabel("<b>Device:</b>"), 2, 0)
        model_layout.addWidget(self.model_device_label, 2, 1)
        model_layout.addWidget(QLabel("<b>Input Size:</b>"), 3, 0)
        model_layout.addWidget(self.model_input_size_label, 3, 1)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Performance Metrics Group
        perf_group = QGroupBox("Performance Metrics")
        perf_layout = QGridLayout()
        
        # Create labels for metrics
        self.preprocess_label = QLabel("-")
        self.inference_label = QLabel("-")
        self.postprocess_label = QLabel("-")
        self.total_label = QLabel("-")
        self.fps_label = QLabel("-")
        
        # Make total time bold
        font = QFont()
        font.setBold(True)
        self.total_label.setFont(font)
        
        perf_layout.addWidget(QLabel("<b>Preprocessing:</b>"), 0, 0)
        perf_layout.addWidget(self.preprocess_label, 0, 1)
        perf_layout.addWidget(QLabel("<b>Inference:</b>"), 1, 0)
        perf_layout.addWidget(self.inference_label, 1, 1)
        perf_layout.addWidget(QLabel("<b>Post-processing:</b>"), 2, 0)
        perf_layout.addWidget(self.postprocess_label, 2, 1)
        
        # Add separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        perf_layout.addWidget(line, 3, 0, 1, 2)
        
        perf_layout.addWidget(QLabel("<b>Total Time:</b>"), 4, 0)
        perf_layout.addWidget(self.total_label, 4, 1)
        perf_layout.addWidget(QLabel("<b>FPS:</b>"), 5, 0)
        perf_layout.addWidget(self.fps_label, 5, 1)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # Image Information Group
        image_group = QGroupBox("Image Information")
        image_layout = QGridLayout()
        
        self.image_size_label = QLabel("-")
        self.corners_label = QLabel("-")
        
        image_layout.addWidget(QLabel("<b>Resolution:</b>"), 0, 0)
        image_layout.addWidget(self.image_size_label, 0, 1)
        image_layout.addWidget(QLabel("<b>Corners Detected:</b>"), 1, 0)
        image_layout.addWidget(self.corners_label, 1, 1)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # Statistics Group
        stats_group = QGroupBox("Statistics")
        stats_layout = QGridLayout()
        
        self.avg_time_label = QLabel("-")
        self.min_time_label = QLabel("-")
        self.max_time_label = QLabel("-")
        self.frames_processed_label = QLabel("0")
        
        stats_layout.addWidget(QLabel("<b>Avg Time:</b>"), 0, 0)
        stats_layout.addWidget(self.avg_time_label, 0, 1)
        stats_layout.addWidget(QLabel("<b>Min Time:</b>"), 1, 0)
        stats_layout.addWidget(self.min_time_label, 1, 1)
        stats_layout.addWidget(QLabel("<b>Max Time:</b>"), 2, 0)
        stats_layout.addWidget(self.max_time_label, 2, 1)
        stats_layout.addWidget(QLabel("<b>Frames Processed:</b>"), 3, 0)
        stats_layout.addWidget(self.frames_processed_label, 3, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def set_model_info(self, model_info: Dict):
        """Set model information"""
        self.model_arch_label.setText(model_info.get('architecture', '-'))
        
        params = model_info.get('total_params', 0)
        self.model_params_label.setText(f"{params:,}")
        
        input_size = model_info.get('input_size', (0, 0))
        self.model_input_size_label.setText(f"{input_size[0]}×{input_size[1]}")
    
    def set_device(self, device: str):
        """Set device information"""
        self.model_device_label.setText(device.upper())
    
    def update_metrics(self, metrics: Dict, image_shape: tuple = None, corners_detected: bool = False):
        """
        Update performance metrics
        
        Args:
            metrics: Dictionary with timing metrics
            image_shape: Image shape (H, W, C)
            corners_detected: Whether corners were detected
        """
        # Update timing labels
        self.preprocess_label.setText(format_time(metrics.get('preprocess_ms', 0)))
        self.inference_label.setText(format_time(metrics.get('inference_ms', 0)))
        self.postprocess_label.setText(format_time(metrics.get('postprocess_ms', 0)))
        
        total_ms = metrics.get('total_ms', 0)
        self.total_label.setText(format_time(total_ms))
        
        # Calculate FPS
        if total_ms > 0:
            fps = 1000.0 / total_ms
            self.fps_label.setText(f"{fps:.1f}")
        else:
            self.fps_label.setText("-")
        
        # Update image info
        if image_shape:
            h, w = image_shape[:2]
            self.image_size_label.setText(f"{w}×{h}")
        
        self.corners_label.setText("Yes ✓" if corners_detected else "No ✗")
        
        # Add to history
        self.metrics_history.append(total_ms)
        
        # Update statistics
        self.update_statistics()
    
    def update_statistics(self):
        """Update statistics from history"""
        if not self.metrics_history:
            return
        
        times = list(self.metrics_history)
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        self.avg_time_label.setText(format_time(avg_time))
        self.min_time_label.setText(format_time(min_time))
        self.max_time_label.setText(format_time(max_time))
        self.frames_processed_label.setText(str(len(self.metrics_history)))
    
    def reset_statistics(self):
        """Reset statistics"""
        self.metrics_history.clear()
        self.avg_time_label.setText("-")
        self.min_time_label.setText("-")
        self.max_time_label.setText("-")
        self.frames_processed_label.setText("0")
