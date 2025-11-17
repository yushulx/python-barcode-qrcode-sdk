"""
Barcode Reader Implementations
This module contains implementations for different barcode reading libraries.
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from pyzbar import pyzbar as zbar
from PIL import Image
import pyzbar.pyzbar as pyzbar
from .benchmark_framework import BarcodeReaderInterface


class ZXingCppReader(BarcodeReaderInterface):
    """ZXing-Cpp implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("ZXing_Cpp", config)
        self.reader = None
    
    def initialize(self) -> bool:
        """Initialize the ZXing-Cpp reader."""
        try:
            import zxingcpp
            self.reader = zxingcpp
            return True
        except ImportError:
            print("ZXing-Cpp not installed. Install with: pip install zxing-cpp")
            return False
        except Exception as e:
            print(f"Failed to initialize ZXing_Cpp: {e}")
            return False
    
    def decode_barcodes(self, image_path: str) -> Tuple[List[Dict[str, Any]], float]:
        """Decode barcodes using ZXing-Cpp."""
        import time
        start_time = time.perf_counter()
        
        try:
            if self.reader is None:
                raise RuntimeError("ZXing-Cpp reader not initialized")
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # ZXing-Cpp works with grayscale or RGB
            results = self.reader.read_barcodes(image)
            
            detected_barcodes = []
            for result in results:
                detected_barcodes.append({
                    'data': result.text,
                    'type': result.format.name,
                    'quality': 1.0,  # ZXing-Cpp doesn't provide quality metric
                    'position': {
                        'x': result.position.top_left.x if hasattr(result, 'position') else 0,
                        'y': result.position.top_left.y if hasattr(result, 'position') else 0,
                        'width': 0,
                        'height': 0
                    }
                })
            
            processing_time = time.perf_counter() - start_time
            return detected_barcodes, processing_time
            
        except Exception as e:
            print(f"Error in ZXing_Cpp decode: {e}")
            processing_time = time.perf_counter() - start_time
            return [], processing_time
    
    def cleanup(self):
        """Cleanup ZXing-Cpp resources."""
        self.reader = None


class PyZBarReader(BarcodeReaderInterface):
    """PyZBar implementation (pure Python binding)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("PyZBar", config)
    
    def initialize(self) -> bool:
        """Initialize the PyZBar reader."""
        try:
            # pyzbar doesn't require explicit scanner initialization
            return True
        except Exception as e:
            print(f"Failed to initialize PyZBar: {e}")
            return False
    
    def decode_barcodes(self, image_path: str) -> Tuple[List[Dict[str, Any]], float]:
        """Decode barcodes using PyZBar."""
        import time
        start_time = time.perf_counter()
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Try multiple preprocessing techniques for better detection
            detected_barcodes = []
            
            # Attempt 1: Original image
            results = pyzbar.decode(image)
            for result in results:
                detected_barcodes.append(self._format_result(result))
            
            # Attempt 2: Grayscale with histogram equalization (if no results)
            if not detected_barcodes:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                enhanced = cv2.equalizeHist(gray)
                results = pyzbar.decode(enhanced)
                for result in results:
                    detected_barcodes.append(self._format_result(result))
            
            # Attempt 3: Try with adaptive thresholding (if still no results)
            if not detected_barcodes:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 11, 2)
                results = pyzbar.decode(adaptive)
                for result in results:
                    detected_barcodes.append(self._format_result(result))
            
            # Remove duplicates (same data)
            seen = set()
            unique_barcodes = []
            for barcode in detected_barcodes:
                if barcode['data'] not in seen:
                    seen.add(barcode['data'])
                    unique_barcodes.append(barcode)
            
            processing_time = time.perf_counter() - start_time
            return unique_barcodes, processing_time
            
        except Exception as e:
            print(f"Error in PyZBar decode: {e}")
            processing_time = time.perf_counter() - start_time
            return [], processing_time
    
    def _format_result(self, result) -> Dict[str, Any]:
        """Format pyzbar result to standard format."""
        (x, y, w, h) = result.rect
        return {
            'data': result.data.decode('utf-8'),
            'type': result.type,
            'quality': 1.0,  # pyzbar doesn't provide quality metric
            'position': {
                'x': x,
                'y': y,
                'width': w,
                'height': h
            }
        }
    
    def cleanup(self):
        """Cleanup PyZBar resources."""
        pass


class DynamsoftBarcodeReader(BarcodeReaderInterface):
    """Dynamsoft Capture Vision Bundle implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Dynamsoft", config)
        self.license = config.get('license', '')
        self.cvr_instance = None
    
    def initialize(self) -> bool:
        """Initialize Dynamsoft Capture Vision Router."""
        try:
            from dynamsoft_capture_vision_bundle import (
                LicenseManager, CaptureVisionRouter, EnumErrorCode
            )
            
            # Initialize license
            error_code, error_message = LicenseManager.init_license(self.license)
            if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
                print(f"Dynamsoft license initialization failed: ErrorCode: {error_code}, ErrorString: {error_message}")
                return False
            
            # Create CaptureVisionRouter instance
            self.cvr_instance = CaptureVisionRouter()
            print(f"Dynamsoft Barcode Reader initialized successfully")
            return True
            
        except ImportError as e:
            print(f"Failed to import Dynamsoft SDK: {e}")
            print("Please install: pip install dynamsoft-capture-vision-bundle")
            return False
        except Exception as e:
            print(f"Failed to initialize Dynamsoft: {e}")
            return False
    
    def decode_barcodes(self, image_path: str) -> Tuple[List[Dict[str, Any]], float]:
        """Decode barcodes using Dynamsoft Capture Vision."""
        import time
        from dynamsoft_capture_vision_bundle import EnumPresetTemplate, EnumErrorCode
        
        start_time = time.perf_counter()
        
        try:
            if self.cvr_instance is None:
                raise RuntimeError("Dynamsoft CVR not initialized")
            
            # Load image with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Capture barcodes
            result = self.cvr_instance.capture(
                image, EnumPresetTemplate.PT_READ_BARCODES.value
            )
            
            detected_barcodes = []
            
            if result.get_error_code() != EnumErrorCode.EC_OK:
                print(f"Dynamsoft decode error: {result.get_error_code()}, {result.get_error_string()}")
            else:
                items = result.get_items()
                for item in items:
                    # Extract barcode information
                    barcode_text = item.get_text()
                    barcode_format = item.get_format_string()
                    location = item.get_location()
                    
                    # Calculate bounding box from polygon points
                    points = location.points
                    x_coords = [p.x for p in points]
                    y_coords = [p.y for p in points]
                    x = min(x_coords)
                    y = min(y_coords)
                    width = max(x_coords) - x
                    height = max(y_coords) - y
                    
                    barcode_info = {
                        'data': barcode_text,
                        'type': barcode_format,
                        'quality': 1.0,  # Dynamsoft doesn't expose confidence in this API
                        'position': {
                            'x': int(x),
                            'y': int(y),
                            'width': int(width),
                            'height': int(height)
                        }
                    }
                    detected_barcodes.append(barcode_info)
            
            processing_time = time.perf_counter() - start_time
            return detected_barcodes, processing_time
            
        except Exception as e:
            print(f"Error in Dynamsoft decode: {e}")
            processing_time = time.perf_counter() - start_time
            return [], processing_time
    
    def cleanup(self):
        """Cleanup Dynamsoft resources."""
        if self.cvr_instance:
            # CaptureVisionRouter doesn't require explicit cleanup in Python
            self.cvr_instance = None


def create_reader(library_name: str, config: Dict[str, Any]) -> BarcodeReaderInterface:
    """Factory function to create barcode readers."""
    readers = {
        'zxing_cpp': ZXingCppReader,
        'pyzbar': PyZBarReader,
        'dynamsoft': DynamsoftBarcodeReader
    }
    
    if library_name not in readers:
        raise ValueError(f"Unknown library: {library_name}")
    
    return readers[library_name](config)