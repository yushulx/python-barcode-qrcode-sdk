#!/usr/bin/env python3
"""
Barcode Scanner for IP Camera GUI Client
Integrates Dynamsoft Capture Vision Bundle for real-time barcode detection.
"""

import queue
import threading
import time
from typing import List, Optional
from PySide6.QtCore import QObject, Signal, QTimer

from dynamsoft_capture_vision_bundle import (
    LicenseManager, CaptureVisionRouter, ImageSourceAdapter, 
    CapturedResultReceiver, EnumErrorCode, EnumPresetTemplate, 
    EnumCapturedResultItemType
)
from utils import convertMat2ImageData


class FrameFetcher(ImageSourceAdapter):
    """Custom frame fetcher for Dynamsoft Capture Vision"""
    
    def __init__(self):
        super().__init__()
        self._has_frame = False
        
    def has_next_image_to_fetch(self) -> bool:
        return self._has_frame
    
    def add_frame(self, image_data):
        """Add frame to the buffer"""
        self.add_image_to_buffer(image_data)
        self._has_frame = True


class BarcodeResultReceiver(CapturedResultReceiver):
    """Custom result receiver for barcode detection results"""
    
    def __init__(self, result_queue):
        super().__init__()
        self.result_queue = result_queue
    
    def on_captured_result_received(self, captured_result):
        """Called when barcode detection results are available"""
        try:
            self.result_queue.put_nowait(captured_result)
        except queue.Full:
            # Drop old results if queue is full
            try:
                self.result_queue.get_nowait()
                self.result_queue.put_nowait(captured_result)
            except queue.Empty:
                pass


class BarcodeScanner(QObject):
    """
    Barcode scanner component that processes video frames
    and emits barcode detection results
    """
    
    # Signals
    barcode_detected = Signal(list)  # List of detected barcode results with details
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Scanner state
        self.is_initialized = False
        self.is_scanning = False
        
        # Dynamsoft components
        self.cvr = None
        self.fetcher = None
        self.receiver = None
        self.result_queue = queue.Queue(maxsize=10)
        
        # Latest barcode results with location information
        self.latest_barcodes = []
        self.last_detection_time = 0
        
        # Initialize license
        self._initialize_license()
    
    def _initialize_license(self):
        """Initialize Dynamsoft license"""
        try:
            license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
            
            error_code, error_msg = LicenseManager.init_license(license_key)
            
            if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
                self.error_occurred.emit(f"License initialization failed: {error_msg}")
                return
            
            self.is_initialized = True
            self._setup_scanner()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize barcode scanner: {str(e)}")
    
    def _setup_scanner(self):
        """Setup Dynamsoft Capture Vision components"""
        try:
            # Create capture vision router
            self.cvr = CaptureVisionRouter()
            
            # Create frame fetcher
            self.fetcher = FrameFetcher()
            self.cvr.set_input(self.fetcher)
            
            # Create result receiver
            self.receiver = BarcodeResultReceiver(self.result_queue)
            self.cvr.add_result_receiver(self.receiver)
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to setup barcode scanner: {str(e)}")
            self.is_initialized = False
    
    def start_scanning(self):
        """Start barcode scanning"""
        if not self.is_initialized or self.is_scanning:
            return
        
        try:
            # Start capturing with barcode template
            error_code, error_msg = self.cvr.start_capturing(
                EnumPresetTemplate.PT_READ_BARCODES.value
            )
            
            if error_code != EnumErrorCode.EC_OK:
                self.error_occurred.emit(f"Failed to start scanning: {error_msg}")
                return
            
            self.is_scanning = True
            
        except Exception as e:
            self.error_occurred.emit(f"Error starting barcode scanning: {str(e)}")
    
    def stop_scanning(self):
        """Stop barcode scanning"""
        if not self.is_scanning:
            return
        
        try:
            # Stop capturing
            if self.cvr:
                self.cvr.stop_capturing()
            
            # Clear result queue
            while not self.result_queue.empty():
                try:
                    self.result_queue.get_nowait()
                except queue.Empty:
                    break
            
            self.is_scanning = False
            
        except Exception as e:
            self.error_occurred.emit(f"Error stopping barcode scanning: {str(e)}")
    
    def process_frame(self, mat):
        """
        Process a frame for barcode detection
        
        Args:
            mat: OpenCV Mat object (BGR format)
        """
        if not self.is_scanning or not self.fetcher:
            return
        
        try:
            # Convert Mat to ImageData
            image_data = convertMat2ImageData(mat)
            
            # Add frame to scanner
            self.fetcher.add_frame(image_data)
            
        except Exception as e:
            # Don't spam with frame processing errors
            pass
    
    def get_fresh_results(self):
        """Get fresh barcode detection results from the queue right now"""
        if not self.is_scanning:
            return []
            
        detected_barcodes = []
        detected_texts = []
        
        try:
            # Process all available results right now
            while not self.result_queue.empty():
                try:
                    captured_result = self.result_queue.get_nowait()
                    items = captured_result.get_items()
                    
                    for item in items:
                        if item.get_type() == EnumCapturedResultItemType.CRIT_BARCODE:
                            text = item.get_text()
                            location = item.get_location()
                            
                            if text and location:
                                # Extract corner points
                                points = []
                                for i in range(4):
                                    x = int(location.points[i].x)
                                    y = int(location.points[i].y)
                                    points.append((x, y))
                                
                                # Create detailed barcode result
                                barcode_result = {
                                    'text': text,
                                    'points': points,
                                    'timestamp': time.time()
                                }
                                
                                detected_barcodes.append(barcode_result)
                                if text not in detected_texts:
                                    detected_texts.append(text)
                                
                                # Clean up location object
                                del location
                    
                except queue.Empty:
                    break
                except Exception as e:
                    # Continue processing other results
                    continue
            
            # Update latest results and emit if any barcodes detected
            if detected_barcodes:
                self.latest_barcodes = detected_barcodes
                self.last_detection_time = time.time()
                # Emit signal for text results panel
                self.barcode_detected.emit(detected_texts)
            
            # Return fresh results for immediate rendering
            return detected_barcodes
                
        except Exception as e:
            # Don't spam with result processing errors
            return []
            
    def get_latest_barcodes(self):
        """Get the cached barcode detection results (for backward compatibility)"""
        return self.latest_barcodes.copy() if self.latest_barcodes else []
    
    def is_available(self) -> bool:
        """Check if barcode scanning is available"""
        return self.is_initialized
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_scanning()
            
            if self.cvr:
                self.cvr = None
            if self.fetcher:
                self.fetcher = None
            if self.receiver:
                self.receiver = None
                
        except Exception:
            pass