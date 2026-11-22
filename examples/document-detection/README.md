# YOLO Document Segmentation Training with MIDV500 Dataset

This directory contains a complete pipeline for training YOLO segmentation models for document detection using the [MIDV500 dataset](https://github.com/fcakyon/midv500/tree/master) and [ultralytics](https://pypi.org/project/ultralytics/).

https://github.com/user-attachments/assets/7b42b523-b3f2-4bae-ac9f-53e3e6d3a7c2

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare Dataset
Download MIDV500 dataset and convert to YOLO format:
```bash
python data.py
python prep_midv500_to_yolov11seg.py
```

### 3. Visualize Dataset
Verify dataset quality with the GUI viewer:
```bash
python dataset_viewer.py
```

![YOLO dataset viewer](https://www.dynamsoft.com/codepool/img/2025/09/yolo-dataset-viewer.png)

### 4. Train Model
Train YOLO11 segmentation model using the provided script:
```bash
python train_yolo_doc_detection.py
```

![YOLO segmentation training](https://www.dynamsoft.com/codepool/img/2025/09/yolo-training.png)

### 5. Run GUI Application
Launch the document detection GUI:
```bash
python document_detector_gui.py
```

![ID detection with YOLO segmentation](https://www.dynamsoft.com/codepool/img/2025/09/document-id-yolo-segmentation.png)

## GPU Setup for Faster Training

### Prerequisites

1. **NVIDIA GPU** with CUDA support (GTX 1060 or better recommended)
2. **NVIDIA drivers** installed and up-to-date
3. **CUDA toolkit** (automatically installed with PyTorch)

### Check GPU Availability

First, verify your GPU is detected:

```bash
# Check NVIDIA GPU and driver
nvidia-smi

# Check current PyTorch GPU support
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

### Install GPU-Enabled PyTorch

If CUDA is not available, install GPU-enabled PyTorch:

```bash
# Uninstall CPU-only PyTorch
pip uninstall torch torchvision torchaudio -y

# Install GPU-enabled PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

For other CUDA versions, visit: https://pytorch.org/get-started/locally/

### Verify GPU Setup

```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

### GPU Training Commands

Once GPU is enabled, use `device=0` for GPU training:

```bash
# GPU training (recommended)
yolo task=segment mode=train model=yolov8s-seg.pt data=dataset/doc.yaml imgsz=640 epochs=80 batch=16 device=0

# CPU training (fallback)
yolo task=segment mode=train model=yolov8s-seg.pt data=dataset/doc.yaml imgsz=640 epochs=80 batch=8 device=cpu
```

