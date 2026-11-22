"""
generate_retail_images.py
--------------------------
Synthesizes a realistic retail-checkout image set used to test the barcode
decoding pipeline. It produces:

  images/products/*.png    - one product "package" per item, each barcode
                             rendered on a colored card with a shadow, slight
                             rotation, and a textured surface (shelf/photo look)
  images/checkout-belt.png - a composite "self-checkout camera" frame: several
                             product packages scattered on a conveyor-belt
                             background, the way an overhead camera would see them

Symbologies reflect what real point-of-sale systems encounter:
  - EAN-13 / UPC-A : primary global retail product codes
  - EAN-8          : small-package products
  - Code 128       : internal logistics / shipping labels
  - GS1-128        : GS1 application-identifier data (batch / weight)
  - QR Code        : loyalty / digital coupon

Run:  python generate_retail_images.py
"""

import os
import random

import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(7)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
PRODUCTS_DIR = os.path.join(OUT_DIR, "products")

# (filename, product label, symbology, value, card color)
CATALOG = [
    ("cereal_box", "Morning Oat Cereal 500g", "ean13", "4006381333931", (255, 214, 102)),
    ("soda_can", "Cola Classic 330ml", "upca", "036000291452", (214, 69, 65)),
    ("gum_pack", "Mint Gum", "ean8", "96385074", (120, 200, 160)),
    ("milk_carton", "Whole Milk 1L", "ean13", "5012345678900", (235, 238, 245)),
    ("shipping_label", "Backroom Carton", "code128", "SKU-7741-CASE24", (206, 178, 140)),
    ("weighed_produce", "Bananas (GS1-128)", "gs1_128", "0109501101530003", (245, 224, 120)),
]

LOYALTY_QR = ("loyalty_coupon", "10% Loyalty Coupon", "QR",
              "https://retail.example.com/coupon/Q7F3K9", (180, 205, 245))


def _font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_linear_barcode(symbology, value):
    """Return a PIL image of a 1D barcode."""
    writer = ImageWriter()
    code_cls = barcode.get_barcode_class(symbology)
    obj = code_cls(value, writer=writer)
    options = {"module_height": 14.0, "font_size": 8, "text_distance": 3.0, "quiet_zone": 3.0}
    path = obj.save(os.path.join(PRODUCTS_DIR, "_tmp_" + symbology), options=options)
    img = Image.open(path).convert("RGB")
    os.remove(path)
    return img


def render_qr(value):
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(value)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _add_noise(img, amount=8):
    """Overlay subtle photographic noise so the surface isn't flat."""
    noise = Image.effect_noise(img.size, amount).convert("L")
    return Image.blend(img, Image.merge("RGB", (noise, noise, noise)), 0.06)


def product_package(label, barcode_img, card_color, width=380):
    """
    Compose a product 'package': a colored card with a header band, the product
    name, and a white barcode panel - i.e. what a real product face looks like.
    """
    pad = 16
    title_font = _font(17)
    bw, bh = barcode_img.size
    panel_w = width - 2 * pad
    scale = panel_w / bw
    barcode_img = barcode_img.resize((int(bw * scale), int(bh * scale)))
    bw, bh = barcode_img.size

    header_h = 46
    panel_pad = 12
    height = header_h + panel_pad + bh + 2 * panel_pad

    card = Image.new("RGB", (width, height), card_color)
    draw = ImageDraw.Draw(card)

    # Header band (slightly darker shade of the card color).
    dark = tuple(max(0, int(c * 0.72)) for c in card_color)
    draw.rectangle([0, 0, width, header_h], fill=dark)
    text_color = (255, 255, 255) if sum(dark) < 380 else (30, 30, 30)
    draw.text((pad, header_h // 2 - 9), label, fill=text_color, font=title_font)

    # White barcode panel.
    panel = [pad, header_h + panel_pad, width - pad, header_h + panel_pad + bh + panel_pad]
    draw.rectangle(panel, fill="white", outline=(200, 200, 200))
    card.paste(barcode_img, ((width - bw) // 2, header_h + panel_pad + panel_pad // 2))

    card = _add_noise(card)
    # Border for definition.
    ImageDraw.Draw(card).rectangle([0, 0, width - 1, height - 1], outline=dark)
    return card


def with_shadow_and_rotation(card, angle):
    """Drop a soft shadow behind the card and rotate it slightly."""
    margin = 40
    base = Image.new("RGBA", (card.width + margin * 2, card.height + margin * 2), (0, 0, 0, 0))

    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rectangle([margin + 8, margin + 10, margin + card.width + 8, margin + card.height + 10],
                    fill=(0, 0, 0, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))

    base.alpha_composite(shadow)
    base.alpha_composite(card.convert("RGBA"), (margin, margin))
    return base.rotate(angle, expand=True, resample=Image.BICUBIC)


def conveyor_background(size):
    """A gray conveyor-belt background with horizontal slat lines and vignette."""
    w, h = size
    bg = Image.new("RGB", size, (150, 154, 160))
    draw = ImageDraw.Draw(bg)
    # Belt slats.
    slat = 46
    for y in range(0, h, slat):
        shade = 138 if (y // slat) % 2 == 0 else 162
        draw.rectangle([0, y, w, y + slat - 6], fill=(shade, shade + 4, shade + 8))
        draw.line([0, y, w, y], fill=(110, 112, 118), width=2)
    bg = _add_noise(bg, amount=14)

    # Vignette.
    vignette = Image.new("L", size, 0)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse([-w * 0.2, -h * 0.2, w * 1.2, h * 1.2], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGB", size, (40, 42, 46))
    return Image.composite(bg, dark, vignette)


def save_studio(card, fname):
    """Place a single package on a soft studio background and save it."""
    studio = Image.new("RGB", (card.width + 80, card.height + 80), (236, 238, 242))
    rotated = with_shadow_and_rotation(card, random.uniform(-6, 6))
    studio.paste(rotated, ((studio.width - rotated.width) // 2,
                           (studio.height - rotated.height) // 2), rotated)
    studio.save(os.path.join(PRODUCTS_DIR, fname + ".png"))


def main():
    os.makedirs(PRODUCTS_DIR, exist_ok=True)

    packages = []
    for fname, label, symbology, value, color in CATALOG:
        barcode_img = render_linear_barcode(symbology, value)
        card = product_package(label, barcode_img, color)
        save_studio(card, fname)
        packages.append(card)
        print("Generated", fname + ".png", "(" + symbology + ":" + value + ")")

    # Loyalty QR coupon.
    qr_card = product_package(LOYALTY_QR[1], render_qr(LOYALTY_QR[3]), LOYALTY_QR[4], width=240)
    save_studio(qr_card, LOYALTY_QR[0])
    packages.append(qr_card)
    print("Generated", LOYALTY_QR[0] + ".png", "(QR)")

    # Composite "self-checkout camera" frame: packages scattered on the belt.
    belt_w, belt_h = 1280, 860
    belt = conveyor_background((belt_w, belt_h))

    cols, rows = 3, 3
    cell_w, cell_h = belt_w // cols, belt_h // rows
    slots = [(c, r) for r in range(rows) for c in range(cols)]
    random.shuffle(slots)

    for pkg, (c, r) in zip(packages, slots):
        scale = random.uniform(0.74, 0.92)
        scaled = pkg.resize((int(pkg.width * scale), int(pkg.height * scale)))
        placed = with_shadow_and_rotation(scaled, random.uniform(-18, 18))
        cx = c * cell_w + cell_w // 2
        cy = r * cell_h + cell_h // 2
        jx = random.randint(-20, 20)
        jy = random.randint(-20, 20)
        x = cx - placed.width // 2 + jx
        y = cy - placed.height // 2 + jy
        belt.paste(placed, (x, y), placed)

    belt_path = os.path.join(OUT_DIR, "checkout-belt.png")
    belt.save(belt_path)
    print("Generated", belt_path)


if __name__ == "__main__":
    main()
