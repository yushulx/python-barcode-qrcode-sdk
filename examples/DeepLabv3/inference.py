"""
Inference pipeline for document detection with performance tracking
"""
import torch
import torch.nn as nn
import numpy as np
import cv2
from typing import Tuple, Optional, Dict
import config
from utils import get_logger, PerformanceTimer
from post_processing import mask_to_boundary, overlay_mask, draw_boundary, visualize_mask

logger = get_logger(__name__)

class DocumentDetector:
    """Document detection inference pipeline"""
    
    def __init__(self, model: nn.Module, device: str):
        """
        Initialize document detector
        
        Args:
            model: Trained DeepLabV3 model
            device: Device to run inference on
        """
        self.model = model
        self.device = device
        self.input_size = config.MODEL_COMMON_CONFIG['input_size']
        self.mean = torch.tensor(config.IMAGENET_MEAN).view(3, 1, 1)
        self.std = torch.tensor(config.IMAGENET_STD).view(3, 1, 1)
        
        logger.info("DocumentDetector initialized")
    
    def preprocess(self, image: np.ndarray) -> Tuple[torch.Tensor, Tuple[int, int]]:
        """
        Preprocess image for model input
        
        Args:
            image: Input image (H, W, 3) in BGR format
        
        Returns:
            Tuple of (preprocessed tensor, original size)
        """
        original_size = (image.shape[1], image.shape[0])  # (width, height)
        
        # Resize to model input size
        resized = cv2.resize(image, self.input_size, interpolation=cv2.INTER_LINEAR)
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Convert to tensor and normalize
        tensor = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
        
        # Normalize with ImageNet stats
        tensor = (tensor - self.mean) / self.std
        
        # Add batch dimension
        tensor = tensor.unsqueeze(0).to(self.device)
        
        return tensor, original_size
    
    def postprocess(self, output: torch.Tensor) -> np.ndarray:
        """
        Postprocess model output to binary mask
        
        Args:
            output: Model output tensor (1, num_classes, H, W)
        
        Returns:
            Binary mask (H, W) with values 0 or 1
        """
        # Get class predictions
        pred = torch.argmax(output, dim=1)  # (1, H, W)
        
        # Convert to numpy
        mask = pred.squeeze(0).cpu().numpy().astype(np.uint8)
        
        return mask
    
    @torch.no_grad()
    def detect(self, image: np.ndarray) -> Dict:
        """
        Detect document in image with performance metrics
        
        Args:
            image: Input image (H, W, 3) in BGR format
        
        Returns:
            Dictionary containing:
                - mask: Binary segmentation mask
                - corners: Document corner points (4, 2) or None
                - visualization: Image with overlay
                - metrics: Performance metrics
        """
        metrics = {}
        
        # Preprocessing
        with PerformanceTimer() as timer:
            input_tensor, original_size = self.preprocess(image)
        metrics['preprocess_ms'] = timer.elapsed_ms
        
        # Inference
        with PerformanceTimer() as timer:
            output = self.model(input_tensor)['out']
        metrics['inference_ms'] = timer.elapsed_ms
        
        # Postprocessing
        with PerformanceTimer() as timer:
            mask = self.postprocess(output)
            corners, contours = mask_to_boundary(mask, original_size)
        metrics['postprocess_ms'] = timer.elapsed_ms
        
        # Total time
        metrics['total_ms'] = (
            metrics['preprocess_ms'] + 
            metrics['inference_ms'] + 
            metrics['postprocess_ms']
        )
        
        # Create visualizations
        mask_colored = visualize_mask(mask)
        mask_resized = cv2.resize(mask_colored, original_size, 
                                  interpolation=cv2.INTER_NEAREST)
        
        # Overlay mask on original image
        overlay = overlay_mask(image, mask_resized, alpha=0.4)
        
        # Draw boundary if corners detected
        if corners is not None:
            overlay = draw_boundary(overlay, corners, color=config.COLORS['boundary'])
        
        return {
            'mask': mask,
            'mask_colored': mask_resized,
            'corners': corners,
            'contours': contours,
            'overlay': overlay,
            'metrics': metrics,
        }
    
    def detect_batch(self, images: list) -> list:
        """
        Detect documents in multiple images
        
        Args:
            images: List of input images
        
        Returns:
            List of detection results
        """
        results = []
        for image in images:
            result = self.detect(image)
            results.append(result)
        return results
