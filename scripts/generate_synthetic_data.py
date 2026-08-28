"""
Generates synthetic Salesforce + Pardot export files matching the schema in
references/salesforce_data_requirements.md and references/pardot_data_requirements.md.

This data is entirely fabricated. It exists so the attribution scripts can be
built and tested without any real customer, prospect, or pipeline data
ever being committed to this public repository. Do not replace these files
with real exports; point the skill at your real files locally instead, and
keep them out of version control (see .gitignore).

Usage:
    python generate_synthetic_data.py --out ../assets/sample_data --opportunities 40 --seed 7
"""

import argparse
import csv
import os
import random
from datetime import datetime, timedelta

INDUSTRIES = ["Consumer Goods", "Apparel & Footwear", "Food & Beverage", "3PL / Logistics", "Retail"]
SEGMENTS = ["Enterprise DTC", "Mid-Market Retail", "3PL Partner", "Enterprise Omnichannel"]
LOSS_REASONS = ["Chose competitor", "Budget cut", "No decision / stalled", "Built in-house", "Timing not right"]
ROLES = ["Economic Buyer", "Champion", "Decision Maker", "Influencer", "Technical Evaluator", "Business User"]
OWNERS = ["J. Alvarez", "M. Chen", "R. Okafor", "S. Patel", "T. Nguyen"]

CAMPAIGNS = [
    ("Peak Season Playbook Download", "Content Syndication", "Paid"),
    ("On-Demand Warehousing ROI Calculator", "Interactive Tool", "Organic"),
    ("Flexible Warehousing 101 Webinar", "Webinar", "Event"),
    ("Spot Warehousing Index Report", "Content Syndication", "Organic"),
    ("MODEX Trade Show", "Trade Show", "Event"),
    ("ABM Direct Mail - Enterprise DTC", "ABM Direct Mail", "Partner"),
    ("Case Study: Enterprise Overflow Program", "Case Study", "Organic"),
    ("Google Search - Warehousing Brand", "Paid Search", "Paid"),
    ("Google Search - Warehousing Non-Brand", "Paid Search", "Paid"),
    ("LinkedIn ABM Retargeting", "Paid Social", "Paid"),
    ("Q3 Email Nurture - Overflow Storage", "Email Nurture", "Email"),
    ("Partner Referral - 3PL Network", "Referral", "Partner"),
    ("Analyst Report Syndication (Gartner)", "Content Syndication", "Paid"),
    ("Demo Request Landing Page", "Demo Request", "Direct"),
    ("Customer Reference Call Program", "Reference Program", "Direct"),
]

TOUCHPOINT_TYPES_BY_CAMPAIGN_TYPE = {
    "Content Syndication": ["Form Submission", "Content Download"],
    "Interactive Tool": ["Landing Page Visit", "Page Action"],
    "Webinar": ["Webinar Registration", "Webinar Attendance"],
    "Trade Show": ["Form Submission", "Page Action"],
    "ABM Direct Mail": ["Page Action"],
    "Case Study": ["Content Download", "Landing Page Visit"],
    "Paid Search": ["Landing Page Visit", "Form Submission"],
    "Paid Social": ["Landing Page Visit"],
    "Email Nurture": ["Email Open", "Email Click"],
    "Referral": ["Form Submission"],
    "Demo Request": ["Demo Request"],
    "Reference Program": ["Page Action"],
}

FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Drew", "Jamie", "Cameron"]
LAST_NAMES = ["Reed", "Bennett", "Foster", "Hayes", "Coleman", "Brooks", "Mercer", "Whitfield", "Ellison", "Grant"]

random.seed(0)


def sf_id(prefix, n):
    return f"{prefix}{n:015d}"


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days), seconds=random.randint(0, 86399))


def generate(num_opportunities, seed, out_dir):
    random.seed(seed)
    os.makedirs(out_dir, exist_ok=True)

    campaign_rows = []
    campaign_ids = []
    for i, (name, ctype, channel) in enumerate(CAMPAIGNS):
        cid = sf_id("701", i + 1)
        campaign_ids.append((cid, name, ctype, channel))
        start = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 400))
        cost = random.choice([0, 0, 5000, 12000, 25000, 40000]) if channel in ("Paid", "Event", "Partner") else 0
        campaign_rows.append({
            "Campaign_ID": cid,
            "Campaign_Name": name,
            "Campaign_Type": ctype,
            "Channel": channel,
            "Parent_Campaign_ID": "",
            "Start_Date": start.strftime("%Y-%m-%d"),
            "Cost": cost,
        })

    accounts, opportunities, contact_roles, influence_rows = [], [], [], []
    prospects, engagement_rows, prospect_map_rows = [], [], []

    prospect_counter = 1
    for opp_num in range(1, num_opportunities + 1):
        account_id = sf_id("001", opp_num)
        account_name = f"{random.choice(['North', 'Summit', 'Harbor', 'Vantage', 'Anchor', 'Pioneer'])} " \
                        f"{random.choice(['Retail Co', 'Goods Group', 'Brands Inc', 'Logistics LLC', 'Supply Co'])}"
        industry = random.choice(INDUSTRIES)
        segment = random.choice(SEGMENTS)
        accounts.append({
            "Account_ID": account_id, "Account_Name": account_name,
            "Account_Industry": industry, "Account_Segment": segment,
            "Employee_Count": random.choice([250, 800, 1500, 4000, 12000]),
        })

        created = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 250))
        cycle_days = int(random.gauss(182, 35))
        cycle_days = max(60, min(cycle_days, 300))
        close = created + timedelta(days=cycle_days)
        is_won = random.random() < 0.35
        is_closed = True
        opp_id = sf_id("006", opp_num)
        amount = random.choice([45000, 60000, 90000, 120000, 180000, 250000])

        num_stakeholders = random.randint(1, 4)
        contacts_for_opp = []
        for s in range(num_stakeholders):
            contact_id = sf_id("003", prospect_counter)
            prospect_counter += 1
            fname, lname = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            contacts_for_opp.append(contact_id)
            contact_roles.append({
                "Opportunity_ID": opp_id, "Contact_ID": contact_id,
                "Contact_Name": f"{fname} {lname}",
                "Role": ROLES[s] if s < len(ROLES) else random.choice(ROLES),
                "Is_Primary": s == 0,
            })
            prospects.append(contact_id)
            prospect_map_rows.append({
                "Prospect_ID": contact_id, "Contact_ID": contact_id, "Account_ID": account_id,
                "Email": f"{fname.lower()}.{lname.lower()}@{account_name.split()[0].lower()}.com",
            })

        # Winning deals get more, and more varied, touches; losing deals get fewer / narrower
        num_touch_campaigns = random.randint(4, 7) if is_won else random.randint(1, 4)
        chosen_campaigns = random.sample(campaign_ids, k=min(num_touch_campaigns, len(campaign_ids)))

        # bias winners toward webinar + ROI tool + case study + demo request being present
        if is_won:
            for must_have in ["On-Demand Warehousing ROI Calculator", "Flexible Warehousing 101 Webinar", "Demo Request Landing Page"]:
                match = next((c for c in campaign_ids if c[1] == must_have), None)
                if match and match not in chosen_campaigns:
                    chosen_campaigns.append(match)

        primary_set = False
        for cid, cname, ctype, channel in chosen_campaigns:
            touch_types = TOUCHPOINT_TYPES_BY_CAMPAIGN_TYPE.get(ctype, ["Page Action"])
            for contact_id in random.sample(contacts_for_opp, k=random.randint(1, len(contacts_for_opp))):
                touch_date = random_date(created - timedelta(days=random.randint(0, 30)),
                                          min(close, created + timedelta(days=cycle_days)))
                engagement_rows.append({
                    "Prospect_ID": contact_id, "Campaign_ID": cid,
                    "Touchpoint_Type": random.choice(touch_types),
                    "Touchpoint_Date": touch_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "Asset_Name": cname,
                    "Score_Delta": random.choice([5, 10, 15, 20, 25]),
                })
            is_primary = not primary_set and random.random() < 0.4
            if is_primary:
                primary_set = True
            influence_rows.append({
                "Opportunity_ID": opp_id, "Campaign_ID": cid,
                "Is_Primary_Campaign_Source": is_primary,
                "Contact_ID": random.choice(contacts_for_opp),
            })

        opportunities.append({
            "Opportunity_ID": opp_id,
            "Opportunity_Name": f"{account_name} - Warehousing Expansion",
            "Account_ID": account_id, "Account_Name": account_name,
            "Account_Industry": industry, "Account_Segment": segment,
            "Amount": amount,
            "Stage": "Closed Won" if is_won else "Closed Lost",
            "Is_Won": is_won, "Is_Closed": is_closed,
            "Created_Date": created.strftime("%Y-%m-%d"),
            "Close_Date": close.strftime("%Y-%m-%d"),
            "Loss_Reason": "" if is_won else random.choice(LOSS_REASONS),
            "Primary_Campaign_Source": next((c[0] for c in chosen_campaigns), ""),
            "Lead_Source": random.choice(["Web", "Trade Show", "Referral", "Outbound Prospecting"]),
            "Owner_Name": random.choice(OWNERS),
        })

    def write_csv(filename, rows, fieldnames):
        path = os.path.join(out_dir, filename)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {path}")

    write_csv("opportunities.csv", opportunities, list(opportunities[0].keys()))
    write_csv("opportunity_contact_roles.csv", contact_roles, list(contact_roles[0].keys()))
    write_csv("campaign_influence.csv", influence_rows, list(influence_rows[0].keys()))
    write_csv("accounts.csv", accounts, list(accounts[0].keys()))
    write_csv("campaigns.csv", campaign_rows, list(campaign_rows[0].keys()))
    write_csv("prospect_engagement.csv", engagement_rows, list(engagement_rows[0].keys()))
    write_csv("prospect_account_map.csv", prospect_map_rows, list(prospect_map_rows[0].keys()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="../assets/sample_data")
    parser.add_argument("--opportunities", type=int, default=40)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    generate(args.opportunities, args.seed, args.out)
