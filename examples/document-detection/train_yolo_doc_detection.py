#!/usr/bin/env python3
"""
Train YOLO11 Segmentation Model for Document Detection

This script trains a YOLO11 segmentation model using the prepared MIDV500 dataset.
"""

import subprocess
import sys
import os
import yaml
import tempfile
from pathlib import Path

def create_dynamic_config():
    """Create a temporary YAML config with dynamic absolute path."""
    dataset_dir = Path(__file__).parent / "dataset"
    dataset_dir = dataset_dir.resolve()  # Get absolute path
    
    config = {
        'names': ['document'],
        'nc': 1,
        'path': str(dataset_dir),
        'train': 'images/train',
        'val': 'images/val'
    }
    
    # Create temporary YAML file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    yaml.dump(config, temp_file, default_flow_style=False)
    temp_file.close()
    
    print(f"Created temporary config: {temp_file.name}")
    print(f"Dataset path: {dataset_dir}")
    
    return temp_file.name

def cleanup_temp_file(temp_path):
    """Clean up temporary file."""
    try:
        os.unlink(temp_path)
        print(f"Cleaned up temporary config: {temp_path}")
    except:
        pass

def run_command(cmd, description):
    """Run a command and print its output."""
    print(f"\n=== {description} ===")
    print(f"Running: {cmd}")
    
    try:
        # For Windows compatibility, don't capture output to avoid Unicode issues
        # Let YOLO print directly to console
        result = subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False

def main():
    # Check if dataset exists
    if not Path("dataset/images/train").exists() or not Path("dataset/images/val").exists():
        print("Error: dataset/images/train or dataset/images/val not found.")
        print("Please run prep_midv500_to_yolov11seg.py first.")
        sys.exit(1)
    
    # Create dynamic config
    temp_config = create_dynamic_config()
    
    try:
        # Download specific YOLO11 model 
        download_cmd = "yolo task=segment model=yolo11s-seg.pt"
        print("Ensuring YOLO11s-seg model is available...")
        subprocess.run(download_cmd, shell=True, check=False, capture_output=True)
        
        # Training command using temporary config
        train_cmd = (
            f"yolo task=segment mode=train model=yolo11s-seg.pt data={temp_config} "
            "imgsz=640 epochs=20 batch=16 device=0 patience=5"
        )
        
        print("Starting YOLO11 Segmentation Training for Document Detection")
        print("Dataset: MIDV500 (converted)")
        print("Model: YOLO11s-seg")
        print("Image size: 640")
        print("Epochs: 20")
        print("Batch size: 16")
        print("Device: GPU 0")
        print("Early stopping patience: 5 epochs")
        
        if run_command(train_cmd, "Training YOLO11 Segmentation Model"):
            print("\n=== Training completed successfully! ===")
            
            # Find the best model
            runs_dir = Path("runs/segment")
            if runs_dir.exists():
                train_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("train")]
                if train_dirs:
                    latest_train = max(train_dirs, key=lambda x: x.stat().st_mtime)
                    best_model = latest_train / "weights" / "best.pt"
                    
                    if best_model.exists():
                        print(f"\nBest model saved at: {best_model}")
                        
                        # Export to ONNX
                        export_cmd = f"yolo export model={best_model} format=onnx opset=12"
                        
                        if run_command(export_cmd, "Exporting model to ONNX"):
                            onnx_model = best_model.with_suffix(".onnx")
                            print(f"\nONNX model exported to: {onnx_model}")
                            print("\n=== Training and Export Complete! ===")
                            print(f"PyTorch model: {best_model}")
                            print(f"ONNX model: {onnx_model}")
                        else:
                            print("ONNX export failed, but training completed.")
                    else:
                        print("Warning: best.pt not found in expected location.")
        else:
            print("Training failed. Please check the error messages above.")
            sys.exit(1)
    
    finally:
        # Clean up temporary config file
        cleanup_temp_file(temp_config)

if __name__ == "__main__":
    main()
