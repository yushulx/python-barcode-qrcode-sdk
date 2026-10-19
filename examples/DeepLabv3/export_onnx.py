"""
Script to export PyTorch model to ONNX format for web deployment
"""
import torch
import torch.onnx
from model_loader import load_model
import config
import sys
from pathlib import Path

def export_to_onnx(model_name="MobileNetV3-Large", output_name="document_detector.onnx"):
    print(f"Loading model: {model_name}...")
    
    # Load the model
    try:
        # Force CPU for export to avoid any CUDA dependencies in the exported graph
        model, _ = load_model(model_name, device='cpu')
        model.eval()
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

    # Create dummy input
    # Shape: (Batch_Size, Channels, Height, Width)
    # We use 1 for batch size, 3 for RGB channels, and 384x384 as input size
    dummy_input = torch.randn(1, 3, 384, 384, requires_grad=True)

    output_path = config.BASE_DIR / "web_app" / output_name
    output_path.parent.mkdir(exist_ok=True)

    print(f"Exporting to {output_path}...")

    # Export
    try:
        torch.onnx.export(
            model,                      # model being run
            dummy_input,                # model input (or a tuple for multiple inputs)
            str(output_path),           # where to save the model
            export_params=True,         # store the trained parameter weights inside the model file
            opset_version=12,           # the ONNX version to export the model to
            do_constant_folding=True,   # whether to execute constant folding for optimization
            input_names=['input'],      # the model's input names
            output_names=['output'],    # the model's output names
            dynamic_axes={              # variable length axes
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        print("✅ Export successful!")
        return True
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

if __name__ == "__main__":
    success = export_to_onnx()
    sys.exit(0 if success else 1)
