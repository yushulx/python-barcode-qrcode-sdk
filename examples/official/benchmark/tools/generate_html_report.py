#!/usr/bin/env python3
"""Generate a self-contained file:// compatible Python benchmark report."""
import argparse
import html
import json
import shutil
from pathlib import Path

STYLE = """
:root{--ink:#172033;--muted:#60708a;--line:#dbe2ea;--bg:#f5f7fa}*{box-sizing:border-box}body{margin:0;font:15px/1.5 Segoe UI,Arial,sans-serif;color:var(--ink);background:var(--bg)}header{padding:52px max(5vw,28px);color:white;background:linear-gradient(120deg,#102649,#1769e0 62%,#00a495)}header h1{margin:0 0 8px;font-size:clamp(30px,5vw,58px);line-height:1.05}.wrap{max-width:1280px;margin:auto;padding:28px}section{background:white;border:1px solid var(--line);border-radius:14px;margin:18px 0;padding:24px;box-shadow:0 3px 18px #1026490c}h2{margin-top:0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.card{border:1px solid var(--line);border-radius:11px;padding:18px}.metric{font-size:32px;font-weight:750}.muted{color:var(--muted)}.disclosure{border-left:5px solid #f0a202;background:#fff8e6;padding:14px 18px}.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}input,select{padding:9px 11px;border:1px solid #bcc8d8;border-radius:7px;background:white}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{position:sticky;top:0;background:#edf3fa}.scroll{overflow:auto;max-height:650px}.correct{color:#087f5b}.not_found,.wrong_text,.wrong_format{color:#c2410c}.unsupported_format{color:#6d28d9}@media print{body{background:white}.controls{display:none}section{break-inside:avoid;box-shadow:none}}
"""

SCRIPT = """
const rows=REPORT_ROWS,body=document.querySelector('#raw tbody');
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render(){const q=document.querySelector('#q').value.toLowerCase(),d=document.querySelector('#decoder').value,o=document.querySelector('#outcome').value;body.innerHTML='';const matched=rows.filter(r=>(!d||r.decoder===d)&&(!o||r.matches.some(m=>m.outcome===o))&&JSON.stringify(r).toLowerCase().includes(q));document.querySelector('#shown').textContent=`Showing ${Math.min(500,matched.length).toLocaleString()} of ${matched.length.toLocaleString()} matching records`;matched.slice(0,500).forEach(r=>{const tr=document.createElement('tr'),out=r.matches.map(m=>m.outcome);tr.innerHTML=`<td>${esc(r.decoder)}</td><td>${esc(r.relative_path)}</td><td>${esc(r.annotation_file)}</td><td>${r.ground_truth.filter(x=>x.decode_eligible).map(x=>esc(x.format)+': '+esc(x.text)).join('<br>')}</td><td>${r.predictions.map(x=>esc(x.format)+': '+esc(x.text)).join('<br>')}</td><td class="${out[0]||''}">${out.map(esc).join(', ')}</td><td>${(r.decode_ns/1e6).toFixed(2)}</td>`;body.appendChild(tr)})}
document.querySelectorAll('#q,#decoder,#outcome').forEach(e=>e.addEventListener('input',render));render();
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--results-json", type=Path)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.results.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    summary = json.loads(args.summary.read_text(encoding="utf8"))
    stats = json.loads(args.inventory.read_text(encoding="utf8"))["summary"]
    environment = json.loads(args.environment.read_text(encoding="utf8"))
    cards = "".join(f'<div class="card"><h3>{html.escape(name)}</h3><div class="metric">{value["coverage_adjusted_recall"]:.1%}</div><div class="muted">{value["correct"]}/{value["eligible_instances"]} exact, mean {value["mean_decode_ms"]:.1f} ms</div></div>' for name, value in summary["decoders"].items())
    decoder_options = "".join(f'<option>{html.escape(x)}</option>' for x in sorted({r["decoder"] for r in rows}))
    outcomes = sorted({m["outcome"] for r in rows for m in r["matches"]})
    outcome_options = "".join(f'<option>{html.escape(x)}</option>' for x in outcomes)
    script = SCRIPT.replace("REPORT_ROWS", json.dumps(rows, ensure_ascii=False).replace("</", "<\\/"))
    decoder_records = sum(value["records"] for value in summary["decoders"].values())
    document = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><link rel="icon" href="data:,"><title>Python BarBeR Barcode Benchmark</title><style>{STYLE}</style><header><h1>ZXing Python vs. Dynamsoft Barcode Reader Python</h1><p>BarBeR public dataset decoding benchmark. Exact payload and canonical format are scored. Localization geometry is not scored.</p></header><main class="wrap"><section><h2>Full benchmark results</h2><div class="cards">{cards}</div></section><section><h2>Dataset audit</h2><div class="cards"><div class="card"><div class="metric">{stats['source_images']:,}</div>original images</div><div class="card"><div class="metric">{stats['annotations']:,}</div>original annotations</div><div class="card"><div class="metric">{stats['excluded_images_without_ground_truth']:,}</div>images without reliable ground truth</div><div class="card"><div class="metric">{stats['duplicate_image_records']:,}</div>exact duplicate image</div><div class="card"><div class="metric">{stats['manifest_images']:,}</div>final unique images</div><div class="card"><div class="metric">{stats['benchmark_annotations']:,}</div>final ground truth barcodes</div><div class="card"><div class="metric">{decoder_records:,}</div>decoder records</div></div></section><section><h2>Method and disclosures</h2><p class="disclosure">{html.escape(summary['disclosure'])}</p><p>Both Python decoders receive the same image loaded by OpenCV. Matching is a location-independent one-to-one multiset match of canonical format and exact normalized payload. UPC-A and EAN-13 leading zero equivalence is normalized before scoring.</p><p><strong>Measured environment:</strong> {html.escape(str(environment.get('operating_system','')))}, {html.escape(str(environment.get('processor','')))}, Python {html.escape(str(environment.get('python','')))}, {html.escape(str(environment.get('configuration','')))} {html.escape(str(environment.get('architecture','')))}, {environment.get('threads_per_decoder_task',1)} thread per decoder task, {environment.get('repetitions',1)} measured run.</p></section><section><h2>Per-image results</h2><p class="muted">The interactive table displays up to 500 matching rows. The complete JSONL stream and a complete JSON package are included in the report downloads.</p><div class="controls"><input id="q" placeholder="Search image, format, payload"><select id="decoder"><option value="">All decoders</option>{decoder_options}</select><select id="outcome"><option value="">All outcomes</option>{outcome_options}</select></div><p id="shown" class="muted"></p><div class="scroll"><table id="raw"><thead><tr><th>Decoder</th><th>Image</th><th>Source</th><th>Ground truth</th><th>Predictions</th><th>Outcomes</th><th>Decode ms</th></tr></thead><tbody></tbody></table></div></section></main><script>{script}</script></html>'''
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf8")
    downloads = args.output.parent / "downloads"
    downloads.mkdir(exist_ok=True)
    downloads_list = [(args.results, "results.jsonl"), (args.summary, "summary.json"), (args.inventory, "barber_source_files.json"), (args.environment, "benchmark_environment.json")]
    if args.results_json:
        downloads_list.append((args.results_json, "results.json"))
    for source, name in downloads_list:
        shutil.copy2(source, downloads / name)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
