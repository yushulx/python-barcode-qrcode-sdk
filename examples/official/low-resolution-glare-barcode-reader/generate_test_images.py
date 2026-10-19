import json
from pathlib import Path

import cv2
import numpy as np
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "assets"
IMAGE_DIR = ASSET_DIR / "images"


GROUND_TRUTH = {
    "code128": "INV-LOWRES-00042",
    "qr": "https://example.com/warehouse/bin/A12?sku=DS-042",
}


def ensure_dirs() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for path in IMAGE_DIR.glob("*.png"):
        path.unlink()


def make_code128() -> Image.Image:
    barcode = Code128(GROUND_TRUTH["code128"], writer=ImageWriter())
    path = IMAGE_DIR / "code128_clean"
    barcode.save(
        str(path),
        {
            "module_width": 0.38,
            "module_height": 24,
            "quiet_zone": 5,
            "font_size": 12,
            "text_distance": 3,
        },
    )
    return Image.open(path.with_suffix(".png")).convert("RGB")


def make_qr() -> Image.Image:
    qr = qrcode.QRCode(
        version=3,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(GROUND_TRUTH["qr"])
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def canvas_with_label(barcode: Image.Image, label: str, size=(760, 420)) -> Image.Image:
    canvas = Image.new("RGB", size, "white")
    barcode = barcode.copy()
    max_w, max_h = size[0] - 120, size[1] - 150
    barcode.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    x = (size[0] - barcode.width) // 2
    y = 90
    canvas.paste(barcode, (x, y))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    draw.text((32, 28), label, fill=(32, 32, 32), font=font)
    draw.rectangle((24, 20, size[0] - 24, size[1] - 24), outline=(210, 210, 210), width=2)
    return canvas


def low_resolution(img: Image.Image, factor=0.24) -> Image.Image:
    small = img.resize(
        (max(1, int(img.width * factor)), max(1, int(img.height * factor))),
        Image.Resampling.BILINEAR,
    )
    return small.resize(img.size, Image.Resampling.BILINEAR)


def low_light(img: Image.Image) -> Image.Image:
    arr = np.array(img).astype(np.float32)
    arr *= np.array([0.42, 0.43, 0.46], dtype=np.float32)
    noise = np.random.default_rng(7).normal(0, 10, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr, "RGB")
    return ImageEnhance.Contrast(out).enhance(0.72)


def glare(img: Image.Image) -> Image.Image:
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    for i in range(42):
        alpha = max(0, 140 - i * 3)
        bbox = (
            int(w * 0.42) - i * 8,
            int(h * 0.22) - i * 5,
            int(w * 0.98) + i * 8,
            int(h * 0.58) + i * 5,
        )
        draw.ellipse(bbox, fill=(255, 255, 255, alpha))
    return Image.alpha_composite(base, overlay).convert("RGB")


def blurred(img: Image.Image) -> Image.Image:
    arr = np.array(img)
    kernel = np.zeros((9, 9), dtype=np.float32)
    kernel[4, :] = 1.0 / 9.0
    return Image.fromarray(cv2.filter2D(arr, -1, kernel)).filter(ImageFilter.GaussianBlur(0.4))


def inverted(img: Image.Image) -> Image.Image:
    return ImageOps.invert(img.convert("RGB"))


def save_case(base: Image.Image, barcode_type: str, variant: str, image: Image.Image, truth: dict) -> None:
    filename = f"{barcode_type}_{variant}.png"
    image.save(IMAGE_DIR / filename)
    truth[filename] = [GROUND_TRUTH[barcode_type]]


def make_cover(cases: list[tuple[str, Image.Image]]) -> Image.Image:
    thumb_w, thumb_h = 420, 260
    cover = Image.new("RGB", (900, 640), (246, 248, 251))
    draw = ImageDraw.Draw(cover)
    try:
        title_font = ImageFont.truetype("arial.ttf", 34)
        label_font = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
    draw.text((32, 28), "Low-resolution, low-light, and glare barcode tests", fill=(26, 32, 44), font=title_font)
    positions = [(32, 100), (448, 100), (32, 370), (448, 370)]
    for (label, img), (x, y) in zip(cases, positions):
        thumb = img.copy()
        thumb.thumbnail((thumb_w - 24, thumb_h - 54), Image.Resampling.LANCZOS)
        draw.rounded_rectangle((x, y, x + thumb_w, y + thumb_h), radius=12, fill="white", outline=(208, 216, 226), width=2)
        cover.paste(thumb, (x + (thumb_w - thumb.width) // 2, y + 42))
        draw.text((x + 16, y + 12), label, fill=(40, 50, 65), font=label_font)
    return cover


def main() -> None:
    ensure_dirs()
    truth = {}

    bases = {
        "code128": canvas_with_label(make_code128(), "Code 128 inventory label"),
        "qr": canvas_with_label(make_qr(), "QR code bin label"),
    }

    cover_cases = []
    for barcode_type, clean in bases.items():
        variants = {
            "clean": clean,
            "low_resolution": low_resolution(clean),
            "low_light": low_light(clean),
            "glare": glare(clean),
            "blurred": blurred(clean),
            "inverted": inverted(clean),
            "inverted_low_light": low_light(inverted(clean)),
        }
        for variant, image in variants.items():
            save_case(clean, barcode_type, variant, image, truth)
        cover_cases.extend(
            [
                (f"{barcode_type} low resolution", variants["low_resolution"]),
                (f"{barcode_type} glare", variants["glare"]),
                (f"{barcode_type} inverted", variants["inverted"]),
            ]
        )

    (ASSET_DIR / "ground_truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    cover = make_cover(cover_cases[:4])
    cover.save(ASSET_DIR / "low-resolution-glare-barcode-reader.png")
    print(f"Generated {len(truth)} test images in {IMAGE_DIR}")
    print(f"Wrote {ASSET_DIR / 'ground_truth.json'}")


if __name__ == "__main__":
    main()
