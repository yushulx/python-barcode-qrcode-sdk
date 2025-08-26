#!/usr/bin/env python3
"""
IP Camera Viewer - Main Application
A professional desktop application for viewing IP camera streams using PySide6.
"""

import sys
import json
import os
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, QTimer, QSettings, QSize, QPoint, Signal
from PySide6.QtGui import QAction, QKeySequence, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QStatusBar, QToolBar, QPushButton, QLabel, QSplitter,
    QMessageBox, QFileDialog, QFrame, QSizePolicy
)

from video_widget import IPCameraVideoWidget
from dialogs import ConnectionDialog, SettingsDialog, AboutDialog


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Set window flags to ensure close button works
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowCloseButtonHint | 
            Qt.WindowType.WindowMinMaxButtonsHint | 
            Qt.WindowType.WindowTitleHint
        )
        
        # Application settings
        self.settings = QSettings('IPCameraViewer', 'MainWindow')
        self.app_settings = self.load_app_settings()
        
        # UI state
        self.is_connected = False
        self.current_camera_name = ""
        self.current_camera_url = ""
        self.is_fullscreen = False
        
        # Setup UI
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_connections()
        
        # Apply settings
        self.apply_settings()
        
        # Restore window state
        self.restore_window_state()
        
        # Update UI state
        self.update_ui_state()
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Set window properties
        self.setWindowTitle("IP Camera Viewer")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Vertical)
        
        # Video display area
        self.video_widget = IPCameraVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.video_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # Set splitter proportions (video gets most space)
        splitter.setSizes([500, 100])
        splitter.setCollapsible(1, True)  # Control panel can be collapsed
        
        main_layout.addWidget(splitter)
        
    def create_control_panel(self):
        """Create the control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMaximumHeight(120)
        
        layout = QVBoxLayout(panel)
        
        # Connection controls - removed duplicate buttons for simplicity
        # (Connection controls are available in toolbar and menu)
        conn_layout = QHBoxLayout()
        conn_layout.addStretch()  # Just add stretch to maintain layout
        
        layout.addLayout(conn_layout)
        
        # Status information
        info_layout = QHBoxLayout()
        
        self.camera_info_label = QLabel("No camera connected")
        self.camera_info_label.setStyleSheet("color: #666; font-weight: bold;")
        info_layout.addWidget(self.camera_info_label)
        
        info_layout.addStretch()
        
        self.fps_label = QLabel("FPS: 0.0")
        info_layout.addWidget(self.fps_label)
        
        self.resolution_label = QLabel("Resolution: 0x0")
        info_layout.addWidget(self.resolution_label)
        
        layout.addLayout(info_layout)
        
        return panel
        
    def setup_menus(self):
        """Setup application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        connect_action = QAction("&Connect to Camera...", self)
        connect_action.setShortcut(QKeySequence.Open)
        connect_action.setStatusTip("Connect to an IP camera")
        connect_action.triggered.connect(self.show_connection_dialog)
        file_menu.addAction(connect_action)
        
        disconnect_action = QAction("&Disconnect", self)
        disconnect_action.setShortcut(QKeySequence("Ctrl+D"))
        disconnect_action.setStatusTip("Disconnect from current camera")
        disconnect_action.triggered.connect(self.disconnect_camera)
        file_menu.addAction(disconnect_action)
        self.disconnect_action = disconnect_action
        
        file_menu.addSeparator()
        
        screenshot_action = QAction("Take &Screenshot", self)
        screenshot_action.setShortcut(QKeySequence("Ctrl+S"))
        screenshot_action.setStatusTip("Save current frame as image")
        screenshot_action.triggered.connect(self.take_screenshot)
        file_menu.addAction(screenshot_action)
        self.screenshot_action = screenshot_action
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close_application)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.setStatusTip("Toggle fullscreen mode")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        view_menu.addSeparator()
        
        # Video fit mode submenu
        fit_menu = view_menu.addMenu("Video &Fit Mode")
        
        fit_actions = []
        fit_modes = ["Keep Aspect Ratio", "Keep Aspect Ratio by Expanding", "Ignore Aspect Ratio"]
        for i, mode in enumerate(fit_modes):
            action = QAction(mode, self)
            action.setCheckable(True)
            action.setData(i)
            action.triggered.connect(lambda checked, idx=i: self.set_video_fit_mode(idx))
            fit_menu.addAction(action)
            fit_actions.append(action)
            
        fit_actions[0].setChecked(True)  # Default to first mode
        self.fit_mode_actions = fit_actions
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence.Preferences)
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(self.show_settings_dialog)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About...", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Setup application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Connect button
        connect_action = QAction("Connect", self)
        # Icon will be set after window is shown
        connect_action.setToolTip("Connect to camera")
        connect_action.triggered.connect(self.show_connection_dialog)
        toolbar.addAction(connect_action)
        
        # Disconnect button
        disconnect_action = QAction("Disconnect", self)
        # Icon will be set after window is shown
        disconnect_action.setToolTip("Disconnect from camera")
        disconnect_action.triggered.connect(self.disconnect_camera)
        disconnect_action.setEnabled(False)
        toolbar.addAction(disconnect_action)
        self.toolbar_disconnect_action = disconnect_action
        
        toolbar.addSeparator()
        
        # Screenshot button
        screenshot_action = QAction("Screenshot", self)
        # Icon will be set after window is shown
        screenshot_action.setToolTip("Take screenshot")
        screenshot_action.triggered.connect(self.take_screenshot)
        screenshot_action.setEnabled(False)
        toolbar.addAction(screenshot_action)
        self.toolbar_screenshot_action = screenshot_action
        
        # Fullscreen button
        fullscreen_action = QAction("Fullscreen", self)
        # Icon will be set after window is shown
        fullscreen_action.setToolTip("Toggle fullscreen")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        toolbar.addAction(fullscreen_action)
        
    def setup_statusbar(self):
        """Setup application status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connection status
        self.connection_status_label = QLabel("Disconnected")
        self.status_bar.addWidget(self.connection_status_label)
        
        self.status_bar.addPermanentWidget(QLabel("|"))
        
        # FPS display
        self.status_fps_label = QLabel("FPS: 0.0")
        self.status_bar.addPermanentWidget(self.status_fps_label)
        
        # Resolution display
        self.status_resolution_label = QLabel("Resolution: 0x0")
        self.status_bar.addPermanentWidget(self.status_resolution_label)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Video widget connections
        self.video_widget.connection_changed.connect(self.on_connection_changed)
        self.video_widget.error_occurred.connect(self.on_error_occurred)
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_info)
        self.status_timer.start(1000)  # Update every second
        
    def show_connection_dialog(self):
        """Show connection dialog"""
        dialog = ConnectionDialog(self)
        dialog.connection_requested.connect(self.connect_to_camera)
        dialog.exec()
        
    def connect_to_camera(self, url: str, name: str):
        """Connect to a camera"""
        try:
            self.current_camera_url = url
            self.current_camera_name = name
            
            # Apply connection timeout from settings
            timeout = self.app_settings.get('connection_timeout', 5)  # Shorter default timeout
            self.video_widget.set_connection_timeout(timeout)
            
            # Reset error tracking
            self._last_error_time = 0
            
            # Connect to stream
            self.video_widget.connect_to_stream(url)
            
            self.status_bar.showMessage(f"Connecting to {name}...", 3000)
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
            
    def disconnect_camera(self):
        """Disconnect from camera"""
        self.video_widget.disconnect_stream()
        self.current_camera_url = ""
        self.current_camera_name = ""
        self.update_ui_state()
        
    def on_connection_changed(self, connected: bool):
        """Handle connection status change"""
        self.is_connected = connected
        self.update_ui_state()
        
        if connected:
            self.status_bar.showMessage(f"Connected to {self.current_camera_name}", 3000)
        else:
            self.status_bar.showMessage("Disconnected", 3000)
            
    def on_error_occurred(self, error_message: str):
        """Handle error from video widget"""
        self.status_bar.showMessage(f"Error: {error_message}", 5000)
        
        # Limit error dialogs to prevent spam
        if not hasattr(self, '_last_error_time'):
            self._last_error_time = 0
            
        import time
        current_time = time.time()
        
        # Only show error dialog if it's been more than 10 seconds since last one
        if current_time - self._last_error_time > 10:
            if "connection" in error_message.lower() or "timeout" in error_message.lower():
                self._last_error_time = current_time
                # Use non-blocking message box
                QTimer.singleShot(100, lambda: self._show_error_dialog(error_message))
            
    def update_ui_state(self):
        """Update UI state based on connection status"""
        # Update menu actions
        self.disconnect_action.setEnabled(self.is_connected)
        self.screenshot_action.setEnabled(self.is_connected)
        
        # Update toolbar actions
        self.toolbar_disconnect_action.setEnabled(self.is_connected)
        self.toolbar_screenshot_action.setEnabled(self.is_connected)
        
        # Update labels
        if self.is_connected and self.current_camera_name:
            self.camera_info_label.setText(f"Connected to: {self.current_camera_name}")
            self.connection_status_label.setText("Connected")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.camera_info_label.setText("No camera connected")
            self.connection_status_label.setText("Disconnected")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def update_status_info(self):
        """Update status information"""
        if self.is_connected:
            fps = self.video_widget.get_current_fps()
            width, height = self.video_widget.get_current_resolution()
            
            self.fps_label.setText(f"FPS: {fps:.1f}")
            self.resolution_label.setText(f"Resolution: {width}x{height}")
            
            self.status_fps_label.setText(f"FPS: {fps:.1f}")
            self.status_resolution_label.setText(f"Resolution: {width}x{height}")
        else:
            self.fps_label.setText("FPS: 0.0")
            self.resolution_label.setText("Resolution: 0x0")
            
            self.status_fps_label.setText("FPS: 0.0")
            self.status_resolution_label.setText("Resolution: 0x0")
            
    def take_screenshot(self):
        """Take a screenshot of current frame"""
        if not self.is_connected:
            return
            
        try:
            # Get current frame from video widget
            current_image = self.video_widget.video_display.current_image
            if not current_image:
                QMessageBox.warning(self, "Screenshot", "No frame available to capture.")
                return
                
            # Save file dialog
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Screenshot",
                f"screenshot_{self.current_camera_name.replace(' ', '_')}.jpg",
                "JPEG Files (*.jpg);;PNG Files (*.png);;All Files (*)"
            )
            
            if filename:
                pixmap = QPixmap.fromImage(current_image)
                if pixmap.save(filename):
                    self.status_bar.showMessage(f"Screenshot saved: {filename}", 3000)
                else:
                    QMessageBox.critical(self, "Error", "Failed to save screenshot.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Screenshot Error", f"Failed to take screenshot: {str(e)}")
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.is_fullscreen:
            self.showNormal()
            self.menuBar().show()
            self.statusBar().show()
            self.findChild(QToolBar).show()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.menuBar().hide()
            self.statusBar().hide()
            self.findChild(QToolBar).hide()
            self.is_fullscreen = True
            
    def set_video_fit_mode(self, mode: int):
        """Set video fit mode"""
        fit_modes = [Qt.KeepAspectRatio, Qt.KeepAspectRatioByExpanding, Qt.IgnoreAspectRatio]
        if 0 <= mode < len(fit_modes):
            self.video_widget.set_fit_mode(fit_modes[mode])
            
            # Update menu checkmarks
            for i, action in enumerate(self.fit_mode_actions):
                action.setChecked(i == mode)
                
    def show_settings_dialog(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.app_settings, self)
        dialog.settings_changed.connect(self.apply_new_settings)
        dialog.exec()
        
    def apply_new_settings(self, new_settings: Dict[str, Any]):
        """Apply new settings"""
        self.app_settings.update(new_settings)
        self.save_app_settings()
        self.apply_settings()
        
    def apply_settings(self):
        """Apply current settings to the application"""
        # Video settings
        overlay_enabled = self.app_settings.get('show_overlay', True)
        self.video_widget.set_overlay_enabled(overlay_enabled)
        
        fit_mode = self.app_settings.get('video_fit_mode', 0)
        self.set_video_fit_mode(fit_mode)
        
        # Window settings - skip always_on_top to avoid close button issues
        # always_on_top functionality removed for simplicity
        
        # Fullscreen on startup
        if self.app_settings.get('start_fullscreen', False):
            QTimer.singleShot(100, self.toggle_fullscreen)
            
    def show_about_dialog(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def load_app_settings(self) -> Dict[str, Any]:
        """Load application settings"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
        # Default settings
        return {
            'video_fit_mode': 0,
            'show_overlay': True,
            'auto_reconnect': True,
            'reconnect_delay': 3,
            'connection_timeout': 10,
            'buffer_size': 1024,
            'user_agent': 'IP-Camera-GUI-Client/1.0',
            'start_fullscreen': False,
            'save_position': True,
            'theme': 0
        }
        
    def save_app_settings(self):
        """Save application settings"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_file, 'w') as f:
                json.dump(self.app_settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def restore_window_state(self):
        """Restore window position and size"""
        if self.app_settings.get('save_position', True):
            # Restore geometry
            geometry = self.settings.value('geometry')
            if geometry:
                self.restoreGeometry(geometry)
            else:
                # Default size and position
                self.resize(1200, 800)
                self.move(100, 100)
                
            # Restore window state
            window_state = self.settings.value('windowState')
            if window_state:
                self.restoreState(window_state)
                
    def save_window_state(self):
        """Save window position and size"""
        if self.app_settings.get('save_position', True):
            self.settings.setValue('geometry', self.saveGeometry())
            self.settings.setValue('windowState', self.saveState())
            
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)
            
    def close_application(self):
        """Close the application properly"""
        # This will trigger closeEvent which handles cleanup
        self.close()
        # Ensure the application exits
        QApplication.quit()
        
    def _show_error_dialog(self, error_message: str):
        """Show error dialog in a non-blocking way"""
        if self.isVisible():
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Connection Error")
            msg.setText(error_message)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setAttribute(Qt.WA_DeleteOnClose)
            msg.show()
    
    def closeEvent(self, event):
        """Handle application close"""
        try:
            # Stop status timer
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            
            # Disconnect camera first
            if self.is_connected:
                try:
                    self.video_widget.disconnect_stream()
                    # Give it a moment to clean up
                    QApplication.processEvents()
                except:
                    pass
            
            # Force quit any background threads
            if hasattr(self.video_widget, 'stream_thread'):
                try:
                    if self.video_widget.stream_thread.isRunning():
                        self.video_widget.stream_thread.stop_stream()
                        if not self.video_widget.stream_thread.wait(1000):  # 1 second timeout
                            self.video_widget.stream_thread.terminate()
                except:
                    pass
            
            # Save window state
            self.save_window_state()
            
            # Save settings
            self.save_app_settings()
                
            event.accept()
            
        except Exception as e:
            # Force close even if there are errors
            print(f"Error during close: {e}")
            event.accept()
            
        # Ensure application quits
        QApplication.quit()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("IP Camera Viewer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("IP Camera Tools")
    
    # Set quit on last window closed
    app.setQuitOnLastWindowClosed(True)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    try:
        return app.exec()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        window.close()
        return 0
    finally:
        # Ensure cleanup
        try:
            window.close()
        except:
            pass


if __name__ == '__main__':
    sys.exit(main())