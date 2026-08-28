# Salesforce Data Requirements

This document defines the CSV export format the skill expects for Salesforce data. Field names are drawn from the standard Salesforce Opportunity, OpportunityContactRole, and CampaignInfluence object model. These have not been validated against a live org yet; treat them as a starting contract and confirm field-level names (especially any custom fields) against the actual org before the first real run.

Export four files. All ID fields should be the standard 18-character Salesforce record IDs so joins are unambiguous.

## 1. opportunities.csv

One row per Opportunity.

| Field | Type | Notes |
|---|---|---|
| Opportunity_ID | string | Salesforce Opportunity Id (18-char) |
| Opportunity_Name | string | |
| Account_ID | string | |
| Account_Name | string | |
| Account_Industry | string | Standard Industry picklist value |
| Account_Segment | string | Custom field if present (e.g. Enterprise, Mid-Market, SMB); omit column if not tracked |
| Amount | number | Deal value in USD |
| Stage | string | StageName, standard or custom stage picklist |
| Is_Won | boolean | True/False |
| Is_Closed | boolean | True/False |
| Created_Date | date (YYYY-MM-DD) | Opportunity CreatedDate |
| Close_Date | date (YYYY-MM-DD) | Actual close date if closed, else current CloseDate estimate |
| Loss_Reason | string | Custom field, blank if not closed lost |
| Primary_Campaign_Source | string | Campaign_ID of the CampaignId field on Opportunity, blank if unset |
| Lead_Source | string | Standard LeadSource picklist |
| Owner_Name | string | Opportunity owner (sales rep) |

## 2. opportunity_contact_roles.csv

One row per OpportunityContactRole. An opportunity can have multiple rows (multiple stakeholders).

| Field | Type | Notes |
|---|---|---|
| Opportunity_ID | string | Joins to opportunities.csv |
| Contact_ID | string | Salesforce Contact Id, must match the ID used in Pardot prospect exports (see pardot_data_requirements.md) |
| Contact_Name | string | |
| Role | string | Standard or custom Role picklist (e.g. Economic Buyer, Decision Maker, Champion, Influencer, Technical Evaluator, Business User) |
| Is_Primary | boolean | IsPrimary flag |

## 3. campaign_influence.csv

One row per Opportunity-to-Campaign influence relationship, from the Salesforce CampaignInfluence related list. This should include every campaign associated with the opportunity, not just the primary one; the skill needs the full influence set to compute multi-touch models.

| Field | Type | Notes |
|---|---|---|
| Opportunity_ID | string | Joins to opportunities.csv |
| Campaign_ID | string | Joins to campaigns.csv (see pardot_data_requirements.md, Connected Campaigns means one Campaign object shared by Salesforce and Pardot) |
| Is_Primary_Campaign_Source | boolean | True if this is the Opportunity's Primary Campaign Source |
| Contact_ID | string | The Contact whose engagement drove this influence record, if available |

## 4. accounts.csv (optional but recommended)

One row per Account. Useful for segmenting attribution results by account type, since a mixed buyer base (e.g. enterprise DTC brands vs. 3PLs vs. mid-market retail) likely has different winning touch patterns.

| Field | Type | Notes |
|---|---|---|
| Account_ID | string | |
| Account_Name | string | |
| Account_Industry | string | |
| Account_Segment | string | |
| Employee_Count | number | Optional, for firmographic cuts |

## Known gaps to validate against the real org

- Confirm whether your org uses a custom Role picklist on OpportunityContactRole, and get the actual value list.
- Confirm whether "Account_Segment" exists as a real field or needs to be derived from another field (e.g. a custom tier field, NAICS code, or Account record type).
- Confirm the CampaignInfluence model currently enabled (Salesforce Influence, Customizable Campaign Influence, or none) since this determines whether campaign_influence.csv can be exported directly or needs to be reconstructed from Campaign Members plus Contact Roles.
- Confirm Loss_Reason field API name if custom.
