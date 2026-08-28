# Pardot (Account Engagement) Data Requirements

This document defines the CSV export format the skill expects for Pardot data. With Connected Campaigns enabled, Pardot campaigns and Salesforce campaigns are the same Campaign object, so campaigns.csv below is the shared reference table used by both the Salesforce and Pardot exports.

Export three files.

## 1. campaigns.csv

One row per Campaign (Connected Campaign object, shared with Salesforce).

| Field | Type | Notes |
|---|---|---|
| Campaign_ID | string | Salesforce Campaign Id (18-char) |
| Campaign_Name | string | |
| Campaign_Type | string | e.g. Webinar, Content Syndication, Paid Search, Paid Social, Email Nurture, Trade Show, ABM Direct Mail, Case Study, Demo Request, Organic Content, Referral, Partner Co-Marketing |
| Channel | string | Paid, Organic, Direct, Partner, Event, Email |
| Parent_Campaign_ID | string | Blank if top-level, used for campaign hierarchy rollups |
| Start_Date | date (YYYY-MM-DD) | |
| Cost | number | Optional, enables ROI/cost-per-influenced-dollar calculations |

## 2. prospect_engagement.csv

One row per meaningful engagement event (not every pageview, "meaningful" per your Pardot completion action / scoring rules). This is the touchpoint stream the attribution models run against.

| Field | Type | Notes |
|---|---|---|
| Prospect_ID | string | Pardot Prospect Id. Must correspond to the same person as Contact_ID in Salesforce's opportunity_contact_roles.csv. If Pardot Prospect ID and Salesforce Contact ID differ, include a Contact_ID column here as the join key instead. |
| Campaign_ID | string | Joins to campaigns.csv |
| Touchpoint_Type | string | Email Open, Email Click, Form Submission, Landing Page Visit, Content Download, Webinar Registration, Webinar Attendance, Page Action, Demo Request, Chat Engagement |
| Touchpoint_Date | datetime (YYYY-MM-DD HH:MM:SS) | Needs time precision, not just date, to sequence same-day touches |
| Asset_Name | string | Specific content/asset title (e.g. "On-Demand Warehousing ROI Calculator", "Peak Season Playbook") |
| Score_Delta | number | Optional, Pardot scoring point value for this action |

## 3. prospect_account_map.csv

One row per Prospect, mapping to the Account/Contact records in Salesforce. Needed because Pardot Prospects and Salesforce Contacts are often the same underlying join key once synced, but this file makes the mapping explicit and catches unsynced/orphaned prospects.

| Field | Type | Notes |
|---|---|---|
| Prospect_ID | string | |
| Contact_ID | string | Blank if not yet converted/synced to a Salesforce Contact, the skill should flag these as unlinked engagement (real signal, but not attributable to a specific opportunity) |
| Account_ID | string | |
| Email | string | Optional, useful as a backup join key if IDs are inconsistent |

## Known gaps to validate against the real org

- Confirm Connected Campaigns is actually enabled; if Pardot and Salesforce campaigns are still separate objects, campaigns.csv needs a mapping layer between Pardot campaign IDs and Salesforce campaign IDs.
- Confirm which Pardot activities count as "meaningful" for this analysis versus noise (e.g. every email open vs. only clicks and form fills). Recommend starting broad and letting the win/loss driver analysis (see references/attribution_frameworks.md) show which touchpoint types actually correlate with wins, then narrowing.
- Confirm whether Prospect_ID and Salesforce Contact_ID are the same value post-sync, or need the explicit prospect_account_map.csv join.
- Confirm data retention window in Pardot; if engagement history beyond a certain window has been purged, the historical scan may be limited to a shorter lookback than the full sales cycle for older opportunities.
