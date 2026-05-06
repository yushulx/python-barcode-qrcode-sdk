# Template Optimizer Prompt

Use this prompt when you have the standalone `template-optimizer/` folder and do not want to rely on `.github/skills` or `.github/prompts`.

## Copyable Prompt

Read `template-optimizer/SKILL.md` and `template-optimizer/KNOWLEDGE.md` first. Follow the Python-only template-optimizer workflow and use the bundled helper scripts under `template-optimizer/tools/` for single-image triage before broad benchmarking.

Task: tune this barcode image.

- Image path: `<image-path>`
- Current template path: `<template-path-or-none>`
- Format hint: `<format-or-none>`
- Proven template path: `<template-path-or-none>`
- Preprocessing allowed: `<yes-or-no>`

Constraints:

- Inspect the image before editing JSON.
- Change one parameter family at a time.
- Use the cheapest trustworthy evidence first.
- If raw plus basic variants all fail, say template-only tuning is likely exhausted.

Use these bundled commands when needed:

- `python template-optimizer/tools/validate_dbr_template.py <image> --template-file <template>`
- `python template-optimizer/tools/probe_dbr_templates.py <image>`
- `python template-optimizer/tools/probe_dbr_templates.py <image> --variant-set basic --report-json tuning-report.json`
- `python template-optimizer/tools/compare_dbr_template_profiles.py <current-template> <proven-template>`

Expected output:

- Visual diagnosis
- Diagnosis
- Example-template relevance
- Exact JSON change
- Validation command
- Next fallback step if it still fails

## Other Prompt Variants

Dataset optimization:

`Read template-optimizer/SKILL.md and template-optimizer/KNOWLEDGE.md. Use the template-optimizer workflow to optimize all images in <image-dir> with ground truth <ground-truth-json-or-none>. Save the best template and generate an HTML report.`

Education:

`Read template-optimizer/SKILL.md and template-optimizer/KNOWLEDGE.md. Explain which DBR parameter families matter most for <problem-type> and include practical tuning advice.`

Report generation:

`Read template-optimizer/SKILL.md. Generate an HTML report from <results-json>, baseline <baseline-json-or-none>, and image directory <image-dir>.`