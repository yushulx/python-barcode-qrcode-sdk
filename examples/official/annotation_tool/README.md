# Barcode Annotation Tool

A desktop application for annotating barcode locations in images. It automatically detects barcodes using **Dynamsoft Barcode Reader** and **ZXing-C++**, then lets you review, edit, and export the annotations.

https://github.com/user-attachments/assets/65c31b71-9573-4d0d-bdbb-2fc446db846a

## Features

- **Dual-engine detection** — Runs both Dynamsoft DBR and ZXing-C++ on every image, showing results side-by-side with differences highlighted.
- **Drag-and-drop** — Drop images or folders onto the file list or directly onto the image display area.
- **Adjustable quad overlays** — Every detected barcode quad has draggable corner handles. Drag any vertex to fine-tune the bounding polygon.
- **4-click manual annotation** — Press **D** to enter draw mode, then click four points to define a custom quad. A dialog lets you enter barcode text and format.
- **Delete / Delete All** — Remove the current image (and its annotations) or clear everything at once.
- **Structured results panel** — A tree view for each barcode showing:
  - Quad point coordinates (updated live when dragging)
  - Dynamsoft result (text, format, coordinates)
  - ZXing result (text, format, coordinates)
  - Differences between the two engines
- **JSON export** — Save all annotations to a JSON file that includes `total_images` and `total_barcodes` counts.

## Requirements

- Python 3.9+
- A valid [Dynamsoft Barcode Reader license key](https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform) 

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### DBR Template Tuning Workflow

If the default DBR preset returns `NO_RESULT` on a hard image, start with an evidence-gathering pass instead of guessing parameters or jumping straight to one special-case template:

```bash
python probe_dbr_templates.py path/to/image.png
```

The probe script tries:

- the built-in `PT_READ_BARCODES` preset
- every template inside `dbr_template.json`
- the included `dbr_incomplete_qr_template.json` example template

The `dbr_incomplete_qr_template.json` file is only an example for one hard incomplete-QR case. It is not the default answer for every difficult image. For other failures, use the same workflow to create a new focused template that matches the actual barcode type and failure mode.

If you want to test only that example template:

```bash
python probe_dbr_templates.py path/to/image.png --template-file dbr_incomplete_qr_template.json
```

If you want a broader evidence pass before changing template parameters, include common preprocessing variants and save a machine-readable report:

```bash
python probe_dbr_templates.py path/to/image.png --variant-set basic --report-json tuning-report.json
```

If you already have a known-good template from Dynamsoft, compare it with your current template before guessing:

```bash
python compare_dbr_template_profiles.py current-template.json known-good-template.json
```

If you want the smallest possible validator, run the template directly through `CaptureVisionRouter.capture()`:

```bash
python validate_dbr_template.py path/to/image.png --template-file candidate-template.json
```

Both standalone helpers, `validate_dbr_template.py` and `probe_dbr_templates.py`, initialize the DBR license before they create `CaptureVisionRouter`. If you add another DBR-only helper script, call `ensure_dbr_license()` first or treat any `NO_RESULT` as untrusted.

To use any custom template inside the GUI, click `Import DBR Template` and select the JSON file you want to test.

The included `dbr_incomplete_qr_template.json` shows what a focused template looks like for one hard single-QR image:

- narrow the task to one symbol type with `BarcodeFormatIds = ["BF_QR_CODE", "BF_MICRO_QR"]`
- narrow the scene to one barcode with `ExpectedBarcodesCount = 1`
- make localization more aggressive by combining `LM_SCAN_DIRECTLY`, `LM_CONNECTED_BLOCKS`, `LM_NEURAL_NETWORK`, `LM_STATISTICS`, and `LM_LINES`
- keep both `GTM_ORIGINAL` and `GTM_INVERTED` grayscale transforms so dark-on-light and light-on-dark candidates are both tested
- strengthen decode with multiple `DeblurModes`, including `DM_NEURAL_NETWORK` and `DM_DEEP_ANALYSIS`
- relax QR acceptance a bit with `MinQuietZoneWidth = 0` and a lower `MinResultConfidence`

After comparing against the official template, there is one important correction to that example strategy: do not assume more `DeblurModes` is the next best move. The official template leans much more on `DeformationResistingModes` such as `DRM_BROAD_WARP` and `DRM_DEWRINKLE`, uses a separate decode image-parameter block, keeps `BarcodeFormatSpecificationNameArray` unset, and sets `IfEraseTextZone` to `0`.

Another important correction is workflow-related: image observation should come first. Before AI edits a template, it should inspect the image and explicitly describe visible symptoms such as quiet-zone loss, clipping, warp, blur, low contrast, inversion, or background texture. Those observations should decide which parameter family gets changed first.

When a new image still fails, tune in this order instead of editing many sections at once:

1. Observe the image first and write down the visible symptoms.
2. Validate the current template with `python validate_dbr_template.py ...`.
Make sure the script initializes the DBR license before creating `CaptureVisionRouter`; otherwise the result is not trustworthy.
3. Restrict the scope when appropriate: one barcode, one format, long timeout.
4. Compare against any known-good template before theorizing.
5. Adjust localization next: add modes or lower `ConfidenceThreshold`.
6. Adjust decode after that: check `DeformationResistingModes`, decode-specific image parameters, grayscale/binarization, and only then add or remove `DeblurModes`.
7. Relax format rules last: quiet zone, mirror mode, partial value.

This keeps each change falsifiable, so you can tell which parameter family actually helped.

If both the raw image and the `basic` variant sweep still return `NO_RESULT`, treat that as evidence that template-only tuning is likely exhausted for the current pixels. At that point, further random parameter changes are usually lower value than preprocessing, better cropping, or a cleaner source image.

### Keyboard Shortcuts

| Key | Action |
|---|---|
| **←** / **→** | Previous / Next image |
| **D** | Toggle draw mode |
| **C** | Toggle crop mode |
| **Esc** | Exit draw / crop mode or cancel current quad |
| **Delete** | Remove current image |
| **Scroll wheel** | Zoom in / out |
| **Right-click** (draw mode) | Cancel current quad-in-progress |

### Workflow

1. **Load images** — Use *Load Files*, *Load Folder*, or drag-and-drop.
2. **Review detections** — Images are automatically sorted into *Verified*, *Needs Review*, and *No Result* lists.
3. **Fix mismatches** — Click an image in *Needs Review*, then edit text/format by clicking a polygon or drag its corner handles to correct the quad position.
4. **Handle missed barcodes** — Click an image in *No Result* to re-run detection. If it still fails, use **Crop Mode** (drag a rectangle over the barcode) or **Draw Mode** (press **D**, click four corners, fill the dialog).
5. **Verify** — Click *✔ Verify* to manually promote any image to the Verified list.
6. **Import previous work** — Click *Import JSON* to reload a prior session's annotations onto the loaded images instantly.
7. **Export / Save dataset** — Click *Export JSON* to save annotations for all images, or *Save Verified Dataset* to write only the Verified images and their annotations to a new folder.

### Export Format

```json
{
  "format": "barcode-benchmark/1.0",
  "dataset": "Annotated Collection",
  "total_images": 42,
  "total_barcodes": 87,
  "images": [
    {
      "file": "label_001.png",
      "barcodes": [
        {
          "text": "1Z999AA10123456784",
          "format": "Code128",
          "points": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        }
      ]
    }
  ]
}
```


## Annotation Viewer (`viewer.py`)

A companion read-only viewer for inspecting exported `barcode-benchmark/1.0` JSON annotation files alongside the original images.

Built with **tkinter** (Python built-in) and **Pillow** only, making it easy to distribute and run anywhere Python is installed.

```bash
pip install Pillow
```

### Usage

```bash
python viewer.py 
```

![barcode annotation viewer](https://www.dynamsoft.com/codepool/img/2026/04/barcode-annotation-viewer.png)

### Keyboard Shortcuts

| Key | Action |
|---|---|
| **←** / **→** | Previous / Next image |
| **O** | Open JSON annotation file |
| **Scroll wheel** | Zoom in / out |

### Workflow

1. **Load images** — Use *Load Images…*, *Load Folder…*, or drag-and-drop image files/folders.
2. **Load JSON** — Use *Open JSON…* or drag-and-drop a `.json` file exported by the annotation tool.
3. **Browse** — Select any image in the list. If its filename appears in the JSON, overlays and barcode details are shown automatically.

## Blog
[Build a Dual-Engine Barcode Annotation Tool in Python to Create Ground-Truth Datasets](https://www.dynamsoft.com/codepool/build-dual-engine-barcode-annotation-tool-python.html)
