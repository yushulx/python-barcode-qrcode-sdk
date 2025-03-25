# backend.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dynamsoft_capture_vision_bundle import *
import io
import os

app = FastAPI()

# Initialize Dynamsoft components
license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
error_code, error_message = LicenseManager.init_license(license_key)
cvr_instance = CaptureVisionRouter()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def upload_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Barcode Scanner</title>
        <style>
            .container { max-width: 600px; margin: 2rem auto; padding: 2rem; }
            .preview { max-width: 300px; margin: 1rem 0; }
            .progress { display: none; color: blue; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Upload Barcode Image</h1>
            <input type="file" id="fileInput" accept="image/*" capture="camera">
            <img class="preview" id="preview">
            <div class="progress" id="progress">Processing...</div>
            <div id="result"></div>

            <script>
                const fileInput = document.getElementById('fileInput');
                const preview = document.getElementById('preview');
                const progress = document.getElementById('progress');
                const resultDiv = document.getElementById('result');

                fileInput.addEventListener('change', async (e) => {
                    const file = e.target.files[0];
                    if (!file) return;

                    // Display preview
                    preview.src = URL.createObjectURL(file);
                    preview.style.display = 'block';
                    
                    // Show progress
                    progress.style.display = 'block';
                    
                    const formData = new FormData();
                    formData.append('file', file);

                    try {
                        const response = await fetch('/scan', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        if (data.success) {
                            let resultHTML = `
                                <h3>Found ${data.count} barcode(s)</h3>
                                <div class="results-container">
                            `;
                            
                            data.items.forEach((item, index) => {
                                resultHTML += `
                                    <div class="barcode-result">
                                        <h4>Barcode #${index + 1}</h4>
                                        <p><strong>Type:</strong> ${item.format}</p>
                                        <p><strong>Content:</strong> ${item.text}</p>
                                        <div class="location">
                                            <span>Coordinates:</span>
                                            <ul>
                                                <li>Point 1: (${item.location.x1}, ${item.location.y1})</li>
                                                <li>Point 2: (${item.location.x2}, ${item.location.y2})</li>
                                                <li>Point 3: (${item.location.x3}, ${item.location.y3})</li>
                                                <li>Point 4: (${item.location.x4}, ${item.location.y4})</li>
                                            </ul>
                                        </div>
                                    </div>
                                `;
                            });
                            
                            resultHTML += `</div>`;
                            resultDiv.innerHTML = resultHTML;
                        } else {
                            resultDiv.innerHTML = `Error: ${data.error}`;
                        }
                    } catch (err) {
                        resultDiv.innerHTML = 'Request failed';
                    } finally {
                        progress.style.display = 'none';
                    }
                });
            </script>
        </div>
    </body>
    </html>
    """

@app.post("/scan")
async def scan_barcode(file: UploadFile = File(...)):
    try:
        # Read image file
        image_data = await file.read()

        # # Decode barcodes
        result = cvr_instance.capture(image_data, EnumPresetTemplate.PT_READ_BARCODES.value)
        
        if result.get_error_code() != EnumErrorCode.EC_OK:
            return JSONResponse(
                {"success": False, "error": "No barcode detected"},
                status_code=400
            )

        # Get and return results 
        items = result.get_items()
        return_items = []
        for item in items:
            format_type = item.get_format()
            text = item.get_text()

            location = item.get_location()
            x1 = location.points[0].x
            y1 = location.points[0].y
            x2 = location.points[1].x
            y2 = location.points[1].y
            x3 = location.points[2].x
            y3 = location.points[2].y
            x4 = location.points[3].x
            y4 = location.points[3].y
            del location

            return_items.append({
                "format": format_type,
                "text": text,
                "location": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "x3": x3,
                    "y3": y3,
                    "x4": x4,
                    "y4": y4
                }
            })

        return {
            "success": True,
            "count": len(items),
            "items": return_items
        }
        
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)