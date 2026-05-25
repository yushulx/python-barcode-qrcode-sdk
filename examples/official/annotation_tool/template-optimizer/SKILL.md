---
name: template-optimizer
description: Iteratively tune a Dynamsoft Barcode Reader JSON template to maximize decode success on difficult barcode images. Also serves as an educational guide for DBR template parameters and can generate visual HTML reports. Use when the user wants to optimize barcode reading, tune DBR templates, understand DBR parameters, or generate barcode decode reports.
---

# DBR Template Optimizer

Iteratively optimize a Dynamsoft Barcode Reader (DBR) template JSON to achieve the best possible barcode decode rate on a set of difficult images. Can also educate users about DBR template structure and parameters, or generate visual decode reports.

## Capabilities

1. **Optimize** — Iteratively tune a template against a test image set
2. **Educate** — Explain DBR template structure, parameters, and best practices
3. **Report** — Generate visual HTML reports showing per-image decode results

## Operating Rules

These rules apply in every mode, especially during optimization:

1. **Observe before editing.** Inspect the barcode image first and describe visible symptoms: quiet-zone loss, border clipping, blur, low contrast, inversion, warping, wrinkles, nearby text, or texture.
2. **Prefer the cheapest trustworthy evidence first.** For a single-image failure, use the repository's direct validator before running a large harness sweep.
3. **Change one parameter family at a time.** Do not modify localization, decode, and acceptance rules together unless there is strong evidence they are coupled.
4. **Use a stop condition.** If the raw image and the basic variant sweep both fail, say explicitly that template-only tuning is likely exhausted for the current pixels.
5. **Prefer focused templates for focused problems.** When the task is about one known symbol or one recurring failure case, favor a minimal single-template JSON over editing a large exported default file.
6. **Do not assume example templates are relevant.** Reuse an existing template only when the barcode type and failure pattern are close enough to justify it.

### Mode Selection

Choose the mode based on what the user asks:

| User Intent | Mode | Trigger Phrases |
|------------|------|-----------------|
| Tune/optimize barcode reading | **Optimize** | "optimize my template", "improve decode rate", "tune DBR for these images", "find the best template" |
| Learn about DBR templates | **Educate** | "explain DeblurModes", "what parameters affect blurry images?", "how does the template JSON work?", "teach me about DBR" |
| Visualize existing results | **Report** | "generate a report from results", "show me the decode results visually", "create an HTML report" |

If ambiguous, ask the user which mode they want.

Inside **Optimize**, choose the execution track that matches the request:

- **Single-image triage** — use when the user is trying to rescue one hard image or one failure case.
- **Dataset optimization** — use when the user wants the best template across many images and needs score-based iteration.

---

## Skill Resources

This skill bundles its own resource files. **Before doing anything else**, locate the skill directory:

```bash
# Find the skill's own SKILL.md to determine the resource paths
Glob: **/template-optimizer/SKILL.md
```

Once found, all resources are relative to that directory:

```
template-optimizer/
   PROMPT.md
   SKILL.md
   KNOWLEDGE.md
   requirements.txt
   tools/validate_dbr_template.py
   tools/probe_dbr_templates.py
   tools/compare_dbr_template_profiles.py
   tools/dbr_license.py
   resources/harness_py/main.py
   resources/harness_py/requirements.txt
   resources/report/report_template.html
   templates/examples/dbr_template.json
   templates/v3.4.1000/parameters.md
```

The bundled single-image evidence tools live under `tools/`, the batch harness lives under `resources/harness_py/`, and the supporting reference lives in `KNOWLEDGE.md` plus `templates/v3.4.1000/parameters.md`.

Assign the skill directory path to a variable `SKILL_DIR` for use throughout the workflow.

Use the bundled tools under `SKILL_DIR/tools/` as the first-line evidence path for **single-image triage**. If the current repository also exposes root-level wrappers such as `validate_dbr_template.py`, `probe_dbr_templates.py`, or `compare_dbr_template_profiles.py`, treat them as compatibility aliases only.

The Python harness runs directly from `SKILL_DIR/resources/harness_py/main.py`.

### Dependencies

| Tool | Required For | Install / Check |
|------|-------------|-----------------|
| Python 3.8+ | All optimizer workflows | `python --version` |
| OpenCV, NumPy, Dynamsoft Capture Vision bundle | Single-image triage and batch harness | `pip install -r SKILL_DIR/requirements.txt` |
| Node.js 18+ (optional) | Report generation (faster for large results) | `node --version` |

## Using With GitHub Copilot

`template-optimizer/` is the canonical, portable package. You can copy this folder into another workspace and use it without `.github/`.

For portable use in Copilot, Claude, or another coding agent:

1. Keep `template-optimizer/PROMPT.md`, `template-optimizer/SKILL.md`, and `template-optimizer/KNOWLEDGE.md` together.
2. Ask the agent to read `template-optimizer/PROMPT.md` and follow the workflow in this directory.
3. Use the bundled tools under `template-optimizer/tools/` for single-image triage.

For Copilot-native discovery inside this repository, `.github/` remains an optional thin wrapper:

1. Keep a discoverable skill entry at `.github/skills/template-optimizer/SKILL.md`.
2. Optionally keep `.github/prompts/tune-dbr-template.prompt.md` as a convenience entrypoint.
3. Make those wrappers point back to this directory as the canonical source.
4. In Copilot Chat, ask for one of these directly:
   - `Use the template-optimizer skill to tune this barcode image`
   - `Use the template-optimizer skill to optimize these images`
   - `Use the template-optimizer skill to explain DeblurModes`
   - `Use the template-optimizer skill to generate a decode report`

If skill discovery does not trigger automatically, ask Copilot to read `template-optimizer/PROMPT.md` and follow the Python-only workflow in this directory.

---

## Mode: Optimize

Optimization has two tracks:

- **Track A: Single-image triage** — diagnose one failure case quickly and make the smallest defensible template change.
- **Track B: Dataset optimization** — iterate against a directory of images and maximize decode success with metrics.

### Step 0 — Gather Information

Ask the user for the following. Use the `AskUserQuestion` tool for structured choices where applicable.

| Parameter | Required | Default | Notes |
| --- | --- | --- | --- |
| Image path or image directory path | Yes | — | Use an image path for Track A and a directory for Track B |
| License key | No | trial key | Ask: "Do you have a Dynamsoft license key, or should I use the trial?" Trial key: `DLS2eyJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSJ9` (may be expired) |
| Barcode format hints | No | All formats | e.g., "DataMatrix only", "1D barcodes" |
| Ground truth file | No | None | JSON mapping filenames → expected barcode texts |
| Max iterations | No | 10 | — |
| Generate visual report | No | Yes | HTML report with per-image results |
| Converted image dir | No | None (temp) | **Required for HEIC/HEIF images** — directory to save converted JPEGs so the HTML report can display them. e.g. `imgs_jpg/`. Created automatically if it doesn't exist. |
| Preprocessing allowed | No | Yes | Required to decide whether padded/rescaled variants are acceptable evidence or whether the task is strictly template-only |
| Current template path | No | None | If provided, validate it directly before theorizing |
| Proven template path | No | None | If the user has a known-good template from Dynamsoft or a teammate, diff it before broad exploration |

Choose the track immediately after Step 0:

- If the user supplied one hard image or explicitly wants help with one failure case, start with **Track A**.
- If the user supplied a directory and wants rate maximization, benchmark gains, or an HTML report, use **Track B**.
- If Track A finds a working candidate and the user later wants broader validation, promote that candidate into Track B.

**Ground truth file format** (optional JSON):

```json
{
  "image1.png": ["expected_barcode_text_1"],
  "image2.jpg": ["expected_text_A", "expected_text_B"]
}
```

### Step 1 — Single-Image Triage (Track A)

Use this track before broad harness work when the problem is a single barcode image.

#### 1a. Observe the image first

Inspect the image directly and record only what is visible:

- Is the quiet zone missing or very thin?
- Is any edge clipped by the image boundary?
- Is the symbol warped, folded, stretched, or wrinkled?
- Is it blurry, or mainly low contrast?
- Is it dark-on-light, light-on-dark, or ambiguous?
- Is there heavy background texture or nearby text?

State which single parameter family those symptoms point to before changing anything.

#### 1b. Validate the current template through the simplest path

Use the bundled helper tools here. In repositories that still expose root-level wrappers, those wrappers should forward to the same commands.

1. Run the direct validator first:

   ```bash
   python SKILL_DIR/tools/validate_dbr_template.py <image> --template-file <template>
   ```

   The validator must initialize the DBR license before creating `CaptureVisionRouter`; otherwise `NO_RESULT` is not trustworthy evidence.

2. Establish the broader baseline only after the direct result is known:

   ```bash
   python SKILL_DIR/tools/probe_dbr_templates.py <image>
   ```

3. If the user already has a proven template, compare it before theorizing:

   ```bash
   python SKILL_DIR/tools/compare_dbr_template_profiles.py <current-template> <proven-template>
   ```

4. If everything still returns `NO_RESULT`, test whether simple preprocessing changes the outcome:

   ```bash
   python SKILL_DIR/tools/probe_dbr_templates.py <image> --variant-set basic --report-json tuning-report.json
   ```

#### 1c. Classify the failure before editing

Use the image observation, direct validation result, probe matrix, and optional template diff together:

- **Raw image succeeds with a candidate template** → keep tuning in the template only.
- **Only a preprocessed variant succeeds** → recommend preprocessing plus template tuning; do not pretend template-only tuning solved the problem.
- **No raw or basic variant succeeds** → stop and say template-only tuning is likely exhausted for the current pixels.
- **A proven template mainly differs in deformation handling or separate decode image parameters** → prioritize those before adding more `DeblurModes`.
- **Tiny single-code DataMatrix crops stall under the standard path** → compare `DPMCRM_SKIP` versus `DPMCRM_GENERAL` before adding rescue ROIs or center-only crops. Validate that candidate on a neighboring slice too, because inverted-only DPM ports can overfit badly.

#### 1d. Make one minimal edit

Apply exactly one parameter family per edit, in this order:

1. Scope first: `ExpectedBarcodesCount`, `BarcodeFormatIds`, `DPMCodeReadingModes`
2. Localization second: `LocalizationModes`, `ConfidenceThreshold`
3. Decode third: `DeformationResistingModes`, decode `ImageParameterOptions`, `DeblurModes`, `BarcodeScaleModes`, grayscale and binarization choices
4. Acceptance last: `MinQuietZoneWidth`, `MirrorMode`, `ReturnPartialBarcodeValue`

Prefer a new focused template file with one `CaptureVisionTemplate` over editing a large exported default file.

#### 1e. Re-validate immediately

After each edit, re-run the direct validator before making another change:

```bash
python SKILL_DIR/tools/validate_dbr_template.py <image> --template-file <candidate-template>
```

Re-run the broader probe only when the direct result changes or remains ambiguous.

### Step 2 — Setup Verification (Track B)

#### 2a. Set Up the Python Harness

1. Check Python: `python --version` (need 3.8+)
2. Install the SDK:

   ```bash
   pip install -r SKILL_DIR/requirements.txt
   ```

3. Set `HARNESS_CMD`:

   ```
   python SKILL_DIR/resources/harness_py/main.py
   ```

   If the environment exposes the interpreter as `python3`, use that instead.

#### 2b. Verify Everything Works

1. Test: `<harness> --help`
2. Test license + dump default template:

   ```bash
   <harness> --dump-default-template default_template.json --license <key>
   ```

3. Verify the image directory exists and contains images
4. If ground truth provided, verify it's valid JSON

All `<harness>` calls in Steps 3–7 mean the `HARNESS_CMD` set above.

The optimizer is Python-only. There is no separate C++ build path.

If any check fails, help the user resolve the issue before proceeding.

### Step 3 — Load Knowledge & Establish Baseline

#### 3a. Read the Knowledge Base

**Read `SKILL_DIR/KNOWLEDGE.md`** to load the full parameter reference, optimization playbook, and failure pattern database. Also read the version-specific reference from `SKILL_DIR/templates/v3.4.1000/parameters.md` (or the appropriate version).

This knowledge is essential for Steps 4 and 5.

If Track A already produced a credible hypothesis or a focused template, carry that evidence forward instead of restarting from a blank default template.

#### 3b. Dump and Run Baseline

1. **Dump the full default template** (reveals every parameter with defaults):

   ```bash
   <harness> --dump-default-template default_template.json --license <key>
   ```

2. **Run baseline test**:

   ```bash
   <harness> --template default_template.json --images <dir> --license <key> --output baseline_results.json
   ```

   If the image directory contains HEIC/HEIF files, add `--converted-dir imgs_jpg` so the
   converted JPEGs are saved for the HTML report:

   ```bash
   <harness> --template default_template.json --images <dir> --license <key> --output baseline_results.json --converted-dir imgs_jpg
   ```

3. **Present baseline results**:

   ```
   BASELINE RESULTS
   ─────────────────────────────────
   Decode rate:      87/202 (43.07%)
   Avg confidence:   88.45
   Avg time/image:   28 ms

   FAILING IMAGES (96 of 202)
   ─────────────────────────────────
   ✗ image_001.png    — 0 barcodes found
   ✗ image_002.png    — 0 barcodes found
   ...
   ```

4. Copy `default_template.json` to `best_template.json`.

### Step 4 — Visual Analysis of Failures

For each failing image (inspect a diverse sample of up to 10 — select images from different timestamps/batches to ensure variety), use the Read tool to visually inspect it.

Diagnose failure causes using the knowledge from `KNOWLEDGE.md` > "Common Failure Patterns" section. Present the diagnosis:

```
FAILURE ANALYSIS (10 sampled from 96 failures)
─────────────────────────────────
image_001.png  → Extreme color noise/grain       → GEM_GRAY_SMOOTH, GEM_GRAY_EQUALIZE
image_015.png  → Very small barcode (~20px)       → BSM_LINEAR_INTERPOLATION
image_042.png  → Light bars on dark background    → GTM_INVERTED
image_078.png  → Blurry, out of focus             → DeblurModes (all modes)
...

DOMINANT ISSUES: noise (6/10), blur (3/10), small size (2/10)
RECOMMENDED FIRST CHANGES: GrayscaleEnhancementModes + GrayscaleTransformationModes
```

During this step, explicitly say which parameter families you are **not** changing yet and why. This prevents random parameter churn.

### Step 5 — Iterative Optimization

For each iteration:

#### 5a. Choose a Change

Pick the most impactful untried adjustment based on the failure analysis and the optimization order in `KNOWLEDGE.md` > "Proven Optimization Order". Apply one logical group of changes per iteration (e.g., "enable all DeblurModes" is one iteration, not nine).

Reject candidate iterations that mix multiple unrelated parameter families unless the evidence clearly ties them together.

#### 5b. Modify the Template

Read the current best template JSON. Navigate to the correct Section/Stage to modify:

**How to find the right location in the template JSON:**

- For **image preprocessing** parameters (GrayscaleTransformationModes, GrayscaleEnhancementModes, BinarizationModes):
  Navigate to `ImageParameterOptions[0].ApplicableStages[]` → find the object with `"Stage": "SST_TRANSFORM_GRAYSCALE"` (or whichever stage) → modify the modes array inside it.

- For **barcode task** parameters (LocalizationModes, DeblurModes, DeformationResistingModes, etc.):
  Navigate to `BarcodeReaderTaskSettingOptions[0].SectionArray[]` → find the section with `"Section": "ST_BARCODE_DECODING"` (or `ST_BARCODE_LOCALIZATION`) → then inside its `StageArray[]` find `"Stage": "SST_DECODE_BARCODES"` (or whichever stage) → modify the modes array.

- For **format specification** parameters (MinResultConfidence, MirrorMode):
  Navigate to `BarcodeFormatSpecificationOptions[]` → modify the relevant spec objects.

- For **top-level** parameters (Timeout):
  Navigate to `CaptureVisionTemplates[0].Timeout`.

When modifying mode arrays, **add** to the array — don't replace. The SDK tries modes in order.

Write the updated template as `iter_N_template.json`.

#### 5c. Run the Test

```bash
<harness> --template iter_N_template.json --images <dir> --license <key> --output iter_N_results.json
```

If using HEIC/HEIF images, include `--converted-dir imgs_jpg` (JPEGs only need converting once — on subsequent iterations the files already exist and are overwritten harmlessly):

```bash
<harness> --template iter_N_template.json --images <dir> --license <key> --output iter_N_results.json --converted-dir imgs_jpg
```

#### 5d. Compare Scores

| Metric | Priority | Compare |
| --- | --- | --- |
| decode_rate (or ground_truth_match_rate) | Primary | Higher is better |
| avg_confidence | Secondary | Higher is better |
| avg_time_ms | Tertiary (tiebreaker only) | Lower is better |

**Regression detection**: Compare the `per_image` arrays between `iter_N_results.json` and the current best results. If any image that **previously decoded** now **fails to decode**, this is a regression. Report which images regressed.

#### 5e. Keep or Revert

- **Improved** (primary metric up, no regressions): Update `best_template.json`. Report the gain.
- **No change** (same primary metric, no regressions): Keep (may help with future combinations).
- **Worse** (primary metric down, or regressions on previously-passing images): Revert to previous best. Note this approach was tried and failed.

If the iteration only helps padded/rescaled variants from Track A but not the raw images, record that separately and do not overstate it as a template-only win.

#### 5f. Log the Iteration

```
ITERATION 3
─────────────────────────────────
Change:    Added DeblurModes [9 modes including DM_DEEP_ANALYSIS]
Decode:    52.48% → 56.44%  +3.96%
Confidence: 87.91 → 85.66  -2.25 (expected for borderline decodes)
Time:      228ms → 321ms  (slower, acceptable)
Regressions: None
Result:    KEPT
```

#### 5g. Convergence Check

Stop iterating when:
- 100% decode rate, or
- Last 3 iterations produced no improvement, or
- Max iterations reached
- Track A evidence shows only preprocessed variants succeed and the user disallows preprocessing

### Step 6 — Fine-Tuning (optional)

After major mode changes converge, fine-tune sub-parameters if decode rate is still below target:

- `BinarizationModes` → `BlockSizeX`, `BlockSizeY` (try 5, 7, 9, 11)
- `BarcodeScaleModes` → `ModuleSizeThreshold` (try 2, 3, 4), `TargetModuleSize` (try 4, 6, 8)
- `LocalizationModes` → `ScanStride` (lower = more thorough)
- `Timeout` → increase to 30000 or 60000 for complex images
- `ExpectedBarcodesCount` → set based on observed maximum

### Step 7 — Output

#### 7a. Save Optimized Template

The default template dump contains multiple `CaptureVisionTemplates` entries (e.g., ReadBarcodes_Default, ReadBarcodes_ReadRateFirst, ReadBarcodes_SpeedFirst, ReadSingleBarcode) along with all their associated settings. The final output should contain **only the single best template** — the one that was actually optimized — with all unreferenced settings removed.

**Pruning procedure:**

1. **Identify the best template** — the `CaptureVisionTemplates` entry that was used during optimization (typically `ReadBarcodes_ReadRateFirst` or whichever was selected/modified).

2. **Trace its dependency chain** — starting from the best template entry, collect all referenced names:
   - `CaptureVisionTemplates[best].ImageROIProcessingNameArray` → keep only matching `TargetROIDefOptions` entries
   - Each kept `TargetROIDefOptions[].TaskSettingNameArray` → keep only matching `BarcodeReaderTaskSettingOptions` entries
   - Each kept `BarcodeReaderTaskSettingOptions[].BarcodeFormatSpecificationNameArray` → keep only matching `BarcodeFormatSpecificationOptions` entries
   - Each kept `BarcodeReaderTaskSettingOptions[].SectionArray[].ImageParameterName` → keep only matching `ImageParameterOptions` entries

3. **Prune the JSON** — remove all entries from each `*Options` array that are not referenced by the best template's dependency chain. The `CaptureVisionTemplates` array should contain exactly one entry.

4. Write the pruned result to `optimized_template.json`.

#### 7b. Generate Visual HTML Report (if requested)

Read the report template from `SKILL_DIR/resources/report/report_template.html`.

Replace the three placeholder values with actual data:
- `__RESULTS_JSON__` → the final results JSON object (inline JS literal, NOT a string)
- `__BASELINE_JSON__` → the baseline results JSON object, or the literal `null`
- `__IMAGE_DIR__` → relative path from the HTML file to the image directory, as a quoted JS string

**HEIC/HEIF images**: If `--converted-dir` was used (e.g. `imgs_jpg`), set `IMAGE_DIR` to that directory — the report uses each image's `converted_file` field (the `.jpg` name) automatically and falls back to `file` for non-converted images. Example: `"imgs_jpg"`.

**If Node.js is available** (recommended for large result files):

```bash
node -e "
const fs = require('fs');
const tpl = fs.readFileSync('SKILL_DIR/resources/report/report_template.html', 'utf-8');
const results = fs.readFileSync('iter_N_results.json', 'utf-8').trim();
const baseline = fs.readFileSync('baseline_results.json', 'utf-8').trim();
let html = tpl.replace('__RESULTS_JSON__', results).replace('__BASELINE_JSON__', baseline).replace('__IMAGE_DIR__', '\"<image-dir>\"');
fs.writeFileSync('optimization_report.html', html);
"
```

**If Node.js is NOT available**: Use the Read and Write tools — read the template, perform the replacements in-context, and write the output HTML.

The report shows:
- Summary stat cards (decode rate, confidence, time)
- Baseline vs. optimized comparison table
- Every image with decoded/failed status
- Barcode text, confidence, format alongside each image
- Barcode location highlighted as a green polygon overlay
- Per-image details collapsed by default (click to expand)
- Filter buttons: All / Decoded / Failed

#### 7c. Present Summary

```
═══════════════════════════════════════════════════
DBR TEMPLATE OPTIMIZATION REPORT
═══════════════════════════════════════════════════

BASELINE → OPTIMIZED
─────────────────────────────────
Decode rate:      43.07% → 56.44%  (+13.37%)
Avg confidence:   88.45  → 85.66   (-2.79)
Avg time/image:   28ms   → 321ms   (+293ms)

ITERATION LOG
─────────────────────────────────
#1  GTM_INVERTED + GEM + DRM + BCM + Timeout    → 43.07% → 50.50%  KEPT
#2  LM_STATISTICS_MARKS + BSM + MinConfidence    → 50.50% → 52.48%  KEPT
#3  All DeblurModes + GEM_GRAY_SMOOTH            → 52.48% → 56.44%  KEPT

OUTPUT FILES
─────────────────────────────────
optimized_template.json    — Best performing template
optimization_report.html   — Visual results report (open in browser)

VALIDATION ENGINE
─────────────────────────────────
Python harness (`dynamsoft-capture-vision-bundle`)
```

If Track A ended in a stop condition, say so plainly in the summary and recommend the next non-template action: preprocessing, re-capture, crop refinement, or ground-truth verification.

#### 7d. Update Knowledge Base

After the optimization run, update `SKILL_DIR/KNOWLEDGE.md` with:
- New parameter combinations that worked (or didn't)
- Updated results tables
- New failure patterns discovered
- Any corrections to parameter understanding

---

## Mode: Educate

When the user asks about DBR templates, parameters, or best practices (rather than running an optimization), enter education mode.

### How It Works

1. **Read `SKILL_DIR/KNOWLEDGE.md`** — the accumulated knowledge about template structure, parameters, optimization strategies, and failure patterns.

2. **Read version-specific data** from `SKILL_DIR/templates/<version>/parameters.md` — defaults, pipeline stages, API details for a specific SDK version.

3. **Answer the user's question** using this knowledge:
   - Clear explanations of template structure and the Section/Stage hierarchy
   - Parameter descriptions with mode values, sub-parameters, and recommended values
   - Before/after template JSON examples when relevant
   - Practical advice from real optimization runs (results data in KNOWLEDGE.md)
   - Failure pattern diagnosis ("for blurry images, try...")

### Growing the Knowledge

After answering, if the conversation revealed new insights or the user provided corrections, update `KNOWLEDGE.md` with the new information. Encourage users to share findings with Dynamsoft engineers for verification (see the "Remaining Items for Dynamsoft Verification" section in KNOWLEDGE.md).

---

## Mode: Report

Generate a visual HTML report from existing results without running an optimization.

### How It Works

1. Ask the user for:
   - Path to the results JSON file (from a previous harness run)
   - Path to a baseline JSON file (optional, for comparison)
   - Path to the image directory
   - Output filename (default: `optimization_report.html`)

2. Read the report template from `SKILL_DIR/resources/report/report_template.html`

3. Replace placeholders (same as Step 7b in Optimize mode):
   - `__RESULTS_JSON__` → parsed results object
   - `__BASELINE_JSON__` → parsed baseline object or `null`
   - `__IMAGE_DIR__` → quoted relative path to images

4. Write the filled HTML to the output path

5. The user can open the HTML in any browser to interactively browse results.

---

## Platform & Shell Compatibility

### Windows

Use forward slashes in all paths when running from Git Bash or similar Unix-like shells. The Python harness and report-generation commands work with both forward and backslash paths on Windows.

### Python

```bash
python --version  # Need 3.8+
pip install -r template-optimizer/resources/harness_py/requirements.txt
```

### Node.js (optional, for report generation)

```bash
node --version 2>/dev/null  # Need 18+
```

If Node.js is not available, report generation falls back to the Write tool.

---

## Example Sessions

### Optimize Mode

```
User: /template-optimizer
Claude: What would you like to do — optimize a template, learn about DBR parameters, or generate a report?
User: Optimize my template for these difficult barcode images in the "samples/" folder
Claude: I'll optimize a DBR template for the images in samples/. A few questions:
        [AskUserQuestion: Do you have a Dynamsoft license key?]
User: Here's my key: t0086YQ...
Claude: [Locates skill resources]
   [Installs Python harness requirements and verifies --help]
        [Reads KNOWLEDGE.md for parameter reference]
        [Dumps default template, runs baseline: 87/202 = 43.07%]
        [Inspects 10 failing images — dominant issues: noise, blur, small barcodes]
        [Iteration 1: adds GTM_INVERTED + enhancement modes → 50.50%]
        [Iteration 2: adds localization modes + scale modes → 52.48%]
        [Iteration 3: adds all DeblurModes → 56.44%]
        [Convergence after 3 more iterations with no improvement]
        [Generates optimization_report.html and optimized_template.json]
        Report saved. Open optimization_report.html in your browser to browse per-image results.
```

### Educate Mode

```
User: /template-optimizer
Claude: What would you like to do — optimize a template, learn about DBR parameters, or generate a report?
User: What parameters should I change for blurry barcode images?
Claude: [Reads KNOWLEDGE.md]
        For blurry images, the most impactful parameters are:

        1. **DeblurModes** — Add DM_DEEP_ANALYSIS, DM_SMOOTHING, DM_SHARPENING...
           [explains each mode with speed/quality trade-offs]

        2. **GrayscaleEnhancementModes** — Add GEM_SHARPEN_SMOOTH...
           [explains with before/after examples]

        In our real-world testing, adding all DeblurModes improved decode rate by +4%
        on extremely noisy DataMatrix images.
```

### Report Mode

```
User: /template-optimizer
Claude: What would you like to do?
User: Generate a visual report from my iter3_results.json
Claude: [Asks for image directory and optional baseline file]
User: Images are in "missed/", baseline is baseline_results.json
Claude: [Reads report template, replaces placeholders, writes HTML]
        Report saved: optimization_report.html
        Open it in your browser — you can filter by decoded/failed and click images to see barcode details.
```

---

## Quick Reference

Consult `KNOWLEDGE.md` for the full parameter deep dive. Summary optimization order:

1. `GrayscaleTransformationModes` — add GTM_INVERTED (nearly free)
2. `GrayscaleEnhancementModes` — add GEM_GRAY_EQUALIZE, GEM_SHARPEN_SMOOTH, GEM_GRAY_SMOOTH
3. `DeblurModes` — explicitly set all modes (controls order, adds modes not in format defaults)
4. `DeformationResistingModes` — DRM_GENERAL (moderate cost)
5. `BarcodeComplementModes` — BCM_GENERAL (low cost)
6. `BarcodeScaleModes` — BSM_LINEAR_INTERPOLATION for small barcodes
7. `LocalizationModes` — add LM_STATISTICS_MARKS, LM_CENTRE, LM_NEURAL_NETWORK
8. `MinResultConfidence` — lower from 30 to 10
9. `Timeout` — increase to 30000ms
10. Sub-parameter fine-tuning (BlockSizeX/Y, ModuleSizeThreshold, etc.)

### Template Modification Rules

- **Locate skill resources first** — Glob for `**/template-optimizer/SKILL.md`
- **Read KNOWLEDGE.md** before making parameter decisions
- **Use bundled helper tools first for a single-image failure** — `SKILL_DIR/tools/validate_dbr_template.py`, `SKILL_DIR/tools/probe_dbr_templates.py`, `SKILL_DIR/tools/compare_dbr_template_profiles.py`
- **State the observed symptom and the target parameter family together** before editing
- Place parameters in the correct **Section/Stage** (see KNOWLEDGE.md architecture diagram)
- When modifying mode arrays, **add** to the array — don't replace
- Change one parameter family per iteration unless there is strong evidence of coupling
- Never sacrifice decode rate for speed
- If a change causes regressions on previously-passing images, revert immediately
- If raw plus basic variants all fail, stop calling it a template-only problem without qualification
- Test each logical group of changes as a separate iteration

### Version-Specific Data

Parameter defaults and pipeline stages vary by SDK version. Check `templates/<version>/parameters.md`. Currently available:

- `v3.4.1000` — DCV v3.4.1000 parameter reference (Feb 2026)
