"""
Compares campaign/touchpoint patterns between closed-won and closed-lost
opportunities. This answers a different question than the attribution
models: not "how should credit be split on deals we won" but "what
distinguishes the deals we won from the ones we lost."

Both views matter for a comprehensive framework: attribution tells you how
to weight budget across campaigns; this tells you which campaigns and
sequences are actually worth having in the mix at all.

Usage:
    python win_loss_driver_analysis.py --journeys ../assets/sample_data/journeys.csv \
        --out ../assets/sample_data/win_loss_drivers.csv
"""

import argparse
import csv
from collections import defaultdict


def load_journeys(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def presence_rate(rows, key_field):
    """
    For each distinct value of key_field (e.g. Campaign_Name), computes the
    fraction of WON opportunities that included at least one touch of that
    value, versus the fraction of LOST opportunities that did. A large gap
    (won rate much higher than lost rate) suggests that touchpoint is a
    positive driver; the reverse suggests it correlates with losses or is
    simply present regardless of outcome (neutral).
    """
    won_opps, lost_opps = set(), set()
    value_to_won_opps = defaultdict(set)
    value_to_lost_opps = defaultdict(set)

    for r in rows:
        opp_id = r["Opportunity_ID"]
        is_won = r["Is_Won"].strip().lower() == "true"
        value = r[key_field]
        if is_won:
            won_opps.add(opp_id)
            value_to_won_opps[value].add(opp_id)
        else:
            lost_opps.add(opp_id)
            value_to_lost_opps[value].add(opp_id)

    total_won = len(won_opps) or 1
    total_lost = len(lost_opps) or 1

    all_values = set(value_to_won_opps) | set(value_to_lost_opps)
    results = []
    for v in all_values:
        won_rate = len(value_to_won_opps[v]) / total_won
        lost_rate = len(value_to_lost_opps[v]) / total_lost
        results.append({
            key_field: v,
            "Won_Opp_Presence_Rate": round(won_rate, 3),
            "Lost_Opp_Presence_Rate": round(lost_rate, 3),
            "Gap_Won_Minus_Lost": round(won_rate - lost_rate, 3),
            "Won_Opp_Count": len(value_to_won_opps[v]),
            "Lost_Opp_Count": len(value_to_lost_opps[v]),
        })
    results.sort(key=lambda r: -r["Gap_Won_Minus_Lost"])
    return results, total_won, total_lost


def touch_volume_comparison(rows):
    """Average number of touches per opportunity, won vs lost. A wide gap
    suggests engagement depth itself (not just which campaigns) matters."""
    opp_touch_count = defaultdict(int)
    opp_is_won = {}
    for r in rows:
        opp_touch_count[r["Opportunity_ID"]] += 1
        opp_is_won[r["Opportunity_ID"]] = r["Is_Won"].strip().lower() == "true"

    won_counts = [c for opp, c in opp_touch_count.items() if opp_is_won[opp]]
    lost_counts = [c for opp, c in opp_touch_count.items() if not opp_is_won[opp]]
    avg_won = sum(won_counts) / len(won_counts) if won_counts else 0
    avg_lost = sum(lost_counts) / len(lost_counts) if lost_counts else 0
    return avg_won, avg_lost


def write_report(campaign_results, type_results, out_path):
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["-- By Campaign --"])
        writer.writerow(["Campaign_Name", "Won_Presence_Rate", "Lost_Presence_Rate", "Gap", "Won_Count", "Lost_Count"])
        for r in campaign_results:
            writer.writerow([r["Campaign_Name"], r["Won_Opp_Presence_Rate"], r["Lost_Opp_Presence_Rate"],
                              r["Gap_Won_Minus_Lost"], r["Won_Opp_Count"], r["Lost_Opp_Count"]])
        writer.writerow([])
        writer.writerow(["-- By Campaign Type --"])
        writer.writerow(["Campaign_Type", "Won_Presence_Rate", "Lost_Presence_Rate", "Gap", "Won_Count", "Lost_Count"])
        for r in type_results:
            writer.writerow([r["Campaign_Type"], r["Won_Opp_Presence_Rate"], r["Lost_Opp_Presence_Rate"],
                              r["Gap_Won_Minus_Lost"], r["Won_Opp_Count"], r["Lost_Opp_Count"]])
    print(f"Wrote win/loss driver report to {out_path}")


def print_summary(campaign_results, avg_won, avg_lost):
    print(f"\nAverage touches per opportunity: won={avg_won:.1f}, lost={avg_lost:.1f}")
    if avg_lost and avg_won / max(avg_lost, 0.1) > 1.3:
        print("  Won deals show meaningfully more touches than lost deals; engagement depth looks like a signal worth tracking.")
    print("\nTop positive drivers (highest won-vs-lost presence gap):")
    for r in campaign_results[:5]:
        print(f"  {r['Campaign_Name']:45s} won={r['Won_Opp_Presence_Rate']:.0%}  lost={r['Lost_Opp_Presence_Rate']:.0%}  gap=+{r['Gap_Won_Minus_Lost']:.0%}")
    print("\nCampaigns present more often on LOST deals (investigate, may be low-intent or too-early-stage):")
    for r in sorted(campaign_results, key=lambda r: r["Gap_Won_Minus_Lost"])[:5]:
        if r["Gap_Won_Minus_Lost"] < 0:
            print(f"  {r['Campaign_Name']:45s} won={r['Won_Opp_Presence_Rate']:.0%}  lost={r['Lost_Opp_Presence_Rate']:.0%}  gap={r['Gap_Won_Minus_Lost']:.0%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--journeys", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = load_journeys(args.journeys)
    campaign_results, total_won, total_lost = presence_rate(rows, "Campaign_Name")
    type_results, _, _ = presence_rate(rows, "Campaign_Type")
    avg_won, avg_lost = touch_volume_comparison(rows)

    print(f"Analyzing {total_won} won and {total_lost} lost opportunities.")
    print_summary(campaign_results, avg_won, avg_lost)
    write_report(campaign_results, type_results, args.out)
