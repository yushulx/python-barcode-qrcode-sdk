import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare the main tuning-relevant parameter families of two DBR templates."
    )
    parser.add_argument("template_a", help="Path to the first template JSON file")
    parser.add_argument("template_b", help="Path to the second template JSON file")
    return parser.parse_args()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def get_first_barcode_reader(template):
    readers = template.get("BarcodeReaderTaskSettingOptions") or []
    return readers[0] if readers else {}


def get_sections(reader):
    return {section.get("Section"): section for section in reader.get("SectionArray") or []}


def get_stage(section, stage_name):
    for stage in section.get("StageArray") or []:
        if stage.get("Stage") == stage_name:
            return stage
    return {}


def get_image_parameter(template, name):
    for item in template.get("ImageParameterOptions") or []:
        if item.get("Name") == name:
            return item
    return {}


def get_applicable_stage(image_param, stage_name):
    for stage in image_param.get("ApplicableStages") or []:
        if stage.get("Stage") == stage_name:
            return stage
    return {}


def list_modes(items):
    if items is None:
        return None
    return [item.get("Mode") for item in items if isinstance(item, dict) and item.get("Mode")]


def summarize_template(template):
    reader = get_first_barcode_reader(template)
    sections = get_sections(reader)

    localization_section = sections.get("ST_BARCODE_LOCALIZATION", {})
    decode_section = sections.get("ST_BARCODE_DECODING", {})

    localization_stage = get_stage(localization_section, "SST_LOCALIZE_CANDIDATE_BARCODES")
    deformation_stage = get_stage(decode_section, "SST_RESIST_DEFORMATION")
    deblur_stage = get_stage(decode_section, "SST_DECODE_BARCODES")

    localize_param_name = localization_section.get("ImageParameterName")
    decode_param_name = decode_section.get("ImageParameterName")
    localize_param = get_image_parameter(template, localize_param_name)
    decode_param = get_image_parameter(template, decode_param_name)

    return {
        "capture_templates": [item.get("Name") for item in template.get("CaptureVisionTemplates") or []],
        "barcode_formats": reader.get("BarcodeFormatIds"),
        "barcode_format_spec_names": reader.get("BarcodeFormatSpecificationNameArray"),
        "expected_barcodes": reader.get("ExpectedBarcodesCount"),
        "localization_modes": list_modes(localization_stage.get("LocalizationModes")),
        "deformation_modes": list_modes(deformation_stage.get("DeformationResistingModes")),
        "deblur_modes": list_modes(deblur_stage.get("DeblurModes")),
        "localize_image_param": localize_param_name,
        "decode_image_param": decode_param_name,
        "localize_gray_transforms": list_modes(
            get_applicable_stage(localize_param, "SST_TRANSFORM_GRAYSCALE").get("GrayscaleTransformationModes")
        ),
        "decode_gray_transforms": list_modes(
            get_applicable_stage(decode_param, "SST_TRANSFORM_GRAYSCALE").get("GrayscaleTransformationModes")
        ),
        "localize_gray_enhance": list_modes(
            get_applicable_stage(localize_param, "SST_ENHANCE_GRAYSCALE").get("GrayscaleEnhancementModes")
        ),
        "decode_gray_enhance": list_modes(
            get_applicable_stage(decode_param, "SST_ENHANCE_GRAYSCALE").get("GrayscaleEnhancementModes")
        ),
        "localize_binarize": list_modes(
            get_applicable_stage(localize_param, "SST_BINARIZE_IMAGE").get("BinarizationModes")
        ),
        "decode_binarize": list_modes(
            get_applicable_stage(decode_param, "SST_BINARIZE_IMAGE").get("BinarizationModes")
        ),
        "localize_texture_removed_binarize": list_modes(
            get_applicable_stage(localize_param, "SST_BINARIZE_TEXTURE_REMOVED_GRAYSCALE").get("BinarizationModes")
        ),
        "decode_texture_removed_binarize": list_modes(
            get_applicable_stage(decode_param, "SST_BINARIZE_TEXTURE_REMOVED_GRAYSCALE").get("BinarizationModes")
        ),
        "localize_erase_text_zone": get_applicable_stage(localize_param, "SST_REMOVE_TEXT_ZONES_FROM_BINARY").get("IfEraseTextZone"),
        "decode_erase_text_zone": get_applicable_stage(decode_param, "SST_REMOVE_TEXT_ZONES_FROM_BINARY").get("IfEraseTextZone"),
        "decode_scale_edge_threshold": get_applicable_stage(decode_param, "SST_SCALE_IMAGE").get("ImageScaleSetting", {}).get("EdgeLengthThreshold"),
    }


def main():
    args = parse_args()
    first = summarize_template(load_json(args.template_a))
    second = summarize_template(load_json(args.template_b))

    print(f"=== {Path(args.template_a).name} ===")
    print(json.dumps(first, indent=2))
    print(f"=== {Path(args.template_b).name} ===")
    print(json.dumps(second, indent=2))

    print("=== differences ===")
    all_keys = sorted(set(first) | set(second))
    for key in all_keys:
        if first.get(key) != second.get(key):
            print(f"- {key}")
            print(f"  A: {first.get(key)}")
            print(f"  B: {second.get(key)}")


if __name__ == "__main__":
    main()