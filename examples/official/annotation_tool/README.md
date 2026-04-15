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
