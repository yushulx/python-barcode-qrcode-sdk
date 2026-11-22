---
name: "Tune DBR Template"
description: "Tune Dynamsoft Barcode Reader template parameters when the default DBR preset cannot decode a hard barcode image. Use for difficult QR, DataMatrix, PDF417, 1D, blurry, low-contrast, skewed, cropped, mirrored, or repeated NO_RESULT cases."
argument-hint: "image path, current template path, expected format, constraints"
agent: "agent"
model: "GPT-5.4 (copilot)"
---

Treat this file as a thin Copilot wrapper around the canonical portable prompt.

1. Read `../../template-optimizer/PROMPT.md` first.
2. Read `../../template-optimizer/SKILL.md` and `../../template-optimizer/KNOWLEDGE.md` next.
3. Use the bundled helper tools under `../../template-optimizer/tools/` as the primary evidence path.
4. Treat root-level `validate_dbr_template.py`, `probe_dbr_templates.py`, and `compare_dbr_template_profiles.py` as compatibility wrappers only.
5. Follow the output format, stop conditions, and one-parameter-family-at-a-time rules from the canonical prompt and skill.
