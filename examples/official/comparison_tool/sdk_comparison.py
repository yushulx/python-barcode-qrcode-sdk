#!/usr/bin/env python3
"""
Enhanced Dual SDK Version Comparison Tool with Improved UI

Features:
1. Dynamic virtual environment configuration
2. Drag & drop support for images and folders
3. Table-based results display
4. Side-by-side image comparison with overlay visualization
5. Real-time processing updates
"""

import sys
import os
import subprocess
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import tempfile
import shutil

# OpenCV for image processing and EXIF handling
import cv2
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QListWidget, QFrame, QGroupBox, 
    QProgressBar, QFileDialog, QMessageBox, QListWidgetItem, QSplitter,
    QStatusBar, QTableWidget, QTableWidgetItem, QHeaderView, 
    QGraphicsView, QGraphicsScene, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QMimeData, QUrl
from PySide6.QtGui import (
    QPixmap, QDragEnterEvent, QDropEvent, QFont, QColor, QImage
)

def load_image_and_draw_overlays(image_path: str, results_dict: Optional[Dict[str, 'ProcessingResult']] = None) -> Dict[str, QPixmap]:
    
    try:
        # Load image with OpenCV (automatically handles EXIF orientation)
        img = cv2.imread(image_path)
        if img is None:
            # Fallback to QPixmap
            return {"image": QPixmap(image_path)}
        
        # Convert BGR to RGB for Qt display
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        pixmaps = {}
        
        if results_dict:
            # Create separate images for each SDK with overlays
            sdk_names = list(results_dict.keys())
            color_palette = [
                (0, 150, 255),    # Blue for first SDK
                (255, 0, 150),    # Pink for second SDK
                (0, 255, 150),    # Green for third SDK
                (255, 150, 0),    # Orange for fourth SDK
                (150, 0, 255),    # Purple for fifth SDK
            ]
            
            for i, (sdk_name, result) in enumerate(results_dict.items()):
                img_copy = img_rgb.copy()
                
                # Draw barcode overlays directly on the image
                if result.success and result.barcodes:
                    # Use different colors for different SDKs
                    color = color_palette[i % len(color_palette)]
                    
                    for i, barcode in enumerate(result.barcodes):
                        if barcode.points and len(barcode.points) >= 4:
                            # Convert points to numpy array
                            points = np.array(barcode.points, dtype=np.int32)
                            
                            # Draw barcode outline
                            cv2.polylines(img_copy, [points], True, color, 2)
                            
                            # Draw filled overlay with transparency
                            overlay = img_copy.copy()
                            cv2.fillPoly(overlay, [points], color)
                            cv2.addWeighted(overlay, 0.2, img_copy, 0.8, 0, img_copy)
                            
                            # Add text label
                            if points.size > 0:
                                text_pos = (int(points[0][0]), int(points[0][1]) - 10)
                                text = f"{i+1}: {barcode.text[:20]}"
                                cv2.putText(img_copy, text, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 
                                          0.5, color, 1, cv2.LINE_AA)
                
                # Convert to QPixmap
                height, width, channel = img_copy.shape
                bytes_per_line = 3 * width
                q_img = QImage(img_copy.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                pixmaps[sdk_name] = QPixmap.fromImage(q_img)
        else:
            # No overlays, just convert the base image
            height, width, channel = img_rgb.shape
            bytes_per_line = 3 * width
            q_img = QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmaps["image"] = QPixmap.fromImage(q_img)
        
        return pixmaps
        
    except Exception as e:
        print(f"Error loading image with OpenCV: {e}")
        # Fallback to QPixmap
        return {"image": QPixmap(image_path)}

@dataclass
class SDKVersion:
    name: str
    version: str
    python_path: str
    description: str
    
    @property
    def unique_id(self) -> str:
        """Generate a unique identifier combining version and environment path"""
        # Extract a short identifier from the path for uniqueness
        path_parts = Path(self.python_path).parts
        env_identifier = ""
        
        # Look for environment indicators in the path
        for i, part in enumerate(path_parts):
            if part.lower() in ['envs', 'venv', 'virtualenv', 'conda']:
                if i + 1 < len(path_parts):
                    env_identifier = path_parts[i + 1]
                break
        
        # If no clear env identifier found, use a hash of the path
        if not env_identifier:
            import hashlib
            env_identifier = hashlib.md5(self.python_path.encode()).hexdigest()[:8]
        
        return f"{self.name}_{env_identifier}"

class SDKVersionDetector:
    """Utility class to detect SDK versions in virtual environments"""
    
    @staticmethod
    def detect_sdk_version(python_path: str) -> Optional[str]:
        """Detect the Dynamsoft Capture Vision version in a given Python environment"""
        try:
            # Create a script to check the SDK version
            version_script = '''
import sys
try:
    import dynamsoft_capture_vision_bundle
    # Try to get version from package metadata
    try:
        import pkg_resources
        version = pkg_resources.get_distribution("dynamsoft-capture-vision-bundle").version
        print(f"VERSION:{version}")
    except:
        # Fallback: try to get from module attributes
        if hasattr(dynamsoft_capture_vision_bundle, '__version__'):
            print(f"VERSION:{dynamsoft_capture_vision_bundle.__version__}")
        else:
            # Try importing a module and checking its attributes
            from dynamsoft_capture_vision_bundle import CaptureVisionRouter
            if hasattr(CaptureVisionRouter, 'get_version'):
                print(f"VERSION:{CaptureVisionRouter.get_version()}")
            else:
                print("VERSION:unknown")
except ImportError as e:
    print(f"ERROR:SDK not installed - {e}")
except Exception as e:
    print(f"ERROR:Failed to detect version - {e}")
'''
            
            # Run the script in the specified Python environment
            result = subprocess.run([
                python_path, '-c', version_script
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output.startswith("VERSION:"):
                    version = output[8:].strip()
                    return version if version != "unknown" else None
                elif output.startswith("ERROR:"):
                    print(f"SDK detection error: {output[6:]}")
                    return None
            else:
                print(f"Failed to detect SDK version: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Exception during SDK version detection: {e}")
            return None
    
    @staticmethod
    def validate_python_path(python_path: str) -> bool:
        """Validate that the Python path exists and is executable"""
        try:
            if not os.path.exists(python_path):
                return False
            
            # Try to run python --version
            result = subprocess.run([
                python_path, '--version'
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def create_sdk_version_from_path(python_path: str, name_prefix: str = "SDK") -> Optional[SDKVersion]:
        """Create an SDKVersion object by detecting the version from a Python path"""
        if not SDKVersionDetector.validate_python_path(python_path):
            return None
        
        version = SDKVersionDetector.detect_sdk_version(python_path)
        if version:
            return SDKVersion(
                name=f"{name_prefix} v{version}",
                version=version,
                python_path=python_path,
                description=f"Auto-detected SDK version {version}"
            )
        return None

@dataclass
class BarcodeResult:
    text: str
    format: str
    confidence: float
    points: List[List[int]]

@dataclass
class ProcessingResult:
    success: bool
    sdk_version: str
    processing_time: float
    barcodes: List[BarcodeResult]
    error: str = ""

class SDKConfigDialog(QDialog):
    """Dialog for configuring SDK virtual environments"""
    
    sdk_configs_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SDK Configuration")
        self.setFixedSize(700, 500)  # Make it slightly larger
        self.setModal(True)  # Make it modal
        self.sdk_configs = []
        self.setup_ui()
        
        # Set window flags to prevent disappearing
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🔧 Configure SDK Virtual Environments")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "Add virtual environment paths for different SDK versions. "
            "The tool will automatically detect the SDK version in each environment."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(instructions)
        
        # SDK configurations table
        self.config_table = QTableWidget(0, 4)
        self.config_table.setHorizontalHeaderLabels([
            "Environment Name", "Python Path", "Detected Version", "Status"
        ])
        self.config_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.config_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Environment")
        add_btn.clicked.connect(self.add_environment)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("➖ Remove Selected")
        remove_btn.clicked.connect(self.remove_environment)
        button_layout.addWidget(remove_btn)
        
        detect_btn = QPushButton("🔍 Auto-Detect")
        detect_btn.clicked.connect(self.auto_detect_environments)
        button_layout.addWidget(detect_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)  # Use reject() for dialog cancellation
        cancel_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; font-weight: bold; }")
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("✅ Apply Configuration")
        apply_btn.clicked.connect(self.apply_configuration)
        apply_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; }")
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        # Auto-detect common environments
        self.auto_detect_environments()
    
    def add_environment(self):
        """Add a new environment configuration"""
        file_dialog = QFileDialog()
        python_path, _ = file_dialog.getOpenFileName(
            self, "Select Python Executable", "", "Python Executable (python.exe);;All Files (*)"
        )
        
        if python_path:
            self.add_environment_to_table("Custom", python_path)
    
    def add_environment_to_table(self, name: str, python_path: str):
        """Add environment to configuration table"""
        row = self.config_table.rowCount()
        self.config_table.insertRow(row)
        
        # Environment name
        name_item = QTableWidgetItem(name)
        self.config_table.setItem(row, 0, name_item)
        
        # Python path
        path_item = QTableWidgetItem(python_path)
        self.config_table.setItem(row, 1, path_item)
        
        # Detect version
        version_item = QTableWidgetItem("Detecting...")
        self.config_table.setItem(row, 2, version_item)
        
        # Status
        status_item = QTableWidgetItem("Checking...")
        self.config_table.setItem(row, 3, status_item)
        
        # Start detection in background
        QTimer.singleShot(100, lambda: self.detect_version_for_row(row))
    
    def detect_version_for_row(self, row: int):
        """Detect SDK version for a specific table row"""
        python_path = self.config_table.item(row, 1).text()
        
        # Use the new SDKVersionDetector
        version = SDKVersionDetector.detect_sdk_version(python_path)
        
        if version:
            self.config_table.setItem(row, 2, QTableWidgetItem(version))
            self.config_table.setItem(row, 3, QTableWidgetItem("✅ Ready"))
            # Update name if it's auto-detected
            if self.config_table.item(row, 0).text().startswith("SDK") or self.config_table.item(row, 0).text() == "Custom":
                self.config_table.setItem(row, 0, QTableWidgetItem(f"SDK v{version}"))
        else:
            # Check if Python path is valid
            if SDKVersionDetector.validate_python_path(python_path):
                self.config_table.setItem(row, 2, QTableWidgetItem("No SDK"))
                self.config_table.setItem(row, 3, QTableWidgetItem("❌ SDK not found"))
            else:
                self.config_table.setItem(row, 2, QTableWidgetItem("Invalid"))
                self.config_table.setItem(row, 3, QTableWidgetItem("❌ Python not found"))
    
    def auto_detect_environments(self):
        """Auto-detect virtual environment locations with SDK installations"""
        # Only check virtual environment paths, not the current Python
        virtual_env_paths = [
            "D:/envs/sdk_v1/Scripts/python.exe",
            "D:/envs/sdk_v2/Scripts/python.exe", 
            "C:/envs/sdk_v1/Scripts/python.exe",
            "C:/envs/sdk_v2/Scripts/python.exe",
            # Also check some common conda/virtualenv locations
            os.path.expanduser("~/envs/sdk_v1/Scripts/python.exe"),
            os.path.expanduser("~/envs/sdk_v2/Scripts/python.exe")
        ]
        
        found_envs = []
        for path in virtual_env_paths:
            if SDKVersionDetector.validate_python_path(path):
                # Check if SDK is installed
                version = SDKVersionDetector.detect_sdk_version(path)
                if version:
                    # Check if already added
                    exists = False
                    for row in range(self.config_table.rowCount()):
                        if self.config_table.item(row, 1).text() == path:
                            exists = True
                            break
                    
                    if not exists:
                        env_name = f"SDK v{version}"
                        self.add_environment_to_table(env_name, path)
                        found_envs.append((env_name, version))
        
        # No fallback to current Python - only show virtual environments with SDK
    
    def remove_environment(self):
        """Remove selected environment"""
        current_row = self.config_table.currentRow()
        if current_row >= 0:
            self.config_table.removeRow(current_row)
    
    def apply_configuration(self):
        """Apply the current configuration"""
        configs = []
        
        for row in range(self.config_table.rowCount()):
            name = self.config_table.item(row, 0).text()
            python_path = self.config_table.item(row, 1).text()
            version = self.config_table.item(row, 2).text()
            status = self.config_table.item(row, 3).text()
            
            # Only include SDK environments, not the current Python
            if "✅" in status and version != "Detecting..." and "SDK" in name:
                configs.append(SDKVersion(
                    name=name,
                    version=version,
                    python_path=python_path,
                    description=f"Virtual environment with SDK v{version}"
                ))
        
        if len(configs) >= 2:
            self.sdk_configs_changed.emit(configs)
            self.accept()  # Use accept() instead of close() for proper dialog closing
        else:
            QMessageBox.warning(self, "Configuration Error", 
                              "Please configure at least 2 working SDK environments for comparison.")

class ResultsTableWidget(QTableWidget):
    """Enhanced table widget for displaying comparison results"""
    
    image_selected = Signal(str)  # Emits image path when row is selected
    
    def __init__(self):
        super().__init__()
        self.sdk_versions = []  # Store SDK versions for header updates
        self.sdk_id_to_version = {}  # Map unique_id to SDKVersion objects
        self.setup_table()
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def update_sdk_headers(self, sdk_versions: List[SDKVersion]):
        """Update table headers with actual SDK version names"""
        self.sdk_versions = sdk_versions
        # Create mapping from unique_id to SDKVersion for display purposes
        self.sdk_id_to_version = {sdk.unique_id: sdk for sdk in sdk_versions}
        
        if len(sdk_versions) >= 2:
            headers = [
                "Image", 
                sdk_versions[0].name, 
                sdk_versions[1].name, 
                "Barcodes Δ", 
                "Speed Δ", 
                "Status"
            ]
        else:
            headers = [
                "Image", "SDK v1", "SDK v2", "Barcodes Δ", "Speed Δ", "Status"
            ]
        self.setHorizontalHeaderLabels(headers)
    
    def setup_table(self):
        """Setup the results table"""
        headers = [
            "Image", "SDK v1", "SDK v2", "Barcodes Δ", "Speed Δ", "Status"
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table appearance
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    
    def get_display_name(self, unique_id: str) -> str:
        """Get the display name for a unique SDK ID"""
        if unique_id in self.sdk_id_to_version:
            return self.sdk_id_to_version[unique_id].name
        return unique_id  # Fallback to unique_id if not found
    
    def add_comparison_result(self, image_path: str, results: Dict[str, ProcessingResult]):
        """Add a comparison result to the table"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Image name
        image_name = os.path.basename(image_path)
        item = QTableWidgetItem(image_name)
        item.setData(Qt.ItemDataRole.UserRole, image_path)
        self.setItem(row, 0, item)
        
        # Get results for both SDKs
        sdk_names = list(results.keys())
        
        if len(sdk_names) >= 2:
            result1 = results[sdk_names[0]]  # First SDK (baseline)
            result2 = results[sdk_names[1]]  # Second SDK (comparison)
            
            # SDK 1 results
            sdk1_text = f"{len(result1.barcodes)} barcodes, {result1.processing_time:.3f}s"
            self.setItem(row, 1, QTableWidgetItem(sdk1_text))
            
            # SDK 2 results  
            sdk2_text = f"{len(result2.barcodes)} barcodes, {result2.processing_time:.3f}s"
            self.setItem(row, 2, QTableWidgetItem(sdk2_text))
            
            # Barcode count difference (SDK2 - SDK1)
            # Positive = SDK2 found more barcodes (improvement)
            barcode_diff = len(result2.barcodes) - len(result1.barcodes)
            if barcode_diff > 0:
                barcode_item = QTableWidgetItem(f"+{barcode_diff}")
                barcode_item.setBackground(QColor(200, 255, 200))  # Green for improvement
                barcode_item.setToolTip(f"SDK2 found {barcode_diff} more barcode(s)")
            elif barcode_diff < 0:
                barcode_item = QTableWidgetItem(str(barcode_diff))
                barcode_item.setBackground(QColor(255, 200, 200))  # Red for regression
                barcode_item.setToolTip(f"SDK2 found {abs(barcode_diff)} fewer barcode(s)")
            else:
                barcode_item = QTableWidgetItem("0")
                barcode_item.setBackground(QColor(240, 240, 240))  # Gray for same
                barcode_item.setToolTip("Same number of barcodes found")
            self.setItem(row, 3, barcode_item)
            
            # Speed difference (SDK2 - SDK1)
            # Negative = SDK2 is faster (improvement)
            speed_diff = result2.processing_time - result1.processing_time
            if speed_diff < 0:
                speed_item = QTableWidgetItem(f"{speed_diff:.3f}s")
                speed_item.setBackground(QColor(200, 255, 200))  # Green for faster
                speed_item.setToolTip(f"SDK2 is {abs(speed_diff):.3f}s faster")
            elif speed_diff > 0:
                speed_item = QTableWidgetItem(f"+{speed_diff:.3f}s")
                speed_item.setBackground(QColor(255, 200, 200))  # Red for slower
                speed_item.setToolTip(f"SDK2 is {speed_diff:.3f}s slower")
            else:
                speed_item = QTableWidgetItem("0.000s")
                speed_item.setBackground(QColor(240, 240, 240))  # Gray for same
                speed_item.setToolTip("Same processing speed")
            self.setItem(row, 4, speed_item)
            
            # Overall status
            if result1.success and result2.success:
                if barcode_diff > 0:
                    status = "✅ Improved"
                elif barcode_diff < 0:
                    status = "❌ Regressed"
                else:
                    status = "➡️ Same"
            else:
                status = "⚠️ Error"
            
            self.setItem(row, 5, QTableWidgetItem(status))
        
        # Force table update
        self.viewport().update()
        self.repaint()
    
    def check_if_image_exists(self, image_path: str) -> int:
        """Check if image already exists in table, return row index or -1"""
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == image_path:
                return row
        return -1
    
    def update_existing_result(self, row: int, image_path: str, results: Dict[str, ProcessingResult]):
        """Update an existing row with new results"""
        # Get results for both SDKs
        sdk_names = list(results.keys())
        
        if len(sdk_names) >= 2:
            result1 = results[sdk_names[0]]  # First SDK (baseline)
            result2 = results[sdk_names[1]]  # Second SDK (comparison)
            
            # Update SDK results
            sdk1_text = f"{len(result1.barcodes)} barcodes, {result1.processing_time:.3f}s"
            self.setItem(row, 1, QTableWidgetItem(sdk1_text))
            
            sdk2_text = f"{len(result2.barcodes)} barcodes, {result2.processing_time:.3f}s"
            self.setItem(row, 2, QTableWidgetItem(sdk2_text))
            
            # Update differences (same logic as add_comparison_result)
            barcode_diff = len(result2.barcodes) - len(result1.barcodes)
            if barcode_diff > 0:
                barcode_item = QTableWidgetItem(f"+{barcode_diff}")
                barcode_item.setBackground(QColor(200, 255, 200))
                barcode_item.setToolTip(f"SDK2 found {barcode_diff} more barcode(s)")
            elif barcode_diff < 0:
                barcode_item = QTableWidgetItem(str(barcode_diff))
                barcode_item.setBackground(QColor(255, 200, 200))
                barcode_item.setToolTip(f"SDK2 found {abs(barcode_diff)} fewer barcode(s)")
            else:
                barcode_item = QTableWidgetItem("0")
                barcode_item.setBackground(QColor(240, 240, 240))
                barcode_item.setToolTip("Same number of barcodes found")
            self.setItem(row, 3, barcode_item)
            
            speed_diff = result2.processing_time - result1.processing_time
            if speed_diff < 0:
                speed_item = QTableWidgetItem(f"{speed_diff:.3f}s")
                speed_item.setBackground(QColor(200, 255, 200))
                speed_item.setToolTip(f"SDK2 is {abs(speed_diff):.3f}s faster")
            elif speed_diff > 0:
                speed_item = QTableWidgetItem(f"+{speed_diff:.3f}s")
                speed_item.setBackground(QColor(255, 200, 200))
                speed_item.setToolTip(f"SDK2 is {speed_diff:.3f}s slower")
            else:
                speed_item = QTableWidgetItem("0.000s")
                speed_item.setBackground(QColor(240, 240, 240))
                speed_item.setToolTip("Same processing speed")
            self.setItem(row, 4, speed_item)
            
            # Update status
            if result1.success and result2.success:
                if barcode_diff > 0:
                    status = "✅ Improved"
                elif barcode_diff < 0:
                    status = "❌ Regressed"
                else:
                    status = "➡️ Same"
            else:
                status = "⚠️ Error"
            self.setItem(row, 5, QTableWidgetItem(status))
    
    def add_or_update_result(self, image_path: str, results: Dict[str, ProcessingResult]):
        """Add new result or update existing one"""
        existing_row = self.check_if_image_exists(image_path)
        if existing_row >= 0:
            # Update existing row
            self.update_existing_result(existing_row, image_path, results)
            # Highlight the updated row
            self.selectRow(existing_row)
        else:
            # Add new row
            self.add_comparison_result(image_path, results)
            # Highlight the new row
            if self.rowCount() > 0:
                self.selectRow(self.rowCount() - 1)
    
    def export_to_csv(self):
        """Export table data to CSV file"""
        if self.rowCount() == 0:
            QMessageBox.information(self, "Export CSV", "No data to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Comparison Results", 
            "sdk_comparison_results.csv", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers
                    headers = []
                    for col in range(self.columnCount()):
                        headers.append(self.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.rowCount()):
                        row_data = []
                        for col in range(self.columnCount()):
                            item = self.item(row, col)
                            if item:
                                row_data.append(item.text())
                            else:
                                row_data.append("")
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "Export Complete", 
                                      f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", 
                                   f"Failed to export CSV: {str(e)}")
    
    def on_selection_changed(self):
        """Handle row selection"""
        current_row = self.currentRow()
        if current_row >= 0:
            item = self.item(current_row, 0)
            if item:
                image_path = item.data(Qt.ItemDataRole.UserRole)
                if image_path:
                    self.image_selected.emit(image_path)

class ImageComparisonWidget(QWidget):
    """Widget for side-by-side image comparison with barcode overlays"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_image = None
        self.results = {}
        self.sdk_id_to_version = {}  # Map unique_id to SDKVersion objects
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📷 Image Comparison View")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Image views container
        images_layout = QHBoxLayout()
        
        # SDK 1 view
        sdk1_container = QVBoxLayout()
        self.sdk1_label = QLabel("SDK Version 1")  # Make it instance variable
        self.sdk1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sdk1_label.setStyleSheet("font-weight: bold; background-color: #e3f2fd; padding: 5px;")
        sdk1_container.addWidget(self.sdk1_label)
        
        self.sdk1_view = QGraphicsView()
        self.sdk1_scene = QGraphicsScene()
        self.sdk1_view.setScene(self.sdk1_scene)
        self.sdk1_view.setMinimumSize(400, 300)
        sdk1_container.addWidget(self.sdk1_view)
        
        # SDK 1 barcode results text area
        sdk1_results_label = QLabel("🔍 Barcode Results:")
        sdk1_results_label.setStyleSheet("font-weight: bold; color: #1976d2;")
        sdk1_container.addWidget(sdk1_results_label)
        
        self.sdk1_results_text = QTextEdit()
        self.sdk1_results_text.setMaximumHeight(120)
        self.sdk1_results_text.setReadOnly(True)
        self.sdk1_results_text.setPlaceholderText("Barcode results will appear here...")
        self.sdk1_results_text.setStyleSheet("font-family: monospace; font-size: 10pt; background-color: #f8f9fa;")
        sdk1_container.addWidget(self.sdk1_results_text)
        
        # SDK 2 view
        sdk2_container = QVBoxLayout()
        self.sdk2_label = QLabel("SDK Version 2")  # Make it instance variable
        self.sdk2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sdk2_label.setStyleSheet("font-weight: bold; background-color: #f3e5f5; padding: 5px;")
        sdk2_container.addWidget(self.sdk2_label)
        
        self.sdk2_view = QGraphicsView()
        self.sdk2_scene = QGraphicsScene()
        self.sdk2_view.setScene(self.sdk2_scene)
        self.sdk2_view.setMinimumSize(400, 300)
        sdk2_container.addWidget(self.sdk2_view)
        
        # SDK 2 barcode results text area
        sdk2_results_label = QLabel("🔍 Barcode Results:")
        sdk2_results_label.setStyleSheet("font-weight: bold; color: #7b1fa2;")
        sdk2_container.addWidget(sdk2_results_label)
        
        self.sdk2_results_text = QTextEdit()
        self.sdk2_results_text.setMaximumHeight(120)
        self.sdk2_results_text.setReadOnly(True)
        self.sdk2_results_text.setPlaceholderText("Barcode results will appear here...")
        self.sdk2_results_text.setStyleSheet("font-family: monospace; font-size: 10pt; background-color: #f8f9fa;")
        sdk2_container.addWidget(self.sdk2_results_text)
        
        images_layout.addLayout(sdk1_container)
        images_layout.addLayout(sdk2_container)
        layout.addLayout(images_layout)
        
        # Results summary
        self.summary_label = QLabel("Add images and configure SDKs to begin comparison")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.summary_label)
    
    def update_sdk_labels(self, sdk_versions: List[SDKVersion]):
        """Update SDK version labels with actual version names"""
        # Update the mapping
        self.sdk_id_to_version = {sdk.unique_id: sdk for sdk in sdk_versions}
        
        if len(sdk_versions) >= 2:
            self.sdk1_label.setText(f"📊 {sdk_versions[0].name}")
            self.sdk2_label.setText(f"📊 {sdk_versions[1].name}")
        elif len(sdk_versions) == 1:
            self.sdk1_label.setText(f"📊 {sdk_versions[0].name}")
            self.sdk2_label.setText("📊 Waiting for second SDK...")
        else:
            self.sdk1_label.setText("📊 Configure SDK Version 1")
            self.sdk2_label.setText("📊 Configure SDK Version 2")
    
    def get_display_name(self, unique_id: str) -> str:
        """Get the display name for a unique SDK ID"""
        if unique_id in self.sdk_id_to_version:
            return self.sdk_id_to_version[unique_id].name
        return unique_id  # Fallback to unique_id if not found
    
    def show_comparison(self, image_path: str, results: Dict[str, ProcessingResult]):
        """Show side-by-side comparison for an image"""
        self.current_image = image_path
        self.results = results
        
        # Load image and create overlays using OpenCV
        pixmaps = load_image_and_draw_overlays(image_path, results)
        
        if not pixmaps:
            self.summary_label.setText(f"Could not load image: {image_path}")
            return
        
        # Get SDK names for proper display
        sdk_names = list(results.keys())
        
        # Clear scenes
        self.sdk1_scene.clear()
        self.sdk2_scene.clear()
        
        # Scale images if needed
        max_size = 400
        
        if len(sdk_names) >= 2:
            # Use the SDK-specific pixmaps with overlays
            sdk1_pixmap = pixmaps.get(sdk_names[0])
            sdk2_pixmap = pixmaps.get(sdk_names[1])
            
            if sdk1_pixmap:
                if sdk1_pixmap.width() > max_size or sdk1_pixmap.height() > max_size:
                    sdk1_pixmap = sdk1_pixmap.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, 
                                                     Qt.TransformationMode.SmoothTransformation)
                self.sdk1_scene.addPixmap(sdk1_pixmap)
                self.sdk1_scene.setSceneRect(sdk1_pixmap.rect())
            
            if sdk2_pixmap:
                if sdk2_pixmap.width() > max_size or sdk2_pixmap.height() > max_size:
                    sdk2_pixmap = sdk2_pixmap.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, 
                                                     Qt.TransformationMode.SmoothTransformation)
                self.sdk2_scene.addPixmap(sdk2_pixmap)
                self.sdk2_scene.setSceneRect(sdk2_pixmap.rect())
            
            # Update labels with actual SDK names (use display names instead of unique IDs)
            sdk1_display_name = self.get_display_name(sdk_names[0])
            sdk2_display_name = self.get_display_name(sdk_names[1])
            self.sdk1_label.setText(f"📊 {sdk1_display_name}")
            self.sdk2_label.setText(f"📊 {sdk2_display_name}")
            
            # Update barcode result text areas
            self.update_barcode_text_area(self.sdk1_results_text, results[sdk_names[0]])
            self.update_barcode_text_area(self.sdk2_results_text, results[sdk_names[1]])
            
            # Update summary
            result1 = results[sdk_names[0]]
            result2 = results[sdk_names[1]]
            summary = (f"📊 {os.path.basename(image_path)} | "
                      f"{sdk1_display_name}: {len(result1.barcodes)} barcodes ({result1.processing_time:.3f}s) | "
                      f"{sdk2_display_name}: {len(result2.barcodes)} barcodes ({result2.processing_time:.3f}s)")
            self.summary_label.setText(summary)
        elif len(sdk_names) == 1:
            # Only one SDK result available
            sdk1_pixmap = pixmaps.get(sdk_names[0])
            if not sdk1_pixmap:
                sdk1_pixmap = pixmaps.get("image", QPixmap())
            
            if sdk1_pixmap and not sdk1_pixmap.isNull():
                if sdk1_pixmap.width() > max_size or sdk1_pixmap.height() > max_size:
                    sdk1_pixmap = sdk1_pixmap.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, 
                                                     Qt.TransformationMode.SmoothTransformation)
                self.sdk1_scene.addPixmap(sdk1_pixmap)
                self.sdk1_scene.setSceneRect(sdk1_pixmap.rect())
            
            sdk1_display_name = self.get_display_name(sdk_names[0])
            self.sdk1_label.setText(f"📊 {sdk1_display_name}")
            self.sdk2_label.setText("📊 No comparison data")
            
            # Update text areas
            self.update_barcode_text_area(self.sdk1_results_text, results[sdk_names[0]])
            self.sdk2_results_text.clear()
            self.sdk2_results_text.setPlaceholderText("No comparison data available")
            
            result1 = results[sdk_names[0]]
            summary = (f"📊 {os.path.basename(image_path)} | "
                      f"{sdk1_display_name}: {len(result1.barcodes)} barcodes ({result1.processing_time:.3f}s)")
            self.summary_label.setText(summary)
        else:
            # No results, just show the base image
            base_pixmap = pixmaps.get("image", QPixmap())
            if base_pixmap and not base_pixmap.isNull():
                if base_pixmap.width() > max_size or base_pixmap.height() > max_size:
                    base_pixmap = base_pixmap.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, 
                                                     Qt.TransformationMode.SmoothTransformation)
                self.sdk1_scene.addPixmap(base_pixmap)
                self.sdk1_scene.setSceneRect(base_pixmap.rect())
            
            # Clear text areas if no results
            self.sdk1_results_text.clear()
            self.sdk2_results_text.clear()
            self.sdk1_results_text.setPlaceholderText("No results available")
            self.sdk2_results_text.setPlaceholderText("No results available")
        
        # Fit views to show the entire scene
        self.sdk1_view.fitInView(self.sdk1_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.sdk2_view.fitInView(self.sdk2_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Force view updates
        self.sdk1_view.update()
        self.sdk2_view.update()
    def update_barcode_text_area(self, text_area: QTextEdit, result: ProcessingResult):
        """Update barcode results text area with formatted barcode data"""
        text_area.clear()
        
        if not result.success:
            text_area.setPlainText(f"❌ Error: {result.error}")
            return
        
        if not result.barcodes:
            text_area.setPlainText("ℹ️ No barcodes detected")
            return
        
        # Format barcode results
        results_text = []
        results_text.append(f"✅ Found {len(result.barcodes)} barcode(s) in {result.processing_time:.3f}s\n")
        
        for i, barcode in enumerate(result.barcodes, 1):
            results_text.append(f"🏷️ Barcode #{i}:")
            results_text.append(f"   Text: {barcode.text}")
            results_text.append(f"   Format: {barcode.format}")
            if barcode.confidence > 0:
                results_text.append(f"   Confidence: {barcode.confidence:.2f}")
            if barcode.points:
                points_str = " → ".join([f"({p[0]},{p[1]})" for p in barcode.points])
                results_text.append(f"   Points: {points_str}")
            results_text.append("")
        
        text_area.setPlainText("\n".join(results_text))
        
        # Move cursor to beginning for easier reading
        cursor = text_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        text_area.setTextCursor(cursor)

class EnhancedDualSDKComparisonTool(QMainWindow):
    """Enhanced main application with improved UI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Dual SDK Comparison Tool")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Data
        self.sdk_versions = []
        self.image_files = []
        self.results = {}  # {image_path: {sdk_name: ProcessingResult}}
        self.processing_thread = None  # Initialize to None
        self._updating_selection = False  # Flag to prevent selection loops
        
        # Setup UI
        self.setup_ui()
        self.setup_drag_drop()
        
        # Show configuration dialog on startup
        QTimer.singleShot(500, self.show_sdk_config)
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop processing thread if running
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait(3000)  # Wait up to 3 seconds
        
        event.accept()
    
    def setup_ui(self):
        """Setup the enhanced user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        config_btn = QPushButton("🔧 Configure SDKs")
        config_btn.clicked.connect(self.show_sdk_config)
        toolbar_layout.addWidget(config_btn)
        
        add_images_btn = QPushButton("📁 Add Images")
        add_images_btn.clicked.connect(self.add_images)
        toolbar_layout.addWidget(add_images_btn)
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self.clear_all)
        toolbar_layout.addWidget(clear_btn)
        
        toolbar_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bbb;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 3px;
            }
        """)
        toolbar_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(toolbar_layout)
        
        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: File list and results table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # File list
        files_group = QGroupBox("📁 Image Files")
        files_layout = QVBoxLayout(files_group)
        
        self.file_list = QListWidget()
        self.file_list.setAcceptDrops(True)
        self.file_list.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        
        # Add custom styling for better visibility
        self.file_list.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #4da6e0;
                color: white;
            }
        """)
        
        # Connect selection change to processing
        self.file_list.currentItemChanged.connect(self.on_image_selected)
        
        files_layout.addWidget(self.file_list)
        
        left_layout.addWidget(files_group)
        
        # Results table
        results_group = QGroupBox("📊 Comparison Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = ResultsTableWidget()
        
        # Add custom styling for better visibility
        self.results_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #007acc;
                color: white;
                font-weight: bold;
            }
            QTableWidget::item:hover {
                background-color: #4da6e0;
                color: white;
            }
        """)
        
        results_layout.addWidget(self.results_table)
        
        # Connect results table selection to file list synchronization
        self.results_table.image_selected.connect(self.on_results_table_selection)
        
        # Export button (after table creation)
        export_btn = QPushButton("📤 Export to CSV")
        export_btn.clicked.connect(self.results_table.export_to_csv)
        export_btn.setStyleSheet("QPushButton { background-color: #007acc; color: white; font-weight: bold; }")
        results_layout.addWidget(export_btn)
        
        left_layout.addWidget(results_group)
        
        splitter.addWidget(left_panel)
        
        # Right panel: Image comparison
        self.image_comparison = ImageComparisonWidget()
        splitter.addWidget(self.image_comparison)
        
        splitter.setSizes([600, 1000])
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Configure SDKs to begin")

        # New added file list
        self.new_files = []
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        urls = event.mimeData().urls()
        new_files = []
        folder_dropped = False
        
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                new_files.append(path)
            elif os.path.isdir(path):
                folder_dropped = True
                # Add all images in directory
                for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff']:
                    new_files.extend(Path(path).glob(ext))
                    new_files.extend(Path(path).glob(ext.upper()))

        if new_files:
            # Convert Path objects to strings
            self.new_files = [str(f) for f in new_files]
            self.add_image_files(self.new_files)
    
    def show_sdk_config(self):
        """Show SDK configuration dialog"""
        config_dialog = SDKConfigDialog(self)  # Pass parent
        config_dialog.sdk_configs_changed.connect(self.update_sdk_versions)
        
        # Show as modal dialog and wait for result
        if config_dialog.exec() == QDialog.DialogCode.Accepted:
            # Dialog was accepted (though we handle this via signal)
            pass
    
    def update_sdk_versions(self, sdk_versions: List[SDKVersion]):
        """Update SDK versions configuration"""
        self.sdk_versions = sdk_versions
        self.status_bar.showMessage(f"Configured {len(sdk_versions)} SDK versions")
        
        # Update the image comparison labels
        self.image_comparison.update_sdk_labels(sdk_versions)
        
        # Update results table headers
        self.results_table.update_sdk_headers(sdk_versions)
        
        # Process the currently selected image if we have one
        current_item = self.file_list.currentItem()
        if current_item and len(sdk_versions) >= 2:
            image_path = current_item.data(Qt.ItemDataRole.UserRole)
            if image_path:
                QTimer.singleShot(500, lambda: self.process_selected_image(image_path))
    
    def add_images(self):
        """Add images via file dialog"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )
        if files:
            self.new_files = [str(f) for f in files]
            self.add_image_files(files)
    
    def add_image_files(self, files: List[str]):
        """Add image files to the list"""
        new_files_added = 0
        last_added_item = None
        
        for file_path in files:

            if file_path not in self.image_files:
                self.image_files.append(str(file_path))
                
                # Create list item with image path stored as data
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                self.file_list.addItem(item)
                
                last_added_item = item
                new_files_added += 1
        
        self.status_bar.showMessage(f"Added {new_files_added} images. Total: {len(self.image_files)}")
        
        # Auto-select the last added image and process it
        if last_added_item and len(self.sdk_versions) >= 2:
            self.file_list.setCurrentItem(last_added_item)
            # Processing will be triggered by the selection change event
        elif last_added_item:
            # Select the item but show SDK configuration message
            self.file_list.setCurrentItem(last_added_item)
            QTimer.singleShot(100, lambda: QMessageBox.information(
                self, "SDK Configuration Required", 
                "Image selected! Please configure SDK versions first to enable processing."
            ))
    
    def on_image_selected(self, current_item, previous_item):
        """Handle image selection from the file list"""
        if current_item is None:
            return
            
        # Get the full image path from the item data
        image_path = current_item.data(Qt.ItemDataRole.UserRole)
        if not image_path:
            return
            
        self.status_bar.showMessage(f"Selected: {os.path.basename(image_path)}")
        
        # Synchronize with results table selection (avoid loops)
        if not self._updating_selection:
            self._updating_selection = True
            self.highlight_results_table_row(image_path)
            self._updating_selection = False
        
        # Check if we have SDK versions configured
        if len(self.sdk_versions) >= 2:
            # Process the selected image
            self.process_selected_image(image_path)
        else:
            # Clear the comparison view and show message
            self.image_comparison.sdk1_scene.clear()
            self.image_comparison.sdk2_scene.clear()
            self.image_comparison.summary_label.setText("Configure SDK versions to process images")
            
            # Clear results table
            self.results_table.setRowCount(0)
    
    def process_selected_image(self, image_path: str):
        """Process a single selected image"""
        if not image_path or not os.path.exists(image_path):
            self.status_bar.showMessage("❌ Image file not found")
            return
            
        # Check if already processing this image
        if (self.processing_thread and 
            self.processing_thread.isRunning() and 
            len(self.processing_thread.image_files) == 1 and 
            self.processing_thread.image_files[0] == image_path):
            self.status_bar.showMessage("Already processing this image...")
            return
            
        # Check if we already have complete results for this image
        if (image_path in self.results and 
            len(self.results[image_path]) == len(self.sdk_versions)):
            # We already have results, just display them
            self.update_single_image_display(image_path)
            self.status_bar.showMessage(f"✅ Using cached results for {os.path.basename(image_path)}")
            return
            
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.sdk_versions) * len(self.new_files))
        self.progress_bar.setValue(0)
        
        self.status_bar.showMessage(f"Processing {os.path.basename(image_path)}...")
        
        # Stop existing thread if running
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait(1000)
        
        # Start processing the selected image
        self.processing_thread = ProcessingThread(self.new_files, self.sdk_versions)
        
        # Connect signals
        self.processing_thread.result_ready.connect(
            self.on_single_result_ready, Qt.ConnectionType.QueuedConnection
        )
        self.processing_thread.processing_complete.connect(
            self.on_single_processing_complete, Qt.ConnectionType.QueuedConnection
        )
        
        self.processing_thread.start()
    
    def on_single_result_ready(self, image_path: str, sdk_name: str, result: ProcessingResult):
        """Handle single image processing result"""
        if image_path not in self.results:
            self.results[image_path] = {}
        
        self.results[image_path][sdk_name] = result
        
        # Update progress
        current_value = self.progress_bar.value() + 1
        self.progress_bar.setValue(current_value)
        
        # Update status
        barcodes_found = len(result.barcodes) if result.success else 0
        status_msg = f"Processed with {sdk_name}: {barcodes_found} barcodes found"
        self.status_bar.showMessage(status_msg)
        
        # If we have results from all SDKs, update the display
        if len(self.results[image_path]) == len(self.sdk_versions):
            self.update_single_image_display(image_path)
    
    def on_single_processing_complete(self):
        """Handle single image processing completion"""
        self.progress_bar.setVisible(False)
        
        # Ensure the display is updated for the current selected image
        current_item = self.file_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.ItemDataRole.UserRole)
            if image_path and image_path in self.results:
                # Double-check that display is updated (safety measure)
                if len(self.results[image_path]) == len(self.sdk_versions):
                    self.update_single_image_display(image_path)
                
                total_barcodes = sum(len(result.barcodes) for result in self.results[image_path].values())
                self.status_bar.showMessage(f"✅ Processing complete! Found {total_barcodes} total barcodes.")
        
        # Clean up thread
        if self.processing_thread:
            self.processing_thread.wait()
            self.processing_thread = None
    
    def update_single_image_display(self, image_path: str):
        """Update display for a single processed image"""
        # Add or update results in the table (append mode)
        self.results_table.add_or_update_result(image_path, self.results[image_path])
        
        # Show the image comparison immediately
        self.image_comparison.show_comparison(image_path, self.results[image_path])
        
        # Force UI updates
        self.results_table.viewport().update()
        self.results_table.repaint()
        QApplication.processEvents()
    
    def clear_all(self):
        """Clear all data"""
        self.image_files.clear()
        self.file_list.clear()
        self.results.clear()
        self.results_table.setRowCount(0)
        self.image_comparison.sdk1_scene.clear()
        self.image_comparison.sdk2_scene.clear()
        self.image_comparison.summary_label.setText("Add images to begin comparison")
        self.image_comparison.sdk1_results_text.clear()
        self.image_comparison.sdk2_results_text.clear()
        self.status_bar.showMessage("Cleared all data")
    
    def on_results_table_selection(self, image_path: str):
        """Handle selection from results table - synchronize with file list"""
        if self._updating_selection:
            return
            
        self._updating_selection = True
        
        # Find and select the corresponding item in the file list
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == image_path:
                self.file_list.setCurrentItem(item)
                break
        
        self._updating_selection = False
        
        # Update the image comparison view
        if image_path in self.results:
            self.image_comparison.show_comparison(image_path, self.results[image_path])
    
    def highlight_results_table_row(self, image_path: str):
        """Highlight the row in results table corresponding to the selected image"""
        if self._updating_selection:
            return
            
        # Find and select the corresponding row in results table
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == image_path:
                # Clear any previous highlighting
                self.clear_results_table_highlighting()
                
                # Highlight the selected row with bright blue background
                for col in range(self.results_table.columnCount()):
                    cell_item = self.results_table.item(row, col)
                    if cell_item:
                        # Don't override the difference column colors, just make them brighter
                        if col == 3:  # Barcode Δ column - keep original logic but brighter
                            text = cell_item.text()
                            if text.startswith('+') and text != '+0':
                                cell_item.setBackground(QColor(100, 255, 100))  # Brighter green
                            elif text.startswith('-') or (text.isdigit() and int(text) < 0):
                                cell_item.setBackground(QColor(255, 100, 100))  # Brighter red
                            elif text == '0':
                                cell_item.setBackground(QColor(200, 200, 200))  # Brighter gray
                            else:
                                cell_item.setBackground(QColor(0, 122, 204))  # Bright blue
                        elif col == 4:  # Speed Δ column - keep original logic but brighter
                            text = cell_item.text()
                            if text.endswith('s') and not text.startswith('+') and text != '0.000s':
                                cell_item.setBackground(QColor(100, 255, 100))  # Brighter green
                            elif text.startswith('+'):
                                cell_item.setBackground(QColor(255, 100, 100))  # Brighter red
                            elif text == '0.000s':
                                cell_item.setBackground(QColor(200, 200, 200))  # Brighter gray
                            else:
                                cell_item.setBackground(QColor(0, 122, 204))  # Bright blue
                        else:
                            # Use bright blue for other columns
                            cell_item.setBackground(QColor(0, 122, 204))  # Bright blue
                            cell_item.setForeground(QColor(255, 255, 255))  # White text
                
                # Select the row
                self.results_table.selectRow(row)
                break
    
    def clear_results_table_highlighting(self):
        """Clear blue highlighting from all rows in results table"""
        for row in range(self.results_table.rowCount()):
            for col in range(self.results_table.columnCount()):
                item = self.results_table.item(row, col)
                if item:
                    # Check if this is a difference column that should keep its color
                    if col == 3:  # Barcode Δ column
                        text = item.text()
                        if text.startswith('+') and text != '+0':
                            item.setBackground(QColor(200, 255, 200))  # Green for improvement
                        elif text.startswith('-') or (text.isdigit() and int(text) < 0):
                            item.setBackground(QColor(255, 200, 200))  # Red for regression
                        elif text == '0':
                            item.setBackground(QColor(240, 240, 240))  # Gray for same
                        else:
                            item.setBackground(QColor())  # Default
                    elif col == 4:  # Speed Δ column
                        text = item.text()
                        if text.endswith('s') and not text.startswith('+') and text != '0.000s':
                            item.setBackground(QColor(200, 255, 200))  # Green for faster
                        elif text.startswith('+'):
                            item.setBackground(QColor(255, 200, 200))  # Red for slower
                        elif text == '0.000s':
                            item.setBackground(QColor(240, 240, 240))  # Gray for same
                        else:
                            item.setBackground(QColor())  # Default
                    else:
                        # Clear background for other columns
                        item.setBackground(QColor())  # Default background

class ProcessingThread(QThread):
    """Background thread for image processing"""
    
    result_ready = Signal(str, str, ProcessingResult)
    processing_complete = Signal()
    
    def __init__(self, image_files: List[str], sdk_versions: List[SDKVersion]):
        super().__init__()
        self.image_files = image_files
        self.sdk_versions = sdk_versions
    
    def run(self):
        """Run processing in background"""
        for image_path in self.image_files:
            for sdk_version in self.sdk_versions:
                result = self.process_single_image(image_path, sdk_version)
                self.result_ready.emit(image_path, sdk_version.unique_id, result)
        
        self.processing_complete.emit()
    
    def process_single_image(self, image_path: str, sdk_version: SDKVersion) -> ProcessingResult:
        """Process a single image with a specific SDK version"""
        temp_dir = None  # Initialize to avoid "possibly unbound" errors
        try:
            # Create processor script
            temp_dir = Path(tempfile.mkdtemp())
            script_path = temp_dir / f"processor_{sdk_version.version.replace('.', '_')}.py"
            
            script_content = f'''#!/usr/bin/env python3
import sys
import json
import time
import os
from dynamsoft_capture_vision_bundle import *

LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="

def process_image(image_path):
    start_time = time.time()
    
    # Initialize license
    error_code, error_message = LicenseManager.init_license(LICENSE_KEY)
    if error_code not in [EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_CACHE_USED]:
        return {{"success": False, "error": f"License error: {{error_message}}"}}
    
    # Process image
    cvr = CaptureVisionRouter()
    result = cvr.capture(image_path, EnumPresetTemplate.PT_READ_BARCODES.value)
    
    if result.get_error_code() != EnumErrorCode.EC_OK:
        return {{"success": False, "error": f"Capture error: {{result.get_error_code()}}"}}
    
    # Extract barcodes
    barcodes = []
    items = result.get_items()
    for item in items:
        if item.get_type() == 2:  # Barcode item
            barcode_data = {{
                "text": item.get_text(),
                "format": item.get_format_string(),
                "confidence": getattr(item, 'get_confidence', lambda: 0.0)()
            }}
            
            # Get location points
            try:
                location = item.get_location()
                if location and hasattr(location, 'points'):
                    barcode_data["points"] = [
                        [int(location.points[0].x), int(location.points[0].y)],
                        [int(location.points[1].x), int(location.points[1].y)],
                        [int(location.points[2].x), int(location.points[2].y)],
                        [int(location.points[3].x), int(location.points[3].y)]
                    ]
                else:
                    barcode_data["points"] = []
            except:
                barcode_data["points"] = []
            
            barcodes.append(barcode_data)
    
    return {{
        "success": True,
        "processing_time": time.time() - start_time,
        "barcodes": barcodes
    }}

if __name__ == "__main__":
    result = process_image(sys.argv[1])
    print(json.dumps(result))
'''
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Run processor with shorter timeout
            result = subprocess.run([
                sdk_version.python_path, str(script_path), image_path
            ], capture_output=True, text=True, timeout=30)  # Reduced timeout
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data["success"]:
                    barcodes = [
                        BarcodeResult(
                            text=b["text"],
                            format=b["format"], 
                            confidence=b["confidence"],
                            points=b["points"]
                        ) for b in data["barcodes"]
                    ]
                    return ProcessingResult(
                        success=True,
                        sdk_version=sdk_version.version,
                        processing_time=data["processing_time"],
                        barcodes=barcodes
                    )
                else:
                    return ProcessingResult(
                        success=False,
                        sdk_version=sdk_version.version,
                        processing_time=0.0,
                        barcodes=[],
                        error=data.get("error", "Unknown error")
                    )
            else:
                return ProcessingResult(
                    success=False,
                    sdk_version=sdk_version.version,
                    processing_time=0.0,
                    barcodes=[],
                    error=f"Process failed: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            try:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception:
                pass  # Ignore cleanup errors
            return ProcessingResult(
                success=False,
                sdk_version=sdk_version.version,
                processing_time=0.0,
                barcodes=[],
                error="Processing timeout"
            )
        except Exception as e:
            try:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception:
                pass  # Ignore cleanup errors
            return ProcessingResult(
                success=False,
                sdk_version=sdk_version.version,
                processing_time=0.0,
                barcodes=[],
                error=str(e)
            )

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = EnhancedDualSDKComparisonTool()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()