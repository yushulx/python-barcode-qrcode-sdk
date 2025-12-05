import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType
from pathlib import Path
import config

def quantize_model(input_model_path, output_model_path):
    print(f"Quantizing model {input_model_path}...")
    
    try:
        quantize_dynamic(
            model_input=input_model_path,
            model_output=output_model_path,
            weight_type=QuantType.QUInt8
        )
        print(f"✅ Quantization successful! Saved to {output_model_path}")
        return True
    except Exception as e:
        print(f"❌ Quantization failed: {e}")
        return False

if __name__ == "__main__":
    input_path = config.BASE_DIR / "web_app" / "document_detector.onnx"
    output_path = config.BASE_DIR / "web_app" / "document_detector_quant.onnx"
    
    if not input_path.exists():
        print(f"Error: Input model {input_path} not found. Please run export_onnx.py first.")
    else:
        quantize_model(input_path, output_path)
