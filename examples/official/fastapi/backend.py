from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from dynamsoft_capture_vision_bundle import *
import os

app = FastAPI()

# License setup
license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
LicenseManager.init_license(license_key)
cvr_instance = CaptureVisionRouter()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and template folders
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def upload_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scan")
async def scan_barcode(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        result = cvr_instance.capture(image_data, EnumPresetTemplate.PT_READ_BARCODES.value)

        if result.get_error_code() != EnumErrorCode.EC_OK:
            return JSONResponse({"success": False, "error": "No barcode detected"}, status_code=400)

        items = result.get_items()
        return_items = []
        for item in items:
            location = item.get_location()
            return_items.append({
                "format": item.get_format(),
                "text": item.get_text(),
                "location": {
                    "x1": location.points[0].x, "y1": location.points[0].y,
                    "x2": location.points[1].x, "y2": location.points[1].y,
                    "x3": location.points[2].x, "y3": location.points[2].y,
                    "x4": location.points[3].x, "y4": location.points[3].y,
                }
            })

        return {"success": True, "count": len(items), "items": return_items}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)