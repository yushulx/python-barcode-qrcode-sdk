"""
Post-processing utilities for document boundary extraction
"""
import cv2
import numpy as np
from typing import Optional, Tuple, List
import config
from utils import get_logger

logger = get_logger(__name__)

def get_boundary_validation_metrics(
    image: np.ndarray,
    corners: np.ndarray
) -> Tuple[float, float, float]:
    """Measure how much image evidence supports a predicted boundary."""
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    gray_float = gray.astype(np.float32)
    grad_x = cv2.Sobel(gray_float, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_float, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = cv2.magnitude(grad_x, grad_y)

    band_width = max(
        config.POSTPROCESSING_CONFIG['min_boundary_band_width'],
        int(round(min(gray.shape[:2]) * config.POSTPROCESSING_CONFIG['boundary_band_width_ratio']))
    )

    band_mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.polylines(band_mask, [corners.astype(np.int32)], True, 255, band_width)

    boundary_values = grad_mag[band_mask > 0]
    if boundary_values.size == 0:
        return 0.0, 0.0, 0.0

    contrast_band_width = max(
        config.POSTPROCESSING_CONFIG['min_contrast_band_width'],
        int(round(min(gray.shape[:2]) * config.POSTPROCESSING_CONFIG['contrast_band_width_ratio']))
    )
    if contrast_band_width % 2 == 0:
        contrast_band_width += 1

    fill_mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.fillPoly(fill_mask, [corners.astype(np.int32)], 255)
    kernel = np.ones((contrast_band_width, contrast_band_width), dtype=np.uint8)
    dilated_mask = cv2.dilate(fill_mask, kernel, iterations=1)
    outer_band = cv2.subtract(dilated_mask, fill_mask) > 0
    inner_region = fill_mask > 0

    inside_outside_contrast = 0.0
    if np.any(inner_region) and np.any(outer_band):
        inside_outside_contrast = abs(
            float(gray[inner_region].mean()) - float(gray[outer_band].mean())
        )

    return (
        float(np.mean(boundary_values)),
        float(np.percentile(boundary_values, 90)),
        inside_outside_contrast,
    )

def has_boundary_evidence(
    image: np.ndarray,
    corners: Optional[np.ndarray],
    model_boundary_margin: Optional[float] = None
) -> bool:
    """
    Validate that a predicted boundary aligns with image gradients.

    Blank or nearly uniform images can still produce a plausible-looking mask.
    Reject those cases unless the candidate quad has enough edge energy nearby.
    """
    if corners is None:
        return False

    if model_boundary_margin is not None:
        if model_boundary_margin < config.POSTPROCESSING_CONFIG['min_model_boundary_margin']:
            logger.info(
                "Rejecting boundary with insufficient model boundary margin: %.3f < %.3f",
                model_boundary_margin,
                config.POSTPROCESSING_CONFIG['min_model_boundary_margin']
            )
            return False

    boundary_gradient_mean, boundary_gradient_p90, inside_outside_contrast = (
        get_boundary_validation_metrics(image, corners)
    )

    if boundary_gradient_mean < config.POSTPROCESSING_CONFIG['min_boundary_gradient_mean']:
        logger.info(
            "Rejecting boundary with insufficient gradient evidence: %.3f < %.3f",
            boundary_gradient_mean,
            config.POSTPROCESSING_CONFIG['min_boundary_gradient_mean']
        )
        return False

    if boundary_gradient_p90 < config.POSTPROCESSING_CONFIG['min_boundary_gradient_p90']:
        logger.info(
            "Rejecting boundary with weak high-percentile edge support: %.3f < %.3f",
            boundary_gradient_p90,
            config.POSTPROCESSING_CONFIG['min_boundary_gradient_p90']
        )
        return False

    if inside_outside_contrast < config.POSTPROCESSING_CONFIG['min_boundary_inside_outside_contrast']:
        logger.info(
            "Rejecting boundary with insufficient inside/outside contrast: %.3f < %.3f",
            inside_outside_contrast,
            config.POSTPROCESSING_CONFIG['min_boundary_inside_outside_contrast']
        )
        return False

    return True

def mask_to_boundary(
    mask: np.ndarray,
    original_size: Tuple[int, int],
    image: Optional[np.ndarray] = None,
    model_boundary_margin: Optional[float] = None
) -> Tuple[Optional[np.ndarray], Optional[List[np.ndarray]]]:
    """
    Extract document boundary from segmentation mask
    
    Args:
        mask: Binary segmentation mask (H, W)
        original_size: Original image size (width, height)
        image: Original input image used to validate the predicted boundary
        model_boundary_margin: Mean absolute softmax margin along the mask boundary
    
    Returns:
        Tuple of (corners, contours) where corners is (4, 2) array of corner points
    """
    # Ensure mask is binary
    if mask.dtype != np.uint8:
        mask = (mask * 255).astype(np.uint8)
    
    # Resize mask to original size
    mask_resized = cv2.resize(mask, original_size, interpolation=cv2.INTER_NEAREST)
    
    # Find contours
    contours, _ = cv2.findContours(
        mask_resized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    if len(contours) == 0:
        logger.warning("No contours found in mask")
        return None, None
    
    # Get the largest contour (assumed to be the document)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Approximate contour to polygon
    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    # Try to get 4 corners
    corners = None
    if len(approx) == 4:
        corners = approx.reshape(4, 2)
    else:
        # If not exactly 4 points, use minimum area rectangle
        rect = cv2.minAreaRect(largest_contour)
        corners = cv2.boxPoints(rect).astype(np.int32)
    
    # Order corners: top-left, top-right, bottom-right, bottom-left
    corners = order_points(corners)

    if image is not None and not has_boundary_evidence(
        image,
        corners,
        model_boundary_margin=model_boundary_margin
    ):
        return None, contours
    
    return corners, contours

def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order points in clockwise order starting from top-left
    
    Args:
        pts: Array of 4 points (4, 2)
    
    Returns:
        Ordered points (4, 2)
    """
    # Initialize ordered points
    rect = np.zeros((4, 2), dtype=np.float32)
    
    # Sum and difference to find corners
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    
    rect[0] = pts[np.argmin(s)]      # Top-left (smallest sum)
    rect[2] = pts[np.argmax(s)]      # Bottom-right (largest sum)
    rect[1] = pts[np.argmin(diff)]   # Top-right (smallest difference)
    rect[3] = pts[np.argmax(diff)]   # Bottom-left (largest difference)
    
    return rect

def draw_boundary(
    image: np.ndarray,
    corners: Optional[np.ndarray],
    color: Tuple[int, int, int] = (0, 0, 255),
    thickness: int = 3
) -> np.ndarray:
    """
    Draw document boundary on image
    
    Args:
        image: Input image
        corners: Corner points (4, 2)
        color: Line color in BGR
        thickness: Line thickness
    
    Returns:
        Image with boundary drawn
    """
    result = image.copy()
    
    if corners is None:
        return result
    
    # Draw boundary lines
    corners_int = corners.astype(np.int32)
    cv2.polylines(result, [corners_int], True, color, thickness)
    
    # Draw corner points
    for i, corner in enumerate(corners_int):
        cv2.circle(result, tuple(corner), 8, (255, 0, 0), -1)
        cv2.putText(
            result, str(i+1), tuple(corner + 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
        )
    
    return result

def overlay_mask(
    image: np.ndarray,
    mask: np.ndarray,
    alpha: float = 0.5,
    color: Tuple[int, int, int] = (0, 255, 0)
) -> np.ndarray:
    """
    Overlay segmentation mask on image
    
    Args:
        image: Original image
        mask: Binary mask
        alpha: Transparency factor
        color: Mask color in BGR
    
    Returns:
        Image with mask overlay
    """
    # Ensure mask is same size as image
    if mask.shape[:2] != image.shape[:2]:
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]), 
                         interpolation=cv2.INTER_NEAREST)
    
    # Create colored mask
    colored_mask = np.zeros_like(image)
    if len(mask.shape) == 2:
        mask_bool = mask > 0
    else:
        mask_bool = mask[:, :, 0] > 0
    
    colored_mask[mask_bool] = color
    
    # Blend with original image
    result = cv2.addWeighted(image, 1, colored_mask, alpha, 0)
    
    return result

def crop_document(
    image: np.ndarray,
    corners: np.ndarray,
    output_size: Tuple[int, int] = (800, 1000)
) -> np.ndarray:
    """
    Crop and perspective transform document
    
    Args:
        image: Original image
        corners: Corner points (4, 2) in order: TL, TR, BR, BL
        output_size: Output image size (width, height)
    
    Returns:
        Cropped and transformed document
    """
    # Define destination points
    dst_points = np.array([
        [0, 0],
        [output_size[0] - 1, 0],
        [output_size[0] - 1, output_size[1] - 1],
        [0, output_size[1] - 1]
    ], dtype=np.float32)
    
    # Calculate perspective transform matrix
    matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst_points)
    
    # Apply perspective transform
    warped = cv2.warpPerspective(image, matrix, output_size)
    
    return warped

def visualize_mask(mask: np.ndarray) -> np.ndarray:
    """
    Convert binary mask to colored visualization
    
    Args:
        mask: Binary mask (H, W) with values 0 or 1
    
    Returns:
        Colored mask (H, W, 3)
    """
    # Create colored version
    colored = np.zeros((*mask.shape, 3), dtype=np.uint8)
    colored[mask > 0] = [0, 255, 0]  # Green for document
    
    return colored
