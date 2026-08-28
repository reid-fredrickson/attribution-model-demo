"""
Computes touchpoint attribution weights under each rule-based framework, for
closed-won opportunities (the deals that produced revenue to attribute).

Input: the journeys.csv produced by ingest_validate.py
Output: attribution_report.csv, one row per (Campaign, Model) with total
credited dollars and touch count, plus a printed summary.

Usage:
    python run_attribution_models.py --journeys ../assets/sample_data/journeys.csv \
        --out ../assets/sample_data/attribution_report.csv --model w_shaped
    python run_attribution_models.py --journeys ... --out ... --model all
"""

import argparse
import csv
from collections import defaultdict


def load_journeys(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    won_rows = [r for r in rows if r["Is_Won"].strip().lower() == "true"]
    return won_rows


def group_by_opportunity(rows):
    opps = defaultdict(list)
    for r in rows:
        opps[r["Opportunity_ID"]].append(r)
    for opp_id in opps:
        opps[opp_id].sort(key=lambda r: r["Touchpoint_Date"])
    return opps


def opp_amount(rows):
    return float(rows[0]["Amount"])


# --- Individual model implementations -------------------------------------
# Each function takes the sorted list of touchpoint rows for one opportunity
# and returns a dict of {row_index: weight_fraction}, weights summing to 1.0.

def model_first_touch(rows):
    return {0: 1.0}

def model_last_touch(rows):
    return {len(rows) - 1: 1.0}

def model_linear(rows):
    n = len(rows)
    return {i: 1.0 / n for i in range(n)}

def model_time_decay(rows, half_life_days=14):
    # More recent touches (closer to close) get exponentially more credit.
    # Weight ~ 2^(-days_before_close / half_life)
    weights = []
    for r in rows:
        days = max(float(r["Days_Before_Close"]), 0)
        weights.append(2 ** (-days / half_life_days))
    total = sum(weights) or 1.0
    return {i: w / total for i, w in enumerate(weights)}

def model_u_shaped(rows):
    # 40% first touch, 40% opportunity-creation-adjacent touch, 20% split across middle
    n = len(rows)
    if n == 1:
        return {0: 1.0}
    if n == 2:
        return {0: 0.5, 1: 0.5}
    # find touch closest to (but not after) opp creation as the "lead creation" analog
    creation_idx = _closest_to_creation_index(rows)
    return _distribute_with_anchors(rows, anchors={0: 0.4, creation_idx: 0.4}, remainder=0.2)

def model_w_shaped(rows):
    # 30% first touch, 30% touch nearest opp creation, 30% touch nearest close (last touch),
    # remaining 10% split across whatever else is in the middle.
    n = len(rows)
    if n == 1:
        return {0: 1.0}
    creation_idx = _closest_to_creation_index(rows)
    last_idx = n - 1
    anchors = {0: 0.30, creation_idx: 0.30, last_idx: 0.30}
    return _distribute_with_anchors(rows, anchors=anchors, remainder=0.10)

def model_full_path(rows):
    # Same as W-shaped but reserves an explicit slice for the close itself,
    # useful when a late re-engagement (e.g. a fresh case study or ROI call)
    # revives a stalling deal right before close.
    n = len(rows)
    if n == 1:
        return {0: 1.0}
    creation_idx = _closest_to_creation_index(rows)
    last_idx = n - 1
    anchors = {0: 0.225, creation_idx: 0.225, last_idx: 0.225}
    close_bonus_idx = last_idx
    result = _distribute_with_anchors(rows, anchors=anchors, remainder=0.10)
    result[close_bonus_idx] = result.get(close_bonus_idx, 0) + 0.225
    return result


def _closest_to_creation_index(rows):
    # index of the earliest touch that occurs on/after opp creation, else the last pre-creation touch
    for i, r in enumerate(rows):
        if r["Is_Before_Opp_Created"].strip().lower() == "false":
            return i
    return len(rows) - 1

def _distribute_with_anchors(rows, anchors, remainder):
    n = len(rows)
    weights = {i: 0.0 for i in range(n)}
    for idx, w in anchors.items():
        weights[idx] += w
    middle_indices = [i for i in range(n) if i not in anchors]
    if middle_indices:
        share = remainder / len(middle_indices)
        for i in middle_indices:
            weights[i] += share
    else:
        # no middle touches, fold remainder into the anchors evenly
        share = remainder / len(anchors)
        for idx in anchors:
            weights[idx] += share
    return weights


MODELS = {
    "first_touch": model_first_touch,
    "last_touch": model_last_touch,
    "linear": model_linear,
    "time_decay": model_time_decay,
    "u_shaped": model_u_shaped,
    "w_shaped": model_w_shaped,
    "full_path": model_full_path,
}

MODEL_NOTES = {
    "first_touch": "Diagnostic only: shows what creates initial awareness. Not recommended as the primary model for a 6-month cycle.",
    "last_touch": "Diagnostic only: shows what triggers the close. Not recommended as the primary model for a 6-month cycle.",
    "linear": "Baseline / sanity check. Treats every touch as equally important, which understates the moments that matter most.",
    "time_decay": "Good if late-stage touches (demos, ROI tools) are believed to matter most. Tune half_life_days to your cycle.",
    "u_shaped": "Emphasizes first touch and lead/opportunity creation. Reasonable default if you don't need to isolate the close itself.",
    "w_shaped": "RECOMMENDED DEFAULT for a ~6-month, multi-stakeholder cycle. Balances awareness, qualification, and late-stage influence.",
    "full_path": "Use if you suspect late re-engagement (a fresh asset, a reference call) is reviving stalled deals right before close.",
}


def run_model(model_name, opps_by_id, half_life_days=14):
    fn = MODELS[model_name]
    campaign_credit = defaultdict(lambda: {"dollars": 0.0, "touches": 0})
    for opp_id, rows in opps_by_id.items():
        amount = opp_amount(rows)
        weights = fn(rows, half_life_days) if model_name == "time_decay" else fn(rows)
        for i, r in enumerate(rows):
            w = weights.get(i, 0.0)
            key = (r["Campaign_ID"], r["Campaign_Name"], r["Campaign_Type"], r["Channel"])
            campaign_credit[key]["dollars"] += amount * w
            campaign_credit[key]["touches"] += 1
    return campaign_credit


def write_report(results_by_model, out_path):
    rows = []
    for model_name, campaign_credit in results_by_model.items():
        for (cid, cname, ctype, channel), vals in campaign_credit.items():
            rows.append({
                "Model": model_name,
                "Campaign_ID": cid,
                "Campaign_Name": cname,
                "Campaign_Type": ctype,
                "Channel": channel,
                "Attributed_Dollars": round(vals["dollars"], 2),
                "Touch_Count": vals["touches"],
            })
    rows.sort(key=lambda r: (r["Model"], -r["Attributed_Dollars"]))
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


def print_summary(results_by_model):
    for model_name, campaign_credit in results_by_model.items():
        print(f"\n=== {model_name} ===")
        print(f"({MODEL_NOTES.get(model_name, '')})")
        ranked = sorted(campaign_credit.items(), key=lambda kv: -kv[1]["dollars"])[:5]
        for (cid, cname, ctype, channel), vals in ranked:
            print(f"  {cname:45s} ${vals['dollars']:>10,.0f}  ({vals['touches']} touches)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--journeys", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="w_shaped", choices=list(MODELS.keys()) + ["all"])
    parser.add_argument("--half-life-days", type=int, default=14)
    args = parser.parse_args()

    won_rows = load_journeys(args.journeys)
    if not won_rows:
        print("No closed-won touchpoint rows found. Cannot compute attribution.")
        raise SystemExit(1)
    opps_by_id = group_by_opportunity(won_rows)
    print(f"Computing attribution across {len(opps_by_id)} closed-won opportunities.")

    model_names = list(MODELS.keys()) if args.model == "all" else [args.model]
    results_by_model = {}
    for name in model_names:
        results_by_model[name] = run_model(name, opps_by_id, args.half_life_days)

    print_summary(results_by_model)
    write_report(results_by_model, args.out)
