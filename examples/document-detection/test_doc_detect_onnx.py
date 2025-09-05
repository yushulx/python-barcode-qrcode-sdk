#!/usr/bin/env python3
"""
ONNX-only YOLOv8/YOLO11 (seg) inference for document detection
- Requires: pip install ultralytics onnxruntime opencv-python numpy
- Uses res.masks.xy (original-image coordinates) to build a quad and warp.
"""

import os, sys, warnings
import numpy as np
import cv2

# ── Force CPU and quiet logs BEFORE importing runtime/ultralytics ──────────────
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"     # don't let PyTorch probe CUDA
os.environ["ORT_LOGGING_LEVEL"] = "4"         # onnxruntime: errors only
warnings.filterwarnings("ignore")

try:
    import onnxruntime as ort
    ort.set_default_logger_severity(4)
except ImportError:
    print("❌ onnxruntime not installed. Run: pip install onnxruntime")
    sys.exit(1)

from ultralytics import YOLO

# ── Config ─────────────────────────────────────────────────────────────────────
MODEL_ONNX = "runs/segment/train/weights/best.onnx"  # your exported ONNX
IMAGE_PATH = "CA01_01.jpg"                            # test image
IMG_SIZE   = 640
CONF       = 0.25

# ── Helpers ────────────────────────────────────────────────────────────────────
def order_pts(pts: np.ndarray) -> np.ndarray:
    """Order 4 points TL, TR, BR, BL."""
    s = pts.sum(1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)],
                     pts[np.argmin(d)],
                     pts[np.argmax(s)],
                     pts[np.argmax(d)]], dtype=np.float32)

def polygon_to_quad(poly_xy: np.ndarray) -> np.ndarray:
    """
    poly_xy: (K,2) float32 in original image coordinates.
    Returns ordered 4x2 quad (float32). Uses approxPolyDP, with minAreaRect fallback.
    """
    cnt = poly_xy.reshape(-1, 1, 2).astype(np.float32)
    peri = cv2.arcLength(cnt, True)

    # try several epsilons, coarse → fine
    for eps in (0.03, 0.025, 0.02, 0.015, 0.01):
        approx = cv2.approxPolyDP(cnt, eps * peri, True)
        if len(approx) == 4:
            return order_pts(approx.reshape(-1, 2).astype(np.float32))

    # fallback: min area rectangle
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect).astype(np.float32)  # (4,2)
    return order_pts(box)

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(MODEL_ONNX):
        print(f"❌ ONNX model not found: {MODEL_ONNX}")
        sys.exit(1)
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image not found: {IMAGE_PATH}")
        sys.exit(1)

    print("Providers (onnxruntime):", ort.get_available_providers())
    print(f"Loading ONNX model: {MODEL_ONNX}")
    model = YOLO(MODEL_ONNX)       # Ultralytics will use onnxruntime backend
    print("✅ ONNX model loaded")

    img = cv2.imread(IMAGE_PATH)
    if img is None:
        print(f"❌ Failed to read image: {IMAGE_PATH}")
        sys.exit(1)
    H, W = img.shape[:2]
    print(f"Image size: {W}x{H}")

    # device='cpu' to avoid any CUDA probing in Ultralytics
    res = model(img, imgsz=IMG_SIZE, conf=CONF, device='cpu')[0]
    print("✅ Inference completed")

    if res.masks is None or len(res.masks.data) == 0:
        print("⚠️  No document detected.")
        return

    # Pick the largest polygon in ORIGINAL coordinates
    polys = res.masks.xy  # list of N (K,2) arrays in original image coords
    areas = [cv2.contourArea(p.astype(np.float32)) for p in polys]
    idx = int(np.argmax(areas))
    poly = polys[idx].astype(np.float32)

    # Build a 4-point quad and warp
    quad = polygon_to_quad(poly)
    w_out = int(max(np.linalg.norm(quad[1]-quad[0]), np.linalg.norm(quad[2]-quad[3])))
    h_out = int(max(np.linalg.norm(quad[2]-quad[1]), np.linalg.norm(quad[3]-quad[0])))
    dst = np.array([[0, 0],
                    [w_out - 1, 0],
                    [w_out - 1, h_out - 1],
                    [0, h_out - 1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(quad, dst)
    warped = cv2.warpPerspective(img, M, (w_out, h_out))

    # Draw overlays
    overlay = img.copy()
    cv2.polylines(overlay, [quad.astype(int)], True, (0, 255, 0), 3)

    # Save results
    cv2.imwrite("detect_overlay.jpg", overlay)
    cv2.imwrite("document_warped.jpg", warped)

    # Print coordinates for debugging
    print("Quad (TL, TR, BR, BL):")
    for i, (x, y) in enumerate(quad):
        print(f"  P{i}: ({x:.1f}, {y:.1f})")
    print("Saved: detect_overlay.jpg, document_warped.jpg")

if __name__ == "__main__":
    main()
