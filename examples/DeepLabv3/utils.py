"""
Utility functions for Document Detection Application
"""
import time
import logging
from functools import wraps
from typing import Callable, Any
import numpy as np
import cv2
from PySide6.QtGui import QImage, QPixmap
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        return result, elapsed_ms
    return wrapper

class PerformanceTimer:
    """Context manager for timing code blocks"""
    def __init__(self, name: str = ""):
        self.name = name
        self.start_time = None
        self.elapsed_ms = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        end_time = time.perf_counter()
        self.elapsed_ms = (end_time - self.start_time) * 1000
        if self.name:
            logger = get_logger(__name__)
            logger.debug(f"{self.name}: {self.elapsed_ms:.2f}ms")

def numpy_to_qimage(array: np.ndarray) -> QImage:
    """Convert numpy array to QImage"""
    if array.dtype != np.uint8:
        array = array.astype(np.uint8)
    
    if len(array.shape) == 2:  # Grayscale
        height, width = array.shape
        bytes_per_line = width
        return QImage(array.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
    elif len(array.shape) == 3:  # Color
        height, width, channels = array.shape
        bytes_per_line = channels * width
        if channels == 3:  # BGR to RGB
            array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
            return QImage(array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        elif channels == 4:  # BGRA to RGBA
            array = cv2.cvtColor(array, cv2.COLOR_BGRA2RGBA)
            return QImage(array.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
    
    raise ValueError(f"Unsupported array shape: {array.shape}")

def numpy_to_qpixmap(array: np.ndarray) -> QPixmap:
    """Convert numpy array to QPixmap"""
    qimage = numpy_to_qimage(array)
    return QPixmap.fromImage(qimage)

def qimage_to_numpy(qimage: QImage) -> np.ndarray:
    """Convert QImage to numpy array"""
    width = qimage.width()
    height = qimage.height()
    
    ptr = qimage.bits()
    if qimage.format() == QImage.Format_RGB888:
        arr = np.array(ptr).reshape(height, width, 3)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    elif qimage.format() == QImage.Format_Grayscale8:
        return np.array(ptr).reshape(height, width)
    else:
        # Convert to RGB888 first
        qimage = qimage.convertToFormat(QImage.Format_RGB888)
        ptr = qimage.bits()
        arr = np.array(ptr).reshape(height, width, 3)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def load_image(path: str) -> np.ndarray:
    """Load image from file path"""
    image = cv2.imread(path)
    if image is None:
        raise ValueError(f"Failed to load image from {path}")
    return image

def save_image(image: np.ndarray, path: str) -> bool:
    """Save image to file path"""
    try:
        cv2.imwrite(path, image)
        return True
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to save image to {path}: {e}")
        return False

def resize_keep_aspect(image: np.ndarray, max_size: tuple) -> np.ndarray:
    """Resize image while keeping aspect ratio"""
    h, w = image.shape[:2]
    max_w, max_h = max_size
    
    scale = min(max_w / w, max_h / h)
    if scale >= 1:
        return image
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

def format_time(ms: float) -> str:
    """Format time in milliseconds to readable string"""
    if ms < 1:
        return f"{ms*1000:.1f}μs"
    elif ms < 1000:
        return f"{ms:.1f}ms"
    else:
        return f"{ms/1000:.2f}s"

def format_size(bytes: int) -> str:
    """Format bytes to readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}TB"
