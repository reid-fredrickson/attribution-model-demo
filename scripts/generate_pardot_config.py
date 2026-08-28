"""
Turns an attribution_report.csv (from run_attribution_models.py) for a single
chosen model into a human-readable implementation spec: what to configure in
Salesforce Customizable Campaign Influence and how to structure Pardot
campaign grouping, so the weighting scheme actually shows up in native
reports rather than staying a one-off analysis.

This script does not connect to Salesforce or Pardot. It produces a markdown
spec for an admin to act on, because Customizable Campaign Influence model
setup, engagement metrics, and weighting rules are configured through the
Salesforce Setup UI (Campaign Influence Setup), not the bulk API in a way
that's safe to script blind.

Usage:
    python generate_pardot_config.py --report ../assets/sample_data/attribution_report.csv \
        --model w_shaped --out ../assets/sample_data/implementation_spec.md
"""

import argparse
import csv
from collections import defaultdict


def load_report(path, model):
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["Model"] == model]
    if not rows:
        raise ValueError(f"No rows found for model '{model}' in {path}")
    return rows


def build_spec(rows, model):
    total_dollars = sum(float(r["Attributed_Dollars"]) for r in rows)
    rows_sorted = sorted(rows, key=lambda r: -float(r["Attributed_Dollars"]))

    by_type = defaultdict(float)
    for r in rows:
        by_type[r["Campaign_Type"]] += float(r["Attributed_Dollars"])

    lines = []
    lines.append(f"# Attribution Implementation Spec: {model}")
    lines.append("")
    lines.append(f"Generated from {len(rows)} campaigns across the analyzed closed-won opportunities, "
                  f"totaling ${total_dollars:,.0f} in attributed pipeline value.")
    lines.append("")
    lines.append("## 1. Salesforce: Customizable Campaign Influence weights")
    lines.append("")
    lines.append("Set up in Setup > Campaign Influence > Campaign Influence Setup. Enable "
                  "Customizable Campaign Influence (if not already active) and define a weighting "
                  f"rule that approximates the {model} split below. Salesforce's engine applies "
                  "weights at the model-configuration level (typically by touch position or "
                  "engagement type), so translate the per-campaign dollar split below into the "
                  "closest equivalent position-based rule your org's edition supports; exact "
                  "per-campaign percentages are the target to validate against once configured, "
                  "not a literal field-by-field mapping.")
    lines.append("")
    lines.append("| Campaign | Campaign Type | Attributed % of analyzed pipeline | Attributed $ |")
    lines.append("|---|---|---|---|")
    for r in rows_sorted[:20]:
        pct = float(r["Attributed_Dollars"]) / total_dollars if total_dollars else 0
        lines.append(f"| {r['Campaign_Name']} | {r['Campaign_Type']} | {pct:.1%} | ${float(r['Attributed_Dollars']):,.0f} |")
    lines.append("")
    lines.append("## 2. Roll-up by campaign type")
    lines.append("")
    lines.append("Use this to sanity-check the model at the channel-strategy level, and as the basis "
                  "for a Pardot campaign folder/tagging convention so future campaigns of the same "
                  "type inherit a sensible starting weight.")
    lines.append("")
    lines.append("| Campaign Type | Share of attributed pipeline |")
    lines.append("|---|---|")
    for ctype, dollars in sorted(by_type.items(), key=lambda kv: -kv[1]):
        pct = dollars / total_dollars if total_dollars else 0
        lines.append(f"| {ctype} | {pct:.1%} |")
    lines.append("")
    lines.append("## 3. Pardot-side changes to support ongoing measurement")
    lines.append("")
    lines.append("- Confirm Connected Campaigns is enabled so every Pardot asset maps to a Salesforce "
                  "Campaign the influence model can read.")
    lines.append("- Standardize a Campaign_Type custom field/picklist matching the taxonomy used here, "
                  "so future campaigns roll into this reporting structure without manual remapping.")
    lines.append("- Turn on completion actions for the touchpoint types that scored highest in the "
                  "win/loss driver analysis (see win_loss_drivers.csv), so those specific actions "
                  "reliably create Campaign Member records rather than being tracked as anonymous "
                  "activity only.")
    lines.append("- Re-run this analysis on a fixed cadence (recommended: quarterly, given the ~6 month "
                  "sales cycle means each new closed-won cohort meaningfully shifts the data) and diff "
                  "the weights against this spec to catch drift.")
    lines.append("")
    lines.append("## 4. Caveats before implementing")
    lines.append("")
    lines.append("- This spec reflects the model and data available at generation time. Validate the "
                  "underlying journeys.csv join rate (see ingest_validate.py console output for "
                  "unmatched-engagement warnings) before treating these percentages as final; a high "
                  "unmatched rate means real engagement is missing from this picture.")
    lines.append("- Multi-touch weighting in Salesforce Customizable Campaign Influence has edition and "
                  "configuration limits; confirm what's actually supported in the org before assuming a "
                  "literal per-campaign percentage is settable.")
    lines.append("- Sample sizes on closed-won cohorts under ~20-30 deals should be treated as directional, "
                  "not final; expect the weights to shift as more closed-won data accumulates.")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = load_report(args.report, args.model)
    spec = build_spec(rows, args.model)
    with open(args.out, "w") as f:
        f.write(spec)
    print(f"Wrote implementation spec to {args.out}")
