"""
Loads the Salesforce + Pardot CSV exports, validates required fields, and
joins them into a single opportunity-to-touchpoint journey table that the
attribution model scripts consume.

Usage:
    python ingest_validate.py --data-dir ../assets/sample_data --out ../assets/sample_data/journeys.csv
"""

import argparse
import csv
import os
import sys
from datetime import datetime

REQUIRED_FILES = {
    "opportunities.csv": ["Opportunity_ID", "Account_ID", "Amount", "Stage", "Is_Won", "Is_Closed", "Created_Date", "Close_Date"],
    "opportunity_contact_roles.csv": ["Opportunity_ID", "Contact_ID", "Role"],
    "campaign_influence.csv": ["Opportunity_ID", "Campaign_ID"],
    "campaigns.csv": ["Campaign_ID", "Campaign_Name", "Campaign_Type", "Channel"],
    "prospect_engagement.csv": ["Prospect_ID", "Campaign_ID", "Touchpoint_Type", "Touchpoint_Date"],
}
OPTIONAL_FILES = ["accounts.csv", "prospect_account_map.csv"]


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def validate(data_dir):
    errors = []
    loaded = {}
    for fname, required_cols in REQUIRED_FILES.items():
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            errors.append(f"MISSING FILE: {fname}")
            continue
        rows = load_csv(path)
        if not rows:
            errors.append(f"EMPTY FILE: {fname}")
            loaded[fname] = []
            continue
        missing_cols = [c for c in required_cols if c not in rows[0].keys()]
        if missing_cols:
            errors.append(f"{fname}: missing required column(s) {missing_cols}")
        loaded[fname] = rows

    for fname in OPTIONAL_FILES:
        path = os.path.join(data_dir, fname)
        loaded[fname] = load_csv(path) if os.path.exists(path) else []
        if not loaded[fname]:
            print(f"NOTE: {fname} not found or empty, proceeding without it (some cuts of the report will be unavailable)")

    return loaded, errors


def parse_date(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {s}")


def build_journeys(loaded):
    """
    Produces one row per (Opportunity, touchpoint) pair, with the touchpoint's
    position in the opportunity's timeline. This is the table every attribution
    model script reads from.
    """
    opps_by_id = {r["Opportunity_ID"]: r for r in loaded["opportunities.csv"]}
    contact_roles = loaded["opportunity_contact_roles.csv"]

    # Map: which contacts belong to which opportunity
    opp_to_contacts = {}
    for r in contact_roles:
        opp_to_contacts.setdefault(r["Opportunity_ID"], set()).add(r["Contact_ID"])

    campaigns_by_id = {r["Campaign_ID"]: r for r in loaded["campaigns.csv"]}

    # Map: which prospects map to which contact (defaults to same ID if no map file)
    prospect_to_contact = {}
    if loaded.get("prospect_account_map.csv"):
        for r in loaded["prospect_account_map.csv"]:
            if r.get("Contact_ID"):
                prospect_to_contact[r["Prospect_ID"]] = r["Contact_ID"]

    def resolve_contact(prospect_id):
        return prospect_to_contact.get(prospect_id, prospect_id)

    # Build contact -> list of opportunities they're on
    contact_to_opps = {}
    for opp_id, contacts in opp_to_contacts.items():
        for c in contacts:
            contact_to_opps.setdefault(c, []).append(opp_id)

    journeys = []
    unmatched_engagement = 0
    for eng in loaded["prospect_engagement.csv"]:
        contact_id = resolve_contact(eng["Prospect_ID"])
        opp_ids = contact_to_opps.get(contact_id, [])
        if not opp_ids:
            unmatched_engagement += 1
            continue
        try:
            touch_date = parse_date(eng["Touchpoint_Date"])
        except ValueError:
            continue
        campaign = campaigns_by_id.get(eng["Campaign_ID"], {})
        for opp_id in opp_ids:
            opp = opps_by_id.get(opp_id)
            if not opp:
                continue
            try:
                created = parse_date(opp["Created_Date"])
                close = parse_date(opp["Close_Date"])
            except ValueError:
                continue
            # Only count touches within a reasonable pre-opp-creation lookback
            # through the close date, discard touches long after close.
            if touch_date > close:
                continue
            journeys.append({
                "Opportunity_ID": opp_id,
                "Is_Won": opp["Is_Won"],
                "Amount": opp["Amount"],
                "Created_Date": opp["Created_Date"],
                "Close_Date": opp["Close_Date"],
                "Contact_ID": contact_id,
                "Campaign_ID": eng["Campaign_ID"],
                "Campaign_Name": campaign.get("Campaign_Name", "Unknown"),
                "Campaign_Type": campaign.get("Campaign_Type", "Unknown"),
                "Channel": campaign.get("Channel", "Unknown"),
                "Touchpoint_Type": eng["Touchpoint_Type"],
                "Touchpoint_Date": eng["Touchpoint_Date"],
                "Days_Before_Close": (close - touch_date).days,
                "Days_After_Created": (touch_date - created).days,
                "Is_Before_Opp_Created": touch_date < created,
            })

    print(f"Built {len(journeys)} touchpoint-journey rows across {len(opps_by_id)} opportunities.")
    if unmatched_engagement:
        print(f"WARNING: {unmatched_engagement} engagement rows could not be matched to any opportunity "
              f"contact (prospect not on any Opportunity Contact Role). These represent real engagement "
              f"that is currently invisible to attribution, likely worth a follow-up data-hygiene pass.")
    return journeys


def write_journeys(journeys, out_path):
    if not journeys:
        print("No journey rows produced, nothing written.")
        return
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(journeys[0].keys()))
        writer.writeheader()
        writer.writerows(journeys)
    print(f"Wrote {len(journeys)} rows to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    loaded, errors = validate(args.data_dir)
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    journeys = build_journeys(loaded)
    write_journeys(journeys, args.out)
