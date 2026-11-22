#!/usr/bin/env python3
"""
Utility functions for IP Camera GUI Client
Contains helper functions for image conversion and barcode scanning.
"""

import cv2
import numpy as np
from dynamsoft_capture_vision_bundle import ImageData, EnumImagePixelFormat


def convertMat2ImageData(mat):
    """
    Convert OpenCV Mat to Dynamsoft ImageData format
    
    Args:
        mat: OpenCV Mat (BGR or grayscale format)
        
    Returns:
        ImageData: Dynamsoft ImageData object
    """
    if len(mat.shape) == 3:
        height, width, channels = mat.shape
        pixel_format = EnumImagePixelFormat.IPF_RGB_888
    else:
        height, width = mat.shape
        channels = 1
        pixel_format = EnumImagePixelFormat.IPF_GRAYSCALED

    stride = width * channels
    imagedata = ImageData(mat.tobytes(), width, height, stride, pixel_format)
    return imagedata


def draw_barcode_results(frame, items):
    """
    Draw barcode detection results on the frame
    
    Args:
        frame: OpenCV frame (BGR format)
        items: List of barcode detection results
        
    Returns:
        tuple: (modified_frame, detected_texts)
    """
    detected_texts = []
    
    for item in items:
        if hasattr(item, 'get_type') and item.get_type().name == 'CRIT_BARCODE':
            text = item.get_text()
            location = item.get_location()
            
            # Get corner points
            points = []
            for i in range(4):
                x = int(location.points[i].x)
                y = int(location.points[i].y)
                points.append([x, y])
            
            # Draw bounding box
            cv2.drawContours(frame, [np.array(points, dtype=np.int32)], 0, (0, 255, 0), 2)
            
            # Draw text
            if points:
                x, y = points[0]
                cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            detected_texts.append(text)
            
            # Clean up location object
            del location
    
    return frame, detected_texts