# Image Symptom Guide

## Goal

Force AI to look at the barcode image first and translate visible symptoms into the next DBR parameter family to test.

## Observation Checklist

Describe only what is visible in the image before touching the template:

- Is the quiet zone missing or very thin?
- Is any edge of the symbol clipped by the image boundary?
- Is the symbol warped, stretched, or wrinkled?
- Is the image blurry or just low contrast?
- Are the finder patterns intact or partially damaged?
- Is the code dark-on-light, light-on-dark, or ambiguous?
- Is there heavy background texture or nearby text?
- Is the symbol front-facing or perspective-skewed?

## Symptom To Parameter Family

### Missing quiet zone or edge clipping

- Check `MinQuietZoneWidth`
- Test padded image variants
- Avoid changing many decode modes first

### Warped, folded, or wrinkled symbol

- Prioritize `DeformationResistingModes`
- Compare against any proven template using `DRM_BROAD_WARP` or `DRM_DEWRINKLE`
- Do not assume extra `DeblurModes` is the answer

### Low contrast but still sharp

- Focus on grayscale enhancement and binarization behavior
- Check separate decode `ImageParameterOptions`

### Blur without obvious geometric damage

- Focus on `DeblurModes` and decode image scaling
- Keep localization stable if the symbol is already likely found

### Background texture or nearby text

- Check texture removal and `IfEraseTextZone`
- Verify that text-zone removal is not erasing damaged QR structure

### Inverted or ambiguous foreground/background

- Check grayscale transforms and inverted variants

## Required AI Behavior

Before proposing template edits, AI should explicitly state:

1. What it sees in the image
2. Which parameter family those symptoms point to
3. Why it is not changing unrelated parameter families first
