# Barcode SDK Benchmark Framework
Comprehensive benchmarking framework to compare barcode reader SDKs: **ZXing-cpp**, **ZBar**, and [Dynamsoft Capture Vision SDK](https://pypi.org/search/?q=dynamsoft-capture-vision-bundle).

This project focuses on **angled barcode detection** and **multiple barcode scenarios**, designed to identify and showcase competitive advantages in barcode recognition performance.

![Python barcode SDK benchmark](https://www.dynamsoft.com/codepool/img/2025/11/success_rate_comparison.png)

## Key Features

- **Multiple SDK Support**: ZXing-Cpp, PyZBar (open-source), Dynamsoft (commercial)
- **Dual Benchmark Modes**: 
  - Simple benchmark with real-world dataset (170 images)
  - Advanced benchmark with generated test scenarios
- **Specialized Testing**: Angled barcodes (15°-75°), multiple barcodes (2-20 per image)
- **Core Metrics**: Detection time (ms) and success rate (%)
- **Professional Reports**: HTML reports with interactive charts and strategic insights
- **Extensible Framework**: Easy to add new SDKs and test scenarios

## Prerequisites
- Install required packages:

    ```bash
    pip install -r requirements.txt
    ```

- Dataset
    
    - **Existing Dataset**: The dataset is sourced from this [GitHub issue](https://github.com/openfoodfacts/openfoodfacts-ai/issues/15). You can download it directly from: https://drive.google.com/uc?id=1uThXXH8HiHAw6KlpdgcimBSbrvi0Mksf&export=download. We have cleaned the images to ensure each image file name matches the barcode content. Extract the images to the `existing_dataset/` folder.
    
    - **Generated Dataset**: The benchmark framework can automatically generate test datasets with various conditions (angles, multiple barcodes, etc.). These are stored in the `generated_dataset/` folder and created by running `advanced.py`.

## Usage

This project provides two benchmark programs:
- **simple.py** - Quick benchmark using existing dataset (real-world barcode images)
- **advanced.py** - Comprehensive benchmark with dataset selection and detailed analysis

### Option 1: Simple Benchmark (simple.py)

1. Obtain a [30-day trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) and update the code with the license key in `simple.py`.
    
    ```python
    from dynamsoft_capture_vision_bundle import *
    error_code, error_message = LicenseManager.init_license(
        "LICENSE-KEY")
    ```

2. Run the Python script:

    ```bash
    # Test with a single image
    python simple.py -i <image_file>
    
    # Run benchmark on existing dataset (default: existing_dataset/)
    python simple.py -d existing_dataset
    ```
    
    **ZXing**
    
    ![python zxing barcode detection](https://www.dynamsoft.com/codepool/img/2024/08/python-zxing-barcode-detection.png)

    **ZBar**

    ![python zxing barcode detection](https://www.dynamsoft.com/codepool/img/2024/08/python-zbar-barcode-detection.png)

    **Dynamsoft Barcode Reader**
    
    ![python zxing barcode detection](https://www.dynamsoft.com/codepool/img/2024/08/python-dbr-barcode-detection.png)

### Option 2: Advanced Benchmark (advanced.py)

Run the comprehensive benchmark with interactive dataset selection:

```bash
python advanced.py
```

This will:
1. **Select dataset**: Choose between generated dataset, existing dataset, or both
2. **Generate test data** (if using generated dataset and not already created)
3. **Run benchmark tests** with enabled SDKs
4. **Analyze results** and generate reports in `results/`

The program will automatically detect which datasets are available and allow you to:
- Use **generated dataset** for controlled testing (angled barcodes, multiple barcodes, etc.)
- Use **existing dataset** for real-world barcode testing (170 images)
- Use **both datasets** for comprehensive benchmarking

## 🔧 Configuration

Edit `config/benchmark_config.json` to enable/disable SDKs and configure settings:

```json
{
  "libraries": {
    "zxing_cpp": {
      "enabled": true
    },
    "pyzbar": {
      "enabled": true
    },
    "dynamsoft": {
      "enabled": false,
      "license": "YOUR_LICENSE_KEY_HERE"
    }
  },
  "test_data": {
    "num_samples": 50
  }
}
```

**Note**: Dynamsoft requires a valid license key. Visit [Dynamsoft's website](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) to obtain one.

## Test Scenarios

### 1. Single Barcodes (Baseline)
- Barcode types: CODE128, CODE39, EAN13, EAN8, ITF, QR_CODE
- Clean images for establishing performance baselines
- Measures basic detection capabilities

### 2. Angled Barcodes (Key Focus)
- Rotation angles: 15°, 30°, 45°, 60°, 75°
- Tests SDK ability to handle rotated/tilted barcodes
- **Critical for real-world mobile scanning** where camera angle varies
- Identifies competitive advantage in flexible positioning

### 3. Multiple Barcodes (Key Focus)
- Barcode counts: 2, 5, 10, 15, 20 per image
- Tests batch processing and scalability
- **Important for inventory, logistics, and warehouse applications**
- Demonstrates efficiency in high-density scanning scenarios

### 4. Challenging Conditions
- Combined tests with noise, blur, occlusion, and perspective distortion
- Validates robustness under real-world degraded conditions

### 5. Existing Dataset (Real-world Testing)
- 170 real-world barcode images from production environments
- Various barcode types including EAN, UPC, CODE128, CODE39
- Tests practical performance with authentic scanning conditions

## Project Structure

```
├── simple.py                   # Simple benchmark using existing dataset
├── advanced.py                 # Advanced benchmark with dataset selection
├── existing_dataset/           # Real-world barcode images (download separately)
├── generated_dataset/          # Auto-generated test cases (created by advanced.py)
│   ├── single_barcode/
│   ├── angled_barcodes/
│   ├── multiple_barcodes/
│   └── challenging_conditions/
├── results/                    # Benchmark results and reports
├── src/                        # Benchmark framework modules
└── config/                     # Configuration files
```

## Supported Barcode Types

**1D Barcodes**: CODE_128, CODE_39, EAN_13, EAN_8, UPC_A, UPC_E, ITF, CODABAR

**2D Barcodes**: QR_CODE, DATA_MATRIX, PDF_417, AZTEC (support varies by SDK)


## Blog
[Comparing Barcode Scanning in Python: ZXing vs. ZBar vs. Dynamsoft Barcode Reader](https://www.dynamsoft.com/codepool/python-zxing-zbar-barcode.html)
