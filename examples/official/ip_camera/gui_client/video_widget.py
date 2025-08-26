#!/usr/bin/env python3
"""
Video Widget for IP Camera Stream Viewer
Custom PySide6 widget to display MJPEG streams from IP cameras.
"""

import sys
import requests
import threading
import time
from io import BytesIO
from typing import Optional, Callable

from PySide6.QtCore import QThread, Signal, QTimer, Qt, QSize
from PySide6.QtGui import QPixmap, QImage, QPainter, QFont, QPen, QBrush
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy


class MJPEGStreamThread(QThread):
    """Thread for fetching MJPEG stream from IP camera"""
    
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    connection_status = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stream_url = ""
        self.running = False
        self.session = None
        self.timeout = 10
        self.retry_interval = 3
        
    def set_stream_url(self, url: str):
        """Set the MJPEG stream URL"""
        self.stream_url = url
        
    def set_timeout(self, timeout: int):
        """Set request timeout in seconds"""
        self.timeout = timeout
        
    def stop_stream(self):
        """Stop the stream thread"""
        self.running = False
        if self.session:
            try:
                self.session.close()
            except:
                pass
            self.session = None
        # Force thread to quit
        self.quit()
        # Wait with timeout to prevent hanging
        if not self.wait(3000):  # 3 second timeout
            self.terminate()
        
    def run(self):
        """Main thread loop for fetching MJPEG frames"""
        self.running = True
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while self.running and consecutive_errors < max_consecutive_errors:
            try:
                if not self.stream_url:
                    self.msleep(1000)
                    continue
                    
                # Create new session for each connection attempt
                self.session = requests.Session()
                
                # Request MJPEG stream with shorter timeout
                response = self.session.get(
                    self.stream_url,
                    stream=True,
                    timeout=5,  # Shorter timeout
                    headers={'User-Agent': 'IP-Camera-GUI-Client/1.0'}
                )
                
                if response.status_code == 200:
                    self.connection_status.emit(True)
                    consecutive_errors = 0  # Reset error count on success
                    self._process_mjpeg_stream(response)
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.reason}")
                    
            except Exception as e:
                consecutive_errors += 1
                self.connection_status.emit(False)
                
                # Only emit error for first few attempts to prevent spam
                if consecutive_errors <= 2:
                    self.error_occurred.emit(f"Stream error: {str(e)}")
                
                # Wait before retry, but check if we should stop
                for _ in range(self.retry_interval * 10):  # Check every 100ms
                    if not self.running:
                        break
                    self.msleep(100)
                    
            finally:
                if self.session:
                    try:
                        self.session.close()
                    except:
                        pass
                    self.session = None
                    
    def _process_mjpeg_stream(self, response):
        """Process the MJPEG stream and extract frames"""
        buffer = b""
        
        try:
            for chunk in response.iter_content(chunk_size=1024):
                if not self.running:
                    break
                    
                if chunk:
                    buffer += chunk
                    
                    # Look for JPEG frame boundaries
                    while True:
                        # Find start of JPEG (FF D8)
                        start_marker = buffer.find(b'\xff\xd8')
                        if start_marker == -1:
                            break
                            
                        # Find end of JPEG (FF D9)
                        end_marker = buffer.find(b'\xff\xd9', start_marker)
                        if end_marker == -1:
                            # Incomplete frame, wait for more data
                            break
                            
                        # Extract complete JPEG frame
                        jpeg_data = buffer[start_marker:end_marker + 2]
                        buffer = buffer[end_marker + 2:]
                        
                        # Convert JPEG to QImage
                        try:
                            image = QImage.fromData(jpeg_data, "JPEG")
                            if not image.isNull():
                                self.frame_ready.emit(image)
                        except Exception as e:
                            # Don't spam with frame decode errors
                            pass
                            
                        # Prevent buffer from growing too large
                        if len(buffer) > 1024 * 1024:  # 1MB limit
                            buffer = buffer[-512 * 1024:]  # Keep last 512KB
                            
        except Exception as e:
            if self.running:  # Only report errors if we're supposed to be running
                self.error_occurred.emit(f"Stream processing error: {str(e)}")


class VideoDisplayWidget(QLabel):
    """Widget for displaying video frames with overlay information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Widget properties
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        
        # Video properties
        self.current_image = None
        self.aspect_ratio = 16.0 / 9.0
        self.fit_mode = Qt.KeepAspectRatio
        
        # Overlay properties
        self.show_overlay = True
        self.overlay_text = "No Signal"
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.frame_count = 0
        
        # Set initial placeholder
        self.show_placeholder()
        
        # Make sure placeholder is visible
        self.setMinimumSize(320, 240)
        
    def show_placeholder(self):
        """Show placeholder when no video signal"""
        self.clear()
        self.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #444;
                border-radius: 8px;
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.setText("📹 No Video Signal\nClick Connect to start streaming")
        self.setAlignment(Qt.AlignCenter)
        
    def set_overlay_text(self, text: str):
        """Set overlay text"""
        self.overlay_text = text
        self.update()
        
    def set_fit_mode(self, mode):
        """Set how video fits in the widget"""
        self.fit_mode = mode
        if self.current_image:
            self.update_display()
            
    def update_frame(self, image: QImage):
        """Update the displayed frame"""
        if image.isNull():
            return
            
        self.current_image = image.copy()
        self.aspect_ratio = image.width() / image.height()
        
        # Update FPS counter
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps_counter = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
            
        self.update_display()
        
    def update_display(self):
        """Update the display with current frame and overlay"""
        if not self.current_image:
            return
            
        # Calculate display size
        widget_size = self.size()
        image_size = self.current_image.size()
        
        # Scale image to fit widget
        if self.fit_mode == Qt.KeepAspectRatio:
            scaled_size = image_size.scaled(widget_size, Qt.KeepAspectRatio)
        elif self.fit_mode == Qt.KeepAspectRatioByExpanding:
            scaled_size = image_size.scaled(widget_size, Qt.KeepAspectRatioByExpanding)
        else:
            scaled_size = widget_size
            
        # Create scaled image
        scaled_image = self.current_image.scaled(
            scaled_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Create pixmap with overlay
        pixmap = QPixmap.fromImage(scaled_image)
        
        if self.show_overlay:
            self._draw_overlay(pixmap)
            
        self.setPixmap(pixmap)
        
    def _draw_overlay(self, pixmap: QPixmap):
        """Draw overlay information on the pixmap"""
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set up overlay style
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        
        # Draw semi-transparent background
        overlay_rect = pixmap.rect()
        overlay_rect.setHeight(30)
        painter.fillRect(overlay_rect, QBrush(Qt.black, Qt.SolidPattern))
        painter.setOpacity(0.8)
        
        # Draw FPS counter
        painter.setPen(QPen(Qt.white))
        fps_text = f"FPS: {self.fps_counter:.1f}"
        painter.drawText(10, 20, fps_text)
        
        # Draw resolution
        if self.current_image:
            res_text = f"Resolution: {self.current_image.width()}x{self.current_image.height()}"
            painter.drawText(100, 20, res_text)
        
        # Draw additional overlay text
        if self.overlay_text:
            painter.drawText(250, 20, self.overlay_text)
            
        painter.end()
        
    def sizeHint(self):
        """Provide size hint based on aspect ratio"""
        if self.aspect_ratio > 0:
            width = 640
            height = int(width / self.aspect_ratio)
            return QSize(width, height)
        return QSize(640, 480)
        
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if self.current_image:
            self.update_display()


class IPCameraVideoWidget(QWidget):
    """Complete video widget with stream thread management"""
    
    connection_changed = Signal(bool)
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create video display
        self.video_display = VideoDisplayWidget()
        layout.addWidget(self.video_display)
        
        # Create stream thread
        self.stream_thread = MJPEGStreamThread()
        self.stream_thread.frame_ready.connect(self.video_display.update_frame)
        self.stream_thread.error_occurred.connect(self.error_occurred.emit)
        self.stream_thread.connection_status.connect(self.connection_changed.emit)
        
        # Connection state
        self.is_connected = False
        self.current_url = ""
        
    def connect_to_stream(self, url: str):
        """Connect to MJPEG stream"""
        if self.is_connected:
            self.disconnect_stream()
            
        self.current_url = url
        self.stream_thread.set_stream_url(url)
        self.stream_thread.start()
        
    def disconnect_stream(self):
        """Disconnect from stream"""
        if self.stream_thread.isRunning():
            self.stream_thread.stop_stream()
            
        self.video_display.show_placeholder()
        self.is_connected = False
        self.current_url = ""
        
    def set_connection_timeout(self, timeout: int):
        """Set connection timeout"""
        self.stream_thread.set_timeout(timeout)
        
    def set_overlay_enabled(self, enabled: bool):
        """Enable/disable overlay"""
        self.video_display.show_overlay = enabled
        self.video_display.update()
        
    def set_fit_mode(self, mode):
        """Set video fit mode"""
        self.video_display.set_fit_mode(mode)
        
    def get_current_fps(self):
        """Get current FPS"""
        return self.video_display.fps_counter
        
    def get_current_resolution(self):
        """Get current resolution"""
        if self.video_display.current_image:
            img = self.video_display.current_image
            return (img.width(), img.height())
        return (0, 0)
        
    def closeEvent(self, event):
        """Handle widget close"""
        try:
            self.disconnect_stream()
            # Give threads time to clean up
            QTimer.singleShot(100, lambda: super(IPCameraVideoWidget, self).closeEvent(event))
        except:
            # Force close if there are issues
            super().closeEvent(event)
            
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.disconnect_stream()
        except:
            pass