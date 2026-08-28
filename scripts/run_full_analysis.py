"""
Runs the full attribution pipeline end to end (ingest/join, win-loss driver
analysis, attribution modeling, implementation spec) and organizes every
output, CSV, markdown, and PDF, into a single timestamped run folder under
`Analysis Outcomes/`.

This is the script the skill's default workflow calls. It defaults to the
bundled synthetic sample data so it can be run immediately with no setup;
point --data-dir at a local folder of real exports to run it against real
data (see README.md for the data-privacy note on why that must stay local).

Usage:
    # Default: run against the bundled sample data
    python run_full_analysis.py

    # Run against your own local exports (never commit these)
    python run_full_analysis.py --data-dir /path/to/your/local/exports --model w_shaped

    # Compare all attribution models instead of just one
    python run_full_analysis.py --model all
"""

import argparse
import csv
import os
import subprocess
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_SAMPLE_DIR = os.path.join(REPO_ROOT, "assets", "sample_data")
OUTCOMES_ROOT = os.path.join(REPO_ROOT, "Analysis Outcomes")


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"Command failed: {' '.join(cmd)}")
    return result.stdout


def count_csv_rows(path):
    if not os.path.exists(path):
        return 0
    with open(path, newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1  # minus header


def csv_to_markdown_simple(csv_path, out_md_path, title, max_rows=200):
    with open(csv_path, newline="") as f:
        rows = list(csv.reader(f))
    lines = [f"# {title}", ""]
    if not rows:
        lines.append("(no rows)")
    else:
        header, body = rows[0], rows[1:max_rows + 1]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        for r in body:
            lines.append("| " + " | ".join(r) + " |")
        if len(rows) - 1 > max_rows:
            lines.append("")
            lines.append(f"_({len(rows) - 1 - max_rows} additional rows omitted from this view; see the CSV for the full table)_")
    with open(out_md_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def win_loss_csv_to_markdown(csv_path, out_md_path):
    with open(csv_path, newline="") as f:
        rows = list(csv.reader(f))
    lines = ["# Win / Loss Driver Analysis", "",
             "Compares which campaigns and campaign types show up more often on closed-won "
             "opportunities versus closed-lost ones. A large positive gap suggests a campaign "
             "correlates with winning; a negative gap is worth investigating.", ""]
    section = None
    header = None
    for row in rows:
        if not row:
            continue
        if row[0].startswith("--"):
            section = row[0].strip("- ")
            lines.append(f"## {section}")
            lines.append("")
            header = None
            continue
        if header is None:
            header = row
            lines.append("| " + " | ".join(header) + " |")
            lines.append("|" + "|".join(["---"] * len(header)) + "|")
        else:
            lines.append("| " + " | ".join(row) + " |")
    with open(out_md_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def attribution_csv_to_markdown(csv_path, out_md_path, top_n=10):
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    by_model = {}
    for r in rows:
        by_model.setdefault(r["Model"], []).append(r)

    lines = ["# Attribution Model Results", "",
              "Top campaigns by attributed pipeline dollars, per model. Compare rankings across "
              "models before trusting any single one; stable rankings are a good sign, wide swings "
              "mean the sample size or data quality needs a look.", ""]
    for model_name, model_rows in by_model.items():
        model_rows_sorted = sorted(model_rows, key=lambda r: -float(r["Attributed_Dollars"]))[:top_n]
        lines.append(f"## {model_name}")
        lines.append("")
        lines.append("| Campaign | Campaign Type | Channel | Attributed Dollars | Touch Count |")
        lines.append("|---|---|---|---|---|")
        for r in model_rows_sorted:
            lines.append(f"| {r['Campaign_Name']} | {r['Campaign_Type']} | {r['Channel']} | "
                          f"${float(r['Attributed_Dollars']):,.0f} | {r['Touch_Count']} |")
        lines.append("")
    with open(out_md_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_manifest(out_dir, data_dir, model, is_sample_data, opp_count, won_count, lost_count):
    path = os.path.join(out_dir, "run_manifest.md")
    lines = [
        "# Run Manifest",
        "",
        f"- Run timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Data source: {data_dir}",
        f"- Data type: {'bundled synthetic sample data' if is_sample_data else 'local file, verify this was not committed to version control'}",
        f"- Attribution model(s) run: {model}",
        f"- Opportunities in journey table: {opp_count}",
        f"- Closed-won / closed-lost: {won_count} / {lost_count}",
        "",
        "## Files in this run",
        "",
        "| File | Format | Contents |",
        "|---|---|---|",
        "| journeys.csv | CSV | Joined opportunity-to-touchpoint table |",
        "| win_loss_drivers.csv / .md / .pdf | CSV, Markdown, PDF | Won vs. lost campaign presence comparison |",
        "| attribution_report.csv / .md / .pdf | CSV, Markdown, PDF | Per-campaign attributed dollars by model |",
        "| implementation_spec.md / .pdf | Markdown, PDF | Salesforce/Pardot configuration recommendations |",
        "",
        "## Caveats" if is_sample_data else "## Notes",
        "",
        ("This run used the bundled synthetic sample data. Numbers here are illustrative only and "
         "demonstrate the pipeline mechanics, not real marketing performance." if is_sample_data else
         "This run used a local data file. Confirm it was not written into any tracked/committed "
         "path in this repository."),
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=DEFAULT_SAMPLE_DIR,
                         help="Folder containing the CSV exports. Defaults to the bundled sample data.")
    parser.add_argument("--model", default="w_shaped",
                         help="Attribution model to run, or 'all' to compute every model.")
    parser.add_argument("--half-life-days", type=int, default=14)
    args = parser.parse_args()

    is_sample_data = os.path.abspath(args.data_dir) == os.path.abspath(DEFAULT_SAMPLE_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = "sample_data" if is_sample_data else "local_data"
    run_dir = os.path.join(OUTCOMES_ROOT, f"run_{timestamp}_{label}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Writing all outputs to: {run_dir}")

    journeys_path = os.path.join(run_dir, "journeys.csv")
    run([sys.executable, os.path.join(SCRIPT_DIR, "ingest_validate.py"),
         "--data-dir", args.data_dir, "--out", journeys_path])

    win_loss_csv = os.path.join(run_dir, "win_loss_drivers.csv")
    run([sys.executable, os.path.join(SCRIPT_DIR, "win_loss_driver_analysis.py"),
         "--journeys", journeys_path, "--out", win_loss_csv])
    win_loss_md = os.path.join(run_dir, "win_loss_drivers.md")
    win_loss_csv_to_markdown(win_loss_csv, win_loss_md)
    run([sys.executable, os.path.join(SCRIPT_DIR, "generate_pdf_reports.py"),
         "--md", win_loss_md, "--out", os.path.join(run_dir, "win_loss_drivers.pdf")])

    attribution_csv = os.path.join(run_dir, "attribution_report.csv")
    run([sys.executable, os.path.join(SCRIPT_DIR, "run_attribution_models.py"),
         "--journeys", journeys_path, "--out", attribution_csv,
         "--model", args.model, "--half-life-days", str(args.half_life_days)])
    attribution_md = os.path.join(run_dir, "attribution_report.md")
    attribution_csv_to_markdown(attribution_csv, attribution_md)
    run([sys.executable, os.path.join(SCRIPT_DIR, "generate_pdf_reports.py"),
         "--md", attribution_md, "--out", os.path.join(run_dir, "attribution_report.pdf")])

    spec_model = args.model if args.model != "all" else "w_shaped"
    spec_md = os.path.join(run_dir, "implementation_spec.md")
    run([sys.executable, os.path.join(SCRIPT_DIR, "generate_pardot_config.py"),
         "--report", attribution_csv, "--model", spec_model, "--out", spec_md])
    run([sys.executable, os.path.join(SCRIPT_DIR, "generate_pdf_reports.py"),
         "--md", spec_md, "--out", os.path.join(run_dir, "implementation_spec.pdf")])

    opp_count = count_csv_rows(os.path.join(args.data_dir, "opportunities.csv"))
    won_count = lost_count = 0
    opps_path = os.path.join(args.data_dir, "opportunities.csv")
    if os.path.exists(opps_path):
        with open(opps_path, newline="") as f:
            for r in csv.DictReader(f):
                if r.get("Is_Won", "").strip().lower() == "true":
                    won_count += 1
                else:
                    lost_count += 1

    write_manifest(run_dir, args.data_dir, args.model, is_sample_data, opp_count, won_count, lost_count)

    print(f"\nDone. All outputs are in: {run_dir}")


if __name__ == "__main__":
    main()
