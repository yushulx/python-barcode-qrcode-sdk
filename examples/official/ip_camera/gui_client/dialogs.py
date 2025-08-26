#!/usr/bin/env python3
"""
Dialogs for IP Camera GUI Client
Connection and settings dialogs for camera configuration.
"""

import json
import os
from typing import Dict, Any, List, Tuple

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QValidator, QIntValidator, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QTabWidget, QWidget, QTextEdit,
    QDialogButtonBox, QMessageBox
)


class IPValidator(QValidator):
    """Validator for IP address input"""
    
    def validate(self, input_str: str, pos: int) -> Tuple[QValidator.State, str, int]:
        if not input_str:
            return QValidator.Intermediate, input_str, pos
            
        parts = input_str.split('.')
        if len(parts) > 4:
            return QValidator.Invalid, input_str, pos
            
        for part in parts:
            if part == '':
                continue
            if not part.isdigit():
                return QValidator.Invalid, input_str, pos
            if int(part) > 255:
                return QValidator.Invalid, input_str, pos
                
        if len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
            return QValidator.Acceptable, input_str, pos
        
        return QValidator.Intermediate, input_str, pos


class ConnectionDialog(QDialog):
    """Dialog for connecting to IP camera"""
    
    connection_requested = Signal(str, str)  # URL, name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to IP Camera")
        self.setModal(True)
        self.resize(400, 250)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Quick connect form (simplified - no tabs)
        self.setup_quick_connect_form(layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.setDefault(True)
        self.connect_button.clicked.connect(self.connect_camera)
        button_layout.addWidget(self.connect_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel("Enter camera connection details")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
    def setup_quick_connect_form(self, layout):
        """Setup quick connect form"""
        form_layout = QFormLayout()
        
        # Camera name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("My IP Camera")
        form_layout.addRow("Camera Name:", self.name_edit)
        
        # Server IP
        self.ip_edit = QLineEdit()
        self.ip_edit.setValidator(IPValidator())
        self.ip_edit.setPlaceholderText("192.168.1.100")
        self.ip_edit.textChanged.connect(self.update_url_preview)
        form_layout.addRow("IP Address:", self.ip_edit)
        
        # Port
        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1, 65535)
        self.port_spinbox.setValue(5000)
        self.port_spinbox.valueChanged.connect(self.update_url_preview)
        form_layout.addRow("Port:", self.port_spinbox)
        
        # Protocol
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["http", "https"])
        self.protocol_combo.currentTextChanged.connect(self.update_url_preview)
        form_layout.addRow("Protocol:", self.protocol_combo)
        
        # Stream path
        self.path_edit = QLineEdit()
        self.path_edit.setText("/video_feed")
        self.path_edit.textChanged.connect(self.update_url_preview)
        form_layout.addRow("Stream Path:", self.path_edit)
        
        # URL preview
        self.url_preview = QLabel()
        self.url_preview.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 8px;
                border-radius: 4px;
                font-family: monospace;
            }
        """)
        form_layout.addRow("Full URL:", self.url_preview)
        
        layout.addLayout(form_layout)
        
        # Update preview initially
        self.update_url_preview()

        
    def update_url_preview(self):
        """Update the URL preview"""
        protocol = self.protocol_combo.currentText()
        ip = self.ip_edit.text() or "0.0.0.0"
        port = self.port_spinbox.value()
        path = self.path_edit.text() or "/"
        
        if not path.startswith('/'):
            path = '/' + path
            
        url = f"{protocol}://{ip}:{port}{path}"
        self.url_preview.setText(url)
        
    def get_current_url(self):
        """Get the current URL"""
        return self.url_preview.text()
        
    def get_current_name(self):
        """Get the current camera name"""
        return self.name_edit.text() or "IP Camera"
            
    def test_connection(self):
        """Test connection to camera"""
        # This would be implemented to actually test the connection
        url = self.get_current_url()
        self.status_label.setText(f"Testing connection to {url}...")
        # In a real implementation, you'd use a QTimer and QNetworkAccessManager
        QTimer.singleShot(1000, lambda: self.status_label.setText("Connection test completed"))
        
    def connect_camera(self):
        """Connect to the camera"""
        url = self.get_current_url()
        name = self.get_current_name()
        
        # Validate URL
        if not url or not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter camera name and connection details.")
            return
            
        self.connection_requested.emit(url, name)
        self.accept()



class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, current_settings: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        self.current_settings = current_settings.copy()
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Settings tabs
        tab_widget = QTabWidget()
        
        # Video settings
        video_tab = QWidget()
        self.setup_video_settings(video_tab)
        tab_widget.addTab(video_tab, "Video")
        
        # Connection settings
        connection_tab = QWidget()
        self.setup_connection_settings(connection_tab)
        tab_widget.addTab(connection_tab, "Connection")
        
        # Interface settings
        interface_tab = QWidget()
        self.setup_interface_settings(interface_tab)
        tab_widget.addTab(interface_tab, "Interface")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        
        layout.addWidget(button_box)
        
    def setup_video_settings(self, parent):
        """Setup video settings tab"""
        layout = QFormLayout(parent)
        
        # Video fit mode
        self.fit_mode_combo = QComboBox()
        self.fit_mode_combo.addItems([
            "Keep Aspect Ratio",
            "Keep Aspect Ratio by Expanding", 
            "Ignore Aspect Ratio"
        ])
        layout.addRow("Video Fit Mode:", self.fit_mode_combo)
        
        # Show overlay
        self.show_overlay_check = QCheckBox("Show video overlay (FPS, resolution)")
        layout.addRow("", self.show_overlay_check)
        
        # Auto-reconnect
        self.auto_reconnect_check = QCheckBox("Automatically reconnect on connection loss")
        layout.addRow("", self.auto_reconnect_check)
        
        # Reconnection delay
        self.reconnect_delay_spinbox = QSpinBox()
        self.reconnect_delay_spinbox.setRange(1, 60)
        self.reconnect_delay_spinbox.setSuffix(" seconds")
        layout.addRow("Reconnection Delay:", self.reconnect_delay_spinbox)
        
    def setup_connection_settings(self, parent):
        """Setup connection settings tab"""
        layout = QFormLayout(parent)
        
        # Connection timeout
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(5, 120)
        self.timeout_spinbox.setSuffix(" seconds")
        layout.addRow("Connection Timeout:", self.timeout_spinbox)
        
        # Buffer size
        self.buffer_size_spinbox = QSpinBox()
        self.buffer_size_spinbox.setRange(512, 8192)
        self.buffer_size_spinbox.setSuffix(" bytes")
        layout.addRow("Stream Buffer Size:", self.buffer_size_spinbox)
        
        # User agent
        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setPlaceholderText("IP-Camera-GUI-Client/1.0")
        layout.addRow("User Agent:", self.user_agent_edit)
        
    def setup_interface_settings(self, parent):
        """Setup interface settings tab"""
        layout = QFormLayout(parent)
        
        # Window always on top
        self.always_on_top_check = QCheckBox("Keep window always on top")
        layout.addRow("", self.always_on_top_check)
        
        # Start fullscreen
        self.start_fullscreen_check = QCheckBox("Start in fullscreen mode")
        layout.addRow("", self.start_fullscreen_check)
        
        # Save window position
        self.save_position_check = QCheckBox("Remember window position and size")
        layout.addRow("", self.save_position_check)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System Default", "Light", "Dark"])
        layout.addRow("Theme:", self.theme_combo)
        
    def load_settings(self):
        """Load current settings into controls"""
        # Video settings
        self.fit_mode_combo.setCurrentIndex(self.current_settings.get('video_fit_mode', 0))
        self.show_overlay_check.setChecked(self.current_settings.get('show_overlay', True))
        self.auto_reconnect_check.setChecked(self.current_settings.get('auto_reconnect', True))
        self.reconnect_delay_spinbox.setValue(self.current_settings.get('reconnect_delay', 3))
        
        # Connection settings
        self.timeout_spinbox.setValue(self.current_settings.get('connection_timeout', 10))
        self.buffer_size_spinbox.setValue(self.current_settings.get('buffer_size', 1024))
        self.user_agent_edit.setText(self.current_settings.get('user_agent', 'IP-Camera-GUI-Client/1.0'))
        
        # Interface settings
        self.always_on_top_check.setChecked(self.current_settings.get('always_on_top', False))
        self.start_fullscreen_check.setChecked(self.current_settings.get('start_fullscreen', False))
        self.save_position_check.setChecked(self.current_settings.get('save_position', True))
        self.theme_combo.setCurrentIndex(self.current_settings.get('theme', 0))
        
    def get_settings(self) -> Dict[str, Any]:
        """Get settings from controls"""
        return {
            # Video settings
            'video_fit_mode': self.fit_mode_combo.currentIndex(),
            'show_overlay': self.show_overlay_check.isChecked(),
            'auto_reconnect': self.auto_reconnect_check.isChecked(),
            'reconnect_delay': self.reconnect_delay_spinbox.value(),
            
            # Connection settings
            'connection_timeout': self.timeout_spinbox.value(),
            'buffer_size': self.buffer_size_spinbox.value(),
            'user_agent': self.user_agent_edit.text(),
            
            # Interface settings
            'always_on_top': self.always_on_top_check.isChecked(),
            'start_fullscreen': self.start_fullscreen_check.isChecked(),
            'save_position': self.save_position_check.isChecked(),
            'theme': self.theme_combo.currentIndex()
        }
        
    def accept_settings(self):
        """Accept and emit settings"""
        new_settings = self.get_settings()
        self.settings_changed.emit(new_settings)
        self.accept()
        
    def restore_defaults(self):
        """Restore default settings"""
        defaults = {
            'video_fit_mode': 0,
            'show_overlay': True,
            'auto_reconnect': True,
            'reconnect_delay': 3,
            'connection_timeout': 10,
            'buffer_size': 1024,
            'user_agent': 'IP-Camera-GUI-Client/1.0',
            'always_on_top': False,
            'start_fullscreen': False,
            'save_position': True,
            'theme': 0
        }
        
        self.current_settings = defaults
        self.load_settings()


class AboutDialog(QDialog):
    """About dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About IP Camera Viewer")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # App info
        app_label = QLabel("IP Camera Viewer")
        app_label.setAlignment(Qt.AlignCenter)
        app_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(app_label)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addWidget(QLabel(""))
        
        # Description
        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(150)
        desc_text.setText(
            "A professional desktop application for viewing IP camera streams.\n\n"
            "Features:\n"
            "• Real-time MJPEG stream viewing\n"
            "• Connection management\n"
            "• Customizable video display\n"
            "• Cross-platform compatibility\n\n"
            "Built with PySide6 and Python."
        )
        layout.addWidget(desc_text)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)