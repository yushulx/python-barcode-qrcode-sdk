# Barcode SDK Benchmark Framework
Comprehensive benchmarking framework to compare barcode reader SDKs: **ZXing-cpp**, **ZBar**, and [Dynamsoft Barcode Reader](https://pypi.org/project/dynamsoft-barcode-reader-bundle/).

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

    Both datasets are hosted in the [Dynamsoft datasets repository](https://github.com/Dynamsoft/datasets-from-dynamsoft/tree/main/zxing-zbar).

    - **Existing Dataset**: 170 real-world barcode images sourced from [Open Food Facts](https://github.com/openfoodfacts/openfoodfacts-ai/issues/15). Clone [Dynamsoft/datasets-from-dynamsoft](https://github.com/Dynamsoft/datasets-from-dynamsoft) and make its `zxing-zbar/existing_dataset` folder available here as `existing_dataset/` (a symlink or junction is fine; copying also works).

    - **Generated Dataset**: A pre-generated snapshot (442 images with 400 JSON annotations, including `skewed_datamatrix`) is available at `zxing-zbar/generated_dataset` in the same repository. It can also be regenerated locally by running `advanced.py`.

    For example, on Windows:

    ```powershell
    git clone https://github.com/Dynamsoft/datasets-from-dynamsoft.git D:\datasets-from-dynamsoft
    New-Item -ItemType Junction -Path existing_dataset -Target D:\datasets-from-dynamsoft\zxing-zbar\existing_dataset
    New-Item -ItemType Junction -Path generated_dataset -Target D:\datasets-from-dynamsoft\zxing-zbar\generated_dataset
    ```

    On Linux/macOS, use `ln -s` instead of `New-Item -ItemType Junction`.

## Usage

This project provides two benchmark programs:
- **simple.py** - Quick benchmark using existing dataset (real-world barcode images)
- **advanced.py** - Comprehensive benchmark with dataset selection and detailed analysis

### Option 1: Simple Benchmark (simple.py)

1. Obtain a [30-day trial license](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) and update the code with the license key in `simple.py`.
    
    ```python
    from dynamsoft_barcode_reader_bundle import *
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

**Note**: Dynamsoft Barcode Reader requires a valid license key. Visit [Dynamsoft's website](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) to obtain one.

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
├── existing_dataset/           # Real-world images (linked from datasets-from-dynamsoft)
├── generated_dataset/          # Test cases (linked or created by advanced.py)
│   ├── single_barcode/
│   ├── angled_barcodes/
│   ├── multiple_barcodes/
│   ├── challenging_conditions/
│   └── skewed_datamatrix/
├── results/                    # Benchmark results and reports
├── src/                        # Benchmark framework modules
└── config/                     # Configuration files
```

## Supported Barcode Types

**1D Barcodes**: CODE_128, CODE_39, EAN_13, EAN_8, UPC_A, UPC_E, ITF, CODABAR

**2D Barcodes**: QR_CODE, DATA_MATRIX, PDF_417, AZTEC (support varies by SDK)


## Blog
[Comparing Barcode Scanning in Python: ZXing vs. ZBar vs. Dynamsoft Barcode Reader](https://www.dynamsoft.com/codepool/python-zxing-zbar-barcode.html)
