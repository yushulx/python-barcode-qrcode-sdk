"""
Configuration file for Document Detection Application
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# Model Configuration
MODELS = {
    'MobileNetV3-Large': {
        'path': BASE_DIR / "model_mbv3_iou_mix_2C049.pth",
        'backbone': 'mbv3',
        'description': 'DeepLabV3 with MobileNetV3-Large backbone'
    }
}

DEFAULT_MODEL = 'MobileNetV3-Large'

MODEL_COMMON_CONFIG = {
    'num_classes': 2,     # Background and Document
    'input_size': (384, 384),  # As used in training
}

# Image Preprocessing
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Device Configuration
DEVICE_PREFERENCE = 'cuda'  # 'cuda' or 'cpu'

# UI Configuration
WINDOW_CONFIG = {
    'title': 'Document Detection - DeepLabV3',
    'width': 1400,
    'height': 900,
    'min_width': 1000,
    'min_height': 700,
}

# Supported Image Formats
SUPPORTED_FORMATS = [
    '*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif'
]

# Visualization Colors (BGR format for OpenCV)
COLORS = {
    'document_mask': (0, 255, 0),      # Green
    'boundary': (0, 0, 255),           # Red
    'corners': (255, 0, 0),            # Blue
    'text': (255, 255, 255),           # White
}

# Performance Settings
PERFORMANCE_CONFIG = {
    'history_size': 50,  # Number of frames to keep in metrics history
    'webcam_fps': 30,
}

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)
