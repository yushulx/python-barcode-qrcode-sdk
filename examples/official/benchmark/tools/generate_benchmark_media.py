import argparse
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1920
HEIGHT = 1080
NAVY = (8, 24, 48)
BLUE = (30, 105, 224)
TEAL = (0, 170, 148)
WHITE = (246, 249, 255)
MUTED = (174, 194, 220)

DISPLAY_NAMES = {
    "dynamsoft-dbr-python": "Dynamsoft Barcode Reader",
    "zxing-python": "ZXing-C++ Python",
}


def font(size, bold=False):
    names = ["seguisb.ttf" if bold else "segoeui.ttf", "arialbd.ttf" if bold else "arial.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def fit_text(draw, text, box_width, start_size, bold=False):
    size = start_size
    while size > 28:
        selected = font(size, bold)
        if draw.textbbox((0, 0), text, font=selected)[2] <= box_width:
            return selected
        size -= 2
    return font(size, bold)


def base_slide():
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)
    for x in range(WIDTH):
        ratio = x / WIDTH
        color = tuple(int(NAVY[i] * (1 - ratio) + (15, 55, 97)[i] * ratio) for i in range(3))
        draw.line((x, 0, x, HEIGHT), fill=color)
    draw.rounded_rectangle((105, 85, 385, 137), 24, fill=TEAL)
    draw.text((135, 94), "FULL BENCHMARK", font=font(25, True), fill=NAVY)
    draw.rectangle((105, 928, 1815, 932), fill=BLUE)
    draw.text((105, 962), "Dynamsoft Codepool", font=font(28, True), fill=MUTED)
    return image, draw


def title_slide(title, subtitle, details=None):
    image, draw = base_slide()
    title_font = fit_text(draw, title, 1710, 78, True)
    draw.text((105, 238), title, font=title_font, fill=WHITE)
    draw.text((108, 355), subtitle, font=font(39), fill=MUTED)
    if details:
        y = 520
        for label, value in details:
            draw.rounded_rectangle((105, y, 560, y + 160), 18, fill=(17, 49, 86), outline=(45, 99, 158), width=2)
            draw.text((137, y + 24), value, font=font(52, True), fill=WHITE)
            draw.text((137, y + 94), label, font=font(25), fill=MUTED)
            y += 190
    return image


def benchmark_cover_slide(summary, images, ground_truth):
    image, draw = base_slide()
    title = "ZXing Python vs. Dynamsoft Barcode Reader"
    draw.text((105, 205), title, font=fit_text(draw, title, 1710, 70, True), fill=WHITE)
    draw.text((108, 302), "BarBeR full dataset benchmark in Python", font=font(34), fill=MUTED)
    decoders = sorted(summary["decoders"].items(), key=lambda item: item[0] != "dynamsoft-dbr-python")
    colors = [TEAL, BLUE]
    for index, (name, metrics) in enumerate(decoders):
        x = 105 + index * 855
        draw.rounded_rectangle((x, 390, x + 750, 800), 22, fill=(17, 49, 86), outline=colors[index], width=4)
        draw.text((x + 42, 430), DISPLAY_NAMES.get(name, name), font=fit_text(draw, DISPLAY_NAMES.get(name, name), 660, 37, True), fill=WHITE)
        values = [
            ("Recall", f'{metrics["coverage_adjusted_recall"] * 100:.2f}%'),
            ("Precision", f'{metrics["precision"] * 100:.2f}%'),
            ("Mean", f'{metrics["mean_decode_ms"]:.2f} ms'),
        ]
        y = 525
        for label, value in values:
            draw.text((x + 42, y), label, font=font(30), fill=MUTED)
            draw.text((x + 310, y - 12), value, font=font(44, True), fill=WHITE)
            y += 86
    draw.text((105, 842), f"{images:,} images | {ground_truth:,} ground truth barcodes | one measured run", font=font(30), fill=MUTED)
    return image


def comparison_slide(summary, images, repetitions):
    image, draw = base_slide()
    draw.text((105, 205), "Measured Results", font=font(72, True), fill=WHITE)
    decoders = sorted(summary["decoders"].items(), key=lambda item: item[0] != "dynamsoft-dbr-python")
    colors = [BLUE, TEAL]
    for index, (name, metrics) in enumerate(decoders):
        x = 105 + index * 855
        draw.rounded_rectangle((x, 345, x + 750, 825), 22, fill=(17, 49, 86), outline=colors[index], width=4)
        draw.text((x + 42, 385), DISPLAY_NAMES.get(name, name), font=font(38, True), fill=WHITE)
        values = [
            ("Recall", f'{metrics["coverage_adjusted_recall"] * 100:.2f}%'),
            ("Precision", f'{metrics["precision"] * 100:.2f}%'),
            ("Mean decode", f'{metrics["mean_decode_ms"]:.2f} ms'),
        ]
        y = 490
        for label, value in values:
            draw.text((x + 42, y), label, font=font(27), fill=MUTED)
            draw.text((x + 310, y - 8), value, font=font(38, True), fill=WHITE)
            y += 94
    draw.text((105, 865), f"{images:,} images across {repetitions} measured run(s)", font=font(29), fill=MUTED)
    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    stats = inventory["summary"]
    images = stats["manifest_images"]
    ground_truth = stats["benchmark_annotations"]
    decoder_records = [value["records"] for value in summary["decoders"].values()]
    if len(decoder_records) != 2 or any(value % images for value in decoder_records):
        raise SystemExit("summary does not contain complete full-dataset decoder records")
    repetitions = decoder_records[0] // images
    if repetitions < 1 or any(value != images * repetitions for value in decoder_records):
        raise SystemExit("summary record counts do not match the audited image count")

    args.output.mkdir(parents=True, exist_ok=True)
    frames = args.output / "video_frames"
    frames.mkdir(exist_ok=True)
    slides = [
        benchmark_cover_slide(summary, images, ground_truth),
        title_slide(
            "One Dataset and One Input Pipeline",
            "The same OpenCV image is passed to both Python barcode readers",
            [("MEASURED RUNS", str(repetitions)), ("DECODER RECORDS", f"{sum(decoder_records):,}")],
        ),
        comparison_slide(summary, images, repetitions),
        title_slide(
            "Auditable from Images to Results",
            "Source hashes, manifest hashes, raw records, configurations, and timing are preserved",
        ),
    ]
    for index, slide in enumerate(slides):
        slide.save(frames / f"frame-{index:02}.png")

    cover = slides[0].resize((1200, 675)).crop((0, 22, 1200, 652))
    cover.save(args.output / "barcode-benchmark-python-cover.png")
    shutil.copy2(frames / "frame-00.png", args.output / "barcode-benchmark-python-video-poster.png")

    concat = frames / "concat.txt"
    lines = []
    for index in range(len(slides)):
        lines.append(f"file 'frame-{index:02}.png'\n")
        lines.append("duration 2.3\n")
    lines.append(f"file 'frame-{len(slides) - 1:02}.png'\n")
    concat.write_text("".join(lines), encoding="utf-8")
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-f", "concat", "-safe", "0", "-i", str(concat),
            "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-movflags", "+faststart", str(args.output / "barcode-benchmark-python-video.mp4"),
        ],
        check=True,
    )
    shutil.rmtree(frames)
    print(args.output)


if __name__ == "__main__":
    main()
