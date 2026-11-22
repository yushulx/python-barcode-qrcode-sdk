# Barcode Benchmark App

A PySide6 desktop application for benchmarking barcode-reading SDKs against annotated image datasets.

## Features

- **Drag & drop** images or folders onto the image viewer, or use the **Browse Files** button
- **Load annotation JSON** (`barcode-benchmark/1.0` format) to enable ground-truth accuracy measurement
- **Load a custom Dynamsoft template** (optional JSON) to override the default capture settings
- **Select SDKs** — Dynamsoft Barcode Reader and/or ZXing-C++
- **Live progress** and per-file results table updated in real time during the benchmark
- **Image viewer with annotation overlay** — after the benchmark, browse images with:
  - **Green polygons** = ground-truth barcode locations (from annotation JSON)
  - **Colored rectangles** = barcode locations detected by each SDK (one color per library)
  - Barcode text labels drawn next to each box
- **Export HTML report** — self-contained file matching the web-app report layout, with aggregate summary and per-image detail tables

## Folder Structure

```
benchmark_app/
├── gui_benchmark.py            # Main application entry point
├── requirements.txt            # Python dependencies
├── config/
│   └── benchmark_config.json  # SDK configuration (licenses, enabled flags)
├── src/
│   ├── barcode_readers.py      # DynamsoftBarcodeReader, ZXingCppReader
│   └── benchmark_framework.py # BarcodeReaderInterface, BenchmarkResult, TestCase
└── README.md
```

## Requirements

See [`requirements.txt`](requirements.txt).

Install:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python benchmark_app/gui_benchmark.py
```

### Workflow

1. **Add images** — drag & drop images / folders onto the viewer, or click **Browse Files**.  
   Supports: JPG, PNG, BMP, TIFF, WebP.
2. **Load Annotation JSON** *(optional)* — click the toolbar button to load a `barcode-benchmark/1.0` file exported from the annotation tool. The status badge shows `✓ N images, N barcodes`.
3. **Load DBR Template** *(optional)* — load a custom Dynamsoft template JSON to override capture settings.
4. **Select SDKs** — check one or more of: Dynamsoft, ZXing Cpp.
5. **Run Benchmark** — the progress bar tracks each file; the Detailed Results table fills in real time.
6. **Review results in the image viewer**:
   - Use **Prev / Next** or click any row in the Detailed Results table.
   - **Green polygons** show expected barcode positions from the annotation.
   - **Colored boxes** show what each SDK detected; each library uses a distinct color.
   - The text strip below the image lists detected values and GT match status.
7. **Export HTML Report** — saves a self-contained HTML file with the same layout as the web-app benchmark report.

## Annotation JSON Format

The annotation JSON must follow the `barcode-benchmark/1.0` schema produced by the annotation tool:

```json
{
  "format": "barcode-benchmark/1.0",
  "total_images": 5,
  "total_barcodes": 12,
  "images": [
    {
      "file": "IMG_001.jpg",
      "barcodes": [
        {
          "text": "1234567890",
          "format": "Code128",
          "points": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        }
      ]
    }
  ]
}
```

`text` is used for accuracy matching; `points` are used to draw the ground-truth overlay polygon on the image.

## Configuration

Edit `config/benchmark_config.json` to set SDK license keys and enable/disable libraries:

```json
{
  "libraries": {
    "dynamsoft": { "enabled": true, "license": "YOUR_LICENSE_KEY" },
    "zxing_cpp": { "enabled": true, "options": {} }
  }
}
```

You can also update the Dynamsoft license through the **SDK Settings** dialog inside the app.

