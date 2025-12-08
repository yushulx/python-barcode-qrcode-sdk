"""
Convert PyTorch DeepLabV3 model (.pth) to TensorFlow.js format.

This script converts the model through the following pipeline:
PyTorch (.pth) -> ONNX -> TensorFlow SavedModel -> TensorFlow.js

Requirements:
    pip install torch torchvision onnx onnx2tf tensorflowjs tensorflow

Usage:
    python convert_pth_to_tfjs.py
"""

import os
import sys
import shutil
import subprocess

# === Windows Fix for TensorFlow.js ===
# tensorflowjs tries to import tensorflow_decision_forests which is not available on Windows.
# We mock it before importing tensorflowjs to prevent the crash.
try:
    import tensorflow_decision_forests
except ImportError:
    class MockTFDF:
        pass
    sys.modules['tensorflow_decision_forests'] = MockTFDF()
# =====================================

def check_dependencies():
    """Check if required packages are installed."""
    required = ['torch', 'torchvision', 'onnx', 'onnx2tf', 'tensorflowjs', 'tensorflow']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    return True


def export_to_onnx(pth_path, onnx_path, input_size=384):
    """Export PyTorch model to ONNX format."""
    import torch
    from torchvision.models.segmentation import deeplabv3_mobilenet_v3_large
    
    print(f"Loading PyTorch model from {pth_path}...")
    
    # Create model architecture
    model = deeplabv3_mobilenet_v3_large(num_classes=2)
    
    # Load weights
    state_dict = torch.load(pth_path, map_location='cpu')
    # Use strict=False to ignore auxiliary classifier weights if present (we only need inference)
    model.load_state_dict(state_dict, strict=False)
    model.eval()
    
    # Create dummy input
    dummy_input = torch.randn(1, 3, input_size, input_size)
    
    print(f"Exporting to ONNX: {onnx_path}...")
    
    # Export to ONNX
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes=None,  # Fixed shape for better compatibility
        opset_version=12,
        do_constant_folding=True
    )
    
    print("ONNX export complete!")
    return True


def convert_onnx_to_tf(onnx_path, tf_output_dir, input_size=384):
    """Convert ONNX model to TensorFlow SavedModel using onnx2tf."""
    print(f"Converting ONNX to TensorFlow SavedModel...")
    
    cmd = [
        'onnx2tf',
        '-i', onnx_path,
        '-o', tf_output_dir,
        '-ois', f'input:1,3,{input_size},{input_size}'  # Fix input shape
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    print("TensorFlow SavedModel conversion complete!")
    return True


def convert_tf_to_tfjs(tf_saved_model_dir, tfjs_output_dir):
    """Convert TensorFlow SavedModel to TensorFlow.js format."""
    import tensorflow as tf
    
    print(f"Converting TensorFlow SavedModel to TensorFlow.js...")
    
    # First, we need to add a signature to the SavedModel
    # This is required for tensorflowjs conversion
    
    print("Loading SavedModel and adding signature...")
    
    # Load the model
    loaded = tf.saved_model.load(tf_saved_model_dir)
    
    # Get the concrete function
    if hasattr(loaded, 'signatures') and 'serving_default' in loaded.signatures:
        print("SavedModel already has serving_default signature")
    else:
        # Need to wrap and re-save with signature
        print("Adding serving_default signature...")
        
        # Find the inference function
        infer = None
        if hasattr(loaded, '__call__'):
            infer = loaded.__call__
        elif hasattr(loaded, 'serve'):
            infer = loaded.serve
        
        if infer is None:
            # Try to get from signatures
            for key in dir(loaded):
                attr = getattr(loaded, key)
                if callable(attr) and not key.startswith('_'):
                    infer = attr
                    break
        
        if infer is None:
            print("Could not find inference function, trying direct conversion...")
        else:
            # Create a wrapper module
            class WrapperModule(tf.Module):
                def __init__(self, model):
                    super().__init__()
                    self.model = model
                
                @tf.function(input_signature=[tf.TensorSpec(shape=[1, 384, 384, 3], dtype=tf.float32)])
                def serving_default(self, x):
                    return self.model(x)
            
            wrapper = WrapperModule(loaded)
            
            # Re-save with signature
            wrapped_dir = tf_saved_model_dir + '_wrapped'
            tf.saved_model.save(
                wrapper,
                wrapped_dir,
                signatures={'serving_default': wrapper.serving_default}
            )
            tf_saved_model_dir = wrapped_dir
    
    # Now convert to TensorFlow.js
    print("Running tensorflowjs converter...")
    
    import tensorflowjs as tfjs
    
    try:
        # Try with signature_def (common in newer versions)
        tfjs.converters.convert_tf_saved_model(
            tf_saved_model_dir,
            tfjs_output_dir,
            signature_def='serving_default'
        )
        print(f"TensorFlow.js model saved to: {tfjs_output_dir}")
        return True
    except TypeError:
        try:
            # Try without signature arg (defaults to serving_default)
            tfjs.converters.convert_tf_saved_model(
                tf_saved_model_dir,
                tfjs_output_dir
            )
            print(f"TensorFlow.js model saved to: {tfjs_output_dir}")
            return True
        except Exception as e:
            print(f"Second attempt failed: {e}")
            raise e
    except Exception as e:
        print(f"Conversion error: {e}")
        
        # Try alternative method using command line
        print("Trying command line converter...")
        cmd = [
            sys.executable, '-m', 'tensorflowjs.converters.converter',
            '--input_format=tf_saved_model',
            '--output_format=tfjs_graph_model',
            '--signature_name=serving_default',
            tf_saved_model_dir,
            tfjs_output_dir
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"TensorFlow.js model saved to: {tfjs_output_dir}")
            return True
        else:
            print(f"Command line conversion failed: {result.stderr}")
            return False


def main():
    # Configuration
    PTH_PATH = 'model_mbv3_iou_mix_2C049.pth'
    ONNX_PATH = 'temp_model.onnx'
    TF_SAVED_MODEL_DIR = 'tf_saved_model'
    TFJS_OUTPUT_DIR = 'web_app_tfjs/tfjs_model'
    INPUT_SIZE = 384
    
    print("=" * 50)
    print("PyTorch to TensorFlow.js Converter")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Force cleanup of previous run artifacts to ensure fresh conversion
    if os.path.exists(ONNX_PATH):
        os.remove(ONNX_PATH)
    if os.path.exists(TF_SAVED_MODEL_DIR):
        shutil.rmtree(TF_SAVED_MODEL_DIR)
    if os.path.exists(TF_SAVED_MODEL_DIR + '_wrapped'):
        shutil.rmtree(TF_SAVED_MODEL_DIR + '_wrapped')
    
    # Step 1: PyTorch -> ONNX
    if not os.path.exists(ONNX_PATH):
        if not export_to_onnx(PTH_PATH, ONNX_PATH, INPUT_SIZE):
            print("Failed to export ONNX model")
            sys.exit(1)
    else:
        print(f"ONNX model already exists: {ONNX_PATH}")
    
    # Step 2: ONNX -> TensorFlow SavedModel
    if not os.path.exists(TF_SAVED_MODEL_DIR):
        if not convert_onnx_to_tf(ONNX_PATH, TF_SAVED_MODEL_DIR, INPUT_SIZE):
            print("Failed to convert to TensorFlow")
            sys.exit(1)
    else:
        print(f"TensorFlow SavedModel already exists: {TF_SAVED_MODEL_DIR}")
    
    # Step 3: TensorFlow SavedModel -> TensorFlow.js
    os.makedirs(TFJS_OUTPUT_DIR, exist_ok=True)
    if not convert_tf_to_tfjs(TF_SAVED_MODEL_DIR, TFJS_OUTPUT_DIR):
        print("Failed to convert to TensorFlow.js")
        sys.exit(1)
    
    # Cleanup temporary files
    if os.path.exists(ONNX_PATH):
        os.remove(ONNX_PATH)
        print(f"Cleaned up: {ONNX_PATH}")
    
    print("=" * 50)
    print("Conversion complete!")
    print(f"TensorFlow.js model: {TFJS_OUTPUT_DIR}/model.json")
    print("=" * 50)


if __name__ == '__main__':
    main()
