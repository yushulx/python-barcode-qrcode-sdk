---
name: template-optimizer
description: 'Python-only DBR template optimizer for single-image triage, batch optimization, parameter education, and HTML reporting.'
argument-hint: 'image path or image directory, current template path if any, known format if any'
user-invocable: true
---

# Template Optimizer

The canonical workflow lives in `template-optimizer/SKILL.md` and `template-optimizer/KNOWLEDGE.md`.
The portable user entrypoint lives in `template-optimizer/PROMPT.md`.

When this skill is invoked in Copilot:

1. Read `../../../template-optimizer/PROMPT.md` first.
2. Read `../../../template-optimizer/SKILL.md` next.
3. Read `../../../template-optimizer/KNOWLEDGE.md` for parameter guidance.
4. Use the bundled Python tools under `../../../template-optimizer/tools/` for single-image failures:
   - `python template-optimizer/tools/validate_dbr_template.py <image> --template-file <template>`
   - `python template-optimizer/tools/probe_dbr_templates.py <image>`
   - `python template-optimizer/tools/compare_dbr_template_profiles.py <current-template> <proven-template>`
5. Treat root-level helper scripts as compatibility wrappers only.
6. Use `../../../template-optimizer/resources/harness_py/` for dataset benchmarking and reporting.
7. Follow the stop conditions and one-parameter-family-at-a-time rules from the canonical skill.

Typical Copilot prompts:

- `Use the template-optimizer skill to tune this barcode image`
- `Use the template-optimizer skill to optimize these images`
- `Use the template-optimizer skill to explain DeblurModes`
- `Use the template-optimizer skill to generate a decode report`