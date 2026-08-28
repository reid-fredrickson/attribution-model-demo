"""
Converts the skill's markdown and CSV outputs into PDF reports, using
reportlab. Handles simple markdown (headers, paragraphs, bullet lists, and
pipe-delimited tables) and raw CSV-to-table rendering.

This is a formatting step only; it does not recompute anything. Run it after
ingest_validate.py / win_loss_driver_analysis.py / run_attribution_models.py /
generate_pardot_config.py have produced their outputs.

Usage:
    python generate_pdf_reports.py --md path/to/implementation_spec.md --out path/to/implementation_spec.pdf
    python generate_pdf_reports.py --csv path/to/attribution_report.csv --title "Attribution Report" --out path/to/attribution_report.pdf
"""

import argparse
import csv
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
)

STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="H1Custom", parent=STYLES["Heading1"], spaceAfter=12))
STYLES.add(ParagraphStyle(name="H2Custom", parent=STYLES["Heading2"], spaceBefore=10, spaceAfter=8))
STYLES.add(ParagraphStyle(name="BodyCustom", parent=STYLES["Normal"], spaceAfter=8, leading=14))


def _clean_inline(text):
    # strip simple markdown emphasis markers so they don't render literally
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", text)
    return text


def markdown_to_flowables(md_path):
    with open(md_path) as f:
        lines = f.read().splitlines()

    flowables = []
    bullet_buffer = []
    table_buffer = []

    def flush_bullets():
        nonlocal bullet_buffer
        if bullet_buffer:
            items = [ListItem(Paragraph(_clean_inline(b), STYLES["BodyCustom"])) for b in bullet_buffer]
            flowables.append(ListFlowable(items, bulletType="bullet", leftIndent=18))
            flowables.append(Spacer(1, 8))
            bullet_buffer = []

    def flush_table():
        nonlocal table_buffer
        if table_buffer:
            rows = [row for row in table_buffer if not re.match(r"^\|?\s*-+\s*\|", row)]
            parsed = [[c.strip() for c in row.strip().strip("|").split("|")] for row in rows]
            if parsed:
                t = Table(parsed, repeatRows=1, hAlign="LEFT")
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2b2b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                flowables.append(t)
                flowables.append(Spacer(1, 10))
            table_buffer = []

    for line in lines:
        stripped = line.strip()
        is_table_row = stripped.startswith("|")

        if not is_table_row:
            flush_table()
        if not stripped.startswith("- "):
            flush_bullets()

        if not stripped:
            continue
        elif stripped.startswith("# "):
            flowables.append(Paragraph(_clean_inline(stripped[2:]), STYLES["H1Custom"]))
        elif stripped.startswith("## "):
            flowables.append(Paragraph(_clean_inline(stripped[3:]), STYLES["H2Custom"]))
        elif stripped.startswith("### "):
            flowables.append(Paragraph(_clean_inline(stripped[4:]), STYLES["Heading3"]))
        elif stripped.startswith("- "):
            bullet_buffer.append(stripped[2:])
        elif is_table_row:
            table_buffer.append(stripped)
        else:
            flowables.append(Paragraph(_clean_inline(stripped), STYLES["BodyCustom"]))

    flush_bullets()
    flush_table()
    return flowables


def csv_to_flowables(csv_path, title):
    with open(csv_path, newline="") as f:
        rows = list(csv.reader(f))
    flowables = [Paragraph(_clean_inline(title), STYLES["H1Custom"]), Spacer(1, 8)]
    if not rows:
        flowables.append(Paragraph("(no rows)", STYLES["BodyCustom"]))
        return flowables

    # Break very wide/long CSVs into manageable chunks so reportlab tables stay legible
    header, body = rows[0], rows[1:]
    chunk_size = 40
    for i in range(0, len(body), chunk_size) or [0]:
        chunk = body[i:i + chunk_size] if body else []
        table_data = [header] + chunk
        t = Table(table_data, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2b2b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        flowables.append(t)
        flowables.append(Spacer(1, 12))
    return flowables


def build_pdf(flowables, out_path, landscape_mode=False):
    pagesize = landscape(letter) if landscape_mode else letter
    doc = SimpleDocTemplate(out_path, pagesize=pagesize,
                             leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    doc.build(flowables)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--md", help="Markdown file to convert")
    parser.add_argument("--csv", help="CSV file to convert")
    parser.add_argument("--title", default="Report", help="Title, used when converting a CSV")
    parser.add_argument("--out", required=True)
    parser.add_argument("--landscape", action="store_true", help="Use landscape orientation (recommended for wide CSVs)")
    args = parser.parse_args()

    if not args.md and not args.csv:
        raise SystemExit("Provide --md or --csv")

    if args.md:
        flowables = markdown_to_flowables(args.md)
        build_pdf(flowables, args.out, landscape_mode=args.landscape)
    else:
        flowables = csv_to_flowables(args.csv, args.title)
        build_pdf(flowables, args.out, landscape_mode=True)
