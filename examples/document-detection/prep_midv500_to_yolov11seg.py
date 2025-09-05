import os, re, json, shutil, random, math
from pathlib import Path
import yaml
import cv2
import numpy as np
from tqdm import tqdm

# --- CONFIG: set these to your MIDV-500 location and output dir ---
MIDV_ROOT = Path("midv500_data/midv500")        # folder that contains all sample sets
OUT_ROOT  = Path("./dataset")                # where the YOLOv8 dataset will be created
TRAIN_SPLIT = 0.9                            # 90% train / 10% val
CLASS_NAME = "document"                      # single class

# Heuristics to find images + annotations.
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
JSON_KEYS = ["quad", "quadrilateral", "polygon", "points"]

def find_images(root: Path):
    return [p for p in root.rglob("*") if p.suffix.lower() in IMG_EXT]

def parse_annotation(img_path: Path):
    """
    Try to find a quadrilateral for this image.
    For MIDV500 dataset structure:
      1) images are in: midv500/XX_YY_id/images/ZZ/filename.tif
      2) annotations are in: midv500/XX_YY_id/ground_truth/ZZ/filename.json
    Return: list of 4 (x,y) points in image pixel coords, or None.
    """
    # Try to find corresponding JSON annotation based on MIDV500 structure
    # img_path: .../midv500/01_alb_id/images/CA/CA01_01.tif
    # want:     .../midv500/01_alb_id/ground_truth/CA/CA01_01.json
    
    if "images" in img_path.parts:
        # Find the images folder index
        parts = list(img_path.parts)
        try:
            images_idx = parts.index("images")
            # Replace "images" with "ground_truth"
            parts[images_idx] = "ground_truth"
            # Change extension to .json
            json_path = Path(*parts).with_suffix(".json")
            
            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text())
                    # Check if it's a single document quad (like CA01_01.json)
                    if "quad" in data and isinstance(data["quad"], list) and len(data["quad"]) >= 4:
                        quad = data["quad"][:4]
                        # Ensure we have [x,y] pairs
                        result = []
                        for pt in quad:
                            if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                                result.append([float(pt[0]), float(pt[1])])
                        if len(result) == 4:
                            return result
                    
                    # Check if it's a multi-field document (like 01_alb_id.json)
                    # In this case, we want the document boundary, not individual fields
                    # For now, skip multi-field documents or implement document boundary detection
                    
                except Exception as e:
                    print(f"Error parsing {json_path}: {e}")
                    pass
        except ValueError:
            pass
    
    # Fallback: original logic for sidecar JSON next to the image
    sidecar = img_path.with_suffix(".json")
    if sidecar.exists():
        try:
            data = json.loads(sidecar.read_text())
            for k in JSON_KEYS:
                if k in data and isinstance(data[k], (list, tuple)) and len(data[k]) >= 4:
                    pts = data[k][:4]
                    # normalize possible dicts {x:...,y:...} to [x,y]
                    quad = []
                    for pt in pts:
                        if isinstance(pt, dict):
                            quad.append([float(pt["x"]), float(pt["y"])])
                        else:
                            quad.append([float(pt[0]), float(pt[1])])
                    return quad
        except Exception:
            pass

    # Case 2: ground_truth.txt in parent/grandparent
    for parent in [img_path.parent, img_path.parent.parent]:
        gt = parent / "ground_truth.txt"
        if gt.exists():
            stem = img_path.stem
            with gt.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = re.split(r"\s+", line.strip())
                    if len(parts) >= 9:
                        # first token can be filename or id
                        key = Path(parts[0]).stem
                        if key == stem:
                            try:
                                vals = list(map(float, parts[1:9]))
                                quad = [[vals[0], vals[1]],
                                        [vals[2], vals[3]],
                                        [vals[4], vals[5]],
                                        [vals[6], vals[7]]]
                                return quad
                            except Exception:
                                pass
    return None

def order_quad(quad):
    """Order points TL, TR, BR, BL."""
    pts = np.array(quad, dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    ordered = np.array([pts[np.argmin(s)],
                        pts[np.argmin(d)],
                        pts[np.argmax(s)],
                        pts[np.argmax(d)]], dtype=np.float32)
    return ordered.tolist()

def main():
    all_imgs = find_images(MIDV_ROOT)
    if not all_imgs:
        raise SystemExit(f"No images found under {MIDV_ROOT}")

    # Gather records with annotations
    records = []
    for img in tqdm(all_imgs, desc="Scanning"):
        quad = parse_annotation(img)
        if quad is None:
            continue
        # verify image size + normalize coords
        im = cv2.imread(str(img))
        if im is None:
            continue
        h, w = im.shape[:2]
        quad = order_quad(quad)
        # clip and normalize
        norm = []
        for x,y in quad:
            x = max(0, min(w-1, x)) / w
            y = max(0, min(h-1, y)) / h
            norm.append([x, y])
        records.append((img, norm, (w,h)))

    if not records:
        raise SystemExit("Found no usable annotations. Adjust parse_annotation().")

    random.shuffle(records)
    n_train = int(len(records) * TRAIN_SPLIT)
    train, val = records[:n_train], records[n_train:]

    # Create folders
    (OUT_ROOT / "images" / "train").mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "images" / "val").mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "labels" / "val").mkdir(parents=True, exist_ok=True)

    def write_example(split_dir, img_path, norm_quad):
        # Convert to JPG for better YOLO compatibility
        dst_img = OUT_ROOT / "images" / split_dir / (img_path.stem + ".jpg")
        dst_lbl = OUT_ROOT / "labels" / split_dir / (img_path.stem + ".txt")
        
        # Read and convert image to JPG if needed
        img = cv2.imread(str(img_path))
        if img is not None:
            cv2.imwrite(str(dst_img), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        else:
            # Fallback: copy original if reading fails
            shutil.copy2(img_path, dst_img)
            
        # Write label: class_id + flattened poly
        flat = " ".join(f"{x:.6f} {y:.6f}" for x,y in norm_quad)
        dst_lbl.write_text(f"0 {flat}\n")

    for img, quad, _ in tqdm(train, desc="Write train"):
        write_example("train", img, quad)
    for img, quad, _ in tqdm(val, desc="Write val"):
        write_example("val", img, quad)

    # Write dataset YAML
    data = {
        "path": str(OUT_ROOT.resolve()),  # Use absolute path for YOLO compatibility
        "train": "images/train",
        "val": "images/val",
        "names": [CLASS_NAME],
        "nc": 1,
    }
    yaml.safe_dump(data, open(OUT_ROOT / "doc.yaml", "w"))
    print(f"\nDONE. Wrote dataset at: {OUT_ROOT}\nTotal: {len(records)}, Train: {len(train)}, Val: {len(val)}")

if __name__ == "__main__":
    main()
